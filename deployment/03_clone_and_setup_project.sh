#!/bin/bash
# Script 3: Clonar proyecto y configurar

set -e

echo "========================================="
echo "Clonando proyecto desde GitHub"
echo "========================================="

cd /var/www/toca3d

# Verificar si ya hay archivos
if [ "$(ls -A /var/www/toca3d 2>/dev/null)" ]; then
    echo "⚠️  El directorio no está vacío."
    read -p "¿Deseas hacer git pull en lugar de clone? (s/n): " respuesta
    if [ "$respuesta" = "s" ]; then
        echo "Ejecutando git pull..."
        git pull origin main
    else
        echo "Abortando. Limpia el directorio primero si deseas clonar."
        exit 1
    fi
else
    # Clonar el repositorio
    echo "Clonando repositorio..."
    echo "Opciones de autenticación:"
    echo "  1) SSH (requiere deploy key configurada)"
    echo "  2) HTTPS (requiere Personal Access Token)"
    read -p "Selecciona (1/2): " auth_method

    if [ "$auth_method" = "1" ]; then
        GIT_SSH_COMMAND='ssh -i ~/.ssh/id_toca3d -o IdentitiesOnly=yes' git clone git@github.com:altamachines/toca3d.git .
    else
        read -p "Usuario de GitHub: " github_user
        read -sp "Personal Access Token: " github_token
        echo ""
        git clone https://${github_user}:${github_token}@github.com/altamachines/toca3d.git .
    fi
fi

# Ajustar permisos después del clone
sudo chown -R am:am /var/www/toca3d

# Copiar archivo de entorno
if [ ! -f .env ]; then
    cp .env.example .env
    echo "✅ Archivo .env creado desde .env.example"
else
    echo "⚠️  Archivo .env ya existe, no se sobrescribe"
fi

echo ""
echo "✅ Proyecto clonado correctamente"
echo ""
echo "⚠️  IMPORTANTE: Edita el archivo .env:"
echo "   nano /var/www/toca3d/.env"
echo ""
echo "   Configura:"
echo "   - SECRET_KEY (genera con: python3 -c \"import secrets; print(secrets.token_urlsafe(50))\")"
echo "   - DB_PASSWORD"
echo "   - Configuraciones de SIFEN si aplica"
