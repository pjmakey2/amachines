import importlib
import arrow
from datetime import datetime
from apps.FL_Structure.models import Clientes
from apps.FL_Masters.models import Producto
from Sifen import mng_sifen, ekuatia_gf
importlib.reload(mng_sifen)
importlib.reload(ekuatia_gf)
#Instancias la clase que genera la solicitud
msifen = mng_sifen.MSifen()

