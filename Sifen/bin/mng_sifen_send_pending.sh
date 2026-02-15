#!/bin/bash
# Send pending documents to Sifen
# This script is meant to run via cron every 5 minutes

cd /app
python manage.py mng_sifen_mainline --send_pending_docs
