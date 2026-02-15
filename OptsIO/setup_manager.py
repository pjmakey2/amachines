"""
Setup Manager - Gestión de configuración inicial del sistema
Maneja la creación del archivo .env, validación de BD, migraciones y usuario admin inicial.
Integra con el sistema de plugins para carga de datos de referencia.
"""
import os
import sys
import secrets
import logging
import subprocess
from pathlib import Path
from typing import Dict, Tuple, List, Callable, Optional
import psycopg2
from django.conf import settings

logger = logging.getLogger(__name__)


class SetupManager:
    """Gestor de configuración inicial del sistema"""

    def __init__(self):
        self.base_dir = Path(__file__).resolve().parent.parent
        self.env_path = self.base_dir / '.env'
        self.setup_flag = self.base_dir / '.setup_completed'
        self.admin_config_file = self.base_dir / '.setup_admin_config.json'

    def save_db_config(self, db_config: Dict[str, str]) -> bool:
        """
        Guarda la configuración de BD en un archivo temporal.
        Necesario porque las sesiones de Django no funcionan antes del setup
        (no existe django_session en SQLite).
        """
        try:
            import json
            db_config_file = self.base_dir / '.setup_db_config.json'
            with open(db_config_file, 'w') as f:
                json.dump(db_config, f)
            return True
        except Exception as e:
            logger.exception("Error guardando db config")
            return False

    def load_db_config(self) -> Dict[str, str]:
        """Carga la configuración de BD desde el archivo temporal."""
        try:
            import json
            db_config_file = self.base_dir / '.setup_db_config.json'
            if db_config_file.exists():
                with open(db_config_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.exception("Error cargando db config")
        return {}

    def save_admin_config(self, admin_config: Dict[str, str]) -> bool:
        """
        Guarda la configuración del admin en un archivo temporal.
        Esto es necesario porque la sesión se invalida al cambiar SECRET_KEY.
        """
        try:
            import json
            with open(self.admin_config_file, 'w') as f:
                json.dump(admin_config, f)
            return True
        except Exception as e:
            logger.exception("Error guardando admin config")
            return False

    def load_admin_config(self) -> Dict[str, str]:
        """
        Carga la configuración del admin desde el archivo temporal.
        """
        try:
            import json
            if self.admin_config_file.exists():
                with open(self.admin_config_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.exception("Error cargando admin config")
        return {}

    def cleanup_admin_config(self):
        """
        Elimina los archivos temporales de configuración del setup.
        """
        try:
            if self.admin_config_file.exists():
                self.admin_config_file.unlink()
            db_config_file = self.base_dir / '.setup_db_config.json'
            if db_config_file.exists():
                db_config_file.unlink()
        except Exception as e:
            logger.exception("Error eliminando config files")

    def save_temp_logo(self, logo_file) -> Optional[str]:
        """
        Guarda el archivo de logo temporalmente para pasarlo al subprocess.

        Args:
            logo_file: Archivo de imagen subido

        Returns:
            Path del archivo temporal o None si hay error
        """
        try:
            import tempfile
            import shutil

            # Crear directorio temporal si no existe
            temp_dir = self.base_dir / 'media' / 'tmp'
            temp_dir.mkdir(parents=True, exist_ok=True)

            # Generar nombre único
            ext = Path(logo_file.name).suffix.lower()
            if ext not in ['.png', '.jpg', '.jpeg', '.gif', '.webp']:
                ext = '.png'

            temp_filename = f"setup_logo_{secrets.token_hex(8)}{ext}"
            temp_path = temp_dir / temp_filename

            # Guardar archivo
            with open(temp_path, 'wb') as f:
                for chunk in logo_file.chunks():
                    f.write(chunk)

            return str(temp_path)
        except Exception as e:
            logger.exception("Error guardando logo temporal")
            return None

    def cleanup_temp_logo(self, temp_path: str):
        """
        Elimina el archivo temporal del logo.
        """
        try:
            if temp_path and Path(temp_path).exists():
                Path(temp_path).unlink()
        except Exception as e:
            logger.exception("Error eliminando logo temporal")

    def is_setup_completed(self) -> bool:
        """Verifica si el setup ya fue completado"""
        return self.setup_flag.exists()

    def mark_setup_completed(self):
        """Marca el setup como completado"""
        self.setup_flag.touch()

    def mark_setup_incomplete(self):
        """Marca el setup como incompleto (para testing)"""
        if self.setup_flag.exists():
            self.setup_flag.unlink()

    def validate_database_connection(self, db_config: Dict[str, str]) -> Tuple[bool, str]:
        """
        Valida la conexión a la base de datos PostgreSQL

        Args:
            db_config: Diccionario con DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT

        Returns:
            Tuple (éxito: bool, mensaje: str)
        """
        try:
            conn = psycopg2.connect(
                dbname=db_config.get('DB_NAME', 'postgres'),
                user=db_config.get('DB_USER'),
                password=db_config.get('DB_PASSWORD'),
                host=db_config.get('DB_HOST'),
                port=db_config.get('DB_PORT', '5432')
            )
            conn.close()
            return True, "Conexión exitosa a la base de datos"
        except psycopg2.OperationalError as e:
            return False, f"Error de conexión: {str(e)}"
        except Exception as e:
            return False, f"Error inesperado: {str(e)}"

    def generate_secret_key(self) -> str:
        """Genera una SECRET_KEY segura para Django"""
        return secrets.token_urlsafe(50)

    def create_env_file(self, config: Dict[str, str]) -> Tuple[bool, str]:
        """
        Crea el archivo .env con la configuración proporcionada

        Args:
            config: Diccionario con todas las variables de entorno

        Returns:
            Tuple (éxito: bool, mensaje: str)
        """
        try:
            # Backup del .env existente si existe
            if self.env_path.exists():
                backup_path = self.base_dir / '.env.backup'
                self.env_path.rename(backup_path)

            # Generar SECRET_KEY si no se proporciona
            if not config.get('SECRET_KEY'):
                config['SECRET_KEY'] = self.generate_secret_key()

            # Escribir archivo .env
            env_content = self._build_env_content(config)

            with open(self.env_path, 'w') as f:
                f.write(env_content)

            return True, "Archivo .env creado exitosamente"

        except Exception as e:
            return False, f"Error al crear .env: {str(e)}"

    def _build_env_content(self, config: Dict[str, str]) -> str:
        """Construye el contenido del archivo .env"""

        # Valores por defecto
        defaults = {
            'DEBUG': 'True',
            'ALLOWED_HOSTS': 'localhost,127.0.0.1',
            'REDIS_HOST': '127.0.0.1',
            'REDIS_PORT': '6379',
            'DB_PORT': '5432',
            'FDOMAIN': 'http://localhost:8000',
            'CSRF_TRUSTED_ORIGINS': 'http://localhost:8000,http://127.0.0.1:8000'
        }

        # Merge con config proporcionado
        final_config = {**defaults, **config}

        # Construir Celery URLs desde Redis
        redis_host = final_config.get('REDIS_HOST')
        redis_port = final_config.get('REDIS_PORT')
        final_config['CELERY_BROKER_URL'] = f'redis://{redis_host}:{redis_port}/0'
        final_config['CELERY_RESULT_BACKEND'] = f'redis://{redis_host}:{redis_port}/0'

        # Template del archivo .env
        content = f"""# Django Settings
SECRET_KEY={final_config.get('SECRET_KEY')}
DEBUG={final_config.get('DEBUG')}
ALLOWED_HOSTS={final_config.get('ALLOWED_HOSTS')}

# Database
DB_NAME={final_config.get('DB_NAME')}
DB_USER={final_config.get('DB_USER')}
DB_PASSWORD={final_config.get('DB_PASSWORD')}
DB_HOST={final_config.get('DB_HOST')}
DB_PORT={final_config.get('DB_PORT')}

# Redis
REDIS_HOST={final_config.get('REDIS_HOST')}
REDIS_PORT={final_config.get('REDIS_PORT')}

# Celery
CELERY_BROKER_URL={final_config.get('CELERY_BROKER_URL')}
CELERY_RESULT_BACKEND={final_config.get('CELERY_RESULT_BACKEND')}

# SIFEN
SIFEN_KEY_PASS={final_config.get('SIFEN_KEY_PASS', 'cambiar-clave-sifen')}

# Email (Mailgun API)
MAILGUN_API_KEY={final_config.get('MAILGUN_API_KEY', 'tu-api-key-mailgun')}
MAILGUN_DOMAIN={final_config.get('MAILGUN_DOMAIN', 'tu-dominio-mailgun.com')}
DEFAULT_FROM_EMAIL={final_config.get('DEFAULT_FROM_EMAIL', 'noreply@amachine.com')}

# Sentry
SENTRY_DSN={final_config.get('SENTRY_DSN', '')}

# Domain
FDOMAIN={final_config.get('FDOMAIN')}

# CSRF Trusted Origins
CSRF_TRUSTED_ORIGINS={final_config.get('CSRF_TRUSTED_ORIGINS')}
"""
        return content

    def run_migrations(self) -> Tuple[bool, str]:
        """
        Ejecuta las migraciones de Django en PostgreSQL.
        Usa subprocess para ejecutar con la configuración correcta de BD.

        Returns:
            Tuple (éxito: bool, mensaje: str)
        """
        try:
            # Verificar que existe el .env
            if not self.env_path.exists():
                return False, "Archivo .env no encontrado. Complete el paso 2 primero."

            # Ejecutar migrate usando subprocess para que use el .env
            # Esto es necesario porque Django ya cargó con SQLite
            result = subprocess.run(
                [sys.executable, 'manage.py', 'migrate', '--noinput'],
                cwd=str(self.base_dir),
                capture_output=True,
                text=True,
                env={**os.environ, 'SETUP_RUNNING_MIGRATIONS': '1'}
            )

            if result.returncode != 0:
                error_msg = result.stderr or result.stdout
                return False, f"Error en migraciones: {error_msg}"

            return True, "Migraciones ejecutadas exitosamente"
        except Exception as e:
            return False, f"Error al ejecutar migraciones: {str(e)}"

    def create_superuser(self, username: str, email: str, password: str) -> Tuple[bool, str]:
        """
        Crea el superusuario administrador en PostgreSQL.
        Usa subprocess para ejecutar con la configuración correcta de BD.

        Args:
            username: Nombre de usuario
            email: Email del usuario
            password: Contraseña

        Returns:
            Tuple (éxito: bool, mensaje: str)
        """
        try:
            # Crear script Python temporal para crear el superuser
            script = f'''
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Amachine.settings')
os.environ['SETUP_RUNNING_MIGRATIONS'] = '1'
django.setup()
from django.contrib.auth import get_user_model
User = get_user_model()
if User.objects.filter(username="{username}").exists():
    print("EXISTS")
else:
    User.objects.create_superuser("{username}", "{email}", "{password}")
    print("CREATED")
'''
            result = subprocess.run(
                [sys.executable, '-c', script],
                cwd=str(self.base_dir),
                capture_output=True,
                text=True
            )

            if result.returncode != 0:
                error_msg = result.stderr or result.stdout
                return False, f"Error al crear superusuario: {error_msg}"

            output = result.stdout.strip()
            if output == "EXISTS":
                return True, f"El usuario '{username}' ya existe"
            elif output == "CREATED":
                return True, f"Superusuario '{username}' creado exitosamente"
            else:
                return False, f"Respuesta inesperada: {output}"

        except Exception as e:
            return False, f"Error al crear superusuario: {str(e)}"

    def setup_sifen_menu(self) -> Tuple[bool, str]:
        """
        Ejecuta el comando setup_sifen_menu para crear los menús del sistema.
        Usa subprocess para ejecutar con PostgreSQL.

        Returns:
            Tuple (éxito: bool, mensaje: str)
        """
        try:
            result = subprocess.run(
                [sys.executable, 'manage.py', 'setup_sifen_menu'],
                cwd=str(self.base_dir),
                capture_output=True,
                text=True,
                env={**os.environ, 'SETUP_RUNNING_MIGRATIONS': '1'}
            )

            if result.returncode != 0:
                error_msg = result.stderr or result.stdout
                return False, f"Error al crear menús: {error_msg}"

            return True, "Menús del sistema creados exitosamente"
        except Exception as e:
            return False, f"Error al crear menús: {str(e)}"

    def complete_setup(self,
                      db_config: Dict[str, str],
                      admin_config: Dict[str, str],
                      extra_config: Dict[str, str] = None) -> Dict[str, any]:
        """
        Ejecuta el proceso completo de setup

        Args:
            db_config: Configuración de base de datos
            admin_config: Configuración del usuario admin (username, email, password)
            extra_config: Configuración adicional opcional

        Returns:
            Dict con resultado del proceso
        """
        results = {
            'success': True,
            'steps': [],
            'errors': []
        }

        # 1. Validar conexión a BD
        success, msg = self.validate_database_connection(db_config)
        results['steps'].append({'step': 'Validar BD', 'success': success, 'message': msg})
        if not success:
            results['success'] = False
            results['errors'].append(msg)
            return results

        # 2. Crear archivo .env
        all_config = {**db_config, **(extra_config or {})}
        success, msg = self.create_env_file(all_config)
        results['steps'].append({'step': 'Crear .env', 'success': success, 'message': msg})
        if not success:
            results['success'] = False
            results['errors'].append(msg)
            return results

        # IMPORTANTE: Después de crear .env, se necesita reiniciar Django
        # para que tome las nuevas variables. En desarrollo esto requiere
        # reinicio manual del servidor.
        results['needs_restart'] = True
        results['steps'].append({
            'step': 'Reinicio requerido',
            'success': True,
            'message': 'El servidor necesita reiniciarse para aplicar la configuración'
        })

        # Los siguientes pasos se ejecutarán después del reinicio
        # Por ahora solo marcamos que están pendientes
        results['pending_steps'] = [
            'Ejecutar migraciones',
            'Crear superusuario',
            'Configurar menús del sistema'
        ]

        return results

    def finalize_setup(self, admin_config: Dict[str, str]) -> Dict[str, any]:
        """
        Finaliza el setup después del reinicio
        Ejecuta migraciones, crea superuser y menús

        Args:
            admin_config: Configuración del usuario admin

        Returns:
            Dict con resultado
        """
        results = {
            'success': True,
            'steps': [],
            'errors': []
        }

        # 1. Ejecutar migraciones
        success, msg = self.run_migrations()
        results['steps'].append({'step': 'Migraciones', 'success': success, 'message': msg})
        if not success:
            results['success'] = False
            results['errors'].append(msg)
            return results

        # 2. Crear superusuario
        success, msg = self.create_superuser(
            admin_config['username'],
            admin_config['email'],
            admin_config['password']
        )
        results['steps'].append({'step': 'Crear Admin', 'success': success, 'message': msg})
        if not success:
            results['success'] = False
            results['errors'].append(msg)
            return results

        # 3. Configurar menús
        success, msg = self.setup_sifen_menu()
        results['steps'].append({'step': 'Menús', 'success': success, 'message': msg})
        if not success:
            results['success'] = False
            results['errors'].append(msg)
            return results

        # 4. Marcar setup como completado
        self.mark_setup_completed()
        results['steps'].append({
            'step': 'Completar setup',
            'success': True,
            'message': 'Setup completado exitosamente'
        })

        return results

    # =========================================================================
    # SISTEMA DE PLUGINS Y DATOS DE REFERENCIA
    # =========================================================================

    def discover_and_register_plugins(self) -> Tuple[bool, str, Dict]:
        """
        Descubre y registra todos los plugins disponibles.

        Returns:
            Tuple (éxito, mensaje, estadísticas)
        """
        try:
            from OptsIO.plugin_manager import plugin_manager

            # Descubrir plugins
            discovered = plugin_manager.discover_plugins()

            # Registrar en BD
            created, updated = plugin_manager.register_plugins()

            return True, f"Plugins registrados: {created} nuevos, {updated} actualizados", {
                'discovered': len(discovered),
                'created': created,
                'updated': updated,
            }
        except Exception as e:
            logger.exception("Error al registrar plugins")
            return False, f"Error al registrar plugins: {str(e)}", {}

    def get_reference_data_list(self) -> List[Dict]:
        """
        Obtiene la lista de datos de referencia disponibles de todos los plugins.

        Returns:
            Lista de diccionarios con información de cada tipo de dato
        """
        try:
            from OptsIO.plugin_manager import plugin_manager

            # Asegurarse de que los plugins están descubiertos
            if not plugin_manager._plugins:
                plugin_manager.discover_plugins()

            return plugin_manager.get_all_reference_data()
        except Exception as e:
            logger.exception("Error obteniendo lista de datos de referencia")
            return []

    def is_reference_data_loaded(self, data_type: str) -> bool:
        """
        Verifica si un tipo de dato de referencia ya fue cargado.

        Args:
            data_type: Nombre del tipo de dato (ej: 'geografias', 'actividades')

        Returns:
            True si ya fue cargado
        """
        try:
            from OptsIO.plugin_manager import plugin_manager
            return plugin_manager.is_reference_data_loaded(data_type)
        except Exception as e:
            logger.exception(f"Error verificando estado de {data_type}")
            return False

    def load_reference_data(
        self,
        data_type: str,
        progress_callback: Optional[Callable[[int, str], None]] = None
    ) -> Tuple[bool, str, Dict]:
        """
        Carga un tipo específico de datos de referencia.

        Args:
            data_type: Nombre del tipo de dato a cargar
            progress_callback: Función opcional para reportar progreso (percent, message)

        Returns:
            Tuple (éxito, mensaje, estadísticas)
        """
        try:
            from OptsIO.plugin_manager import plugin_manager

            # Asegurarse de que los plugins están descubiertos
            if not plugin_manager._plugins:
                plugin_manager.discover_plugins()

            return plugin_manager.load_reference_data(data_type, progress_callback)
        except Exception as e:
            logger.exception(f"Error cargando datos de referencia: {data_type}")
            return False, f"Error: {str(e)}", {}

    def load_all_reference_data(
        self,
        progress_callback: Optional[Callable[[int, str], None]] = None
    ) -> Dict:
        """
        Carga todos los datos de referencia requeridos de todos los plugins.

        Args:
            progress_callback: Función para reportar progreso global

        Returns:
            Diccionario con resultados por tipo de dato
        """
        results = {
            'success': True,
            'steps': [],
            'errors': [],
            'stats': {}
        }

        ref_data_list = self.get_reference_data_list()

        # Ordenar por 'order' si existe
        ref_data_list.sort(key=lambda x: x.get('order', 999))

        total = len(ref_data_list)

        for idx, ref_data in enumerate(ref_data_list):
            data_type = ref_data['name']
            display_name = ref_data.get('display_name', data_type)

            # Calcular progreso global
            global_progress = int((idx / total) * 100)
            if progress_callback:
                progress_callback(global_progress, f"Cargando {display_name}...")

            # Verificar si ya está cargado
            if self.is_reference_data_loaded(data_type):
                results['steps'].append({
                    'step': display_name,
                    'success': True,
                    'message': 'Ya estaba cargado',
                    'skipped': True
                })
                continue

            # Cargar datos
            success, message, stats = self.load_reference_data(data_type, None)

            results['steps'].append({
                'step': display_name,
                'success': success,
                'message': message
            })

            results['stats'][data_type] = stats

            if not success:
                results['errors'].append(f"{display_name}: {message}")
                # Para datos requeridos, fallar completamente
                if ref_data.get('required', False):
                    results['success'] = False

        if progress_callback:
            progress_callback(100, "Carga de datos completada")

        return results

    def finalize_setup_with_reference_data(
        self,
        admin_config: Dict[str, str],
        progress_callback: Optional[Callable[[int, str], None]] = None
    ) -> Dict:
        """
        Finaliza el setup incluyendo la carga de datos de referencia.
        TODO está se ejecuta vía subprocess para usar PostgreSQL.

        Args:
            admin_config: Configuración del usuario admin
            progress_callback: Función para reportar progreso

        Returns:
            Dict con resultado completo
        """
        results = {
            'success': True,
            'steps': [],
            'errors': []
        }

        # Verificar que existe el .env
        if not self.env_path.exists():
            results['success'] = False
            results['errors'].append("Archivo .env no encontrado")
            return results

        # Paso 1: Ejecutar migraciones
        if progress_callback:
            progress_callback(5, "Ejecutando migraciones...")

        success, msg = self.run_migrations()
        results['steps'].append({'step': 'Migraciones', 'success': success, 'message': msg})
        if not success:
            results['success'] = False
            results['errors'].append(msg)
            return results

        # Paso 2: Cargar datos de referencia y crear admin via subprocess
        if progress_callback:
            progress_callback(20, "Cargando datos de referencia...")

        script = f'''
import os
import sys
import json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Amachine.settings')
os.environ['SETUP_RUNNING_MIGRATIONS'] = '1'

import django
django.setup()

results = {{"steps": [], "errors": [], "success": True}}

# Cargar datos de referencia
try:
    from Sifen.plugin import Plugin as SifenPlugin
    plugin = SifenPlugin()

    ref_data_items = [
        ('tipo_contribuyente', 'Tipos de Contribuyente'),
        ('geografias', 'Geografías'),
        ('actividades', 'Actividades Económicas'),
        ('medidas', 'Unidades de Medida'),
        ('porcentaje_iva', 'Porcentajes IVA'),
        ('metodos_pago', 'Métodos de Pago'),
    ]

    for data_name, display_name in ref_data_items:
        try:
            success, message, stats = plugin.load_reference_data(data_name)
            results["steps"].append({{"step": display_name, "success": success, "message": message}})
            if not success:
                results["errors"].append(f"{{display_name}}: {{message}}")
        except Exception as e:
            results["steps"].append({{"step": display_name, "success": False, "message": str(e)}})
            results["errors"].append(f"{{display_name}}: {{str(e)}}")

except Exception as e:
    results["success"] = False
    results["errors"].append(f"Error cargando datos: {{str(e)}}")

# Crear superusuario
try:
    from django.contrib.auth import get_user_model
    User = get_user_model()
    username = "{admin_config['username']}"
    email = "{admin_config['email']}"
    password = "{admin_config['password']}"

    if User.objects.filter(username=username).exists():
        results["steps"].append({{"step": "Crear Admin", "success": True, "message": f"Usuario '{{username}}' ya existe"}})
    else:
        User.objects.create_superuser(username, email, password)
        results["steps"].append({{"step": "Crear Admin", "success": True, "message": f"Usuario '{{username}}' creado"}})
except Exception as e:
    results["steps"].append({{"step": "Crear Admin", "success": False, "message": str(e)}})
    results["errors"].append(f"Error creando admin: {{str(e)}}")

# Crear menús
try:
    from django.core.management import call_command
    call_command('setup_sifen_menu', verbosity=0)
    results["steps"].append({{"step": "Menús", "success": True, "message": "Menús creados"}})
except Exception as e:
    results["steps"].append({{"step": "Menús", "success": False, "message": str(e)}})
    results["errors"].append(f"Error creando menús: {{str(e)}}")

print(json.dumps(results))
'''

        try:
            result = subprocess.run(
                [sys.executable, '-c', script],
                cwd=str(self.base_dir),
                capture_output=True,
                text=True,
                timeout=300  # 5 minutos máximo
            )

            if result.returncode != 0:
                results['success'] = False
                results['errors'].append(f"Error en subprocess: {result.stderr}")
                return results

            # Parsear resultado JSON
            import json
            try:
                subprocess_results = json.loads(result.stdout.strip())
                results['steps'].extend(subprocess_results.get('steps', []))
                results['errors'].extend(subprocess_results.get('errors', []))
                if subprocess_results.get('errors'):
                    results['success'] = False
            except json.JSONDecodeError:
                results['steps'].append({
                    'step': 'Datos y Admin',
                    'success': True,
                    'message': 'Proceso completado'
                })

        except subprocess.TimeoutExpired:
            results['success'] = False
            results['errors'].append("Timeout al cargar datos")
            return results
        except Exception as e:
            results['success'] = False
            results['errors'].append(f"Error: {str(e)}")
            return results

        if progress_callback:
            progress_callback(90, "Finalizando...")

        # NO marcar como completado aquí - eso se hace en setup_business
        results['steps'].append({
            'step': 'Datos de Referencia',
            'success': True,
            'message': 'Datos cargados. Configure su empresa.'
        })

        if progress_callback:
            progress_callback(100, "Listo")

        return results

    def get_business_form_options(self) -> Dict:
        """
        Obtiene las opciones para el formulario de Business via subprocess.
        Consulta PostgreSQL para obtener contribuyentes, actividades y departamentos.

        Returns:
            Dict con listas de opciones
        """
        script = '''
import os
import sys
import json
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Amachine.settings')
os.environ['SETUP_RUNNING_MIGRATIONS'] = '1'

import django
django.setup()

from Sifen.models import TipoContribuyente, ActividadEconomica, Departamentos, Distrito, Ciudades
from collections import defaultdict

result = {
    'contribuyentes': [],
    'actividades': [],
    'departamentos': []
}

# Tipos de contribuyente
try:
    for tc in TipoContribuyente.objects.all().order_by('codigo'):
        result['contribuyentes'].append({
            'codigo': tc.codigo,
            'descripcion': tc.tipo
        })
    sys.stderr.write(f"Contribuyentes: {len(result['contribuyentes'])}\\n")
except Exception as e:
    sys.stderr.write(f"Error contribuyentes: {e}\\n")

# Actividades económicas
try:
    for ae in ActividadEconomica.objects.all().order_by('codigo_actividad'):
        result['actividades'].append({
            'id': ae.id,
            'codigo': ae.codigo_actividad,
            'descripcion': ae.nombre_actividad[:100] if ae.nombre_actividad else ''
        })
    sys.stderr.write(f"Actividades: {len(result['actividades'])}\\n")
except Exception as e:
    sys.stderr.write(f"Error actividades: {e}\\n")

# Departamentos con ciudades - query optimizada (evita N+1)
try:
    dep_count = Departamentos.objects.count()
    sys.stderr.write(f"Departamentos count: {dep_count}\\n")

    # Pre-cargar todas las ciudades agrupadas por departamento
    # via: Ciudad -> Distrito -> Departamento
    ciudades_por_dep = defaultdict(list)
    for ciudad in Ciudades.objects.select_related('distritoobj__dptoobj').order_by('nombre_ciudad'):
        dep_codigo = ciudad.distritoobj.dptoobj.codigo_departamento
        ciudades_por_dep[dep_codigo].append({
            'id': ciudad.id,
            'descripcion': ciudad.nombre_ciudad
        })

    sys.stderr.write(f"Ciudades cargadas: {sum(len(v) for v in ciudades_por_dep.values())}\\n")

    for dep in Departamentos.objects.all().order_by('nombre_departamento'):
        result['departamentos'].append({
            'codigo': dep.codigo_departamento,
            'descripcion': dep.nombre_departamento,
            'ciudades': ciudades_por_dep.get(dep.codigo_departamento, [])
        })
    sys.stderr.write(f"Departamentos: {len(result['departamentos'])}\\n")
except Exception as e:
    sys.stderr.write(f"Error departamentos: {e}\\n")
    import traceback
    traceback.print_exc(file=sys.stderr)

print(json.dumps(result))
'''
        try:
            result = subprocess.run(
                [sys.executable, '-c', script],
                cwd=str(self.base_dir),
                capture_output=True,
                text=True,
                timeout=120
            )

            if result.stderr:
                logger.info(f"Subprocess stderr: {result.stderr}")

            if result.returncode == 0:
                import json
                data = json.loads(result.stdout.strip())
                logger.info(
                    f"Opciones cargadas: {len(data.get('contribuyentes', []))} contribuyentes, "
                    f"{len(data.get('actividades', []))} actividades, "
                    f"{len(data.get('departamentos', []))} departamentos"
                )
                return data
            else:
                logger.error(f"Error obteniendo opciones (rc={result.returncode}): {result.stderr}")
                return {'contribuyentes': [], 'actividades': [], 'departamentos': []}

        except subprocess.TimeoutExpired:
            logger.error("Timeout (120s) obteniendo opciones de business")
            return {'contribuyentes': [], 'actividades': [], 'departamentos': []}
        except Exception as e:
            logger.exception("Error en get_business_form_options")
            return {'contribuyentes': [], 'actividades': [], 'departamentos': []}

    def create_business_subprocess(self, business_data: Dict, logo_temp_path: Optional[str] = None) -> Dict:
        """
        Crea un Business en PostgreSQL via subprocess.

        Args:
            business_data: Diccionario con datos del negocio
            logo_temp_path: Path temporal del logo (opcional)

        Returns:
            Dict con success y message
        """
        import json as json_module

        # Escapar datos para evitar inyección
        data_json = json_module.dumps(business_data)
        logo_path_escaped = logo_temp_path.replace('\\', '\\\\').replace('"', '\\"') if logo_temp_path else ''

        script = f'''
import os
import json
import shutil
from datetime import datetime
from pathlib import Path

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Amachine.settings')
os.environ['SETUP_RUNNING_MIGRATIONS'] = '1'

import django
django.setup()

from django.conf import settings
from Sifen.models import Business, TipoContribuyente, ActividadEconomica, Ciudades

data = json.loads("""{data_json}""")
logo_temp_path = "{logo_path_escaped}" if "{logo_path_escaped}" else None
result = {{"success": False, "message": ""}}

try:
    # Verificar si ya existe
    if Business.objects.filter(ruc=data['ruc']).exists():
        result["message"] = f"Ya existe una empresa con el RUC {{data['ruc']}}"
        print(json.dumps(result))
        exit(0)

    # Obtener objetos relacionados
    try:
        contribuyente = TipoContribuyente.objects.get(codigo=int(data['contribuyente_codigo']))
    except TipoContribuyente.DoesNotExist:
        result["message"] = "Tipo de contribuyente no válido"
        print(json.dumps(result))
        exit(0)

    try:
        actividad = ActividadEconomica.objects.get(id=int(data['actividad_id']))
    except ActividadEconomica.DoesNotExist:
        result["message"] = "Actividad económica no válida"
        print(json.dumps(result))
        exit(0)

    try:
        ciudad = Ciudades.objects.get(id=int(data['ciudad_id']))
    except Ciudades.DoesNotExist:
        result["message"] = "Ciudad no válida"
        print(json.dumps(result))
        exit(0)

    # Crear Business
    name = data['name']
    business = Business.objects.create(
        name=name,
        abbr=data.get('abbr') or name[:10],
        ruc=data['ruc'],
        ruc_dv=data['ruc_dv'],
        contribuyenteobj=contribuyente,
        nombrefactura=data.get('nombrefactura') or name,
        nombrefantasia=data.get('nombrefantasia', ''),
        numero_casa=data.get('numero_casa', ''),
        direccion=data.get('direccion', ''),
        ciudadobj=ciudad,
        telefono=data.get('telefono', ''),
        celular=data.get('celular', ''),
        correo=data.get('correo', ''),
        web=data.get('web', ''),
        denominacion=data.get('denominacion', ''),
        actividadecoobj=actividad,
        cargado_fecha=datetime.now(),
        cargado_usuario='SETUP',
        actualizado_fecha=datetime.now(),
        actualizado_usuario='SETUP',
    )

    # Procesar logo si existe
    if logo_temp_path and Path(logo_temp_path).exists():
        try:
            # Crear directorio de destino
            media_root = Path(settings.MEDIA_ROOT)
            business_dir = media_root / 'business'
            business_dir.mkdir(parents=True, exist_ok=True)

            # Generar nombre de archivo final
            ext = Path(logo_temp_path).suffix
            final_filename = f"logo_{{business.ruc}}{{ext}}"
            final_path = business_dir / final_filename

            # Mover archivo
            shutil.move(logo_temp_path, final_path)

            # Actualizar Business con el path relativo
            business.logo = f"business/{{final_filename}}"
            business.save(update_fields=['logo'])
        except Exception as logo_error:
            # No fallar todo el proceso por el logo
            result["logo_warning"] = f"Logo no procesado: {{str(logo_error)}}"

    result["success"] = True
    result["message"] = f'Empresa "{{name}}" creada exitosamente'
    result["business_id"] = business.id

except Exception as e:
    result["message"] = f"Error: {{str(e)}}"

print(json.dumps(result))
'''
        try:
            result = subprocess.run(
                [sys.executable, '-c', script],
                cwd=str(self.base_dir),
                capture_output=True,
                text=True,
                timeout=60
            )

            if result.returncode == 0:
                return json_module.loads(result.stdout.strip())
            else:
                return {
                    'success': False,
                    'message': f'Error en subprocess: {result.stderr}'
                }

        except subprocess.TimeoutExpired:
            return {'success': False, 'message': 'Timeout al crear empresa'}
        except Exception as e:
            logger.exception("Error en create_business_subprocess")
            return {'success': False, 'message': str(e)}

