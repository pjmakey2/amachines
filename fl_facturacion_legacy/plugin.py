"""
Plugin FL Facturación Legacy para Amachine ERP

Este plugin proporciona:
- Integración directa con base de datos MySQL de Frontliner
- Entrega de paquetes (generación de tickets/acuses)
- Administración de facturas pendientes
- Facturación electrónica SIFEN
"""

from typing import List, Dict, Tuple

from OptsIO.plugin_manager import BasePlugin


class Plugin(BasePlugin):
    """Plugin de Facturación Legacy Frontliner."""

    name = "fl_facturacion_legacy"
    display_name = "Frontliner - Facturación Legacy"
    description = "Integración con sistema Frontliner para facturación electrónica de paquetes"
    version = "1.0.0"
    author = "Alta Machines"
    is_core = False  # Plugin opcional
    dependencies = ['sifen']  # Depende del plugin SIFEN para facturación electrónica
    icon = "mdi mdi-package-variant-closed"
    category = "integraciones"

    def get_menus(self) -> List[Dict]:
        """Retorna los menús del módulo FL Legacy."""
        return [
            {
                'menu': 'FL Legacy',
                'menu_icon': 'mdi mdi-truck-delivery',
                'prioridad': 35,
                'items': [
                    {
                        'app_name': 'fl_entregar_paquetes',
                        'friendly_name': 'Entregar Paquetes',
                        'icon': 'mdi mdi-package-variant',
                        'url': 'fl_facturacion_legacy/FLEntregarPaquetesUi.html',
                        'prioridad': 1,
                        'background': '#8B5CF6',
                    },
                    {
                        'app_name': 'fl_administrar_facturas',
                        'friendly_name': 'Administrar Facturas',
                        'icon': 'mdi mdi-file-document-multiple',
                        'url': 'fl_facturacion_legacy/FLFacturaHomeUi.html',
                        'prioridad': 2,
                        'background': '#6366F1',
                    },
                    {
                        'app_name': 'fl_facturar',
                        'friendly_name': 'Facturar',
                        'icon': 'mdi mdi-receipt',
                        'url': 'fl_facturacion_legacy/FLFacturarUi.html',
                        'prioridad': 3,
                        'background': '#4F46E5',
                    },
                ]
            }
        ]

    def get_reference_data(self) -> List[Dict]:
        """FL Facturación no carga datos de referencia propios."""
        return []

    def get_celery_tasks(self) -> List[str]:
        """Tareas Celery del plugin (si las hubiera)."""
        return []

    def get_setup_steps(self) -> List[Dict]:
        """Pasos de setup de Frontliner."""
        return [
            {
                'name': 'configure_fl_mysql',
                'display_name': 'Configurar MySQL Frontliner',
                'description': 'Configurar conexión a base de datos MySQL de Frontliner',
                'order': 250,
                'handler': 'setup_configure_mysql',
                'required': True,
            },
        ]

    def on_business_enable(self, business) -> bool:
        """
        Llamado cuando el plugin se activa para un negocio.
        """
        # Verificar conexión a MySQL
        try:
            from .fl_mysql_client import FLMySQLClient
            client = FLMySQLClient()
            # Test connection
            with client.get_connection() as conn:
                pass
            return True
        except Exception as e:
            import logging
            logging.error(f"Error activando plugin Frontliner: {e}")
            return False

    def load_reference_data(self, data_name: str, progress_callback=None) -> Tuple[bool, str, Dict]:
        """Frontliner no tiene datos de referencia para cargar."""
        return False, f"Frontliner no tiene datos de referencia: {data_name}", {}
