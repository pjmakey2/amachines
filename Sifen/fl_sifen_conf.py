from django.conf import settings
from dotenv import load_dotenv
import os

BASE_APP  = f'{settings.BASE_DIR}/Sifen'
BS='Toca3d'
LOGO = f'{settings.BASE_DIR}/media/toca3d_logo.png'

load_dotenv(settings.BASE_DIR / '.env')

RUC='80163121'
ESTABLECIMIENTO = {
    1: '1'.zfill(3), #CENTRAL
}

ESTABLECIMIENTO_CIUDAD = {
    1: 'ASUNCIÓN',
}

K_TIPO_OPE = {
    1: 'Venta de mercadería',
    2: 'Prestación de servicios',
    3: 'Mixto (Venta de mercadería y servicios)',
    4: 'Venta de activo fijo',
    5: 'Venta de divisas',
    6: 'Compra de divisas',
    7: 'Promoción o entrega de muestras',
    8: 'Donación',
    9: 'Anticipo',
    10: 'Compra de productos',
    11: 'Compra de servicios',
    12: 'Venta de crédito fiscal',
    13: 'Muestras médicas (Art. 3 RG 24/2014)',
}
K_TIPO_IMPUESTO = {
    1: 'IVA',
    2: 'ISC',
    3: 'Renta',
    4: 'Ninguno',
    5: 'IVA - Renta'
}
K_T_GS = {
    'GS': 'PYG',
    'USD': 'USD'
}

K_P_GS = {
    'GS': 'GUARANI',
    'USD': 'US Dollar'
}

K_OP_RES = {
    1: 'Operación presencial',
    2: 'Operación electrónica',
    3: 'Operación telemarketing',
    4: 'Venta a domicilio',
    5: 'Operación bancaria',
    6: 'Operación cíclica',
    9: 'Otro',
}

K_CRE_TIPO_COD = {
    1: "Contado",
    2: "Crédito"
}

K_TIPO_PAGO = {
    1: 'Efectivo',
    2: 'Cheque',
    3: 'Tarjeta de crédito',
    4: 'Tarjeta de débito',
    5: 'Transferencia',
    6: 'Giro',
    7: 'Billetera electrónica',
    8: 'Tarjeta empresarial',
    9: 'Vale',
    10: 'Retención',
    11: 'Pago por anticipo',
    12: 'Valor fiscal',
    13: 'Valor comercial',
    14: 'Compensación',
    15: 'Permuta',
    16: 'Pago bancario',
    17: 'Pago Móvil',
    18: 'Donación',
    19: 'Promoción',
    20: 'Consumo Interno',
    21: 'Pago Electrónico',
    99: 'Otro',
}

K_CRE_COND = {
    0: 'ND',
    1: "Plazo",
    2: "Cuota"
}

K_TIPO_CON = {
    1: 'B2C',
    2: 'B2B',
    3: 'B2G',
    4: 'B2F',
}

K_PROCESADORA = {
    1:'Visa',
    2:'Mastercard',
    3:'American Express',
    4:'Maestro',
    5:'Panal',
    6:'Cabal',
    9:'Otro'
}

K_VENDEDOR_COD = {
    1: "No contribuyente",
    2: "Extranjero"
}

K_TDOC_COD = {
    1: "Cédula paraguaya",
    2: "Pasaporte",
    3: "Cédula extranjera",
    4: "Carnet de residencia ",
}

EFDEBUG = os.environ.get('DEBUG', 'True') == 'True'
EVERSION = '150'
RFOLDER = f'{BASE_APP}/invoice_xml'

#This has to be string because the pkcs12 library manage the password as as byte like object
PASS = settings.SIFEN_KEY_PASS.encode()
PFX =  f'{BASE_APP}/certs/toca3d.pfx'.encode()
PEMF = f'{BASE_APP}/certs/toca3d.pem'.encode()
KEYF = f'{BASE_APP}/certs/toca3d.key'.encode()


URL = 'https://sifen.set.gov.py/de/ws'  # Servidor de prueba
ROUTE_RECIBE='/sync/recibe.wsdl'
ROUTE_RECIBE_LOTE = '/async/recibe-lote.wsdl'
ROUTE_EVENTO = '/eventos/evento.wsdl'
ROUTE_CONSULTA_LOTE = '/consultas/consulta-lote.wsdl'
ROUTE_CONSULTA_RUC = '/consultas/consulta-ruc.wsdl'
ROUTE_CONSULTA = '/consultas/consulta.wsdl'

URL_Q = 'https://ekuatia.set.gov.py/consultas/qr?'  # Servidor de prueba

SOAP_NAME_SPACE = '{http://www.w3.org/2003/05/soap-envelope}'
SIFEN_NAME_SPACE = '{http://ekuatia.set.gov.py/sifen/xsd}'
XSI_NAME_SPACE = '{http://www.w3.org/2001/XMLSchema-instance}'

if EFDEBUG:
    PASS = settings.SIFEN_KEY_PASS.encode()
    PFX =  f'{BASE_APP}/certs/toca3d.pfx'.encode()
    PEMF = f'{BASE_APP}/certs/toca3d.pem'.encode()
    KEYF = f'{BASE_APP}/certs/toca3d.key'.encode()
    URL = 'https://sifen-test.set.gov.py/de/ws'
    URL_Q = 'https://ekuatia.set.gov.py/consultas-test/qr?'
    ROUTE_RECIBE='/sync/recibe.wsdl'
    ROUTE_RECIBE_LOTE='/async/recibe-lote.wsdl'
    ROUTE_EVENTO='/eventos/evento.wsdl'
    ROUTE_CONSULTA_LOTE='/consultas/consulta-lote.wsdl'
    ROUTE_CONSULTA_RUC='/consultas/consulta-ruc.wsdl'
    ROUTE_CONSULTA='/consultas/consulta.wsdl'
#XML_CMD='/usr/bin/xmlsec1 --sign --output {output_file} --privkey-pem {pvt_key},{crt_file} --id-attr:Id DE {xml_file}'
#XML_CMD='/usr/bin/xmlsec1 --sign --output {output_file} --pkcs12 /home/peter/web_sales/etrans/cert/80026598-0.pfx  --pwd {pass} --trusted-pem /home/peter/web_sales/etrans/cert/80026598-0.crt --id-attr:Id DE {xml_file}'
