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
        'model_name': 'Embarques',
        'dbcon': 'fl',
        'mquery': json.dumps([{'field': 'embarquecodigo', 'value': 1642}]),
        'fields': json.dumps(['estadoembarquedescripcion']),
        'detail_objs': json.dumps(
            {
                'dset': 'paquetes_set',
                'dfilter': {
                    'paquetecodigo__in': [1187934, 1187957, 1187970]
                },
                'sfields': ['paquetecodigo', 'clientecodigo__tarifa']
            }
        )
    }
)
for r in records.get('qs'):
    print(r)