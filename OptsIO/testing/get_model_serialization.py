import importlib
from OptsIO import io_serial, io_construct
#This is to be used in ipython shell
importlib.reload(io_serial)
importlib.reload(io_construct)
import json
ios = io_serial.IoS()
records = ios.seModel(
    qdict={
        'model_app_name': 'FL_Structure',
        'model_name': 'Clientes',
        'dbcon': 'fl',
        'mquery': json.dumps([]),
        'fields': json.dumps(['sucursal__nombre']),
        'allfields': 1,
    }
)
for r in records.get('qs'):
    print(r)