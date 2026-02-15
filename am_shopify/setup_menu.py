"""
Script para crear entradas de menú de Shopify en OptsIO.Apps

Ejecutar con:
    python manage.py shell < am_shopify/setup_menu.py
"""
from OptsIO.models import Apps

entries = [
    {
        'prioridad': 100,
        'menu': 'Shopify',
        'app_name': 'ShopifyCustomer',
        'friendly_name': 'Clientes',
        'icon': 'mdi mdi-account-group',
        'url': 'am_shopify/ShopifyCustomerUi.html',
        'version': 1,
        'background': '#FFFFFF',
        'active': True,
    },
    {
        'prioridad': 100,
        'menu': 'Shopify',
        'app_name': 'ShopifyProduct',
        'friendly_name': 'Productos',
        'icon': 'mdi mdi-package-variant',
        'url': 'am_shopify/ShopifyProductUi.html',
        'version': 1,
        'background': '#FFFFFF',
        'active': True,
    },
    {
        'prioridad': 100,
        'menu': 'Shopify',
        'app_name': 'ShopifyOrder',
        'friendly_name': 'Órdenes',
        'icon': 'mdi mdi-cart',
        'url': 'am_shopify/ShopifyOrderUi.html',
        'version': 1,
        'background': '#FFFFFF',
        'active': True,
    },
    {
        'prioridad': 100,
        'menu': 'Shopify',
        'app_name': 'ShopifyPayment',
        'friendly_name': 'Pagos',
        'icon': 'mdi mdi-cash-register',
        'url': 'am_shopify/ShopifyPaymentUi.html',
        'version': 1,
        'background': '#FFFFFF',
        'active': True,
    },
]

print("Creando entradas de menú de Shopify...")

for entry in entries:
    # Verificar si ya existe
    existing = Apps.objects.filter(app_name=entry['app_name']).first()
    if existing:
        print(f"⊘ Ya existe: {entry['friendly_name']} (ID: {existing.id})")
    else:
        app = Apps.objects.create(**entry)
        print(f"✓ Creado: {entry['friendly_name']} (ID: {app.id})")

print("\n✓ Proceso completado!")
print("\nPara ver el menú, recarga la página o ejecuta:")
print("    python manage.py setup_sifen_menu")
