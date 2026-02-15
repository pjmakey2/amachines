from django.forms import model_to_dict
from OptsIO.io_serial import IoS
from Anime.models import Anime
from OptsIO import io_json

class MAnime:
    def create_anime(self, *args, **kwargs) -> tuple:
        """
        Crea un nuevo anime en la base de datos
        """
        ios = IoS()
        userobj = kwargs.get('userobj')
        q: dict = kwargs.get('qdict', {})
        dbcon = q.get('dbcon', 'default')
        uc_fields: dict = io_json.from_json(q.get('uc_fields', {}))
        rnorm, rrm, rbol = ios.format_data_for_db(Anime, uc_fields)
        for c in rrm: uc_fields.pop(c)
        for f, fv in rbol: uc_fields[f] = fv
        for f, fv in rnorm: uc_fields[f] = fv
        ff = ios.form_model_fields(uc_fields, Anime._meta.fields)
        for rr in ff:
            uc_fields.pop(rr)
        pk = uc_fields.get('id')
        msg = 'Registro creado exitosamente'
        files: dict = kwargs.get('files')
        if pk:
            mobj = Anime.objects.get(pk=pk)
            msg = 'Registro actualizado exitosamente'
            u_fields = ios.get_differences_fields(model_to_dict(mobj), uc_fields)
            for name, fobj in files.items():
                fname = f'embarque_{fobj.name}'
                dfobj = File(fobj, name=fname)
                setattr(mobj, name, dfobj)
            if not u_fields and not files:
                return {'info': f'Nada que actualizar'}, args, kwargs
            if not u_fields and files:
                msg = 'Archivos actualizados exitosamente'
            if u_fields:
                Anime.objects.using(dbcon).filter(pk=mobj.pk).update(**u_fields)
            if u_fields and files:
                msg = 'Registro y archivos actualizados exitosamente'
        else:
            mobj = Anime.objects.using(dbcon).create(**uc_fields)
        return {'success': msg, 
                'record_id': mobj.id
            }, args, kwargs

    def delete_anime(self, *args, **kwargs) -> dict:
        """
        Elimina un anime de la base de datos
        """
        ios = IoS()
        userobj = kwargs.get('userobj')
        q: dict = kwargs.get('qdict', {})
        dbcon = q.get('dbcon', 'default')
        ids = io_json.from_json(q.get('ids'))
        msgs = []
        if not ids:
            msgs.append({'error': 'Falta los IDs de los registros a eliminar'})
            return {'msgs': msgs }
        for pk in ids:
            mobj = Anime.objects.using(dbcon).get(pk=pk)
            mobj.delete()
            msgs.append({'success': 'Registro eliminado exitosamente'})
        return {'msgs': msgs }