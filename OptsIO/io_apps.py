from django.forms import model_to_dict
from django.core.files import File
from OptsIO.io_serial import IoS
from OptsIO.models import Menu, Apps, AppsBookMakrs
from OptsIO import io_json

class IOApps:
    def create_menu(self, *args, **kwargs) -> tuple:
        """
        Crea o actualiza un registro de Menu
        """
        ios = IoS()
        userobj = kwargs.get('userobj')
        q: dict = kwargs.get('qdict', {})
        dbcon = q.get('dbcon', 'default')
        uc_fields: dict = io_json.from_json(q.get('uc_fields', {}))
        rnorm, rrm, rbol = ios.format_data_for_db(Menu, uc_fields)
        for c in rrm: uc_fields.pop(c)
        for f, fv in rbol: uc_fields[f] = fv
        for f, fv in rnorm: uc_fields[f] = fv
        ff = ios.form_model_fields(uc_fields, Menu._meta.fields)
        for rr in ff:
            uc_fields.pop(rr)
        pk = uc_fields.get('id')
        msg = 'Registro creado exitosamente'
        files: dict = kwargs.get('files')
        if pk:
            mobj = Menu.objects.get(pk=pk)
            msg = 'Registro actualizado exitosamente'
            u_fields = ios.get_differences_fields(model_to_dict(mobj), uc_fields)
            if not u_fields and not files:
                return {'info': f'Nada que actualizar'}, args, kwargs
            if not u_fields and files:
                msg = 'Archivos actualizados exitosamente'
            if u_fields:
                Menu.objects.using(dbcon).filter(pk=mobj.pk).update(**u_fields)
            if u_fields and files:
                msg = 'Registro y archivos actualizados exitosamente'
        else:
            mobj = Menu.objects.using(dbcon).create(**uc_fields)
        if files:
            for name, fobj in files.items():
                fname = f'user_{userobj.username}_{fobj.name}'
                dfobj = File(fobj, name=fname)
                setattr(mobj, name, dfobj)
            mobj.save()
        return {'success': msg,
                'record_id': mobj.id
            }, args, kwargs

    def create_apps(self, *args, **kwargs) -> tuple:
        """
        Crea o actualiza un registro de Apps
        """
        ios = IoS()
        userobj = kwargs.get('userobj')
        q: dict = kwargs.get('qdict', {})
        dbcon = q.get('dbcon', 'default')
        uc_fields: dict = io_json.from_json(q.get('uc_fields', {}))
        rnorm, rrm, rbol = ios.format_data_for_db(Apps, uc_fields)
        for c in rrm: uc_fields.pop(c)
        for f, fv in rbol: uc_fields[f] = fv
        for f, fv in rnorm: uc_fields[f] = fv
        ff = ios.form_model_fields(uc_fields, Apps._meta.fields)
        for rr in ff:
            uc_fields.pop(rr)
        pk = uc_fields.get('id')
        msg = 'Registro creado exitosamente'
        files: dict = kwargs.get('files')
        if pk:
            mobj = Apps.objects.get(pk=pk)
            msg = 'Registro actualizado exitosamente'
            u_fields = ios.get_differences_fields(model_to_dict(mobj), uc_fields)
            if not u_fields and not files:
                return {'info': f'Nada que actualizar'}, args, kwargs
            if not u_fields and files:
                msg = 'Archivos actualizados exitosamente'
            if u_fields:
                Apps.objects.using(dbcon).filter(pk=mobj.pk).update(**u_fields)
            if u_fields and files:
                msg = 'Registro y archivos actualizados exitosamente'
        else:
            mobj = Apps.objects.using(dbcon).create(**uc_fields)
        return {'success': msg,
                'record_id': mobj.id
            }, args, kwargs

    def create_appsbookmakrs(self, *args, **kwargs) -> tuple:
        """
        Crea o actualiza un registro de AppsBookMakrs
        """
        ios = IoS()
        userobj = kwargs.get('userobj')
        q: dict = kwargs.get('qdict', {})
        dbcon = q.get('dbcon', 'default')
        uc_fields: dict = io_json.from_json(q.get('uc_fields', {}))
        rnorm, rrm, rbol = ios.format_data_for_db(AppsBookMakrs, uc_fields)
        for c in rrm: uc_fields.pop(c)
        for f, fv in rbol: uc_fields[f] = fv
        for f, fv in rnorm: uc_fields[f] = fv
        ff = ios.form_model_fields(uc_fields, AppsBookMakrs._meta.fields)
        for rr in ff:
            uc_fields.pop(rr)
        pk = uc_fields.get('id')
        msg = 'Registro creado exitosamente'
        files: dict = kwargs.get('files')
        if pk:
            mobj = AppsBookMakrs.objects.get(pk=pk)
            msg = 'Registro actualizado exitosamente'
            u_fields = ios.get_differences_fields(model_to_dict(mobj), uc_fields)
            if not u_fields and not files:
                return {'info': f'Nada que actualizar'}, args, kwargs
            if not u_fields and files:
                msg = 'Archivos actualizados exitosamente'
            if u_fields:
                AppsBookMakrs.objects.using(dbcon).filter(pk=mobj.pk).update(**u_fields)
            if u_fields and files:
                msg = 'Registro y archivos actualizados exitosamente'
        else:
            mobj = AppsBookMakrs.objects.using(dbcon).create(**uc_fields)
        return {'success': msg,
                'record_id': mobj.id
            }, args, kwargs

    def delete_menu(self, *args, **kwargs) -> dict:
        """
        Elimina uno o más registros de Menu
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
            mobj = Menu.objects.using(dbcon).get(pk=pk)
            mobj.delete()
            msgs.append({'success': 'Registro eliminado exitosamente'})
        return {'msgs': msgs }

    def delete_apps(self, *args, **kwargs) -> dict:
        """
        Elimina uno o más registros de Apps
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
            mobj = Apps.objects.using(dbcon).get(pk=pk)
            mobj.delete()
            msgs.append({'success': 'Registro eliminado exitosamente'})
        return {'msgs': msgs }

    def delete_appsbookmakrs(self, *args, **kwargs) -> dict:
        """
        Elimina uno o más registros de AppsBookMakrs
        """
        ios = IoS()
        userobj = kwargs.get('userobj')
        q: dict = kwargs.get('qdict', {})
        dbcon = q.get('dbcon', 'default')
        ids = io_json.from_json(q.get('ids'))
        msgs = []
        if not ids:
            msgs.append({'error': 'Falta los IDs de los registros a eliminar'})
            return { 'msgs': msgs }
        for pk in ids:
            mobj = AppsBookMakrs.objects.using(dbcon).get(pk=pk)
            mobj.delete()
            msgs.append({'success': 'Registro eliminado exitosamente'})
        return { 'msgs': msgs }
