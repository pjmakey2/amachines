from celery import chain, group
import inspect, importlib
from .io_json import from_json
class IoE(object):
    def execute_task(self, rq, module, package, attr, chains, groups):
        dobj = getattr(importlib.import_module(f'{module}.{package}'), attr)
        if groups:
            groups = from_json(groups)
            cc = []
            for c in groups:
                dobj = getattr(importlib.import_module(f'{c.module}.{c.package}'), c.attr)
                cc.append(dobj.s(
                    username=rq.user.username,
                    files=rq.FILES,
                    qdict=c.get('qdict'),
                ).set(serializer='pickle'))
            c = group(*cc)
            c()
            return {'success': 'Ejecucion de grupos de tareas en curso',
                    'data': groups
                    }
        elif chains:
            chains = from_json(chains)
            cc = []
            for c in chains:
                dobj = getattr(importlib.import_module(f'{c.module}.{c.package}'), c.attr)
                cc.append(dobj.s(
                    username=rq.user.username,
                    files=rq.FILES,
                    qdict=c.get('qdict'),
                ).set(serializer='pickle'))
            c = chain(*cc)
            c()
            return {'success': 'Ejecucion de cadenas de tareas en curso',
                    'data': chains
                    }
        else:
            t = dobj.apply_async(
                kwargs={
                    'username': rq.user.username,
                    'files': rq.FILES,
                    'qdict': rq.POST,
                },
                serializer='pickle'
            )
            return {'success': 'Ejecucion de tarea en curso',
                    'data': t.task_id
                    }


    def execute_module(self, rq, module, package, attr,mname=None):
        """Dinamic execution of python modules

        Args:
            rq (queryset): A dictionary containing the parameters from a HTTP REQUEST
            module (string): A module (with a __init__.py) inside the root package
            attr (string): method, class ...etc inside the module
            mname (string): Just in case attr was a class
        """
        # Try to import as top-level module first (e.g., Sifen.mng_sifen, OptsIO.io_grid)
        # If that fails, try as OptsIO submodule (e.g., OptsIO.apps_man.apps_ui)
        dobj = getattr(importlib.import_module(f'{module}.{package}'), attr)
        if inspect.isclass(dobj):
            if not mname: 
                 return {'error': 'Falta proveer el metodo para la ejecucion'}
            cls = dobj()
            dobj = getattr(cls, mname)

        return dobj(userobj=rq.user,
                    rq=rq,
                    files=rq.FILES,
                    qdict=rq.POST,
                    )