from OptsIO.io_json import from_json, to_json
from django.core.management.base import BaseCommand
from OptsIO import io_users
from django.contrib.auth.models import User
from apps.FL_Orders import mng_order
from OptsIO.models import SysParams
from django.http import QueryDict

class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("--file", nargs="?", type=str)
        parser.add_argument("--create_admin", action="store_true")
        parser.add_argument("--predefined_permissions", action="store_true")
        parser.add_argument("--set_tested_users", action="store_true")
        parser.add_argument("--set_user_dashboard", action="store_true")
        parser.add_argument("--set_global_parameters_business", action="store_true")
        parser.add_argument("--set_sucursal_estante", action="store_true")
        parser.add_argument("--test_printing", action="store_true")

    def handle(self, *args, **options):
        iou = io_users.IOUser()
        if options['create_admin']:
            iou.create_admin()
        if options['predefined_permissions']:
            iou.predefined_permissions(sps_file=options['file'])
        if options['set_tested_users']:
            iou.set_tested_users()
        if options['set_user_dashboard']:
            iou.set_user_dashboard()
        if options['set_global_parameters_business']:
            iou.set_global_parameters_business()
        if options['set_sucursal_estante']:
            iou.set_sucursal_estante()
        if options['test_printing']:
            mo = mng_order.MOrder()
            qd = QueryDict(mutable=True)
            qd.update({'id': 10002,
                    'dbcon': 'default',
                    'dattrs': to_json({
                        #'full': 1, 
                        'base_cond': SysParams.objects.get(valor='Orden Compra Base y condiciones', tipo='str').valor_s
                    })
            })
            mo.crear_notapedido(userobj=User.objects.last(), qdict=qd)

