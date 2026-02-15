"""
Plugin Shopify para Amachine ERP

Este plugin proporciona:
- Integración con Shopify
- Sincronización de clientes, productos y órdenes
- Conversión de pagos a facturas SIFEN
"""

from typing import List, Dict, Tuple

from OptsIO.plugin_manager import BasePlugin


class Plugin(BasePlugin):
    """Plugin de Integración Shopify."""

    name = "shopify"
    display_name = "Shopify - Integración E-commerce"
    description = "Sincronización con tiendas Shopify: clientes, productos, órdenes y pagos"
    version = "1.0.0"
    author = "Alta Machines"
    is_core = False  # Plugin opcional
    dependencies = ['sifen']  # Depende del plugin SIFEN para facturación
    icon = "mdi mdi-shopping"
    category = "integraciones"

    def get_menus(self) -> List[Dict]:
        """Retorna los menús del módulo Shopify."""
        return [
            {
                'menu': 'Shopify',
                'menu_icon': 'mdi mdi-shopping',
                'prioridad': 50,
                'items': [
                    {
                        'app_name': 'shopify_orders',
                        'friendly_name': 'Órdenes',
                        'icon': 'mdi mdi-cart',
                        'url': '/dtmpl/?template=am_shopify/ShopifyOrderHomeUi.html',
                        'prioridad': 1,
                    },
                    {
                        'app_name': 'shopify_payments',
                        'friendly_name': 'Pagos',
                        'icon': 'mdi mdi-cash',
                        'url': '/dtmpl/?template=am_shopify/ShopifyPaymentHomeUi.html',
                        'prioridad': 2,
                    },
                    {
                        'app_name': 'shopify_customers',
                        'friendly_name': 'Clientes',
                        'icon': 'mdi mdi-account-group',
                        'url': '/dtmpl/?template=am_shopify/ShopifyCustomerHomeUi.html',
                        'prioridad': 3,
                    },
                    {
                        'app_name': 'shopify_products',
                        'friendly_name': 'Productos',
                        'icon': 'mdi mdi-package-variant',
                        'url': '/dtmpl/?template=am_shopify/ShopifyProductHomeUi.html',
                        'prioridad': 4,
                    },
                    {
                        'app_name': 'shopify_sync',
                        'friendly_name': 'Sincronización',
                        'icon': 'mdi mdi-sync',
                        'url': '/dtmpl/?template=am_shopify/ShopifySyncUi.html',
                        'prioridad': 5,
                    },
                ]
            }
        ]

    def get_reference_data(self) -> List[Dict]:
        """Shopify no carga datos de referencia."""
        return []

    def get_celery_tasks(self) -> List[str]:
        """Tareas Celery del plugin Shopify."""
        return [
            'am_shopify.tasks.sync_customers',
            'am_shopify.tasks.sync_products',
            'am_shopify.tasks.sync_orders',
            'am_shopify.tasks.sync_payments',
            'am_shopify.tasks.convert_payments_to_invoices',
        ]

    def get_setup_steps(self) -> List[Dict]:
        """Pasos de setup de Shopify."""
        return [
            {
                'name': 'configure_shopify',
                'display_name': 'Configurar Shopify',
                'description': 'Configurar credenciales de API de Shopify',
                'order': 200,
                'handler': 'setup_configure_shopify',
                'required': False,  # No requerido, es opcional
            },
        ]

    def on_business_enable(self, business) -> bool:
        """
        Llamado cuando el plugin se activa para un negocio.
        Puede crear configuración inicial de Shopify.
        """
        # Aquí se podría crear la configuración de Shopify para el negocio
        return True

    def load_reference_data(self, data_name: str, progress_callback=None) -> Tuple[bool, str, Dict]:
        """Shopify no tiene datos de referencia para cargar."""
        return False, f"Shopify no tiene datos de referencia: {data_name}", {}
