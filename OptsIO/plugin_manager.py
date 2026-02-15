"""
Plugin Manager para Amachine ERP

Este módulo gestiona el sistema de plugins, permitiendo:
- Autodescubrimiento de plugins
- Activación/desactivación por negocio
- Gestión de dependencias
- Carga de datos de referencia
"""

import importlib
import hashlib
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Type
from dataclasses import dataclass, field
from datetime import datetime

from django.conf import settings
from django.apps import apps

logger = logging.getLogger(__name__)


@dataclass
class PluginInfo:
    """Información de un plugin descubierto."""
    name: str
    display_name: str
    description: str = ""
    version: str = "1.0.0"
    author: str = ""
    app_name: str = ""
    module_path: str = ""
    is_core: bool = False
    dependencies: List[str] = field(default_factory=list)
    icon: str = "mdi mdi-puzzle"
    category: str = "general"

    # Funcionalidades que el plugin puede registrar
    menus: List[Dict] = field(default_factory=list)
    reference_data: List[Dict] = field(default_factory=list)
    celery_tasks: List[str] = field(default_factory=list)
    setup_steps: List[Dict] = field(default_factory=list)


class BasePlugin:
    """
    Clase base para todos los plugins de Amachine.

    Los plugins deben heredar de esta clase e implementar los métodos necesarios.
    """

    # Información del plugin (sobreescribir en subclases)
    name: str = ""
    display_name: str = ""
    description: str = ""
    version: str = "1.0.0"
    author: str = ""
    is_core: bool = False
    dependencies: List[str] = []
    icon: str = "mdi mdi-puzzle"
    category: str = "general"

    def __init__(self):
        self._initialized = False

    def get_info(self) -> PluginInfo:
        """Retorna información del plugin."""
        return PluginInfo(
            name=self.name,
            display_name=self.display_name,
            description=self.description,
            version=self.version,
            author=self.author,
            app_name=self._get_app_name(),
            module_path=self.__module__,
            is_core=self.is_core,
            dependencies=self.dependencies,
            icon=self.icon,
            category=self.category,
            menus=self.get_menus(),
            reference_data=self.get_reference_data(),
            celery_tasks=self.get_celery_tasks(),
            setup_steps=self.get_setup_steps(),
        )

    def _get_app_name(self) -> str:
        """Obtiene el nombre de la app Django asociada."""
        module_parts = self.__module__.split('.')
        return module_parts[0] if module_parts else ""

    def initialize(self) -> bool:
        """
        Inicializa el plugin.
        Llamado cuando el plugin se activa.
        """
        self._initialized = True
        return True

    def shutdown(self) -> bool:
        """
        Apaga el plugin.
        Llamado cuando el plugin se desactiva.
        """
        self._initialized = False
        return True

    def get_menus(self) -> List[Dict]:
        """
        Retorna los menús que el plugin registra.

        Ejemplo:
        return [
            {
                'menu': 'Facturación',
                'menu_icon': 'mdi mdi-file-document',
                'items': [
                    {
                        'app_name': 'factura_crear',
                        'friendly_name': 'Nueva Factura',
                        'icon': 'mdi mdi-plus',
                        'url': '/sifen/factura/create/',
                    }
                ]
            }
        ]
        """
        return []

    def get_reference_data(self) -> List[Dict]:
        """
        Retorna la definición de datos de referencia a cargar.

        Ejemplo:
        return [
            {
                'name': 'geografias',
                'display_name': 'Geografías',
                'loader': 'load_geografias',
                'source_file': 'Sifen/rf/CODIGO DE REFERENCIA GEOGRAFICA.xlsx',
                'required': True,
            }
        ]
        """
        return []

    def get_celery_tasks(self) -> List[str]:
        """
        Retorna lista de tareas Celery que el plugin registra.

        Ejemplo:
        return [
            'Sifen.tasks.send_document',
            'Sifen.tasks.track_lotes',
        ]
        """
        return []

    def get_setup_steps(self) -> List[Dict]:
        """
        Retorna pasos de setup específicos del plugin.

        Ejemplo:
        return [
            {
                'name': 'configure_sifen',
                'display_name': 'Configurar SIFEN',
                'order': 100,
                'handler': 'configure_sifen_step',
                'required': True,
            }
        ]
        """
        return []

    def on_business_enable(self, business) -> bool:
        """
        Llamado cuando el plugin se activa para un negocio.
        Puede usarse para crear datos específicos del negocio.
        """
        return True

    def on_business_disable(self, business) -> bool:
        """
        Llamado cuando el plugin se desactiva para un negocio.
        """
        return True

    def load_reference_data(self, data_name: str, progress_callback=None) -> Tuple[bool, str, Dict]:
        """
        Carga datos de referencia específicos.

        Args:
            data_name: Nombre del conjunto de datos a cargar
            progress_callback: Función opcional para reportar progreso

        Returns:
            Tuple de (success, message, stats)
        """
        return False, f"Loader no implementado para {data_name}", {}


class PluginManager:
    """
    Gestor central de plugins para Amachine ERP.

    Responsabilidades:
    - Autodescubrir plugins en las apps Django
    - Registrar plugins en la base de datos
    - Gestionar activación/desactivación por negocio
    - Cargar datos de referencia
    """

    _instance = None
    _plugins: Dict[str, BasePlugin] = {}
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self._plugins = {}
            PluginManager._initialized = True

    def discover_plugins(self) -> List[PluginInfo]:
        """
        Descubre plugins en todas las apps Django.

        Busca archivos `plugin.py` en cada app y carga la clase Plugin.
        """
        discovered = []

        for app_config in apps.get_app_configs():
            try:
                # Intentar importar el módulo plugin de la app
                module_path = f"{app_config.name}.plugin"
                plugin_module = importlib.import_module(module_path)

                # Buscar la clase Plugin
                if hasattr(plugin_module, 'Plugin'):
                    plugin_class = getattr(plugin_module, 'Plugin')
                    if issubclass(plugin_class, BasePlugin):
                        plugin_instance = plugin_class()
                        plugin_info = plugin_instance.get_info()

                        # Registrar el plugin
                        self._plugins[plugin_info.name] = plugin_instance
                        discovered.append(plugin_info)

                        logger.info(f"Plugin descubierto: {plugin_info.display_name} v{plugin_info.version}")

            except ImportError:
                # La app no tiene módulo plugin, es normal
                pass
            except Exception as e:
                logger.error(f"Error al cargar plugin de {app_config.name}: {e}")

        return discovered

    def register_plugins(self) -> Tuple[int, int]:
        """
        Registra los plugins descubiertos en la base de datos.

        Returns:
            Tuple de (plugins_creados, plugins_actualizados)
        """
        from OptsIO.models import Plugin as PluginModel

        created = 0
        updated = 0

        for name, plugin_instance in self._plugins.items():
            info = plugin_instance.get_info()

            plugin_obj, was_created = PluginModel.objects.update_or_create(
                name=info.name,
                defaults={
                    'display_name': info.display_name,
                    'description': info.description,
                    'version': info.version,
                    'author': info.author,
                    'app_name': info.app_name,
                    'module_path': info.module_path,
                    'is_core': info.is_core,
                    'dependencies': info.dependencies,
                    'icon': info.icon,
                    'category': info.category,
                }
            )

            if was_created:
                created += 1
                # Activar plugins core por defecto
                if info.is_core:
                    plugin_obj.status = 'active'
                    plugin_obj.save()
            else:
                updated += 1

        return created, updated

    def get_plugin(self, name: str) -> Optional[BasePlugin]:
        """Obtiene una instancia de plugin por nombre."""
        return self._plugins.get(name)

    def get_all_plugins(self) -> Dict[str, BasePlugin]:
        """Retorna todos los plugins registrados."""
        return self._plugins.copy()

    def is_plugin_enabled_for_business(self, plugin_name: str, business) -> bool:
        """Verifica si un plugin está habilitado para un negocio."""
        from OptsIO.models import BusinessPlugin, Plugin as PluginModel

        try:
            plugin = PluginModel.objects.get(name=plugin_name)
            bp = BusinessPlugin.objects.filter(business=business, plugin=plugin).first()
            return bp.enabled if bp else plugin.is_core
        except PluginModel.DoesNotExist:
            return False

    def enable_plugin_for_business(self, plugin_name: str, business, enabled_by: str = "") -> Tuple[bool, str]:
        """
        Habilita un plugin para un negocio.
        """
        from OptsIO.models import BusinessPlugin, Plugin as PluginModel

        try:
            plugin_model = PluginModel.objects.get(name=plugin_name)
            plugin_instance = self._plugins.get(plugin_name)

            if not plugin_instance:
                return False, f"Plugin {plugin_name} no está cargado"

            # Verificar dependencias
            for dep_name in plugin_model.dependencies:
                if not self.is_plugin_enabled_for_business(dep_name, business):
                    return False, f"Dependencia {dep_name} no está habilitada"

            # Crear o actualizar relación
            bp, created = BusinessPlugin.objects.update_or_create(
                business=business,
                plugin=plugin_model,
                defaults={
                    'enabled': True,
                    'enabled_by': enabled_by,
                }
            )

            # Ejecutar hook del plugin
            plugin_instance.on_business_enable(business)

            return True, f"Plugin {plugin_name} habilitado para {business.name}"

        except PluginModel.DoesNotExist:
            return False, f"Plugin {plugin_name} no existe"
        except Exception as e:
            return False, str(e)

    def disable_plugin_for_business(self, plugin_name: str, business) -> Tuple[bool, str]:
        """
        Deshabilita un plugin para un negocio.
        """
        from OptsIO.models import BusinessPlugin, Plugin as PluginModel

        try:
            plugin_model = PluginModel.objects.get(name=plugin_name)

            if plugin_model.is_core:
                return False, f"Plugin {plugin_name} es core y no puede deshabilitarse"

            plugin_instance = self._plugins.get(plugin_name)

            bp = BusinessPlugin.objects.filter(business=business, plugin=plugin_model).first()
            if bp:
                bp.enabled = False
                bp.save()

                if plugin_instance:
                    plugin_instance.on_business_disable(business)

            return True, f"Plugin {plugin_name} deshabilitado para {business.name}"

        except PluginModel.DoesNotExist:
            return False, f"Plugin {plugin_name} no existe"
        except Exception as e:
            return False, str(e)

    def get_all_menus(self, business=None) -> List[Dict]:
        """
        Obtiene todos los menús de todos los plugins activos.

        Si se proporciona business, solo incluye menús de plugins habilitados.
        """
        menus = []

        for name, plugin in self._plugins.items():
            if business and not self.is_plugin_enabled_for_business(name, business):
                continue

            plugin_menus = plugin.get_menus()
            menus.extend(plugin_menus)

        return menus

    def get_all_reference_data(self) -> List[Dict]:
        """
        Obtiene toda la información de datos de referencia de todos los plugins.
        """
        all_data = []

        for name, plugin in self._plugins.items():
            ref_data = plugin.get_reference_data()
            for data in ref_data:
                data['plugin'] = name
            all_data.extend(ref_data)

        return all_data

    def load_reference_data(self, data_type: str, progress_callback=None) -> Tuple[bool, str, Dict]:
        """
        Carga datos de referencia de un tipo específico.
        """
        from OptsIO.models import ReferenceDataLoad

        # Buscar qué plugin proporciona estos datos
        for name, plugin in self._plugins.items():
            ref_data_list = plugin.get_reference_data()
            for ref_data in ref_data_list:
                if ref_data.get('name') == data_type:
                    # Cargar los datos
                    success, message, stats = plugin.load_reference_data(data_type, progress_callback)

                    if success:
                        # Registrar la carga
                        ReferenceDataLoad.objects.create(
                            data_type=data_type,
                            source_file=ref_data.get('source_file', ''),
                            records_loaded=stats.get('loaded', 0),
                            records_updated=stats.get('updated', 0),
                            records_skipped=stats.get('skipped', 0),
                            loaded_by='system',
                            notes=message,
                        )

                    return success, message, stats

        return False, f"No se encontró loader para {data_type}", {}

    def is_reference_data_loaded(self, data_type: str) -> bool:
        """Verifica si un tipo de datos de referencia ya fue cargado."""
        from OptsIO.models import ReferenceDataLoad
        return ReferenceDataLoad.objects.filter(data_type=data_type).exists()

    def get_file_hash(self, file_path: str) -> str:
        """Calcula el hash SHA256 de un archivo."""
        full_path = Path(settings.BASE_DIR) / file_path
        if not full_path.exists():
            return ""

        sha256_hash = hashlib.sha256()
        with open(full_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()


# Instancia global del Plugin Manager
plugin_manager = PluginManager()
