import logging
from OptsIO.io_serial import IoS
from OptsIO.io_json import to_json, from_json
from django.forms import model_to_dict
from OptsIO.models import Roles, RolesUser, RolesApps, UserProfile, Apps
from Sifen.models import Business

logger = logging.getLogger(__name__)


class IORoles:
    """Gestor de Roles y Permisos"""

    def __init__(self, userobj=None, business=None):
        """
        Inicializa IORoles con el Business del usuario o uno proporcionado.

        Args:
            userobj: Usuario de Django (opcional)
            business: Objeto Business directo (opcional)
        """
        self.bsobj = None

        # Prioridad: business directo > business del usuario
        if business:
            self.bsobj = business
        elif userobj:
            self.bsobj = self._get_business_from_user(userobj)

        # Si no hay business, tomar el primero disponible
        if not self.bsobj:
            self.bsobj = Business.objects.first()

    def _get_business_from_user(self, userobj):
        """Obtiene el Business activo del usuario."""
        from OptsIO.models import UserBusiness
        try:
            profile = UserProfile.objects.filter(username=userobj.username).first()
            if not profile:
                return None

            active_ub = UserBusiness.objects.filter(
                userprofileobj=profile,
                active=True
            ).select_related('businessobj').first()

            if active_ub and active_ub.businessobj:
                return active_ub.businessobj
        except Exception as e:
            logger.warning(f'Error obteniendo business del usuario: {e}')

        return None

    # =========================================================================
    # ROLES
    # =========================================================================

    def create_roles(self, *args, **kwargs) -> tuple:
        """Crea o actualiza un registro de Roles"""
        ios = IoS()
        userobj = kwargs.get('userobj')
        q: dict = kwargs.get('qdict', {})
        dbcon = q.get('dbcon', 'default')
        uc_fields: dict = from_json(q.get('uc_fields', {}))

        # Formatear datos para la base de datos
        rnorm, rrm, rbol = ios.format_data_for_db(Roles, uc_fields)
        for c in rrm:
            uc_fields.pop(c)
        for f, fv in rbol:
            uc_fields[f] = fv
        for f, fv in rnorm:
            uc_fields[f] = fv

        # Remover campos que no pertenecen al modelo
        ff = ios.form_model_fields(uc_fields, Roles._meta.fields)
        for rr in ff:
            uc_fields.pop(rr)

        pk = uc_fields.get('id')
        msg = 'Rol creado exitosamente'
        files: dict = kwargs.get('files')

        # Asegurar que el businessobj esté presente
        if not uc_fields.get('businessobj_id') and self.bsobj:
            uc_fields['businessobj_id'] = self.bsobj.id

        if pk:
            mobj = Roles.objects.get(pk=pk)
            msg = 'Rol actualizado exitosamente'
            u_fields = ios.get_differences_fields(model_to_dict(mobj), uc_fields)
            if not u_fields and not files:
                return {'info': 'Nada que actualizar'}, args, kwargs
            if not u_fields and files:
                msg = 'Archivos actualizados exitosamente'
            if u_fields:
                Roles.objects.using(dbcon).filter(pk=mobj.pk).update(**u_fields)
            if u_fields and files:
                msg = 'Rol y archivos actualizados exitosamente'
        else:
            mobj = Roles.objects.using(dbcon).create(**uc_fields)

        return {'success': msg, 'record_id': mobj.id}, args, kwargs

    def delete_roles(self, *args, **kwargs) -> dict:
        """Elimina uno o mas registros de Roles"""
        q: dict = kwargs.get('qdict', {})
        dbcon = q.get('dbcon', 'default')
        ids = from_json(q.get('ids'))
        msgs = []

        if not ids:
            msgs.append({'error': 'Falta los IDs de los registros a eliminar'})
            return {'msgs': msgs}

        for pk in ids:
            try:
                mobj = Roles.objects.using(dbcon).get(pk=pk)
                mobj.delete()
                msgs.append({'success': 'Rol eliminado exitosamente'})
            except Roles.DoesNotExist:
                msgs.append({'error': f'Rol con ID {pk} no encontrado'})
            except Exception as e:
                msgs.append({'error': f'Error al eliminar rol: {str(e)}'})

        return {'msgs': msgs}

    # =========================================================================
    # ROLES USER
    # =========================================================================

    def create_rolesuser(self, *args, **kwargs) -> tuple:
        """Crea o actualiza un registro de RolesUser"""
        ios = IoS()
        userobj = kwargs.get('userobj')
        q: dict = kwargs.get('qdict', {})
        dbcon = q.get('dbcon', 'default')
        uc_fields: dict = from_json(q.get('uc_fields', {}))

        # Formatear datos para la base de datos
        rnorm, rrm, rbol = ios.format_data_for_db(RolesUser, uc_fields)
        for c in rrm:
            uc_fields.pop(c)
        for f, fv in rbol:
            uc_fields[f] = fv
        for f, fv in rnorm:
            uc_fields[f] = fv

        # Remover campos que no pertenecen al modelo
        ff = ios.form_model_fields(uc_fields, RolesUser._meta.fields)
        for rr in ff:
            uc_fields.pop(rr)

        pk = uc_fields.get('id')
        msg = 'Rol de usuario creado exitosamente'
        files: dict = kwargs.get('files')

        # Asegurar que el businessobj esté presente
        if not uc_fields.get('businessobj_id') and self.bsobj:
            uc_fields['businessobj_id'] = self.bsobj.id

        if pk:
            mobj = RolesUser.objects.get(pk=pk)
            msg = 'Rol de usuario actualizado exitosamente'
            u_fields = ios.get_differences_fields(model_to_dict(mobj), uc_fields)
            if not u_fields and not files:
                return {'info': 'Nada que actualizar'}, args, kwargs
            if not u_fields and files:
                msg = 'Archivos actualizados exitosamente'
            if u_fields:
                RolesUser.objects.using(dbcon).filter(pk=mobj.pk).update(**u_fields)
            if u_fields and files:
                msg = 'Rol de usuario y archivos actualizados exitosamente'
        else:
            mobj = RolesUser.objects.using(dbcon).create(**uc_fields)

        return {'success': msg, 'record_id': mobj.id}, args, kwargs

    def delete_rolesuser(self, *args, **kwargs) -> dict:
        """Elimina uno o mas registros de RolesUser"""
        q: dict = kwargs.get('qdict', {})
        dbcon = q.get('dbcon', 'default')
        ids = from_json(q.get('ids'))
        msgs = []

        if not ids:
            msgs.append({'error': 'Falta los IDs de los registros a eliminar'})
            return {'msgs': msgs}

        for pk in ids:
            try:
                mobj = RolesUser.objects.using(dbcon).get(pk=pk)
                mobj.delete()
                msgs.append({'success': 'Rol de usuario eliminado exitosamente'})
            except RolesUser.DoesNotExist:
                msgs.append({'error': f'Rol de usuario con ID {pk} no encontrado'})
            except Exception as e:
                msgs.append({'error': f'Error al eliminar rol de usuario: {str(e)}'})

        return {'msgs': msgs}

    # =========================================================================
    # ROLES APPS
    # =========================================================================

    def create_rolesapps(self, *args, **kwargs) -> tuple:
        """
        Crea o actualiza un registro de RolesApps.
        Si appsobj_id es un array, crea múltiples registros (uno por cada App).
        """
        ios = IoS()
        userobj = kwargs.get('userobj')
        q: dict = kwargs.get('qdict', {})
        dbcon = q.get('dbcon', 'default')
        uc_fields: dict = from_json(q.get('uc_fields', {}))

        # Verificar si appsobj_id es un array (múltiple selección)
        appsobj_ids = uc_fields.get('appsobj_id')
        is_multiple = isinstance(appsobj_ids, list) and len(appsobj_ids) >= 1

        if is_multiple:
            # Crear múltiples registros RolesApps
            rolesobj_id = uc_fields.get('rolesobj_id')
            active = uc_fields.get('active', 'true')

            if not rolesobj_id:
                return {'error': 'El rol es requerido'}, args, kwargs

            # Asegurar que el businessobj esté presente
            businessobj_id = uc_fields.get('businessobj_id')
            if not businessobj_id and self.bsobj:
                businessobj_id = self.bsobj.id

            created_count = 0
            skipped_count = 0
            msgs = []

            for app_id in appsobj_ids:
                # Verificar si ya existe esta combinación Rol-App
                existing = RolesApps.objects.filter(
                    rolesobj_id=rolesobj_id,
                    appsobj_id=app_id,
                    businessobj_id=businessobj_id
                ).first()

                if existing:
                    skipped_count += 1
                    continue

                # Crear el registro
                try:
                    RolesApps.objects.using(dbcon).create(
                        rolesobj_id=rolesobj_id,
                        appsobj_id=app_id,
                        businessobj_id=businessobj_id,
                        active=(active == 'true')
                    )
                    created_count += 1
                except Exception as e:
                    msgs.append({'error': f'Error creando permiso para App ID {app_id}: {str(e)}'})

            if created_count > 0:
                msgs.append({'success': f'{created_count} permiso(s) de aplicación creado(s) exitosamente'})
            if skipped_count > 0:
                msgs.append({'info': f'{skipped_count} permiso(s) ya existían y fueron omitidos'})

            if not msgs:
                msgs.append({'error': 'No se pudo crear ningún permiso'})

            return {'msgs': msgs}, args, kwargs

        else:
            # Comportamiento normal para un solo registro
            # Formatear datos para la base de datos
            rnorm, rrm, rbol = ios.format_data_for_db(RolesApps, uc_fields)
            for c in rrm:
                uc_fields.pop(c)
            for f, fv in rbol:
                uc_fields[f] = fv
            for f, fv in rnorm:
                uc_fields[f] = fv

            # Remover campos que no pertenecen al modelo
            ff = ios.form_model_fields(uc_fields, RolesApps._meta.fields)
            for rr in ff:
                uc_fields.pop(rr)

            pk = uc_fields.get('id')
            msg = 'Permiso de aplicación creado exitosamente'
            files: dict = kwargs.get('files')

            # Asegurar que el businessobj esté presente
            if not uc_fields.get('businessobj_id') and self.bsobj:
                uc_fields['businessobj_id'] = self.bsobj.id

            if pk:
                mobj = RolesApps.objects.get(pk=pk)
                msg = 'Permiso de aplicación actualizado exitosamente'
                u_fields = ios.get_differences_fields(model_to_dict(mobj), uc_fields)
                if not u_fields and not files:
                    return {'info': 'Nada que actualizar'}, args, kwargs
                if not u_fields and files:
                    msg = 'Archivos actualizados exitosamente'
                if u_fields:
                    RolesApps.objects.using(dbcon).filter(pk=mobj.pk).update(**u_fields)
                if u_fields and files:
                    msg = 'Permiso de aplicación y archivos actualizados exitosamente'
            else:
                mobj = RolesApps.objects.using(dbcon).create(**uc_fields)

            return {'success': msg, 'record_id': mobj.id}, args, kwargs

    def delete_rolesapps(self, *args, **kwargs) -> dict:
        """Elimina uno o mas registros de RolesApps"""
        q: dict = kwargs.get('qdict', {})
        dbcon = q.get('dbcon', 'default')
        ids = from_json(q.get('ids'))
        msgs = []

        if not ids:
            msgs.append({'error': 'Falta los IDs de los registros a eliminar'})
            return {'msgs': msgs}

        for pk in ids:
            try:
                mobj = RolesApps.objects.using(dbcon).get(pk=pk)
                mobj.delete()
                msgs.append({'success': 'Permiso de aplicación eliminado exitosamente'})
            except RolesApps.DoesNotExist:
                msgs.append({'error': f'Permiso de aplicación con ID {pk} no encontrado'})
            except Exception as e:
                msgs.append({'error': f'Error al eliminar permiso de aplicación: {str(e)}'})

        return {'msgs': msgs}
