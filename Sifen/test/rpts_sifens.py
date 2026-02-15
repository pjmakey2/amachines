from Sifen import mng_sifen
import importlib
importlib.reload(mng_sifen)
msf = mng_sifen.MSifen()
msf.rpt_libre_vta(qdict={'ejercicio': 2024, 'periodo': 10})