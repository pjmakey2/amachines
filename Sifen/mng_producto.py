"""Gestión de Productos y Modelos Relacionados"""
from django.forms import model_to_dict
from OptsIO.io_serial import IoS
from django.core.files import File
from OptsIO.io_json import from_json
from Sifen.models import Producto, Categoria, Marca, PorcentajeIva
import logging

log = logging.getLogger(__name__)


class MProducto:
    """Clase para gestión de Productos"""

    def create_categoria(self, *args, **kwargs) -> tuple:
        """
        Crea o actualiza un registro de Categoria
        """
        ios = IoS()
        userobj = kwargs.get('userobj')
        q: dict = kwargs.get('qdict', {})
        dbcon = q.get('dbcon', 'default')
        uc_fields: dict = from_json(q.get('uc_fields', {}))
        rnorm, rrm, rbol = ios.format_data_for_db(Categoria, uc_fields)
        for c in rrm: uc_fields.pop(c)
        for f, fv in rbol: uc_fields[f] = fv
        for f, fv in rnorm: uc_fields[f] = fv
        ff = ios.form_model_fields(uc_fields, Categoria._meta.fields)
        for rr in ff:
            uc_fields.pop(rr)
        pk = uc_fields.get('id')
        msg = 'Registro creado exitosamente'
        files: dict = kwargs.get('files')
        if pk:
            mobj = Categoria.objects.get(pk=pk)
            msg = 'Registro actualizado exitosamente'
            u_fields = ios.get_differences_fields(model_to_dict(mobj), uc_fields)
            if not u_fields and not files:
                return {'info': f'Nada que actualizar'}, args, kwargs
            if not u_fields and files:
                msg = 'Archivos actualizados exitosamente'
            if u_fields:
                Categoria.objects.using(dbcon).filter(pk=mobj.pk).update(**u_fields)
            if u_fields and files:
                msg = 'Registro y archivos actualizados exitosamente'
        else:
            mobj = Categoria.objects.using(dbcon).create(**uc_fields)
        return {'success': msg,
                'record_id': mobj.id
            }, args, kwargs

    def create_marca(self, *args, **kwargs) -> tuple:
        """
        Crea o actualiza un registro de Marca
        """
        ios = IoS()
        userobj = kwargs.get('userobj')
        q: dict = kwargs.get('qdict', {})
        dbcon = q.get('dbcon', 'default')
        uc_fields: dict = from_json(q.get('uc_fields', {}))
        rnorm, rrm, rbol = ios.format_data_for_db(Marca, uc_fields)
        for c in rrm: uc_fields.pop(c)
        for f, fv in rbol: uc_fields[f] = fv
        for f, fv in rnorm: uc_fields[f] = fv
        ff = ios.form_model_fields(uc_fields, Marca._meta.fields)
        for rr in ff:
            uc_fields.pop(rr)
        pk = uc_fields.get('id')
        msg = 'Registro creado exitosamente'
        files: dict = kwargs.get('files')
        if pk:
            mobj = Marca.objects.get(pk=pk)
            msg = 'Registro actualizado exitosamente'
            u_fields = ios.get_differences_fields(model_to_dict(mobj), uc_fields)
            if not u_fields and not files:
                return {'info': f'Nada que actualizar'}, args, kwargs
            if not u_fields and files:
                msg = 'Archivos actualizados exitosamente'
            if u_fields:
                Marca.objects.using(dbcon).filter(pk=mobj.pk).update(**u_fields)
            if u_fields and files:
                msg = 'Registro y archivos actualizados exitosamente'
        else:
            mobj = Marca.objects.using(dbcon).create(**uc_fields)
        return {'success': msg,
                'record_id': mobj.id
            }, args, kwargs

    def create_porcentajeiva(self, *args, **kwargs) -> tuple:
        """
        Crea o actualiza un registro de PorcentajeIva
        """
        ios = IoS()
        userobj = kwargs.get('userobj')
        q: dict = kwargs.get('qdict', {})
        dbcon = q.get('dbcon', 'default')
        uc_fields: dict = from_json(q.get('uc_fields', {}))
        rnorm, rrm, rbol = ios.format_data_for_db(PorcentajeIva, uc_fields)
        for c in rrm: uc_fields.pop(c)
        for f, fv in rbol: uc_fields[f] = fv
        for f, fv in rnorm: uc_fields[f] = fv
        ff = ios.form_model_fields(uc_fields, PorcentajeIva._meta.fields)
        for rr in ff:
            uc_fields.pop(rr)
        pk = uc_fields.get('id')
        msg = 'Registro creado exitosamente'
        files: dict = kwargs.get('files')
        if pk:
            mobj = PorcentajeIva.objects.get(pk=pk)
            msg = 'Registro actualizado exitosamente'
            u_fields = ios.get_differences_fields(model_to_dict(mobj), uc_fields)
            if not u_fields and not files:
                return {'info': f'Nada que actualizar'}, args, kwargs
            if not u_fields and files:
                msg = 'Archivos actualizados exitosamente'
            if u_fields:
                PorcentajeIva.objects.using(dbcon).filter(pk=mobj.pk).update(**u_fields)
            if u_fields and files:
                msg = 'Registro y archivos actualizados exitosamente'
        else:
            mobj = PorcentajeIva.objects.using(dbcon).create(**uc_fields)
        return {'success': msg,
                'record_id': mobj.id
            }, args, kwargs

    def create_producto(self, *args, **kwargs) -> tuple:
        """
        Crea o actualiza un registro de Producto
        """
        ios = IoS()
        userobj = kwargs.get('userobj')
        q: dict = kwargs.get('qdict', {})
        dbcon = q.get('dbcon', 'default')
        uc_fields: dict = from_json(q.get('uc_fields', {}))
        rnorm, rrm, rbol = ios.format_data_for_db(Producto, uc_fields)
        for c in rrm: uc_fields.pop(c)
        for f, fv in rbol: uc_fields[f] = fv
        for f, fv in rnorm: uc_fields[f] = fv
        ff = ios.form_model_fields(uc_fields, Producto._meta.fields)
        for rr in ff:
            uc_fields.pop(rr)
        pk = uc_fields.get('id')
        msg = 'Registro creado exitosamente'
        files: dict = kwargs.get('files')
        if pk:
            mobj = Producto.objects.get(pk=pk)
            msg = 'Registro actualizado exitosamente'
            u_fields = ios.get_differences_fields(model_to_dict(mobj), uc_fields)
            if not u_fields and not files:
                return {'info': f'Nada que actualizar'}, args, kwargs
            if not u_fields and files:
                msg = 'Archivos actualizados exitosamente'
            if u_fields:
                Producto.objects.using(dbcon).filter(pk=mobj.pk).update(**u_fields)
            if u_fields and files:
                msg = 'Registro y archivos actualizados exitosamente'
        else:
            mobj = Producto.objects.using(dbcon).create(**uc_fields)
        
        if files:
            for name, fobj in files.items():
                fname = f'user_{userobj.username}_{fobj.name}'
                dfobj = File(fobj, name=fname)
                setattr(mobj, name, dfobj)
            mobj.save()
        return {'success': msg,
                'record_id': mobj.id
            }, args, kwargs

    def delete_producto(self, *args, **kwargs) -> dict:
        """
        Elimina productos seleccionados
        """
        userobj = kwargs.get('userobj')
        q: dict = kwargs.get('qdict', {})
        dbcon = q.get('dbcon', 'default')
        ids = from_json(q.get('ids'))
        msgs = []

        if not ids:
            msgs.append({'error': 'Falta los IDs de los registros a eliminar'})
            return {'msgs': msgs}

        for pk in ids:
            try:
                mobj = Producto.objects.using(dbcon).get(pk=pk)
                descripcion = mobj.descripcion
                mobj.delete()
                msgs.append({'success': f'Producto "{descripcion}" eliminado exitosamente'})
            except Producto.DoesNotExist:
                msgs.append({'error': f'Producto con ID {pk} no encontrado'})
            except Exception as e:
                log.error(f'Error al eliminar producto {pk}: {str(e)}')
                msgs.append({'error': f'Error al eliminar producto: {str(e)}'})

        return {'msgs': msgs}

    def delete_categoria(self, *args, **kwargs) -> dict:
        """
        Elimina categorías seleccionadas
        """
        userobj = kwargs.get('userobj')
        q: dict = kwargs.get('qdict', {})
        dbcon = q.get('dbcon', 'default')
        ids = from_json(q.get('ids'))
        msgs = []

        if not ids:
            msgs.append({'error': 'Falta los IDs de los registros a eliminar'})
            return {'msgs': msgs}

        for pk in ids:
            try:
                mobj = Categoria.objects.using(dbcon).get(pk=pk)
                nombre = mobj.nombre
                # Verificar si tiene productos asociados
                productos_count = Producto.objects.using(dbcon).filter(categoriaobj=mobj).count()
                if productos_count > 0:
                    msgs.append({'warning': f'Categoría "{nombre}" tiene {productos_count} producto(s) asociado(s). Se eliminará la categoría pero los productos quedarán sin categoría.'})
                mobj.delete()
                msgs.append({'success': f'Categoría "{nombre}" eliminada exitosamente'})
            except Categoria.DoesNotExist:
                msgs.append({'error': f'Categoría con ID {pk} no encontrada'})
            except Exception as e:
                log.error(f'Error al eliminar categoría {pk}: {str(e)}')
                msgs.append({'error': f'Error al eliminar categoría: {str(e)}'})

        return {'msgs': msgs}

    def delete_marca(self, *args, **kwargs) -> dict:
        """
        Elimina marcas seleccionadas
        """
        userobj = kwargs.get('userobj')
        q: dict = kwargs.get('qdict', {})
        dbcon = q.get('dbcon', 'default')
        ids = from_json(q.get('ids'))
        msgs = []

        if not ids:
            msgs.append({'error': 'Falta los IDs de los registros a eliminar'})
            return {'msgs': msgs}

        for pk in ids:
            try:
                mobj = Marca.objects.using(dbcon).get(pk=pk)
                nombre = mobj.nombre
                # Verificar si tiene productos asociados
                productos_count = Producto.objects.using(dbcon).filter(marcaobj=mobj).count()
                if productos_count > 0:
                    msgs.append({'warning': f'Marca "{nombre}" tiene {productos_count} producto(s) asociado(s). Se eliminará la marca pero los productos quedarán sin marca.'})
                mobj.delete()
                msgs.append({'success': f'Marca "{nombre}" eliminada exitosamente'})
            except Marca.DoesNotExist:
                msgs.append({'error': f'Marca con ID {pk} no encontrada'})
            except Exception as e:
                log.error(f'Error al eliminar marca {pk}: {str(e)}')
                msgs.append({'error': f'Error al eliminar marca: {str(e)}'})

        return {'msgs': msgs}

    def delete_porcentajeiva(self, *args, **kwargs) -> dict:
        """
        Elimina porcentajes de IVA seleccionados
        """
        userobj = kwargs.get('userobj')
        q: dict = kwargs.get('qdict', {})
        dbcon = q.get('dbcon', 'default')
        ids = from_json(q.get('ids'))
        msgs = []

        if not ids:
            msgs.append({'error': 'Falta los IDs de los registros a eliminar'})
            return {'msgs': msgs}

        for pk in ids:
            try:
                mobj = PorcentajeIva.objects.using(dbcon).get(pk=pk)
                descripcion = mobj.descripcion
                # Verificar si tiene productos asociados
                productos_count = Producto.objects.using(dbcon).filter(porcentaje_iva=mobj).count()
                if productos_count > 0:
                    msgs.append({'error': f'Porcentaje IVA "{descripcion}" tiene {productos_count} producto(s) asociado(s). No se puede eliminar.'})
                    continue
                mobj.delete()
                msgs.append({'success': f'Porcentaje IVA "{descripcion}" eliminado exitosamente'})
            except PorcentajeIva.DoesNotExist:
                msgs.append({'error': f'Porcentaje IVA con ID {pk} no encontrado'})
            except Exception as e:
                log.error(f'Error al eliminar porcentaje IVA {pk}: {str(e)}')
                msgs.append({'error': f'Error al eliminar porcentaje IVA: {str(e)}'})

        return {'msgs': msgs}
