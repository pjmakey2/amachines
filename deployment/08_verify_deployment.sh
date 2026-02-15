#!/bin/bash
# Script 8: Verificar despliegue

set -e

echo "========================================="
echo "Verifying deployment"
echo "========================================="

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Función para checks
check_service() {
    local service=$1
    local name=$2

    if systemctl is-active --quiet $service; then
        echo -e "${GREEN}✓${NC} $name is running"
        return 0
    else
        echo -e "${RED}✗${NC} $name is not running"
        return 1
    fi
}

check_docker_container() {
    local container=$1
    local name=$2

    if docker compose ps | grep $container | grep -q "Up"; then
        echo -e "${GREEN}✓${NC} $name container is running"
        return 0
    else
        echo -e "${RED}✗${NC} $name container is not running"
        return 1
    fi
}

# Navegar al directorio
cd /var/www/toca3d

echo "1. Checking system services..."
echo "------------------------------"
check_service docker "Docker"
check_service nginx "Nginx"
check_service toca3d-docker "Toca3D Docker service"

echo ""
echo "2. Checking Docker containers..."
echo "--------------------------------"
check_docker_container "toca3d_web" "Web (Daphne)"
check_docker_container "toca3d_celery_worker" "Celery Worker"
check_docker_container "toca3d_redis" "Redis"
check_docker_container "toca3d_db" "PostgreSQL"

echo ""
echo "3. Checking SSL certificate..."
echo "------------------------------"
if [ -f /etc/letsencrypt/live/toca3d.altamachines.com/fullchain.pem ]; then
    echo -e "${GREEN}✓${NC} SSL certificate exists"

    # Verificar validez del certificado
    expiry=$(sudo openssl x509 -enddate -noout -in /etc/letsencrypt/live/toca3d.altamachines.com/fullchain.pem | cut -d= -f2)
    echo "  Expires: $expiry"
else
    echo -e "${RED}✗${NC} SSL certificate not found"
fi

echo ""
echo "4. Checking network connectivity..."
echo "-----------------------------------"

# Test local application
if nc -z localhost 8002 2>/dev/null; then
    echo -e "${GREEN}✓${NC} Port 8002 is open (Daphne listening)"
else
    echo -e "${RED}✗${NC} Port 8002 is not open"
fi

# Test nginx proxy
if curl -f -k https://toca3d.altamachines.com > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} Application accessible via domain (HTTPS)"
else
    echo -e "${YELLOW}⚠${NC} Application not accessible via domain"
    echo "  (This might be normal if DNS hasn't propagated yet)"
fi

echo ""
echo "5. Checking WebSocket support..."
echo "--------------------------------"
# Verificar que nginx está configurado para WebSocket
if sudo nginx -T 2>/dev/null | grep -q "Upgrade.*upgrade"; then
    echo -e "${GREEN}✓${NC} Nginx configured for WebSocket"
else
    echo -e "${YELLOW}⚠${NC} WebSocket configuration might be missing"
fi

echo ""
echo "6. Checking logs for errors..."
echo "------------------------------"
# Últimas líneas de logs de Docker
echo "Recent Docker logs (web):"
docker compose logs --tail=10 web 2>&1 | grep -i error || echo "  No errors found"

echo ""
echo "Recent Nginx logs:"
sudo tail -5 /var/log/nginx/toca3d_error.log 2>&1 || echo "  No error log yet"

echo ""
echo "7. Resource usage..."
echo "--------------------"
docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}"

echo ""
echo "========================================"
echo "Deployment verification complete!"
echo "========================================"
echo ""
echo "Useful commands for monitoring:"
echo "  - View all logs:          docker compose logs -f"
echo "  - View web logs:          docker compose logs -f web"
echo "  - View celery logs:       docker compose logs -f celery_worker"
echo "  - View nginx access log:  sudo tail -f /var/log/nginx/toca3d_access.log"
echo "  - View nginx error log:   sudo tail -f /var/log/nginx/toca3d_error.log"
echo "  - Check systemd service:  sudo systemctl status toca3d-docker"
echo "  - Container stats:        docker stats"
echo ""
echo "To test WebSocket connection:"
echo "  Open browser console on https://toca3d.altamachines.com"
echo "  Run: new WebSocket('wss://toca3d.altamachines.com/ws/...')"
