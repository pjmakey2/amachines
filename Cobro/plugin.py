"""
Plugin de Cobros para Amachine ERP

Este plugin proporciona:
- Gestión de cobros y pagos de facturas a crédito
- Registro de pagos parciales
- Seguimiento de saldos pendientes
- Reportes de cuentas por cobrar
"""

from typing import List, Dict, Tuple

from OptsIO.plugin_manager import BasePlugin


class Plugin(BasePlugin):
    """Plugin de Gestión de Cobros."""

    name = "cobro"
    display_name = "Gestión de Cobros"
    description = "Sistema de gestión de cobros y pagos de facturas a crédito"
    version = "1.0.0"
    author = "Alta Machines"
    is_core = False  # Plugin opcional
    dependencies = ['sifen']  # Depende del plugin SIFEN para acceso a facturas
    icon = "mdi mdi-cash-multiple"
    category = "facturacion"

    def get_menus(self) -> List[Dict]:
        """Retorna los menús del módulo de Cobros."""
        return [
            {
                'menu': 'COBROS',
                'menu_icon': 'mdi mdi-cash-register',
                'prioridad': 40,
                'items': [
                    {
                        'app_name': 'cobro_gestion',
                        'friendly_name': 'Gestión de Cobros',
                        'icon': 'mdi mdi-cash-multiple',
                        'url': 'Cobro/GestionUi.html',
                        'prioridad': 1,
                        'background': '#10B981',
                    },
                ]
            }
        ]

    def get_reference_data(self) -> List[Dict]:
        """Cobros no carga datos de referencia propios."""
        return []

    def get_celery_tasks(self) -> List[str]:
        """Tareas Celery del plugin (si las hubiera)."""
        return []

    def get_setup_steps(self) -> List[Dict]:
        """Pasos de setup de Cobros."""
        return []

    def on_business_enable(self, business) -> bool:
        """
        Llamado cuando el plugin se activa para un negocio.
        """
        # No requiere configuración especial
        return True

    def load_reference_data(self, data_name: str, progress_callback=None) -> Tuple[bool, str, Dict]:
        """Cobros no tiene datos de referencia para cargar."""
        return False, f"Cobros no tiene datos de referencia: {data_name}", {}
