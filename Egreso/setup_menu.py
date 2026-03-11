"""
Script para crear entradas de menú de Egresos en OptsIO.Apps

Ejecutar con:
    python manage.py shell < Egreso/setup_menu.py
"""
from OptsIO.models import Apps, Menu

# Crear menú Egreso si no existe
menu, created = Menu.objects.get_or_create(
    menu='Egreso',
    defaults={
        'prioridad': 20,
        'friendly_name': 'Gestión de Egresos',
        'icon': 'mdi mdi-cart-arrow-up',
        'url': '#',
        'background': '#D97706',
        'active': True,
    }
)
print(f"{'+ Menú creado' if created else 'O Menú ya existe'}: Egreso")

entries = [
    {
        'prioridad': 1,
        'menu': 'Egreso',
        'app_name': 'egreso_ordenes_compra',
        'friendly_name': 'Órdenes de Compra',
        'icon': 'mdi mdi-file-document-outline',
        'url': 'Egreso/OrdenCompraUi.html',
        'version': 1,
        'background': '#D97706',
        'active': True,
    },
    {
        'prioridad': 2,
        'menu': 'Egreso',
        'app_name': 'egreso_gestion_pagos',
        'friendly_name': 'Gestión de Pagos',
        'icon': 'mdi mdi-cash-multiple',
        'url': 'Egreso/OrdenCompraPagoGestionUi.html',
        'version': 1,
        'background': '#B45309',
        'active': True,
    },
]

print("\nCreando entradas de menú de Egresos...")
for entry in entries:
    existing = Apps.objects.filter(app_name=entry['app_name']).first()
    if existing:
        print(f"O Ya existe: {entry['friendly_name']} (ID: {existing.id})")
    else:
        app = Apps.objects.create(**entry)
        print(f"+ Creado: {entry['friendly_name']} (ID: {app.id})")

print("\n+ Proceso completado!")
print("Para ver el menú, recarga la página.")
