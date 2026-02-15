import logging
from django.contrib.auth.models import User
from django.forms import model_to_dict
from django.core.files import File
from OptsIO.io_serial import IoS
from OptsIO.io_json import to_json, from_json
from OptsIO.models import UserProfile, UserBusiness
from Sifen.models import Business

logger = logging.getLogger(__name__)


class MMaster:
    """Gestor de Usuarios y Datos Maestros"""

    def __init__(self, userobj=None, business=None):
        """
        Inicializa MMaster.

        Args:
            userobj: Usuario de Django (opcional)
            business: Objeto Business directo (opcional)
        """
        self.userobj = userobj
        self.bsobj = business

    def create_user(self, *args, **kwargs) -> tuple:
        """
        Crea o actualiza un usuario de Django junto con su UserProfile.
        Maneja ambos modelos en una sola transacción.
        """
        ios = IoS()
        userobj = kwargs.get('userobj')
        q: dict = kwargs.get('qdict', {})
        dbcon = q.get('dbcon', 'default')
        uc_fields: dict = from_json(q.get('uc_fields', {}))
        files: dict = kwargs.get('files')

        # Extraer campos específicos de User
        user_fields = {}
        profile_fields = {}

        # Campos de User de Django
        if 'username' in uc_fields:
            user_fields['username'] = uc_fields.pop('username')
        if 'email' in uc_fields:
            user_fields['email'] = uc_fields.pop('email')
        if 'first_name' in uc_fields:
            user_fields['first_name'] = uc_fields.pop('first_name')
        if 'last_name' in uc_fields:
            user_fields['last_name'] = uc_fields.pop('last_name')
        if 'is_active' in uc_fields:
            user_fields['is_active'] = uc_fields.pop('is_active') == 'true'
        if 'is_staff' in uc_fields:
            user_fields['is_staff'] = uc_fields.pop('is_staff') == 'true'
        if 'is_superuser' in uc_fields:
            user_fields['is_superuser'] = uc_fields.pop('is_superuser') == 'true'

        # Password (solo si se proporciona y no está vacío)
        password = uc_fields.pop('password', None)
        password_confirm = uc_fields.pop('password_confirm', None)

        pk = uc_fields.get('id')
        msg = 'Usuario creado exitosamente'

        if pk:
            # Actualización de usuario existente
            try:
                user_instance = User.objects.get(pk=pk)
                profile_instance = UserProfile.objects.get(username=user_instance.username)

                msg = 'Usuario actualizado exitosamente'

                # Actualizar campos de User
                updated = False
                for field, value in user_fields.items():
                    if getattr(user_instance, field) != value:
                        setattr(user_instance, field, value)
                        updated = True

                # Actualizar password solo si se proporciona
                if password and password.strip():
                    if password == password_confirm:
                        user_instance.set_password(password)
                        updated = True
                    else:
                        return {'error': 'Las contraseñas no coinciden'}, args, kwargs

                if updated:
                    user_instance.save()

                # Manejar archivos de UserProfile
                if files:
                    for name, fobj in files.items():
                        if name == 'photo':
                            fname = f'user_{user_instance.username}_{fobj.name}'
                            dfobj = File(fobj, name=fname)
                            profile_instance.photo = dfobj
                            profile_instance.save()
                            msg = 'Usuario y foto actualizados exitosamente'

                if not updated and not files:
                    return {'info': 'Nada que actualizar'}, args, kwargs

                return {'success': msg, 'record_id': user_instance.id}, args, kwargs

            except User.DoesNotExist:
                return {'error': f'Usuario con ID {pk} no encontrado'}, args, kwargs
            except UserProfile.DoesNotExist:
                return {'error': 'Perfil de usuario no encontrado'}, args, kwargs

        else:
            # Creación de nuevo usuario
            if not user_fields.get('username'):
                return {'error': 'El nombre de usuario es requerido'}, args, kwargs

            if not password or not password.strip():
                return {'error': 'La contraseña es requerida para nuevos usuarios'}, args, kwargs

            if password != password_confirm:
                return {'error': 'Las contraseñas no coinciden'}, args, kwargs

            # Verificar que el username no exista
            if User.objects.filter(username=user_fields['username']).exists():
                return {'error': f'El usuario {user_fields["username"]} ya existe'}, args, kwargs

            # Crear User - create_user() no acepta .using(), se especifica en .save()
            user_instance = User.objects.create_user(
                username=user_fields['username'],
                email=user_fields.get('email', ''),
                password=password,
                first_name=user_fields.get('first_name', ''),
                last_name=user_fields.get('last_name', '')
            )

            # Establecer permisos y guardar
            user_instance.is_active = user_fields.get('is_active', True)
            user_instance.is_staff = user_fields.get('is_staff', False)
            user_instance.is_superuser = user_fields.get('is_superuser', False)
            user_instance.save()

            # Crear UserProfile
            profile_instance = UserProfile.objects.create(
                username=user_fields['username']
            )

            # Manejar foto si se proporciona
            if files and 'photo' in files:
                fobj = files['photo']
                fname = f'user_{user_instance.username}_{fobj.name}'
                dfobj = File(fobj, name=fname)
                profile_instance.photo = dfobj
                profile_instance.save()

            return {'success': msg, 'record_id': user_instance.id}, args, kwargs

    def delete_user(self, *args, **kwargs) -> dict:
        """
        Elimina uno o más usuarios de Django junto con sus UserProfile.
        """
        q: dict = kwargs.get('qdict', {})
        dbcon = q.get('dbcon', 'default')
        ids = from_json(q.get('ids'))
        msgs = []

        if not ids:
            msgs.append({'error': 'Falta los IDs de los registros a eliminar'})
            return {'msgs': msgs}

        for pk in ids:
            try:
                user_instance = User.objects.get(pk=pk)
                username = user_instance.username

                # Eliminar UserProfile asociado
                try:
                    profile = UserProfile.objects.get(username=username)
                    profile.delete()
                except UserProfile.DoesNotExist:
                    pass  # Si no existe el perfil, continuar

                # Eliminar User
                user_instance.delete()
                msgs.append({'success': f'Usuario {username} eliminado exitosamente'})

            except User.DoesNotExist:
                msgs.append({'error': f'Usuario con ID {pk} no encontrado'})
            except Exception as e:
                msgs.append({'error': f'Error al eliminar usuario: {str(e)}'})

        return {'msgs': msgs}

    def create_userbusiness(self, *args, **kwargs) -> tuple:
        """
        Crea o actualiza una asignación de negocio a usuario.
        Solo puede haber UN negocio activo por usuario a la vez.
        """
        ios = IoS()
        userobj = kwargs.get('userobj')
        q: dict = kwargs.get('qdict', {})
        dbcon = q.get('dbcon', 'default')
        uc_fields: dict = from_json(q.get('uc_fields', {}))

        # Extraer campos
        userprofileobj_id = uc_fields.get('userprofileobj_id')
        businessobj_id = uc_fields.get('businessobj_id')
        active = uc_fields.get('active', 'true') == 'true'
        pk = uc_fields.get('id')

        msg = 'Negocio asignado al usuario exitosamente'

        if pk:
            # Actualización de asignación existente
            try:
                user_business = UserBusiness.objects.get(pk=pk)

                # Si se está activando, desactivar todos los demás primero
                if active and not user_business.active:
                    UserBusiness.objects.filter(
                        userprofileobj=user_business.userprofileobj
                    ).update(active=False)

                user_business.active = active
                user_business.save()

                msg = 'Asignación actualizada exitosamente'
                return {'success': msg, 'record_id': user_business.id}, args, kwargs

            except UserBusiness.DoesNotExist:
                return {'error': f'Asignación con ID {pk} no encontrada'}, args, kwargs

        else:
            # Creación de nueva asignación
            if not userprofileobj_id:
                return {'error': 'El usuario es requerido'}, args, kwargs

            if not businessobj_id:
                return {'error': 'El negocio es requerido'}, args, kwargs

            # Verificar que el usuario exista
            try:
                user_profile = UserProfile.objects.get(pk=userprofileobj_id)
            except UserProfile.DoesNotExist:
                return {'error': 'Usuario no encontrado'}, args, kwargs

            # Verificar que el negocio exista
            try:
                business = Business.objects.get(pk=businessobj_id)
            except Business.DoesNotExist:
                return {'error': 'Negocio no encontrado'}, args, kwargs

            # Verificar si ya existe esta asignación
            existing = UserBusiness.objects.filter(
                userprofileobj=user_profile,
                businessobj=business
            ).first()

            if existing:
                return {'error': f'El usuario ya tiene asignado el negocio {business.name}'}, args, kwargs

            # Si se está creando como activo, desactivar todos los demás del usuario
            if active:
                UserBusiness.objects.filter(userprofileobj=user_profile).update(active=False)

            # Crear nueva asignación
            user_business = UserBusiness.objects.create(
                userprofileobj=user_profile,
                businessobj=business,
                active=active
            )

            return {'success': msg, 'record_id': user_business.id}, args, kwargs

    def delete_userbusiness(self, *args, **kwargs) -> dict:
        """
        Elimina una o más asignaciones de negocio a usuario.
        """
        q: dict = kwargs.get('qdict', {})
        dbcon = q.get('dbcon', 'default')
        ids = from_json(q.get('ids'))
        msgs = []

        if not ids:
            msgs.append({'error': 'Falta los IDs de los registros a eliminar'})
            return {'msgs': msgs}

        for pk in ids:
            try:
                user_business = UserBusiness.objects.get(pk=pk)
                username = user_business.userprofileobj.username
                business_name = user_business.businessobj.name

                user_business.delete()
                msgs.append({'success': f'Asignación de {business_name} a {username} eliminada exitosamente'})

            except UserBusiness.DoesNotExist:
                msgs.append({'error': f'Asignación con ID {pk} no encontrada'})
            except Exception as e:
                msgs.append({'error': f'Error al eliminar asignación: {str(e)}'})

        return {'msgs': msgs}
