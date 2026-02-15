#!/bin/bash
set -e

echo "Waiting for PostgreSQL..."
while ! nc -z $DB_HOST $DB_PORT; do
  sleep 0.1
done
echo "PostgreSQL started"

# Ejecutar migraciones
echo "Running migrations..."
python manage.py migrate --noinput

# Recolectar archivos estáticos
echo "Collecting static files..."
python manage.py collectstatic --noinput --clear

# Crear superusuario si no existe
echo "Creating superuser if needed..."
python manage.py create_amadmin || true

# Iniciar cron en background
echo "Starting cron jobs..."
supercronic /app/docker/crontab &

exec "$@"
