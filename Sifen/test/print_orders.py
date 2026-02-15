import importlib
import arrow
from datetime import datetime
from apps.FL_Structure.models import Clientes
from apps.FL_Masters.models import Producto
from Sifen import mng_sifen, e_kude
importlib.reload(mng_sifen)
importlib.reload(e_kude)
#Instancias la clase que genera la solicitud
msifen = mng_sifen.MSifen()

msifen.generar_pdf(
    [#'bb90bb2c-3d96-4ee7-911d-26ea0132abeb', #FE
     #'7290682c-1188-421e-9e94-d2f25855241a', #NC
     #'db376882-c40f-4bfc-b533-8f14fea315b3', #ND
     'ca33ce4e-a2f3-49e1-84c8-f58e56706d3f', #AF
    ]
)