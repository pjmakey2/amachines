# Sistema de Setup Autoconfigurable - Amachine ERP

## Descripción General

El sistema de setup autoconfigurable permite configurar Amachine ERP a través de una interfaz web sin necesidad de editar archivos manualmente. Este sistema guía al usuario a través de la configuración inicial de la base de datos, creación del archivo `.env`, carga de datos de referencia y configuración de la empresa.

## Flujo del Proceso

### Paso 1: Configuración de Base de Datos
- **URL**: `/setup/`
- **Descripción**: Formulario para configurar la conexión a PostgreSQL
- **Campos**:
  - Host de Base de Datos (localhost, 127.0.0.1, db)
  - Puerto (por defecto: 5432)
  - Nombre de Base de Datos
  - Usuario
  - Contraseña
- **Funcionalidad**: Botón "Probar Conexión" para validar antes de continuar

### Paso 2: Crear archivo .env
- **URL**: `/setup/step2/`
- **Descripción**: Procesa la configuración y crea el archivo .env
- **Resultado**:
  - Crea archivo `.env` con todas las variables necesarias
  - Genera `SECRET_KEY` automáticamente
  - Configura Redis y Celery
  - **IMPORTANTE**: Requiere reinicio del servidor

### Paso 3: Cargar Datos y Configurar Sistema
- **URL**: `/setup/finalize/`
- **Descripción**: Ejecuta las configuraciones finales después del reinicio
- **Acciones**:
  1. Ejecuta migraciones (`python manage.py migrate`)
  2. Descubre y registra plugins del sistema
  3. Carga datos de referencia de todos los plugins:
     - Tipos de Contribuyente
     - Geografías (Departamentos, Ciudades, Barrios)
     - Actividades Económicas
     - Unidades de Medida
     - Porcentajes IVA
     - Métodos de Pago
  4. Crea superusuario administrador
  5. Ejecuta `setup_sifen_menu` para crear menús del sistema
- **Resultado**: Redirige a `/setup/business/` para configurar empresa

### Paso 4: Configurar Empresa
- **URL**: `/setup/business/`
- **Descripción**: Formulario para crear el primer Business (empresa)
- **Campos**:
  - Datos Básicos: Nombre, Abreviatura, RUC, DV, Tipo Contribuyente
  - Datos de Facturación: Nombre en factura, Nombre fantasía, Actividad económica
  - Dirección: Dirección, Número, Ciudad
  - Contacto: Teléfono, Celular, Email, Web
- **Resultado**:
  - Crea el primer Business
  - Activa plugins core para el Business
  - Marca setup como completado (crea archivo `.setup_completed`)
  - Redirige a `/glogin/` para acceder al sistema

## Componentes del Sistema

### 1. SetupManager (`OptsIO/setup_manager.py`)

Clase principal que maneja toda la lógica del setup:

```python
from OptsIO.setup_manager import SetupManager

setup = SetupManager()

# Verificar si setup está completado
if setup.is_setup_completed():
    # Ya configurado
    pass

# Validar conexión a BD
success, msg = setup.validate_database_connection({
    'DB_NAME': 'amachine',
    'DB_USER': 'amachine',
    'DB_PASSWORD': 'password',
    'DB_HOST': 'localhost',
    'DB_PORT': '5432'
})

# Crear archivo .env
config = {
    'DB_NAME': 'amachine',
    'DB_USER': 'amachine',
    'DB_PASSWORD': 'password',
    'DB_HOST': 'localhost',
    'DB_PORT': '5432'
}
success, msg = setup.create_env_file(config)

# Ejecutar migraciones
success, msg = setup.run_migrations()

# Crear superuser
success, msg = setup.create_superuser('admin', 'admin@amachine.com', 'admin123')
```

#### Métodos Principales:

- `is_setup_completed()`: Verifica si existe el archivo `.setup_completed`
- `validate_database_connection(db_config)`: Prueba conexión a PostgreSQL
- `generate_secret_key()`: Genera SECRET_KEY segura
- `create_env_file(config)`: Crea archivo .env con backup del existente
- `run_migrations()`: Ejecuta `python manage.py migrate`
- `create_superuser(username, email, password)`: Crea usuario admin
- `setup_sifen_menu()`: Ejecuta comando para crear menús
- `complete_setup(...)`: Proceso completo de setup (pasos 1-2)
- `finalize_setup(admin_config)`: Finalización después del reinicio

### 2. SetupCheckMiddleware (`OptsIO/middleware.py`)

Middleware que redirige a `/setup/` si el sistema no está configurado:

```python
class SetupCheckMiddleware:
    def __init__(self, get_response=None):
        self.setup_manager = SetupManager()
        self.whitelist = [
            '/setup/',
            '/setup/step1/',
            '/setup/step2/',
            '/setup/finalize/',
            '/static/',
            '/media/',
        ]
```

**Funcionamiento**:
- Verifica si existe `.setup_completed`
- Si NO existe, redirige todo el tráfico a `/setup/`
- Excepto URLs en whitelist (setup, static, media)
- Una vez completado, permite acceso normal

### 3. Vistas de Setup (`OptsIO/mng_setup.py`)

Cuatro vistas principales:

1. **setup_index**: Muestra formulario de configuración de BD
2. **setup_validate_database**: Endpoint AJAX para validar conexión
3. **setup_step2**: Procesa formulario y crea .env
4. **setup_finalize**: Ejecuta migraciones y configuración final

### 4. Templates

- **SetupUi.html**: Formulario de configuración de BD (Paso 1)
- **SetupFinalizeUi.html**: Pantalla de finalización con progreso (Paso 3)

## Uso del Sistema

### Primera Instalación

1. **Clonar repositorio e instalar dependencias**
   ```bash
   git clone https://github.com/tu-org/amachine.git
   cd amachine
   pip install -r requirements.txt
   ```

2. **Crear base de datos PostgreSQL**
   ```bash
   sudo -u postgres psql
   CREATE DATABASE amachine;
   CREATE USER amachine WITH PASSWORD 'tu-password';
   GRANT ALL PRIVILEGES ON DATABASE amachine TO amachine;
   \q
   ```

3. **Iniciar servidor Django**
   ```bash
   python manage.py runserver
   ```

4. **Acceder a http://localhost:8000**
   - Automáticamente redirige a `/setup/`

5. **Completar configuración**
   - Paso 1: Ingresar datos de BD y probar conexión
   - Paso 2: Se crea archivo .env
   - **IMPORTANTE**: Reiniciar servidor
     ```bash
     # Detener con Ctrl+C
     python manage.py runserver
     ```
   - Paso 3: Acceder a `/setup/finalize/` y completar

6. **Acceder al sistema**
   - Usuario: admin
   - Contraseña: (la que ingresaste)

### Con Docker

1. **Docker Compose**
   ```bash
   docker compose up -d
   ```

2. **Acceder a http://localhost:8002**
   - Redirige a `/setup/`

3. **Configurar**
   - Host DB: `db` (nombre del servicio en docker-compose)
   - Puerto: `5432`
   - Resto de configuración

4. **Reiniciar container después del paso 2**
   ```bash
   docker compose restart web
   ```

5. **Completar setup en `/setup/finalize/`**

## Archivo .env Generado

Ejemplo de archivo `.env` creado por el sistema:

```bash
# Django Settings
SECRET_KEY=auto-generated-secure-key-50-chars
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database
DB_NAME=amachine
DB_USER=amachine
DB_PASSWORD=tu-password
DB_HOST=localhost
DB_PORT=5432

# Redis
REDIS_HOST=127.0.0.1
REDIS_PORT=6379

# Celery
CELERY_BROKER_URL=redis://127.0.0.1:6379/0
CELERY_RESULT_BACKEND=redis://127.0.0.1:6379/0

# SIFEN
SIFEN_KEY_PASS=cambiar-clave-sifen

# Email (Mailgun API)
MAILGUN_API_KEY=tu-api-key-mailgun
MAILGUN_DOMAIN=tu-dominio-mailgun.com
DEFAULT_FROM_EMAIL=noreply@amachine.com

# Sentry
SENTRY_DSN=

# Domain
FDOMAIN=http://localhost:8000

# CSRF Trusted Origins
CSRF_TRUSTED_ORIGINS=http://localhost:8000,http://127.0.0.1:8000
```

## Reiniciar Setup (Desarrollo)

Si necesitas volver a ejecutar el setup:

```bash
# Eliminar archivo de bandera
rm .setup_completed

# Eliminar .env (opcional)
rm .env

# Reiniciar servidor
python manage.py runserver
```

## Seguridad

1. **Acceso a Setup**: Solo disponible cuando `.setup_completed` NO existe
2. **Backup automático**: Crea `.env.backup` antes de sobrescribir
3. **Validación**: Valida conexión a BD antes de crear archivos
4. **SECRET_KEY**: Genera clave segura de 50 caracteres
5. **Deshabilitación**: Middleware bloquea acceso después de completado

## Troubleshooting

### Error: "El servidor necesita reiniciarse"

**Causa**: Después de crear el .env, Django necesita recargar las variables de entorno.

**Solución**:
- Desarrollo: Detener (Ctrl+C) y ejecutar `python manage.py runserver`
- Docker: `docker compose restart web`

### Error: "Conexión a base de datos fallida"

**Verificar**:
1. PostgreSQL está corriendo: `sudo systemctl status postgresql`
2. Base de datos existe: `psql -U postgres -l`
3. Usuario tiene permisos: `psql -U amachine -d amachine`

### Error: "Módulo psycopg2 no encontrado"

**Solución**:
```bash
pip install psycopg2-binary
```

### Error: "Permission denied al crear .env"

**Verificar**:
- Usuario que ejecuta Django tiene permisos de escritura en el directorio
- En Docker: verificar permisos del volumen

## API Endpoints

### POST /setup/validate-db/
Valida conexión a base de datos sin guardar configuración.

**Request**:
```json
{
    "db_name": "amachine",
    "db_user": "amachine",
    "db_password": "password",
    "db_host": "localhost",
    "db_port": "5432"
}
```

**Response (éxito)**:
```json
{
    "success": true,
    "message": "Conexión exitosa a la base de datos"
}
```

**Response (error)**:
```json
{
    "success": false,
    "message": "Error de conexión: could not connect to server"
}
```

### POST /setup/step2/
Crea archivo .env con configuración completa.

**Form Data**:
- db_name, db_user, db_password, db_host, db_port
- redis_host, redis_port
- fdomain
- admin_username, admin_email, admin_password

**Response**:
```json
{
    "success": true,
    "message": "Configuración guardada. El servidor necesita reiniciarse.",
    "needs_restart": true,
    "next_step": "/setup/finalize/"
}
```

### POST /setup/finalize/
Ejecuta migraciones, registra plugins, carga datos de referencia y crea admin.

**Response**:
```json
{
    "success": true,
    "message": "Datos de referencia cargados. Configure su empresa a continuación.",
    "steps": [
        {"step": "Migraciones", "success": true, "message": "Migraciones ejecutadas exitosamente"},
        {"step": "Registrar Plugins", "success": true, "message": "Plugins registrados: 3 nuevos, 0 actualizados"},
        {"step": "Datos: Tipos de Contribuyente", "success": true, "message": "Tipos de contribuyente cargados"},
        {"step": "Datos: Geografías", "success": true, "message": "Geografías cargadas (2500 registros)"},
        {"step": "Datos: Actividades Económicas", "success": true, "message": "Actividades económicas cargadas"},
        {"step": "Datos: Unidades de Medida", "success": true, "message": "Unidades de medida cargadas"},
        {"step": "Datos: Porcentajes IVA", "success": true, "message": "Porcentajes IVA cargados"},
        {"step": "Datos: Métodos de Pago", "success": true, "message": "Métodos de pago cargados"},
        {"step": "Crear Admin", "success": true, "message": "Superusuario 'admin' creado exitosamente"},
        {"step": "Menús", "success": true, "message": "Menús del sistema creados exitosamente"}
    ],
    "redirect": "/setup/business/"
}
```

### POST /setup/business/
Crea el primer Business y completa el setup.

**Form Data**:
- name, abbr, ruc, ruc_dv, contribuyente
- nombrefactura, nombrefantasia, denominacion, actividad
- direccion, numero_casa, ciudad
- telefono, celular, correo, web

**Response**:
```json
{
    "success": true,
    "message": "Empresa 'Mi Empresa' creada exitosamente",
    "redirect": "/glogin/"
}
```

## Arquitectura

```
Usuario accede a http://localhost:8000
         ↓
SetupCheckMiddleware detecta .setup_completed NO existe
         ↓
Redirige a /setup/
         ↓
[Paso 1] SetupUi.html - Formulario BD
         ↓ (usuario llena formulario)
POST /setup/validate-db/ (AJAX) → Valida conexión
         ↓ (OK)
POST /setup/step2/ → Crea .env
         ↓
Mensaje: "Reiniciar servidor"
         ↓
Usuario reinicia servidor
         ↓
[Paso 3] Usuario accede a /setup/finalize/
         ↓
POST /setup/finalize/ → Migraciones + Plugins + Datos + Admin + Menús
         ↓
Redirige a /setup/business/
         ↓
[Paso 4] SetupBusinessUi.html - Formulario Empresa
         ↓ (usuario llena formulario)
POST /setup/business/ → Crea Business + Activa Plugins Core
         ↓
Crea .setup_completed
         ↓
Redirige a /glogin/
         ↓
Sistema listo para usar
```

---

**Última actualización**: 2026-01-04
**Mantenido por**: Equipo de Desarrollo Amachine
