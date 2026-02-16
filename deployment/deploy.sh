#!/bin/bash
# =============================================================================
# Amachine ERP - Deploy Script
# =============================================================================
# Deploy nativo o Docker a servidor remoto.
#
# Ejemplo:
#   ./deploy.sh --server 165.227.53.87 --user am --branch develop \
#               --dominio fl.altamachines.com --virtualenv Amachine \
#               --env /home/peter/projects/Amachine/.env_fl \
#               --bind_port_gunicorn 8010 --prefix_services_names fl_am \
#               --bind_port_nginx 8000
# =============================================================================

set -euo pipefail

# ─── Colores ─────────────────────────────────────────────────────────────────
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'
BOLD='\033[1m'

log()   { echo -e "${GREEN}[✓]${NC} $1"; }
warn()  { echo -e "${YELLOW}[!]${NC} $1"; }
error() { echo -e "${RED}[✗]${NC} $1"; exit 1; }
info()  { echo -e "${BLUE}[→]${NC} $1"; }
header(){ echo -e "\n${CYAN}${BOLD}═══ $1 ═══${NC}\n"; }

# ─── Valores por defecto ─────────────────────────────────────────────────────
SERVER=""
USER=""
BRANCH="main"
DOCKER=false
DOMINIO=""
VIRTUALENV=""
PYTHON_VERSION="3.13.0"
ENV_FILE=""
BIND_PORT_GUNICORN=8010
BIND_PORT_NGINX=""
PREFIX_SERVICES="altamachines"
MIGRATIONS=false
GITHUB_ACTION=""

# Derivados del proyecto local
LOCAL_PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PROJECT_NAME="$(basename "$LOCAL_PROJECT_DIR")"

# ─── Parse argumentos ────────────────────────────────────────────────────────
while [[ $# -gt 0 ]]; do
    case $1 in
        --server)               SERVER="$2"; shift 2 ;;
        --user)                 USER="$2"; shift 2 ;;
        --branch)               BRANCH="$2"; shift 2 ;;
        --docker)               DOCKER=true; shift ;;
        --dominio)              DOMINIO="$2"; shift 2 ;;
        --virtualenv)
            VIRTUALENV="$2"; shift
            # Si el siguiente arg parece versión python (X.Y.Z), consumirlo
            if [[ $# -gt 1 && "$2" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
                PYTHON_VERSION="$2"; shift
            fi
            shift ;;
        --env)                  ENV_FILE="$2"; shift 2 ;;
        --bind_port_gunicorn)   BIND_PORT_GUNICORN="$2"; shift 2 ;;
        --bind_port_nginx)      BIND_PORT_NGINX="$2"; shift 2 ;;
        --prefix_services_names) PREFIX_SERVICES="$2"; shift 2 ;;
        --migrations)           MIGRATIONS=true; shift ;;
        --github_action)        GITHUB_ACTION="$2"; shift 2 ;;
        -h|--help)
            echo "Uso: deploy.sh --server <IP> --user <USER> --branch <BRANCH> [opciones]"
            echo ""
            echo "Opciones:"
            echo "  --server <IP>                  Servidor destino (requerido)"
            echo "  --user <USER>                  Usuario SSH (requerido)"
            echo "  --branch <BRANCH>              Branch a deployar (default: main)"
            echo "  --docker                       Deploy con Docker (default: nativo)"
            echo "  --dominio <DOMAIN>             Dominio para Let's Encrypt"
            echo "  --virtualenv <NAME> [VERSION]  Virtualenv pyenv (default python: 3.13.0)"
            echo "  --env <PATH>                   Archivo .env local a subir"
            echo "  --bind_port_gunicorn <PORT>    Puerto gunicorn (default: 8010)"
            echo "  --bind_port_nginx <PORT>       Puerto nginx listen"
            echo "  --prefix_services_names <NAME> Prefijo servicios systemd (default: altamachines)"
            echo "  --migrations                   Ejecutar makemigrations + migrate"
            echo "  --github_action <ACTION>       Nombre del GitHub Action a ejecutar"
            exit 0 ;;
        *) error "Opción desconocida: $1. Use --help" ;;
    esac
done

# ─── Validaciones ────────────────────────────────────────────────────────────
[[ -z "$SERVER" ]] && error "Debe especificar --server <IP>"
[[ -z "$USER" ]]   && error "Debe especificar --user <USER>"

# Rutas remotas derivadas de la estructura local
REMOTE_HOME="/home/$USER"
REMOTE_PROJECT_DIR="$REMOTE_HOME/projects/$PROJECT_NAME"

# ─── SSH helper ──────────────────────────────────────────────────────────────
SSH_OPTS="-o StrictHostKeyChecking=accept-new -o ServerAliveInterval=30 -o ServerAliveCountMax=10"

ssh_run() {
    ssh $SSH_OPTS "$USER@$SERVER" "$@"
}

ssh_sudo() {
    ssh $SSH_OPTS "$USER@$SERVER" "sudo bash -c '$*'"
}

# ─── Mostrar configuración ──────────────────────────────────────────────────
header "Amachine ERP - Deploy"
echo "  Servidor:     $USER@$SERVER"
echo "  Branch:       $BRANCH"
echo "  Modo:         $([ "$DOCKER" = true ] && echo 'Docker' || echo 'Nativo')"
echo "  Proyecto:     $REMOTE_PROJECT_DIR"
echo "  Gunicorn:     :$BIND_PORT_GUNICORN"
echo "  Servicios:    ${PREFIX_SERVICES}_*.service"
[[ -n "$DOMINIO" ]]    && echo "  Dominio:      $DOMINIO"
[[ -n "$VIRTUALENV" ]] && echo "  Virtualenv:   $VIRTUALENV (Python $PYTHON_VERSION)"
[[ -n "$ENV_FILE" ]]   && echo "  .env:         $ENV_FILE"
[[ -n "$BIND_PORT_NGINX" ]] && echo "  Nginx:        :$BIND_PORT_NGINX"
echo ""

# ─── GitHub Action mode ─────────────────────────────────────────────────────
if [[ -n "$GITHUB_ACTION" ]]; then
    info "Modo GitHub Action: $GITHUB_ACTION"
    info "Este script debe ejecutarse desde el workflow de GitHub Actions."
    info "Las variables --server, --user, --branch se pasan como inputs del workflow."
    exit 0
fi

# ─── Verificar conectividad ─────────────────────────────────────────────────
header "1. Verificando conectividad"
ssh_run "echo 'Conectado a \$(hostname) - \$(cat /etc/os-release | grep PRETTY_NAME | cut -d= -f2)'" \
    || error "No se puede conectar a $SERVER"
log "Conectividad OK"

# =============================================================================
# 2. INSTALAR DEPENDENCIAS DEL SISTEMA
# =============================================================================
header "2. Instalando dependencias del sistema"

# Verificar si ya están instalados los paquetes clave
NEEDS_APT=$(ssh_run '
    MISSING=0
    for pkg in nginx postgresql redis-server libpango-1.0-0 libpq-dev; do
        dpkg -s "$pkg" >/dev/null 2>&1 || MISSING=1
    done
    echo $MISSING
')

if [[ "$NEEDS_APT" == "1" ]]; then
    ssh_run 'sudo apt-get update -qq' || true

    info "Instalando paquetes base..."
    ssh_run 'sudo apt-get install -y -qq \
        build-essential curl git wget unzip \
        libssl-dev zlib1g-dev libbz2-dev libreadline-dev libsqlite3-dev \
        libncursesw5-dev xz-utils tk-dev libxml2-dev libxmlsec1-dev \
        libffi-dev liblzma-dev \
        libpq-dev libmariadb-dev \
        libpango-1.0-0 libpangoft2-1.0-0 libpangocairo-1.0-0 \
        libgdk-pixbuf-2.0-0 libcairo2 libgirepository1.0-dev \
        gir1.2-pango-1.0 \
        nginx certbot python3-certbot-nginx \
        postgresql postgresql-contrib \
        redis-server memcached \
        supervisor \
        2>&1 | tail -3'
    log "Paquetes base instalados"

    info "Habilitando servicios..."
    ssh_run 'sudo systemctl enable --now postgresql redis-server memcached nginx 2>/dev/null || true'
    log "Servicios habilitados"
else
    log "Dependencias del sistema ya instaladas (skip)"
fi

# =============================================================================
# 3. INSTALAR PYENV + PYTHON + VIRTUALENV
# =============================================================================
if [[ -n "$VIRTUALENV" ]]; then
    header "3. Configurando pyenv + Python $PYTHON_VERSION"

    # Instalar pyenv si no existe
    info "Verificando pyenv..."
    ssh_run "
        if [ ! -d \"\$HOME/.pyenv\" ]; then
            echo 'Instalando pyenv...'
            curl -fsSL https://pyenv.run | bash

            # Agregar al perfil
            echo '' >> \$HOME/.bashrc
            echo 'export PYENV_ROOT=\"\$HOME/.pyenv\"' >> \$HOME/.bashrc
            echo 'export PATH=\"\$PYENV_ROOT/bin:\$PATH\"' >> \$HOME/.bashrc
            echo 'eval \"\$(pyenv init -)\"' >> \$HOME/.bashrc
            echo 'eval \"\$(pyenv virtualenv-init -)\"' >> \$HOME/.bashrc
        fi

        export PYENV_ROOT=\"\$HOME/.pyenv\"
        export PATH=\"\$PYENV_ROOT/bin:\$PATH\"
        eval \"\$(pyenv init -)\"
        eval \"\$(pyenv virtualenv-init -)\" 2>/dev/null || true

        echo \"pyenv version: \$(pyenv --version)\"
    "
    log "pyenv listo"

    # Instalar Python
    info "Instalando Python $PYTHON_VERSION (puede tardar)..."
    ssh_run "
        export PYENV_ROOT=\"\$HOME/.pyenv\"
        export PATH=\"\$PYENV_ROOT/bin:\$PATH\"
        eval \"\$(pyenv init -)\"

        if ! pyenv versions | grep -q '$PYTHON_VERSION'; then
            pyenv install '$PYTHON_VERSION'
        fi
        echo 'Python $PYTHON_VERSION disponible'
    "
    log "Python $PYTHON_VERSION instalado"

    # Crear virtualenv
    info "Creando virtualenv '$VIRTUALENV'..."
    ssh_run "
        export PYENV_ROOT=\"\$HOME/.pyenv\"
        export PATH=\"\$PYENV_ROOT/bin:\$PATH\"
        eval \"\$(pyenv init -)\"
        eval \"\$(pyenv virtualenv-init -)\" 2>/dev/null || true

        if ! pyenv versions | grep -q '$VIRTUALENV'; then
            pyenv virtualenv '$PYTHON_VERSION' '$VIRTUALENV'
        fi
        echo 'Virtualenv $VIRTUALENV listo'
    "
    log "Virtualenv '$VIRTUALENV' creado"
fi

# =============================================================================
# 4. PREPARAR DIRECTORIO DEL PROYECTO
# =============================================================================
header "4. Preparando directorio del proyecto"

info "Creando estructura de directorios..."
ssh_run "mkdir -p '$REMOTE_PROJECT_DIR'"

# Verificar si el repo ya está cloneado
info "Verificando repositorio git..."
REPO_URL=$(git -C "$LOCAL_PROJECT_DIR" remote get-url origin 2>/dev/null || echo "")

if [[ -z "$REPO_URL" ]]; then
    error "No se encontró remote origin en el proyecto local"
fi

ssh_run "
    if [ -d '$REMOTE_PROJECT_DIR/.git' ]; then
        echo 'Repositorio ya existe, actualizando...'
        cd '$REMOTE_PROJECT_DIR'
        git fetch --all
    else
        # Si el directorio existe pero no es un repo git, preservar archivos clave y clonar
        if [ -d '$REMOTE_PROJECT_DIR' ] && [ ! -d '$REMOTE_PROJECT_DIR/.git' ]; then
            echo 'Directorio existe pero no es repo git, reubicando archivos...'
            # Preservar .env y .python-version si existen
            [ -f '$REMOTE_PROJECT_DIR/.env' ] && cp '$REMOTE_PROJECT_DIR/.env' /tmp/_deploy_env_backup
            [ -f '$REMOTE_PROJECT_DIR/.python-version' ] && cp '$REMOTE_PROJECT_DIR/.python-version' /tmp/_deploy_pyver_backup
            rm -rf '$REMOTE_PROJECT_DIR'
        fi

        echo 'Clonando repositorio...'
        git clone '$REPO_URL' '$REMOTE_PROJECT_DIR'
        cd '$REMOTE_PROJECT_DIR'

        # Restaurar archivos preservados
        [ -f /tmp/_deploy_env_backup ] && mv /tmp/_deploy_env_backup '$REMOTE_PROJECT_DIR/.env'
        [ -f /tmp/_deploy_pyver_backup ] && mv /tmp/_deploy_pyver_backup '$REMOTE_PROJECT_DIR/.python-version'
    fi

    cd '$REMOTE_PROJECT_DIR'
    git checkout '$BRANCH' 2>/dev/null || git checkout -b '$BRANCH' origin/'$BRANCH'
    git pull origin '$BRANCH'
    echo \"Branch: \$(git branch --show-current)\"
    echo \"Commit: \$(git log --oneline -1)\"
"
log "Repositorio actualizado en branch '$BRANCH'"

# Configurar .python-version para autoswitch
if [[ -n "$VIRTUALENV" ]]; then
    info "Configurando .python-version..."
    ssh_run "echo '$VIRTUALENV' > '$REMOTE_PROJECT_DIR/.python-version'"
    log ".python-version configurado"
fi

# =============================================================================
# 5. SUBIR ARCHIVO .env
# =============================================================================
if [[ -n "$ENV_FILE" ]]; then
    header "5. Subiendo archivo .env"

    if [[ ! -f "$ENV_FILE" ]]; then
        error "Archivo .env no encontrado: $ENV_FILE"
    fi

    scp $SSH_OPTS "$ENV_FILE" "$USER@$SERVER:$REMOTE_PROJECT_DIR/.env"
    log ".env subido a $REMOTE_PROJECT_DIR/.env"
else
    header "5. Archivo .env"
    warn "No se especificó --env. Verificando si existe en el servidor..."
    ssh_run "[ -f '$REMOTE_PROJECT_DIR/.env' ] && echo '.env existe' || echo 'WARNING: No hay .env en el servidor'"
fi

# =============================================================================
# 6. INSTALAR DEPENDENCIAS PYTHON
# =============================================================================
header "6. Instalando dependencias Python"

ssh_run "
    export PYENV_ROOT=\"\$HOME/.pyenv\"
    export PATH=\"\$PYENV_ROOT/bin:\$PATH\"
    eval \"\$(pyenv init -)\"
    eval \"\$(pyenv virtualenv-init -)\" 2>/dev/null || true

    cd '$REMOTE_PROJECT_DIR'

    # Activar virtualenv
    pyenv activate '$VIRTUALENV' 2>/dev/null || true

    echo \"Python: \$(python --version)\"
    echo \"Pip: \$(pip --version)\"

    pip install --upgrade pip -q
    pip install -r requirements.txt 2>&1 | tail -10
    pip install gunicorn flower -q

    echo ''
    echo 'Paquetes instalados: '
    pip list --format=columns 2>/dev/null | wc -l
"
log "Dependencias Python instaladas"

# =============================================================================
# 7. CONFIGURAR BASE DE DATOS POSTGRESQL
# =============================================================================
header "7. Configurando PostgreSQL"

# Leer variables del .env si existe
if [[ -n "$ENV_FILE" && -f "$ENV_FILE" ]]; then
    DB_NAME=$(grep '^DB_NAME=' "$ENV_FILE" | cut -d= -f2 | tr -d "'\"" || echo "amachine")
    DB_USER=$(grep '^DB_USER=' "$ENV_FILE" | cut -d= -f2 | tr -d "'\"" || echo "amachine")
    DB_PASSWORD=$(grep '^DB_PASSWORD=' "$ENV_FILE" | cut -d= -f2 | tr -d "'\"" || echo "amachine")
else
    DB_NAME="amachine"
    DB_USER="amachine"
    DB_PASSWORD="amachine"
    warn "Sin .env - usando valores por defecto para PostgreSQL"
fi

info "Configurando BD: $DB_NAME / usuario: $DB_USER"
ssh_run "
    sudo -u postgres psql -tc \"SELECT 1 FROM pg_roles WHERE rolname='$DB_USER'\" | grep -q 1 || \
        sudo -u postgres psql -c \"CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';\"

    sudo -u postgres psql -tc \"SELECT 1 FROM pg_database WHERE datname='$DB_NAME'\" | grep -q 1 || \
        sudo -u postgres psql -c \"CREATE DATABASE $DB_NAME OWNER $DB_USER;\"

    sudo -u postgres psql -c \"GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;\"
    echo 'PostgreSQL configurado'
"
log "PostgreSQL: BD '$DB_NAME' y usuario '$DB_USER' listos"

# =============================================================================
# 8. MIGRACIONES
# =============================================================================
if [[ "$MIGRATIONS" = true ]]; then
    header "8. Ejecutando migraciones"

    ssh_run "
        export PYENV_ROOT=\"\$HOME/.pyenv\"
        export PATH=\"\$PYENV_ROOT/bin:\$PATH\"
        eval \"\$(pyenv init -)\"
        eval \"\$(pyenv virtualenv-init -)\" 2>/dev/null || true

        cd '$REMOTE_PROJECT_DIR'
        pyenv activate '$VIRTUALENV' 2>/dev/null || true

        python manage.py makemigrations 2>&1
        python manage.py migrate 2>&1
        python manage.py collectstatic --noinput 2>&1 | tail -3
    "
    log "Migraciones completadas"
else
    header "8. Migraciones"
    warn "Omitido (use --migrations para ejecutar)"
fi

# =============================================================================
# 9. CREAR SERVICIOS SYSTEMD
# =============================================================================
header "9. Configurando servicios systemd"

# Rutas para los servicios
PYENV_PYTHON="$REMOTE_HOME/.pyenv/versions/$VIRTUALENV/bin/python"
PYENV_GUNICORN="$REMOTE_HOME/.pyenv/versions/$VIRTUALENV/bin/gunicorn"
PYENV_CELERY="$REMOTE_HOME/.pyenv/versions/$VIRTUALENV/bin/celery"
PYENV_FLOWER="$REMOTE_HOME/.pyenv/versions/$VIRTUALENV/bin/flower"
PYENV_DAPHNE="$REMOTE_HOME/.pyenv/versions/$VIRTUALENV/bin/daphne"

# Calcular workers: (2 * CPU) + 1
CPU_COUNT=$(ssh_run "nproc")
GUNICORN_WORKERS=$(( (CPU_COUNT * 2) + 1 ))
DAPHNE_PORT=$((BIND_PORT_GUNICORN + 1))
info "CPU: $CPU_COUNT cores → Gunicorn workers: $GUNICORN_WORKERS"

# Crear directorio de logs
ssh_run "mkdir -p '$REMOTE_PROJECT_DIR/log'"

# Flag para saber si algún servicio cambió
SERVICES_CHANGED=false

# Helper: escribe servicio solo si cambió
write_service() {
    local SVC_NAME="$1"
    local SVC_CONTENT="$2"
    local SVC_PATH="/etc/systemd/system/${SVC_NAME}.service"

    # Comparar contenido actual con el nuevo
    local CHANGED
    CHANGED=$(ssh_run "
        NEW_MD5=\$(echo '$SVC_CONTENT' | md5sum | cut -d' ' -f1)
        if [ -f '$SVC_PATH' ]; then
            OLD_MD5=\$(sudo md5sum '$SVC_PATH' | cut -d' ' -f1)
            [ \"\$NEW_MD5\" != \"\$OLD_MD5\" ] && echo 'changed' || echo 'same'
        else
            echo 'changed'
        fi
    ")

    if [[ "$CHANGED" == "changed" ]]; then
        ssh_run "echo '$SVC_CONTENT' | sudo tee '$SVC_PATH' > /dev/null"
        log "${SVC_NAME}.service actualizado"
        SERVICES_CHANGED=true
    else
        log "${SVC_NAME}.service sin cambios (skip)"
    fi
}

# --- Gunicorn service ---
GUNICORN_SVC="[Unit]
Description=${PREFIX_SERVICES} - Gunicorn (Amachine ERP)
After=network.target postgresql.service redis-server.service

[Service]
Type=notify
User=${USER}
Group=${USER}
WorkingDirectory=${REMOTE_PROJECT_DIR}
Environment=PYENV_ROOT=${REMOTE_HOME}/.pyenv
Environment=PATH=${REMOTE_HOME}/.pyenv/versions/${VIRTUALENV}/bin:${REMOTE_HOME}/.pyenv/bin:/usr/local/bin:/usr/bin:/bin
EnvironmentFile=${REMOTE_PROJECT_DIR}/.env
ExecStart=${PYENV_GUNICORN} Amachine.wsgi:application --bind 127.0.0.1:${BIND_PORT_GUNICORN} --workers ${GUNICORN_WORKERS} --timeout 120 --access-logfile ${REMOTE_PROJECT_DIR}/log/gunicorn_access.log --error-logfile ${REMOTE_PROJECT_DIR}/log/gunicorn_error.log
ExecReload=/bin/kill -s HUP \$MAINPID
Restart=on-failure
RestartSec=5
KillMode=mixed

[Install]
WantedBy=multi-user.target"

write_service "${PREFIX_SERVICES}" "$GUNICORN_SVC"

# --- Celery service ---
CELERY_SVC="[Unit]
Description=${PREFIX_SERVICES} - Celery Worker (Amachine ERP)
After=network.target redis-server.service

[Service]
Type=forking
User=${USER}
Group=${USER}
WorkingDirectory=${REMOTE_PROJECT_DIR}
Environment=PYENV_ROOT=${REMOTE_HOME}/.pyenv
Environment=PATH=${REMOTE_HOME}/.pyenv/versions/${VIRTUALENV}/bin:${REMOTE_HOME}/.pyenv/bin:/usr/local/bin:/usr/bin:/bin
EnvironmentFile=${REMOTE_PROJECT_DIR}/.env
ExecStart=${PYENV_CELERY} -A Amachine multi start worker1 --pidfile=${REMOTE_PROJECT_DIR}/log/celery_%%n.pid --logfile=${REMOTE_PROJECT_DIR}/log/celery_%%n.log --loglevel=info --concurrency=2 --max-tasks-per-child=1000
ExecStop=${PYENV_CELERY} -A Amachine multi stopwait worker1 --pidfile=${REMOTE_PROJECT_DIR}/log/celery_%%n.pid
ExecReload=${PYENV_CELERY} -A Amachine multi restart worker1 --pidfile=${REMOTE_PROJECT_DIR}/log/celery_%%n.pid --logfile=${REMOTE_PROJECT_DIR}/log/celery_%%n.log --loglevel=info --concurrency=2
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target"

write_service "${PREFIX_SERVICES}_celery" "$CELERY_SVC"

# --- Flower service ---
FLOWER_SVC="[Unit]
Description=${PREFIX_SERVICES} - Celery Flower (Amachine ERP)
After=network.target ${PREFIX_SERVICES}_celery.service

[Service]
Type=simple
User=${USER}
Group=${USER}
WorkingDirectory=${REMOTE_PROJECT_DIR}
Environment=PYENV_ROOT=${REMOTE_HOME}/.pyenv
Environment=PATH=${REMOTE_HOME}/.pyenv/versions/${VIRTUALENV}/bin:${REMOTE_HOME}/.pyenv/bin:/usr/local/bin:/usr/bin:/bin
EnvironmentFile=${REMOTE_PROJECT_DIR}/.env
ExecStart=${PYENV_CELERY} -A Amachine flower --port=5555 --broker_api=redis://127.0.0.1:6379/0 --basic_auth=admin:admin
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target"

write_service "${PREFIX_SERVICES}_flower" "$FLOWER_SVC"

# --- Daphne service (WebSockets) ---
DAPHNE_SVC="[Unit]
Description=${PREFIX_SERVICES} - Daphne WebSocket (Amachine ERP)
After=network.target redis-server.service

[Service]
Type=simple
User=${USER}
Group=${USER}
WorkingDirectory=${REMOTE_PROJECT_DIR}
Environment=PYENV_ROOT=${REMOTE_HOME}/.pyenv
Environment=PATH=${REMOTE_HOME}/.pyenv/versions/${VIRTUALENV}/bin:${REMOTE_HOME}/.pyenv/bin:/usr/local/bin:/usr/bin:/bin
EnvironmentFile=${REMOTE_PROJECT_DIR}/.env
ExecStart=${PYENV_DAPHNE} -b 127.0.0.1 -p ${DAPHNE_PORT} Amachine.asgi:application
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target"

write_service "${PREFIX_SERVICES}_daphne" "$DAPHNE_SVC"

if [[ "$SERVICES_CHANGED" == "true" ]]; then
    ssh_run "sudo systemctl daemon-reload"
    log "systemd daemon recargado"
fi

# =============================================================================
# 10. CONFIGURAR NGINX
# =============================================================================
header "10. Configurando Nginx"

# Puerto de escucha de nginx (default: 8000 si se especificó, sino 80)
NGINX_PORT="${BIND_PORT_NGINX:-80}"
NGINX_SERVER_NAME="${DOMINIO:-_}"
NGINX_CHANGED=false

# Bloque de locations compartido (reutilizado en el server block principal)
NGINX_LOCATIONS="
    client_max_body_size 20M;

    location /static/ {
        alias ${REMOTE_PROJECT_DIR}/staticfiles/;
        expires 30d;
        add_header Cache-Control \"public, immutable\";
    }

    location /media/ {
        alias ${REMOTE_PROJECT_DIR}/media/;
        expires 7d;
    }

    location /ws/ {
        proxy_pass http://${PREFIX_SERVICES}_daphne;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \\\$http_upgrade;
        proxy_set_header Connection \"upgrade\";
        proxy_set_header Host \\\$host;
        proxy_set_header X-Real-IP \\\$remote_addr;
        proxy_set_header X-Forwarded-For \\\$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \\\$scheme;
        proxy_read_timeout 86400;
    }

    location /flower/ {
        proxy_pass http://127.0.0.1:5555/;
        proxy_set_header Host \\\$host;
        proxy_set_header X-Real-IP \\\$remote_addr;
        proxy_set_header X-Forwarded-For \\\$proxy_add_x_forwarded_for;
        proxy_redirect off;
    }

    location / {
        proxy_pass http://${PREFIX_SERVICES}_gunicorn;
        proxy_set_header Host \\\$host;
        proxy_set_header X-Real-IP \\\$remote_addr;
        proxy_set_header X-Forwarded-For \\\$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \\\$scheme;
        proxy_read_timeout 120;
    }"

# Construir config según si hay dominio (SSL) o no
if [[ -n "$DOMINIO" ]]; then
    # Con dominio: nginx escucha en NGINX_PORT con SSL + puerto 80 para redirect/certbot
    NGINX_CONF="upstream ${PREFIX_SERVICES}_gunicorn {
    server 127.0.0.1:${BIND_PORT_GUNICORN};
}

upstream ${PREFIX_SERVICES}_daphne {
    server 127.0.0.1:${DAPHNE_PORT};
}

server {
    listen ${NGINX_PORT} ssl;
    server_name ${NGINX_SERVER_NAME};

    ssl_certificate /etc/letsencrypt/live/${DOMINIO}/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/${DOMINIO}/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;
${NGINX_LOCATIONS}
}

# Puerto 80: renovación certbot + redirect a HTTPS
server {
    listen 80;
    server_name ${NGINX_SERVER_NAME};
    return 301 https://\\\$host:${NGINX_PORT}\\\$request_uri;
}"
else
    # Sin dominio: nginx escucha en NGINX_PORT sin SSL
    NGINX_CONF="upstream ${PREFIX_SERVICES}_gunicorn {
    server 127.0.0.1:${BIND_PORT_GUNICORN};
}

upstream ${PREFIX_SERVICES}_daphne {
    server 127.0.0.1:${DAPHNE_PORT};
}

server {
    listen ${NGINX_PORT};
    server_name ${NGINX_SERVER_NAME};
${NGINX_LOCATIONS}
}"
fi

# Verificar si la config de nginx cambió
NGINX_CHECK=$(ssh_run "
    NGINX_PATH='/etc/nginx/sites-available/${PREFIX_SERVICES}'
    if [ -f \"\$NGINX_PATH\" ]; then
        CURRENT_MD5=\$(md5sum \"\$NGINX_PATH\" | cut -d' ' -f1)
        NEW_MD5=\$(echo '$NGINX_CONF' | md5sum | cut -d' ' -f1)
        if [ \"\$CURRENT_MD5\" = \"\$NEW_MD5\" ]; then
            echo 'unchanged'
        else
            echo 'changed'
        fi
    else
        echo 'missing'
    fi
")

if [[ "$NGINX_CHECK" == "missing" || "$NGINX_CHECK" == "changed" ]]; then
    info "Creando/actualizando configuración nginx para ${NGINX_SERVER_NAME}..."
    ssh_run "echo '$NGINX_CONF' | sudo tee /etc/nginx/sites-available/${PREFIX_SERVICES} > /dev/null"
    ssh_run "
        sudo ln -sf /etc/nginx/sites-available/${PREFIX_SERVICES} /etc/nginx/sites-enabled/${PREFIX_SERVICES}
        sudo rm -f /etc/nginx/sites-enabled/default 2>/dev/null || true
        sudo nginx -t
    "
    NGINX_CHANGED=true
    log "Nginx configurado"
else
    log "Nginx sin cambios (skip)"
fi

# =============================================================================
# 11. CERTIFICADO SSL (Let's Encrypt)
# =============================================================================
if [[ -n "$DOMINIO" ]]; then
    header "11. Configurando SSL con Let's Encrypt"

    # Verificar si ya existe un certificado válido para el dominio
    CERT_EXISTS=$(ssh_run "
        if sudo certbot certificates 2>/dev/null | grep -q '$DOMINIO'; then
            echo 'exists'
        else
            echo 'missing'
        fi
    ")

    if [[ "$CERT_EXISTS" == "missing" ]]; then
        info "Solicitando certificado para $DOMINIO..."

        # Certbot necesita puerto 80 para validación HTTP-01.
        # Crear config temporal en puerto 80 para obtener el certificado.
        ssh_run "
            echo 'server { listen 80; server_name $DOMINIO; location / { return 200; } }' \
                | sudo tee /etc/nginx/sites-available/${PREFIX_SERVICES}_certbot > /dev/null
            sudo ln -sf /etc/nginx/sites-available/${PREFIX_SERVICES}_certbot /etc/nginx/sites-enabled/${PREFIX_SERVICES}_certbot
            sudo nginx -t && sudo systemctl reload nginx
        "

        # Obtener certificado (certonly, sin modificar nginx)
        ssh_run "
            sudo certbot certonly --nginx -d '$DOMINIO' --non-interactive --agree-tos \
                --email admin@altamachines.com 2>&1 || \
            echo 'WARN: Certbot falló. Verificar DNS y puerto 80.'
        "

        # Limpiar config temporal de certbot
        ssh_run "
            sudo rm -f /etc/nginx/sites-available/${PREFIX_SERVICES}_certbot
            sudo rm -f /etc/nginx/sites-enabled/${PREFIX_SERVICES}_certbot
        "

        log "Certificado SSL obtenido"
    else
        log "Certificado SSL para $DOMINIO ya existe (skip)"
    fi

    # Reescribir nginx config con SSL en el puerto correcto
    # (La config del paso 10 ya incluye SSL si hay dominio,
    # pero si el cert se acaba de generar, recargar nginx)
    ssh_run "sudo nginx -t && sudo systemctl reload nginx"
    log "Nginx recargado con SSL en puerto $NGINX_PORT"
else
    header "11. SSL"
    warn "Omitido: no se especificó --dominio"
fi

# =============================================================================
# 12. LEVANTAR SERVICIOS
# =============================================================================
header "12. Levantando servicios"

ssh_run "
    # Habilitar servicios si no lo están
    for svc in ${PREFIX_SERVICES} ${PREFIX_SERVICES}_celery ${PREFIX_SERVICES}_flower ${PREFIX_SERVICES}_daphne; do
        sudo systemctl is-enabled \$svc >/dev/null 2>&1 || sudo systemctl enable \$svc 2>/dev/null
    done

    # Siempre reiniciar servicios de app (hay código nuevo del git pull)
    for svc in ${PREFIX_SERVICES} ${PREFIX_SERVICES}_celery ${PREFIX_SERVICES}_flower ${PREFIX_SERVICES}_daphne; do
        sudo systemctl restart \$svc
        echo \"  \$svc: \$(sudo systemctl is-active \$svc)\"
    done

    # Nginx: reload solo si cambió config, sino verificar que esté activo
    if [ '${NGINX_CHANGED}' = 'true' ]; then
        sudo systemctl reload nginx
        echo '  nginx: reloaded'
    else
        sudo systemctl is-active nginx >/dev/null 2>&1 && echo '  nginx: running (sin cambios)' || sudo systemctl start nginx
    fi
"
log "Servicios levantados"

# =============================================================================
# 13. VERIFICACIÓN FINAL
# =============================================================================
header "13. Verificación final"

ssh_run "
    echo '─── Servicios ───'
    for svc in ${PREFIX_SERVICES} ${PREFIX_SERVICES}_celery ${PREFIX_SERVICES}_flower ${PREFIX_SERVICES}_daphne nginx redis-server postgresql; do
        STATUS=\$(sudo systemctl is-active \$svc 2>/dev/null || echo 'not found')
        if [ \"\$STATUS\" = 'active' ]; then
            echo \"  ✓ \$svc: \$STATUS\"
        else
            echo \"  ✗ \$svc: \$STATUS\"
        fi
    done

    echo ''
    echo '─── Puertos ───'
    sudo ss -tlnp | grep -E ':${BIND_PORT_GUNICORN}|:${DAPHNE_PORT}|:5555|:80|:443' || true

    echo ''
    echo '─── Proyecto ───'
    cd '$REMOTE_PROJECT_DIR'
    echo \"  Path:   \$(pwd)\"
    echo \"  Branch: \$(git branch --show-current)\"
    echo \"  Commit: \$(git log --oneline -1)\"
    echo \"  .env:   \$([ -f .env ] && echo 'presente' || echo 'FALTA')\"
"

# Resumen final
echo ""
header "Deploy completado"
echo "  Servidor:    $USER@$SERVER"
echo "  Proyecto:    $REMOTE_PROJECT_DIR"
echo "  Branch:      $BRANCH"
echo "  Gunicorn:    127.0.0.1:$BIND_PORT_GUNICORN"
echo "  Daphne:      127.0.0.1:$DAPHNE_PORT"
echo "  Flower:      127.0.0.1:5555"
[[ -n "$DOMINIO" ]] && echo "  URL:         https://$DOMINIO"
echo ""
echo "  Servicios systemd:"
echo "    sudo systemctl status ${PREFIX_SERVICES}"
echo "    sudo systemctl status ${PREFIX_SERVICES}_celery"
echo "    sudo systemctl status ${PREFIX_SERVICES}_flower"
echo "    sudo systemctl status ${PREFIX_SERVICES}_daphne"
echo ""
