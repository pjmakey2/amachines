"""
Plugin Core OptsIO para Amachine ERP

Este plugin proporciona:
- Funcionalidades core del sistema
- Gestión de usuarios y perfiles
- Menús de administración
- Sistema de permisos
"""

from typing import List, Dict, Tuple

from OptsIO.plugin_manager import BasePlugin


class Plugin(BasePlugin):
    """Plugin Core del Sistema."""

    name = "optsio"
    display_name = "OptsIO - Core del Sistema"
    description = "Funcionalidades core: usuarios, perfiles, menús, permisos"
    version = "1.0.0"
    author = "Alta Machines"
    is_core = True  # Plugin core, siempre activo
    dependencies = []
    icon = "mdi mdi-cogs"
    category = "sistema"

    def get_menus(self) -> List[Dict]:
        """Retorna los menús del módulo core."""
        return [
            {
                'menu': 'Administración',
                'menu_icon': 'mdi mdi-shield-account',
                'prioridad': 99,
                'items': [
                    {
                        'app_name': 'admin_users',
                        'friendly_name': 'Usuarios',
                        'icon': 'mdi mdi-account-multiple',
                        'url': '/dtmpl/?template=OptsIO/UserHomeUi.html',
                        'prioridad': 1,
                    },
                    {
                        'app_name': 'admin_groups',
                        'friendly_name': 'Grupos de Permisos',
                        'icon': 'mdi mdi-account-group',
                        'url': '/dtmpl/?template=OptsIO/PermissionGroupHomeUi.html',
                        'prioridad': 2,
                    },
                    {
                        'app_name': 'admin_plugins',
                        'friendly_name': 'Plugins',
                        'icon': 'mdi mdi-puzzle',
                        'url': '/dtmpl/?template=OptsIO/PluginHomeUi.html',
                        'prioridad': 3,
                    },
                ]
            }
        ]

    def get_reference_data(self) -> List[Dict]:
        """OptsIO no carga datos de referencia."""
        return []

    def get_celery_tasks(self) -> List[str]:
        """Tareas Celery del plugin core."""
        return [
            'OptsIO.tasks.cleanup_old_tasks',
        ]

    def get_setup_steps(self) -> List[Dict]:
        """Pasos de setup del core."""
        return [
            {
                'name': 'create_admin',
                'display_name': 'Crear Usuario Admin',
                'description': 'Crear el usuario administrador inicial',
                'order': 50,
                'handler': 'setup_create_admin',
                'required': True,
            },
        ]

    def load_reference_data(self, data_name: str, progress_callback=None) -> Tuple[bool, str, Dict]:
        """OptsIO no tiene datos de referencia para cargar."""
        return False, f"OptsIO no tiene datos de referencia: {data_name}", {}
