"""Resolucion del negocio activo y aislamiento multi-tenant para modelos con FK `businessobj`."""
from django.core.exceptions import FieldDoesNotExist


def get_active_business(userobj):
    """Business activo del usuario (UserBusiness.active) o None."""
    from OptsIO.models import UserProfile, UserBusiness
    username = getattr(userobj, 'username', None)
    if not username:
        return None
    ub = UserBusiness.objects.filter(
        userprofileobj__username=username, active=True
    ).select_related('businessobj').first()
    return ub.businessobj if ub else None


def is_tenant_model(model_class) -> bool:
    """Un modelo es por-negocio si declara la FK `businessobj`."""
    try:
        model_class._meta.get_field('businessobj')
        return True
    except FieldDoesNotExist:
        return False
