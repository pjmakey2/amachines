#coding: utf-8
import logging
import os
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from django.db.models import Sum, F
from Sifen.models import Business, DocumentHeader, DocumentDetail
from Sifen import mng_xml, xml_signer, mng_gmdata
from Sifen.fl_sifen_conf import RFOLDER, EVERSION, EFDEBUG
from Sifen.mng_certificate import certificate_manager

class Egf(object):
    def __init__(self):
        self.asuzone = ZoneInfo('America/Asuncion')
        now = datetime.now(tz=self.asuzone)
        tnow = now.strftime('%Y%m%d')
        self.ttime = datetime.now(ZoneInfo('America/Asuncion')) - timedelta(minutes=2)
        self.mxml = mng_xml.MngXml()
        self.ROOTFOLDER = '{}/{}/'.format(RFOLDER, tnow)
        self.create_dayfolder()

    def create_dayfolder(self):
        try:
            os.mkdir(self.ROOTFOLDER)
        except:pass

    def header_DE(self, sk_xml, cdc, cdc_dv, codseg, prof_number, obs, doc_fecha):
        obs = u"{} PED {}".format(obs, prof_number).strip()
        # tnow = datetime.now().strftime('%Y-%m-%dT%H:%M:%S') 
        
        tnow = '{}{}'.format(doc_fecha.strftime('%Y-%m-%d'), 
                             self.ttime.strftime('T%H:%M:%S'))
        
        de_xml = self.mxml.create_SubElement(sk_xml, 'DE', Id=cdc)
        self.mxml.create_SubElement(de_xml, 
                    'dDVId', 
                    _text=cdc_dv)
        self.mxml.create_SubElement(de_xml, 'dFecFirma', _text=tnow)
        # 1=Sistema de facturación delcontribuyente
        # 2=SIFEN solución gratuita
        self.mxml.create_SubElement(de_xml, 'dSisFact', _text=1)
        gope = self.mxml.create_SubElement(de_xml, 'gOpeDE')
        # 1=Normal
        # 2=Contingencia
        self.mxml.create_SubElement(gope, 'iTipEmi', _text=1)
        self.mxml.create_SubElement(gope, 'dDesTipEmi', _text='Normal')
        self.mxml.create_SubElement(gope, 'dCodSeg', _text=codseg)
        self.mxml.create_SubElement(gope, 'dInfoEmi', _text=obs)
        if EFDEBUG:
            self.mxml.create_SubElement(gope, 'dInfoFisc', _text=u'Información de interés del Fisco respecto al DE')
        return de_xml

    def g_timbrado(self, de_xml, tdoc, timb, esta, expd,doc,vigencia):
        tipo_docs = {
            1: u'Factura electrónica',
            2: u'Factura electrónica de exportación',
            3: u'Factura electrónica de importación',
            4: u'Autofactura electrónica',
            5: u'Nota de crédito electrónica',
            6: u'Nota de débito electrónica',
            7: u'Nota de remisión electrónica',
            8: u'Comprobante de retención electrónico',
        }
        tdoc = int(tdoc)
        gtimb = self.mxml.create_SubElement(de_xml, 'gTimb')
        self.mxml.create_SubElement(gtimb, 'iTiDE', _text=str(tdoc))
        self.mxml.create_SubElement(gtimb, 'dDesTiDE', _text=tipo_docs.get(tdoc))
        self.mxml.create_SubElement(gtimb, 'dNumTim', _text=timb)
        self.mxml.create_SubElement(gtimb, 'dEst', _text=str(esta).zfill(3))
        self.mxml.create_SubElement(gtimb, 'dPunExp', _text=str(expd).zfill(3))
        self.mxml.create_SubElement(gtimb, 'dNumDoc', _text=str(doc).zfill(7))
        # if EFDEBUG:
        #      self.mxml.create_SubElement(gtimb, 'dSerieNum', _text='AB')
        self.mxml.create_SubElement(gtimb, 'dFeIniT', _text=vigencia)
        return de_xml

    def g_degeneral(self, de_xml, doc_fecha_kude, headerobj: DocumentHeader):
        # Obligatorio si C002 = 1 o 4
        # No informar si C002 ≠ 1 o 4
        k_tipo_ope = {
            1: u'Venta de mercadería',
            2: u'Prestación de servicios',
            3: u'Mixto (Venta de mercadería y servicios)',
            4: u'Venta de activo fijo',
            5: u'Venta de divisas',
            6: u'Compra de divisas',
            7: u'Promoción o entrega de muestras',
            8: u'Donación',
            9: u'Anticipo',
            10: u'Compra de productos',
            11: u'Compra de servicios',
            12: u'Venta de crédito fiscal',
            13: u'Muestras médicas (Art. 3 RG 24/2014)',
        }
        k_tipo_impuesto = {
            1: u'IVA',
            2: u'ISC',
            3: u'Renta',
            4: u'Ninguno',
            5: u'IVA - Renta'
        }
        k_t_gs = {
            'GS': 'PYG',
            'USD': u'USD'
        }

        k_p_gs = {
            'GS': 'GUARANI',
            'USD': u'US Dollar'
        }        
        
        gdatgralope = self.mxml.create_SubElement(de_xml, 'gDatGralOpe')
        self.mxml.create_SubElement(gdatgralope, 'dFeEmiDE', _text=doc_fecha_kude)
        gopecom = self.mxml.create_SubElement(gdatgralope, 'gOpeCom')
        if headerobj.doc_tipo in ['FE', 'FL', 'AF', 'SE']:
            self.mxml.create_SubElement(gopecom, 'iTipTra', _text=headerobj.doc_tipo_ope)
            self.mxml.create_SubElement(gopecom, 'dDesTipTra', _text=headerobj.doc_tipo_ope_desc)
        self.mxml.create_SubElement(gopecom, 
                'iTImp', 
                _text=headerobj.doc_tipo_imp)
        self.mxml.create_SubElement(gopecom, 
                'dDesTImp', 
                _text=headerobj.doc_tipo_imp_desc)
        self.mxml.create_SubElement(gopecom, 
                'cMoneOpe', 
                _text=k_t_gs.get(headerobj.doc_moneda))
        self.mxml.create_SubElement(gopecom, 
                'dDesMoneOpe', 
                _text=k_p_gs.get(headerobj.doc_moneda))
        if headerobj.doc_moneda != 'GS':
            self.mxml.create_SubElement(gopecom, 
                    'dCondTiCam', 
                    _text=1)  
            self.mxml.create_SubElement(gopecom, 
                    'dTiCam', 
                    _text='{:.4f}'.format(headerobj.tasa_cambio))
        self.emisor_de(gdatgralope, headerobj.ek_bs_ruc)
        # self.responsable_de(gdatgralope, headerobj)
        if headerobj.doc_tipo == 'AF':
            self.receptor_de_af(gdatgralope, str(headerobj.ek_bs_ruc))
        else:
            self.receptor_de(gdatgralope, headerobj)
        return de_xml

    def emisor_de(self, de_xml, ruc):
        eobj = Business.objects.get(ruc=ruc)
        ciuobj = eobj.ciudadobj
        actobj = eobj.actividadecoobj
        disobj = ciuobj.distritoobj
        depobj = disobj.dptoobj
        gemis = self.mxml.create_SubElement(de_xml, 'gEmis')
        self.mxml.create_SubElement(gemis, 'dRucEm', _text=eobj.ruc)
        self.mxml.create_SubElement(gemis, 'dDVEmi', _text=eobj.ruc_dv)
        #TODO: Ver para establecer la forma a nivel de base de datos
        self.mxml.create_SubElement(gemis, 'iTipCont', _text=eobj.contribuyenteobj.codigo)
        # self.mxml.create_SubElement(gemis, 'cTipReg', _text=2)
        if EFDEBUG:
            self.mxml.create_SubElement(gemis, 'dNomEmi', _text=u'DE generado en ambiente de prueba - sin valor comercial ni fiscal')
        else:
            self.mxml.create_SubElement(gemis, 'dNomEmi', _text=eobj.name)
        # if eobj.nombrefantasia:
        #     if eobj.nombrefantasia.strip() != '':
        #         self.mxml.create_SubElement(gemis, 'dNomFanEmi', _text=eobj.nombrefantasia)
        self.mxml.create_SubElement(gemis, 'dDirEmi', _text=eobj.direccion)
        self.mxml.create_SubElement(gemis, 'dNumCas', _text=eobj.numero_casa)
        self.mxml.create_SubElement(gemis, 'cDepEmi', _text=depobj.codigo_departamento)
        self.mxml.create_SubElement(gemis, 'dDesDepEmi', _text=depobj.nombre_departamento)
        self.mxml.create_SubElement(gemis, 'cDisEmi', _text=disobj.codigo_distrito)
        self.mxml.create_SubElement(gemis, 'dDesDisEmi', _text=disobj.nombre_distrito)
        self.mxml.create_SubElement(gemis, 'cCiuEmi', _text=ciuobj.codigo_ciudad)
        self.mxml.create_SubElement(gemis, 'dDesCiuEmi', _text=ciuobj.nombre_ciudad)
        self.mxml.create_SubElement(gemis, 'dTelEmi', _text=eobj.telefono)
        self.mxml.create_SubElement(gemis, 'dEmailE', _text=eobj.correo)
        gacteco = self.mxml.create_SubElement(gemis, 'gActEco')
        self.mxml.create_SubElement(gacteco, 'cActEco', _text=actobj.codigo_actividad)
        self.mxml.create_SubElement(gacteco, 'dDesActEco', _text=actobj.nombre_actividad)
        return de_xml

    def responsable_de(self, de_xml, headerobj):
        grespde = self.mxml.create_SubElement(de_xml, 'gRespDE')
        self.mxml.create_SubElement(grespde, 'iTipIDRespDE', _text=headerobj.impx_tdoc_cod)
        self.mxml.create_SubElement(grespde, 'dDTipIDRespDE', _text=headerobj.impx_tdoc_nam)
        self.mxml.create_SubElement(grespde, 'dNumIDRespDE', _text=headerobj.impx_doc_num)
        self.mxml.create_SubElement(grespde, 'dNomRespDE', _text=headerobj.impx_nombre)
        self.mxml.create_SubElement(grespde, 'dCarRespDE', _text=headerobj.impx_cargo)
        return de_xml

    def receptor_de(self, de_xml, headerobj: DocumentHeader):
        gdatrec = self.mxml.create_SubElement(de_xml, 'gDatRec')
        #inatrec = headerobj.pdv_tipocontribuyente if headerobj.pdv_tipocontribuyente else 2
        #TODO: This has to be in the meta pedidosheader
        tb = {
            'B2B':1,
            'B2C':2,
            'B2G':3,
            'B2F':4,
        }
        self.mxml.create_SubElement(gdatrec, 'iNatRec', _text=1 if headerobj.pdv_es_contribuyente else 2)
        print(headerobj.pdv_type_business, 'put carajo')
        if headerobj.pdv_type_business:
            self.mxml.create_SubElement(gdatrec, 'iTiOpe', _text=tb.get(headerobj.pdv_type_business))
        else:
            self.mxml.create_SubElement(gdatrec, 'iTiOpe', _text='B2C')
        self.mxml.create_SubElement(gdatrec, 'cPaisRec', _text=headerobj.pdv_pais_cod)
        self.mxml.create_SubElement(gdatrec, 'dDesPaisRe', _text=headerobj.pdv_pais)
        if headerobj.pdv_es_contribuyente:
        # if headerobj.pdv_tipocontribuyente != 0:
            self.mxml.create_SubElement(gdatrec, 'iTiContRec', _text=headerobj.pdv_tipocontribuyente)
            self.mxml.create_SubElement(gdatrec, 'dRucRec', _text=headerobj.pdv_ruc)
            self.mxml.create_SubElement(gdatrec, 'dDVRec', _text=headerobj.pdv_ruc_dv)
        else:
        # if headerobj.pdv_tipocontribuyente == 0:
            if headerobj.pdv_innominado:
                self.mxml.create_SubElement(gdatrec, 'iTipIDRec', _text=5)
                self.mxml.create_SubElement(gdatrec, 'dDTipIDRec', _text=u'Innominado')
            elif headerobj.pdv_pais == 'Paraguay':
                self.mxml.create_SubElement(gdatrec, 'iTipIDRec', _text=1)
                self.mxml.create_SubElement(gdatrec, 'dDTipIDRec', _text=u'Cédula paraguaya')
            else:
                self.mxml.create_SubElement(gdatrec, 'iTipIDRec', _text=9)
                self.mxml.create_SubElement(gdatrec, 'dDTipIDRec', _text=u'Número de Registro')
            self.mxml.create_SubElement(gdatrec, 'dNumIDRec', _text=headerobj.pdv_ruc)
        self.mxml.create_SubElement(gdatrec, 'dNomRec', _text=headerobj.pdv_nombrefactura)
        self.mxml.create_SubElement(gdatrec, 'dNomFanRec', _text=headerobj.pdv_nombrefantasia)
        if headerobj.pdv_direccion_entrega:
            self.mxml.create_SubElement(gdatrec, 'dDirRec', _text=headerobj.pdv_direccion_entrega)
            self.mxml.create_SubElement(gdatrec, 'dNumCasRec', _text=headerobj.pdv_numero_casa)
        if headerobj.pdv_dpto_cod:
            self.mxml.create_SubElement(gdatrec, 'cDepRec', _text=headerobj.pdv_dpto_cod)
            self.mxml.create_SubElement(gdatrec, 'dDesDepRec', _text=headerobj.pdv_dpto_nombre)
        if headerobj.pdv_distrito_cod:
            self.mxml.create_SubElement(gdatrec, 'cDisRec', _text=headerobj.pdv_distrito_cod)
            self.mxml.create_SubElement(gdatrec, 'dDesDisRec', _text=headerobj.pdv_distrito_nombre)
        if headerobj.pdv_ciudad_cod:
            self.mxml.create_SubElement(gdatrec, 'cCiuRec', _text=headerobj.pdv_ciudad_cod)
            self.mxml.create_SubElement(gdatrec, 'dDesCiuRec', _text=headerobj.pdv_ciudad_nombre)
        if headerobj.pdv_telefono:
            if len(headerobj.pdv_telefono) > 15 or len(headerobj.pdv_telefono) < 6:
                headerobj.pdv_telefono = headerobj.pdv_telefono[0:15].zfill(15)
        else:
            headerobj.pdv_telefono = '0'.zfill(15)
        self.mxml.create_SubElement(gdatrec, 'dTelRec', _text=headerobj.pdv_telefono)
        if headerobj.pdv_celular:
            if len(headerobj.pdv_celular) > 20 or len(headerobj.pdv_celular) < 10:
                headerobj.pdv_celular = headerobj.pdv_celular[0:10].zfill(20)
        else:
            headerobj.pdv_celular = '0'
        self.mxml.create_SubElement(gdatrec, 'dCelRec', _text=headerobj.pdv_celular)
        if headerobj.pdv_email:
            self.mxml.create_SubElement(gdatrec, 'dEmailRec', _text=headerobj.pdv_email.split(',')[0].strip())
        self.mxml.create_SubElement(gdatrec, 'dCodCliente', _text=headerobj.pdv_ruc if headerobj.pdv_ruc != '0' else '999')
        return de_xml
    
    def receptor_de_af(self, de_xml, ruc):
        eobj = Business.objects.get(ruc=ruc)
        ciuobj = eobj.ciudadobj
        
        actobj = eobj.actividadecoobj
        disobj = ciuobj.distritoobj
        depobj = disobj.dptoobj
        gdatrec = self.mxml.create_SubElement(de_xml, 'gDatRec')
        #inatrec = headerobj.pdv_tipocontribuyente if headerobj.pdv_tipocontribuyente else 2
        #TODO: This has to be in the meta pedidosheader
        tb = {
            'B2B':1,
            'B2C':2,
            'B2G':3,
            'B2F':4,
        }
        self.mxml.create_SubElement(gdatrec, 'iNatRec', _text=1)
        self.mxml.create_SubElement(gdatrec, 'iTiOpe', _text=2)
        self.mxml.create_SubElement(gdatrec, 'cPaisRec', _text='PRY')
        self.mxml.create_SubElement(gdatrec, 'dDesPaisRe', _text='Paraguay')
        
        self.mxml.create_SubElement(gdatrec, 'iTiContRec', _text=eobj.contribuyenteobj.codigo)
        self.mxml.create_SubElement(gdatrec, 'dRucRec', _text=eobj.ruc)
        self.mxml.create_SubElement(gdatrec, 'dDVRec', _text=eobj.ruc_dv)
        
        self.mxml.create_SubElement(gdatrec, 'dNomRec', _text=eobj.name)
        self.mxml.create_SubElement(gdatrec, 'dNomFanRec', _text=eobj.name)
        self.mxml.create_SubElement(gdatrec, 'dDirRec', _text=eobj.direccion)
        self.mxml.create_SubElement(gdatrec, 'dNumCasRec', _text=eobj.numero_casa)
        self.mxml.create_SubElement(gdatrec, 'cDepRec', _text=depobj.codigo_departamento)
        self.mxml.create_SubElement(gdatrec, 'dDesDepRec', _text=depobj.nombre_departamento)
        self.mxml.create_SubElement(gdatrec, 'cDisRec', _text=disobj.codigo_distrito)
        self.mxml.create_SubElement(gdatrec, 'dDesDisRec', _text=disobj.nombre_distrito)
        self.mxml.create_SubElement(gdatrec, 'cCiuRec', _text=ciuobj.codigo_ciudad)
        self.mxml.create_SubElement(gdatrec, 'dDesCiuRec', _text=ciuobj.nombre_ciudad)
        self.mxml.create_SubElement(gdatrec, 'dTelRec', _text=eobj.telefono)
        self.mxml.create_SubElement(gdatrec, 'dEmailRec', _text=eobj.correo)
        return de_xml

    def tipo_de(self, de_xml, headerobj: DocumentHeader):
        tds = {
            1: u'Devolución y Ajuste de prec',
            2: u'Devolución',
            3: u'Descuento',
            4: u'Bonificación',
            5: u'Crédito incobrable',
            6: u'Recupero de costo',
            7: u'Recupero de gasto',
            8: u'Ajuste de precio',
        }        
        gdtipde = self.mxml.create_SubElement(de_xml, 'gDtipDE')
        if headerobj.doc_tipo in ['FE', 'FL', 'SE']:
            gcamfe = self.mxml.create_SubElement(gdtipde, 'gCamFE')
            self.mxml.create_SubElement(gcamfe, 'iIndPres', _text=headerobj.doc_op_pres_cod)
            self.mxml.create_SubElement(gcamfe, 'dDesIndPres', _text=headerobj.doc_op_pres)
            # self.mxml.create_SubElement(gcamfe, 'dFecEmNR', _text=headerobj.pedidoheader.fecha_entrega)
            self.condope_de(gdtipde, headerobj)
        if headerobj.doc_tipo == 'AF':
            eobj = Business.objects.get(ruc=headerobj.ek_bs_ruc)
            ciuobj = eobj.ciudadobj
            disobj = ciuobj.distritoobj
            depobj = disobj.dptoobj
            gcamae = self.mxml.create_SubElement(gdtipde, 'gCamAE')
            self.mxml.create_SubElement(gcamae, 'iNatVen', _text=headerobj.af_vendedor_cod)
            self.mxml.create_SubElement(gcamae, 'dDesNatVen', _text=headerobj.af_vendedor)
            self.mxml.create_SubElement(gcamae, 'iTipIDVen', _text=headerobj.af_tdoc_cod)
            self.mxml.create_SubElement(gcamae, 'dDTipIDVen', _text=headerobj.af_tdoc)
            self.mxml.create_SubElement(gcamae, 'dNumIDVen', _text=headerobj.af_doc_id)
            self.mxml.create_SubElement(gcamae, 'dNomVen', _text=headerobj.af_nombrefantasia)
            self.mxml.create_SubElement(gcamae, 'dDirVen', _text=headerobj.af_direccion)
            self.mxml.create_SubElement(gcamae, 'dNumCasVen', _text=headerobj.af_nro_casa)
            self.mxml.create_SubElement(gcamae, 'cDepVen', _text=headerobj.af_dpto_cod)
            self.mxml.create_SubElement(gcamae, 'dDesDepVen', _text=headerobj.af_dpto_nombre)
            self.mxml.create_SubElement(gcamae, 'cDisVen', _text=headerobj.af_distrito_cod)
            self.mxml.create_SubElement(gcamae, 'dDesDisVen', _text=headerobj.af_distrito_nombre)
            self.mxml.create_SubElement(gcamae, 'cCiuVen', _text=headerobj.af_ciudad_cod)
            self.mxml.create_SubElement(gcamae, 'dDesCiuVen', _text=headerobj.af_ciudad_nombre)
            self.mxml.create_SubElement(gcamae, 'dDirProv', _text=eobj.direccion)
            self.mxml.create_SubElement(gcamae, 'cDepProv', _text=depobj.codigo_departamento)
            self.mxml.create_SubElement(gcamae, 'dDesDepProv', _text=depobj.nombre_departamento)
            self.mxml.create_SubElement(gcamae, 'cDisProv', _text=disobj.codigo_distrito)
            self.mxml.create_SubElement(gcamae, 'dDesDisProv', _text=disobj.nombre_distrito)
            self.mxml.create_SubElement(gcamae, 'cCiuProv', _text=ciuobj.codigo_ciudad)
            self.mxml.create_SubElement(gcamae, 'dDesCiuProv', _text=ciuobj.nombre_ciudad)
            self.condope_de(gdtipde, headerobj)

        if headerobj.doc_tipo == 'RE':
            #To implement
            pass        
        if headerobj.doc_tipo in ['NC', 'ND']:
            # 4= Autofactura electronica
            # 5= Nota de credito electronica
            # 6= Nota de debito electronica
            gcamfe = self.mxml.create_SubElement(gdtipde, 'gCamNCDE')
            #TODO: Put this in the UI
            if headerobj.doc_motivo == u'Devolución':
                self.mxml.create_SubElement(gcamfe, 'iMotEmi', _text='2')
                self.mxml.create_SubElement(gcamfe, 'dDesMotEmi',_text=u'Devolución')
            if headerobj.doc_motivo == u'Bonificación':
                self.mxml.create_SubElement(gcamfe, 'iMotEmi', _text='4')
                self.mxml.create_SubElement(gcamfe, 'dDesMotEmi', _text=u'Bonificación')
            if headerobj.doc_motivo == u'Crédito incobrable':
                self.mxml.create_SubElement(gcamfe, 'iMotEmi', _text='5')
                self.mxml.create_SubElement(gcamfe, 'dDesMotEmi', _text=u'Crédito incobrable')
        attr_cant = 'cantidad'
        if headerobj.doc_op == 'RS' and headerobj.doc_tipo == 'NC':
            attr_cant = 'cantidad_devolucion'
        attr_precio = 'precio_unitario'
        attr_descuento = 'descuento'
        attr_exenta = 'exenta'
        attr_gravada_5 = 'gravada_5'
        attr_gravada_10 = 'gravada_10'

        for pdobj in headerobj.documentdetail_set.filter(anulado=False).order_by('pk'):
            self.detalle_de(gdtipde, 
                headerobj,
                pdobj,
                attr_cant,
                attr_precio,
                attr_descuento,
                attr_exenta,
                attr_gravada_5,
                attr_gravada_10,
            )
        return de_xml

    def doc_relacion(self, de_xml, headerobj: DocumentHeader):
        gCamDEAsoc = self.mxml.create_SubElement(de_xml, 'gCamDEAsoc')
        self.mxml.create_SubElement(gCamDEAsoc, 'iTipDocAso', _text=headerobj.doc_relacion_cod)
        self.mxml.create_SubElement(gCamDEAsoc,'dDesTipDocAso', _text=headerobj.doc_relacion)
        if headerobj.doc_relacion_cod == 1:
            self.mxml.create_SubElement(gCamDEAsoc,'dCdCDERef', _text=headerobj.doc_relacion_cdc)
        elif headerobj.doc_relacion_cod == 3:
            self.mxml.create_SubElement(gCamDEAsoc,'iTipCons', _text=headerobj.doc_relacion_tipo_cod)
            self.mxml.create_SubElement(gCamDEAsoc,'dDesTipCons', _text=headerobj.doc_relacion_tipo)
        else:
            #No se necesita por que todos los documentos con el timbrado sifen
            self.mxml.create_SubElement(gCamDEAsoc,'dNTimDI', _text=headerobj.doc_relacion_timbrado)
            self.mxml.create_SubElement(gCamDEAsoc,'dEstDocAso', _text=str(headerobj.doc_relacion_establecimiento).zfill(3))
            self.mxml.create_SubElement(gCamDEAsoc,'dPExpDocAso', _text=str(headerobj.doc_relacion_expedicion).zfill(3))
            self.mxml.create_SubElement(gCamDEAsoc,'dNumDocAso', _text=headerobj.doc_relacion_cdc)
            self.mxml.create_SubElement(gCamDEAsoc,'iTipoDocAso', _text=headerobj.doc_relacion_tipo_cod)
            self.mxml.create_SubElement(gCamDEAsoc,'dDTipoDocAso', _text=headerobj.doc_relacion_tipo)
            self.mxml.create_SubElement(gCamDEAsoc,'dFecEmiDI', _text=headerobj.doc_relacion_fecha)
        return de_xml

    def condope_de(self, de_xml, headerobj: DocumentHeader):
        gcamcond = self.mxml.create_SubElement(de_xml, 'gCamCond')
        self.mxml.create_SubElement(gcamcond, 'iCondOpe', _text=headerobj.doc_cre_tipo_cod)
        self.mxml.create_SubElement(gcamcond, 'dDCondOpe', _text=headerobj.doc_cre_tipo)
        if headerobj.doc_cre_tipo_cod == 1:
            self.condope_contado_de(gcamcond, headerobj)
        if headerobj.doc_cre_tipo_cod == 2:
            self.condope_credito_de(gcamcond, headerobj)
        return de_xml

    def condope_contado_de(self, de_xml, headerobj: DocumentHeader):
        """
        iTiPago
            1= Efectivo
            2= Cheque
            3= Tarjeta de crédito
            4= Tarjeta de débito
            5= Transferencia
            6= Giro
            7= Billetera electrónica
            8= Tarjeta empresarial
            9= Vale
            10= Retención
            11= Pago por anticipo
            12= Valor fiscal
            13= Valor comercial
            14= Compensación
            15= Permuta
            16= Pago bancario (Informar solo
            si E011=5)
            17 = Pago Móvil
            18 = Donación
            19 = Promoción
            20 = Consumo Interno
            21 = Pago Electrónico
            99 = Otro
        """
        monto_total = headerobj.doc_total
        gpaconeini = self.mxml.create_SubElement(de_xml, 'gPaConEIni')
        self.mxml.create_SubElement(gpaconeini, 'iTiPago', _text=headerobj.doc_tipo_pago_cod)
        self.mxml.create_SubElement(gpaconeini, 'dDesTiPag', _text=headerobj.doc_tipo_pago)
        self.mxml.create_SubElement(gpaconeini, 'dMonTiPag', _text='{:.4f}'.format(monto_total))
        self.mxml.create_SubElement(gpaconeini, 'cMoneTiPag', _text='PYG')
        self.mxml.create_SubElement(gpaconeini, 'dDMoneTiPag', _text='Guarani')
        #self.mxml.create_SubElement(gpaconeini, 'dTiCamTiPag', _text=)
        #TODO: CAJA POS Data
        # if headerobj.doc_tipo_pago_cod == 2:
        #     dpks = headerobj.transdocext_set.filter(documentoobj__tipo='cheque').values_list('documentoobj__pk', flat=True).distinct('documentoobj__pk')
        #     if dpks:
        #         gpagcheq = self.mxml.create_SubElement(gpaconeini, 'gPagCheq')
        #         dpks = headerobj.transdocext_set.filter(documentoobj__tipo='cheque').values_list('documentoobj__pk', flat=True).distinct('documentoobj__pk')
        #         for chqobj in DocumentoExterno.objects.filter(pk__in=dpks, anulado=False):
        #             self.mxml.create_SubElement(gpagcheq, 'dNumCheq', _text=chqobj.numero[0:8].zfill(8))
        #             self.mxml.create_SubElement(gpagcheq, 'dBcoEmi', _text=chqobj.banco_agencia.get('banco'))
        # if headerobj.doc_tipo_pago_cod == 3:
        #     dpks = headerobj.transdocext_set.filter(documentoobj__tipo__in=['tj', 'td'])\
        #                  .values_list('documentoobj__pk', flat=True)\
        #                  .distinct('documentoobj__pk')
        #     if dpks:
        #         gpagtj = self.mxml.create_SubElement(gpaconeini, 'gPagTarCD')
        #         for tjobj in DocumentoExterno.objects.filter(pk__in=dpks, anulado=False):
        #             self.mxml.create_SubElement(gpagtj,'iDenTarj', _text=tjobj.tj_deno_cod)
        #             self.mxml.create_SubElement(gpagtj,'dDesDenTarj', _text=tjobj.tj_deno)
        #             self.mxml.create_SubElement(gpagtj,'dRSProTar', _text=tjobj.tj_proce_rz)
        #             self.mxml.create_SubElement(gpagtj,'dRUCProTar', _text=tjobj.tj_proce_ruc)
        #             self.mxml.create_SubElement(gpagtj,'dDVProTar', _text=tjobj.tj_proce_dv)
        #             self.mxml.create_SubElement(gpagtj,'iForProPa', _text=tjobj.tj_type_proc)
        #             self.mxml.create_SubElement(gpagtj,'dCodAuOpe', _text=tjobj.tj_auto)
        #             self.mxml.create_SubElement(gpagtj,'dNomTit', _text=tjobj.tj_titular)
        #             self.mxml.create_SubElement(gpagtj,'dNumTarj', _text=tjobj.numero)
        return de_xml
        
    def condope_credito_de(self, de_xml, headerobj: DocumentHeader):
        gpagcred = self.mxml.create_SubElement(de_xml, 'gPagCred')
        self.mxml.create_SubElement(gpagcred, 'iCondCred',_text=headerobj.doc_cre_cond)
        self.mxml.create_SubElement(gpagcred, 'dDCondCred',_text=headerobj.doc_cre_cond_desc)
        if headerobj.doc_cre_cond == 1:
            self.mxml.create_SubElement(gpagcred, 'dPlazoCre',_text=headerobj.doc_cre_plazo)
        if headerobj.doc_cre_cuota == 2:
            self.mxml.create_SubElement(gpagcred, 'dCuotas ',_text=headerobj.doc_cre_cuota)
        if headerobj.doc_cre_entrega_inicial:
            self.mxml.create_SubElement(gpagcred, 'dMonEnt', _text='{:.4f}'.format(headerobj.doc_cre_entrega_inicial))
        if headerobj.doc_cre_cond == 2:
            gcuotas = self.mxml.create_SubElement(gpagcred, 'gCuotas')
            #TODO: PAGO CUOTAS
            # for fobj in headerobj.pedidosheaderfees_set.filter(anulado=False):
            #     self.mxml.create_SubElement(gcuotas,'cMoneCuo',_text=fobj.cre_cuota_mone)
            #     self.mxml.create_SubElement(gcuotas,'dDMoneCuo',_text=fobj.cre_cuota_mone_desc)
            #     self.mxml.create_SubElement(gcuotas,'dMonCuota',_text='{:.4f}'.format(fobj.cre_cuota_mon))
            #     self.mxml.create_SubElement(gcuotas,'dVencCuo',_text=fobj.cre_cuota_ven)
        return de_xml

    def detalle_de(self, de_xml, headerobj: DocumentHeader, pdobj: DocumentDetail,attr_cant,attr_precio,
                         attr_descuento,attr_exenta,attr_gravada_5,
                          attr_gravada_10):
        iva_5, iva_10 = pdobj.get_ivas()
        base_g_5, base_g_10 = pdobj.get_base_gravada()
        cantidad = getattr(pdobj, attr_cant)
        precio_unitario = getattr(pdobj, attr_precio)
        exenta = getattr(pdobj, attr_exenta)
        gravada_5 = getattr(pdobj, attr_gravada_5)
        gravada_10 = getattr(pdobj, attr_gravada_10)
        descuento = getattr(pdobj, attr_descuento)
        if headerobj.doc_op == 'RS':
            if exenta:
                exenta = precio_unitario*cantidad
            if gravada_5:
                gravada_5 = precio_unitario*cantidad
            if gravada_10:
                gravada_10 = precio_unitario*cantidad

        if pdobj.per_descuento == 100:
            setattr(pdobj, attr_exenta,0)
            setattr(pdobj, attr_gravada_5,0)
            setattr(pdobj, attr_gravada_10,0)
        gcamitem = self.mxml.create_SubElement(de_xml, 'gCamItem')
        self.mxml.create_SubElement(gcamitem, 'dCodInt', _text=pdobj.prod_cod)
        # if artobj.prod_partidaarancelaria:
        #     self.mxml.create_SubElement(gcamitem, 'dParAranc', _text=artobj.prod_partidaarancelaria)
        # if artobj.ncm:
        #     self.mxml.create_SubElement(gcamitem, 'dNCM', _text=artobj.ncm)
        # if artobj.dncpg: 
        #     self.mxml.create_SubElement(gcamitem, 'dDncpG', _text=artobj.dncpg)
        # if artobj.dncpe:             
        #     self.mxml.create_SubElement(gcamitem, 'dDncpE', _text=artobj.dncpe)
        # br = artobj.get_codigobarra_fancy()
        # brc = artobj.get_codigobarracaja_fancy()
        # if len(str(br)) in [8,12, 13, 14]:
        #     self.mxml.create_SubElement(gcamitem, 'dGtin', _text=br) 
        # if len(str(brc)) in [8,12, 13, 14]:
        #     self.mxml.create_SubElement(gcamitem, 'dGtinPq', _text=brc)
        if EFDEBUG:
            self.mxml.create_SubElement(gcamitem, 'dDesProSer', _text='DE generado en ambiente de prueba - sin valor comercial ni fiscal')
        else:
            if headerobj.doc_tipo in ['SE']:
                self.mxml.create_SubElement(gcamitem, 'dDesProSer', _text=pdobj.observacion.replace('&', '').encode('utf-8'))
            else:
                # print(pdobj.prod_descripcion.replace('&', '').encode('ascii'), 
                # repr(pdobj.prod_descripcion.replace('&', '').encode('ascii')),
                # sep='\n')
                self.mxml.create_SubElement(gcamitem, 'dDesProSer', _text=pdobj.prod_descripcion.replace('&', '').encode('utf-8').decode())
        self.mxml.create_SubElement(gcamitem, 'cUniMed', _text=pdobj.prod_unidad_medida) 
        self.mxml.create_SubElement(gcamitem, 'dDesUniMed', _text=pdobj.prod_unidad_medida_desc)
        self.mxml.create_SubElement(gcamitem, 'dCantProSer', _text='{:.4f}'.format(cantidad))
        if pdobj.prod_pais_origen:
            self.mxml.create_SubElement(gcamitem, 'cPaisOrig', _text=pdobj.prod_pais_origen)
            self.mxml.create_SubElement(gcamitem, 'dDesPaisOrig', _text=pdobj.prod_pais_origen_desc)
        # self.mxml.create_SubElement(gcamitem, 'dInfItem', _text=headerobj)  
        # self.mxml.create_SubElement(gcamitem, 'cRelMerc', _text=headerobj) 
        # self.mxml.create_SubElement(gcamitem, 'cDesRelMec', _text=headerobj) 
        # self.mxml.create_SubElement(gcamitem, 'dCanQuiMer', _text=headerobj) 
        # self.mxml.create_SubElement(gcamitem, 'dPorQuiMer', _text=headerobj) 
        # self.mxml.create_SubElement(gcamitem, 'dCDCAnticipo', _text=headerobj)  
        gvaloritem = self.mxml.create_SubElement(gcamitem, 'gValorItem') 
        self.mxml.create_SubElement(gvaloritem, 'dPUniProSer', _text='{:.4f}'.format(precio_unitario))
        # if pdobj.pedidoheader.moneda != 'GS':
        #     self.mxml.create_SubElement(gvaloritem, 'dTiCamIt', _text=headerobj.tasa_cambio)
        bruto_item = precio_unitario * cantidad
        self.mxml.create_SubElement(gvaloritem, 'dTotBruOpeItem', _text='{:.4f}'.format(bruto_item))
        gvalorrestaitem = self.mxml.create_SubElement(gvaloritem, 'gValorRestaItem')

        # dDescItem es descuento sobre precio unitario (por unidad, no total)
        descuento_por_unidad = float(descuento) / float(cantidad) if cantidad > 0 else 0
        self.mxml.create_SubElement(gvalorrestaitem, 'dDescItem', _text='{:.4f}'.format(descuento_por_unidad))

        if pdobj.descuento:
            self.mxml.create_SubElement(gvalorrestaitem, 'dPorcDesIt', _text='{:.4f}'.format(pdobj.per_descuento))

        # Descuento global por ítem (también por unidad)
        desc_global = float(pdobj.documentheaderobj.doc_descuento_global or 0)
        desc_global_por_unidad = desc_global / float(cantidad) if cantidad > 0 and desc_global > 0 else 0
        if desc_global_por_unidad > 0:
            self.mxml.create_SubElement(gvalorrestaitem, 'dDescGloItem', _text='{:.4f}'.format(desc_global_por_unidad))

        # dTotOpeItem = (PU - DescItem - DescGloItem) × Cantidad
        # Que es equivalente a: Bruto - DescuentoTotal - DescGlobalTotal
        totopeitem = float(bruto_item) - float(descuento) - desc_global
        if totopeitem < 0:
            totopeitem = 0
        self.mxml.create_SubElement(gvalorrestaitem,
                    'dTotOpeItem',
                    _text='{:.4f}'.format(totopeitem))
        # if pdobj.pedidoheader.moneda != 'GS':
        #     self.mxml.create_SubElement(gvalorrestaitem, 
        #             'dTotOpeGs', 
        #             _text='{:.4f}'.format(totopeitem*float(pdobj.pedidoheader.tasa_cambio)))
        if headerobj.doc_tipo != 'AF':
            gcamiva = self.mxml.create_SubElement(gcamitem, 'gCamIVA') 
            if pdobj.iva_5 or pdobj.iva_10:
                if not pdobj.exenta:
                    self.mxml.create_SubElement(gcamiva, 'iAfecIVA', _text=1)
                    self.mxml.create_SubElement(gcamiva, 'dDesAfecIVA', _text=u"Gravado IVA")
                    self.mxml.create_SubElement(gcamiva, 'dPropIVA', _text=100)
                else:
                    self.mxml.create_SubElement(gcamiva, 'iAfecIVA', _text=4)
                    self.mxml.create_SubElement(gcamiva, 'dDesAfecIVA', _text="Gravado parcial (Grav- Exento)")
                    self.mxml.create_SubElement(gcamiva, 'dPropIVA', _text=pdobj.per_tipo_iva)
                if pdobj.iva_5:
                    #base_g_5 = (totopeitem*(100/100)/1.05)
                    self.mxml.create_SubElement(gcamiva, 'dTasaIVA', _text=5)
                    self.mxml.create_SubElement(gcamiva, 'dBasGravIVA', _text='{:.4f}'.format(base_g_5))
                    self.mxml.create_SubElement(gcamiva, 'dLiqIVAItem', _text='{:.4f}'.format(iva_5 if not pdobj.bonifica else 0))
                    # self.mxml.create_SubElement(gcamiva, 'dBasGravIVA', _text=round(base_g_5, 4))
                    # self.mxml.create_SubElement(gcamiva, 'dLiqIVAItem', _text=round(iva_5, 4) if not pdobj.bonifica else 0)
                if pdobj.iva_10:
                    #base_g_10 = (totopeitem*(100/100)/1.1)
                    self.mxml.create_SubElement(gcamiva, 'dTasaIVA', _text=10)
                    self.mxml.create_SubElement(gcamiva, 'dBasGravIVA', _text='{:.4f}'.format(base_g_10))
                    self.mxml.create_SubElement(gcamiva, 'dLiqIVAItem',_text='{:.4f}'.format(iva_10 if not pdobj.bonifica else 0))
                    # self.mxml.create_SubElement(gcamiva, 'dBasGravIVA', _text=round(base_g_10, 4))
                    # self.mxml.create_SubElement(gcamiva, 'dLiqIVAItem', _text=round(iva_10, 4) if not pdobj.bonifica else 0)                
            if pdobj.exenta and not pdobj.iva_5 and not pdobj.iva_10:
                self.mxml.create_SubElement(gcamiva, 'iAfecIVA', _text=3)
                self.mxml.create_SubElement(gcamiva, 'dDesAfecIVA', _text=u"Exento")
                self.mxml.create_SubElement(gcamiva, 'dPropIVA', _text=0)
                self.mxml.create_SubElement(gcamiva, 'dTasaIVA', _text=0)
                self.mxml.create_SubElement(gcamiva, 'dBasGravIVA', _text=0)
                self.mxml.create_SubElement(gcamiva, 'dLiqIVAItem', _text=0)
            if ( pdobj.iva_5 or pdobj.iva_10 ) and pdobj.exenta:
                #aifeciva.text = '4'
                #Si E731 = 4 este campo es igual al resultado del cálculo: [100 * EA008 * (100 – E733)] / [10000 + (E734 * E733)]
                x = (100 * totopeitem * ( 100 - pdobj.per_tipo_iva ))
                y = ( 10000 + ( pdobj.porcentaje_iva * pdobj.per_tipo_iva))
                be = x / y
                self.mxml.create_SubElement(gcamiva, 'dBasExe', _text='{:.4f}'.format(pdobj.exenta))
            else:
                self.mxml.create_SubElement(gcamiva, 'dBasExe', _text=0)


        if pdobj.prod_lote and pdobj.prod_vencimiento:
            grasmerc = self.mxml.create_SubElement(gcamitem, 'gRasMerc') 
            self.mxml.create_SubElement(grasmerc, 'dNumLote', _text=pdobj.prod_lote)
            self.mxml.create_SubElement(grasmerc, 'dVencMerc', _text=pdobj.prod_vencimiento)
            self.mxml.create_SubElement(grasmerc, 'dNSerie', _text=0)
            self.mxml.create_SubElement(grasmerc, 'dNumPedi', _text=pdobj.documentheaderobj.prof_number)
            self.mxml.create_SubElement(grasmerc, 'dNumSegui', _text=pdobj.documentheaderobj.prof_number)
            # self.mxml.create_SubElement('dNomImp', _text='')
            # self.mxml.create_SubElement('dDirImp', _text='')
            # self.mxml.create_SubElement('dNumFir', _text='')
            # self.mxml.create_SubElement('dNumReg', _text='')
            # self.mxml.create_SubElement('dNumRegEntCom', _text='')
        return de_xml

    def gtosub_de(self, de_xml, headerobj: DocumentHeader):
        gtotsub = self.mxml.create_SubElement(de_xml, 'gTotSub')
        exenta = headerobj.get_total_exenta()
        sub_5 = headerobj.get_sub_5()
        sub_10 = headerobj.get_sub_10()
        totope = headerobj.get_total_operacion() #exenta+sub_5+sub_10
        totgral = headerobj.get_total_operacion()
        # if headerobj.doc_redondeo > 0:
        #     totgral = totope + headerobj.doc_redondeo
        # else:
        if abs(headerobj.doc_redondeo):
            totgral = totope - abs(headerobj.doc_redondeo)
            #totgral = totope - (headerobj.doc_redondeo*-1)
        if headerobj.doc_exenta and headerobj.doc_tipo != 'AF':
            if headerobj.get_total_exenta() > 0:
                self.mxml.create_SubElement(gtotsub, 'dSubExe', _text='{:.4f}'.format(exenta))
        # self.mxml.create_SubElement(gtotsub, 'dSubExo', _text='')
        if headerobj.doc_tipo != 'AF':
            self.mxml.create_SubElement(gtotsub, 'dSub5', _text='{:.4f}'.format(sub_5))
            self.mxml.create_SubElement(gtotsub, 'dSub10', _text='{:.4f}'.format(sub_10))
        self.mxml.create_SubElement(gtotsub, 'dTotOpe', _text='{:.4f}'.format(totope))
        # dTotDesc = Suma de todos los descuentos particulares por ítem (suma del campo descuento de cada detalle)
        descuento_particular = float(headerobj.documentdetail_set.filter(anulado=False).aggregate(
            total=Sum('descuento'))['total'] or 0)
        self.mxml.create_SubElement(gtotsub, 'dTotDesc', _text='{:.4f}'.format(descuento_particular))
        # dTotDescGlotem = Suma del descuento global (ya es el total, no multiplicar por items)
        total_desc_global = float(headerobj.doc_descuento_global or 0)
        self.mxml.create_SubElement(gtotsub, 'dTotDescGlotem', _text='{:.4f}'.format(total_desc_global))
        self.mxml.create_SubElement(gtotsub, 'dTotAntItem', _text=0)
        self.mxml.create_SubElement(gtotsub, 'dTotAnt', _text=0)
        # dPorcDescTotal (F010) = Porcentaje de descuento GLOBAL sobre total de la operación
        # IMPORTANTE: Este campo es SOLO para descuento GLOBAL, no para descuento particular por ítem
        # Si F010 > 0, es obligatorio informar EA004 (dDescGloItem) en cada ítem
        # Si no hay descuento global, debe ser 0
        total_bruto = float(headerobj.documentdetail_set.filter(anulado=False).aggregate(
            total=Sum(F('precio_unitario') * F('cantidad')))['total'] or 0)
        # Solo calcular porcentaje si hay descuento global
        porc_desc_global = (total_desc_global / total_bruto * 100) if (total_bruto > 0 and total_desc_global > 0) else 0
        self.mxml.create_SubElement(gtotsub, 'dPorcDescTotal', _text='{:.4f}'.format(porc_desc_global))
        # dDescTotal (F011) = Suma de descuentos particulares (EA002) + descuentos globales (EA004) de cada ítem
        total_descuentos = descuento_particular + total_desc_global
        self.mxml.create_SubElement(gtotsub, 'dDescTotal', _text='{:.4f}'.format(total_descuentos))
        self.mxml.create_SubElement(gtotsub, 'dAnticipo', _text=0)
        self.mxml.create_SubElement(gtotsub, 'dRedon', _text='{:.4f}'.format(abs(headerobj.doc_redondeo)))
        self.mxml.create_SubElement(gtotsub, 'dTotGralOpe', _text='{:.4f}'.format(totgral))
        #[EA008 * (E733/100)] / 1,1
        if headerobj.doc_tipo != 'AF':
            self.mxml.create_SubElement(gtotsub, 'dIVA5', _text='{:.4f}'.format(headerobj.get_ivas_5_master()))
            self.mxml.create_SubElement(gtotsub, 'dIVA10', _text='{:.4f}'.format(headerobj.get_ivas_10_master()))
            self.mxml.create_SubElement(gtotsub, 'dTotIVA', _text='{:.4f}'.format(headerobj.get_ivas_master()))
            b5 = 0
            g5 = float(headerobj.get_total_gravada_5())
            if g5:
                b5 = (g5*(100/100)/1.05)
            self.mxml.create_SubElement(gtotsub, 'dBaseGrav5', _text='{:.4f}'.format(headerobj.get_base_gravada_master_5()))
            b10 = 0
            g10 = float(headerobj.get_total_gravada_10())
            if g10:
                b10 = (g10*(100/100)/1.1)
            self.mxml.create_SubElement(gtotsub, 'dBaseGrav10', _text='{:.4f}'.format(headerobj.get_base_gravada_master_10()))
            self.mxml.create_SubElement(gtotsub, 'dTBasGraIVA', _text='{:.4f}'.format(headerobj.get_base_gravada_master()))
            if headerobj.doc_moneda != 'GS':
                self.mxml.create_SubElement(
                        gtotsub,
                        'dTotalGs',
                        _text='{:.4f}'.format((round(float(headerobj.get_total_venta()), 4))*float(headerobj.tasa_cambio)))
        # self.mxml.create_SubElement(gtotsub, 'dBaseGrav10', _text=round(headerobj.get_base_gravada_master_10(), 4))
        # self.mxml.create_SubElement(gtotsub, 'dTBasGraIVA', _text=round(headerobj.get_base_gravada_master(), 4))        
        return de_xml

    def set_signer_template(self, de_xml, cdc, headerobj, fname):
        signature = self.mxml.create_SubElement(de_xml, 'Signature', xmlns='http://www.w3.org/2000/09/xmldsig#')
        signedinfo = self.mxml.create_SubElement(signature, 'SignedInfo')
        self.mxml.create_SubElement(signedinfo, 'CanonicalizationMethod', Algorithm="http://www.w3.org/TR/2001/REC-xml-c14n-20010315")
        self.mxml.create_SubElement(signedinfo, 'SignatureMethod', Algorithm="http://www.w3.org/2001/04/xmldsig-more#rsa-sha256")
        reference = self.mxml.create_SubElement(signedinfo, 'Reference', URI="#{}".format(cdc))
        transforms = self.mxml.create_SubElement(reference, 'Transforms')
        self.mxml.create_SubElement(transforms, 'Transform', Algorithm="http://www.w3.org/2000/09/xmldsig#enveloped-signature")
        self.mxml.create_SubElement(transforms, 'Transform', Algorithm="http://www.w3.org/2001/10/xml-exc-c14n#")
        self.mxml.create_SubElement(reference, 'DigestMethod', Algorithm="http://www.w3.org/2001/04/xmlenc#sha256")
        self.mxml.create_SubElement(reference, 'DigestValue')
        self.mxml.create_SubElement(signature, 'SignatureValue')
        keyinfo = self.mxml.create_SubElement(signature, 'KeyInfo')
        x509data = self.mxml.create_SubElement(keyinfo, 'X509Data')
        self.mxml.create_SubElement(x509data, 'X509Certificate')
        fname = fname.replace('.xml', '_sign_template.xml')
        logging.info('Saving file with signed template {}'.format(fname))
        self.mxml.save_xml(de_xml, fname)
        xsign = xml_signer.ESigner()
        xsign.sign_xmlsec1(fname)
        fname_qr = self.set_qr_to_xml_tmpl(fname.replace('template', 'signed'), headerobj)
        return { 'de_xml': de_xml, 'xml_signature_tmpl': fname, 'xml_signature_qr':  fname_qr}        

    def set_qr_to_xml_tmpl(self, xml_tmpl, headerobj):
        xml_tmpl_qr = xml_tmpl.replace('signed', 'signed_qr')
        de_fxml = self.mxml.parse_xml(xml_tmpl)
        digest = de_fxml.find('{http://www.w3.org/2000/09/xmldsig#}Signature/{http://www.w3.org/2000/09/xmldsig#}SignedInfo/{http://www.w3.org/2000/09/xmldsig#}Reference/{http://www.w3.org/2000/09/xmldsig#}DigestValue').text
        self.qr_de(de_fxml, digest, headerobj)
        self.mxml.save_xml(de_fxml, xml_tmpl_qr)
        return xml_tmpl_qr

    def qr_de(self, de_xml, digest, headerobj):
        gcamfufd = self.mxml.create_SubElement(de_xml, 'gCamFuFD')
        mngo = mng_gmdata.Gdata()
        qpar = mngo.format_qr(digest, headerobj)
        self.mxml.create_SubElement(gcamfufd, 'dCarQR', _text=qpar)
        return de_xml

    def gen_xml_ekuatia(self, **kwargs):
        """This generate the output of the xml file that is need to be send to the SET"""
        logging.info('Running gen_xml_ekuatia')
        qdict = kwargs.get('qdict')
        prof_number = qdict.get('prof_number')
        logging.info('Convertings order {} to xml format for the SET'.format(prof_number))
        headerobj = DocumentHeader.objects.get(prof_number=prof_number)
        codseg = headerobj.ek_cod_seg
        doc_fecha_kude = headerobj.doc_fecha.strftime('%Y-%m-%dT%H:%M:%S')
        cdc = headerobj.ek_cdc
        cdc_dv = headerobj.ek_cdc_dv
        logging.info('Generate the initial skeleton')
        sk_xml = self.mxml.default_xml_skeleton(EVERSION)
        obs = headerobj.observacion.replace('\n','').replace('\t', '')[0:100].strip() if headerobj.observacion else ''
        de_xml = self.header_DE(sk_xml, cdc, cdc_dv, codseg, headerobj.prof_number, obs, headerobj.doc_fecha)
        de_xml = self.g_timbrado(
            de_xml, 
            headerobj.doc_tipo_cod, 
            headerobj.ek_timbrado, 
            headerobj.doc_establecimiento, 
            headerobj.doc_expedicion,
            headerobj.doc_numero,
            headerobj.ek_timbrado_vigencia.strftime('%Y-%m-%d')
        )
        self.g_degeneral(de_xml, doc_fecha_kude, headerobj)
        self.tipo_de(de_xml, headerobj)
        self.gtosub_de(de_xml, headerobj)
        if headerobj.doc_tipo in ['NC', 'ND', 'AF']:
            self.doc_relacion(de_xml, headerobj)
        fname = '{}/{}.xml'.format(self.ROOTFOLDER, headerobj.prof_number)
        if not headerobj.ek_xml_ekua:
            logging.info('Write file {}'.format(fname))
            self.mxml.save_xml(sk_xml, fname)
        if qdict.get('reprocess'):
            logging.info('Reprocess file {}'.format(fname))
            self.mxml.save_xml(sk_xml, fname)
        return {'exitos': 'Hecho', 'xml_file': fname}

    def sign_xml(self, fname, method, prof_number):
        headerobj = DocumentHeader.objects.get(prof_number=prof_number)
        xsign = xml_signer.ESigner()

        # Obtener certificado activo del negocio
        pem_path = None
        key_path = None
        try:
            businessobj = Business.objects.get(ruc=headerobj.ek_bs_ruc)
            cert_obj = certificate_manager.get_active_certificate_for_business(businessobj)
            if cert_obj and cert_obj.pem_file and cert_obj.key_file:
                pem_path = cert_obj.pem_file.path
                key_path = cert_obj.key_file.path
                logging.info(f'Usando certificado {cert_obj.nombre} para negocio {businessobj.name}')
        except Business.DoesNotExist:
            logging.warning(f'Business con RUC {headerobj.ek_bs_ruc} no encontrado, usando certificado por defecto')

        # The order of the methods matters because it is what is recommended
        if method == 'XMLSIGNER':
            return xsign.digital_signature_xmlsigner(fname, headerobj, pem_path=pem_path, key_path=key_path)
        return {'error': 'Debe especificar un metodo criptografico'}
    
