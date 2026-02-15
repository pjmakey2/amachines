#!/bin/bash
# Script 2: Crear directorio base y logs

set -e

echo "========================================="
echo "Creando directorios base"
echo "========================================="

# Crear directorio base (vacío, para el git clone)
sudo mkdir -p /var/www/toca3d

# Crear directorio de logs
sudo mkdir -p /var/log/toca3d

# Cambiar propietario a usuario am
sudo chown -R am:am /var/www/toca3d
sudo chown -R am:am /var/log/toca3d

echo "✅ Directorios creados:"
echo "   - /var/www/toca3d (para el proyecto)"
echo "   - /var/log/toca3d (para logs)"
