# Amachine ERP

<div align="center">

**Sistema ERP multi-tenant, modular y extensible mediante plugins**

[![Python](https://img.shields.io/badge/Python-3.10+-green.svg)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-5.2+-green.svg)](https://www.djangoproject.com/)

</div>

---

## Descripcion

Amachine es una plataforma ERP (Enterprise Resource Planning) multi-tenant desarrollada en Django. Permite que multiples negocios operen de forma independiente dentro de una misma instancia, con un sistema de plugins que extiende sus funcionalidades segun las necesidades de cada implementacion.

---

## Caracteristicas

- **Multi-Tenant** - Multiples negocios aislados en una sola instancia
- **Sistema de Plugins** - Funcionalidades extensibles sin modificar el core
- **Facturacion Electronica** - Integracion SIFEN (Paraguay) con firma digital y XML
- **Integracion Shopify** - Sincronizacion de productos, ordenes y pagos
- **WebSockets** - Notificaciones en tiempo real via Django Channels
- **Tareas Asincronas** - Procesamiento en segundo plano con Celery
- **Reportes PDF** - Generacion dinamica con diseno personalizado por negocio
- **Setup Autoconfigurable** - Wizard web de 4 pasos, sin editar archivos manualmente
- **Roles y Permisos** - Control granular de acceso por usuario y negocio

---

## Stack Tecnologico

### Backend
- **Django 5.2+** - Framework principal
- **Django Channels 4.0+** - WebSockets
- **Celery 5.3+** - Tareas asincronas
- **Daphne** - Servidor ASGI
- **PostgreSQL 15** - Base de datos
- **Redis** - Cache, broker y channel layer

### Frontend
- **Bootstrap 5** - Layout y componentes
- **jQuery + Axios** - Comunicacion HTTP/AJAX
- **DataTables** - Tablas dinamicas
- **Select2** - Selects avanzados con busqueda
- **SweetAlert2** - Dialogos y alertas
- **Chart.js** - Graficos

---

## Arquitectura

### Multi-Tenant

```
User (Django Auth) → UserProfile → UserBusiness (N:1) → Business
```

Cada operacion queda scoped al negocio activo del usuario.

### Sistema de Plugins

Cada app Django puede registrar un `plugin.py` que define menus, datos de referencia, tareas Celery y pasos de setup.

| Plugin | Categoria | Descripcion |
|--------|-----------|-------------|
| `optsio` | sistema | Core: usuarios, permisos, administracion |
| `sifen` | facturacion | Facturacion electronica SIFEN (Paraguay) |
| `shopify` | integraciones | Sincronizacion con tiendas Shopify |

### Endpoints Principales

| Endpoint | Descripcion |
|----------|-------------|
| `/iom/` | Ejecuta metodos en cualquier modulo segun parametrizacion |
| `/dtmpl/` | Renderiza templates dinamicos con contexto |
| `/api_iom/` | Version API con autenticacion por token |
| `/api_dtmpl/` | Version API de renderizado de templates |

---

## Estructura del Proyecto

```
Amachine/               # Configuracion Django (settings, urls, asgi, celery)
OptsIO/                 # Core: autenticacion, menus, permisos, WebSockets, plugins
Sifen/                  # Facturacion electronica SIFEN (Paraguay)
am_shopify/             # Integracion Shopify
Cobro/                  # Gestion de cobros
templates/              # Templates HTML (BaseUi, Offcanvas, Modals, por app)
static/amui/            # JS custom: a_ui.js, form_ui.js, table_ui.js, a_ws.js
docs/                   # Documentacion adicional
.claude/                # Guias de desarrollo y patrones
```

---

## Instalacion

### 1. Clonar el repositorio

```bash
git clone git@github.com:pjmakey2/amachines.git
cd amachines
```

### 2. Entorno virtual

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Iniciar servicios

```bash
# Redis (si no esta como servicio)
redis-server

# Django
python manage.py runserver

# Celery worker
celery -A Amachine worker -l info
```

### 4. Setup via web

Al acceder por primera vez, el wizard de setup guia la configuracion:

1. **Base de datos** - Configurar conexion PostgreSQL
2. **Variables de entorno** - Genera archivo `.env`
3. **Migraciones** - Ejecuta migraciones y carga datos de referencia
4. **Negocio** - Crea el primer negocio

---

## Deployment con Docker

```bash
docker compose up -d
```

Servicios: `web` (Django + Daphne :8002), `db` (PostgreSQL), `redis`, `celery_worker`.

Ver `DEPLOYMENT_GUIDE.md` y `deployment/README.md` para instrucciones completas.

---

## Variables de Entorno

```env
SECRET_KEY=cambiar-en-produccion
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
DB_NAME=amachine
DB_USER=amachine
DB_PASSWORD=cambiar
DB_HOST=localhost
DB_PORT=5432
REDIS_HOST=127.0.0.1
REDIS_PORT=6379
CELERY_BROKER_URL=redis://localhost:6379/0
SIFEN_KEY_PASS=clave-certificado
SHOPIFY_STORE=tu-tienda.myshopify.com
SHOPIFY_API_ADMIN=shpat_tu_token
```

---

## Documentacion

La carpeta `.claude/` contiene las guias tecnicas del proyecto:

| Archivo | Contenido |
|---------|-----------|
| `context.md` | Guidelines generales de desarrollo |
| `crud_patterm.md` | Patron completo para interfaces CRUD |
| `form_ui.md` | Referencia de formularios y controles |
| `table_ui.md` | Wrapper de DataTables con backend |
| `javascript_methods.md` | Lista completa de metodos JS disponibles |
| `models_reference.md` | Estructura de modelos multi-tenant |
| `plugin_system.md` | Arquitectura de plugins |
| `setup_system.md` | Sistema de setup autoconfigurable |
| `record_from_backend.md` | Patron seModel para consultas |

---

## Desarrollado por

**[Alta Machines](https://altamachines.com)** - Soluciones de software empresarial

Contacto: pjmakey2@gmail.com
