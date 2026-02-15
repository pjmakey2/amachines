# Estructura Inicial del Proyecto Toca3d

## ✅ Tareas Completadas

### 1. **Descompresión y Análisis del Template Hope UI**
   - Descomprimí `hope-ui-html-2.0.zip`
   - Copié todos los assets (CSS, JS, imágenes) a `/static/hope-ui/`
   - Analicé la estructura del template para adaptarlo al proyecto

### 2. **Archivos Modulares Creados con Prefijo AM:**

   - **AMCSS.html** - Contiene todos los estilos CSS del template Hope UI
   - **AMJS.html** - Contiene todos los scripts JavaScript del template
   - **AMOffcanvasUi.html** - Offcanvas que se despliega desde arriba ocupando toda la página, con botón de cierre y soporte para ESC
   - **AMModalUi.html** - Modales genéricos del sistema
   - **AMToolbarUi.html** - Barra de herramientas superior con buscador, notificaciones y perfil de usuario
   - **AMThemeSettingsUi.html** - Panel de configuración del tema

### 3. **BaseUi.html**
   - Archivo base modular que incluye todos los componentes AM
   - Estructura Django con bloques `{% block content %}` y `{% block extra_css/js %}`
   - Loader integrado
   - Soporte para usuarios bloqueados

### 4. **LoginUi.html**
   - Basado en el template `sign-in.html` de Hope UI
   - Adaptado para Django con formulario de autenticación
   - Diseño responsive con imagen lateral
   - Integración con mensajes de Django

### 5. **AppsUi.html Actualizado**
   - **CAMBIO PRINCIPAL**: Ahora usa `openAppInOffcanvas()` en lugar de `OTabs.openOrFocusWindow()`
   - El offcanvas se despliega desde arriba y ocupa toda la página
   - Se cierra con el botón X o con la tecla ESC
   - Carga el contenido dinámicamente mediante el endpoint `dtmpl`
   - Mantiene todas las funcionalidades existentes: drag & drop, bookmarks, reordenar menús/apps, editar nombres

## 📁 Estructura de Archivos Creada

```
/home/peter/projects/Toca3d/
├── static/
│   └── hope-ui/
│       ├── css/
│       ├── js/
│       ├── images/
│       └── vendor/
└── templates/
    ├── AMCSS.html
    ├── AMJS.html
    ├── AMOffcanvasUi.html
    ├── AMModalUi.html
    ├── AMToolbarUi.html
    ├── AMThemeSettingsUi.html
    ├── BaseUi.html
    ├── LoginUi.html
    └── AppsUi.html
```

## 🔄 Cambios Importantes en AppsUi.html

La función que antes era:
```javascript
OTabs.openOrFocusWindow('{% url "dinamic_template" %}?...')
```

Ahora es:
```javascript
openAppInOffcanvas(app_friendly_name, app_url, app_icon, ajson)
```

Esta nueva función:
- Abre un offcanvas desde arriba que ocupa el 100% de la pantalla
- Carga el contenido mediante POST al endpoint `dtmpl`
- Muestra un spinner mientras carga
- Se puede cerrar con el botón X o con ESC
- Maneja errores de carga

## 📝 Archivos Modulares - Descripción Detallada

### AMCSS.html
Contiene las referencias a todos los estilos CSS del template Hope UI:
- Favicon
- Library / Plugin Css Build (libs.min.css)
- Aos Animation Css
- Hope UI Design System Css (hope-ui.min.css)
- Custom Css (custom.min.css)
- Dark Mode Css (dark.min.css)
- Customizer Css (customizer.min.css)
- RTL Css (rtl.min.css)

### AMJS.html
Contiene las referencias a todos los scripts JavaScript del template:
- Library Bundle Script (libs.min.js)
- External Library Bundle Script (external.min.js)
- Widgetchart Script
- Mapchart Script
- Dashboard Script
- Fslightbox Script
- Settings Script
- Slider-tab Script
- Form Wizard Script
- AOS Animation Plugin
- Hope UI App Script (hope-ui.js)

### AMOffcanvasUi.html
Offcanvas para las aplicaciones con las siguientes características:
- Se despliega desde arriba (`offcanvas-top`)
- Ocupa el 100% de la altura de la pantalla (`h-100`)
- Header con título dinámico y botón de cierre
- Body que carga contenido dinámicamente vía AJAX
- Spinner de carga mientras se obtiene el contenido
- Función JavaScript `openAppInOffcanvas(title, templateUrl, icon, ajson)` que:
  - Actualiza el título y el ícono del offcanvas
  - Muestra el offcanvas usando Bootstrap 5
  - Realiza una petición POST al endpoint `dtmpl`
  - Carga el contenido en el offcanvas
  - Ejecuta scripts dentro del contenido cargado
  - Maneja errores de carga
- Soporte para cerrar con ESC mediante event listener

### AMModalUi.html
Sistema de modales del proyecto:
- **globalModal**: Modal genérico configurable
  - Título dinámico
  - Body dinámico
  - Footer personalizable
  - Función `showGlobalModal(title, content, footerButtons)`
- **confirmModal**: Modal de confirmación
  - Para acciones que requieren confirmación del usuario
  - Función `showConfirmModal(message, onConfirm, title)`
  - Callback personalizable para ejecutar al confirmar

### AMToolbarUi.html
Barra de herramientas superior con:
- Logo y nombre del sistema (TOCA3D)
- Buscador de aplicaciones (condicional según parámetro `search_app`)
- Botón de menú responsive (hamburger menu)
- Área de notificaciones con dropdown
- Perfil de usuario con:
  - Avatar
  - Nombre completo del usuario
  - Puesto/rol
  - Dropdown con opciones: Perfil, Configuración, Cerrar Sesión
- Estilos personalizados para el buscador con ícono de lupa

### AMThemeSettingsUi.html
Panel de configuración del tema:
- Offcanvas lateral derecho
- Opciones de configuración:
  - **Modo de Color**: Auto, Claro, Oscuro
  - **Esquema de Color**: 5 variantes de color predefinidas
  - **Dirección**: LTR (Left to Right) / RTL (Right to Left)
- Botón flotante en la esquina inferior derecha con ícono de engranaje giratorio
- Integración con el sistema de settings de Hope UI

### BaseUi.html
Template base del sistema:
- Estructura HTML5 completa
- Meta tags para responsive design
- Inclusión modular de componentes:
  - CSS mediante `{% include "./AMCSS.html" %}`
  - Offcanvas mediante `{% include "./AMOffcanvasUi.html" %}`
  - Modales mediante `{% include "./AMModalUi.html" %}`
  - Toolbar mediante `{% include "./AMToolbarUi.html" %}`
  - Apps Menu mediante `{% include "./AppsUi.html" %}`
  - Theme Settings mediante `{% include "./AMThemeSettingsUi.html" %}`
  - JavaScript mediante `{% include "./AMJS.html" %}`
- Loader de página
- Bloques Django para extensión:
  - `{% block extra_css %}` - CSS adicional
  - `{% block content %}` - Contenido principal
  - `{% block extra_js %}` - JavaScript adicional
- Soporte para lock screen (oculta toolbar si el usuario está bloqueado)

### LoginUi.html
Página de inicio de sesión:
- Diseño dividido en dos columnas (50/50)
- Columna izquierda:
  - Logo y título TOCA3D
  - Formulario de login con:
    - Campo de usuario
    - Campo de contraseña
    - Checkbox "Recordarme"
    - Link "¿Olvidaste tu contraseña?"
  - Botón de "Iniciar Sesión"
  - Área para mostrar mensajes de Django
  - Decoración SVG de fondo
- Columna derecha:
  - Imagen de fondo con gradiente
  - Solo visible en pantallas medianas o mayores (responsive)
- Integración completa con el sistema de autenticación de Django
- Auto-oculta el loader cuando la página termina de cargar

### AppsUi.html
Sistema completo de gestión de aplicaciones:

#### Características principales:
1. **Grid de Aplicaciones**
   - Diseño responsive basado en CSS Grid
   - Agrupación por menús
   - Iconos personalizables con degradados
   - Hover effects y animaciones

2. **Bookmarks**
   - Área para aplicaciones favoritas
   - Drag & drop desde el grid de apps
   - Reordenamiento mediante drag & drop
   - Guardado de prioridades en base de datos
   - Eliminación con confirmación

3. **Búsqueda**
   - Búsqueda en tiempo real
   - Filtra por nombre de app o menú
   - Muestra mensaje cuando no hay resultados

4. **Modos de Edición**
   - **Reordenar Menús**: Permite cambiar el orden de las secciones de menú
   - **Reordenar Apps**: Permite cambiar el orden de las apps dentro de cada menú
   - **Editar Nombres**: Permite cambiar el nombre amigable de las apps (solo DIRECTOR)

5. **Funciones JavaScript principales**
   - `loadApps()`: Carga las aplicaciones desde el endpoint
   - `loadBookmarks()`: Carga los bookmarks del usuario
   - `createAppCard(app)`: Crea una tarjeta de aplicación
   - `createBookmarkItem(app, bookmarkPk)`: Crea un item de bookmark
   - `openAppInOffcanvas(title, templateUrl, icon, ajson)`: **NUEVA** - Abre apps en offcanvas
   - `setupBookmarksDropZone()`: Configura el área de drop para bookmarks
   - `toggleReorderMenusMode()`: Activa/desactiva modo de reordenar menús
   - `toggleReorderAppsMode()`: Activa/desactiva modo de reordenar apps
   - `toggleEditNamesMode()`: Activa/desactiva modo de editar nombres
   - `saveAppsBookmarkAsync(app_pk)`: Guarda un bookmark (async)
   - `saveBookMarkPrioridad()`: Guarda las prioridades de los bookmarks
   - `update_app_name()`: Actualiza los nombres de las apps
   - `update_appmenu_prioridad()`: Actualiza las prioridades de menús y apps

6. **Integración con Backend**
   - Endpoint: `{% url "em" %}` (endpoint manager)
   - Módulo: `apps_man`
   - Package: `apps_ui`
   - Métodos disponibles:
     - `get_apps`: Obtiene todas las aplicaciones
     - `get_bookmarks`: Obtiene los bookmarks del usuario
     - `save_bookmark`: Guarda un nuevo bookmark
     - `delete_bookmark`: Elimina un bookmark
     - `set_bookmarks_prioridad`: Actualiza prioridades de bookmarks
     - `update_app_name`: Actualiza el nombre de una app
     - `update_appmenu_prioridad`: Actualiza prioridades de menús y apps

## 🎨 Sistema de Estilos

### Paleta de Colores
- Primary: `#667eea` - `#764ba2` (gradiente)
- Background: Gradiente blanco a azul translúcido
- Shadows: Sombras suaves con opacidad variable

### Responsive Breakpoints
- Desktop: > 1200px - Grid 4 columnas para apps
- Tablet: 768px - 1200px - Grid 3 columnas para apps
- Mobile: < 768px - Grid 3 columnas para apps, controles compactos

### Animaciones
- `fadeIn`: Aparición suave de elementos
- `spin`: Rotación para spinners de carga
- Transiciones suaves en hover y drag & drop

## 🔌 Endpoints del Sistema

### Autenticación
- `set_auth/`: Autenticación de usuario
- `set_logout/`: Cierre de sesión

### Templates Dinámicos
- `dinamic_template/` (`dtmpl/`): Renderiza templates de las Apps con parámetros
- `api_dtmpl/`: Mismo que dtmpl pero con acceso vía token

### Ejecución de Métodos
- `em/` (`iom/`): Ejecuta métodos dentro del proyecto según parametrización
- `api_iom/`: Mismo que iom pero con acceso vía token

### Otros
- `glogin/`: Interfaz para realizar login
- `glogout/`: Salir del sistema
- `show_media_file/<filename>`: Acceso a archivos generados por el sistema
- `api_isauth/`: Verificación de autenticación vía token
- `api_refresh/`: Refrescar token

## 🚀 Próximos Pasos Sugeridos

1. Configurar las rutas de Django para los templates creados
2. Implementar los métodos del backend en `apps_man.apps_ui.Menu`
3. Crear el modelo `Apps` en la base de datos si no existe
4. Configurar la carpeta `static` en settings.py
5. Probar el login con usuarios reales
6. Verificar que el endpoint `dtmpl` funcione correctamente con el offcanvas
7. Crear aplicaciones de ejemplo para poblar el menú

## 📚 Dependencias Frontend

### Hope UI Template
- Bootstrap 5
- jQuery (para selectores en algunas funciones)
- Axios (para peticiones HTTP)
- AOS (Animate On Scroll)
- Material Design Icons (mdi)
- Flatpickr (date picker)
- fslightbox (lightbox para imágenes)

### Scripts Personalizados
- Todos los scripts de Hope UI están incluidos vía AMJS.html
- Scripts adicionales en cada template modular

## 🔒 Seguridad

- Uso de `{% csrf_token %}` en formularios
- Autenticación de Django integrada
- Verificación de roles (ejemplo: solo DIRECTOR puede editar nombres)
- Validación de usuarios bloqueados (lock_screen)

## 📱 Características Responsive

- Grid adaptable según tamaño de pantalla
- Menú hamburger en móviles
- Imágenes y avatares escalables
- Offcanvas ocupa 100vh en todas las resoluciones
- Controles táctiles optimizados para móviles

---

**Fecha de creación**: 2025-11-12
**Versión Hope UI**: 2.0.0
**Framework**: Django + Bootstrap 5
