#!/bin/bash
# Replica il tenant con i dati reali (tenant_produzione del DB di produzione)
# nell'ambiente di sviluppo, per riprodurre bachi su dati specifici o fare
# prove potenzialmente distruttive senza toccare l'originale.
#
# - Produzione: solo LETTURA (pg_dump dello schema e copia dei documenti).
# - Sviluppo: lo schema tenant_produzione del DB di sviluppo e la sua
#   cartella documenti vengono SOSTITUITI dalla copia (prima ne viene fatto
#   un backup). Poi lo schema viene portato al codice di sviluppo con le
#   migrazioni: e' anche la prova delle migrazioni sui dati veri prima di
#   un rilascio.
#
# Uso: scripts/replica_produzione.sh

set -euo pipefail

REPO="$(cd "$(dirname "$0")/.." && pwd)"
STABLE_DIR="/home/htpc/apps/gestione-affitti-stable"
BACKUP_DIR="${GESTIONE_AFFITTI_BACKUP_DIR:-$HOME/apps/gestione-affitti-backups}"
SCHEMA="tenant_produzione"
STAMP="$(date +%Y%m%d_%H%M%S)"

PROD_ENV_FILE="${GESTIONE_AFFITTI_PROD_ENV:-$HOME/.config/gestione-affitti-prod.env}"
# shellcheck disable=SC1090
source "$PROD_ENV_FILE"
: "${PGHOST:?}" "${PGPORT:?}" "${PGUSER:?}" "${PGPASSWORD:?}" "${PROD_DB:?}"
PROD_URL="postgresql://$PGUSER:$PGPASSWORD@$PGHOST:$PGPORT/$PROD_DB"
unset PGHOST PGPORT PGUSER PGPASSWORD   # da qui ogni comando dice esplicitamente dove va

DEV_URL="$(grep -E '^DATABASE_URL=' "$REPO/backend/.env" | cut -d= -f2- | sed 's/+psycopg2//')"
DEV_DB="$(psql "$DEV_URL" -X -At -c 'SELECT current_database()' 2>/dev/null)"
if [ "$DEV_DB" = "$PROD_DB" ] || [ -z "$DEV_DB" ]; then
    echo "ERRORE: il DB di sviluppo ('$DEV_DB') coincide con quello di produzione o non risponde." >&2
    exit 1
fi

(umask 077; mkdir -p "$BACKUP_DIR")
DEV_BACKUP="$BACKUP_DIR/dev_${SCHEMA}_${STAMP}.dump"
PROD_DUMP="$BACKUP_DIR/replica_${SCHEMA}_${STAMP}.dump"
trap 'rm -f "$PROD_DUMP"' EXIT   # la copia dei dati reali non resta in giro

echo "==> Backup dello schema $SCHEMA di sviluppo ($DEV_DB)"
(umask 077; pg_dump "$DEV_URL" -n "$SCHEMA" -Fc -f "$DEV_BACKUP")
(umask 077; tar -C "$REPO/backend/storage" -czf "${DEV_BACKUP%.dump}.storage.tgz" "$SCHEMA" 2>/dev/null || true)
echo "    $DEV_BACKUP"

echo "==> Lettura di $SCHEMA da produzione ($PROD_DB)"
(umask 077; pg_dump "$PROD_URL" -n "$SCHEMA" -Fc --no-owner --no-privileges -f "$PROD_DUMP" 2>/dev/null)

echo "==> Sostituzione di $SCHEMA in sviluppo"
psql "$DEV_URL" -X -q -v ON_ERROR_STOP=1 -c "DROP SCHEMA IF EXISTS $SCHEMA CASCADE" 2>/dev/null
if ! pg_restore -d "$DEV_URL" --no-owner --no-privileges "$PROD_DUMP" 2> "$BACKUP_DIR/replica_${STAMP}.log"; then
    echo "ATTENZIONE: pg_restore ha segnalato errori (dettagli in $BACKUP_DIR/replica_${STAMP}.log):" >&2
    grep -v "versione di confronto\|DETAIL\|HINT\|collation version" "$BACKUP_DIR/replica_${STAMP}.log" | head -15 >&2
fi

echo "==> Copia dei documenti"
mkdir -p "$REPO/backend/storage/$SCHEMA"
if [ -d "$STABLE_DIR/backend/storage/$SCHEMA" ]; then
    rsync -a --delete "$STABLE_DIR/backend/storage/$SCHEMA/" "$REPO/backend/storage/$SCHEMA/"
fi

echo "==> Allineamento al codice di sviluppo (migrazioni core e moduli)"
cd "$REPO/backend"
venv/bin/python -m alembic -x "schema=$SCHEMA" upgrade head 2>&1 | grep -v "versione di confronto\|DETAIL\|HINT" | tail -2
venv/bin/python scripts/sync_modules.py 2>&1 | grep -E "ERRORE|ATTENZIONE|-> $SCHEMA" | grep -v migrazioni || true

echo
echo "==> Replica pronta: $SCHEMA nel DB di sviluppo ($DEV_DB) e backend/storage/$SCHEMA"
echo "    $(psql "$DEV_URL" -X -At -c "SELECT count(*) FROM information_schema.tables WHERE table_schema='$SCHEMA'" 2>/dev/null) tabelle"
echo "    Per tornare alla versione di sviluppo precedente:"
echo "    psql \"\$DEV\" -c 'DROP SCHEMA $SCHEMA CASCADE' && pg_restore -d \"\$DEV\" $DEV_BACKUP"
