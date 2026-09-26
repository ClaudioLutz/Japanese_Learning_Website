#!/bin/bash
# Wrapper fuer Pipeline-Laeufe auf hp-ubuntu gegen die Prod-DB (Host-Port 5432).
# Nutzung: bash /tmp/l1/lektionen1_run.sh <pipeline-args...>
set -e
cd /home/hp-ubuntu/git/Japanese_Learning_Website
DB_LINE=$(grep '^DATABASE_URL=' .env | head -1 | cut -d= -f2- | tr -d '"')
export DATABASE_URL=$(echo "$DB_LINE" | sed 's/@db:/@localhost:/; s/@db\//@localhost:5432\//')
export PYTHONIOENCODING=utf-8
exec venv/bin/python "$@"
