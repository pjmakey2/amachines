#!/bin/bash
# Script de sincronización de Shopify
# Uso: ./sync_shopify.sh [opciones]
#
# Opciones:
#   --clientes      Sincronizar clientes
#   --productos     Sincronizar productos
#   --ordenes       Sincronizar órdenes
#   --pagos         Sincronizar pagos
#   --all           Sincronizar todo
#   --fecha-desde   Fecha desde (YYYY-MM-DD) - Default: 14 días atrás
#   --fecha-hasta   Fecha hasta (YYYY-MM-DD) - Default: hoy
#   --limit         Límite de registros (default: 250)

# Directorio del proyecto
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$(dirname "$SCRIPT_DIR")")"
LOG_DIR="${PROJECT_DIR}/log"

# Crear directorio de logs si no existe
mkdir -p "$LOG_DIR"

# Log file
LOG_FILE="${LOG_DIR}/sync_shopify.log"

# Fechas por defecto
FECHA_HASTA=$(date +%Y-%m-%d)
FECHA_DESDE=$(date -d "-14 days" +%Y-%m-%d)
LIMIT=250

# Opciones de sincronización
SYNC_CLIENTES=false
SYNC_PRODUCTOS=false
SYNC_ORDENES=false
SYNC_PAGOS=false

# Parsear argumentos
while [[ $# -gt 0 ]]; do
    case $1 in
        --clientes)
            SYNC_CLIENTES=true
            shift
            ;;
        --productos)
            SYNC_PRODUCTOS=true
            shift
            ;;
        --ordenes)
            SYNC_ORDENES=true
            shift
            ;;
        --pagos)
            SYNC_PAGOS=true
            shift
            ;;
        --all)
            SYNC_CLIENTES=true
            SYNC_PRODUCTOS=true
            SYNC_ORDENES=true
            SYNC_PAGOS=true
            shift
            ;;
        --fecha-desde)
            FECHA_DESDE="$2"
            shift 2
            ;;
        --fecha-hasta)
            FECHA_HASTA="$2"
            shift 2
            ;;
        --limit)
            LIMIT="$2"
            shift 2
            ;;
        -h|--help)
            echo "Uso: $0 [opciones]"
            echo ""
            echo "Opciones:"
            echo "  --clientes      Sincronizar clientes de Shopify"
            echo "  --productos     Sincronizar productos de Shopify"
            echo "  --ordenes       Sincronizar órdenes de Shopify"
            echo "  --pagos         Sincronizar pagos de Shopify"
            echo "  --all           Sincronizar todo"
            echo "  --fecha-desde   Fecha desde (YYYY-MM-DD) - Default: 14 días atrás"
            echo "  --fecha-hasta   Fecha hasta (YYYY-MM-DD) - Default: hoy"
            echo "  --limit N       Límite de registros (default: 250)"
            echo "  -h, --help      Mostrar esta ayuda"
            exit 0
            ;;
        *)
            echo "Opción desconocida: $1"
            exit 1
            ;;
    esac
done

# Si no se especificó ninguna opción, mostrar ayuda
if [[ "$SYNC_CLIENTES" == "false" && "$SYNC_PRODUCTOS" == "false" && "$SYNC_ORDENES" == "false" && "$SYNC_PAGOS" == "false" ]]; then
    echo "Error: Debe especificar al menos una opción de sincronización."
    echo "Use --help para ver las opciones disponibles."
    exit 1
fi

# Función de log
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Ir al directorio del proyecto
cd "$PROJECT_DIR" || exit 1

log "=========================================="
log "Iniciando sincronización de Shopify"
log "Fecha desde: $FECHA_DESDE"
log "Fecha hasta: $FECHA_HASTA"
log "Límite: $LIMIT"
log "=========================================="

# Sincronizar clientes
if [[ "$SYNC_CLIENTES" == "true" ]]; then
    log "Sincronizando clientes..."
    python manage.py shopify_sync_mainline --clientes --limit "$LIMIT" --fecha-desde "$FECHA_DESDE" --fecha-hasta "$FECHA_HASTA" 2>&1 | tee -a "$LOG_FILE"
    log "Clientes sincronizados."
fi

# Sincronizar productos
if [[ "$SYNC_PRODUCTOS" == "true" ]]; then
    log "Sincronizando productos..."
    python manage.py shopify_sync_mainline --productos --limit "$LIMIT" --fecha-desde "$FECHA_DESDE" --fecha-hasta "$FECHA_HASTA" 2>&1 | tee -a "$LOG_FILE"
    log "Productos sincronizados."
fi

# Sincronizar órdenes
if [[ "$SYNC_ORDENES" == "true" ]]; then
    log "Sincronizando órdenes..."
    python manage.py shopify_sync_mainline --ordenes --limit "$LIMIT" --fecha-desde "$FECHA_DESDE" --fecha-hasta "$FECHA_HASTA" 2>&1 | tee -a "$LOG_FILE"
    log "Órdenes sincronizadas."
fi

# Sincronizar pagos
if [[ "$SYNC_PAGOS" == "true" ]]; then
    log "Sincronizando pagos..."
    python manage.py shopify_sync_mainline --pagos --limit "$LIMIT" --fecha-desde "$FECHA_DESDE" --fecha-hasta "$FECHA_HASTA" 2>&1 | tee -a "$LOG_FILE"
    log "Pagos sincronizados."
fi

log "=========================================="
log "Sincronización completada."
log "=========================================="
