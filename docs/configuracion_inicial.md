# Configuración Inicial del Sistema - Toca3d

## ✅ Cambios Realizados

### 1. Vista Principal `base`

Se creó la vista `base` en `OptsIO/views.py` que:
- Verifica si el usuario está autenticado
- Si NO está autenticado → Redirige a `/io/glogin/`
- Si está autenticado → Muestra `BaseUi.html`

```python
def base(request):
    """
    Vista principal del sistema.
    Si el usuario no está autenticado, redirige a login.
    Si está autenticado, muestra la interfaz base.
    """
    if not request.user.is_authenticated:
        return redirect('glogin')

    rr = str(uuid.uuid4()).replace('-', '')[0:5]
    return render(request, "BaseUi.html", {'rr': rr})
```

### 2. Configuración de URLs

#### `Toca3d/urls.py` (Principal)
```python
from OptsIO.views import base

urlpatterns = [
    path('admin/', admin.site.urls),
    path('io/', include('OptsIO.urls')),      # Endpoints de OptsIO
    path('', base, name='base'),              # Vista principal en la raíz
]
```

#### `OptsIO/urls.py`
Los endpoints de OptsIO se mantienen bajo el prefijo `/io/`:
```python
urlpatterns = [
    path('set_auth/', set_auth, name='set_auth'),
    path('set_logout/', set_logout, name='set_logout'),
    path('iom/', login_required(iom), name='iom'),
    path('dtmpl/', login_required(dtmpl), name='dtmpl'),
    path('api_dtmpl/', api_dtmpl, name='api_dtmpl'),
    path('api_iom/', api_iom, name='api_iom'),
    path('api_isauth/', api_isauth, name='api_isauth'),
    path('api_refresh/', TokenRefreshView.as_view(), name='api_refresh'),
    path('glogin/', glogin, name='glogin'),
    path('glogout/', glogout, name='glogout'),
    re_path('show_media_file/(?P<filename>[0-9\w|\/\.\-]+)', show_media_file, name='show_media_file'),
]
```

### 3. Actualización de Templates

#### `LoginUi.html`
- Formulario de login con AJAX
- Redirección automática a `/` después de login exitoso
- Usa endpoint `/io/glogin/`

#### `AMToolbarUi.html`
- Link de logout actualizado a `/io/glogout/`
- Script AJAX para manejar el logout
- Redirección a `/io/glogin/` después de logout

#### `AMOffcanvasUi.html`
- Función `openAppInOffcanvas()` usa endpoint `/io/dtmpl/`
- Carga templates dinámicamente en offcanvas

#### `AppsUi.html`
- Todas las llamadas AJAX usan `/io/iom/`
- Sistema de bookmarks, menús y apps intacto

## 🔗 Mapa de URLs

### URLs Principales
```
/                           → Vista base (requiere autenticación)
/admin/                     → Django Admin
```

### URLs de OptsIO (Prefijo `/io/`)
```
/io/glogin/                 → Login (GET: form, POST: authenticate)
/io/glogout/                → Logout
/io/set_auth/               → Auth legacy
/io/set_logout/             → Logout legacy
/io/iom/                    → Ejecutor de métodos (requiere auth)
/io/dtmpl/                  → Templates dinámicos (requiere auth)
/io/api_dtmpl/              → Templates vía token
/io/api_iom/                → Métodos vía token
/io/api_isauth/             → Verificar token
/io/api_refresh/            → Refrescar token
/io/show_media_file/<path>  → Archivos media
```

## 🔄 Flujo de Navegación

### Acceso Inicial
```
1. Usuario accede a "/"
   ↓
2. Sistema verifica autenticación
   ↓
3. No autenticado → Redirige a "/io/glogin/"
   Autenticado → Muestra "BaseUi.html"
```

### Login
```
1. Usuario ingresa credenciales en "/io/glogin/"
   ↓
2. JavaScript envía POST a "/io/glogin/"
   ↓
3. Backend valida credenciales
   ↓
4. Si válido:
   - Crea sesión Django
   - Genera tokens JWT
   - Retorna JSON success
   ↓
5. Frontend redirige a "/"
   ↓
6. Sistema muestra "BaseUi.html"
```

### Logout
```
1. Usuario click en "Cerrar Sesión"
   ↓
2. JavaScript envía POST a "/io/glogout/"
   ↓
3. Backend cierra sesión
   ↓
4. Frontend redirige a "/io/glogin/"
```

### Cargar Aplicación en Offcanvas
```
1. Usuario click en app desde AppsUi
   ↓
2. JavaScript llama openAppInOffcanvas()
   ↓
3. Función envía POST a "/io/dtmpl/"
   ↓
4. Backend renderiza template
   ↓
5. JavaScript muestra contenido en offcanvas
```

## 📝 Archivos Modificados

### Vistas (OptsIO/views.py)
- ✅ Importado `redirect`
- ✅ Vista `glogin` actualizada para usar `LoginUi.html`
- ✅ Vista `glogout` actualizada para usar `LoginUi.html`
- ✅ Nueva vista `base` creada

### URLs
- ✅ `Toca3d/urls.py` - Agregada ruta raíz y mantenido `/io/`
- ✅ `OptsIO/urls.py` - Mantenidos todos los endpoints

### Templates
- ✅ `LoginUi.html` - AJAX login con redirección
- ✅ `AMToolbarUi.html` - Logout con AJAX
- ✅ `AMOffcanvasUi.html` - Endpoint dtmpl correcto
- ✅ `AppsUi.html` - Endpoints iom correctos

## 🧪 Pruebas Recomendadas

### 1. Verificar Redirección
```bash
# Sin autenticación, debe redirigir a login
curl -I http://localhost:8000/

# Debe retornar 302 Found
# Location: /io/glogin/
```

### 2. Probar Login
```bash
# Acceder a la página de login
curl http://localhost:8000/io/glogin/

# Debe retornar el HTML del formulario de login
```

### 3. Probar Autenticación
- Acceder a `http://localhost:8000/`
- Debe redirigir a `http://localhost:8000/io/glogin/`
- Ingresar credenciales válidas
- Debe redirigir a `http://localhost:8000/` y mostrar BaseUi.html

### 4. Probar Logout
- Estando autenticado, hacer click en "Cerrar Sesión"
- Debe redirigir a `http://localhost:8000/io/glogin/`
- Intentar acceder a `http://localhost:8000/`
- Debe redirigir nuevamente a login

### 5. Probar Offcanvas
- Autenticado, hacer click en una app del menú
- Debe abrir offcanvas desde arriba
- Debe cargar el contenido del template
- Debe poder cerrar con botón X o ESC

## ⚠️ Puntos Importantes

1. **Prefijo `/io/`**: Todos los endpoints de OptsIO usan este prefijo
2. **Vista raíz**: La raíz `/` está definida en `Toca3d/urls.py`
3. **Named URLs**: Los endpoints usan nombres como `glogin`, `glogout`, etc.
4. **Templates Dinámicos**: Endpoint `dtmpl` en `/io/dtmpl/`
5. **Ejecutor de Métodos**: Endpoint `iom` en `/io/iom/`

## 🔐 Seguridad

### Decoradores Aplicados
- `@login_required`: Para `iom` y `dtmpl`
- `@csrf_exempt`: Para `glogin`, `glogout` y endpoints API
- `@token_validation`: Para endpoints API

### Validación de Sesión
- La vista `base` verifica `request.user.is_authenticated`
- Redirige a login si no está autenticado
- Mantiene la sesión de Django

## 📚 Próximos Pasos

1. ✅ Configurar base de datos PostgreSQL
2. ✅ Ejecutar migraciones: `python manage.py migrate`
3. ✅ Crear superusuario: `python manage.py createsuperuser`
4. ✅ Configurar `STATIC_ROOT` y `MEDIA_ROOT` en settings.py
5. ✅ Ejecutar `python manage.py collectstatic`
6. ✅ Probar login con usuario creado
7. ⏳ Crear modelo `Apps` para el menú de aplicaciones
8. ⏳ Implementar métodos del backend en `apps_man.apps_ui.Menu`

---

**Fecha de creación**: 2025-11-12
**Última actualización**: 2025-11-12
