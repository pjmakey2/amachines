#coding: utf-8
import re
import arrow
from tqdm import tqdm
from datetime import datetime
from django.db.models import Q
from etrans.models import PedidosHeader, Business, CSeg
from etrans import ekuatia_gf

ek = ekuatia_gf.Egf()


def update_pedidosheader():
    onum = re.compile('^[A-Za-z]+|\.|\s+|\-')
    ruc = 80026598
    eobj = Business.objects.get(ruc=ruc)
    ahora = datetime.now()
    ahoras = ahora.strftime('%Y-%m-%d %H:%M:%S')
    PedidosHeader.objects.filter(
        Q(factura_fecha__gte='2022-01-01') |
        Q(nc_fecha__gte='2022-01-01') |
        Q(nd_fecha__gte='2022-01-01'),
        empresa='ACO'
    ).update(ruc_empresa=ruc, dv_empresa=eobj.ruc_dv)
    for pedobj in tqdm(PedidosHeader.objects.select_related('puntoventaobj')
                       .filter(
            Q(factura_numero__gt=0) |
            Q(nc_numero__gt=0) |
            Q(nd_numero__gt=0),
            aprobado_050_fecha__gte='2022-01-01',
            empresa='ACO',
            pedidosheadermdata__isnull=True
    ).order_by('pedido_numero').distinct('pedido_numero')):
        pdvobj = pedobj.puntoventaobj
        if pdvobj.extension:
            pdvobj = CPuntoventa.objects.get(clientecod=pdvobj.extension)
        fiobj = pdvobj.financtacte_set.filter(aprobado_050=True,
                                              aprobado_050_fecha__isnull=False)\
            .order_by('ultima_actualizacion').last()
        if not fiobj: continue
        error_gen = True
        while error_gen:
            codseg = str(ek.gen_codseg()).zfill(9)
            try:
                CSeg.objects.create(
                    codigo_seguridad=codseg,
                    asignado_model='ND',
                    asignado_doc=0
                )
            except:
                continue
            else:
                error_gen = False
        doc_numero = pedobj.factura_numero
        doc_fecha = pedobj.factura_fecha
        tipo_doc = '01'
        if pedobj.factura_numero:
            doc_numero = pedobj.factura_numero
            doc_fecha = pedobj.factura_fecha.strftime('%Y%m%d')
            tipo_doc = '01'
            tipo_doc_desc = u'Factura electrónica'
            app = 'VTA'
        if pedobj.nc_numero:
            doc_numero = pedobj.nc_numero
            doc_fecha = pedobj.nc_fecha.strftime('%Y%m%d')
            tipo_doc = '05'
            tipo_doc_desc = u'Nota de crédito electrónica'
            app = 'NC'
        if pedobj.nd_numero:
            doc_numero = pedobj.nd_numero
            doc_fecha = pedobj.nd_fecha.strftime('%Y%m%d')
            tipo_doc = '06'
            tipo_doc_desc = u'Nota de débito electrónica'
            app = 'ND'
        try:
            dobj = DocInventarioD.objects.get(timbrado=pedobj.timbrado,
                                            aplicacion=app,
                                            numero=doc_numero)
        except DocInventarioD.DoesNotExist:
            continue
        cdc = ek.gen_cdc(
            tipo_doc,
            pedobj.ruc_empresa,
            pedobj.dv_empresa,
            pedobj.impreso_sucursal,
            pedobj.impreso_caja,
            doc_numero,
            pdvobj.tipoconobj.codigo,
            doc_fecha,
            codseg
        )
        pedobj.impreso_usuario = dobj.impresooperador
        pedobj.documento_pago_set_cod = fiobj.documento_pago_set_cod
        pedobj.documento_pago_set = fiobj.documento_pago_set
        pedobj.factura_vencimiento = arrow.get(pedobj.factura_fecha).shift(
            days=pedobj.facturas_vencidas_dias).strftime('%Y-%m-%d')
        if fiobj.forma_pago == 'CREDITO':
            pedobj.cre_cond = fiobj.doc_pago_set_cod
            pedobj.cre_cond_desc = fiobj.doc_pago_set
            if pedobj.cre_cond == 1:
                pedobj.cre_plazo = '{} dias'.format(
                    pedobj.facturas_vencidas_dias)
        # if pedobj.documento_pago.startswith('CHEQUE'):
        #     pedobj.documento_pago_set_cod = 2
        #     pedobj.documento_pago_set = "Cheque"
        # if pedobj.documento_pago == 'CREDITO':
        #     pedobj.documento_pago_set_cod = 0
        #     pedobj.documento_pago_set = "CREDITO"
        # if pedobj.documento_pago in ['CONTADO', 'EFECTIVO', 'ND', '*_NO_TIENE_*']:
        #     pedobj.documento_pago_set_cod = 1
        #     pedobj.documento_pago_set = "Efectivo"
        pedobj.gravada_10 = pedobj.get_total_gravada_10()
        pedobj.gravada_5 = pedobj.get_total_gravada_5()
        pedobj.per_descuento = (float(pedobj.descuento)*100) / \
            float(pedobj.get_total_venta())
        pedobj.save()
        impx_doc_num='1111'
        impx_nombre='SUPERVISOR'
        impx_cargo='SISTEMA'
        if pedobj.impreso_usuario.strip() != '':
            userobj = UserProfile.objects.get(
                userobj__username=pedobj.impreso_usuario)
            impx_doc_num=userobj.cedula
            impx_nombre=userobj.nombrefantasia
            impx_cargo=userobj.puesto
        tipo_imp = 4
        tipo_imp_desc = u'Ninguno'
        if pedobj.iva_5 or pedobj.iva_10:
            tipo_imp = 1
            tipo_imp_desc = u'IVA'

        PedidosHeaderMdata.objects.create(
            pedidoheader=pedobj,
            cdc=cdc,
            cod_seg=codseg,
            tipo_doc = tipo_doc,
            tipo_doc_desc = tipo_doc_desc,            
            tipo_negocio_cod=eobj.actividadecoobj.codigo_actividad,
            tipo_negocio=eobj.actividadecoobj.codigo_actividad,
            impx_tdoc_cod=1,
            impx_tdoc_nam=u'Cédula paraguaya',
            impx_doc_num=impx_doc_num,
            impx_nombre=impx_nombre,
            impx_cargo=impx_cargo,
            pdv_innominado=pdvobj.innominado,
            pdv_pais_cod=pdvobj.pais_alfa,
            pdv_pais=pdvobj.pais,
            pdv_tipocontribuyente=pdvobj.tipoconobj.codigo,
            pdv_type_business=pdvobj.type_business,
            pdv_nombrefactura=pdvobj.nombrefactura,
            pdv_nombrefantasia=pdvobj.nombrefantasia,
            pdv_ruc=pdvobj.ruc,
            pdv_ruc_dv=pdvobj.dv,
            pdv_direccion=pdvobj.direccion,
            pdv_direccion_entrega=pdvobj.direccion_entrega,
            pdv_dir_calle_sec=pdvobj.direccion_calle_sec,
            pdv_direccion_comple=pdvobj.direccion_comple,
            pdv_numero_casa=pdvobj.numero_casa,
            pdv_numero_casa_entrega=pdvobj.numero_casa_entrega,
            pdv_dpto_cod=pdvobj.departamento_cod,
            pdv_dpto_nombre=pdvobj.departamento,
            pdv_distrito_cod=pdvobj.distrito_cod,
            pdv_distrito_nombre=pdvobj.distrito,
            pdv_ciudad_cod=pdvobj.ciudad_cod,
            pdv_ciudad_nombre=pdvobj.ciudad,
            pdv_telefono=re.sub(onum, '', pdvobj.telefono).split('/')[0] if pdvobj.telefono else 0,
            pdv_celular=re.sub(onum, '', pdvobj.telefono_entrega).split('/')[0] if pdvobj.telefono_entrega else 0,
            pdv_email=pdvobj.correos[0].get('correo') if pdvobj.correos else None,
            pdv_codigo=pdvobj.clientecod,
            tipo_ope=1,
            tipo_ope_desc=u'Venta de mercadería',
            tipo_imp=tipo_imp,
            tipo_imp_desc=tipo_imp_desc,
            op_pres_cod=2 if pedobj.sepsaobj else 1,
            op_pres=u"Operación electrónica" if pedobj.sepsaobj else u"Operación presencial",
            cre_tipo_cod=2 if pedobj.condicion_pago == 'CREDITO' else 1,
            cre_tipo=u"Crédito" if pedobj.condicion_pago == 'CREDITO' else "Contado",
            tipo_pago_cod=pedobj.documento_pago_set_cod,
            tipo_pago=pedobj.documento_pago_set,
            trans_ruc='80009699',
            cargado_fecha=ahoras,
            cargado_usuario='AUTOMATICO',
            actualizado_fecha=ahoras,
            actualizado_usuario='AUTOMATICO',
            aprobado_fecha=ahoras,
            aprobado_usuario='AUTOMATICO'
        )
