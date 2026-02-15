#!/bin/bash
# Send invoice emails to clients for documents from 14 days ago
# This script is meant to run via cron

FOURTEEN_DAYS_AGO=$(date -d "14 day ago" +'%Y-%m-%d')

cd /app
python manage.py mng_sifen_mainline --send_email --date "${FOURTEEN_DAYS_AGO}"
