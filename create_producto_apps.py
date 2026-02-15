"""
Script para crear registros en el modelo Apps para las interfaces de Producto
Ejecutar con: python manage.py shell < create_producto_apps.py
"""
from OptsIO.models import Apps

# Lista de interfaces a crear
interfaces = [
    {
        'prioridad': 100,
        'menu': '',
        'app_name': 'Categoria',
        'friendly_name': 'Categorías',
        'icon': 'mdi mdi-shape',
        'url': 'Sifen/CategoriaUi.html',
        'version': 1,
        'background': '#FFFFFF',
        'active': True,
    },
    {
        'prioridad': 100,
        'menu': '',
        'app_name': 'Marca',
        'friendly_name': 'Marcas',
        'icon': 'mdi mdi-tag',
        'url': 'Sifen/MarcaUi.html',
        'version': 1,
        'background': '#FFFFFF',
        'active': True,
    },
    {
        'prioridad': 100,
        'menu': '',
        'app_name': 'PorcentajeIva',
        'friendly_name': 'Porcentajes IVA',
        'icon': 'mdi mdi-percent',
        'url': 'Sifen/PorcentajeIvaUi.html',
        'version': 1,
        'background': '#FFFFFF',
        'active': True,
    },
    {
        'prioridad': 100,
        'menu': '',
        'app_name': 'Producto',
        'friendly_name': 'Productos',
        'icon': 'mdi mdi-package-variant',
        'url': 'Sifen/ProductoUi.html',
        'version': 1,
        'background': '#FFFFFF',
        'active': True,
    },
]

print("=" * 60)
print("CREANDO REGISTROS EN APPS")
print("=" * 60)

created_count = 0
updated_count = 0
error_count = 0

for interface in interfaces:
    try:
        # Verificar si ya existe por app_name
        existing = Apps.objects.filter(app_name=interface['app_name']).first()

        if existing:
            # Actualizar registro existente
            for key, value in interface.items():
                setattr(existing, key, value)
            existing.save()
            print(f"✓ ACTUALIZADO: {interface['friendly_name']} ({interface['app_name']})")
            updated_count += 1
        else:
            # Crear nuevo registro
            Apps.objects.create(**interface)
            print(f"✓ CREADO: {interface['friendly_name']} ({interface['app_name']})")
            created_count += 1

    except Exception as e:
        print(f"✗ ERROR en {interface['app_name']}: {str(e)}")
        error_count += 1

print("=" * 60)
print(f"RESUMEN:")
print(f"  - Creados: {created_count}")
print(f"  - Actualizados: {updated_count}")
print(f"  - Errores: {error_count}")
print("=" * 60)

if error_count == 0:
    print("\n✓ Todos los registros se procesaron correctamente")
    print("\nLas nuevas interfaces ya están disponibles en el menú Sifen")
else:
    print(f"\n⚠ Se encontraron {error_count} error(es)")
