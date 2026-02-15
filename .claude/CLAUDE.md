# Amachine ERP - Documentación del Proyecto

## Descripción General

**Amachine** es un sistema ERP multi-tenant genérico desarrollado en Django, diseñado para que múltiples negocios puedan operar de forma independiente dentro de la misma instancia.

**Desarrollado por:** Alta Machines
**Arquitectura:** Django 5.x + Django Channels (WebSockets) + Celery + PostgreSQL + Redis

---

## Reglas para Claude

1. **Siempre preguntar antes de hacer commit** - No asumir que los cambios están listos para commit. Esperar confirmación explícita del usuario.

2. **Verificar TODOS los archivos modificados antes de /commit o /deploy** - Antes de ejecutar cualquier comando de commit o deploy, SIEMPRE revisar `git status` y `git diff` para ver TODOS los archivos con cambios pendientes. Mostrar al usuario un resumen de cada archivo modificado y preguntar cuáles incluir.

3. **Mostrar siempre el path completo** - Al ejecutar comandos bash, siempre mostrar el path completo donde se ejecutará el comando.

---

## Arquitectura Multi-Tenant

### Modelos Principales

```
User (Django Auth)
    ↓
UserProfile (OptsIO/models.py)
    ↓ (1:N)
UserBusiness (OptsIO/models.py)
    ↓ (N:1)
Business (Sifen/models.py)
```

### Flujo de Usuario

1. **Login** → Signal crea/actualiza `UserProfile`
2. **Sin negocio** → Modal para asignar negocio existente o crear nuevo
3. **Con negocio** → Template tags obtienen datos del negocio activo
4. **Cambiar negocio** → Selector en toolbar permite cambiar negocio activo

### Template Tags Disponibles

| Tag | Descripción | Default |
|-----|-------------|---------|
| `{% business_logo %}` | URL del logo del negocio activo | `amachine_logo.png` |
| `{% business_logo_path %}` | Path del logo (para PDFs) | - |
| `{% business_name %}` | Nombre del negocio | `Alta Machines` |
| `{% business_email %}` | Email del negocio | `info@altamachines.com` |
| `{% business_web %}` | Website del negocio | `https://altamachines.com` |

---

## Sistema de Plugins

Amachine utiliza un sistema de plugins modular que permite extender funcionalidades:

### Plugins Disponibles

| Plugin | Categoría | Core | Descripción |
|--------|-----------|------|-------------|
| `optsio` | sistema | Sí | Core: usuarios, permisos, administración |
| `sifen` | facturación | Sí | Facturación electrónica SIFEN (Paraguay) |
| `shopify` | integraciones | No | Integración con tiendas Shopify |

### Archivos de Plugin

Cada app puede tener un archivo `plugin.py` que define:
- Menús y aplicaciones
- Datos de referencia
- Tareas Celery
- Pasos de setup

### Modelos del Sistema de Plugins

| Modelo | Descripción |
|--------|-------------|
| `Plugin` | Registro de plugins disponibles |
| `BusinessPlugin` | Relación Plugin-Business (multi-tenant) |
| `ReferenceDataLoad` | Registro de datos de referencia cargados |
| `SetupStep` | Pasos de setup ejecutados |

Ver documentación completa: `.claude/plugin_system.md`

---

## Estructura del Proyecto

```
Amachine/                   # Configuración Django
├── settings.py
├── urls.py
├── wsgi.py
├── asgi.py
└── celery.py

OptsIO/                     # Core del sistema
├── models.py               # UserProfile, UserBusiness, Apps, Menu
├── mng_user_profile.py     # Gestión de perfiles y negocios
├── mng_registration.py     # Login, registro, cambio de negocio
├── consumers.py            # WebSocket consumers
├── templatetags/io_tags.py # Template tags (business_*, etc.)
└── signals.py              # Señales (crear profile en login)

Sifen/                      # Facturación Electrónica (Paraguay)
├── models.py               # Business, DocumentHeader, Clientes, etc.
├── mng_sifen.py            # Lógica de facturación
├── ekuatia_gf.py           # Generación de XML SIFEN
├── rq_soap_handler.py      # Comunicación con SIFEN
└── xml_signer.py           # Firma digital de documentos

am_shopify/                 # Integración Shopify
├── models.py               # ShopifyOrder, ShopifyPayment, etc.
├── shopify_client.py       # Cliente API de Shopify
└── mng_shopify.py          # Sincronización y conversión a facturas

templates/                  # Templates HTML
├── BaseUi.html             # Layout principal
├── OptsIO/                 # Login, registro, configuración
├── Sifen/                  # Facturas, notas de crédito, etc.
└── am_shopify/             # Interfaces de Shopify

static/                     # Archivos estáticos
├── amui/                   # CSS y JS del sistema
└── images/                 # Logos e imágenes
```

---

## Apps Django

| App | Descripción |
|-----|-------------|
| `OptsIO` | Core del sistema: autenticación, menús, permisos, WebSockets |
| `Sifen` | Facturación electrónica SIFEN (Paraguay) |
| `am_shopify` | Integración con Shopify |
| `Anime` | App de ejemplo/demo |
| `Finance` | Cálculos financieros |

---

## Configuración Docker

### Servicios

| Servicio | Container | Puerto | Descripción |
|----------|-----------|--------|-------------|
| web | `amachine_web` | 8002 | Django + Daphne (ASGI) |
| db | `amachine_db` | 5432 | PostgreSQL 15 |
| redis | `amachine_redis` | 6379 | Cache + Channels + Celery |
| celery_worker | `amachine_celery_worker` | - | Tareas asíncronas |

### Comandos Docker

```bash
# Iniciar
docker compose up -d

# Ver logs
docker compose logs -f web

# Ejecutar comando Django
docker exec -it amachine_web python manage.py <comando>

# Shell de Django
docker exec -it amachine_web python manage.py shell

# Reiniciar
docker compose down && docker compose up -d
```

---

## Variables de Entorno (.env)

```bash
# Django
SECRET_KEY=cambiar-en-produccion
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database
DB_NAME=amachine
DB_USER=amachine
DB_PASSWORD=cambiar-password
DB_HOST=localhost
DB_PORT=5432

# Redis
REDIS_HOST=127.0.0.1
REDIS_PORT=6379

# Celery
CELERY_BROKER_URL=redis://localhost:6379/0

# SIFEN (Paraguay)
SIFEN_KEY_PASS=clave-certificado

# Email (Mailgun)
MAILGUN_API_KEY=key
MAILGUN_DOMAIN=dominio
DEFAULT_FROM_EMAIL=email@dominio.com

# Domain
FDOMAIN=http://localhost:8000
CSRF_TRUSTED_ORIGINS=http://localhost:8000
```

---

## Deployment

### Archivos de Configuración

| Archivo | Descripción |
|---------|-------------|
| `docker-compose.yml` | Orquestación de servicios |
| `Dockerfile` | Imagen de la aplicación |
| `docker/nginx/amachine.conf` | Configuración Nginx |
| `docker/amachine-docker.service` | Servicio systemd |
| `docker/crontab` | Cron jobs (supercronic) |
| `docker/entrypoint.sh` | Script de inicio |

### Cron Jobs (supercronic)

| Job | Script | Frecuencia | Descripción |
|-----|--------|------------|-------------|
| track_lotes | `mng_sifen_track_lotes.sh` | */5 * | Rastrear lotes SIFEN |
| send_pending | `mng_sifen_send_pending.sh` | */5 * | Enviar documentos pendientes |
| send_email | `mng_sifen_send_email.sh` | */5 * | Enviar emails de facturas |
| sync_shopify | `sync_shopify.sh` | */5 * | Sincronizar Shopify |

---

## Modelo de Negocio (Business)

```python
Business:
    name            # Nombre del negocio
    abbr            # Abreviación
    ruc             # RUC (único)
    ruc_dv          # Dígito verificador
    logo            # Logo del negocio
    correo          # Email de contacto
    web             # Sitio web
    direccion       # Dirección
    ciudadobj       # FK a Ciudades
    contribuyenteobj # FK a TipoContribuyente
    actividadecoobj # FK a ActividadEconomica
```

### Tipos de Contribuyente

| ID | Tipo | pdv_es_contribuyente |
|----|------|---------------------|
| 1 | Física | True |
| 2 | Jurídica | True |
| 3 | No Contribuyente | False |

---

## Facturación SIFEN

### Tipos de Documento

| Código | Tipo |
|--------|------|
| 1 | Factura Electrónica |
| 4 | Autofactura Electrónica |
| 5 | Nota de Crédito Electrónica |
| 6 | Nota de Débito Electrónica |
| 7 | Nota de Remisión Electrónica |

### Estados de Documento

| Estado | Descripción |
|--------|-------------|
| `null` | Pendiente de envío |
| `Aprobado` | Aprobado por SIFEN |
| `Rechazado` | Rechazado por SIFEN |

### Flujo de Facturación

1. Crear documento → `MSifen.create_documentheader()`
2. Generar XML → `ekuatia_gf.py`
3. Firmar XML → `xml_signer.py`
4. Enviar a SIFEN → `rq_soap_handler.py`
5. Procesar respuesta → Actualizar `ek_estado`

---

## Integración Shopify

### Modelos

| Modelo | Descripción |
|--------|-------------|
| `ShopifyCustomer` | Clientes de Shopify |
| `ShopifyProduct` | Productos sincronizados |
| `ShopifyOrder` | Órdenes (todas) |
| `ShopifyPayment` | Pagos para facturar |

### Sincronización

```bash
# Sincronizar todo
docker exec -it amachine_web /app/am_shopify/bin/sync_shopify.sh --all

# Sincronizar específico
--clientes    # Solo clientes
--productos   # Solo productos
--ordenes     # Solo órdenes
--pagos       # Solo pagos
```

### Conversión a Facturas

Los `ShopifyPayment` se convierten a `DocumentHeader` (facturas SIFEN):
- Descuentos por ítem desde `discount_allocations`
- Shipping como línea adicional
- Cliente innominado si no tiene datos

---

## Comandos de Management

```bash
# SIFEN
python manage.py mng_sifen_mainline --track_lotes --date 2024-01-01
python manage.py mng_sifen_mainline --send_pending_docs
python manage.py mng_sifen_mainline --send_email --date 2024-01-01
python manage.py mng_sifen_mainline --classify_clients

# Shopify
python manage.py shopify_sync_mainline --all
python manage.py shopify_sync_mainline --payments

# Sistema
python manage.py setup_sifen_menu  # Crear menús
python manage.py create_amadmin    # Crear usuario admin
```

---

## Archivos Importantes

| Archivo | Descripción |
|---------|-------------|
| `OptsIO/templatetags/io_tags.py` | Template tags del sistema |
| `Sifen/mng_sifen.py` | Lógica principal de facturación |
| `Sifen/ekuatia_gf.py` | Generación de XML SIFEN |
| `am_shopify/mng_shopify.py` | Conversión Shopify → Facturas |
| `am_shopify/shopify_client.py` | Cliente API Shopify |
| `templates/BaseUi.html` | Layout principal con multi-tenant |

---

## Notas de Desarrollo

### Descuentos SIFEN

- **EA002 (dDescItem)**: Descuento particular por ítem (por unidad)
- **EA004 (dDescGloItem)**: Descuento global aplicado a cada ítem
- **F009 (dTotDesc)**: Suma de todos los EA002
- **F008 (dTotDescGlotem)**: Suma de todos los EA004
- **F010 (dPorcDescTotal)**: Solo si hay descuento global (evita error EA004a)
- **F011 (dDescTotal)**: F009 + F008

### Clientes Innominados

Un cliente es **innominado** cuando:
- No tiene RUC (`pdv_ruc` vacío o '0')
- Independiente del nombre

### WebSockets

- Configurados con Django Channels
- Redis como channel layer
- Consumer en `OptsIO/consumers.py`
- Routing en `OptsIO/routing.py`
