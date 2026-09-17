"""Fixtures compartidos para tests de plugins multi-tenant."""
from django.contrib.auth.models import User

from OptsIO.models import UserProfile, UserBusiness
from Sifen.models import Business, TipoContribuyente, ActividadEconomica, Ciudades


def make_business(ruc='80000001', name='Negocio Test') -> Business:
    return Business.objects.create(
        name=name, abbr=name[:10], ruc=ruc, ruc_dv=0, nombrefactura=name, nombrefantasia=name,
        correo='test@test.com', denominacion='Test',
        contribuyenteobj=TipoContribuyente.objects.get_or_create(codigo=2, tipo='Juridica')[0],
        actividadecoobj=ActividadEconomica.objects.get_or_create(codigo_actividad='1', nombre_actividad='Test')[0],
        ciudadobj=Ciudades.objects.get_or_create(codigo_ciudad=1, nombre_ciudad='Asuncion')[0],
    )


def make_user(username, business=None, superuser=False) -> User:
    """Usuario con UserProfile y, si se indica, `business` como negocio activo."""
    user = User.objects.create_user(username=username, password='x', is_superuser=superuser)
    profile, _ = UserProfile.objects.get_or_create(username=username)
    if business:
        UserBusiness.objects.create(userprofileobj=profile, businessobj=business, active=True)
    return user
