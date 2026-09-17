"""Almacen: bodegas, ubicaciones, recepcion de mercaderia, almacenaje (traslados), ajustes y consulta de stock."""
import re
from datetime import datetime
from decimal import Decimal

from django.db import transaction

from Almacen.models import (
    AjusteStock, Bodega, MovimientoStock, Recepcion, RecepcionDetalle, StockUbicacion, Ubicacion,
    mover_stock, stock_disponible, stock_en_ubicacion,
)
from OptsIO.io_business import get_active_business, siguiente_numero, user_label
from OptsIO.io_json import from_json
from OptsIO.io_money import precision_monetaria
from Sifen.models import Producto

RE_DECIMAL = re.compile(r'^\d+(\.\d+)?$')
RE_FECHA = re.compile(r'^\d{4}-\d{2}-\d{2}$')
CATALOGOS = {'Bodega': Bodega, 'Ubicacion': Ubicacion}
EN_USO = {
    'Bodega': lambda ids: Ubicacion.objects.filter(bodegaobj_id__in=ids).exists(),
    'Ubicacion': lambda ids: MovimientoStock.objects.filter(ubicacionobj_id__in=ids).exists(),
}


def _dec(value) -> Decimal:
    texto = str(value if value is not None else '').strip()
    return Decimal(texto) if RE_DECIMAL.match(texto) else Decimal(0)


def _fecha(value):
    texto = str(value or '').strip()[:10]
    return datetime.strptime(texto, '%Y-%m-%d').date() if RE_FECHA.match(texto) else None


class MAlmacen:

    def delete_catalogo(self, *args, **kwargs) -> dict:
        q = kwargs.get('qdict', {})
        model = CATALOGOS.get(q.get('model_name'))
        bobj = get_active_business(kwargs.get('userobj'))
        if not model or not bobj:
            return {'msgs': [{'error': 'Solicitud invalida'}]}
        ids = list(model.objects.filter(pk__in=from_json(q.get('ids', '[]')), businessobj=bobj).values_list('pk', flat=True))
        if EN_USO[q.get('model_name')](ids):
            return {'msgs': [{'error': 'El registro ya tiene movimientos o ubicaciones: desactívelo en lugar de borrarlo'}]}
        n, _ = model.objects.filter(pk__in=ids).delete()
        return {'msgs': [{'success': f'{n} registro(s) borrado(s)'}]}

    @precision_monetaria
    def create_recepcion(self, *args, **kwargs) -> tuple:
        """c_a de RecepcionCreateUi. `detalles` = [{producto_id, ubicacion_id, cantidad_esperada, cantidad_recibida, costo_unitario, lote, vencimiento}]."""
        userobj = kwargs.get('userobj')
        f = from_json(kwargs.get('qdict', {}).get('uc_fields', '{}'))
        bobj = get_active_business(userobj)
        if not bobj:
            return {'error': 'El usuario no tiene un negocio activo'}, args, kwargs
        fecha = _fecha(f.get('fecha'))
        bodega = Bodega.objects.filter(pk=f.get('bodegaobj_id') or 0, businessobj=bobj, activo=True).first()
        detalles = [d for d in (f.get('detalles') or []) if d.get('producto_id') and _dec(d.get('cantidad_recibida')) > 0]
        if not fecha or not bodega or not detalles:
            return {'error': 'Fecha, bodega y al menos un producto con cantidad recibida son obligatorios'}, args, kwargs
        productos = {p.pk: p for p in Producto.objects.filter(pk__in=[d.get('producto_id') for d in detalles])}
        ubicaciones = {u.pk: u for u in Ubicacion.objects.filter(businessobj=bobj, bodegaobj=bodega, activo=True)}
        for d in detalles:
            if int(d.get('producto_id')) not in productos:
                return {'error': 'Hay productos inexistentes en la recepción'}, args, kwargs
            if int(d.get('ubicacion_id') or 0) not in ubicaciones:
                return {'error': f'Cada línea necesita una ubicación de la bodega {bodega}'}, args, kwargs
        with transaction.atomic():
            if f.get('id'):
                rec = Recepcion.objects.select_for_update().filter(pk=f.get('id'), businessobj=bobj).first()
                if not rec:
                    return {'error': 'Recepción inexistente'}, args, kwargs
                if rec.estado != 'cargado' or rec.anulado:
                    return {'error': f'La recepción está {rec.estado}: ya no se puede modificar'}, args, kwargs
                rec.actualizado_fecha, rec.actualizado_usuario = datetime.now(), user_label(userobj)
            else:
                rec = Recepcion(businessobj=bobj, numero=siguiente_numero(Recepcion, bobj))
                rec.registrar_carga(userobj)
            rec.fecha, rec.bodegaobj = fecha, bodega
            rec.proveedor = (f.get('proveedor') or '').strip()[:300]
            rec.documento_ref = (f.get('documento_ref') or '').strip()[:120]
            rec.orden_compra_ref = (f.get('orden_compra_ref') or '').strip()[:60]
            rec.observacion = (f.get('observacion') or '').strip()[:300]
            rec.save()
            rec.detalles.all().delete()
            RecepcionDetalle.objects.bulk_create([RecepcionDetalle(
                recepcionobj=rec, productoobj=productos[int(d.get('producto_id'))], ubicacionobj=ubicaciones[int(d.get('ubicacion_id'))],
                cantidad_esperada=_dec(d.get('cantidad_esperada')), cantidad_recibida=_dec(d.get('cantidad_recibida')),
                costo_unitario=_dec(d.get('costo_unitario')), lote=(d.get('lote') or '').strip()[:80],
                vencimiento=_fecha(d.get('vencimiento'))) for d in detalles])
        return {'success': f'Recepción {rec.get_numero_display()} guardada. El stock ingresa al aprobarse.', 'record_id': rec.pk}, args, kwargs

    def get_recepcion(self, *args, **kwargs) -> dict:
        bobj = get_active_business(kwargs.get('userobj'))
        rec = Recepcion.objects.filter(pk=kwargs.get('qdict', {}).get('id') or 0, businessobj=bobj).first()
        if not rec:
            return {'error': 'Recepción inexistente'}
        return {'success': True, 'detalles': [{
            'producto_id': d.productoobj_id, 'producto': f"{d.productoobj.prod_cod} - {d.productoobj.descripcion}",
            'ubicacion_id': d.ubicacionobj_id, 'cantidad_esperada': float(d.cantidad_esperada),
            'cantidad_recibida': float(d.cantidad_recibida), 'costo_unitario': float(d.costo_unitario), 'lote': d.lote,
            'vencimiento': d.vencimiento.strftime('%Y-%m-%d') if d.vencimiento else '',
        } for d in rec.detalles.select_related('productoobj')]}

    def get_ubicaciones(self, *args, **kwargs) -> dict:
        q = kwargs.get('qdict', {})
        bobj = get_active_business(kwargs.get('userobj'))
        qs = Ubicacion.objects.filter(businessobj=bobj, activo=True).select_related('bodegaobj')
        if q.get('bodega_id'):
            qs = qs.filter(bodegaobj_id=q.get('bodega_id'))
        return {'success': True, 'ubicaciones': [{'id': u.pk, 'text': u.get_descripcion(), 'tipo': u.tipo} for u in qs]}

    @precision_monetaria
    def trasladar(self, *args, **kwargs) -> dict:
        """Almacenaje: mueve stock entre dos ubicaciones del negocio (ej: del muelle de recepcion al estante)."""
        userobj, q = kwargs.get('userobj'), kwargs.get('qdict', {})
        bobj = get_active_business(userobj)
        origen = Ubicacion.objects.filter(pk=q.get('origen_id') or 0, businessobj=bobj).first()
        destino = Ubicacion.objects.filter(pk=q.get('destino_id') or 0, businessobj=bobj, activo=True).first()
        producto = Producto.objects.filter(pk=q.get('producto_id') or 0).first()
        cantidad = _dec(q.get('cantidad'))
        if not origen or not destino or not producto or origen.pk == destino.pk:
            return {'error': 'Indique producto, origen y un destino distinto'}
        if cantidad <= 0 or cantidad > stock_en_ubicacion(producto, origen):
            return {'error': f'Cantidad inválida: en {origen} hay {stock_en_ubicacion(producto, origen):,.2f}'}
        with transaction.atomic():
            texto = f"Traslado {origen} -> {destino}"
            mover_stock(bobj, producto, origen, -cantidad, 'traslado', texto, userobj=userobj)
            mover_stock(bobj, producto, destino, cantidad, 'traslado', texto, userobj=userobj)
        return {'success': f'{cantidad:,.2f} de {producto.descripcion} → {destino}'}

    @precision_monetaria
    def create_ajuste(self, *args, **kwargs) -> tuple:
        """c_a de AjusteStockCreateUi: registra el conteo; el stock se corrige al aprobarse."""
        userobj = kwargs.get('userobj')
        f = from_json(kwargs.get('qdict', {}).get('uc_fields', '{}'))
        bobj = get_active_business(userobj)
        producto = Producto.objects.filter(pk=f.get('productoobj_id') or 0).first()
        ubicacion = Ubicacion.objects.filter(pk=f.get('ubicacionobj_id') or 0, businessobj=bobj).first()
        contada = str(f.get('cantidad_contada') or '').strip()
        if not bobj or not producto or not ubicacion or not RE_DECIMAL.match(contada) or not (f.get('motivo') or '').strip():
            return {'error': 'Producto, ubicación, cantidad contada y motivo son obligatorios'}, args, kwargs
        if f.get('id'):
            return {'error': 'Un conteo no se modifica: anúlelo y cargue otro'}, args, kwargs
        with transaction.atomic():
            ajuste = AjusteStock(businessobj=bobj, numero=siguiente_numero(AjusteStock, bobj), fecha=_fecha(f.get('fecha')) or datetime.now().date(),
                                 productoobj=producto, ubicacionobj=ubicacion, cantidad_sistema=stock_en_ubicacion(producto, ubicacion),
                                 cantidad_contada=Decimal(contada), motivo=f.get('motivo').strip()[:300])
            ajuste.registrar_carga(userobj)
            ajuste.save()
        return {'success': f'Conteo {ajuste.numero} cargado (sistema {ajuste.cantidad_sistema:,.2f} / contado {ajuste.cantidad_contada:,.2f})', 'record_id': ajuste.pk}, args, kwargs

    @precision_monetaria
    def get_stock_producto(self, *args, **kwargs) -> dict:
        bobj = get_active_business(kwargs.get('userobj'))
        producto = Producto.objects.filter(pk=kwargs.get('qdict', {}).get('producto_id') or 0).first()
        if not bobj or not producto:
            return {'error': 'Producto inexistente'}
        filas = StockUbicacion.objects.filter(businessobj=bobj, productoobj=producto, cantidad__gt=0).select_related('ubicacionobj__bodegaobj')
        return {'success': True, 'disponible': float(stock_disponible(bobj, producto)),
                'ubicaciones': [{'id': s.ubicacionobj_id, 'ubicacion': s.ubicacionobj.get_descripcion(), 'cantidad': float(s.cantidad)} for s in filas]}
