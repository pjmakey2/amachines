import logging
import os
from datetime import datetime
from Sifen import mng_xml, mng_gmdata
from signxml import XMLSigner, XMLVerifier, namespaces
from Sifen.fl_sifen_conf import PASS, PFX, PEMF, KEYF, RFOLDER


class ESigner:
    def __init__(self):
        self.mxml = mng_xml.MngXml()
        now = datetime.now()
        tnow = now.strftime('%Y%m%d')        
        self.ROOTFOLDER = '{}/{}'.format(RFOLDER, tnow)
        self.create_dayfolder()

    def create_dayfolder(self):
        try:
            os.mkdir(self.ROOTFOLDER)
        except:pass

    def digital_signature_xmlsigner(self, fname, pedobj, pem_path=None, key_path=None):
        """
           This method receives the DE file
           Sign the xml file with the algorithm expressed in the Paraguayan manual for the
           Electronic generation of documents
        """
        logging.info('Running digital_signature_xmlsigner')
        logging.info('Reading file {}'.format(fname))
        mngo = mng_gmdata.Gdata()
        root = self.mxml.parse_xml(fname)
        # Usar paths pasados como parámetro o fallback a fl_sifen_conf
        pem_file = pem_path or PEMF
        key_file = key_path or KEYF
        logging.info('Reading CERT {} and KEY {} files'.format(pem_file, key_file))
        cert = open(pem_file, 'rb').read()
        key = open(key_file, 'rb').read()
        signer = XMLSigner(c14n_algorithm='http://www.w3.org/2001/10/xml-exc-c14n#')
        signer.namespaces = {None: namespaces.ds}
        signed_root = signer.sign(root, reference_uri=pedobj.ek_cdc, key=key, cert=cert)
        digest = signed_root.getchildren()[2].getchildren()[0].getchildren()[-1].getchildren()[-1].text
        logging.info('Attaching QR url to the signed XML')
        qpar = mngo.format_qr(digest, pedobj)
        gcamfufd = self.mxml.set_eroot('gCamFuFD')
        self.mxml.create_SubElement(gcamfufd, 'dCarQR', _text=qpar.get('qpar'))
        signed_root.append(gcamfufd)
        logging.info('Verifying the signature against the certificate')
        verified_data = XMLVerifier().verify(signed_root,
                                             x509_cert=cert,
                                             #ca_pem_file=PEMF,
                                             ).signed_xml
        logging.info('File {} signed successfull with digest {}'.format(fname, digest))
        #print(mxml.to_string_xml(verified_data))
        #print(mxml.to_string_xml(signed_root))
        sfname = '{}/{}_verified_signed.xml'.format(self.ROOTFOLDER, pedobj.ek_cdc)
        logging.info('Save signed file {}'.format(sfname))
        self.mxml.save_xml(signed_root, sfname)
        return {'exitos': 'Hecho', 
                'xmlsigner_file': sfname, 
                'qpar': qpar.get('qpar'), 
                'qri': qpar.get('qri')}

    def dynamically_sign(self, eroot, ref_uri, pem_path=None, key_path=None):
        pem_file = pem_path or PEMF
        key_file = key_path or KEYF
        cert = open(pem_file, 'rb').read()
        key = open(key_file, 'rb').read()
        signer = XMLSigner(c14n_algorithm='http://www.w3.org/2001/10/xml-exc-c14n#')
        signer.namespaces = {None: namespaces.ds}
        # logging.info('Dynamically sign {}'.format(
        #     self.mxml.to_string_xml(eroot)
        # ))
        signed_root = signer.sign(eroot, reference_uri=ref_uri, key=key, cert=cert)
        #digest = signed_root.getchildren()[2].getchildren()[0].getchildren()[-1].getchildren()[-1].text
        logging.info('Verifying the signature against the certificate')
        verified_data = XMLVerifier().verify(signed_root,x509_cert=cert).signed_xml
        signature = signed_root.getchildren()[-1]
        #print(self.mxml.to_string_xml(signed_root, pretty_print=True))
        return signature
