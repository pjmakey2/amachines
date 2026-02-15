from Sifen.fl_sifen_conf import SOAP_NAME_SPACE, SIFEN_NAME_SPACE, XSI_NAME_SPACE
from lxml import etree
import re


class MngXml:
    def set_eroot(self, *args, **kwargs):
        rele = etree.Element(*args,**kwargs)
        return rele

    def create_SubElement(self, _parent,
                                _tag,attrib={},
                                _text=None,
                                nsmap=None,
                                **_extra):
        result = etree.SubElement(_parent,_tag,attrib,nsmap,**_extra)
        if _text:
            result.text = str(_text)
        if _text == 0:
            result.text = str(_text)
        return result        

    def default_xml_skeleton(self, version):
        tr = self.clean_up_string("""<rDE xmlns="http://ekuatia.set.gov.py/sifen/xsd" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://ekuatia.set.gov.py/sifen/xsd siRecepDE_v150.xsd">
            </rDE>
        """)
        rde = self.fromstring(tr)
        self.create_SubElement(rde, 'dVerFor', _text=version)
        return rde        

    def parse_xml(self, fname):
        return etree.parse(fname).getroot()

    def save_xml(self, eroot, fname, pretty_print=False):
        et = etree.ElementTree(eroot)
        et.write(fname, pretty_print=pretty_print, encoding='UTF-8', xml_declaration=True)
        return {'exitos': f'Hecho Guardado con exitos {fname}'}

    def pprint_xml(self, node, pretty_print=False):
        ppr = etree.tostring(node, pretty_print=pretty_print)
        return ppr

    def to_string_xml(self, node, pretty_print=False, xml_declaration=False):
        return etree.tostring(node, pretty_print=pretty_print, encoding='UTF-8', xml_declaration=xml_declaration)

    def fromstring(self, xml):
        xml = xml.replace("<?xml version='1.0' encoding='UTF-8'?>", '')
        return etree.fromstring(xml)

    def validate_xml(self, fname_xsd, fname_xml):
        gxsd = etree.parse(fname_xsd)
        xmlschema = etree.XMLSchema(gxsd)
        xml_doc = etree.parse(fname_xml)
        result = xmlschema.validate(xml_doc)
        return result

    def get_soap_schema(self, xsd_schm=False, nssoap='env', xsi_schm=False):
        xmlns = {
            nssoap: SOAP_NAME_SPACE.strip('{}'),
        }
        if xsd_schm:
            xmlns['xsd'] = SIFEN_NAME_SPACE.strip('{}')
        if xsi_schm:
            xmlns['xsi'] = XSI_NAME_SPACE.strip('{}')
        ele = self.set_eroot(SOAP_NAME_SPACE+'Envelope', nsmap=xmlns)
        header = self.create_SubElement(ele, SOAP_NAME_SPACE+'Header')    
        sbody = self.create_SubElement(ele, SOAP_NAME_SPACE+'Body')            
        return ele, header, sbody

    def clean_up_string(self, sele):
        sele = ''.join(sele.split('\r\n'))
        sele = ''.join(sele.split('\n'))
        sele = ''.join(sele.split('\t'))
        sele = ''.join(sele.split('    '))
        sele = ''.join(sele.split('>    <'))
        sele = ''.join(sele.split('>  <'))
        sele = re.sub('\r?\n|\r', '', sele)
        return sele

    def file_xml_to_dict(self, *args, **kwargs):
        qdict = kwargs.get('query_dict')
        xml_file = qdict.get('xml_file')
        rt = self.parse_xml(xml_file)
        return self.xml_to_dict(rt, False)

    def xml_to_dict(self, rt, child):
        drsp = {}
        for a in rt.iter():
            cltag = re.sub('{(.*?)}', '', a.tag).lower()
            vt = a.text
            if not vt:
                drsp[cltag] = [ self.xml_to_dict(rr, True) for rr in a.getchildren() ]
            if vt and child:
                drsp[cltag] = a.text
        return drsp

        
        
