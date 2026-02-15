#!/bin/bash
# Script de deploy automático para Toca3D
# Uso: ./deploy.sh [--no-build]

set -e  # Salir si hay error

PROJECT_DIR="/var/www/toca3d"
LOG_FILE="/var/log/toca3d-deploy.log"

# Colores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"
}

warn() {
    echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')] WARNING:${NC} $1" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')] ERROR:${NC} $1" | tee -a "$LOG_FILE"
    exit 1
}

# Verificar directorio
cd "$PROJECT_DIR" || error "No se puede acceder a $PROJECT_DIR"

log "=========================================="
log "Iniciando deploy de Toca3D"
log "=========================================="

# Guardar commit actual para rollback
CURRENT_COMMIT=$(git rev-parse HEAD)
log "Commit actual: $CURRENT_COMMIT"

# Pull changes (usando SSH key específica)
log "Descargando cambios de GitHub..."
export GIT_SSH_COMMAND='ssh -i ~/.ssh/id_toca3d -o IdentitiesOnly=yes'
git fetch origin main
git reset --hard origin/main

NEW_COMMIT=$(git rev-parse HEAD)
log "Nuevo commit: $NEW_COMMIT"

if [ "$CURRENT_COMMIT" == "$NEW_COMMIT" ]; then
    warn "No hay cambios nuevos. Continuando de todas formas..."
fi

# Build
if [ "$1" != "--no-build" ]; then
    log "Construyendo imágenes Docker..."
    docker compose build web celery_worker
fi

# Restart containers
log "Reiniciando contenedores..."
docker compose up -d --force-recreate web celery_worker

# Wait for containers to be healthy
log "Esperando que los contenedores estén listos..."
sleep 10

# Run migrations
log "Ejecutando migraciones..."
docker compose exec -T web python manage.py migrate --noinput

# Collect static
log "Recolectando archivos estáticos..."
docker compose exec -T web python manage.py collectstatic --noinput

# Verify
log "Verificando estado de contenedores..."
docker compose ps

# Health check
log "Verificando salud de la aplicación..."
if curl -s -o /dev/null -w "%{http_code}" http://localhost:8002/health/ | grep -q "200"; then
    log "✅ Health check: OK"
else
    warn "Health check falló, pero los contenedores están corriendo"
fi

log "=========================================="
log "✅ Deploy completado exitosamente"
log "=========================================="
