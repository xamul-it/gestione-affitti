#!/bin/bash
# Script per avviare il backend senza variabili d'ambiente che causano conflitti
cd /home/htpc/test/gestione-affitti/backend
. ./venv/bin/activate
cd "$(dirname "$0")"
env -u DATABASE_URL -u BACKEND_CORS_ORIGINS LOG_LEVEL=DEBUG python -m app.main
