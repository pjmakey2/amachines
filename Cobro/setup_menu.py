"""
Script para crear entradas de menú de Cobros en OptsIO.Apps

Ejecutar con:
    python manage.py shell < Cobro/setup_menu.py
"""
from OptsIO.models import Apps

entries = [
    {
        'prioridad': 90,
        'menu': 'Cobros',
        'app_name': 'CobroGestion',
        'friendly_name': 'Gestión',
        'icon': 'mdi mdi-cash-multiple',
        'url': 'Cobro/GestionUi.html',
        'version': 1,
        'background': '#FFFFFF',
        'active': True,
    },
]

print("Creando entradas de menú de Cobros...")

for entry in entries:
    # Verificar si ya existe
    existing = Apps.objects.filter(app_name=entry['app_name']).first()
    if existing:
        print(f"O Ya existe: {entry['friendly_name']} (ID: {existing.id})")
    else:
        app = Apps.objects.create(**entry)
        print(f"+ Creado: {entry['friendly_name']} (ID: {app.id})")

print("\n+ Proceso completado!")
print("\nPara ver el menú, recarga la página.")
