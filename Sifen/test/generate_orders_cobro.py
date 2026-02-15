from random import randint
import importlib
import arrow
from datetime import datetime
from apps.FL_Structure.models import Clientes
from apps.FL_Masters.models import Producto
from Sifen import mng_sifen
importlib.reload(mng_sifen)
#Instancias la clase que genera la solicitud
msifen = mng_sifen.MSifen()
tnow = datetime.now()
#La mayoria de los campos son autexplicativos, no obstante en la firma del method hay una breve descripcion de parametros
clobj = Clientes.objects.using('fl').get(clientecodigo=11151)
doc_total = 175000
artobj = Producto.objects.all().last()
ext_link = randint(2000, 3000)
msifen.crear_proforma(**{
    "userobj": "admin",
    "clientecodigo": 23600,
    "expedicion": 1,
    "source": "PRESENCIAL",
    "ext_link": ext_link,
    "doc_moneda": "GS",
    "doc_fecha": "2024-12-16",
    "doc_tipo": "FE",
    "doc_op": "VTA",
    "doc_estado": "CONCLUIDO",
    "doc_total": 244616.0,
    "details": [
        {
            "prod_cod": 5,
            "prod_descripcion": "SERVICIO DE FLETE AEREO INTERNACIONAL DDP",
            "prod_unidad_medida": 77,
            "prod_unidad_medida_desc": "UNI",
            "precio_unitario": 170662.5,
            "precio_unitario_siniva": 1,
            "cantidad_devolucion": 0,
            "cantidad": 0.1,
            "bonifica": False,
            "descuento": 0,
            "per_descuento": 0
        }
    ],
    "pagos": [],
    "doc_redondeo": 16.0,
    "cre_tipo_cod": 2
})