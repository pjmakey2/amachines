import logging
from django.conf import settings
from urllib.parse import quote
from django.forms import model_to_dict
from django.db.models import Sum
from datetime import datetime, timedelta
import json
from django.http import HttpRequest, QueryDict
from bs4 import BeautifulSoup
import re
import requests
from requests_pkcs12 import Pkcs12Adapter
from Sifen.models import DocumentHeader, Business
from Sifen import mng_xml
from Sifen.fl_sifen_conf import PFX, PASS
from Sifen.mng_certificate import certificate_manager
from cryptography.hazmat.primitives.serialization.pkcs12 import load_key_and_certificates
from cryptography.hazmat.primitives.serialization import Encoding, PrivateFormat, NoEncryption
from cryptography.hazmat.backends import default_backend
from Sifen import soap_schemas_xml
from Sifen.models import SoapMsg, CdcTrack, RucQr, TrackLote
from Sifen.fl_sifen_conf import URL, ROUTE_RECIBE, ROUTE_RECIBE_LOTE, \
    ROUTE_EVENTO, ROUTE_CONSULTA_LOTE, \
        ROUTE_CONSULTA_RUC, ROUTE_CONSULTA,EFDEBUG, \
        RFOLDER

class SoapSifen:
    def __init__(self, business=None):
        self.mxml = mng_xml.MngXml()
        if business:
            self.business = business
        else:
            # Fallback al último Business cargado
            self.business = Business.objects.order_by('-id').first()
        self._pfx_path = None
        self._pfx_pass = None

    def _get_certificate_credentials(self):
        """
        Obtiene las credenciales del certificado.
        Prioridad: Certificate model > fl_sifen_conf
        """
        if self._pfx_path and self._pfx_pass:
            return self._pfx_path, self._pfx_pass

        # Intentar obtener del modelo Certificate
        if self.business:
            cert_obj = certificate_manager.get_active_certificate_for_business(self.business)
            if cert_obj and cert_obj.pfx_file:
                try:
                    pfx_password = certificate_manager.decrypt_password(cert_obj.pfx_password_encrypted)
                    self._pfx_path = cert_obj.pfx_file.path
                    self._pfx_pass = pfx_password
                    logging.info(f'Usando certificado {cert_obj.nombre} para negocio {self.business.name}')
                    return self._pfx_path, self._pfx_pass
                except Exception as e:
                    logging.warning(f'Error obteniendo certificado del modelo: {e}')

        # Fallback a fl_sifen_conf
        logging.info('Usando certificado por defecto de fl_sifen_conf')
        self._pfx_path = PFX
        self._pfx_pass = PASS
        return self._pfx_path, self._pfx_pass

    def set_session(self, business=None):
        """
        Crea una sesión con el certificado apropiado.

        Args:
            business: Objeto Business para obtener certificado específico.
                      Si no se proporciona, usa self.business o fl_sifen_conf.
        """
        session = requests.Session()

        # Actualizar business si se proporciona
        if business:
            self.business = business
            self._pfx_path = None  # Reset cache
            self._pfx_pass = None

        pfx_path, pfx_pass = self._get_certificate_credentials()
        logging.info(f'set_session: URL={URL}, PFX={pfx_path}')
        session.mount(URL, Pkcs12Adapter(pkcs12_filename=pfx_path, pkcs12_password=pfx_pass))
        return session

    def send_rq(self,session, pload, SRV, fake=False):
        furl = URL+SRV
        if EFDEBUG:
            et = self.mxml.pprint_xml(self.mxml.fromstring(pload), pretty_print=True)
            logging.info(u'Send request to: {} with payload:\n {}'.format(furl, et))
        headers = {
            'User-Agent': 'facturaSend',
            'Content-Type': 'application/xml; charset=utf-8'}
        if fake:
            logging.info(
                u"""FAKE!!: Sending request to url {} 
                  with headers {}
                  paypoad {}""".format(
                    furl,
                    headers, 
                    pload.strip()
                  )
            )
            return {'exitos': 'Hecho', 'fake': True}
        return session.post(furl, data=pload, headers=headers)

    def qr_ruc(self, ruc, format=True):
        logging.info('Ejecutando qr_ruc')
        sxml = soap_schemas_xml.siConsRUC(ruc)
        session = self.set_session()
        rsp = self.send_rq(session, sxml.get('xml').decode('utf-8'), ROUTE_CONSULTA_RUC)
        if format:
            rt = self.mxml.fromstring(str(rsp.text).replace('&lt;', '<').replace('<?xml version="1.0" encoding="UTF-8"?>', ''))
            drsp = self.xtodict(rt, 'siConsRUC', clientecod=ruc)
            return drsp
        #self.update_rsp(rsp, sxml.get('sppk'), metodo='siConsRUC', clientecod=clientecod)
        return rsp

    def qr_ruc_lote(self, rucs):
        sxml = soap_schemas_xml.rEnviConsArchivoRUCRequest(rucs)
        session = self.set_session()
        rsp = self.send_rq(session, sxml.get('xml'), ROUTE_CONSULTA)
        self.update_rsp(rsp, sxml.get('sppk'), metodo='rEnviConsArchivoRUCRequest')
        return rsp        

    def qr_cdc(self, cdc):
        sxml = soap_schemas_xml.SiConsDE(cdc)
        session = self.set_session()
        rsp = self.send_rq(session, sxml.get('xml').decode('utf-8'), ROUTE_CONSULTA)
        self.update_rsp(rsp, sxml.get('sppk'), cdc=cdc, metodo='SiConsDE')
        rt = self.mxml.fromstring(str(rsp.text).replace('&lt;', '<').replace('<?xml version="1.0" encoding="UTF-8"?>', ''))
        drsp = self.xtodict(rt, 'qr_cdc')
        if drsp.get('dmsgres') == 'CDC encontrado':
            return {'exitos': drsp.get('dmsgres')}
        return {'error': drsp.get('dmsgres')}

    def qr_lote(self, lote):
        sxml = soap_schemas_xml.SiResultLoteDE(lote)
        session = self.set_session()
        rsp = self.send_rq(session, 
                           sxml.get('xml').decode('utf-8'), 
                           ROUTE_CONSULTA_LOTE)
        self.update_rsp(rsp, sxml.get('sppk'), cdc=lote, metodo='SiResultLoteDE')
        return rsp        


    def send_xde(self, cdc, fname):
        now = datetime.now()
        tnow = now.strftime('%Y-%m-%d %H:%M:%S')
        sxml = soap_schemas_xml.siRecepDE(fname)
        session = self.set_session()
        rsp = self.send_rq(session, 
                        sxml.get('xml').decode('utf-8'),
                        ROUTE_RECIBE)
        self.update_rsp(rsp, 
                        sxml.get('sppk'),
                        metodo='siRecepDE',
                        cdc=cdc
                    )
        CdcTrack.objects.create(
            cdc = cdc,
            metodo = 'siRecepDE',
            header_msg = 'EnvioDE',
            cod_rsp = 0,
            state = 'PENDIENTE',
            dfecproc = tnow,
            msg = 'PENDIENTE',
            transaccion = sxml.get('sppk'),
            qr_link='ND'
        )
        return rsp

    def send_xde_lote(self, ppks, fnames):
        logging.info('Ejecutando send_xde_lote')
        sxml = soap_schemas_xml.SiRecepLoteDE(fnames)
        session = self.set_session()
        rsp = self.send_rq(session, 
                           sxml.get('xml').decode('utf-8'), 
                           ROUTE_RECIBE_LOTE)        
        self.update_rsp(rsp, 
                        sxml.get('sppk'), 
                        cdc=sxml.get('zipfname'), metodo='SiRecepLoteDE',
                        ppks=ppks
                        )
        return rsp

    def cancelar_xde(self, cdc, motivo):
        now = datetime.now()
        tnow = now.strftime('%Y-%m-%d %H:%M:%S')
        sxml = soap_schemas_xml.CancelacionDeEvento(cdc, motivo)
        session = self.set_session()
        rsp = self.send_rq(session, 
                           sxml.get('xml').decode('utf-8'), 
                           ROUTE_EVENTO)
        self.update_rsp(rsp, 
                        sxml.get('sppk'),
                        metodo='CancelacionDeEvento',
                        cdc=cdc
                    )
        CdcTrack.objects.create(
            cdc = cdc,
            metodo = 'CancelacionDeEvento',
            header_msg = 'CancelacionDeEvento',
            cod_rsp = 0,
            state = 'PENDIENTE',
            dfecproc = tnow,
            msg = 'PENDIENTE',
            transaccion = sxml.get('sppk'),
            qr_link='ND'
        )
        return rsp        
    

    def inutilizar_nros(self, timbrado, dtipo, establecimiento, expd, start, end, motivo):
        now = datetime.now()
        sxml = soap_schemas_xml.InutilizacionDeEvento(
            timbrado, 
            str(establecimiento).zfill(3), 
            str(expd).zfill(3), 
            str(start).zfill(7), 
            str(end).zfill(7), 
            dtipo, 
            motivo
        )
        session = self.set_session()
        rsp = self.send_rq(session, 
                           sxml.get('xml').decode('utf-8'), 
                           ROUTE_EVENTO)
        self.update_rsp(rsp, 
                        sxml.get('sppk'),
                        metodo='InutilizacionDeEvento',
                    )
        return rsp
    

    def update_rsp(self, rsp, sppk, cdc=0, metodo='ND', clientecod=None, ppks=[]):
        """This gonna be used to update the soap table with the response that we got from the SET server"""
        try:
            rt = self.mxml.fromstring(str(rsp.text).replace('&lt;', '<').replace('<?xml version="1.0" encoding="UTF-8"?>', ''))
        except Exception as e:
            #print(e)
            logging.info(e)
            rt = rsp.text
            SoapMsg.objects.filter(pk=sppk)\
                    .update(
                        url_send=rsp.url,
                        headers=dict(rsp.headers),
                        cookies=dict(rsp.cookies),
                        elapsed=rsp.elapsed.total_seconds(),
                        xml_rsp=rsp.text, 
                        json_rsp={'dprotconslote': cdc } if metodo == 'SiResultLoteDE' else {},
                        msgres='Error en la peticion',
                        dprotaut=-99)
            return {'error': 'No fue posible guardar el XML'}
        else:
            SRFOLDER = soap_schemas_xml.set_sifen_response_folder()
            srs = self.mxml.save_xml(rt, f'{SRFOLDER}/rsp_{sppk}.xml')
            # SRFOLDER = soap_schemas_xml.set_sifen_response_folder()
            # with open(f'{SRFOLDER}/rsp_{sppk}.xml', 'w') as f:
            #     f.write(rt)
            if metodo == 'SiRecepLoteDE':
                print(srs, 'eyyy')
        drsp = self.xtodict(rt, metodo, clientecod=clientecod, ppks=ppks)
        # for a in rt.iter():
        #     cltag = re.sub('{(.*?)}', '', a.tag).lower()
        #     if cltag in dscp: continue
        #     vt = a.text
        #     if not vt: continue
        #     drsp[cltag] = a.text
        dtrans = drsp.get('dprotaut', 99)
        cdc = drsp.get('cdc', 0)
        if metodo == 'SiResultLoteDE':
            drsp['dprotconslote'] = cdc
        cdc = drsp.get('cdc', cdc)
        SoapMsg.objects.filter(pk=sppk)\
                .update(
                    url_send=rsp.url,
                    headers=dict(rsp.headers),
                    cookies=dict(rsp.cookies),
                    elapsed=rsp.elapsed.total_seconds(),
                    xml_rsp=rsp.text, 
                    json_rsp=drsp, 
                    msgres=drsp.get('dmsgres') if drsp.get('dmsgres') else 'ND',
                    cdc=cdc,
                    dprotaut= dtrans if dtrans else drsp.get('dcodres'))
        return {'exitos': 'Track soap actualizado'}

    def xtodict(self, rt, metodo, clientecod=None, ppks=[]):
        dscp = ['envelope', 'header', 'body']
        drsp = {}
        for a in rt.iter():
            cltag = re.sub('{(.*?)}', '', a.tag).lower()
            if cltag in dscp: continue
            vt = a.text
            if vt:
                drsp[cltag] = a.text
            if cltag == 'rresenvilotede':
                soup = BeautifulSoup(self.mxml.to_string_xml(a), 'xml')
                dFecProc = soup.find(name='dFecProc').text
                dCodRes = soup.find(name='dCodRes').text
                dMsgRes = soup.find(name='dMsgRes').text
                dProtConsLote = soup.find(name='dProtConsLote').text if soup.find(name='dProtConsLote')  else 'ND'
                logging.info(f'Lote {dProtConsLote} recibido {dMsgRes} dcodreslot {dCodRes} fecha {dFecProc}')
                TrackLote.objects.create(
                        lote=dProtConsLote,
                        estado='RECIBIDO',
                        msge=dMsgRes,
                        dcodreslot=dCodRes,
                        fecha=dFecProc
                )
                logging.info(f'Actualizando pedidos {ppks} con lote {dProtConsLote}')
                DocumentHeader.objects.filter(pk__in=ppks).update(
                    lote = dProtConsLote,
                    lote_estado = 'RECIBIDO',
                    lote_msg = dMsgRes
                )
                if dMsgRes in ['Lote no encolado para procesamiento [Error inesperado]']:
                    logging.error(f'Error inesperado al enviar lote {dProtConsLote}: {dMsgRes}')
                    DocumentHeader.objects.filter(pk__in=ppks).update(
                        lote = 0,
                        lote_estado = 'ERROR',
                        lote_msg = dMsgRes
                    )
            if cltag == 'rresenviconslotede':
                soup = BeautifulSoup(self.mxml.to_string_xml(a), 'xml')
                dFecProc = soup.find(name='dFecProc').text
                dCodResLot = soup.find(name='dCodResLot').text
                dMsgResLot = soup.find(name='dMsgResLot').text
                if re.search('en procesamiento', dMsgResLot.lower()):
                    lote = re.findall('{[0-9]+}', dMsgResLot)[0].strip('{}')
                    logging.info(f'Lote {lote} en procesamiento {dMsgResLot} dcodreslot {dCodResLot} fecha {dFecProc}')
                    TrackLote.objects.filter(lote=lote).update(
                        estado='PROCESANDO',
                        msge=dMsgResLot,
                        dcodreslot=dCodResLot,
                        fecha=dFecProc
                    )
                    logging.info(f'Actualizando DocumentHeader con lote {lote} como PROCESANDO')
                    DocumentHeader.objects.filter(lote=lote).update(
                        lote_estado = 'PROCESANDO',
                        lote_msg = dMsgResLot
                    )
                if re.search('concluido', dMsgResLot.lower()):
                    lote = re.findall('{[0-9]+}', dMsgResLot)[0].strip('{}')
                    logging.info(f'Lote {lote} concluido {dMsgResLot} dcodreslot {dCodResLot} fecha {dFecProc}')
                    TrackLote.objects.filter(lote=lote).update(
                        estado='CONCLUIDO',
                        msge=dMsgResLot,
                        dcodreslot=dCodResLot,
                        fecha=dFecProc
                    )
                    logging.info(f'Actualizando DocumentHeader con lote {lote} como CONCLUIDO')
                    DocumentHeader.objects.filter(lote=lote).update(
                        lote_estado = 'CONCLUIDO',
                        lote_msg = dMsgResLot
                    )
                for d in soup.find_all(name='gResProcLote'):
                    cdc = d.find('id').text
                    dEstRes = d.find('dEstRes').text
                    dProtAut = d.find(name='dProtAut').text if d.find(name='dProtAut') else 'ND'
                    for l in d.find_all(name='gResProc'):
                        dCodRes = l.find('dCodRes').text
                        dMsgRes = l.find('dMsgRes').text
                        if EFDEBUG:
                            logging.info(u"""
                                dFecProc = {}
                                dCodResLot = {}
                                dMsgResLot = {}
                                cdc = {}
                                dEstRes = {}
                                dCodRes = {}
                                dMsgRes = {}
                            """.format(
                                dFecProc, dCodResLot, dMsgResLot, cdc, dEstRes, dCodRes, dMsgRes
                            ))
                        logging.info(f'CDC {cdc} estado {dEstRes} msg {dMsgRes} dcodres {dCodRes} metodo {metodo}')
                        CdcTrack.objects.create(
                            cdc = cdc, 
                            metodo = metodo,
                            header_msg = dEstRes,
                            cod_rsp = dCodResLot,
                            state = dEstRes,
                            dfecproc = dFecProc,
                            msg = dMsgRes,
                            transaccion = dProtAut,
                        )
                        logging.info(f'Actualizando DocumentHeader ek_cdc={cdc} con estado {dEstRes} msg {dMsgRes}')
                        udh = {
                            'lote': lote,
                            'lote_estado': dEstRes,
                            'lote_msg': dMsgRes
                        }
                        if dEstRes == 'Aprobado':
                            udh['ek_estado'] = 'Aprobado'
                        DocumentHeader.objects.filter(ek_cdc=cdc).update(
                            **udh
                        )
                        #ek_cdc
            if cltag == 'renviconsderesponse':
                soup = BeautifulSoup(self.mxml.to_string_xml(a), 'xml')
                dFecProc = soup.find(name='dFecProc').text
                dCodRes = soup.find(name='dCodRes').text if soup.find(name='dCodRes') else 'ND'
                dMsgRes = soup.find(name='dMsgRes').text
                dProtAut = soup.find(name='dProtAut').text if soup.find(name='dProtAut') else 'ND'
                cdc = soup.find(name='DE').attrs['Id'] if soup.find(name='DE') else 'ND'
                dCarQR = soup.find(name='dCarQR').text.replace('&amp;', '&') if soup.find(name='dCarQR') else 'ND'
                if EFDEBUG:
                    logging.info("""
                       dFecProc = {}
                       dCodRes = {}
                       dMsgRes = {}
                       dProtAut = {}
                       Cdc = {}
                       dCarQR = {}
                    """.format(dFecProc,dCodRes,dMsgRes,dProtAut, cdc, dCarQR))
                logging.info(f'CDC {cdc} recibido con msg {dMsgRes} dcodres {dCodRes} fecha {dFecProc}')
                CdcTrack.objects.create(
                    cdc = cdc, 
                    metodo = metodo,
                    header_msg = dMsgRes,
                    cod_rsp = dCodRes,
                    state = dMsgRes,
                    dfecproc = dFecProc,
                    msg = dMsgRes,
                    transaccion = dProtAut,
                    qr_link=dCarQR
                )
                logging.info(f'Actualizando DocumentHeader ek_cdc={cdc} con estado {dMsgRes} msg {dMsgRes}')
                DocumentHeader.objects.filter(ek_cdc=cdc).update(
                    lote_estado = dEstRes,
                    lote_msg = dMsgRes
                )
            if cltag == 'rretenvide':
                soup = BeautifulSoup(self.mxml.to_string_xml(a), 'xml')
                logging.info(self.mxml.to_string_xml(a))
                dMsgRes = soup.find(name='dMsgRes').text
                if dMsgRes == 'XML Mal Formado.':
                    SoapMsg.objects.create(
                        method_name = metodo,
                        url_send = 'ND',
                        headers = {},
                        cookies = {},
                        elapsed = 1,
                        xml_send = '',
                        xml_rsp = '',
                        json_rsp = {},
                        msgres = dMsgRes,
                        cdc = 'ND',
                        dprotaut = 0
                    )
                    continue
                cdc = soup.find(name='Id').text if soup.find(name='Id') else 'ND'
                dDigVal = soup.find(name='dDigVal').text
                dFecProc = soup.find(name='dFecProc').text
                dEstRes = soup.find('dEstRes').text
                dProtAut = soup.find(name='dProtAut').text if soup.find(name='dProtAut') else 'ND'
                dCodRes = soup.find(name='dCodRes').text
                dCodRes = soup.find(name='dCodRes').text
                logging.info(f'CDC {cdc} recibido con msg {dMsgRes} dcodres {dCodRes} fecha {dFecProc}')
                CdcTrack.objects.create(
                    cdc = cdc, 
                    metodo = metodo,
                    header_msg = dMsgRes,
                    cod_rsp = dCodRes,
                    state = dMsgRes,
                    dfecproc = dFecProc,
                    msg = dDigVal,
                    transaccion = dProtAut,
                )
                upps = {
                    'lote_estado': dEstRes,
                    'lote_msg': dMsgRes
                }
                if dEstRes == 'Aprobado':
                    upps['ek_estado'] = 'Aprobado'
                logging.info(f'Procesando mensaje para cdc={cdc} con estado {dEstRes} msg {dMsgRes}')
                DocumentHeader.objects.filter(ek_cdc=cdc).update(
                    **upps
                )
            if cltag == 'rresenviconsruc':
                now = datetime.now()
                tnow = now.strftime('%Y-%m-%d %H:%M:%S')
                soup = BeautifulSoup(self.mxml.to_string_xml(a), 'xml')
                dcodres = soup.find(name='dCodRes').text
                dmsgres = soup.find(name='dMsgRes').text
                druccons = soup.find(name='dRUCCons').text if soup.find(name='dRUCCons') else 'ND'
                drazcons = soup.find(name='dRazCons').text if soup.find(name='dRazCons') else 'ND'
                dcodestcons = soup.find(name='dCodEstCons').text if soup.find(name='dCodEstCons') else 'ND'
                ddesestcons = soup.find(name='dDesEstCons').text if soup.find(name='dDesEstCons') else 'ND'
                drucfactelec = soup.find(name='dRUCFactElec').text if soup.find(name='dRUCFactElec') else 'ND'
                if EFDEBUG:
                    logging.info("""
                        dcodres = {}
                        dmsgres = {}
                        druccons = {}
                        drazcons = {}
                        dcodestcons = {}
                        ddesestcons = {}
                        drucfactelec = {}
                        tnow = {}
                    """.format(
                            dcodres,dmsgres,druccons,
                            drazcons,dcodestcons,ddesestcons,
                            drucfactelec,tnow
                    ))
                logging.info(f'RUC {druccons} consultado con msg {dmsgres} dcodres {dcodres} fecha {tnow}')
                RucQr.objects.create(
                    dcodres = clientecod if clientecod else dcodres,
                    dmsgres = dmsgres,
                    druccons = druccons,
                    drazcons = drazcons[0:400],
                    dcodestcons = dcodestcons,
                    ddesestcons = ddesestcons,
                    drucfactelec = drucfactelec,
                    process_date = tnow
                )
            # if cltag == 'xcontende':
            #     #a.tag = 'de_rsp'
            #     rf = re.findall('<dProtAut>[0-9]+</dProtAut>', a.text if a.text else 'ND')
            #     if rf:
            #         drsp['dprotaut'] = rf[0].replace('dProtAut', '').replace('/', '').strip('<>')
            #     rf = re.findall('Id=[0-9]{44}', a.text)
            #     if rf:
            #         drsp['cdc'] = rf[0].replace('Id=', '')
        return drsp

    def track_lote_state(self, *args, **kwargs):
        now = datetime.now()
        tnow = now.strftime('%Y-%m-%d')
        for soapobj  in SoapMsg.objects.filter(method_name='SiRecepLoteDE',fproc__icontains=tnow).order_by('-fproc')[0:2]:
            LL = soapobj.json_rsp.get('dprotconslote')
            logging.info(f'Consultando lote {LL}')
            self.qr_lote(LL)
        return {'exitos': 'Hecho'}

    def notification_interactions(self, *args, **kwargs):
        #tnow = (datetime.now() - timedelta(minutes=60)).strftime('%Y-%m-%d %H:%M:%S')
        qdict = kwargs.get('query_dict', {})
        fecha = qdict.get('fecha')
        tnow = datetime.now().strftime('%Y-%m-%d 00:00:00')
        if fecha:
            tnow = fecha
        requestshell = HttpRequest()
        ipm = imp_man_manag.ImpManag()
        cdcs = CdcTrack.objects.filter(dfecproc__gte=tnow, msg__in=['Aprobado', 'Cancelado']).values_list('cdc', flat=True).distinct('cdc')
        tnow = datetime.now().strftime('%Y-%m-%d')
        ndata = [ model_to_dict(cdcobj) for cdcobj in CdcTrack.objects.filter(dfecproc__gte=tnow).exclude(cdc__in=cdcs).order_by('-pk')]
        qdict = QueryDict(mutable=True)
        if not ndata: return {'exitos': 'Sin errores de CDC'}
        nnd = []
        cdca = []
        type_business = {
            'B2B': 'Negocio a negocio',
            'B2C': 'Negocio a cliente',
        }
        for n in ndata:
            if n.get('cdc') in cdca: continue
            try:
                pedobj = PedidosHeader.objects.get(pedidosheadermdata__cdc=n.get('cdc'))
            except:
                #print(n.get('cdc'))
                continue
            pdvobj = pedobj.puntoventaobj
            monto = pedobj.get_total_venta()
            ttp = {
                'cliente': pdvobj.nombrefactura,
                'cliente_cod': pdvobj.clientecod,
                'ruc': pdvobj.rucydv,
                'dv': pdvobj.dv,
                'es_contribuyente': 'SI' if pdvobj.es_contribuyente else 'NO',
                'tipoconobj__tipo': pdvobj.tipoconobj.tipo if pdvobj.tipoconobj else 'FALTA DEFINIR',
                'set_categoria': pdvobj.set_categoria,
                'type_business': type_business.get(pdvobj.type_business, pdvobj.type_business),
                'pedido_numero': pedobj.pedido_numero,
                'doc_fecha': pedobj.doc_fecha,
                'doc_numero': pedobj.doc_numero,
                'tipo_doc': pedobj.doc_tipo,
                'monto': pedobj.monto_total,
                'msg': n.get('msg'),
                'cdc': n.get('cdc')
            }
            nnd.append(ttp)
            cdca.append(n.get('cdc'))
        nnd = sorted(nnd, key=lambda x: x['cliente_cod'], reverse=True)
        attrs = quote(json.dumps({'cdcobjs': nnd}))
        qdict.update({'dinamic_attrs': attrs,'template': 'Sifen/CdcInteractionsUI.html'})
        requestshell.GET = qdict
        destinos = list(
                UserNotification.objects.filter(
                        operation='soap_sifen_notification_interactions', 
                        anulado_040=False)\
                    .values_list('mail', flat=True)\
                    .distinct('mail')
        )
        if settings.DEBUG:
            destinos = ['supervisor_red@rkf.com.py']
        ipm.render_view_report(module_name='imp_man.views',
                               class_name='DinamicTemplate',
                               method_name='get',
                               modulo= '[SIFEN - ACO] Documentos rechazados por la SET',
                               destinatarios=','.join(destinos),
                               requestshell=requestshell)
        return {'exitos': 'Hecho'}
