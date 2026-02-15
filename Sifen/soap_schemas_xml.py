from Sifen import mng_xml
import logging
import base64
import hashlib
import os
import zipfile
from Sifen.xml_signer import ESigner
from Sifen.models import SendBulk
from Sifen.fl_sifen_conf import RFOLDER, SOAP_NAME_SPACE, SIFEN_NAME_SPACE, EVERSION, XSI_NAME_SPACE
from datetime import datetime
import lxml
from Sifen.models import SoapMsg

mxml = mng_xml.MngXml()

def set_soap_folder():
    now = datetime.now()
    tnow = now.strftime('%Y%m%d')
    ROOTFOLDER = '{}/soaps/{}'.format(RFOLDER, tnow)
    try:os.mkdir('{}/soaps/'.format(RFOLDER))
    except:pass
    try:os.mkdir(ROOTFOLDER)
    except:pass
    return ROOTFOLDER

def set_sifen_response_folder():
    now = datetime.now()
    tnow = now.strftime('%Y%m%d')
    SRFOLDER = f'{RFOLDER}/sifen_response/{tnow}'
    try:os.mkdir(f'{SRFOLDER}/sifen_response/')
    except:pass
    try:os.mkdir(SRFOLDER)
    except:pass
    return SRFOLDER


def track_soap_msg(method_name, cxml):
    sobj = SoapMsg.objects.create(method_name=method_name, xml_send=cxml, json_rsp={}, dprotaut=0)
    return sobj.pk

def save_bulk_de(zipfname, lotefname, fname, fnames):
    tnow = datetime.now()
    sendobj = SendBulk.objects.create(
        zipfname = zipfname,
        xmlfname = lotefname,
        soapfname = fname,
        cargado_fecha = tnow
    )
    for f in fnames:
        sendobj.sendbulkdetail_set.create(
            xmlfile=f,
            cargado_fecha = tnow
        )
    return {'exitos': 'Save sendbulk tracking'}

def SiRecepLoteDE(fnames):
    ROOTFOLDER = set_soap_folder()
    ele, header, sbody = mxml.get_soap_schema()    
    renviolote = mxml.create_SubElement(sbody, 'rEnvioLote', xmlns="http://ekuatia.set.gov.py/sifen/xsd")
    did = mxml.create_SubElement(renviolote, 'dId')
    dxde = mxml.create_SubElement(renviolote, 'xDE')
    rlotede = mxml.set_eroot('rLoteDE')
    cdcs = []
    for a in fnames:
        cdcs.append(os.path.basename(a).split('_')[0])
        fsxm = mxml.parse_xml(a)
        rlotede.append(fsxm)
    cdcs.sort()
    cc = str.encode('^'.join(cdcs))
    hfname = hashlib.md5(cc).hexdigest()
    lotefname = '{}/{}.xml'.format(ROOTFOLDER, hfname)
    zipfname = '{}/{}.zip'.format(ROOTFOLDER, hfname)
    mxml.save_xml(rlotede, lotefname)
    zipf = zipfile.ZipFile(zipfname, 'w', zipfile.ZIP_DEFLATED)
    zipf.write(lotefname)
    zipf.close()
    with open(zipfname, "rb") as f:
        bytes = f.read()
        encoded = base64.b64encode(bytes)
        dxde.text = encoded
    sppk = track_soap_msg('SiRecepLoteDE', mxml.to_string_xml(ele))
    did.text = str(sppk)
    fname = '{}/SiRecepLoteDE_{}_soap.xml'.format(ROOTFOLDER, sppk)
    logging.info('Guardando envio soap en {}'.format(fname))
    mxml.save_xml(ele, fname)
    save_bulk_de(zipfname, lotefname, fname, fnames)
    return {'xml': mxml.to_string_xml(ele), 'sppk': sppk, 'zipfname': zipfname }

def siRecepDE(fname):
    ROOTFOLDER = set_soap_folder()
    if isinstance(fname, str) or isinstance(fname, unicode):
        xde = mxml.parse_xml(fname)
    if isinstance(fname, lxml.etree._Element):
        xde = fname
        fname = '{}/{}.xml'.format(ROOTFOLDER, xde.getchildren()[1].attrib.get('Id'))
    xmlns = {
        'env': SOAP_NAME_SPACE.strip('{}'),
        # 'xsd': SIFEN_NAME_SPACE.strip('{}')
    }
    ele = mxml.set_eroot(SOAP_NAME_SPACE+'Envelope', nsmap=xmlns)
    mxml.create_SubElement(ele, SOAP_NAME_SPACE+'Header')    
    sbody = mxml.create_SubElement(ele, SOAP_NAME_SPACE+'Body')    
    renvide = mxml.create_SubElement(sbody, 'rEnviDe', xmlns="http://ekuatia.set.gov.py/sifen/xsd")    
    did = mxml.create_SubElement(renvide, 'dId')
    #mxml.create_SubElement(renvide, 'iAmb', _text=1)
    dxde = mxml.create_SubElement(renvide, 'xDE')
    dxde.append(xde)
    sppk = track_soap_msg('siRecepDE', mxml.to_string_xml(ele))
    did.text = str(sppk)
    mxml.save_xml(ele, fname.replace('.xml', '_{}_soap.xml'.format(sppk)))
    mxml.save_xml(renvide, fname.replace('.xml', '_xde.xml'))
    #sele = unicode(mxml.clean_up_string(mxml.to_string_xml(ele, xml_declaration=True)), 'utf-8')
    cdc = fname.split('/')[-1].replace('_verified_signed.xml', '')
    return {'xml': mxml.to_string_xml(ele), 'sppk': sppk, 'cdc': cdc}

def siConsRUC(ruc):
    ROOTFOLDER = set_soap_folder()
    xmlns = {
        'env': SOAP_NAME_SPACE.strip('{}'),
        'xsd': SIFEN_NAME_SPACE.strip('{}')}
    ele = mxml.set_eroot(SOAP_NAME_SPACE+'Envelope', nsmap=xmlns)
    mxml.create_SubElement(ele, SOAP_NAME_SPACE+'Header')    
    sbody = mxml.create_SubElement(ele, SOAP_NAME_SPACE+'Body')    
    renviconsruc = mxml.create_SubElement(sbody, SIFEN_NAME_SPACE+'rEnviConsRUC')    
    did = mxml.create_SubElement(renviconsruc, SIFEN_NAME_SPACE+'dId')
    mxml.create_SubElement(renviconsruc, SIFEN_NAME_SPACE+'dRUCCons', _text=ruc)
    sppk = track_soap_msg('siConsRUC', mxml.to_string_xml(ele))
    did.text = str(sppk)
    fname = '{}/SiConsDE_{}_soap.xml'.format(ROOTFOLDER, sppk)
    logging.info('Guardando eschema soap en {}'.format(fname))
    mxml.save_xml(ele, fname)
    return {'xml': mxml.to_string_xml(ele), 'sppk': sppk }

def rEnviConsArchivoRUCRequest(rucs):
    ROOTFOLDER = set_soap_folder()
    # xmlns = {
    #     'soap': SOAP_NAME_SPACE.strip('{}'),
    #     'xsd': SIFEN_NAME_SPACE.strip('{}')
    # }
    # ele = mxml.set_eroot(SOAP_NAME_SPACE+'Envelope', nsmap=xmlns)
    # mxml.create_SubElement(ele, SOAP_NAME_SPACE+'Header')    
    # sbody = mxml.create_SubElement(ele, SOAP_NAME_SPACE+'Body')    
    esign = ESigner()
    ele, header, sbody = mxml.get_soap_schema()
    renviconsruc = mxml.create_SubElement(sbody, 'rEnviConsArchivoRUCRequest', xmlns="http://ekuatia.set.gov.py/sifen/xsd")
    rconsultaarchivo = mxml.create_SubElement(renviconsruc, 'rConsultaArchivo')
    consude = mxml.create_SubElement(rconsultaarchivo, 'ConsultaDTE')
    for ruc in rucs:
        mxml.create_SubElement(consude, 'dRucFactElec', _text=ruc)
    sppk = track_soap_msg('rEnviConsArchivoRUCRequest', mxml.to_string_xml(ele))
    consude.attrib['Id'] = str(sppk)
    signature = esign.dynamically_sign(consude, None)
    rconsultaarchivo.append(signature)
    fname = '{}/rEnviConsArchivoRUCRequest_{}_soap.xml'.format(ROOTFOLDER, sppk)
    mxml.save_xml(ele, fname)    
    return {'xml': mxml.to_string_xml(ele), 'sppk': sppk }

def SiConsDE(cdc):
    ROOTFOLDER = set_soap_folder()
    ele, header, sbody = mxml.get_soap_schema()
    rEnviConsDe = mxml.create_SubElement(sbody, 'rEnviConsDeRequest', xmlns="http://ekuatia.set.gov.py/sifen/xsd")
    did = mxml.create_SubElement(rEnviConsDe, 'dId')
    mxml.create_SubElement(rEnviConsDe, 'dCDC', _text=cdc)
    sppk = track_soap_msg('SiConsDE', mxml.to_string_xml(ele))
    did.text = str(sppk)
    fname = '{}/SiConsDE_{}_soap.xml'.format(ROOTFOLDER, sppk)
    mxml.save_xml(ele, fname)
    return {'xml': mxml.to_string_xml(ele), 'sppk': sppk }

def SiResultLoteDE(lote):
    ROOTFOLDER = set_soap_folder()
    ele, header, sbody = mxml.get_soap_schema()
    rEnviConsDe = mxml.create_SubElement(sbody, 'rEnviConsLoteDe', xmlns="http://ekuatia.set.gov.py/sifen/xsd")
    did = mxml.create_SubElement(rEnviConsDe, 'dId')
    mxml.create_SubElement(rEnviConsDe, 'dProtConsLote', _text=lote)
    sppk = track_soap_msg('SiResultLoteDE', mxml.to_string_xml(ele))
    did.text = str(sppk)
    fname = '{}/SiResultLoteDE{}_soap.xml'.format(ROOTFOLDER, sppk)
    mxml.save_xml(ele, fname)
    return {'xml': mxml.to_string_xml(ele), 'sppk': sppk }

def CancelacionDeEvento(cdc, motivo):
    """
    <rEnviEventoDe
        xmlns="http://ekuatia.set.gov.py/sifen/xsd"
        xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
        <dEvReg>
            <gGroupGesEve>
                <rGesEve xsi:schemaLocation="http://ekuatia.set.gov.py/sifen/xsd
        siRecepEvento_v150.xsd"
                         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
                    <rEve Id="123">
                    </rEve>
                </rGesEve>
            </gGroupGesEve>
        </dEvReg>
    </rEnviEventoDe>
    """
    ROOTFOLDER = set_soap_folder()
    attr_qname = lxml.etree.QName("http://www.w3.org/2001/XMLSchema-instance", "schemaLocation")
    now = datetime.now()
    tnow = now.strftime('%Y-%m-%dT%H:%M:%S')
    esign = ESigner()
    ele, header, sbody = mxml.get_soap_schema()
    rEnviEventoDe = mxml.create_SubElement(
                    sbody,
                    'rEnviEventoDe',
                    xmlns=SIFEN_NAME_SPACE.strip('{}'),
                    #nsmap={'xsi': XSI_NAME_SPACE.strip('{}')}
    )
    did = mxml.create_SubElement(rEnviEventoDe,'dId')
    dEvReg = mxml.create_SubElement(rEnviEventoDe,'dEvReg')
    gGroupGesEve = mxml.create_SubElement(
                    dEvReg,
                    'gGroupGesEve',
                    {attr_qname: 'http://ekuatia.set.gov.py/sifen/xsd siRecepEvento_v150.xsd'},
                    xmlns=SIFEN_NAME_SPACE.strip('{}'),
                    nsmap={'xsi': XSI_NAME_SPACE.strip('{}')}
    )
    rGesEve = mxml.create_SubElement(gGroupGesEve,
                                     'rGesEve', 
                                    
                                )
    reve = mxml.create_SubElement(rGesEve, 'rEve')
    mxml.create_SubElement(reve, 'dFecFirma', _text=tnow)
    mxml.create_SubElement(reve, 'dVerFor', _text=EVERSION)
    #mxml.create_SubElement(reve, 'dTiGDE', _text='1')
    ggrouptievt = mxml.create_SubElement(reve, 'gGroupTiEvt')
    rgevecan = mxml.create_SubElement(ggrouptievt, 'rGeVeCan')
    mxml.create_SubElement(rgevecan, 'Id', _text=cdc)
    mxml.create_SubElement(rgevecan, 'mOtEve', _text=motivo)
    sppk = track_soap_msg('CancelacionDeEvento', mxml.to_string_xml(ele))
    did.text = str(sppk)
    #did.text = str(1)
    reve.attrib['Id'] = str(sppk)
    fname = '{}/EventoDeCancelacion{}_soap.xml'.format(ROOTFOLDER, sppk)
    signature = esign.dynamically_sign(rEnviEventoDe, str(sppk))
    rGesEve.append(signature)
    mxml.save_xml(ele, fname)
    print(mxml.to_string_xml(ele, pretty_print=True))
    return {'xml': mxml.to_string_xml(ele), 'sppk': sppk }


def InutilizacionDeEvento(timbrado, esta, punex, nin, nfin, dtipo, motivo):
    """
    <rEnviEventoDe
        xmlns="http://ekuatia.set.gov.py/sifen/xsd"
        xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
        <dEvReg>
            <gGroupGesEve>
                <rGesEve xsi:schemaLocation="http://ekuatia.set.gov.py/sifen/xsd
        siRecepEvento_v150.xsd"
                         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
                    <rEve Id="123">
                    </rEve>
                </rGesEve>
            </gGroupGesEve>
        </dEvReg>
    </rEnviEventoDe>
    """
    ROOTFOLDER = set_soap_folder()
    attr_qname = lxml.etree.QName("http://www.w3.org/2001/XMLSchema-instance", "schemaLocation")
    now = datetime.now()
    tnow = now.strftime('%Y-%m-%dT%H:%M:%S')
    esign = ESigner()
    ele, header, sbody = mxml.get_soap_schema()
    rEnviEventoDe = mxml.create_SubElement(
                    sbody,
                    'rEnviEventoDe',
                    xmlns=SIFEN_NAME_SPACE.strip('{}'),
                    #nsmap={'xsi': XSI_NAME_SPACE.strip('{}')}
    )
    did = mxml.create_SubElement(rEnviEventoDe,'dId')
    dEvReg = mxml.create_SubElement(rEnviEventoDe,'dEvReg')
    gGroupGesEve = mxml.create_SubElement(
                    dEvReg,
                    'gGroupGesEve',
                    {attr_qname: 'http://ekuatia.set.gov.py/sifen/xsd siRecepEvento_v150.xsd'},
                    xmlns=SIFEN_NAME_SPACE.strip('{}'),
                    nsmap={'xsi': XSI_NAME_SPACE.strip('{}')}
    )
    rGesEve = mxml.create_SubElement(gGroupGesEve,
                                     'rGesEve', 
                                    
                                )
    reve = mxml.create_SubElement(rGesEve, 'rEve')
    mxml.create_SubElement(reve, 'dFecFirma', _text=tnow)
    mxml.create_SubElement(reve, 'dVerFor', _text=EVERSION)
    # mxml.create_SubElement(reve, 'dTiGDE', _text='2')
    ggrouptievt = mxml.create_SubElement(reve, 'gGroupTiEvt')
    rgeveinu = mxml.create_SubElement(ggrouptievt, 'rGeVeInu')
    mxml.create_SubElement(rgeveinu, 'dNumTim', _text=timbrado)
    mxml.create_SubElement(rgeveinu, 'dEst', _text=esta)
    mxml.create_SubElement(rgeveinu, 'dPunExp', _text=punex)
    mxml.create_SubElement(rgeveinu, 'dNumIn', _text=nin)
    mxml.create_SubElement(rgeveinu, 'dNumFin', _text=nfin)
    mxml.create_SubElement(rgeveinu, 'iTiDE', _text=dtipo)
    mxml.create_SubElement(rgeveinu, 'mOtEve', _text=motivo)
    sppk = track_soap_msg('CancelacionDeEvento', mxml.to_string_xml(ele))
    did.text = str(sppk)
    #did.text = str(1)
    reve.attrib['Id'] = str(sppk)
    fname = '{}/EventoDeInutilizacion{}_soap.xml'.format(ROOTFOLDER, sppk)
    signature = esign.dynamically_sign(rEnviEventoDe, str(sppk))
    rGesEve.append(signature)
    mxml.save_xml(ele, fname)
    print(mxml.to_string_xml(ele, pretty_print=True))
    return {'xml': mxml.to_string_xml(ele), 'sppk': sppk }
