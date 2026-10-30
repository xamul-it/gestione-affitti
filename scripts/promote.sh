#!/bin/bash
# Promuove il codice e il DB dall'ambiente di sviluppo (questo repo, branch
# passato come argomento, default master) all'ambiente stabile/produzione
# (worktree separato ~/apps/gestione-affitti-stable, branch "stable").
#
# Non tocca mai il DB di sviluppo: lavora solo sul DB di produzione
# (gestione_affitti_prod), e lo fa sempre dopo averne fatto un backup.
#
# Uso: scripts/promote.sh [ref-da-promuovere]   (default: master)

set -euo pipefail

DEV_REPO="/home/htpc/test/gestione-affitti"
STABLE_DIR="/home/htpc/apps/gestione-affitti-stable"
# Fuori dal worktree: dentro, i dump risulterebbero file non tracciati e
# bloccherebbero la promozione successiva.
BACKUP_DIR="${GESTIONE_AFFITTI_BACKUP_DIR:-$HOME/apps/gestione-affitti-backups}"
TARGET_REF="${1:-master}"

# Credenziali del DB di produzione: NON in questo file (che e' nel repo),
# ma in un file fuori da git, leggibile solo dall'utente (chmod 600).
PROD_ENV_FILE="${GESTIONE_AFFITTI_PROD_ENV:-$HOME/.config/gestione-affitti-prod.env}"
if [ ! -f "$PROD_ENV_FILE" ]; then
    echo "ERRORE: file credenziali mancante: $PROD_ENV_FILE" >&2
    exit 1
fi
# shellcheck disable=SC1090
source "$PROD_ENV_FILE"
: "${PGHOST:?PGHOST non impostato in $PROD_ENV_FILE}"
: "${PGPORT:?PGPORT non impostato in $PROD_ENV_FILE}"
: "${PGUSER:?PGUSER non impostato in $PROD_ENV_FILE}"
: "${PGPASSWORD:?PGPASSWORD non impostato in $PROD_ENV_FILE}"
: "${PROD_DB:?PROD_DB non impostato in $PROD_ENV_FILE}"
export PGPASSWORD

echo "==> Promuovo '$TARGET_REF' su stable"

cd "$STABLE_DIR"

if [ -n "$(git status --porcelain)" ]; then
    echo "ERRORE: il worktree stable ha modifiche non committate. Risolvi prima di promuovere." >&2
    git status --short
    exit 1
fi

git fetch "$DEV_REPO" "$TARGET_REF":refs/tmp/promote-source
if ! git merge-base --is-ancestor stable refs/tmp/promote-source; then
    echo "ERRORE: stable non e' un antenato di '$TARGET_REF' (storie divergenti)." >&2
    echo "Promozione interrotta per evitare di perdere commit solo-stable. Risolvi manualmente." >&2
    git update-ref -d refs/tmp/promote-source
    exit 1
fi
git merge --ff-only refs/tmp/promote-source
git update-ref -d refs/tmp/promote-source

echo "==> Aggiorno dipendenze backend"
cd "$STABLE_DIR/backend"
source venv/bin/activate
# Il venv e' creato con uv e non contiene pip: "pip" risolverebbe a quello di
# sistema, che rifiuta l'installazione (PEP 668) e fa fallire lo script.
uv pip install --python venv/bin/python -r requirements.txt -q

echo "==> Build frontend"
cd "$STABLE_DIR/frontend"
npm install --silent
npm run build

echo "==> Backup del DB di produzione prima della migrazione"
# I dump contengono tutti i dati di produzione (hash password inclusi):
# leggibili solo dall'utente.
(umask 077; mkdir -p "$BACKUP_DIR")
chmod 700 "$BACKUP_DIR"
BACKUP_FILE="$BACKUP_DIR/${PROD_DB}_$(date +%Y%m%d_%H%M%S).sql"
(umask 077; pg_dump -h "$PGHOST" -p "$PGPORT" -U "$PGUSER" "$PROD_DB" > "$BACKUP_FILE")
echo "    backup salvato in: $BACKUP_FILE"

# Tiene solo gli ultimi 14 backup per non saturare lo spazio disco
ls -t "$BACKUP_DIR"/${PROD_DB}_*.sql 2>/dev/null | tail -n +15 | xargs -r rm -f

echo "==> Migrazione del DB di produzione (tutti gli schema)"
cd "$STABLE_DIR/backend"
alembic -x schema=all upgrade head

echo "==> Riavvio backend (il frontend e' servito da Apache direttamente da dist/)"
systemctl --user restart gestione-affitti-backend.service

sleep 2
systemctl --user --no-pager status gestione-affitti-backend.service

echo
echo "==> Promozione completata. In caso di problemi, ripristino da backup:"
echo "    dropdb -h $PGHOST -p $PGPORT -U $PGUSER $PROD_DB"
echo "    createdb -h $PGHOST -p $PGPORT -U $PGUSER $PROD_DB"
echo "    psql -h $PGHOST -p $PGPORT -U $PGUSER $PROD_DB < $BACKUP_FILE"
