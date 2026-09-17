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

from celery.schedules import crontab

from OptsIO.plugin_manager import BasePlugin


class Plugin(BasePlugin):
    """Plugin de Gestión de Egresos."""

    name = "egreso"
    display_name = "Gestión de Egresos"
    description = "Módulo de egresos: órdenes de compra, pagos a proveedores y seguimiento de cuentas por pagar"
    version = "1.0.0"
    author = "Alta Machines"
    is_core = False
    dependencies = ['sifen', 'tesoreria']
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
                    {'app_name': 'egreso_gastos', 'friendly_name': 'Gastos', 'icon': 'mdi mdi-receipt-text-outline',
                     'url': 'Egreso/GastoUi.html', 'prioridad': 3, 'background': '#92400E'},
                    {'app_name': 'egreso_pagos_proveedor', 'friendly_name': 'Pagos a Proveedores', 'icon': 'mdi mdi-account-cash',
                     'url': 'Egreso/PagoProveedorUi.html', 'prioridad': 4, 'background': '#92400E'},
                    {'app_name': 'egreso_transferencias', 'friendly_name': 'Transferencias Internas', 'icon': 'mdi mdi-bank-transfer',
                     'url': 'Egreso/TransferenciaInternaUi.html', 'prioridad': 5, 'background': '#92400E'},
                    {'app_name': 'egreso_proveedores', 'friendly_name': 'Proveedores', 'icon': 'mdi mdi-truck-outline',
                     'url': 'Egreso/ProveedorUi.html', 'prioridad': 6, 'background': '#78350F'},
                    {'app_name': 'egreso_recurrentes', 'friendly_name': 'Gastos Recurrentes', 'icon': 'mdi mdi-calendar-sync',
                     'url': 'Egreso/GastoRecurrenteUi.html', 'prioridad': 7, 'background': '#78350F'},
                    {'app_name': 'egreso_categorias', 'friendly_name': 'Categorías de Gasto', 'icon': 'mdi mdi-tag-multiple-outline',
                     'url': 'Egreso/CategoriaGastoUi.html', 'prioridad': 8, 'background': '#78350F'},
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

    def get_beat_schedule(self) -> Dict[str, Dict]:
        return {'egreso-gastos-recurrentes': {'task': 'Egreso.tasks.generar_gastos_recurrentes',
                                              'schedule': crontab(hour=6, minute=0)}}

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
