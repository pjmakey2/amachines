#!/bin/bash
# Script 7: Configurar servicio systemd

set -e

echo "========================================="
echo "Setting up systemd service"
echo "========================================="

# Copiar archivo de servicio
echo "Installing systemd service..."
sudo cp /var/www/toca3d/docker/toca3d-docker.service /etc/systemd/system/

# Recargar systemd
echo "Reloading systemd daemon..."
sudo systemctl daemon-reload

# Habilitar servicio para inicio automático
echo "Enabling service..."
sudo systemctl enable toca3d-docker.service

# Iniciar servicio
echo "Starting service..."
sudo systemctl start toca3d-docker.service

# Verificar estado
echo ""
echo "Service status:"
sudo systemctl status toca3d-docker.service --no-pager

echo ""
echo "✓ Systemd service configured successfully!"
echo ""
echo "Service commands:"
echo "  Start service:   sudo systemctl start toca3d-docker"
echo "  Stop service:    sudo systemctl stop toca3d-docker"
echo "  Restart service: sudo systemctl restart toca3d-docker"
echo "  View status:     sudo systemctl status toca3d-docker"
echo "  View logs:       sudo journalctl -u toca3d-docker -f"
echo ""
echo "⚠ NOTE: The service will start automatically on system boot"
