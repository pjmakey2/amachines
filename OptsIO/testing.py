"""Fixtures compartidos para tests de plugins multi-tenant."""
import json
import re
import shutil
import subprocess

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


def check_ui(testcase, user, template, model=None, pk=None, dattrs=None):
    """
    Renderiza un template por el endpoint real `dtmpl` (con `mobj` si se pasa pk) y valida
    la sintaxis del JavaScript resultante con node. Devuelve el HTML.
    """
    params = {'tmpl': template, 'raw': 'true', 'dattrs': json.dumps({'t_guid': 'dtable_test', **(dattrs or {})})}
    if pk:
        app, model_name = model
        params.update({'model_app_name': app, 'model_name': model_name, 'pk': pk, 'dbcon': 'default'})
    testcase.client.force_login(user)
    rsp = testcase.client.get('/io/dtmpl/', params)
    testcase.assertEqual(rsp.status_code, 200, template)
    html = rsp.content.decode()
    if shutil.which('node'):
        js = '\n;\n'.join(re.findall(r'<script[^>]*>(.*?)</script>', html, re.DOTALL))
        out = subprocess.run(['node', '--check', '-'], input=js, capture_output=True, text=True)
        testcase.assertEqual(out.returncode, 0, f"{template}: {out.stderr[:600]}")
    return html


def grid_records(testcase, user, app, model, fields, methods=(), mquery=()):
    """Pide registros igual que Grid.datatables_wrapper (iom -> IoG.get_records) y devuelve las filas."""
    testcase.client.force_login(user)
    rsp = testcase.client.post('/io/iom/', {
        'module': 'OptsIO', 'package': 'io_grid', 'attr': 'IoG', 'mname': 'get_records', 'format': 'datatables',
        'model_app_name': app, 'model_name': model, 'dbcon': 'default', 'fields': json.dumps(list(fields)),
        'methods': json.dumps(list(methods)), 'mquery': json.dumps(list(mquery)), 'draw': 1, 'start': 0, 'length': 100,
    })
    testcase.assertEqual(rsp.status_code, 200)
    return json.loads(rsp.content)['data']
