# Scripts de Despliegue - Toca3D

Esta carpeta contiene los scripts necesarios para desplegar Toca3D en un servidor de producción.

## 📋 Orden de Ejecución

Ejecuta los scripts en este orden:

### 1️⃣ Instalar Docker
```bash
./01_install_docker.sh
```
⚠️ **Importante**: Después de este script, cierra sesión y vuelve a iniciarla.

### 2️⃣ Configurar Directorios
```bash
./02_setup_directories.sh
```

### 3️⃣ Clonar y Configurar Proyecto
```bash
./03_clone_and_setup_project.sh
```
⚠️ **Importante**: Después de este script, edita el archivo `/var/www/toca3d/.env` con tus credenciales.

### 4️⃣ Generar Certificado SSL
```bash
./04_generate_ssl_certificate.sh
```

### 5️⃣ Configurar Nginx
```bash
./05_configure_nginx.sh
```

### 6️⃣ Construir e Iniciar Contenedores
```bash
cd /var/www/toca3d
./deployment/06_build_and_start.sh
```

### 7️⃣ Configurar Servicio Systemd
```bash
./07_setup_systemd.sh
```

### 8️⃣ Verificar Despliegue
```bash
./08_verify_deployment.sh
```

## 📝 Descripción de Scripts

| Script | Descripción |
|--------|-------------|
| `01_install_docker.sh` | Instala Docker Engine y Docker Compose plugin |
| `02_setup_directories.sh` | Crea estructura de directorios en `/var/www/toca3d` |
| `03_clone_and_setup_project.sh` | Clona repositorio y crea archivo `.env` |
| `04_generate_ssl_certificate.sh` | Genera certificado SSL con Let's Encrypt |
| `05_configure_nginx.sh` | Configura Nginx como reverse proxy con WebSocket |
| `06_build_and_start.sh` | Construye imágenes Docker e inicia contenedores |
| `07_setup_systemd.sh` | Configura servicio systemd para auto-inicio |
| `08_verify_deployment.sh` | Verifica que todo está funcionando correctamente |

## 🎯 Ejecución Rápida

Si ya tienes todo configurado y solo quieres ejecutar todos los scripts:

```bash
# ⚠️ ADVERTENCIA: Solo usa esto si sabes lo que haces
./01_install_docker.sh && \
echo "⚠️ Cierra sesión y vuelve a ejecutar el resto manualmente" && \
exit
```

Después de volver a iniciar sesión:

```bash
./02_setup_directories.sh && \
./03_clone_and_setup_project.sh && \
echo "⚠️ Edita /var/www/toca3d/.env antes de continuar" && \
read -p "Presiona ENTER cuando hayas configurado el .env..."

./04_generate_ssl_certificate.sh && \
./05_configure_nginx.sh && \
cd /var/www/toca3d && \
./deployment/06_build_and_start.sh && \
./deployment/07_setup_systemd.sh && \
./deployment/08_verify_deployment.sh
```

## 🔧 Pre-requisitos

Antes de ejecutar los scripts:

- [x] Usuario `am` con permisos sudo
- [x] Acceso SSH al servidor
- [x] DNS configurado: `toca3d.altamachines.com` → `167.99.145.70`
- [x] Puerto 80 y 443 abiertos en el firewall
- [x] Acceso al repositorio Git

## 📚 Documentación Completa

Para instrucciones detalladas, troubleshooting y comandos útiles, consulta:

**[DEPLOYMENT_GUIDE.md](../DEPLOYMENT_GUIDE.md)**

## 🐛 Troubleshooting Rápido

### Problema: Script falla con "Permission denied"

```bash
chmod +x deployment/*.sh
```

### Problema: Docker no está disponible después del script 01

```bash
# Cierra sesión y vuelve a iniciarla
exit
# Vuelve a conectarte por SSH
ssh am@167.99.145.70
```

### Problema: Certificado SSL no se genera

```bash
# Verifica DNS
nslookup toca3d.altamachines.com

# Verifica que los puertos están abiertos
sudo netstat -tlnp | grep :80
sudo netstat -tlnp | grep :443
```

### Problema: Contenedores no inician

```bash
cd /var/www/toca3d
# Verifica el archivo .env
cat .env

# Ver logs
docker compose logs
```

## ⚠️ Notas Importantes

1. **Edición del .env**: El script 03 crea un `.env` desde `.env.example`. Debes editarlo con valores reales antes de continuar con el script 06.

2. **Reinicio de sesión**: Después del script 01, es **obligatorio** cerrar sesión y volver a iniciarla para que el usuario `am` pueda usar Docker sin sudo.

3. **DNS**: Asegúrate de que el DNS está propagado antes de ejecutar el script 04 (certificado SSL).

4. **Backups**: Estos scripts NO configuran backups automáticos. Configúralos manualmente después del despliegue.

## 🎉 Resultado Final

Una vez completados todos los scripts, tendrás:

- ✅ Aplicación corriendo en https://toca3d.altamachines.com
- ✅ 4 contenedores Docker (web, celery, redis, postgresql)
- ✅ Nginx configurado con SSL/TLS y WebSocket
- ✅ Servicio systemd para auto-inicio
- ✅ Certificado SSL con renovación automática

## 📞 Soporte

Si encuentras problemas:

1. Revisa los logs de cada script
2. Consulta [DEPLOYMENT_GUIDE.md](../DEPLOYMENT_GUIDE.md)
3. Verifica los logs de Docker: `docker compose logs -f`
4. Verifica los logs de Nginx: `sudo tail -f /var/log/nginx/toca3d_error.log`
