import arrow
from boltons import iterutils
from django.http import QueryDict
from django.forms import model_to_dict
from django.db.models import Q
from datetime import datetime, date
from tqdm import tqdm
from Sifen.models import Etimbrado, Enumbers, TrackLote, DocumentRecibo, DocumentHeader, Business, SoapMsg
from Sifen import  ekuatia_gf, mng_orders_mdata,rq_soap_handler
from django.core.files import File
import logging

class Eserial(object):
    def __init__(self):
        self.tnow = date.today()
        self.tnows = date.today().strftime('%Y-%m-%d')

    def create_timbrado(self, *args, **kwargs):
        logging.info('Running create_timbrado')
        userobj = args[0]
        now = datetime.now()
        qdict = kwargs.get('qdict')
        ruc = qdict.get('ruc')
        dv = qdict.get('dv')
        timbrado = qdict.get('timbrado')
        establecimiento = qdict.getlist('establecimiento')
        inicio = qdict.get('inicio')
        fcsc = qdict.get('fcsc')
        scsc = qdict.get('scsc')
        expds = qdict.getlist('expd')
        tipos = qdict.getlist('tipo')
        series = qdict.getlist('serie')
        nstarts = qdict.getlist('nstart')
        nends = qdict.getlist('nend')
        logging.info(f'Generate timbrado base on ruc={ruc} dv={dv} timbrado={timbrado} establecimiento={establecimiento} inicio={inicio} fcsc={fcsc} scsc={scsc} expd={expds} tipo={tipos} serie={series} nstart={nstarts} nends={nends}')
        etobj = Etimbrado.objects.create(
                ruc =  ruc,
                dv = dv,
                timbrado =  timbrado,
                inicio =  inicio,
                fcsc =  fcsc,
                scsc =  scsc,
                cargado_fecha =  now,
                cargado_usuario =  userobj.username,
        )
        for esta in establecimiento:
            eobj = etobj.eestablecimiento_set.create(
                establecimiento =  esta,
                expedicion = expds,
                cargado_fecha =  now,
                cargado_usuario = userobj.username
            )
            for serie, nstart, nend, tipo in tqdm(zip(series, nstarts, nends, tipos)):
                logging.info(f'Creating numbers for estable {esta} serie {serie} start on {nstart} end on {nend} of type {tipo}')
                for n in range(int(nstart), int(nend)+1):
                    eobj.enumbers_set.create(
                        tipo=tipo,
                        serie = serie,
                        numero =  n,
                        estado = 'L'
                    )
        return {'success': 'Done'}
    
    def generate_numbers_timbrado(self, timbrado, tipo, establecimiento, expds, serie, nstart, nend):
        now = datetime.now()
        etobj = Etimbrado.objects.get(timbrado=timbrado)
        eobj = etobj.eestablecimiento_set.get(
                    establecimiento =  establecimiento)
        for n in range(int(nstart), int(nend)+1):
            eobj.enumbers_set.create(
                tipo=tipo,
                serie = serie,
                numero =  n,
                estado = 'L'
            )
        return {'success': f'Done, creado numeros para tipo {tipo} del {nstart} al {nend}'}

    
    def get_last_number(self, *args, **kwargs):
        qdict = kwargs.get('qdict')
        tipo = qdict.get('tipo')
        timbrado = qdict.get('timbrado')
        establecimiento = qdict.get('establecimiento')
        eobj = Etimbrado.objects.get(timbrado=timbrado)
        timbrado = eobj.timbrado
        expobj = eobj.eestablecimiento_set.get(establecimiento=establecimiento)
        numobj = Enumbers.objects.filter(
                    expobj=expobj,estado='L',tipo=tipo)\
                .order_by('numero').first()
        if not numobj: return {'error': 'Sin numero'}
        if not eobj:
            return {'error': 'No hay numeros disponibles'}
        return {'success': 'Done', 
                'numero': numobj.numero,
                'estado': numobj.estado,
                'timbrado': timbrado,
                'establecimiento': establecimiento,
                'tipo': tipo
            }

    def get_available_numbers(self, *args, **kwargs):
        qdict = kwargs.get('qdict')
        timbrado = qdict.get('timbrado')
        establecimiento = qdict.get('establecimiento')
        tipo = qdict.get('tipo')
        #MI is for the internal movements of goods
        if tipo == 'MI':
            tipo = 'PD'
        enums = list(Enumbers.objects.filter(
                            expobj__establecimiento=establecimiento,
                            expobj__timbradoobj__timbrado=timbrado,
                            estado='L',
                            tipo=tipo)\
                        .order_by('-numero')\
                        .values_list('numero', 'tipo', 'expobj__timbradoobj__timbrado'))
        if not enums:
            return {'error': 'No hay numeros disponibles'}
        return {'success': 'Done', 
                'numeros': enums,
                'estado': 'L',
                'timbrado': timbrado,
                'establecimiento': establecimiento,
                'tipo': tipo
            }

    def set_state_numbers(self, *args, **kwargs):
        logging.info('Running set_state_numbers')
        qdict = kwargs.get('qdict')
        timbrado = qdict.get('timbrado')
        establecimiento = qdict.get('establecimiento')
        tipo = qdict.get('tipo')
        state = qdict.get('state')
        nums = qdict.getlist('numero')
        logging.info('Set used numbers to state {} '.format(state))
        Enumbers.objects.filter(
            expobj__timbradoobj__timbrado=timbrado,
            expobj__establecimiento=establecimiento,
            numero__in=nums,
            tipo=tipo).update(
                estado=state
        )
        return {'success': 'Done'}

    def get_available_timbrado(self, *args, **kwargs):
        qdict = kwargs.get('qdict')
        ruc = qdict.get('ruc')
        tps = {
            'ruc':ruc,
            #'establecimiento':establecimiento,
            'inicio__lte':self.tnows
        }
        if not ruc:
            abbr = qdict.get('abbr')
            tps['ruc'] = Business.objects.get(abbr=abbr).ruc
        eobj = Etimbrado.objects.filter(**tps).last()
        if not eobj:
            return {'error': 'El timbrado no existe'}
        eobjs = model_to_dict(eobj)
        return {'success': 'Done','tobj': eobjs}

    def set_number_typeconstrains(self, tipo):
        #Defaults attributes for the types PD and FL
        attr_date = 'factura_fecha'
        attr_number = 'factura_numero'
        order_invoice = ('repartoobj__reparto_numero', 'prof_number')
        pps = {'factura_numero__isnull': True,
                'anulado_040': False,
                'repartoobj__isnull': False}
        if tipo == 'NC':
            pps = {'nc_numero__isnull': True,
                   'anulado_040': False}
            attr_date = 'nc_fecha'
            attr_number = 'nc_numero'
            order_invoice = ('prof_number', )
        if tipo == 'ND':
            pps = {'nd_numero__isnull': True,
                   'anulado_040': False,
                   }
            attr_date = 'nd_fecha'
            attr_number = 'nd_numero'
            order_invoice = ('prof_number', )
        if tipo in ['AF', 'SE', 'MI']:
            pps = {'factura_numero__isnull': True,
                   'anulado_040': False,
                   }
            attr_date = 'factura_fecha'
            attr_number = 'factura_numero'
            order_invoice = ('prof_number', )            
        return {
            'attr_date': attr_date,
            'attr_number': attr_number,
            'pps': pps,
            'order_invoice': order_invoice
        }

    def check_block_status(self, bbs):
        if not DocumentHeader.objects.filter(
                bloqueobj__pk__in=bbs, 
                anulado_040=False, 
                factura_numero__isnull=True):
            return {'error': 'No hay pedidos que asignar'}
        return {'success': 'OK'}
        # pps.update({'bloqueobj__pk': bbs})
        # pedobjs = DocumentHeader.objects.filter(**pps).order_by('repartoobj__reparto_numero', 'reparto_prioridad')

    def set_number_receive(self, *args, **kwargs):
        logging.info('Running set_numbert')
        qdict = kwargs.get('qdict')
        ahora = date.today()
        ahoraf = ahora.strftime('%Y-%m-%d')
        invoicedate = ahora
        ruc = qdict.get('ruc')
        establecimiento = qdict.get('establecimiento')
        expd = qdict.get('expd')
        prof_number = qdict.getlist('prof_number')
        tipo = qdict.get('tipo')
        recobjs = DocumentRecibo.objects.filter(prof_number__in=prof_number, doc_tipo=tipo, doc_numero__isnull=True).order_by('pk')
        if not recobjs: return {'error': 'No se puede asignar numero de documentos a los recibos'}
        numeros_necesarios = recobjs.count()
        qed = QueryDict(mutable=True)
        logging.info('Get available timbrado for {} and establishment {}'.format(
            ruc, establecimiento
        ))
        timp = {'ruc': ruc,'establecimiento': establecimiento }
        timbradoobj = self.get_available_timbrado(qdict=timp)
        if timbradoobj.get('error'):
            raise ValueError(timbradoobj.get('error'))
        timbradoobj = timbradoobj.get('tobj')
        serie = timbradoobj.get('serie')
        vigencia = timbradoobj.get('inicio')
        fcsc = timbradoobj.get('fcsc')
        scsc = timbradoobj.get('scsc')
        venct = timbradoobj.get('vencimiento')
        enumobjs = self.get_available_numbers(qdict={
            'timbrado': timbradoobj.get('timbrado'),
            'establecimiento': establecimiento,
            'tipo': tipo
        })
        if enumobjs.get('error'):
            raise ValueError(enumobjs.get('error'))
        
        if len(enumobjs.get('numeros')) < numeros_necesarios:
            raise ValueError('IMPOSIBLE GENERAR LA ORDEN DE IMPRESION, LA CANTIDAD DE NUMEROS ES INSUFICIENTE')
        impreso_caja = expd
        impreso_sucursal = establecimiento
        numbers = enumobjs.get('numeros')
        aorde = QueryDict(mutable=True)
        tcount = 0
        for pedobj in pedobjs:
            # if pedobj.pedidos_set.all().count() == pedobj.pedidos_set.filter(anulado_040=True).count():
            #     continue
            enum, tipo, timbrado = numbers.pop()
            if not enum:
                return {'error': 'No hay numeros disponibles'}
            
            vencimiento = venct
            logging.info('Set number {} for type {} and attrib doc_numero'.format(
                enum, tipo
            ))
            pedobj.doc_fecha = invoicedate
            pedobj.doc_numero = enum
            #pedobj.doc_op = tipo
            #pedobj.doc_tipo = pedobj.pedido_tipo
            # pedobj.ek_serie =  serie
            # pedobj.ek_timbrado = timbrado
            # pedobj.ek_timbrado_vencimiento = vencimiento
            # pedobj.ek_timbrado_vigencia = vigencia
            #pedobj.doc_expedicion = impreso_caja
            pedobj.doc_establecimiento = impreso_sucursal
            pedobj.impx_nombre = 'GENERICO'
            #pedobj.ek_idcsc = fcsc
            #pedobj.ek_idscsc = scsc
            #pedobj.doc_entregado = pedobj.doc_fecha.strftime('%Y-%m-%d %H:%M:%S')
            pedobj.save()
            aorde.update({'prof_number': pedobj.prof_number})
            tcount += 1
            qed.update({'numero': enum})
        qed.update({
            'timbrado': timbradoobj.get('timbrado'),
            'establecimiento': establecimiento,
            'ruc': ruc,
            'tipo': tipo,
            'expd': expd,
            'state': 'R'
        })
        aorde.update({
            'ruc': ruc
        })
        self.set_state_numbers(qdict=qed)
        
        return {'success': 'Done', 
                'affected_numbers': qed,
                'affected_orders': aorde,
                'timbradoobj': timbradoobj,
                }



    def set_number(self, *args, **kwargs):
        logging.info('Running set_numbert')
        qdict = kwargs.get('qdict')
        ahora = date.today()
        ahoraf = ahora.strftime('%Y-%m-%d')
        invoicedate = ahora
        ruc = qdict.get('ruc')
        timbrado = qdict.get('timbrado')
        establecimiento = qdict.get('establecimiento')
        expd = qdict.get('expd')
        prof_number = qdict.getlist('prof_number')
        tipo = qdict.get('tipo')
        sign_document = qdict.get('sign_document', True)
        #viene por query dict, pero es un proceso interno despues del ruteo
        #por eso ya esta como lista
        recobjs = DocumentHeader.objects.filter(prof_number__in=prof_number, doc_tipo=tipo, doc_numero__isnull=True).order_by('prof_number')
        if not recobjs: return {'error': 'No se puede asignar numero de documentos a los pedidos'}
        numeros_necesarios = recobjs.count()
        logging.info('We need upto {} numbers for type {}'.format(numeros_necesarios, tipo))
        qed = QueryDict(mutable=True)
        logging.info('Get available timbrado for {} and establishment {}'.format(
            ruc, establecimiento
        ))
        timp = {'ruc': ruc,'establecimiento': establecimiento }
        
        #timbradoobj = self.get_available_timbrado(qdict=timp)
        timbradoobj = Etimbrado.objects.get(timbrado=timbrado)
        
        # if timbradoobj.get('error'):
        #     raise ValueError(timbradoobj.get('error'))
        
        serie = timbradoobj.serie
        vigencia = timbradoobj.inicio
        fcsc = timbradoobj.fcsc
        scsc = timbradoobj.scsc
        venct = timbradoobj.vencimiento
        logging.info(f'Get available numbers for timbrado {timbradoobj.timbrado} establishment {establecimiento} type {tipo}')

        enumobjs = self.get_available_numbers(qdict={
            'timbrado': timbradoobj.timbrado,
            'establecimiento': establecimiento,
            'tipo': tipo
        })
        logging.info('Response of get_available_numbers timbrado {} estaclemiento {} tipo {}'.format(
            enumobjs.get('timbrado'),
            enumobjs.get('establecimiento'),
            enumobjs.get('tipo'),
        ))
        if enumobjs.get('error'):
            raise ValueError(enumobjs.get('error'))
        
        if len(enumobjs.get('numeros')) < numeros_necesarios:
            raise ValueError('IMPOSIBLE GENERAR LA ORDEN DE IMPRESION, LA CANTIDAD DE NUMEROS ES INSUFICIENTE')
        impreso_caja = expd
        impreso_sucursal = establecimiento
        numbers = enumobjs.get('numeros')
        aorde = QueryDict(mutable=True)
        tcount = 0
        for recobj in recobjs:
            # if pedobj.pedidos_set.all().count() == pedobj.pedidos_set.filter(anulado_040=True).count():
            #     continue
            enum, tipo, timbrado = numbers.pop()
            if not enum:
                return {'error': 'No hay numeros disponibles'}
            
            vencimiento = venct
            logging.info('Set number {} for type {} and attrib doc_numero'.format(
                enum, tipo
            ))
            recobj.doc_fecha = invoicedate
            recobj.doc_numero = enum
            #recobj.doc_op = tipo
            #recobj.doc_tipo = recobj.pedido_tipo
            recobj.ek_serie =  serie
            recobj.ek_timbrado = timbrado
            recobj.ek_timbrado_vencimiento = vencimiento
            recobj.ek_timbrado_vigencia = vigencia
            recobj.doc_expedicion = impreso_caja
            recobj.doc_establecimiento = impreso_sucursal
            recobj.impx_nombre = 'GENERICO'
            recobj.ek_idcsc = fcsc
            recobj.ek_idscsc = scsc
            recobj.save()
            aorde.update({'prof_number': recobj.prof_number})
            tcount += 1
            qed.update({'numero': enum})
        qed.update({
            'timbrado': timbradoobj.timbrado,
            'establecimiento': establecimiento,
            'ruc': ruc,
            'tipo': tipo,
            'expd': expd,
            'state': 'R'
        })
        aorde.update({
            'ruc': ruc
        })
        self.set_state_numbers(qdict=qed)
        if sign_document:
            self.set_data_ekuatia(qdict=aorde)
        return {'success': 'Done', 
                'affected_numbers': qed,
                'affected_orders': aorde,
                'timbradoobj': timbradoobj,
                }
    
    def set_data_ekuatia(self, *args, **kwargs):
        logging.info('Sign orders to send it to the external system')
        morm = mng_orders_mdata.Morders()
        ek = ekuatia_gf.Egf()
        qdict = kwargs.get('qdict')
        peds = qdict.getlist('prof_number')
        ruc = qdict.get('ruc')
        msge = ['<ul>']
        for ped in peds:
            rsp = morm.generate_pmeta(qdict={'prof_number': ped, 'ruc': ruc})
            if rsp.get('error'): 
                logging.error(rsp.get('msg'))
                msge.append(rsp.get('msg'))
                continue
            #print(ped)
            exml = ek.gen_xml_ekuatia(qdict={'prof_number': ped})
            sixml = ek.sign_xml(exml.get('xml_file'), 'XMLSIGNER', ped)
            pedobj = DocumentHeader.objects.get(prof_number=ped)
            if not pedobj.ek_xml_ekua:
                pedobj.ek_xml_ekua = True
                pedobj.ek_xml_file = File(open(exml.get('xml_file'), 'rb'), name=exml.get('xml_file').split('/')[-1])
                pedobj.ek_xml_file_signed = File(open(sixml.get('xmlsigner_file'), 'rb'),name=sixml.get('xmlsigner_file').split('/')[-1])
                pedobj.ek_qr_link = sixml.get('qpar')
                pedobj.ek_qr_img = File(open(sixml.get('qri'), 'rb'), name=sixml.get('qri').split('/')[-1])
                pedobj.save()
                # DocumentHeader.objects.filter(
                #     prof_number=pedobj.prof_number)\
                #     .update(
                #         ek_xml_ekua = True,
                #         ek_xml_file = exml.get('xml_file'),
                #         ek_xml_file_signed = sixml.get('xmlsigner_file'),
                #         ek_qr_link = sixml.get('qpar'),
                #         ek_qr_img = sixml.get('qri')
                # )
        return {'success': 'Done'}

    def check_consistency_numbers(self, timbrado, ttype, show_p=False):
        rsp = []
        for pedobj in tqdm(DocumentHeader.objects\
                                        .filter(ek_timbrado=timbrado, pedido_tipo=ttype)\
                                        .order_by('doc_numero')):
            ccc = DocumentHeader.objects\
                                .filter(ek_timbrado=timbrado,
                                        pedido_tipo=ttype, 
                                        doc_numero=pedobj.doc_numero)\
                                .count()
            if show_p:
                logging.info(
                    pedobj.doc_numero, pedobj.pedido_tipo, pedobj.ek_estado, pedobj.cod_seg, ccc
                )
            if ccc > 1:
                rsp.append({'error': 'Verificar el pedido {} tienen el numero de coumento {} tipo {} DUPLICADO'.format(
                                        pedobj.prof_number, pedobj.doc_numero, pedobj.pedido_tipo

                )})
        return rsp
                

    def generate_pending_cdc_console(self, pps={}, ruc=None, timbrado=None):
        """This is a strictly use case for the ipython console.
           We already define a static parameters for pass to the method send_pending_cdc
           DO NOT USE THIS FROM THE FRONT-END
        """
        dpps = {'ek_timbrado': timbrado}
        if pps:
            dpps.update(pps)
        return self.generate_pending_cdc(dpps, ruc=ruc)

    def generate_pending_cdc(self, pps, ruc=None):
        """This is explicitly to test the signing and sending method
           This should be doing it before the generation process of the invoice
        """
        logging.info('Running send_pending_cdc filter {}'.format(pps))
        tks = ['Aprobado', 'Cancelado', 'Inutilizado']
        DocumentHeader.objects.filter(**pps)\
                        .exclude(ek_estado__in=tks)\
                        .update(ek_xml_ekua=False, ek_xml_file=None, ek_xml_file_signed=None, ek_cod_seg=0)
        aorde = QueryDict(mutable=True)
        aorde.update({'ruc': ruc})
        for e in list(
            DocumentHeader.objects.filter(**pps)\
                                .exclude(ek_estado__in=tks)\
                                .values_list('prof_number', flat=True)\
                                .order_by('pdv_codigo', 'doc_numero')
            ):
            aorde.update({'prof_number': e})
        self.set_data_ekuatia(qdict=aorde)
        return {'success': 'Datos xml firmados', 'prof_number': aorde.getlist('prof_number')}

    def send_pending_signedxml(self, orders):
        rqsoap = rq_soap_handler.SoapSifen()
        # if len(orders) == 1:
        #     order = orders[0]
        #     docobj = DocumentHeader.objects.get(prof_number=order)
        #     rsp = rqsoap.send_xde(docobj.ek_cdc, docobj.ek_xml_file_signed.path)
        #     return rsp
        xml_file_signed = [ (d.pk ,d.ek_xml_file_signed.path) for d in DocumentHeader.objects\
                                    .filter(prof_number__in=orders, ek_xml_file_signed__isnull=False)\
                                    .order_by('doc_tipo', 'doc_numero') ]
        for xmlff in iterutils.chunked(xml_file_signed, 20):
            xfnames = [ x[1] for x in xmlff ]
            ppks = [ x[0] for x in xmlff ]
            rsp = rqsoap.send_xde_lote(ppks, xfnames)
        return {'success': 'Done'}


    def track_lotes(self, *args, fdate=None, **kwargs):
        now = arrow.now()
        nows = now.strftime('%Y-%m-%d')
        if fdate:
            nows = fdate
        rqsoap = rq_soap_handler.SoapSifen()
        pps = {
            'fecha__gte': nows,
            'estado': 'CONCLUIDO',
            'lote__isnull': False,
        }
        q = kwargs.get('qdict', {})
        if q.get('remove_estado'):
            pps.pop('estado')
            pps.update({'estado__in': ['RECIBIDO', 'PROCESANDO', 'CONCLUIDO']})
        logging.info('Tracking lotes with params {}'.format(pps))
        lotes = list(TrackLote.objects.filter(**pps).values_list('lote', flat=True))
        if q.get('last'):
            lotes = lotes[-int(q.get('last')):]
        for soapobj in SoapMsg.objects.filter(method_name='SiRecepLoteDE',fproc__gte=nows):
            lote = soapobj.json_rsp.get('dprotconslote')
            if lote == None: continue
            if lote in lotes: 
                logging.info('El proceso para el lote {} esta concluido'.format(lote))
                continue
            logging.info('Track lote {}'.format(lote))
            rsp = rqsoap.qr_lote(lote)
        return {'success': 'Done'}

    def send_result_lote(self):
        rqsoap = rq_soap_handler.SoapSifen()
        rqsoap.notification_interactions()

    def qr_ruc(self, ruc, business=None):
        rqsoap = rq_soap_handler.SoapSifen(business=business)
        rsp = rqsoap.qr_ruc(ruc)
        return rsp
