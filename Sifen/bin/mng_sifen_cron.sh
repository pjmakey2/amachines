#!/bin/bash
# Track lotes + Send emails
# Crontab usage: */5 * * * * /home/am/projects/Amachine/Sifen/bin/mng_sifen_cron.sh >> /var/log/amachine_cron.log 2>&1

PYTHON=/home/am/.pyenv/versions/Amachine/bin/python
MANAGE=/home/am/projects/Amachine/manage.py7

$PYTHON $MANAGE mng_sifen_mainline --track_lotes
$PYTHON $MANAGE mng_sifen_mainline --send_email
