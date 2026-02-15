#!/bin/bash
# Script 1: Instalar Docker y Docker Compose
# Compatible con: Debian 12 (bookworm)

set -e

echo "========================================="
echo "Installing Docker and Docker Compose"
echo "Sistema: Debian 12 (bookworm)"
echo "========================================="

# Eliminar versiones antiguas si existen
for pkg in docker.io docker-doc docker-compose podman-docker containerd runc; do
    sudo apt-get remove -y $pkg 2>/dev/null || true
done

# Actualizar paquetes
sudo apt-get update

# Instalar dependencias
sudo apt-get install -y \
    apt-transport-https \
    ca-certificates \
    curl \
    gnupg

# Crear directorio para keyrings
sudo install -m 0755 -d /etc/apt/keyrings

# Agregar la clave GPG oficial de Docker (Debian)
curl -fsSL https://download.docker.com/linux/debian/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

# Configurar el repositorio estable (Debian)
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/debian \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Instalar Docker Engine
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Iniciar y habilitar Docker
sudo systemctl start docker
sudo systemctl enable docker

# Agregar usuario am al grupo docker
sudo usermod -aG docker am

# Verificar instalación
echo ""
echo "Verificando instalación..."
docker --version
docker compose version

echo ""
echo "✅ Docker instalado correctamente!"
echo "⚠️  IMPORTANTE: Cierra sesión y vuelve a conectarte para aplicar permisos"
echo "   Ejecuta: exit"
echo "   Luego: ssh am@167.99.145.70"
