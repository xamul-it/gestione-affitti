#!/bin/bash

# Export password
export PGPASSWORD=affitti

# Activate venv and run test
cd /home/htpc/test/gestione-affitti
source backend/venv/bin/activate
python tmp/test_import_complete.py
