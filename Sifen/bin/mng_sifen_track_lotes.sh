#!/bin/bash
# Track lotes from 5 days ago
# This script is meant to run via cron every 5 minutes

FIVE_DAYS_AGO=$(date -d "5 day ago" +'%Y-%m-%d')

cd /app
python manage.py mng_sifen_mainline --track_lotes --date "${FIVE_DAYS_AGO}"
