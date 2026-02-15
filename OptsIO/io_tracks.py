from datetime import date, datetime
from apps.FL_Structure.models import Bitacora
from celery.execute import send_task

actions = {
    'recepcion_paquete': 'Recepcion Paquetes: Inserta-Reg. Paquete codigo {paquetecodigo} Tracking {paquetetracking}'
}

def dset_bitacora(codopcion: str, action: str):
    def set_bitacora(func):
        def wrapped_view(*args, **kwargs):
            userobj = kwargs.get('userobj')
            rq = kwargs.get('rq')
            qdict = kwargs.get('qdict')
            send_task('apps.OptsIO.tasks.save_bitacora',
                  args=(userobj.funcionariocodigo,
                        codopcion, 
                        action, 
                        qdict, 
                        rq.META.get('REMOTE_ADDR')), 
                  kwargs={})
            return func(*args, **kwargs)
        return wrapped_view
    return set_bitacora