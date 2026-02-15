from OptsIO.io_serial import IoS
from OptsIO import io_json
from Sifen.models import Business

class MMaster:
    """
    Management class for master data tables in Sifen app
    """

    def delete_business(self, *args, **kwargs) -> dict:
        ios = IoS()
        userobj = kwargs.get('userobj')
        q: dict = kwargs.get('qdict', {})
        dbcon = q.get('dbcon', 'default')
        ids = io_json.from_json(q.get('ids'))
        msgs = []
        if not ids:
            msgs.append({'error': 'Falta los IDs de los registros a eliminar'})
            return {'msgs': msgs}
        for pk in ids:
            mobj = Business.objects.using(dbcon).get(pk=pk)
            mobj.delete()
            msgs.append({'success': 'Registro eliminado exitosamente'})
        return {'msgs': msgs}
