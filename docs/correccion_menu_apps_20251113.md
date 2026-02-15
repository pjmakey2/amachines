# Corrección de Menús y Apps - 13 de Noviembre 2025

## Resumen
Se identificaron y corrigieron 4 problemas que impedían que los menús y apps se cargaran correctamente después del login.

---

## Problemas Identificados y Soluciones

### 1. 🔴 CRÍTICO: Token CSRF faltante en BaseUi.html

**Archivo:** `templates/BaseUi.html:15`

**Descripción del Problema:**
- El template BaseUi.html no incluía el tag `{% csrf_token %}`
- El JavaScript en `AMJS.html:54-57` buscaba el token con `document.querySelector('[name=csrfmiddlewaretoken]')` pero no lo encontraba
- Cuando el frontend intentaba hacer llamadas POST a `/io/iom/` para cargar menús y apps, Django rechazaba la petición con error **"CSRF token missing"** (403 Forbidden)

**Impacto:**
- ❌ No se podían cargar los menús
- ❌ No se podían cargar las apps
- ❌ No se podían cargar los bookmarks
- ❌ Cualquier llamada POST a `/io/iom/` o `/io/dtmpl/` fallaba

**Solución Aplicada:**
```html
<body class="" data-bs-spy="scroll" data-bs-target="#elements-section" data-bs-offset="0" tabindex="0">
    {% csrf_token %}
    <!-- Loader Start -->
    <div id="loading">
        <div class="loader"></div>
    </div>
    <!-- Resto del contenido -->
```

---

### 2. 🔴 CRÍTICO: Error en importación de módulos

**Archivo:** `OptsIO/io_execution.py:60`

**Descripción del Problema:**
- El código intentaba importar `apps_man.apps_ui` directamente
- Python no podía encontrar el módulo porque la ruta correcta es `OptsIO.apps_man.apps_ui`
- Error: `ModuleNotFoundError: No module named 'apps_man'`

**Código Original:**
```python
dobj = getattr(importlib.import_module(f'{module}.{package}'), attr)
```

**Código Corregido:**
```python
dobj = getattr(importlib.import_module(f'OptsIO.{module}.{package}'), attr)
```

**Razón:**
- El frontend envía `module='apps_man'` y `package='apps_ui'`
- El sistema necesita buscar en `OptsIO/apps_man/apps_ui.py`
- La ruta completa de importación debe ser `OptsIO.apps_man.apps_ui`

---

### 3. 🔴 CRÍTICO: Parámetros incorrectos al instanciar clases

**Archivo:** `OptsIO/io_execution.py:64-66`

**Descripción del Problema:**
- Al instanciar una clase para llamar un método, no se pasaban parámetros al constructor
- Luego se intentaba pasar los parámetros al método, causando error
- Error: `Menu.get_apps() got an unexpected keyword argument 'userobj'`

**Código Original:**
```python
if inspect.isclass(dobj):
    if not mname:
         return {'error': 'Falta proveer el metodo para la ejecucion'}
    cls = dobj()  # ❌ Sin parámetros
    dobj = getattr(cls, mname)
#converge mysql user with django user

return dobj(userobj=rq.user,  # ❌ Intentaba pasar parámetros al método
            rq=rq,
            files=rq.FILES,
            qdict=rq.POST,
            )
```

**Código Corregido:**
```python
if inspect.isclass(dobj):
    if not mname:
         return {'error': 'Falta proveer el metodo para la ejecucion'}
    cls = dobj(userobj=rq.user, rq=rq, files=rq.FILES, qdict=rq.POST)  # ✅ Parámetros al constructor
    dobj = getattr(cls, mname)
    return dobj()  # ✅ Llamar método sin parámetros
#converge mysql user with django user

return dobj(userobj=rq.user,
            rq=rq,
            files=rq.FILES,
            qdict=rq.POST,
            )
```

---

### 3.1 Actualización del constructor de la clase Menu

**Archivo:** `OptsIO/apps_man/apps_ui.py:8`

**Descripción del Problema:**
- El constructor de `Menu` solo aceptaba `request` y `qdict`
- `io_execution.py` enviaba `userobj`, `rq`, `files`, `qdict`
- Había incompatibilidad en los nombres de parámetros

**Código Original:**
```python
def __init__(self, request=None, qdict=None, **kwargs):
    self.request = request
    self.qdict = qdict or {}
    self.kwargs = kwargs
```

**Código Corregido:**
```python
def __init__(self, userobj=None, rq=None, files=None, qdict=None, **kwargs):
    self.userobj = userobj
    self.request = rq
    self.files = files
    self.qdict = qdict or {}
    self.kwargs = kwargs
```

---

### 4. 🟡 UI: Botón de configuración del tema innecesario

**Archivo:** `templates/BaseUi.html:60`

**Descripción del Problema:**
- El botón de configuración del tema (engranaje) en la esquina inferior derecha no era necesario
- Mostraba opciones de tema (modo claro/oscuro, esquemas de color, RTL/LTR) que no se utilizaban

**Solución Aplicada:**
```html
<!-- START Theme Settings -->
{# {% include "./AMThemeSettingsUi.html" %} #}
<!-- END Theme Settings -->
```

---

## Archivos Modificados

1. `templates/BaseUi.html`
   - Agregado `{% csrf_token %}` en línea 15
   - Comentado include de `AMThemeSettingsUi.html` en línea 60

2. `OptsIO/io_execution.py`
   - Modificado import para agregar prefijo `OptsIO.` en línea 60
   - Corregida instanciación de clases en líneas 64-66

3. `OptsIO/apps_man/apps_ui.py`
   - Actualizada firma del constructor en línea 8

---

## Pruebas Realizadas

### Login
```bash
curl -X POST http://localhost:8000/io/glogin/ \
  -d "username=amadmin&password=zz9cd3zrsXe9kU@IBi5A"
```
**Resultado:** ✅ Login exitoso, retorna tokens JWT

### Cargar Apps
```bash
curl -X POST http://localhost:8000/io/iom/ \
  -H "X-CSRFToken: <token>" \
  -b cookies.txt \
  -d "module=apps_man&package=apps_ui&attr=Menu&mname=get_apps"
```
**Resultado:** ✅ Devuelve 3 apps (Facturar, Retenciones, Recibo)

### Cargar Menús
```bash
curl -X POST http://localhost:8000/io/iom/ \
  -H "X-CSRFToken: <token>" \
  -b cookies.txt \
  -d "module=apps_man&package=apps_ui&attr=Menu&mname=get_menus"
```
**Resultado:** ✅ Devuelve 1 menú (Sifen - Facturación Electrónica)

### Cargar Bookmarks
```bash
curl -X POST http://localhost:8000/io/iom/ \
  -H "X-CSRFToken: <token>" \
  -b cookies.txt \
  -d "module=apps_man&package=apps_ui&attr=Menu&mname=get_bookmarks"
```
**Resultado:** ✅ Devuelve lista vacía (sin bookmarks configurados para el usuario)

---

## Endpoints Principales

### 1. `/io/glogin/` - Login (POST)
- Autentica usuario con username y password
- Retorna tokens JWT (access y refresh)
- Crea sesión Django

### 2. `/io/iom/` - Ejecutor de Módulos (POST, requiere autenticación)
- Ejecuta métodos de módulos Python dinámicamente
- Parámetros:
  - `module`: Nombre del módulo (ej: `apps_man`)
  - `package`: Nombre del paquete (ej: `apps_ui`)
  - `attr`: Clase o función (ej: `Menu`)
  - `mname`: Método a ejecutar (ej: `get_apps`)
- Usado para: cargar menús, apps, bookmarks, etc.

### 3. `/io/dtmpl/` - Carga de Templates Dinámicos (POST, requiere autenticación)
- Carga templates HTML con contexto
- Usado para cargar interfaces de apps en offcanvas

---

## Flujo de Inicialización del Sistema

1. Usuario accede a `/io/glogin/` e ingresa credenciales
2. Backend autentica y crea sesión + tokens JWT
3. Usuario es redirigido a `/` (página base)
4. `BaseUi.html` se carga e incluye `AppsUi.html`
5. JavaScript ejecuta en `DOMContentLoaded`:
   - Obtiene token CSRF del campo oculto
   - Configura axios con header `X-CSRFToken`
   - Llama a `loadMenusAndApps()` → `/io/iom/` con `mname=get_apps`
   - Llama a `loadBookmarks()` → `/io/iom/` con `mname=get_bookmarks`
6. Sidebar se puebla con menús agrupados por apps
7. Usuario puede hacer click en apps para abrir en offcanvas

---

## Notas Técnicas

### Sistema de Importación Dinámica
El sistema usa `importlib.import_module()` para cargar módulos dinámicamente basándose en parámetros POST. Esto permite:
- Modularidad y extensibilidad
- Agregar nuevas funcionalidades sin modificar rutas
- Reutilización del endpoint `/io/iom/` para múltiples propósitos

### Seguridad CSRF
Django requiere token CSRF en todas las peticiones POST que modifican estado. El sistema:
1. Genera token con `{% csrf_token %}` en el template
2. JavaScript lo lee con `document.querySelector('[name=csrfmiddlewaretoken]')`
3. Axios lo envía en header `X-CSRFToken` en cada petición

### Autenticación
El sistema usa dos métodos de autenticación:
1. **Sesión Django** para endpoints web (`/io/iom/`, `/io/dtmpl/`)
2. **JWT Tokens** para endpoints API (`/io/api_iom/`, `/io/api_dtmpl/`)

---

## Estado Final

✅ **Todos los problemas resueltos**
- Token CSRF presente y funcional
- Módulos se importan correctamente con prefijo `OptsIO.`
- Clases se instancian con parámetros correctos
- Botón de configuración del tema oculto
- Menús y apps cargan correctamente después del login

---

## Fecha de Corrección
13 de Noviembre de 2025
