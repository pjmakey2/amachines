"""
Middleware para Amachine ERP
"""
import os
from django.shortcuts import redirect
from django.core.management import call_command
from OptsIO.setup_manager import SetupManager


class SetupCheckMiddleware:
    """
    Middleware para verificar si el sistema está configurado
    Redirige a /setup si no se ha completado la configuración inicial
    """

    # Flag de clase para ejecutar migraciones solo una vez por proceso
    _migrations_checked = False

    def __init__(self, get_response=None):
        self.get_response = get_response
        self.setup_manager = SetupManager()

        # URLs que no requieren setup completado
        self.whitelist = [
            '/setup/',
            '/setup/step1/',
            '/setup/step2/',
            '/setup/finalize/',
            '/setup/business/',
            '/setup/validate-db/',
            '/setup/reference-data-status/',
            '/api_iom/',  # Para búsquedas select2 durante setup
            '/static/',
            '/media/',
        ]

    def __call__(self, request):
        # Si el setup ya está completado, continuar normalmente
        if self.setup_manager.is_setup_completed():
            return self.get_response(request)

        # Setup no completado - asegurar que las migraciones estén aplicadas
        # (solo se ejecuta una vez por proceso)
        self._ensure_setup_migrations()

        # Verificar si la URL actual está en whitelist
        path = request.path
        if any(path.startswith(url) for url in self.whitelist):
            return self.get_response(request)

        # Redirigir a setup
        return redirect('/setup/')

    def _ensure_setup_migrations(self):
        """
        Asegura que las migraciones estén aplicadas en la base de datos temporal
        durante el setup. Solo se ejecuta una vez por proceso.
        """
        if SetupCheckMiddleware._migrations_checked:
            return

        SetupCheckMiddleware._migrations_checked = True

        # Solo ejecutar si no hay .env (modo setup)
        from django.conf import settings
        env_path = os.path.join(settings.BASE_DIR, '.env')

        if not os.path.exists(env_path):
            try:
                # Ejecutar migraciones silenciosamente
                call_command('migrate', '--run-syncdb', verbosity=0)
            except Exception as e:
                # Log error pero no fallar - el setup mostrará el error apropiado
                print(f"[SetupMiddleware] Error running migrations: {e}")

    def process_request(self, request):
        pass