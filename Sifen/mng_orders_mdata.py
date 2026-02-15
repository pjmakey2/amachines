#coding: utf-8
from django.db.models import F
import logging
import re
from datetime import datetime
from Sifen import mng_gmdata
from Sifen.models import CdcTrack
from Sifen.models import DocumentHeader
from Sifen.models import Business, CSeg

class Morders:
    def track_order_state(self, *args, **kwargs):
        qdict = kwargs.get('qdict', {})
        fecha = qdict.get('fecha')
        if not fecha:
            now = datetime.now()
            fecha = now.strftime('%Y-%m-%d')
        for cdcobj in CdcTrack.objects.filter(dfecproc__icontains=fecha, metodo='SiResultLoteDE').order_by('dfecproc'):
            if cdcobj.msg == 'Aprobado':
                DocumentHeader.objects.filter(cdc=cdcobj.cdc, ek_estado__isnull=True).update(
                    ek_transacion = cdcobj.transaccion,
                    ek_estado = cdcobj.msg,
                    ek_date = cdcobj.dfecproc
                )
        return {'exitos': 'Hecho'}


    def generate_pmeta(self, *args, **kwargs):
        """Generate data that is need it by the SET"""
        logging.info('Running generate_pmeta')
        onum = re.compile('^[A-Za-z]+|\.|\s+|\-')
        ahoran = datetime.now()
        ahoras = ahoran.strftime('%Y-%m-%d')
        qdict = kwargs.get('qdict')
        ped_nu = qdict.get('prof_number')
        ruc = qdict.get('ruc')
        eobj = Business.objects.get(ruc=ruc)
        pedobj = DocumentHeader.objects.get(prof_number=ped_nu)
        mgdata = mng_gmdata.Gdata()
        error_gen = False
        # codseg = int(pedobj.ek_cod_seg)
        # if codseg == 0:
        #     error_gen = True
        error_gen = True
        while error_gen:
            codseg = str(mgdata.gen_codseg()).zfill(9)
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
            logging.info('Generate cod_seg {}'.format(codseg))
        
        if pedobj.doc_tipo == 'FE':
            tipo_doc = '01'
            tipo_doc_desc = u'Factura electrónica'
        if pedobj.doc_tipo == 'NC':
            tipo_doc = '05'
            tipo_doc_desc = u'Nota de crédito electrónica'
        if pedobj.doc_tipo == 'ND':
            tipo_doc = '06'
            tipo_doc_desc = u'Nota de débito electrónica'
        if pedobj.doc_tipo == 'AF':
            tipo_doc = '04'
            tipo_doc_desc = u' Autofactura electrónica'
            
        cdc, cdc_dv = mgdata.gen_cdc(
            tipo_doc, 
            eobj.ruc,
            eobj.ruc_dv,
            pedobj.doc_establecimiento,
            pedobj.doc_expedicion,
            pedobj.doc_numero,
            eobj.contribuyenteobj.codigo,
            pedobj.doc_fecha,
            codseg
        )
        logging.info('Set CDC {}'.format(cdc))
        if pedobj.impx_nombre == 'ND' or pedobj.impx_nombre == 'GENERICO' or not pedobj.impx_nombre:
            pedobj.impx_doc_num = '00000000'
            pedobj.impx_nombre = 'GENERICO'
            pedobj.impx_cargo = 'IMPRESOR'
        pedobj.doc_tipo_imp = 4
        pedobj.doc_tipo_imp_desc =  u'Ninguno'
        if pedobj.doc_i5 or pedobj.doc_i10:
            pedobj.doc_tipo_imp = 1
            pedobj.doc_tipo_imp_desc =  u'IVA'
        correos = []
        if not pedobj.doc_tipo_ope:
            pedobj.doc_tipo_ope =  1
            pedobj.doc_tipo_ope_desc =  u'Venta de mercadería'
            pedobj.doc_op_pres_cod = 1
            pedobj.doc_op_pres = u"Operación presencial"
        pedobj.ek_cdc = cdc
        pedobj.ek_cdc_dv = cdc_dv
        pedobj.ek_cod_seg = codseg
        pedobj.doc_tipo_cod = tipo_doc
        pedobj.doc_tipo_desc = tipo_doc_desc
        #pedobj.tipo_negocio_cod = eobj.actividadecoobj.codigo_actividad
        #pedobj.tipo_negocio =  eobj.actividadecoobj.codigo_actividad
        pedobj.impx_tdoc_cod = 1
        pedobj.impx_tdoc_nam = u'Cédula paraguaya'
        #pedobj.doc_cre_tipo_cod = 2 if pedobj.forma_pago_set == 'CREDITO' else 1
        #pedobj.cre_tipo = u"Crédito" if pedobj.forma_pago_set == 'CREDITO' else "Contado"
        pedobj.save()
        if pedobj.doc_tipo in ['NC', 'ND']:
            #Set the relationship of the document
            #If this faild the process can not go on
            rpedobj = DocumentHeader.objects.filter(prof_number=pedobj.doc_loop_link)
            if not rpedobj:
                msg = u'<li>[DE] El pedido {} del cliente {}[{}] no tiene una relacion valida {}</li>'.format(
                                pedobj.prof_number,
                                pedobj.pdv_nombrefactura,
                                pedobj.pdv_codigo,
                                pedobj.doc_loop_link
                            )
                return {'error': 'Sin relacion valida', 'msg': msg}
            rpedobj = rpedobj.last()
            pedobj.doc_relacion_cod = 1
            pedobj.doc_relacion = 'Electrónico'
            pedobj.doc_relacion_cdc = rpedobj.ek_cdc
            pedobj.doc_relacion_timbrado = rpedobj.ek_timbrado
            pedobj.doc_relacion_establecimiento = rpedobj.doc_establecimiento
            pedobj.doc_relacion_expedicion = rpedobj.doc_expedicion

            if rpedobj.doc_tipo in ['FE', 'FL']:
                pedobj.doc_relacion_tipo_cod = 1
                pedobj.doc_relacion_tipo = u'Factura'
            if rpedobj.doc_tipo == 'NC':
                pedobj.doc_relacion_tipo_cod = 2
                pedobj.doc_relacion_tipo = u'Nota de crédito'
            if rpedobj.doc_tipo == 'ND':
                pedobj.doc_relacion_tipo_cod = 3
                pedobj.doc_relacion_tipo = u'Nota de débito'
            if rpedobj.doc_tipo == 'AF':
                pedobj.doc_relacion_tipo_cod = 4
                pedobj.doc_relacion_tipo = u'Nota de remisión'
            pedobj.doc_relacion_fecha = rpedobj.doc_fecha.strftime('%Y-%m-%d')
            pedobj.save()
        return {'exitos': 'Hecho'}

    def compare_order_xml(self, *args, **kwargs):
        qdict = kwargs.get('qdict')
        prof_number = qdict.get('prof_number')
        pedobj = DocumentHeader.objects.get(prof_number=prof_number)
        attr_cant = 'cantidad'
        if pedobj.nc_tipo == 'RS':
            attr_cant = 'cantidad_devolucion'        
        attr_precio = 'precio_unitario'
        attr_descuento = 'descuento'
        attr_exenta = 'exenta'
        attr_gravada_5 = 'gravada_5'
        attr_gravada_10 = 'gravada_10'        
        pdvobj = pedobj.puntoventaobj
        if pdvobj.extension:
            pdvobj = CPuntoventa.objects.get(clietnecod=pdvobj.extension)        
        correos = self.get_pdv_correo(pedobj, pdvobj)
        bdata = {
            prof_number: {
                'receptor': [
                    {
                        'iTiContRec': pdvobj.tipoconobj.codigo,
                        'dRucRec': pdvobj.ruc,
                        'dDVRec': pdvobj.dv,
                        'dNomRec': pdvobj.nombrefactura,
                        'dNomFanRec': pdvobj.nombrefantasia,
                        'dDirRec': pdvobj.direccion,
                        'dNumCasRec': pdvobj.numero_casa,
                        'dTelRec': pdvobj.telefono,
                        'dCelRec': pdvobj.telefono_entrega,
                        'dEmailRec': correos[0] if correos else None,
                        'dCodCliente': pdvobj.clientecod
                    }
                ],
                'items': [],
                'footer': []
            }
        }
        for pobj in pedobj.pedidos_set.filter(anulado_040=False).exclude(articulo_cod=90000).order_by('pk'):
            cantidad = getattr(pobj, attr_cant)
            precio_unitario = getattr(pobj, attr_precio)
            exenta = getattr(pobj, attr_exenta)
            gravada_5 = getattr(pobj, attr_gravada_5)
            gravada_10 = getattr(pobj, attr_gravada_10)
            descuento = getattr(pobj, attr_descuento)
            if pedobj.doc_op == 'RS':
                if exenta:
                    exenta = precio_unitario*cantidad
                if gravada_5:
                    gravada_5 = precio_unitario*cantidad
                if gravada_10:
                    gravada_10 = precio_unitario*cantidad
            if pobj.per_descuento == 100:
                setattr(pobj, attr_exenta,0)
                setattr(pobj, attr_gravada_5,0)
                setattr(pobj, attr_gravada_10,0)
            totopeitem = float((pobj.precio_unitario-pobj.descuento)*pobj.cantidad)
            dad = {
                'dDesProSer': pobj.articulo_cod,
                'cUniMed': pobj.articulo_unidad_medida,
                'dDesUniMed': pobj.articulo_unidad_medida_desc,
                'dCantProSer': cantidad,
                'dPUniProSer': precio_unitario,
                'dTotBruOpeItem': precio_unitario*cantidad,
                'dDescItem': pobj.descuento if pobj.descuento else 0,
                'dTotOpeItem': totopeitem,
            }
            if pobj.iva_5 or pobj.iva_10:
                dad['iAfecIVA'] = 1
                dad['dDesAfecIVA'] = 'Gravado IVA'
                dad['dPropIVA'] = 100
                if pobj.iva_5:
                    base_g_5 = (totopeitem*(100/100)/1.05)
                    dad['dTasaIVA'] = 5
                    dad['dBasGravIVA'] = base_g_5
                    dad['dLiqIVAItem'] = pobj.iva_5 if not pobj.bonifica else 0
                if pobj.iva_10:
                    base_g_10 = (totopeitem*(100/100)/1.1)
                    dad['dTasaIVA'] = 10
                    dad['dBasGravIVA'] = base_g_10
                    dad['dLiqIVAItem'] = pobj.iva_10 if not pobj.bonifica else 0
            if pobj.exenta:
                dad['iAfecIVA'] = 3
                dad['dDesAfecIVA'] = 'Exento'
                dad['dPropIVA'] = 0
                dad['dTasaIVA'] = 0
                dad['dBasGravIVA'] = 0
                dad['dLiqIVAItem'] = 0
            if pobj.lote and pobj.venc:
                dad['dNumLote'] = pobj.lote[-1]
                dad['dVencMerc'] = pobj.venc[-1]
                dad['dNSerie'] = 0
                dad['dNumPedi'] = pobj.pedidoheader.prof_number
                dad['dNumSegui'] = pobj.pedidoheader.repartoobj_id
            bdata[prof_number]['items'].append(dad)
        descuento = sum(pedobj.get_total_descuento())
        dsub = {
            'dSub5': pedobj.get_total_iva_5(),
            'dSub10': pedobj.get_total_iva_10(),
            'dTotOpe': pedobj.get_total_venta(),
            'dTotDesc': descuento,
            'dTotDescGlotem': pedobj.descuento_global,
            'dTotAntItem': 0,
            'dTotAnt': 0,
            'dPorcDescTotal': 0,
            'dDescTotal': pedobj.descuento_global+descuento,
            'dAnticipo': 0,
            'dRedon': 0,
            'dTotGralOpe': pedobj.get_total_venta(),
            'dIVA5': pedobj.get_total_iva_5(),
            'dIVA10': pedobj.get_total_iva_10(),
            'dTotIVA': pedobj.get_total_iva(),
        }
        
        b5 = 0
        g5 = float(pedobj.get_total_gravada_5())
        if g5:
            b5 = (g5*(100/100)/1.05)
        dsub['dBaseGrav5'] = b5
        b10 = 0
        g10 = float(pedobj.get_total_gravada_10())
        if g10:
            b10 = (g10*(100/100)/1.1)        
        dsub['dBaseGrav10'] = b10
        dsub['dTBasGraIVA'] = b5+b10
        bdata['footer'].append(dsub)
