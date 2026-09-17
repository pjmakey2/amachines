"""Handlers del bus de eventos del Ecommerce."""
from django.contrib.auth.models import User

from Ecommerce.models import Pedido
from OptsIO import io_json
from Sifen import mng_gmdata
from Sifen.mng_sifen import MSifen
from Sifen.models import Ciudades, Clientes, Distrito, DocumentHeader


class FacturacionError(Exception):
    """La factura no pudo generarse: el evento queda en error y se reintenta (o se factura a mano desde Pedidos)."""


def _datos_cliente(pedido) -> dict:
    """Mismo criterio que el resto del sistema: sin RUC/CI valido la factura es innominada."""
    distobj = Distrito.objects.filter(nombre_distrito='ASUNCION (DISTRITO)').first()
    ciudadobj = Ciudades.objects.filter(distritoobj=distobj).first() if distobj else None
    base = {
        'pdv_pais_cod': 'PRY', 'pdv_pais': 'Paraguay', 'pdv_type_business': 'B2C', 'pdv_numero_casa': 0,
        'pdv_direccion_entrega': (pedido.direccion or 'ND')[:200],
        'pdv_dpto_cod': distobj.dptoobj.codigo_departamento if distobj else 1,
        'pdv_dpto_nombre': distobj.dptoobj.nombre_departamento if distobj else 'CAPITAL',
        'pdv_distrito_cod': distobj.codigo_distrito if distobj else 1,
        'pdv_distrito_nombre': distobj.nombre_distrito if distobj else 'ASUNCION (DISTRITO)',
        'pdv_ciudad_cod': ciudadobj.codigo_ciudad if ciudadobj else 1,
        'pdv_ciudad_nombre': ciudadobj.nombre_ciudad if ciudadobj else 'ASUNCION (DISTRITO)',
        'pdv_telefono': pedido.cliente_telefono or '00000', 'pdv_celular': pedido.cliente_telefono or '00000',
        'pdv_email': pedido.cliente_email or 'nomail@nomail.com',
    }
    ruc = (pedido.cliente_documento or '').split('-')[0].strip()
    if not ruc or ruc == '0':
        return {**base, 'pdv_innominado': True, 'pdv_tipocontribuyente': '3', 'pdv_es_contribuyente': False, 'pdv_codigo': 999,
                'pdv_ruc': '0', 'pdv_ruc_dv': 0, 'pdv_nombrefantasia': 'Sin Nombre', 'pdv_nombrefactura': 'Sin Nombre'}
    cliente = Clientes.objects.filter(pdv_ruc=ruc).first()
    return {**base, 'pdv_innominado': False, 'pdv_codigo': 0, 'pdv_ruc': ruc,
            'pdv_ruc_dv': (cliente.pdv_ruc_dv if cliente else mng_gmdata.Gdata().calculate_dv(ruc)) or 0,
            'pdv_tipocontribuyente': str(cliente.pdv_tipocontribuyente) if cliente else '3',
            'pdv_es_contribuyente': cliente.pdv_es_contribuyente if cliente else False,
            'pdv_nombrefantasia': (cliente.pdv_nombrefantasia if cliente else pedido.cliente_nombre)[:300],
            'pdv_nombrefactura': (cliente.pdv_nombrefactura if cliente else pedido.cliente_nombre)[:300]}


def facturar(pedido, userobj) -> DocumentHeader:
    """Genera la factura electronica (contado) del pedido por el circuito normal de Sifen. Idempotente."""
    if pedido.documentheader_id:
        return DocumentHeader.objects.get(pk=pedido.documentheader_id)
    existente = DocumentHeader.objects.filter(source='ECOMMERCE', ext_link=pedido.pk).first()
    if not existente:
        iva = lambda prod: prod.porcentaje_iva.porcentaje if prod.porcentaje_iva_id else 10
        detalles = [{
            'prod_cod': d.productoobj.prod_cod, 'prod_descripcion': d.titulo[:500], 'precio_unitario': float(d.precio_unitario),
            'cantidad': float(d.cantidad), 'prod_unidad_medida_desc': '77', 'prod_unidad_medida_desc_text': 'UNI',
            'exenta': 100 if iva(d.productoobj) == 0 else 0, 'g5': 100 if iva(d.productoobj) == 5 else 0,
            'g10': 100 if iva(d.productoobj) not in (0, 5) else 0,
            'descuento': 0, 'per_descuento': 0, 'descuento_global_item': 0,
        } for d in pedido.detalles.select_related('productoobj__porcentaje_iva')]
        if pedido.costo_envio > 0:
            detalles.append({'prod_cod': 999999, 'prod_descripcion': 'Envío', 'precio_unitario': float(pedido.costo_envio), 'cantidad': 1,
                             'prod_unidad_medida_desc': '77', 'prod_unidad_medida_desc_text': 'UNI', 'exenta': 0, 'g5': 0, 'g10': 100,
                             'descuento': 0, 'per_descuento': 0, 'descuento_global_item': 0})
        uc_fields = {
            **_datos_cliente(pedido), 'doc_tipo': 'FE', 'doc_tipo_cod': '1', 'doc_tipo_desc': 'Factura electrónica', 'doc_op': 'VTA',
            'doc_motivo': 'VTA', 'doc_moneda': 'GS' if pedido.moneda == 'PYG' else pedido.moneda, 'doc_tipo_ope': 1,
            'doc_tipo_ope_desc': 'Venta de mercadería', 'doc_cre_tipo': 1,
            'doc_tipo_pago_cod': 5 if pedido.metodo_pago == 'transferencia' else 1,
            'doc_tipo_pago': 'Transferencia' if pedido.metodo_pago == 'transferencia' else 'Efectivo',
            'observacion': f'Pedido online {pedido.get_numero_display()} - {pedido.tiendaobj.nombre}', 'details': detalles, 'send_save': True,
        }
        result, _, _ = MSifen().create_documentheader(userobj=userobj, qdict={'dbcon': 'default', 'uc_fields': io_json.to_json(uc_fields)})
        if not result.get('success'):
            raise FacturacionError(result.get('error') or 'No se pudo generar la factura')
        existente = DocumentHeader.objects.get(pk=result.get('record_id'))
        DocumentHeader.objects.filter(pk=existente.pk).update(source='ECOMMERCE', ext_link=pedido.pk)
    Pedido.objects.filter(pk=pedido.pk).update(documentheader_id=existente.pk)
    return existente


def facturar_pedido(event) -> dict:
    """ecommerce.pedido.pagado -> factura electronica. La emite el usuario que confirmo el pago."""
    pedido = Pedido.objects.get(pk=event.source_id)
    userobj = User.objects.filter(username=event.created_by).first()
    if not userobj:
        raise FacturacionError(f"Usuario {event.created_by} inexistente para emitir la factura")
    doc = facturar(pedido, userobj)
    return {'documentheader_id': doc.pk}
