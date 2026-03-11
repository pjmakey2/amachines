# Guía de Desarrollo de Plugins - Amachine ERP

## ¿Qué es un Plugin?

Un plugin es una app Django que se integra al sistema de Amachine ERP registrando sus menús, datos de referencia, tareas Celery y pasos de configuración a través de un archivo `plugin.py`. El sistema descubre automáticamente todos los plugins al iniciar Django.

---

## Estructura Mínima de un Plugin

```
mi_app/
├── __init__.py
├── apps.py
├── admin.py
├── models.py
├── mng_mi_app.py       # Lógica de negocio
├── plugin.py           # ← Punto de entrada al sistema de plugins
├── setup_menu.py       # Script legacy para crear menús manualmente
└── migrations/
    └── __init__.py
```

---

## 1. Crear el archivo `plugin.py`

Este es el único archivo requerido para integrarse al sistema de plugins.

```python
# mi_app/plugin.py

from typing import List, Dict, Tuple
from OptsIO.plugin_manager import BasePlugin


class Plugin(BasePlugin):
    """Plugin de Mi App."""

    # --- Metadatos ---
    name = "mi_app"                          # Identificador único (snake_case)
    display_name = "Mi App"                  # Nombre visible en el sistema
    description = "Descripción completa"     # Descripción larga
    version = "1.0.0"                        # Versión semántica
    author = "Alta Machines"
    is_core = False                          # True = no puede desactivarse
    dependencies = ['sifen']                 # Plugins requeridos (por name)
    icon = "mdi mdi-puzzle"                  # Icono Material Design Icons
    category = "general"                     # sistema | facturacion | compras | integraciones | general

    def get_menus(self) -> List[Dict]:
        """Define los menús y sus ítems."""
        return [
            {
                'menu': 'Mi Menú',           # Nombre del menú padre
                'menu_icon': 'mdi mdi-folder',
                'prioridad': 50,             # Orden de aparición (menor = primero)
                'items': [
                    {
                        'app_name': 'mi_app_home',        # Identificador único del ítem
                        'friendly_name': 'Inicio',
                        'icon': 'mdi mdi-home',
                        'url': 'mi_app/HomeUi.html',      # Path al template
                        'prioridad': 1,
                        'background': '#10B981',          # Color de fondo (hex)
                    },
                ]
            }
        ]

    def get_reference_data(self) -> List[Dict]:
        """Define datasets de referencia que el plugin puede cargar."""
        return [
            {
                'name': 'mis_datos',
                'display_name': 'Mis Datos de Referencia',
                'description': 'Descripción del dataset',
                'loader': 'load_mis_datos',
                'source_file': 'mi_app/data/datos.csv',
                'required': False,
                'order': 100,
            }
        ]

    def get_celery_tasks(self) -> List[str]:
        """Rutas de módulo de las tareas Celery del plugin."""
        return [
            'mi_app.tasks.mi_tarea_periodica',
        ]

    def get_setup_steps(self) -> List[Dict]:
        """Pasos de configuración inicial del plugin."""
        return [
            {
                'name': 'configurar_mi_app',
                'display_name': 'Configurar Mi App',
                'description': 'Paso inicial de configuración',
                'order': 100,
            }
        ]

    def on_business_enable(self, business) -> bool:
        """Llamado al activar el plugin para un Business."""
        # Crear configuración inicial, datos por defecto, etc.
        return True

    def on_business_disable(self, business) -> bool:
        """Llamado al desactivar el plugin para un Business."""
        return True

    def load_reference_data(self, data_name: str, progress_callback=None) -> Tuple[bool, str, Dict]:
        """Ejecuta la carga de un dataset de referencia."""
        if data_name == 'mis_datos':
            return self._load_mis_datos(progress_callback)
        return False, f"No hay loader para: {data_name}", {}

    def _load_mis_datos(self, progress_callback=None) -> Tuple[bool, str, Dict]:
        from mi_app.models import MiModelo

        stats = {'loaded': 0, 'updated': 0, 'skipped': 0}

        if progress_callback:
            progress_callback(10, "Iniciando carga...")

        # ... lógica de carga ...

        if progress_callback:
            progress_callback(100, "Completado")

        return True, f"Datos cargados ({stats['loaded']} nuevos)", stats
```

---

## 2. Registrar la App en Django

Agregar la app a `INSTALLED_APPS` en `Amachine/settings.py`:

```python
INSTALLED_APPS = [
    # ... apps existentes ...
    'mi_app',  # Descripción breve
]
```

---

## 3. Crear las Migraciones

```bash
docker exec -it amachine_web python manage.py makemigrations mi_app
docker exec -it amachine_web python manage.py migrate
```

---

## 4. Registrar el Plugin en la Base de Datos

El sistema descubre plugins automáticamente al iniciar. Para forzar el registro:

```python
from OptsIO.plugin_manager import plugin_manager

# Descubrir y registrar
plugin_manager.discover_plugins()
plugin_manager.register_plugins()
```

O desde el shell de Django:

```bash
docker exec -it amachine_web python manage.py shell -c "
from OptsIO.plugin_manager import plugin_manager
plugin_manager.discover_plugins()
created, updated = plugin_manager.register_plugins()
print(f'Creados: {created}, Actualizados: {updated}')
"
```

---

## 5. Crear los Menús (setup_menu.py)

Si el plugin_manager aún no está integrado en el flujo de setup, usar el script legacy:

```bash
docker exec -it amachine_web python manage.py shell < mi_app/setup_menu.py
```

El archivo `setup_menu.py` crea entradas en `OptsIO.Apps` directamente:

```python
from OptsIO.models import Apps, Menu

Menu.objects.get_or_create(
    menu='Mi Menú',
    defaults={'prioridad': 50, 'icon': 'mdi mdi-folder', ...}
)

Apps.objects.get_or_create(
    app_name='mi_app_home',
    defaults={
        'menu': 'Mi Menú',
        'friendly_name': 'Inicio',
        'url': 'mi_app/HomeUi.html',
        'icon': 'mdi mdi-home',
        ...
    }
)
```

---

## 6. Habilitar el Plugin para un Business

```python
from OptsIO.plugin_manager import plugin_manager
from Sifen.models import Business

business = Business.objects.get(ruc='...')
success, msg = plugin_manager.enable_plugin_for_business('mi_app', business, 'admin')
```

---

## Referencia: Plugins Existentes

| Plugin | `name` | `is_core` | `dependencies` | Categoría |
|--------|--------|-----------|----------------|-----------|
| OptsIO | `optsio` | Sí | — | sistema |
| Sifen | `sifen` | Sí | — | facturacion |
| Cobro | `cobro` | No | `sifen` | facturacion |
| Egreso | `egreso` | No | `sifen` | compras |
| Shopify | `shopify` | No | `sifen` | integraciones |
| FL Legacy | `fl_facturacion_legacy` | No | `sifen` | facturacion |

---

## Convenciones

| Campo | Formato | Ejemplo |
|-------|---------|---------|
| `name` | snake_case | `mi_app` |
| `app_name` (menú) | snake_case | `mi_app_home` |
| `url` | Path relativo al template | `mi_app/HomeUi.html` |
| `icon` | MDI class | `mdi mdi-home` |
| `prioridad` (menú padre) | Entero, menor = antes | `20`, `40`, `90` |
| `prioridad` (ítem) | Entero secuencial | `1`, `2`, `3` |
| `background` | Hex color | `#10B981` |

---

## Dependencias

Un plugin puede declarar otros plugins como requeridos:

```python
dependencies = ['sifen']  # El plugin sifen debe estar activo
```

El Plugin Manager valida las dependencias antes de activar un plugin para un Business. Si una dependencia no está activa, la activación falla con un mensaje descriptivo.

---

## Categorías Disponibles

| Categoría | Uso |
|-----------|-----|
| `sistema` | Core del ERP (usuarios, permisos) |
| `facturacion` | Facturación, cobros, documentos |
| `compras` | Egresos, órdenes de compra |
| `integraciones` | Shopify, APIs externas |
| `general` | Otros módulos |

---

*Última actualización: 2026-03-11*
*Mantenido por: Equipo de Desarrollo Amachine*
