#Subir el doocumento a la sifen
import importlib
from Sifen import ekuatia_serials, mng_sifen, ekuatia_gf, soap_schemas_xml, mng_xml, rq_soap_handler
eser = ekuatia_serials.Eserial()
msifen = mng_sifen.MSifen()
importlib.reload(rq_soap_handler)
importlib.reload(ekuatia_serials)
importlib.reload(mng_sifen)
importlib.reload(ekuatia_gf)
importlib.reload(soap_schemas_xml)
importlib.reload(mng_xml)
orders = [DocumentHeader.objects.last().prof_number]
msifen.firmar_proforma(qsf={'prof_number__in': orders})
eser.send_pending_signedxml(orders)

#Consultar Lote

import importlib
from Sifen import rq_soap_handler
importlib.reload(rq_soap_handler)
rqs = rq_soap_handler.SoapSifen()
rqs.qr_lote()