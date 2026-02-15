# Endpoints y Autenticación - Toca3d

## 📍 Endpoints Principales

### Autenticación

#### `glogin/` - Login de Usuario
- **URL**: `/glogin/`
- **Métodos**: `GET`, `POST`
- **Autenticación**: No requerida
- **Descripción**: Página de inicio de sesión del sistema

**GET Request:**
- Muestra el formulario de login (`LoginUi.html`)

**POST Request:**
```javascript
// Parámetros
{
    "username": "nombre_usuario",
    "password": "contraseña"
}

// Respuesta exitosa
{
    "success": "Hecho!!",
    "refresh": "token_refresh",
    "access": "token_access",
    "username": "nombre_usuario",
    "first_name": "Nombre",
    "last_name": "Apellido"
}

// Respuesta con error
{
    "error": "Acceso denegado"
}
```

#### `glogout/` - Logout de Usuario
- **URL**: `/glogout/`
- **Métodos**: `GET`, `POST`
- **Autenticación**: No requerida
- **Descripción**: Cierre de sesión del usuario

**POST Request:**
```javascript
// Respuesta
{
    "success": "Hecho!!"
}
```

#### `set_auth/` - Autenticación API (Legacy)
- **URL**: `/set_auth/`
- **Método**: `POST`
- **Autenticación**: No requerida
- **Descripción**: Endpoint legacy para autenticación

**Nota**: Este endpoint usa `email` en lugar de `username`. Se recomienda usar `glogin/` en su lugar.

#### `set_logout/` - Logout API (Legacy)
- **URL**: `/set_logout/`
- **Método**: `POST`
- **Autenticación**: No requerida
- **Descripción**: Endpoint legacy para logout

**Nota**: Se recomienda usar `glogout/` en su lugar.

### Vista Principal

#### `/` - Base (Raíz del Sistema)
- **URL**: `/`
- **Método**: `GET`
- **Autenticación**: Requerida
- **Descripción**: Vista principal del sistema
- **Comportamiento**:
  - Si el usuario NO está autenticado → Redirige a `/glogin/`
  - Si el usuario está autenticado → Muestra `BaseUi.html`

### Templates Dinámicos

#### `dtmpl/` - Renderizado de Templates Dinámicos
- **URL**: `/dtmpl/`
- **Método**: `GET`, `POST`
- **Autenticación**: Requerida (`@login_required`)
- **Descripción**: Renderiza templates dinámicamente con parámetros

**Parámetros GET:**
- `tmpl`: Nombre del template a renderizar (default: 'UI.html')
- `dattrs`: JSON con atributos dinámicos
- `model_app_name`: Nombre de la app del modelo (opcional)
- `model_name`: Nombre del modelo (opcional)
- `pk`: ID del registro (opcional)
- `dbcon`: Conexión de base de datos (default: 'default')
- `mobile_view`: Vista móvil (opcional)
- `specific_qdict`: JSON con configuración específica (opcional)
- `surround`: Template que rodea el contenido (opcional)
- `rpt_view`: Vista de reporte (opcional)

**Ejemplo de uso:**
```javascript
// Abrir template en offcanvas
openAppInOffcanvas(
    'Título de la App',
    'ruta/del/template.html',
    'mdi mdi-icon',
    {
        parametro1: 'valor1',
        parametro2: 'valor2'
    }
);
```

#### `api_dtmpl/` - Template Dinámico vía Token
- **URL**: `/api_dtmpl/`
- **Método**: `GET`, `POST`
- **Autenticación**: Token (`@token_validation`)
- **Descripción**: Igual que `dtmpl/` pero acceso vía token JWT

### Ejecución de Métodos

#### `iom/` - Ejecutor de Métodos (IO Manager)
- **URL**: `/iom/`
- **Método**: `POST`
- **Autenticación**: Requerida (`@login_required`)
- **Descripción**: Ejecuta métodos dentro del proyecto según parametrización

**Parámetros POST:**
- `module`: Nombre del módulo
- `package`: Nombre del paquete
- `attr`: Atributo/clase a ejecutar
- `mname`: Nombre del método (opcional)
- `io_task`: Flag para ejecución de tarea (opcional)
- `chains`: Cadenas de ejecución (opcional)
- `groups`: Grupos de ejecución (opcional)

**Ejemplo de uso:**
```javascript
let fdata = new FormData();
fdata.append('module', 'apps_man');
fdata.append('package', 'apps_ui');
fdata.append('attr', 'Menu');
fdata.append('mname', 'get_apps');

axios.post('/iom/', fdata).then(response => {
    console.log(response.data);
});
```

#### `api_iom/` - Ejecutor de Métodos vía Token
- **URL**: `/api_iom/`
- **Método**: `POST`
- **Autenticación**: Token (`@token_validation`)
- **Descripción**: Igual que `iom/` pero acceso vía token JWT

### Autenticación JWT

#### `api_isauth/` - Verificar Autenticación
- **URL**: `/api_isauth/`
- **Método**: `POST`
- **Autenticación**: Token (`@token_validation`)
- **Descripción**: Verifica si el token es válido

**Respuesta:**
```javascript
{
    "is_authenticated": true,
    "accessToken": "token_access",
    "refreshToken": "token_refresh"
}
```

#### `api_refresh/` - Refrescar Token
- **URL**: `/api_refresh/`
- **Método**: `POST`
- **Autenticación**: Refresh Token
- **Descripción**: Genera un nuevo access token usando el refresh token

**Request:**
```javascript
{
    "refresh": "token_refresh"
}
```

**Respuesta:**
```javascript
{
    "access": "nuevo_token_access"
}
```

### Archivos Media

#### `show_media_file/<filename>` - Servir Archivos
- **URL**: `/show_media_file/<filename>`
- **Método**: `GET`
- **Autenticación**: No requerida
- **Descripción**: Sirve archivos generados por el sistema

**Ejemplo:**
```
/show_media_file/uploads/documento.pdf
```

## 🔐 Sistema de Autenticación

### Flujo de Login

1. **Usuario accede a `/`**
   - Sistema verifica si está autenticado
   - Si NO → Redirige a `/glogin/`
   - Si SÍ → Muestra `BaseUi.html`

2. **Usuario ingresa credenciales en `/glogin/`**
   - JavaScript envía POST a `/glogin/` con username y password
   - Backend valida credenciales
   - Si válido:
     - Crea sesión de Django
     - Genera tokens JWT (access y refresh)
     - Retorna JSON con datos del usuario
   - Frontend recibe respuesta y redirige a `/`

3. **Usuario autenticado accede a recursos**
   - Todos los endpoints bajo `@login_required` verifican sesión
   - Endpoints API (`api_*`) verifican token JWT

### Flujo de Logout

1. **Usuario hace click en "Cerrar Sesión"**
   - JavaScript intercepta el click
   - Envía POST a `/glogout/`
   - Backend cierra la sesión de Django
   - Frontend redirige a `/glogin/`

## 🔑 Decoradores de Seguridad

### `@login_required`
- Requiere sesión activa de Django
- Usado en: `iom/`, `dtmpl/`

### `@csrf_exempt`
- Exime de validación CSRF
- Usado en: `glogin/`, `glogout/`, `api_*`

### `@token_validation`
- Valida token JWT
- Usado en: `api_dtmpl/`, `api_iom/`, `api_isauth/`

### `@grab_error`
- Captura y formatea errores
- Usado en: `dtmpl/`, `iom/`

### `@set_fl_user`
- Establece usuario en contexto
- Usado en: `dtmpl/`, `iom/`

## 📊 Estructura de URLs

```
/                           → base (requiere auth)
/glogin/                    → Login (GET: form, POST: auth)
/glogout/                   → Logout
/admin/                     → Django Admin
/set_auth/                  → Auth legacy
/set_logout/                → Logout legacy
/iom/                       → Ejecutor de métodos (requiere auth)
/dtmpl/                     → Templates dinámicos (requiere auth)
/api_dtmpl/                 → Templates vía token
/api_iom/                   → Métodos vía token
/api_isauth/                → Verificar token
/api_refresh/               → Refrescar token
/show_media_file/<path>     → Archivos media
```

## 🛡️ Seguridad

### Recomendaciones

1. **CSRF Protection**
   - Los formularios usan `{% csrf_token %}`
   - Los endpoints API están exentos de CSRF
   - Los requests AJAX incluyen el token CSRF automáticamente

2. **Token JWT**
   - Access Token: Corta duración (15-30 min)
   - Refresh Token: Larga duración (7 días)
   - Almacenar tokens de forma segura (no en localStorage sin encriptar)

3. **HTTPS**
   - En producción, SIEMPRE usar HTTPS
   - Configurar `SECURE_SSL_REDIRECT = True` en settings.py

4. **Validación de Entrada**
   - Todos los parámetros son sanitizados
   - Usar `authenticate()` de Django para validar credenciales

## 📝 Ejemplos de Uso

### Login desde JavaScript

```javascript
async function login(username, password) {
    const formData = new FormData();
    formData.append('username', username);
    formData.append('password', password);

    try {
        const response = await axios.post('/glogin/', formData);
        if (response.data.success) {
            window.location.href = '/';
        } else {
            console.error(response.data.error);
        }
    } catch (error) {
        console.error('Error:', error);
    }
}
```

### Logout desde JavaScript

```javascript
async function logout() {
    try {
        await axios.post('/glogout/', new FormData());
        window.location.href = '/glogin/';
    } catch (error) {
        console.error('Error:', error);
        window.location.href = '/glogin/';
    }
}
```

### Ejecutar método del backend

```javascript
async function ejecutarMetodo() {
    const fdata = new FormData();
    fdata.append('module', 'apps_man');
    fdata.append('package', 'apps_ui');
    fdata.append('attr', 'Menu');
    fdata.append('mname', 'get_apps');

    try {
        const response = await axios.post('/iom/', fdata);
        console.log(response.data);
    } catch (error) {
        console.error('Error:', error);
    }
}
```

### Cargar template dinámico

```javascript
function cargarTemplate() {
    openAppInOffcanvas(
        'Título',
        'ruta/template.html',
        'mdi mdi-home',
        {
            parametro1: 'valor1',
            parametro2: 'valor2'
        }
    );
}
```

## 🔄 Migración de URLs Legacy

Si tienes código que usa las URLs antiguas con `/io/`, actualiza:

```javascript
// Antiguo
'/io/set_auth/'
'/io/dtmpl/'
'/io/iom/'

// Nuevo
'/glogin/'      // Para login
'/dtmpl/'       // Para templates
'/iom/'         // Para métodos
```

## 📚 Referencias

- [Django Authentication](https://docs.djangoproject.com/en/stable/topics/auth/)
- [Django REST Framework JWT](https://www.django-rest-framework.org/api-guide/authentication/#json-web-token-authentication)
- [Axios Documentation](https://axios-http.com/docs/intro)

---

**Fecha de creación**: 2025-11-12
**Última actualización**: 2025-11-12
