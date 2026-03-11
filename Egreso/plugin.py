"""
Plugin de Egresos para Amachine ERP

Este plugin proporciona:
- Gestión de Órdenes de Compra a proveedores
- Registro y seguimiento de pagos a proveedores
- Soporte para condición contado y crédito con cuotas
- Generación de PDFs de Órdenes de Compra
- Control de saldos pendientes a proveedores
"""

from typing import List, Dict, Tuple

from OptsIO.plugin_manager import BasePlugin


class Plugin(BasePlugin):
    """Plugin de Gestión de Egresos."""

    name = "egreso"
    display_name = "Gestión de Egresos"
    description = "Módulo de egresos: órdenes de compra, pagos a proveedores y seguimiento de cuentas por pagar"
    version = "1.0.0"
    author = "Alta Machines"
    is_core = False
    dependencies = ['sifen']
    icon = "mdi mdi-cart-arrow-up"
    category = "compras"

    def get_menus(self) -> List[Dict]:
        """Retorna los menús del módulo de Egresos."""
        return [
            {
                'menu': 'Egreso',
                'menu_icon': 'mdi mdi-cart-arrow-up',
                'prioridad': 20,
                'items': [
                    {
                        'app_name': 'egreso_ordenes_compra',
                        'friendly_name': 'Órdenes de Compra',
                        'icon': 'mdi mdi-file-document-outline',
                        'url': 'Egreso/OrdenCompraUi.html',
                        'prioridad': 1,
                        'background': '#D97706',
                    },
                    {
                        'app_name': 'egreso_gestion_pagos',
                        'friendly_name': 'Gestión de Pagos',
                        'icon': 'mdi mdi-cash-multiple',
                        'url': 'Egreso/OrdenCompraPagoGestionUi.html',
                        'prioridad': 2,
                        'background': '#B45309',
                    },
                ]
            }
        ]

    def get_reference_data(self) -> List[Dict]:
        """Egresos no carga datos de referencia propios."""
        return []

    def get_celery_tasks(self) -> List[str]:
        """Tareas Celery del plugin."""
        return []

    def get_setup_steps(self) -> List[Dict]:
        """Pasos de setup de Egresos."""
        return []

    def on_business_enable(self, business) -> bool:
        """Llamado cuando el plugin se activa para un negocio."""
        return True

    def load_reference_data(self, data_name: str, progress_callback=None) -> Tuple[bool, str, Dict]:
        """Egresos no tiene datos de referencia para cargar."""
        return False, f"Egresos no tiene datos de referencia: {data_name}", {}
