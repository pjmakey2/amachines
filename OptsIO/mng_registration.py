"""User Registration Management"""
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password
from OptsIO.models import UserProfile, UserBusiness
from OptsIO.io_json import from_json
from datetime import datetime
import re
import logging

log = logging.getLogger(__name__)

class MRegistration:
    """User Registration Management Class"""

    def check_username_available(self, *args, **kwargs) -> dict:
        """
        Check if username is available
        """
        q: dict = kwargs.get('qdict', {})
        username = q.get('username', '').strip().lower()

        if not username:
            return {'error': 'Usuario requerido'}

        if len(username) < 4:
            return {'error': 'El usuario debe tener al menos 4 caracteres'}

        if User.objects.filter(username=username).exists():
            return {'error': 'Este usuario ya está registrado'}

        return {'success': 'Usuario disponible'}

    def check_email_available(self, *args, **kwargs) -> dict:
        """
        Check if email is available and not suspended
        """
        q: dict = kwargs.get('qdict', {})
        email = q.get('email', '').strip().lower()

        if not email:
            return {'error': 'Email requerido'}

        email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_regex, email):
            return {'error': 'Formato de email inválido'}

        user = User.objects.filter(email=email).first()
        if user:
            if not user.is_active:
                return {'error': 'Esta cuenta está suspendida. Contacte al administrador'}
            return {'error': 'Este email ya está registrado'}

        return {'success': 'Email disponible'}

    def validate_password_strength(self, *args, **kwargs) -> dict:
        """
        Validate password complexity
        - Minimum 8 characters
        - At least one uppercase letter
        - At least one lowercase letter
        - At least one number
        - At least one special character
        """
        q: dict = kwargs.get('qdict', {})
        password = q.get('password', '')

        if len(password) < 8:
            return {'error': 'La contraseña debe tener al menos 8 caracteres'}

        if not re.search(r'[A-Z]', password):
            return {'error': 'La contraseña debe contener al menos una mayúscula'}

        if not re.search(r'[a-z]', password):
            return {'error': 'La contraseña debe contener al menos una minúscula'}

        if not re.search(r'[0-9]', password):
            return {'error': 'La contraseña debe contener al menos un número'}

        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            return {'error': 'La contraseña debe contener al menos un carácter especial (!@#$%^&*(),.?":{}|<>)'}

        return {'success': 'Contraseña válida'}

    def register_user(self, *args, **kwargs) -> dict:
        """
        Register new user with all validations
        """
        q: dict = kwargs.get('qdict', {})
        dbcon = q.get('dbcon', 'default')
        uc_fields: dict = from_json(q.get('uc_fields', {}))

        username = uc_fields.get('n_user', '').strip().lower()
        email = uc_fields.get('n_email', '').strip().lower()
        password = uc_fields.get('n_pass', '')
        first_name = uc_fields.get('first_name', '').strip()
        last_name = uc_fields.get('last_name', '').strip()

        # Update qdict for validation methods
        q['username'] = username
        q['email'] = email
        q['password'] = password

        # Validate username
        username_check = self.check_username_available(*args, **kwargs)
        if username_check.get('error'):
            return username_check

        # Validate email
        email_check = self.check_email_available(*args, **kwargs)
        if email_check.get('error'):
            return email_check

        # Validate password
        password_check = self.validate_password_strength(*args, **kwargs)
        if password_check.get('error'):
            return password_check

        # Validate required fields
        if not first_name:
            return {'error': 'Nombre es requerido'}

        if not last_name:
            return {'error': 'Apellido es requerido'}

        # Create User
        user = User.objects.create(
            username=username,
            email=email,
            first_name=first_name,
            last_name=last_name,
            password=make_password(password),
            is_active=True
        )

        # Create UserProfile
        profile = UserProfile.objects.using(dbcon).create(
            username=username,
            preferences={},
            last_change_password=datetime.now()
        )

        log.info(f'User registered: {username}')

        return {
            'success': 'Usuario registrado exitosamente. Ahora puede iniciar sesión',
            'user_id': user.id,
            'username': username
        }

    def check_user_has_business(self, *args, **kwargs) -> dict:
        """
        Check if user has at least one business configured
        """
        userobj = kwargs.get('userobj')
        q: dict = kwargs.get('qdict', {})
        dbcon = q.get('dbcon', 'default')

        profile = UserProfile.objects.using(dbcon).filter(username=userobj.username).first()
        if not profile:
            return {'has_business': False, 'needs_setup': True}

        user_businesses = UserBusiness.objects.using(dbcon).filter(
            userprofileobj=profile
        ).count()

        if user_businesses == 0:
            return {'has_business': False, 'needs_setup': True}

        return {'has_business': True, 'needs_setup': False}

    def get_active_business(self, *args, **kwargs) -> dict:
        """
        Get active business for the logged user
        """
        userobj = kwargs.get('userobj')
        q: dict = kwargs.get('qdict', {})
        dbcon = q.get('dbcon', 'default')

        profile = UserProfile.objects.using(dbcon).filter(username=userobj.username).first()
        if not profile:
            return {'error': 'Perfil de usuario no encontrado'}

        active_business = UserBusiness.objects.using(dbcon).filter(
            userprofileobj=profile,
            active=True
        ).select_related('businessobj').first()

        if not active_business:
            return {'info': 'No hay negocio activo configurado'}

        business_data = {
            'business_id': active_business.businessobj.id,
            'business_name': active_business.businessobj.name,
            'business_ruc': active_business.businessobj.ruc,
            'user_business_id': active_business.id
        }

        # Add logo URL if exists
        if active_business.businessobj.logo:
            business_data['business_logo'] = active_business.businessobj.logo.url
        else:
            business_data['business_logo'] = None

        return business_data

    def get_user_businesses(self, *args, **kwargs) -> dict:
        """
        Get all businesses for the logged user
        """
        userobj = kwargs.get('userobj')
        q: dict = kwargs.get('qdict', {})
        dbcon = q.get('dbcon', 'default')

        profile = UserProfile.objects.using(dbcon).filter(username=userobj.username).first()
        if not profile:
            return {'businesses': []}

        businesses = UserBusiness.objects.using(dbcon).filter(
            userprofileobj=profile
        ).select_related('businessobj').values(
            'id',
            'businessobj__id',
            'businessobj__name',
            'businessobj__ruc',
            'active'
        )

        return {'businesses': list(businesses)}

    def set_active_business(self, *args, **kwargs) -> dict:
        """
        Set a business as active for the user
        """
        userobj = kwargs.get('userobj')
        q: dict = kwargs.get('qdict', {})
        dbcon = q.get('dbcon', 'default')
        business_id = q.get('business_id', '')

        if not business_id:
            return {'error': 'ID de negocio requerido'}

        profile = UserProfile.objects.using(dbcon).filter(username=userobj.username).first()
        if not profile:
            return {'error': 'Perfil de usuario no encontrado'}

        # Deactivate all businesses for this user
        UserBusiness.objects.using(dbcon).filter(
            userprofileobj=profile
        ).update(active=False)

        # Activate the selected business
        user_business = UserBusiness.objects.using(dbcon).filter(
            userprofileobj=profile,
            businessobj_id=business_id
        ).first()

        if not user_business:
            return {'error': 'Negocio no encontrado para este usuario'}

        user_business.active = True
        user_business.save()

        return {'success': 'Negocio activado exitosamente'}

    def get_businesses_by_username(self, *args, **kwargs) -> dict:
        """
        Get all businesses for a user by username (for login flow)
        This is called BEFORE full authentication
        """
        q: dict = kwargs.get('qdict', {})
        username = q.get('username', '').strip().lower()
        dbcon = q.get('dbcon', 'default')

        if not username:
            return {'error': 'Usuario requerido'}

        # Check if user exists
        user = User.objects.filter(username=username).first()
        if not user:
            return {'businesses': []}

        # Get UserProfile
        profile = UserProfile.objects.using(dbcon).filter(username=username).first()
        if not profile:
            return {'businesses': []}

        # Get all businesses for this user with logo URL
        businesses = UserBusiness.objects.using(dbcon).filter(
            userprofileobj=profile
        ).select_related('businessobj').values(
            'id',
            'businessobj__id',
            'businessobj__name',
            'businessobj__ruc',
            'businessobj__logo',
            'active'
        )

        # Add logo URLs
        business_list = []
        for biz in businesses:
            business_data = dict(biz)
            # Get the actual Business object to access the logo URL
            from Sifen.models import Business
            business_obj = Business.objects.using(dbcon).filter(id=biz['businessobj__id']).first()
            if business_obj and business_obj.logo:
                business_data['logo_url'] = business_obj.logo.url
            else:
                business_data['logo_url'] = None
            business_list.append(business_data)

        return {'businesses': business_list}
