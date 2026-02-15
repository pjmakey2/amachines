from OptsIO import io_rf
from apps.FL_Structure.models import Paquetes
from apps.FL_Paquetes.models import PaqueteDesconocido
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("--set_rf_params", action="store_true")
        parser.add_argument("--rf_foto_paquete_desconocidos", action="store_true")
        parser.add_argument("--rf_foto_paquete_deposito", action="store_true")
        parser.add_argument("--rf_foto_paquete_entregado", action="store_true")
        parser.add_argument("--rf_foto_paquete_anulado", action="store_true")
        parser.add_argument("--rf_awb_paquete", action="store_true")


    def handle(self, *args, **options):
        # ELIMINAR FOTO PAQUETES
        # ELIMINAR FOTO PAQUETE DESCONOCIDOS
        # ELIMINAR FOTO PAQUETE DEPOSITO
        # ELIMINAR FOTO PAQUETE ENTREGADO
        # ELIMINAR DOCUMENTO PAQUETE AWB
        if options['set_rf_params']:
            io_rf.set_rf_params()
        if options['rf_foto_paquete_desconocidos']:
            io_rf.eliminar_rf(
                'ELIMINAR FOTO PAQUETE DESCONOCIDOS',
                PaqueteDesconocido,
                'paquetefoto',
                filters={},
                exc={'paquetefoto': ''},
                dbcon='default'
            )
        if options['rf_foto_paquete_deposito']:
            io_rf.eliminar_rf(
                'ELIMINAR FOTO PAQUETE DEPOSITO',
                Paquetes,
                'paquetefoto',
                filters={'estado':"B",
                         'fechallegada__isnull':False,
                         'paquetefoto__isnull': False
                },
                exc={'paquetefoto': ''}
            )
        if options['rf_foto_paquete_entregado']:
            io_rf.eliminar_rf(
                'ELIMINAR FOTO PAQUETE ENTREGADO',
                Paquetes,
                'paquetefoto',
                filters={'estado':"C",
                         'fechallegada__isnull':False,
                         'paquetefoto__isnull': False
                },
                exc={'paquetefoto': ''}
            )
        if options['rf_foto_paquete_anulado']:
            io_rf.eliminar_rf(
                'ELIMINAR FOTO PAQUETE ANULADO',
                Paquetes,
                'paquetefoto',
                filters={'estado':"D",
                         'fechallegada__isnull':False,
                         'paquetefoto__isnull': False
                },
                exc={'paquetefoto': ''}
            )
        if options['rf_awb_paquete']:
            io_rf.eliminar_rf(
                'ELIMINAR DOCUMENTO PAQUETE AWB',
                Paquetes,
                'paqueteawb',
                filters={'paqueteawb__isnull':False},
                exc={'paqueteawb': ''}
            )
