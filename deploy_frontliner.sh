#!/bin/bash
# =============================================================================
# deploy_frontliner.sh
# Instala y configura el sistema Frontliner en un droplet Debian 12 desde cero.
# Se ejecuta desde la máquina local — conecta al droplet vía SSH.
#
# Uso:
#   chmod +x deploy_frontliner.sh
#   ./deploy_frontliner.sh
# =============================================================================
set -euo pipefail

# =============================================================================
# CONFIGURACION
# =============================================================================
DROPLET_IP="143.110.238.24"
DROPLET_USER="am"
SSH_OPTS="-o StrictHostKeyChecking=accept-new"

LOCAL_PROJECT="/home/peter/projects/frontlinerSistema"
LOCAL_DUMP=$(ls -t /home/peter/projects/Amachine/dumps/frontlin_db_prod_*.sql.bz2 /home/peter/projects/Amachine/dumps/frontlin_db_prod_*.sql 2>/dev/null | grep -v '_old_' | head -1)

REMOTE_PROJECT="/var/www/frontliner"
REMOTE_DUMP="/tmp/frontlin_db.sql"

DB_NAME="frontlin_db"
DB_USER="mainline"
DB_PASS="mainline"

APACHE_PORT="80"
VHOST_CONF="/etc/apache2/sites-available/frontliner.conf"

# =============================================================================
# HELPERS
# =============================================================================
info()  { echo -e "\n\033[1;34m[INFO]\033[0m  $*"; }
ok()    { echo -e "\033[1;32m[OK]\033[0m    $*"; }
error() { echo -e "\033[1;31m[ERROR]\033[0m $*"; exit 1; }

run_remote() {
    ssh $SSH_OPTS "${DROPLET_USER}@${DROPLET_IP}" sudo bash -s <<EOF
$1
EOF
}

# =============================================================================
# VERIFICACIONES PREVIAS
# =============================================================================
info "Verificando prerequisitos locales..."

[ -d "$LOCAL_PROJECT" ] || error "No se encuentra el proyecto en $LOCAL_PROJECT"
[ -n "$LOCAL_DUMP" ]    || error "No se encontró ningún dump en /home/peter/projects/Amachine/dumps/"

ok "Proyecto: $LOCAL_PROJECT"
ok "Dump:     $LOCAL_DUMP ($(du -sh "$LOCAL_DUMP" | cut -f1))"

info "Verificando conectividad con el droplet..."
ssh $SSH_OPTS "${DROPLET_USER}@${DROPLET_IP}" "echo ok" > /dev/null || error "No se puede conectar a ${DROPLET_IP}"
ok "Conexión SSH OK"

# =============================================================================
# PASO 1: INSTALACION DE DEPENDENCIAS EN EL DROPLET
# =============================================================================
info "Instalando dependencias en el droplet (Apache, PHP 7.4, MariaDB)..."

run_remote "
set -e

# Evitar prompts interactivos
export DEBIAN_FRONTEND=noninteractive

# Agregar repo de PHP 7.4 (sury.org)
apt-get install -y -q lsb-release apt-transport-https ca-certificates curl 2>/dev/null
curl -sSL https://packages.sury.org/php/apt.gpg -o /usr/share/keyrings/sury-php.gpg
echo \"deb [signed-by=/usr/share/keyrings/sury-php.gpg] https://packages.sury.org/php/ \$(lsb_release -sc) main\" > /etc/apt/sources.list.d/sury-php.list
apt-get update -q

# Instalar Apache
apt-get install -y -q apache2

# Instalar PHP 7.4 con extensiones necesarias
apt-get install -y -q \
    php7.4 \
    libapache2-mod-php7.4 \
    php7.4-mysql \
    php7.4-mbstring \
    php7.4-curl \
    php7.4-gd \
    php7.4-xml \
    php7.4-zip \
    php7.4-intl \
    php7.4-json

# Asegurarse que mod_php7.4 esté activo
a2dismod php8.4 2>/dev/null || true
a2enmod php7.4

# Instalar MariaDB
apt-get install -y -q mariadb-server

echo 'DEPENDENCIAS OK'
"
ok "Dependencias instaladas"

# =============================================================================
# PASO 2: CONFIGURAR MARIADB
# =============================================================================
info "Configurando base de datos..."

ssh $SSH_OPTS "${DROPLET_USER}@${DROPLET_IP}" sudo mysql <<SQL
CREATE DATABASE IF NOT EXISTS \`${DB_NAME}\` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER IF NOT EXISTS '${DB_USER}'@'localhost' IDENTIFIED BY '${DB_PASS}';
GRANT ALL PRIVILEGES ON \`${DB_NAME}\`.* TO '${DB_USER}'@'localhost';
FLUSH PRIVILEGES;
SQL
ok "Base de datos configurada: ${DB_NAME} / ${DB_USER}"

# =============================================================================
# PASO 3: COPIAR EL PROYECTO
# =============================================================================
info "Copiando proyecto al droplet (puede tardar unos minutos)..."

ssh $SSH_OPTS "${DROPLET_USER}@${DROPLET_IP}" "sudo mkdir -p ${REMOTE_PROJECT} && sudo chown ${DROPLET_USER}:${DROPLET_USER} ${REMOTE_PROJECT}"

rsync -az --progress \
    --exclude='*.backup.*' \
    --exclude='.git' \
    --exclude='uploads/*' \
    -e "ssh $SSH_OPTS" \
    "${LOCAL_PROJECT}/" \
    "${DROPLET_USER}@${DROPLET_IP}:${REMOTE_PROJECT}/"

ssh $SSH_OPTS "${DROPLET_USER}@${DROPLET_IP}" "sudo chown -R www-data:www-data ${REMOTE_PROJECT} && sudo chmod -R 755 ${REMOTE_PROJECT}"

ok "Proyecto copiado a ${REMOTE_PROJECT}"

# =============================================================================
# PASO 4: ACTUALIZAR CONFIGURACION PHP (BD y rutas del droplet)
# =============================================================================
info "Actualizando Configuracion.php para el droplet..."

ssh $SSH_OPTS "${DROPLET_USER}@${DROPLET_IP}" "sudo sed -i \
    -e \"s|'bdServidor'.*|'bdServidor'            ] = 'localhost';|\" \
    -e \"s|'bdUsuarioBaseDatos'.*|'bdUsuarioBaseDatos'    ] = '${DB_USER}';|\" \
    -e \"s|'bdContraseniaUsuario'.*|'bdContraseniaUsuario'  ] = '${DB_PASS}';|\" \
    -e \"s|'bdNombreBaseDatos'.*|'bdNombreBaseDatos'     ] = '${DB_NAME}';|\" \
    -e \"s|'rutaDirectorioCargaArchivos'.*|'rutaDirectorioCargaArchivos'] = '${REMOTE_PROJECT}/uploads';|\" \
    ${REMOTE_PROJECT}/Sistema/PHP/Configuracion.php"

ssh $SSH_OPTS "${DROPLET_USER}@${DROPLET_IP}" "sudo mkdir -p ${REMOTE_PROJECT}/uploads && sudo chown www-data:www-data ${REMOTE_PROJECT}/uploads"

ok "Configuracion.php actualizado"

# =============================================================================
# PASO 5: CONFIGURAR APACHE
# =============================================================================
info "Configurando Apache..."

# Crear VirtualHost evitando heredoc anidado
ssh $SSH_OPTS "${DROPLET_USER}@${DROPLET_IP}" sudo tee "${VHOST_CONF}" > /dev/null <<VHOST
<VirtualHost *:${APACHE_PORT}>
    ServerName ${DROPLET_IP}
    DocumentRoot ${REMOTE_PROJECT}

    php_value auto_prepend_file ${REMOTE_PROJECT}/mysql_compat.php

    <Directory ${REMOTE_PROJECT}>
        Options Indexes FollowSymLinks
        AllowOverride All
        Require all granted
    </Directory>

    ErrorLog \${APACHE_LOG_DIR}/frontliner-error.log
    CustomLog \${APACHE_LOG_DIR}/frontliner-access.log combined
</VirtualHost>
VHOST

run_remote "
set -e
sed -i '/^Listen 80$/d' /etc/apache2/ports.conf 2>/dev/null || true
grep -q 'Listen ${APACHE_PORT}' /etc/apache2/ports.conf || echo 'Listen ${APACHE_PORT}' >> /etc/apache2/ports.conf
a2dissite 000-default 2>/dev/null || true
a2ensite frontliner
a2enmod rewrite
systemctl enable apache2
systemctl restart apache2
echo 'APACHE OK'
"
ok "Apache configurado en puerto ${APACHE_PORT}"

# =============================================================================
# PASO 6: COPIAR E IMPORTAR EL DUMP
# =============================================================================
DUMP_SIZE=$(du -sh "$LOCAL_DUMP" | cut -f1)
info "Copiando dump al droplet ($DUMP_SIZE)..."
scp $SSH_OPTS "$LOCAL_DUMP" "${DROPLET_USER}@${DROPLET_IP}:${REMOTE_DUMP}"
ok "Dump copiado"

info "Importando dump en MariaDB..."
if [[ "$LOCAL_DUMP" == *.bz2 ]]; then
    ssh $SSH_OPTS "${DROPLET_USER}@${DROPLET_IP}" "bzcat ${REMOTE_DUMP} | sudo mysql -u ${DB_USER} -p${DB_PASS} ${DB_NAME} && sudo rm -f ${REMOTE_DUMP} && echo 'IMPORT OK'"
else
    ssh $SSH_OPTS "${DROPLET_USER}@${DROPLET_IP}" "sudo mysql -u ${DB_USER} -p${DB_PASS} ${DB_NAME} < ${REMOTE_DUMP} && sudo rm -f ${REMOTE_DUMP} && echo 'IMPORT OK'"
fi
ok "Dump importado"

# =============================================================================
# PASO 7: USUARIO DE PRUEBA
# =============================================================================
info "Creando usuario de prueba 999991..."
ssh $SSH_OPTS "${DROPLET_USER}@${DROPLET_IP}" sudo mysql -u ${DB_USER} -p${DB_PASS} ${DB_NAME} <<SQL
INSERT INTO usuarios
    (funcionariocodigo, funcionarionombre, funcionarioapellido, funcionarioci,
     funcionariocorreo, funcionariotel, funcionariocelular, funcionariodireccion,
     ciudad, sucursal, funcionariofecharegistro, codigorol, funcionarioestado,
     funcionariopassword, fechaultactualizacion, codoficina, cargocodigo, tipopanel)
VALUES
    (999991, 'ADMINISTRADOR', 'DEL SISTEMA', '999991',
     'dooslines@gmail.com', '', '', '',
     1, 0, '2015-01-15', 1, 1,
     MD5('..uno3..'), CURDATE(), 0, 1, 0)
ON DUPLICATE KEY UPDATE funcionariopassword = MD5('..uno3..'), funcionarioestado = 1;
SQL
ok "Usuario 999991 listo"

# =============================================================================
# PASO 8: VERIFICACION FINAL
# =============================================================================
info "Verificando instalación..."

HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "http://${DROPLET_IP}:${APACHE_PORT}/")
if [ "$HTTP_CODE" = "200" ]; then
    ok "HTTP $HTTP_CODE — el sistema responde correctamente"
else
    echo -e "\033[1;33m[WARN]\033[0m  HTTP $HTTP_CODE — revisá los logs en el droplet"
fi

echo ""
echo "============================================================"
echo "  INSTALACION COMPLETADA"
echo "  URL: http://${DROPLET_IP}:${APACHE_PORT}/"
echo "  Usuario de prueba: 999991 / ..uno3.."
echo "============================================================"
