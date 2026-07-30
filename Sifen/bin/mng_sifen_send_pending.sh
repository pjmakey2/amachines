#!/bin/bash
# Send pending documents to Sifen
# This script is meant to run via cron every 5 minutes
PYTHON=/home/am/.pyenv/versions/Amachine/bin/python
MANAGE=/home/am/projects/Amachine/manage.py
$PYTHON $MANAGE mng_sifen_mainline --send_pending_docs
