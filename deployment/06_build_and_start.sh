#!/bin/bash
# Script 6: Construir y arrancar contenedores Docker

set -e

echo "========================================="
echo "Building and starting Docker containers"
echo "========================================="

# Navegar al directorio del proyecto
cd /var/www/toca3d

# Verificar que existe el archivo .env
if [ ! -f .env ]; then
    echo "✗ Error: .env file not found"
    echo "  Please copy .env.example to .env and configure it first"
    exit 1
fi

# Detener contenedores existentes si los hay
if docker compose ps | grep -q "Up"; then
    echo "Stopping existing containers..."
    docker compose down
fi

# Construir imágenes
echo "Building Docker images..."
docker compose build --no-cache

# Iniciar contenedores
echo "Starting containers..."
docker compose up -d

# Esperar a que los contenedores estén listos
echo "Waiting for containers to be ready..."
sleep 10

# Verificar estado de los contenedores
echo ""
echo "Container status:"
docker compose ps

# Verificar logs
echo ""
echo "Recent logs from web container:"
docker compose logs --tail=20 web

# Verificar que la aplicación responde
echo ""
echo "Testing application health..."
sleep 5

if curl -f -k https://localhost:8002 > /dev/null 2>&1; then
    echo "✓ Application is responding!"
else
    echo "⚠ Warning: Application might not be ready yet"
    echo "  Check logs with: docker compose logs -f web"
fi

echo ""
echo "✓ Docker containers started successfully!"
echo ""
echo "Useful commands:"
echo "  View logs:        docker compose logs -f"
echo "  View web logs:    docker compose logs -f web"
echo "  View celery logs: docker compose logs -f celery_worker"
echo "  Restart services: docker compose restart"
echo "  Stop services:    docker compose down"
