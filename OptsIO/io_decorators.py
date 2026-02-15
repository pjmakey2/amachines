import logging, traceback
from django.contrib.auth.models import User
from django.shortcuts import render
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken
from rest_framework import status
from django.contrib.auth.views import redirect_to_login
from functools import wraps
from django.shortcuts import HttpResponse
from datetime import datetime
from OptsIO.io_json import to_json
from OptsIO.models import TrackBtask
from sentry_sdk import capture_exception
from django.core.serializers.json import DjangoJSONEncoder
#from FL_Structure.models import Clientes, Usuarios
from django.core.cache import caches
rcd = caches['default']


def tracktask(func):
    def wrapped_view(*args, **kwargs):
        task_id = kwargs.get('task_id')
        if task_id:
            userobj = kwargs.get('userobj')
            cobj, created = TrackBtask.objects.get_or_create(task_id=task_id)
            if created:
                cobj.task_id = task_id
                cobj.created_at = datetime.now()
                cobj.username = userobj.username if userobj else 'ND'
                cobj.module = func.__module__
                cobj.package = func.__module__
                cobj.attr = args[0].__class__.__name__
                cobj.mname = kwargs.get('mname')
                if args[1:]:
                    cobj.args = to_json(args[1:])
                if kwargs:
                    cobj.kwargs = to_json(kwargs)
                cobj.state = 'STARTED'
            cobj.save()
        resp = func(*args, **kwargs)
        if task_id:
            cobj, created = TrackBtask.objects.get_or_create(task_id=task_id)
            cobj.updated_at = datetime.now()
            cobj.state = 'SUCCESS'
            cobj.save()
        return resp
    return wrapped_view


def set_agent(func):
    def wrapped_view(*args, **kwargs):
        request = args[0]
        agent = request.META['HTTP_USER_AGENT']
        request.META['is_mobile'] = False
        if agent.lower().find('android') > 0:
            request.META['is_mobile'] = True
        return func(*args, **kwargs)
    return wrapped_view

def grab_error(func):
    def wrapped_view(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            request = args[0]
            jsonp = request.POST.get('jsonp')
            logging.error("An error occurred:\n%s", traceback.format_exc())
            capture_exception()
            response = {'error': '{}'.format(e)}
            if jsonp:
                jsondata = jsonp+'('+to_json(response)+');'
                return HttpResponse(jsondata, content_type='application/javascript')
            return HttpResponse(to_json(response), content_type='application/javascript')
    return wrapped_view


def set_fl_client(func):
    def wrapped_view(*args, **kwargs):
        try:
            request = args[0]
            userobj = request.user
        except:
            userobj = kwargs.get('userobj')
        try:
            cl_fl = Clientes.objects.using('fl').get(clientemail=userobj.username)
        except Clientes.MultipleObjectsReturned:
            cl_fl = Clientes.objects.filter(clientemail=userobj.username).order_by('clientecodigo').first()
        except Clientes.DoesNotExist:
            return func(*args, **kwargs)
        userobj.clientecodigo = cl_fl.clientecodigo
        userobj.first_name = cl_fl.clientenombre
        userobj.last_name = cl_fl.clienteapellido
        userobj.completo = cl_fl.completo
        userobj.normalize_name_little = cl_fl.normalize_name_little()
        request.user = userobj
        args = list(args)
        args[0] = request
        return func(*args, **kwargs)
    return wrapped_view

def set_fl_user(func):
    def wrapped_view(*args, **kwargs):
        try:
            request = args[0]
            userobj = request.user
        except:
            userobj = kwargs.get('userobj')
        fluser = rcd.get(f'fluser_{request.user.username}')
        return func(*args, **kwargs)
    return wrapped_view


def cl_login_required(login_url=None):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                # Redirect to the specified login URL
                return redirect_to_login(request.get_full_path(), login_url)
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator


def token_validation(setr='json'):
    def t_decorator(view_func):
        @wraps(view_func)
        def wrapped_view(request, *args, **kwargs):
            #refresh_token = request.COOKIES.get("refresh_token")
            refresh_token = request.headers.get('Authorization')
            if not refresh_token:
                if setr == 'json':
                    return HttpResponse(to_json({'error': 'sin token, debe loguearse de nuevo'}), 
                                        status=status.HTTP_401_UNAUTHORIZED,
                                        content_type='application/javascript'
                                        )
                return render(request, "OptsIO/LoginUi.html", {}, status=401)

            try:
                # Validate refresh token
                token = RefreshToken(refresh_token)
                user_id = token['user_id']
                request.user = User.objects.get(id=user_id)
                # Optionally also issue new access token here
                request.new_access_token = str(token.access_token)
            except (TokenError, InvalidToken, User.DoesNotExist) as e:
                logging.error(f'Token {refresh_token} error: {e}')
                if setr == 'json':
                    return HttpResponse(to_json({'error': 'token invalido, debe loguearse'}), 
                                        status=status.HTTP_401_UNAUTHORIZED,
                                        content_type='application/javascript'
                                        )
                return render(request, "OptsIO/LoginUi.html", {}, status=401)
            return view_func(request, *args, **kwargs)
        return wrapped_view
    return t_decorator