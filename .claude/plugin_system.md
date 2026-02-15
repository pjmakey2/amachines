# Sistema de Plugins - Amachine ERP

## Descripción General

El sistema de plugins permite extender la funcionalidad de Amachine ERP de forma modular. Los plugins pueden:

- Registrar menús y aplicaciones
- Cargar datos de referencia
- Registrar tareas Celery
- Definir pasos de setup específicos
- Configurarse por Business (multi-tenant)

## Arquitectura

### Componentes Principales

```
OptsIO/
├── plugin_manager.py    # Plugin Manager central
├── plugin.py            # Plugin core del sistema
├── models.py            # Modelos: Plugin, BusinessPlugin, ReferenceDataLoad, SetupStep
└── setup_manager.py     # Integración con setup

Sifen/
└── plugin.py            # Plugin de Facturación SIFEN

am_shopify/
└── plugin.py            # Plugin de integración Shopify
```

### Modelos

#### Plugin

Registro de plugins disponibles:

```python
class Plugin(models.Model):
    name            # Nombre único del plugin
    display_name    # Nombre para mostrar
    description     # Descripción
    version         # Versión (ej: "1.0.0")
    author          # Autor
    app_name        # App Django asociada
    module_path     # Path al módulo
    status          # active, inactive, error
    is_core         # Si es core (no desactivable)
    dependencies    # Lista de plugins requeridos
    icon            # Icono MDI
    category        # Categoría
```

#### BusinessPlugin

Relación Plugin-Business para multi-tenancy:

```python
class BusinessPlugin(models.Model):
    business        # FK a Business
    plugin          # FK a Plugin
    enabled         # Si está activo para este negocio
    config          # Configuración específica (JSON)
```

#### ReferenceDataLoad

Registro de datos de referencia cargados:

```python
class ReferenceDataLoad(models.Model):
    data_type       # Tipo de dato (geografias, actividades, etc.)
    source_file     # Archivo fuente
    source_hash     # Hash del archivo
    records_loaded  # Registros cargados
    records_updated # Registros actualizados
    records_skipped # Registros omitidos
    loaded_at       # Fecha de carga
```

## Crear un Nuevo Plugin

### 1. Crear archivo plugin.py en la app

```python
# mi_app/plugin.py

from typing import List, Dict, Tuple
from OptsIO.plugin_manager import BasePlugin

class Plugin(BasePlugin):
    """Plugin de Mi App."""

    name = "mi_app"
    display_name = "Mi App - Descripción Corta"
    description = "Descripción completa del plugin"
    version = "1.0.0"
    author = "Tu Nombre"
    is_core = False  # True si no puede desactivarse
    dependencies = []  # Lista de plugins requeridos
    icon = "mdi mdi-puzzle"
    category = "general"

    def get_menus(self) -> List[Dict]:
        """Retorna los menús a registrar."""
        return [
            {
                'menu': 'Mi Menú',
                'menu_icon': 'mdi mdi-folder',
                'prioridad': 50,
                'items': [
                    {
                        'app_name': 'mi_app_home',
                        'friendly_name': 'Inicio',
                        'icon': 'mdi mdi-home',
                        'url': '/dtmpl/?template=mi_app/HomeUi.html',
                        'prioridad': 1,
                    },
                ]
            }
        ]

    def get_reference_data(self) -> List[Dict]:
        """Define datos de referencia a cargar."""
        return [
            {
                'name': 'mis_datos',
                'display_name': 'Mis Datos',
                'description': 'Datos de referencia personalizados',
                'loader': 'load_mis_datos',
                'source_file': 'mi_app/data/datos.csv',
                'required': False,
                'order': 100,
            }
        ]

    def get_celery_tasks(self) -> List[str]:
        """Tareas Celery del plugin."""
        return [
            'mi_app.tasks.mi_tarea',
        ]

    def load_reference_data(self, data_name: str, progress_callback=None) -> Tuple[bool, str, Dict]:
        """Carga datos de referencia."""
        if data_name == 'mis_datos':
            return self._load_mis_datos(progress_callback)
        return False, f"No hay loader para {data_name}", {}

    def _load_mis_datos(self, progress_callback=None) -> Tuple[bool, str, Dict]:
        """Implementación del loader."""
        from mi_app.models import MiModelo

        stats = {'loaded': 0, 'updated': 0, 'skipped': 0}

        if progress_callback:
            progress_callback(10, "Cargando datos...")

        # ... lógica de carga ...

        if progress_callback:
            progress_callback(100, "Datos cargados")

        return True, f"Datos cargados ({stats['loaded']} nuevos)", stats
```

### 2. Autodescubrimiento

Los plugins se descubren automáticamente al iniciar Django. El Plugin Manager busca un archivo `plugin.py` en cada app y carga la clase `Plugin`.

### 3. Registro en BD

Durante el setup o al ejecutar:

```python
from OptsIO.plugin_manager import plugin_manager

# Descubrir plugins
discovered = plugin_manager.discover_plugins()

# Registrar en BD
created, updated = plugin_manager.register_plugins()
```

## Plugin Manager

### Uso Básico

```python
from OptsIO.plugin_manager import plugin_manager

# Obtener un plugin
plugin = plugin_manager.get_plugin('sifen')

# Obtener todos los plugins
all_plugins = plugin_manager.get_all_plugins()

# Verificar si está habilitado para un negocio
is_enabled = plugin_manager.is_plugin_enabled_for_business('sifen', business)

# Habilitar/deshabilitar
success, msg = plugin_manager.enable_plugin_for_business('shopify', business, 'admin')
success, msg = plugin_manager.disable_plugin_for_business('shopify', business)

# Obtener menús filtrados por negocio
menus = plugin_manager.get_all_menus(business)

# Cargar datos de referencia
success, msg, stats = plugin_manager.load_reference_data('geografias')
```

## Plugins Incluidos

### OptsIO (Core)

- **Categoría**: sistema
- **Core**: Sí
- **Dependencias**: Ninguna
- **Funcionalidades**:
  - Gestión de usuarios y perfiles
  - Sistema de permisos
  - Administración de plugins

### Sifen (Facturación)

- **Categoría**: facturacion
- **Core**: Sí
- **Dependencias**: Ninguna
- **Funcionalidades**:
  - Facturación electrónica SIFEN
  - Documentos: facturas, notas de crédito, etc.
  - Gestión de clientes, productos, timbrados
- **Datos de Referencia**:
  - Tipos de Contribuyente
  - Geografías (Departamentos, Ciudades, Barrios)
  - Actividades Económicas
  - Unidades de Medida
  - Porcentajes IVA
  - Métodos de Pago

### Shopify (Integración)

- **Categoría**: integraciones
- **Core**: No
- **Dependencias**: sifen
- **Funcionalidades**:
  - Sincronización con Shopify
  - Clientes, productos, órdenes
  - Conversión de pagos a facturas

## Flujo de Setup con Plugins

1. **Configuración BD** (`/setup/`)
   - Formulario de conexión PostgreSQL
   - Crear archivo .env

2. **Reinicio del servidor**
   - Django carga nuevas variables de entorno

3. **Finalización** (`/setup/finalize/`)
   - Ejecutar migraciones
   - Descubrir y registrar plugins
   - Cargar datos de referencia (de todos los plugins)
   - Crear usuario admin
   - Configurar menús

4. **Configurar Empresa** (`/setup/business/`)
   - Formulario de datos de la empresa
   - Crear primer Business
   - Habilitar plugins core
   - Marcar setup como completado

## Extensibilidad

### Hooks de Negocio

Los plugins pueden implementar hooks que se ejecutan cuando se activan/desactivan para un negocio:

```python
def on_business_enable(self, business) -> bool:
    """Llamado al activar el plugin para un negocio."""
    # Crear configuración inicial
    # Crear datos por defecto
    return True

def on_business_disable(self, business) -> bool:
    """Llamado al desactivar el plugin para un negocio."""
    # Limpiar datos si es necesario
    return True
```

### Configuración por Negocio

Cada BusinessPlugin puede tener configuración específica en JSON:

```python
bp = BusinessPlugin.objects.get(business=business, plugin__name='shopify')
bp.config = {
    'store_url': 'mi-tienda.myshopify.com',
    'api_key': '...',
    'sync_interval': 300,
}
bp.save()
```

---

**Última actualización**: 2026-01-04
**Mantenido por**: Equipo de Desarrollo Amachine
