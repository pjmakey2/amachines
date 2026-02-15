# Guía de Despliegue - Toca3D

Esta guía describe el proceso completo para desplegar Toca3D en un servidor Digital Ocean usando Docker Compose.

## 📋 Información del Servidor

- **IP**: 167.99.145.70
- **Dominio**: toca3d.altamachines.com
- **Usuario**: am
- **Sistema Operativo**: Ubuntu/Debian
- **Puerto Aplicación**: 8002

## 🏗️ Arquitectura del Despliegue

```
[Internet]
    ↓
[Nginx (443/80)]
    ├── HTTPS/WSS Proxy → [Docker: Web (Daphne:8002)]
    ├── Static Files     → /var/www/toca3d/staticfiles/
    └── Media Files      → /var/www/toca3d/media/

[Docker Compose]
├── web (Daphne + Django Channels) - Puerto 8002
├── celery_worker (Async Tasks)
├── redis (Broker + Channel Layer)
└── db (PostgreSQL 15)
```

### Componentes:

1. **Nginx**: Reverse proxy con soporte SSL/TLS y WebSocket
2. **Daphne**: Servidor ASGI para Django Channels (WebSocket)
3. **Django 5.2+**: Framework de la aplicación
4. **Celery Worker**: Procesamiento de tareas asíncronas (sin Beat)
5. **Redis**: Broker para Celery y capa de canales
6. **PostgreSQL 15**: Base de datos principal

## 🚀 Pre-requisitos

Antes de comenzar, asegúrate de tener:

1. Acceso SSH al servidor como usuario `am`
2. Permisos sudo configurados para el usuario `am`
3. DNS configurado apuntando toca3d.altamachines.com a 167.99.145.70
4. Repositorio clonado o accesible vía Git
5. Archivo `.env` configurado con las credenciales correctas

## 📝 Proceso de Despliegue

### Paso 1: Instalar Docker y Docker Compose

```bash
cd /home/am
# Copiar scripts de deployment a tu home o temp
./deployment/01_install_docker.sh
```

**⚠️ IMPORTANTE**: Después de este script, debes **cerrar sesión y volver a iniciarla** para que los cambios en el grupo docker surtan efecto.

```bash
# Verificar instalación
docker --version
docker compose version
```

### Paso 2: Configurar Directorios

```bash
./deployment/02_setup_directories.sh
```

Este script crea:
- `/var/www/toca3d` - Directorio principal de la aplicación
- `/var/www/toca3d/staticfiles` - Archivos estáticos de Django
- `/var/www/toca3d/media` - Archivos subidos por usuarios
- `/var/log/toca3d` - Logs de la aplicación

### Paso 3: Clonar Proyecto y Configurar

```bash
./deployment/03_clone_and_setup_project.sh
```

**⚠️ IMPORTANTE**: Después de ejecutar este script, debes editar el archivo `.env`:

```bash
nano /var/www/toca3d/.env
```

Configura los siguientes valores críticos:

```env
# Django
SECRET_KEY=tu-clave-secreta-muy-larga-y-aleatoria
DEBUG=False
ALLOWED_HOSTS=toca3d.altamachines.com,167.99.145.70

# Base de datos
DB_NAME=toca3d
DB_USER=toca3d_user
DB_PASSWORD=tu-password-segura-aqui
DB_HOST=db
DB_PORT=5432

# Redis
REDIS_HOST=redis
REDIS_PORT=6379

# Celery
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0

# Email (si aplica)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=tu-email@gmail.com
EMAIL_HOST_PASSWORD=tu-app-password

# SIFEN (Sistema de Facturación Electrónica Paraguay)
SIFEN_API_URL=https://sifen.set.gov.py/
SIFEN_CLIENT_ID=tu-client-id
SIFEN_CLIENT_SECRET=tu-client-secret
```

### Paso 4: Generar Certificado SSL

```bash
./deployment/04_generate_ssl_certificate.sh
```

Este script:
- Instala certbot si no está presente
- Genera certificado Let's Encrypt para toca3d.altamachines.com
- Configura renovación automática

**Nota**: El certificado se renovará automáticamente vía `certbot.timer`.

### Paso 5: Configurar Nginx

```bash
./deployment/05_configure_nginx.sh
```

Este script:
- Instala Nginx
- Copia la configuración con soporte WebSocket
- Habilita el sitio
- Verifica la configuración
- Recarga Nginx

### Paso 6: Construir e Iniciar Contenedores

```bash
cd /var/www/toca3d
./deployment/06_build_and_start.sh
```

Este script:
- Construye las imágenes Docker
- Inicia todos los contenedores
- Ejecuta migraciones de base de datos
- Recolecta archivos estáticos
- Crea superusuario si no existe

**Tiempo estimado**: 5-10 minutos (primera vez)

### Paso 7: Configurar Servicio Systemd

```bash
./deployment/07_setup_systemd.sh
```

Este script:
- Instala el servicio systemd para Docker Compose
- Habilita inicio automático en el arranque del servidor
- Inicia el servicio

### Paso 8: Verificar Despliegue

```bash
./deployment/08_verify_deployment.sh
```

Este script verifica:
- ✓ Servicios del sistema (Docker, Nginx, toca3d-docker)
- ✓ Contenedores Docker corriendo
- ✓ Certificado SSL válido
- ✓ Conectividad de red
- ✓ Configuración de WebSocket
- ✓ Logs sin errores críticos
- ✓ Uso de recursos

## 🔍 Verificación Manual

### 1. Verificar Contenedores

```bash
cd /var/www/toca3d
docker compose ps
```

Deberías ver 4 contenedores en estado "Up":
- toca3d-web-1
- toca3d-celery_worker-1
- toca3d-redis-1
- toca3d-db-1

### 2. Verificar Logs

```bash
# Logs de todos los servicios
docker compose logs -f

# Solo web
docker compose logs -f web

# Solo celery
docker compose logs -f celery_worker
```

### 3. Verificar Nginx

```bash
sudo systemctl status nginx
sudo nginx -t
```

### 4. Verificar Acceso HTTPS

```bash
curl -I https://toca3d.altamachines.com
```

Deberías recibir un código 200 OK.

### 5. Verificar WebSocket

Abre la consola del navegador en https://toca3d.altamachines.com y ejecuta:

```javascript
const ws = new WebSocket('wss://toca3d.altamachines.com/ws/test/');
ws.onopen = () => console.log('WebSocket connected!');
ws.onerror = (error) => console.error('WebSocket error:', error);
```

## 🛠️ Comandos Útiles

### Gestión de Contenedores

```bash
cd /var/www/toca3d

# Ver logs en tiempo real
docker compose logs -f

# Reiniciar servicios
docker compose restart

# Detener servicios
docker compose down

# Reconstruir y reiniciar
docker compose up -d --build

# Ver uso de recursos
docker stats

# Entrar a un contenedor
docker compose exec web bash
docker compose exec db psql -U toca3d_user -d toca3d
```

### Gestión del Servicio Systemd

```bash
# Estado del servicio
sudo systemctl status toca3d-docker

# Iniciar/detener/reiniciar
sudo systemctl start toca3d-docker
sudo systemctl stop toca3d-docker
sudo systemctl restart toca3d-docker

# Ver logs del servicio
sudo journalctl -u toca3d-docker -f
```

### Django Management Commands

```bash
cd /var/www/toca3d

# Ejecutar migraciones
docker compose exec web python manage.py migrate

# Recolectar estáticos
docker compose exec web python manage.py collectstatic --noinput

# Crear superusuario
docker compose exec web python manage.py createsuperuser

# Shell de Django
docker compose exec web python manage.py shell

# Cualquier comando de manage.py
docker compose exec web python manage.py <comando>
```

### Gestión de Base de Datos

```bash
# Acceder a PostgreSQL
docker compose exec db psql -U toca3d_user -d toca3d

# Backup de base de datos
docker compose exec db pg_dump -U toca3d_user toca3d > backup_$(date +%Y%m%d).sql

# Restaurar backup
docker compose exec -T db psql -U toca3d_user -d toca3d < backup_20241124.sql
```

### Logs

```bash
# Logs de Nginx
sudo tail -f /var/log/nginx/toca3d_access.log
sudo tail -f /var/log/nginx/toca3d_error.log

# Logs de aplicación
docker compose logs -f web --tail=100

# Logs de Celery
docker compose logs -f celery_worker --tail=100
```

## 🔄 Actualizar la Aplicación

Cuando necesites actualizar el código:

```bash
cd /var/www/toca3d

# 1. Obtener últimos cambios
git pull origin main

# 2. Reconstruir contenedores
docker compose up -d --build

# 3. Ejecutar migraciones (si hay)
docker compose exec web python manage.py migrate

# 4. Recolectar estáticos (si cambiaron)
docker compose exec web python manage.py collectstatic --noinput

# 5. Verificar logs
docker compose logs -f web
```

## 🐛 Troubleshooting

### Problema: Contenedores no inician

```bash
# Ver logs detallados
docker compose logs

# Verificar que el .env está configurado
cat .env

# Verificar puertos en uso
sudo netstat -tlnp | grep :8002
sudo netstat -tlnp | grep :5432
sudo netstat -tlnp | grep :6379
```

### Problema: Error de base de datos

```bash
# Ver logs de PostgreSQL
docker compose logs db

# Verificar que la BD está lista
docker compose exec db pg_isready -U toca3d_user

# Recrear base de datos (⚠️ DESTRUYE DATOS)
docker compose down -v
docker compose up -d
```

### Problema: WebSocket no funciona

```bash
# Verificar configuración de Nginx
sudo nginx -T | grep -A 20 "location /ws/"

# Verificar headers de WebSocket
curl -i -N -H "Connection: Upgrade" -H "Upgrade: websocket" \
  https://toca3d.altamachines.com/ws/test/

# Ver logs de Daphne
docker compose logs -f web | grep -i websocket
```

### Problema: Certificado SSL expirado

```bash
# Verificar expiración
sudo certbot certificates

# Renovar manualmente
sudo certbot renew

# Verificar renovación automática
sudo systemctl status certbot.timer
```

### Problema: Archivos estáticos no se sirven

```bash
# Verificar permisos
ls -la /var/www/toca3d/staticfiles/

# Recolectar estáticos nuevamente
docker compose exec web python manage.py collectstatic --noinput --clear

# Verificar configuración de Nginx
sudo nginx -T | grep -A 5 "location /static/"
```

### Problema: Alto uso de memoria

```bash
# Ver uso de recursos
docker stats

# Reiniciar contenedores uno por uno
docker compose restart celery_worker
docker compose restart web

# Limpiar imágenes antiguas
docker system prune -a
```

## 🔐 Seguridad

### Recomendaciones:

1. **Firewall**: Configura UFW para permitir solo puertos necesarios
```bash
sudo ufw allow 22/tcp   # SSH
sudo ufw allow 80/tcp   # HTTP (redirect a HTTPS)
sudo ufw allow 443/tcp  # HTTPS
sudo ufw enable
```

2. **Actualizar regularmente**:
```bash
sudo apt update && sudo apt upgrade -y
```

3. **Monitorear logs**:
```bash
# Buscar intentos de acceso no autorizado
sudo tail -f /var/log/nginx/toca3d_access.log | grep -i "401\|403"
```

4. **Backups automáticos**: Configura backups diarios de la base de datos

5. **Cambiar contraseñas por defecto**: Asegúrate de cambiar todas las contraseñas en `.env`

## 📊 Monitoreo

### Health Checks

```bash
# Verificar que todos los servicios están vivos
curl https://toca3d.altamachines.com/health/  # Si tienes endpoint de health

# Verificar uso de disco
df -h

# Verificar memoria
free -h

# Verificar procesos Docker
docker compose ps
```

## 📞 Soporte

En caso de problemas:

1. Revisa los logs: `docker compose logs -f`
2. Verifica la configuración: `cat .env`
3. Consulta esta guía de troubleshooting
4. Revisa la documentación del proyecto en `.claude/`

## 📄 Archivos Importantes

- `/var/www/toca3d/.env` - Variables de entorno
- `/etc/nginx/sites-available/toca3d` - Configuración Nginx
- `/etc/letsencrypt/live/toca3d.altamachines.com/` - Certificados SSL
- `/var/www/toca3d/docker-compose.yml` - Orquestación de contenedores
- `/etc/systemd/system/toca3d-docker.service` - Servicio systemd

## ✅ Checklist de Despliegue

- [ ] Ejecutar script 01 - Instalar Docker
- [ ] Cerrar sesión y volver a iniciarla
- [ ] Ejecutar script 02 - Configurar directorios
- [ ] Ejecutar script 03 - Clonar proyecto
- [ ] Editar archivo `.env` con credenciales reales
- [ ] Ejecutar script 04 - Generar certificado SSL
- [ ] Ejecutar script 05 - Configurar Nginx
- [ ] Ejecutar script 06 - Construir e iniciar contenedores
- [ ] Ejecutar script 07 - Configurar systemd
- [ ] Ejecutar script 08 - Verificar despliegue
- [ ] Acceder a https://toca3d.altamachines.com
- [ ] Verificar WebSocket funciona
- [ ] Crear primer usuario/negocio
- [ ] Configurar backups automáticos

## 🎉 ¡Listo!

Una vez completados todos los pasos, tu aplicación Toca3D estará corriendo en:

**https://toca3d.altamachines.com**

Con soporte completo para:
- ✅ HTTPS con certificado válido
- ✅ WebSocket para comunicación en tiempo real
- ✅ Procesamiento asíncrono con Celery
- ✅ Persistencia de datos con PostgreSQL
- ✅ Archivos estáticos y media servidos eficientemente
- ✅ Inicio automático en boot del servidor
- ✅ Logs centralizados y fáciles de consultar
