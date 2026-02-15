#!/bin/bash
# Script 5: Configurar Nginx

set -e

echo "========================================="
echo "Configuring Nginx"
echo "========================================="

# Instalar nginx si no está instalado
if ! command -v nginx &> /dev/null; then
    echo "Installing nginx..."
    sudo apt-get update
    sudo apt-get install -y nginx
fi

# Copiar configuración de nginx
echo "Copying nginx configuration..."
sudo cp /var/www/toca3d/docker/nginx/toca3d.conf /etc/nginx/sites-available/toca3d

# Crear enlace simbólico
if [ -f /etc/nginx/sites-enabled/toca3d ]; then
    echo "Removing existing symlink..."
    sudo rm /etc/nginx/sites-enabled/toca3d
fi

echo "Creating symlink..."
sudo ln -s /etc/nginx/sites-available/toca3d /etc/nginx/sites-enabled/toca3d

# Eliminar configuración por defecto si existe
if [ -f /etc/nginx/sites-enabled/default ]; then
    echo "Removing default nginx configuration..."
    sudo rm /etc/nginx/sites-enabled/default
fi

# Probar configuración
echo "Testing nginx configuration..."
sudo nginx -t

# Reiniciar nginx
echo "Restarting nginx..."
sudo systemctl restart nginx

# Habilitar nginx para inicio automático
sudo systemctl enable nginx

echo "✓ Nginx configured successfully!"
echo ""
echo "Configuration file: /etc/nginx/sites-available/toca3d"
echo "Active site: /etc/nginx/sites-enabled/toca3d"
