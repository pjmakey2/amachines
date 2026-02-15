"""
Setup Views - Vistas para el proceso de configuración inicial del sistema
"""
from datetime import datetime
from django.shortcuts import render, redirect
from django.urls import reverse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from OptsIO.setup_manager import SetupManager
import json
import logging

logger = logging.getLogger(__name__)


@require_http_methods(["GET"])
def setup_index(request):
    """
    Vista principal de setup - Paso 1: Configuración de Base de Datos
    """
    setup_manager = SetupManager()

    # Si ya está completado, redirigir al login
    if setup_manager.is_setup_completed():
        return redirect('glogin')

    context = {
        'step': 1,
        'title': 'Configuración Inicial - Amachine ERP',
        'page_title': 'Paso 1: Configuración de Base de Datos'
    }

    return render(request, 'OptsIO/SetupUi.html', context)


@csrf_exempt
@require_http_methods(["POST"])
def setup_validate_database(request):
    """
    Ajax endpoint para validar conexión a base de datos
    """
    try:
        data = json.loads(request.body)
        setup_manager = SetupManager()

        db_config = {
            'DB_NAME': data.get('db_name'),
            'DB_USER': data.get('db_user'),
            'DB_PASSWORD': data.get('db_password'),
            'DB_HOST': data.get('db_host'),
            'DB_PORT': data.get('db_port', '5432')
        }

        success, message = setup_manager.validate_database_connection(db_config)

        # Si la validación es exitosa, guardar config en archivo
        # (las sesiones no funcionan antes del setup: no existe django_session)
        if success:
            setup_manager.save_db_config(db_config)

        return JsonResponse({
            'success': success,
            'message': message
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error al validar: {str(e)}'
        }, status=400)


@csrf_exempt
@require_http_methods(["GET", "POST"])
def setup_step2(request):
    """
    Paso 2: Configuración de Usuario Administrador y opciones adicionales
    """
    setup_manager = SetupManager()

    # Si ya está completado, redirigir
    if setup_manager.is_setup_completed():
        return redirect('glogin')

    if request.method == 'GET':
        # Obtener configuración de BD desde archivo (sesiones no funcionan antes del setup)
        db_config = setup_manager.load_db_config()

        if not db_config:
            return redirect('setup_index')

        context = {
            'step': 2,
            'title': 'Configuración Inicial - Amachine ERP',
            'page_title': 'Paso 2: Usuario Administrador',
            'db_config': db_config
        }

        return render(request, 'OptsIO/SetupStep2Ui.html', context)

    # POST - Procesar formulario
    if request.method == 'POST':
        try:
            # Obtener datos del formulario
            db_config = {
                'DB_NAME': request.POST.get('db_name'),
                'DB_USER': request.POST.get('db_user'),
                'DB_PASSWORD': request.POST.get('db_password'),
                'DB_HOST': request.POST.get('db_host'),
                'DB_PORT': request.POST.get('db_port', '5432')
            }

            # Guardar config de BD en archivo
            setup_manager.save_db_config(db_config)

            # Si solo estamos guardando la config (viene de step 1)
            if request.POST.get('save_session_only') == '1':
                return JsonResponse({
                    'success': True,
                    'message': 'Configuración de BD guardada'
                })

            # Validar conexión nuevamente
            success, message = setup_manager.validate_database_connection(db_config)
            if not success:
                return JsonResponse({
                    'success': False,
                    'message': f'Error de conexión a BD: {message}'
                }, status=400)

            # Guardar configuración adicional
            extra_config = {
                'REDIS_HOST': request.POST.get('redis_host', '127.0.0.1'),
                'REDIS_PORT': request.POST.get('redis_port', '6379'),
                'FDOMAIN': request.POST.get('fdomain', 'http://localhost:8000'),
            }

            # Ejecutar setup inicial (crea .env)
            result = setup_manager.complete_setup(
                db_config=db_config,
                admin_config={},
                extra_config=extra_config
            )

            if not result['success']:
                return JsonResponse({
                    'success': False,
                    'message': 'Error en setup: ' + ', '.join(result['errors'])
                }, status=400)

            # Guardar info del admin en sesión Y en archivo temporal
            # (el archivo es necesario porque la sesión se invalida al cambiar SECRET_KEY)
            admin_config = {
                'username': request.POST.get('admin_username'),
                'email': request.POST.get('admin_email'),
                'password': request.POST.get('admin_password')
            }
            request.session['setup_admin_config'] = admin_config
            setup_manager.save_admin_config(admin_config)

            return JsonResponse({
                'success': True,
                'message': 'Configuración guardada. El servidor necesita reiniciarse.',
                'needs_restart': True,
                'next_step': '/setup/finalize/'
            })

        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error al procesar setup: {str(e)}'
            }, status=500)


@csrf_exempt
@require_http_methods(["GET", "POST"])
def setup_finalize(request):
    """
    Paso final: Ejecutar migraciones, crear usuario admin y menús
    Se ejecuta después del reinicio del servidor
    """
    setup_manager = SetupManager()

    # Si ya está completado, redirigir
    if setup_manager.is_setup_completed():
        return redirect('glogin')

    if request.method == 'GET':
        # Verificar que tengamos la config del admin (sesión o archivo)
        admin_config = request.session.get('setup_admin_config')
        if not admin_config:
            # Intentar cargar desde archivo (la sesión se invalida al cambiar SECRET_KEY)
            admin_config = setup_manager.load_admin_config()

        if not admin_config:
            return redirect('setup_index')

        context = {
            'step': 3,
            'title': 'Configuración Inicial - Amachine ERP',
            'page_title': 'Paso 3: Finalizar Configuración',
            'admin_username': admin_config.get('username')
        }

        return render(request, 'OptsIO/SetupFinalizeUi.html', context)

    # POST - Ejecutar finalización
    if request.method == 'POST':
        try:
            # Cargar config del admin (sesión o archivo)
            admin_config = request.session.get('setup_admin_config')
            if not admin_config:
                admin_config = setup_manager.load_admin_config()

            if not admin_config:
                return JsonResponse({
                    'success': False,
                    'message': 'Configuración de admin no encontrada. Por favor, reinicie el proceso de setup.'
                }, status=400)

            # Ejecutar finalización CON carga de datos de referencia
            result = setup_manager.finalize_setup_with_reference_data(admin_config)

            if result['success']:
                # NO limpiar sesión todavía, se necesita para business
                # request.session.pop('setup_db_config', None)
                # request.session.pop('setup_admin_config', None)

                return JsonResponse({
                    'success': True,
                    'message': 'Datos de referencia cargados. Configure su empresa a continuación.',
                    'steps': result['steps'],
                    'redirect': '/setup/business/'  # Redirigir a config de negocio
                })
            else:
                return JsonResponse({
                    'success': False,
                    'message': 'Error en finalización: ' + ', '.join(result['errors']),
                    'steps': result['steps']
                }, status=400)

        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error al finalizar setup: {str(e)}'
            }, status=500)


@csrf_exempt
@require_http_methods(["GET", "POST"])
def setup_business(request):
    """
    Paso 4: Configuración del primer Business (empresa)
    Se ejecuta después de la carga de datos de referencia.
    Todas las operaciones de BD se hacen via subprocess porque
    el servidor web usa SQLite mientras PostgreSQL tiene los datos.
    """
    setup_manager = SetupManager()

    # Si ya está completado, redirigir
    if setup_manager.is_setup_completed():
        return redirect('glogin')

    if request.method == 'GET':
        # Obtener opciones para los selects via subprocess
        options = setup_manager.get_business_form_options()

        context = {
            'step': 4,
            'title': 'Configuración Inicial - Amachine ERP',
            'page_title': 'Paso 4: Configurar Empresa',
            'contribuyentes': options.get('contribuyentes', []),
            'actividades': options.get('actividades', []),
            'departamentos': options.get('departamentos', []),
        }

        return render(request, 'OptsIO/SetupBusinessUi.html', context)

    # POST - Crear Business via subprocess
    if request.method == 'POST':
        try:
            # Recolectar datos del formulario
            business_data = {
                'name': request.POST.get('name'),
                'abbr': request.POST.get('abbr', ''),
                'ruc': request.POST.get('ruc'),
                'ruc_dv': request.POST.get('ruc_dv'),
                'contribuyente_codigo': request.POST.get('contribuyente'),
                'actividad_id': request.POST.get('actividad'),
                'ciudad_id': request.POST.get('ciudad'),
                'nombrefactura': request.POST.get('nombrefactura', ''),
                'nombrefantasia': request.POST.get('nombrefantasia', ''),
                'numero_casa': request.POST.get('numero_casa', ''),
                'direccion': request.POST.get('direccion'),
                'telefono': request.POST.get('telefono', ''),
                'celular': request.POST.get('celular', ''),
                'correo': request.POST.get('correo'),
                'web': request.POST.get('web', ''),
                'denominacion': request.POST.get('denominacion', ''),
            }

            # Manejar carga de logo
            logo_temp_path = None
            if 'logo' in request.FILES:
                logo_file = request.FILES['logo']
                # Guardar temporalmente el logo
                logo_temp_path = setup_manager.save_temp_logo(logo_file)

            # Crear Business via subprocess
            result = setup_manager.create_business_subprocess(business_data, logo_temp_path=logo_temp_path)

            if result['success']:
                # Marcar setup como completado y limpiar archivos temporales
                setup_manager.mark_setup_completed()
                setup_manager.cleanup_admin_config()

                return JsonResponse({
                    'success': True,
                    'message': result['message'],
                    'redirect': reverse('glogin')
                })
            else:
                return JsonResponse({
                    'success': False,
                    'message': result['message']
                }, status=400)

        except Exception as e:
            logger.exception("Error creando Business en setup")
            return JsonResponse({
                'success': False,
                'message': f'Error al crear empresa: {str(e)}'
            }, status=500)


@require_http_methods(["GET"])
def setup_reference_data_status(request):
    """
    API endpoint para obtener el estado de los datos de referencia
    """
    setup_manager = SetupManager()

    ref_data_list = setup_manager.get_reference_data_list()

    status = []
    for ref_data in ref_data_list:
        status.append({
            'name': ref_data['name'],
            'display_name': ref_data.get('display_name', ref_data['name']),
            'loaded': setup_manager.is_reference_data_loaded(ref_data['name']),
            'required': ref_data.get('required', False),
        })

    return JsonResponse({
        'success': True,
        'reference_data': status
    })
