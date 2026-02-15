# Configuración de Archivos Estáticos - Toca3d

## 📁 Estructura de Directorios

```
/home/peter/projects/Toca3d/
├── static/                     # Archivos estáticos del proyecto
│   └── hope-ui/               # Template Hope UI
│       ├── css/
│       ├── js/
│       ├── images/
│       └── vendor/
├── staticfiles/               # Archivos estáticos recopilados (producción)
└── media/                     # Archivos subidos por usuarios
```

## ⚙️ Configuración en settings.py

### Archivos Estáticos (Static Files)

```python
# URL para acceder a archivos estáticos
STATIC_URL = 'static/'

# Directorios donde buscar archivos estáticos en desarrollo
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]

# Directorio donde se recopilan archivos estáticos en producción
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
```

### Archivos Media

```python
# URL para acceder a archivos media
MEDIA_URL = '/media/'

# Directorio donde se guardan archivos subidos
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
```

## 🔗 Configuración en urls.py

Para servir archivos estáticos en **modo desarrollo** (DEBUG=True):

```python
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # ... tus URLs ...
]

# Servir archivos estáticos y media en modo desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
```

## 📝 Uso en Templates

### Cargar Tag de Static

En todos los templates que usen archivos estáticos:

```django
{% load static %}
```

### Referenciar Archivos Estáticos

```django
<!-- CSS -->
<link rel="stylesheet" href="{% static 'hope-ui/css/hope-ui.min.css' %}">

<!-- JavaScript -->
<script src="{% static 'hope-ui/js/hope-ui.js' %}"></script>

<!-- Imágenes -->
<img src="{% static 'hope-ui/images/logo.png' %}" alt="Logo">
```

## 🗂️ Estructura de Archivos Hope UI

```
static/hope-ui/
├── css/
│   ├── core/
│   │   └── libs.min.css
│   ├── hope-ui.min.css
│   ├── custom.min.css
│   ├── dark.min.css
│   ├── customizer.min.css
│   └── rtl.min.css
├── js/
│   ├── core/
│   │   ├── libs.min.js
│   │   └── external.min.js
│   ├── charts/
│   │   ├── widgetcharts.js
│   │   ├── vectore-chart.js
│   │   └── dashboard.js
│   ├── plugins/
│   │   ├── fslightbox.js
│   │   ├── setting.js
│   │   ├── slider-tabs.js
│   │   └── form-wizard.js
│   └── hope-ui.js
├── images/
│   ├── auth/
│   ├── avatars/
│   ├── brands/
│   ├── dashboard/
│   └── settings/
└── vendor/
    ├── aos/
    └── flatpickr/
```

## 🚀 Comandos Útiles

### Verificar Archivos Estáticos

```bash
# Ver qué archivos estáticos Django puede encontrar
python manage.py findstatic hope-ui/css/hope-ui.min.css

# Listar todos los archivos estáticos
python manage.py collectstatic --dry-run
```

### Recopilar Archivos Estáticos (Producción)

```bash
# Recopilar todos los archivos estáticos a STATIC_ROOT
python manage.py collectstatic

# Recopilar sin confirmación
python manage.py collectstatic --noinput

# Limpiar archivos antiguos antes de recopilar
python manage.py collectstatic --clear --noinput
```

## 🧪 Verificación

### 1. Verificar que los Directorios Existen

```bash
# Verificar directorio static
ls -la /home/peter/projects/Toca3d/static/

# Verificar hope-ui
ls -la /home/peter/projects/Toca3d/static/hope-ui/

# Crear directorio media si no existe
mkdir -p /home/peter/projects/Toca3d/media/
```

### 2. Probar en el Navegador

Con el servidor de desarrollo corriendo:

```
# Debería cargar el CSS
http://localhost:8000/static/hope-ui/css/hope-ui.min.css

# Debería cargar el JS
http://localhost:8000/static/hope-ui/js/hope-ui.js

# Debería cargar una imagen
http://localhost:8000/static/hope-ui/images/favicon.ico
```

### 3. Verificar en las DevTools

1. Abrir el navegador
2. Presionar F12 para abrir DevTools
3. Ir a la pestaña "Network"
4. Recargar la página
5. Verificar que los archivos .css y .js se carguen con status 200

## ⚠️ Problemas Comunes

### Problema: Archivos no se cargan (404)

**Causa**: Django no encuentra los archivos estáticos

**Solución**:
1. Verificar que `STATICFILES_DIRS` esté configurado correctamente
2. Verificar que la carpeta `static` exista en la raíz del proyecto
3. Reiniciar el servidor de desarrollo: `python manage.py runserver`

### Problema: Archivos se cargan pero no se actualizan

**Causa**: Caché del navegador

**Solución**:
1. Hacer hard refresh: `Ctrl + Shift + R` (Linux/Windows) o `Cmd + Shift + R` (Mac)
2. Limpiar caché del navegador
3. Agregar version query string: `{% static 'file.css' %}?v=2.0.0`

### Problema: Archivos funcionan en desarrollo pero no en producción

**Causa**: No se ejecutó `collectstatic`

**Solución**:
```bash
python manage.py collectstatic --noinput
```

## 📦 Producción

### Servir Archivos Estáticos

En producción, **NO usar** el servidor de desarrollo de Django para servir archivos estáticos.

#### Opción 1: Nginx

```nginx
location /static/ {
    alias /home/peter/projects/Toca3d/staticfiles/;
}

location /media/ {
    alias /home/peter/projects/Toca3d/media/;
}
```

#### Opción 2: WhiteNoise (Más simple)

1. Instalar WhiteNoise:
```bash
pip install whitenoise
```

2. Agregar a `MIDDLEWARE` en settings.py:
```python
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # ← Agregar aquí
    # ... otros middleware ...
]
```

3. Configurar compresión (opcional):
```python
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
```

## 🔒 Seguridad

### Desarrollo (DEBUG=True)

```python
# OK servir archivos estáticos con Django
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, ...)
```

### Producción (DEBUG=False)

```python
# settings.py
DEBUG = False
ALLOWED_HOSTS = ['tu-dominio.com']

# NUNCA usar Django para servir archivos estáticos
# Usar Nginx, Apache, o WhiteNoise
```

## 📊 Rendimiento

### Comprimir Archivos CSS/JS

En producción, usar archivos minificados:
- ✅ `hope-ui.min.css` (ya minificado)
- ✅ `hope-ui.min.js` (ya minificado)
- ✅ `libs.min.css` (ya minificado)
- ✅ `libs.min.js` (ya minificado)

### Caché del Navegador

Configurar headers de caché en Nginx/Apache:

```nginx
location /static/ {
    alias /path/to/staticfiles/;
    expires 1y;
    add_header Cache-Control "public, immutable";
}
```

### CDN (Opcional)

Para mejor rendimiento global, usar un CDN:

```python
# settings.py (producción)
STATIC_URL = 'https://cdn.tu-dominio.com/static/'
```

## 🔍 Debugging

### Ver qué archivos Django puede encontrar

```python
# En shell de Django
python manage.py shell

>>> from django.contrib.staticfiles import finders
>>> finders.find('hope-ui/css/hope-ui.min.css')
'/home/peter/projects/Toca3d/static/hope-ui/css/hope-ui.min.css'
```

### Listar todos los archivos estáticos

```bash
python manage.py findstatic --verbosity 2 hope-ui/
```

## 📚 Referencias

- [Django Static Files](https://docs.djangoproject.com/en/stable/howto/static-files/)
- [Django STATICFILES_DIRS](https://docs.djangoproject.com/en/stable/ref/settings/#staticfiles-dirs)
- [WhiteNoise Documentation](http://whitenoise.evans.io/)

---

**Fecha de creación**: 2025-11-12
**Última actualización**: 2025-11-12
