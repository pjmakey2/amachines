import importlib
from Sifen import rq_soap_handler, soap_schemas_xml
importlib.reload(rq_soap_handler)
importlib.reload(soap_schemas_xml)
rqsoap = rq_soap_handler.SoapSifen()
rsp = rqsoap.qr_ruc('2463986', format=True)