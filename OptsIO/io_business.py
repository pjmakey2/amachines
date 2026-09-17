"""Resolucion del negocio activo y aislamiento multi-tenant para modelos con FK `businessobj`."""
from django.core.exceptions import FieldDoesNotExist

from OptsIO.models import UserBusiness


def get_active_business(userobj):
    """Business activo del usuario (UserBusiness.active) o None."""
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


def user_label(userobj) -> str:
    """Valor para los campos <paso>_usuario (misma convencion que IOMaction: first_name)."""
    return getattr(userobj, 'first_name', '') or getattr(userobj, 'username', '') or ''
