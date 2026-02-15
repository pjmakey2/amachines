import importlib, os
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import IsAuthenticated
from django.core.files import File
from .io_decorators import grab_error,set_fl_user, token_validation
from .io_json import to_json, from_json
from .io_execution import IoE
from .mng_registration import MRegistration
from .io_rpt import IoRpt
from django.shortcuts import render, HttpResponse, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.template.loader import render_to_string
import uuid, json
from random import randint
from django.apps import apps
from django.conf import settings
from django.http import JsonResponse
from django.middleware.csrf import get_token


get_model = apps.get_model


# Create your views here.

@grab_error
@set_fl_user
def dtmpl(request, from_hub=False):
    #rr = randint(1, 999)
    rr = str(uuid.uuid4()).replace('-', '')[0:5]
    # if not request.user.is_authenticated:
    #     return render(request, "AuthUi.html", {'rr': rr})
    g = request.GET
    tmpl = g.get('tmpl')
    if not tmpl:
        tmpl = 'UI.html'
    dattrs = g.get('dattrs')
    uid = int(uuid.uuid4())
    qdict = {}
    qdict.update({'uuid': uid, 'rr': rr })
    if dattrs:
        qdict.update(from_json(dattrs))
    if g.get('model_app_name') and g.get('model_name'):
        model_app_name: str = g.get("model_app_name", '')
        model_name: str = g.get("model_name", '')
        pk: str = g.get("pk", '')
        dbcon: str = g.get("dbcon", "default")
        appobj = apps.get_app_config(model_app_name)
        model_class = appobj.get_model(model_name)
        mobj = model_class.objects.using(dbcon).get(pk=pk)
        qdict.update({'mobj': mobj})
    if g.get('mobile_view'):
        qdict.update({'mobile_view': True})

    if g.get('specific_qdict'):
        specific_qdict = from_json(g.get('specific_qdict'))
        print(specific_qdict, type(specific_qdict), g.get('specific_qdict'))
        module = specific_qdict.get('module')
        package = specific_qdict.get('package')
        attr = specific_qdict.get('attr')
        mname = specific_qdict.get('mname')
        print(module, package, attr, mname)
        dobj = getattr(importlib.import_module(f'{module}.{package}'), attr)
        print(dobj)
        cls = dobj()
        dobj = getattr(cls, mname)
        print(dobj)
        print(dattrs)
        qdict.update(dobj(**from_json(dattrs)))

    if g.get('surround'):
        btmpl = f'{settings.BASE_DIR}/templates/tmp'
        surround = g.get('surround')
        rout = render_to_string(
                tmpl,
                context=qdict,
                request=request)
        rout = f'{{% extends "{surround}" %}}{{% block content %}}{rout}{{% endblock %}}'
        ttm = tmpl.split('/')[-1]
        tmpl = f'{btmpl}/{rr}{ttm}'
        with open(tmpl, 'w', encoding='utf-8') as ff:
            ff.write(rout)
    qdict.update({'from_hub': from_hub})
    if g.get('rpt_view'):
        return  HttpResponse(
            to_json(IoRpt().rpt_view(request)),
            content_type='application/javascript'
        )
    return render(request, tmpl, qdict)

@token_validation(setr='html')
def api_dtmpl(request):
    return dtmpl(request, from_hub=True)

@grab_error
@set_fl_user
def iom(request):
    if not request.user.is_authenticated:
        return HttpResponse(
                to_json({'error': 'Sin acceso'}),
                content_type='application/javascript')
    ioe = IoE()
    g = request.POST
    if (g.get('io_task')):
        tj = to_json(
            ioe.execute_task(
                request, 
                g.get('module'), 
                g.get('package'), 
                g.get('attr'), 
                g.get('chains'), 
                g.get('groups')
            )
        )
    else:
        tj = to_json(ioe.execute_module(request,
                                g.get('module'),
                                g.get('package'),
                                g.get('attr'),
                                mname=g.get('mname'),
                            ))
    return HttpResponse(tj, content_type='application/javascript')

@csrf_exempt
@token_validation()
def api_iom(request):
    return iom(request)

@csrf_exempt
@token_validation()
def api_isauth(request):
    return HttpResponse(
            to_json({'is_authenticated': True,
              'accessToken': request.POST.get('accessToken', ''),
              'refreshToken': request.POST.get('refreshToken', ''),
            }),
            content_type='application/javascript'
    )

def set_auth(request):
    if request.method == 'GET':
        return HttpResponse(to_json({'error': 'Get no implementado'}), content_type='application/javascript')
    post = request.POST
    email = post.get('email')
    password = post.get('password')
    userobj = authenticate(username=email, password=password)
    if not userobj: 
        return HttpResponse(to_json({'error': 'Acceso denegado'}), content_type='application/javascript')
    login(request, User.objects.get(username=userobj.funcionariocodigo))
    return HttpResponse(to_json({'exitos': 'Hecho!!'}), content_type='application/javascript')

def set_logout(request):
    logout(request)
    return HttpResponse(to_json({'exitos': 'Hecho!!'}), content_type='application/javascript')

def show_media_file(request, filename):
    try:
        wrapper = File(open(f'/{filename}', 'rb'))
    except Exception as e:
        return HttpResponse(json.dumps({'error': ['NO SE PUDO IMPRIMIR EL DOCUMENTO %s' % str(e)]}),
                            content_type='application/javascript' )
    response = HttpResponse(wrapper, content_type='application/image')
    response['Content-Disposition'] = 'attachment; filename="%s"' % filename.split('/')[-1]
    response['Content-Length'] = os.path.getsize('/%s' % filename)
    return response

def hub_ui(request):
    rr = str(uuid.uuid4()).replace('-', '')[0:5]
    return render(request, "FL_Hub/HubUi.html", {'rr': rr})

def glogin(request):
    if request.method == 'POST':
        post = request.POST
        username = post.get('username')
        password = post.get('password')
        # Debug logging
        print(f"[glogin] username='{username}', password_len={len(password) if password else 0}")
        print(f"[glogin] POST data: {dict(post)}")
        userobj = authenticate(username=username, password=password)
        print(f"[glogin] authenticate result: {userobj}")
        if not userobj:
            return HttpResponse(
                json.dumps({'error': 'Acceso denegado'}),
                content_type='application/javascript'
            )
        login(request, userobj)
        refresh = RefreshToken.for_user(userobj)
        request.user = userobj
        # Optionally also issue new access token here
        request.new_access_token = str(refresh.access_token)
        res = HttpResponse(
            json.dumps({'success': 'Hecho!!',
                        'refresh': str(refresh),
                        'access': str(refresh.access_token),
                        'username': userobj.username,
                        'first_name': userobj.first_name,
                        'last_name': userobj.last_name
                        }),
            content_type='application/javascript'
        )
        return res
    return render(request, "OptsIO/LoginUi.html", {})


@csrf_exempt
def glogout(request):
    if request.method == 'POST':
        logout(request)
        return HttpResponse(
            json.dumps({'success': 'Hecho!!'}),
            content_type='application/javascript'
        )
    return render(request, "LoginUi.html", {})

def gregister(request):
    """
    Registration view - handles GET (show form) and POST (register user)
    """
    if request.method == 'POST':
        mreg = MRegistration()
        action = request.POST.get('action', 'register')

        qdict = {
            'username': request.POST.get('username', ''),
            'email': request.POST.get('email', ''),
            'password': request.POST.get('password', ''),
            'uc_fields': request.POST.get('uc_fields', '{}'),
            'dbcon': 'default'
        }

        if action == 'check_username':
            result = mreg.check_username_available(qdict=qdict)
        elif action == 'check_email':
            result = mreg.check_email_available(qdict=qdict)
        elif action == 'register':
            result = mreg.register_user(qdict=qdict)
        else:
            result = {'error': 'Acción no válida'}

        return JsonResponse(result)

    return render(request, "OptsIO/RegistrationUi.html", {})

def base(request):
    """
    Vista principal del sistema.
    Si el usuario no está autenticado, redirige a login.
    Si está autenticado, muestra la interfaz base.
    """
    if not request.user.is_authenticated:
        return redirect('glogin')

    rr = str(uuid.uuid4()).replace('-', '')[0:5]
    return render(request, "BaseUi.html", {'rr': rr})
    