import importlib, arrow
from datetime import datetime
from apps.FL_Structure.models import Clientes
from apps.FL_Masters.models import Producto
from Sifen import mng_sifen, ekuatia_serials
importlib.reload(mng_sifen)
importlib.reload(ekuatia_serials)
msifen = mng_sifen.MSifen()
msifen.set_number(
    list(DocumentHeader.objects.filter(doc_tipo='FE').values_list('prof_number', flat=
True)),
    1,1,sign_document=False,doc_tipo='FE'
)
msifen.set_number(
    list(DocumentHeader.objects.filter(doc_tipo='NC').values_list('prof_number', flat=
True)),
    1,1,sign_document=False,doc_tipo='NC'
)
msifen.set_number(
    list(DocumentHeader.objects.filter(doc_tipo='ND').values_list('prof_number', flat=
True)),
    1,1,sign_document=False,doc_tipo='ND'
)

msifen.set_number(
    list(DocumentHeader.objects.filter(doc_tipo='AF').values_list('prof_number', flat=
True)),
    1,1,sign_document=False,doc_tipo='AF' #Por que no tiene AF en su timbrado
)
