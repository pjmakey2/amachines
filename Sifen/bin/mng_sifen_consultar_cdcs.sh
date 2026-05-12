#!/bin/bash
# Consultar CDCs en SIFEN para documentos del mes anterior y mes actual
# Actualiza ek_estado/lote_estado segun respuesta de SIFEN

FECHA_DESDE=$(date -d "$(date +'%Y-%m-01') -1 month" +'%Y-%m-%d')
FECHA_HASTA=$(date +'%Y-%m-%d')

cd /app
python manage.py mng_sifen_mainline --consultar_cdcs --dates "${FECHA_DESDE}" "${FECHA_HASTA}"
