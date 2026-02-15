"""User Profile Management"""
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password
from OptsIO.models import UserProfile, UserBusiness
from OptsIO.io_serial import IoS
from OptsIO.io_json import from_json
from django.forms import model_to_dict
from datetime import datetime
from django.core.files import File
from Sifen.models import Business
import logging

log = logging.getLogger(__name__)

class MUserProfile:
    """User Profile Management Class"""

    def get_or_create_profile(self, *args, **kwargs) -> dict:
        """
        Get or create user profile for the logged user
        """
        userobj = kwargs.get('userobj')
        q: dict = kwargs.get('qdict', {})
        dbcon = q.get('dbcon', 'default')

        profile, created = UserProfile.objects.using(dbcon).get_or_create(
            username=userobj.username,
            defaults={'preferences': {}}
        )

        user_data = {
            'id': userobj.id,
            'username': userobj.username,
            'first_name': userobj.first_name,
            'last_name': userobj.last_name,
            'email': userobj.email,
        }

        profile_data = model_to_dict(profile)

        return {
            'user': user_data,
            'profile': profile_data,
            'created': created
        }

    def update_profile(self, *args, **kwargs) -> dict:
        """
        Update user profile and user data
        """
        ios = IoS()
        userobj = kwargs.get('userobj')
        q: dict = kwargs.get('qdict', {})
        files: dict = kwargs.get('files', {})
        dbcon = q.get('dbcon', 'default')
        uc_fields: dict = from_json(q.get('uc_fields', {}))

        # Separate user fields from profile fields
        user_fields = {}
        profile_fields = {}
        new_password = None

        for field, value in uc_fields.items():
            if field in ['first_name', 'last_name', 'email']:
                user_fields[field] = value
            elif field == 'new_password' and value != '':
                new_password = value
            elif field == 'current_password':
                continue
            elif field in ['preferences']:
                # Ensure JSON fields are properly handled
                if isinstance(value, str):
                    if value.strip() != '':
                        profile_fields[field] = from_json(value)
                else:
                    profile_fields[field] = value
            else:
                profile_fields[field] = value

        # Update User model
        if user_fields:
            User.objects.filter(pk=userobj.pk).update(**user_fields)

        # Update password if provided
        if new_password:
            if new_password.strip() != '':
                current_password = uc_fields.get('current_password', '')
                if not userobj.check_password(current_password):
                    return {'error': 'Contraseña actual incorrecta'}

                userobj.password = make_password(new_password)
                userobj.save()

                # Update last_change_password in profile
                profile_fields['last_change_password'] = datetime.now()

        # Get or create profile
        profile, created = UserProfile.objects.using(dbcon).get_or_create(
            username=userobj.username,
            defaults={'preferences': {}}
        )

        # Handle file uploads
        if files:
            for name, fobj in files.items():
                if name == 'photo':
                    fname = f'user_{userobj.username}_{fobj.name}'
                    dfobj = File(fobj, name=fname)
                    setattr(profile, name, dfobj)

        # Update profile fields
        if profile_fields:
            for field, value in profile_fields.items():
                setattr(profile, field, value)
            profile.save()

        msg = 'Perfil actualizado exitosamente'
        if new_password:
            msg = 'Perfil y contraseña actualizados exitosamente'

        return {
            'success': msg,
            'record_id': profile.id
        }

    def validate_current_password(self, *args, **kwargs) -> dict:
        """
        Validate current user password
        """
        userobj = kwargs.get('userobj')
        q: dict = kwargs.get('qdict', {})
        current_password = q.get('current_password', '')

        if userobj.check_password(current_password):
            return {'success': 'Contraseña válida'}
        else:
            return {'error': 'Contraseña incorrecta'}

    def assign_business_to_user(self, *args, **kwargs) -> tuple:
        """
        Asigna un negocio existente al usuario logueado
        """
        ios = IoS()
        userobj = kwargs.get('userobj')
        request = kwargs.get('request')
        q: dict = kwargs.get('qdict', {})
        dbcon = q.get('dbcon', 'default')
        uc_fields: dict = from_json(q.get('uc_fields', {}))

        businessobj_id = uc_fields.get('businessobj_id')
        if not businessobj_id:
            return {'error': 'ID de negocio no proporcionado'}, args, kwargs

        # Verify business exists
        business = Business.objects.using(dbcon).filter(pk=businessobj_id).first()
        if not business:
            return {'error': 'Negocio no encontrado'}, args, kwargs

        # Get user profile
        profile = UserProfile.objects.using(dbcon).filter(username=userobj.username).first()
        if not profile:
            return {'error': 'Perfil de usuario no encontrado'}, args, kwargs

        # Check if already assigned
        existing = UserBusiness.objects.using(dbcon).filter(
            userprofileobj=profile,
            businessobj=business
        ).first()

        if existing:
            # Deactivate all and activate this one
            UserBusiness.objects.using(dbcon).filter(userprofileobj=profile).update(active=False)
            existing.active = True
            existing.save()
            return {'success': 'Negocio ya estaba asignado, ahora está activo'}, args, kwargs

        # Deactivate all other businesses for this user
        UserBusiness.objects.using(dbcon).filter(userprofileobj=profile).update(active=False)

        # Create new UserBusiness assignment
        mobj = UserBusiness.objects.using(dbcon).create(
            userprofileobj=profile,
            businessobj=business,
            active=True
        )

        # Clear session flag if exists
        if request and 'needs_business_setup' in request.session:
            request.session['needs_business_setup'] = False
            request.session.modified = True

        return {
            'success': f'Negocio {business.name} asignado exitosamente',
            'record_id': mobj.id
        }, args, kwargs

    def create_business_and_assign(self, *args, **kwargs) -> tuple:
        """
        Crea un nuevo negocio y lo asigna al usuario logueado
        """
        ios = IoS()
        userobj = kwargs.get('userobj')
        request = kwargs.get('request')
        q: dict = kwargs.get('qdict', {})
        files: dict = kwargs.get('files', {})
        dbcon = q.get('dbcon', 'default')
        uc_fields: dict = from_json(q.get('uc_fields', {}))

        # Check if RUC already exists
        if 'ruc' in uc_fields:
            existing = Business.objects.using(dbcon).filter(ruc=uc_fields['ruc']).first()
            if existing:
                return {'error': f'Ya existe un negocio con el RUC {uc_fields["ruc"]}'}, args, kwargs

        # Format data for Business model
        rnorm, rrm, rbol = ios.format_data_for_db(Business, uc_fields)
        for c in rrm:
            uc_fields.pop(c)
        for f, fv in rbol:
            uc_fields[f] = fv
        for f, fv in rnorm:
            uc_fields[f] = fv

        ff = ios.form_model_fields(uc_fields, Business._meta.fields)
        for rr in ff:
            uc_fields.pop(rr)

        pk = uc_fields.get('id')
        msg = 'Negocio creado exitosamente'

        if pk:
            mobj = Business.objects.get(pk=pk)
            msg = 'Negocio actualizado exitosamente'
            u_fields = ios.get_differences_fields(model_to_dict(mobj), uc_fields)
            if not u_fields and not files:
                return {'info': 'Nada que actualizar'}, args, kwargs
            if not u_fields and files:
                msg = 'Logo actualizado exitosamente'
            if u_fields:
                Business.objects.using(dbcon).filter(pk=mobj.pk).update(**u_fields)
            if u_fields and files:
                msg = 'Negocio y logo actualizados exitosamente'
        else:
            mobj = Business.objects.using(dbcon).create(**uc_fields)

        # Handle logo file upload
        if files:
            for name, fobj in files.items():
                fname = f'business_{mobj.id}_{fobj.name}'
                dfobj = File(fobj, name=fname)
                setattr(mobj, name, dfobj)
            mobj.save()

        # Get user profile
        profile = UserProfile.objects.using(dbcon).filter(username=userobj.username).first()
        if not profile:
            return {'error': 'Perfil de usuario no encontrado'}, args, kwargs

        # Deactivate all other businesses for this user
        UserBusiness.objects.using(dbcon).filter(userprofileobj=profile).update(active=False)

        # Check if UserBusiness already exists
        user_business, created = UserBusiness.objects.using(dbcon).get_or_create(
            userprofileobj=profile,
            businessobj=mobj,
            defaults={'active': True}
        )
        if not created:
            user_business.active = True
            user_business.save()

        # Clear session flag if exists
        if request and 'needs_business_setup' in request.session:
            request.session['needs_business_setup'] = False
            request.session.modified = True

        return {
            'success': f'Negocio {mobj.name} creado y asignado exitosamente',
            'record_id': mobj.id
        }, args, kwargs
