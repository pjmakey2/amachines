import logging
from apps.FL_Structure.models import Paquetes
from OptsIO.models import SysParams
from django.utils.timezone import make_aware
from datetime import datetime, timedelta
from django.core.files.storage import default_storage
from datetime import date
import os

def set_rf_params():
    kt = {
        'ELIMINAR FOTO PAQUETE DESCONOCIDOS': 90,
        'ELIMINAR FOTO PAQUETE DEPOSITO':  90,
        'ELIMINAR FOTO PAQUETE ENTREGADO': 15,
        'ELIMINAR FOTO PAQUETE ANULADO': 15,
        'ELIMINAR DOCUMENTO PAQUETE AWB': 60,
    }
    SysParams.objects.filter(valor__in=kt.keys()).delete()
    for k, v in kt.items():
        logging.info(f'Creating SysParams: {k} = {v}')
        SysParams.objects.create(
            valor=k, 
            tipo='int', 
            valor_f=v, 
            vigencia=date.today(), 
            save_user='AUTOMATIC', 
            date_save=date.today())

def eliminar_rf(valor, mobj, attr_field, exc={}, filters={}, dbcon='fl'):
    """
        paquetefoto__isnull=False,
        estado="B"
    """
    sysopobj = SysParams.objects.get(valor=valor)
    days = sysopobj.valor_f
    ppks = []
    for vobj in mobj.objects.using(dbcon).filter(
        **filters
    ).exclude(**exc):
        attrobj = getattr(vobj, attr_field)
        if not attrobj:
            logging.warning(f'{mobj.__name__} {vobj.pk} no tiene valor en {attr_field}')
            continue
        if not hasattr(attrobj, 'path'):
            logging.warning(f'{mobj.__name__} {vobj.pk} no tiene ruta para el campo {attr_field}')
            continue
        file_path = attrobj.path
        if not os.path.exists(file_path):
            logging.warning(f'{mobj.__name__} {vobj.pk} no tiene archivo en {file_path}')
            continue
        file_name = attrobj.name
        ctime = os.path.getctime(file_path)
        created = make_aware(datetime.fromtimestamp(ctime))

        # Compare
        now = datetime.now(tz=created.tzinfo)
        delta = now - created

        # If older than <days>
        if delta > timedelta(days=days):
            logging.info(f'Eliminando {file_name} from {mobj.__name__} {vobj.pk} dias {delta.days}')
            default_storage.delete(file_name)
            ppks.append(vobj.pk)
    if ppks:
        ft = {
            attr_field: None,
        }
        logging.info(f'Marcando como None campo {attr_field} para {mobj.__name__} {ppks}')
        mobj.objects.using(dbcon).filter(
            pk__in=ppks
        ).update(**ft)