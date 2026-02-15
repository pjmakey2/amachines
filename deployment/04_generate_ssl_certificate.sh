#!/bin/bash
# Script 4: Generar certificado SSL con Let's Encrypt

set -e

echo "========================================="
echo "Generating SSL certificate"
echo "========================================="

# Instalar certbot si no está instalado
if ! command -v certbot &> /dev/null; then
    echo "Installing certbot..."
    sudo apt-get update
    sudo apt-get install -y certbot python3-certbot-nginx
fi

# Detener nginx temporalmente si está corriendo
if systemctl is-active --quiet nginx; then
    echo "Stopping nginx temporarily..."
    sudo systemctl stop nginx
fi

# Generar certificado
echo "Generating certificate for toca3d.altamachines.com..."
sudo certbot certonly --standalone \
    -d toca3d.altamachines.com \
    --non-interactive \
    --agree-tos \
    -m pjmakey2@gmail.com

# Verificar que se generó el certificado
if [ -f /etc/letsencrypt/live/toca3d.altamachines.com/fullchain.pem ]; then
    echo "✓ SSL certificate generated successfully!"
    echo "  Certificate: /etc/letsencrypt/live/toca3d.altamachines.com/fullchain.pem"
    echo "  Private key: /etc/letsencrypt/live/toca3d.altamachines.com/privkey.pem"
else
    echo "✗ Error: Certificate not found"
    exit 1
fi

echo ""
echo "⚠ NOTE: Certificate will auto-renew via certbot timer"
echo "   Check with: sudo systemctl status certbot.timer"
