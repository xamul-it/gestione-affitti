#!/bin/bash
# Promuove il codice e il DB dall'ambiente di sviluppo (questo repo, branch
# passato come argomento, default master) all'ambiente stabile/produzione
# (worktree separato ~/apps/gestione-affitti-stable, branch "stable").
#
# Non tocca mai il DB di sviluppo: lavora solo sul DB di produzione
# (gestione_affitti_prod), e lo fa sempre dopo averne fatto un backup
# verificato. Migra la catena core e quelle dei moduli su tutti gli schema,
# applica i dati di base pubblici dei moduli, e confronta il numero di righe
# di ogni tabella prima e dopo: se qualcosa diminuisce si ferma, salvo le
# tabelle elencate in PROMOTE_PERDITA_CONSENTITA (azzeramento voluto).
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

# Azzeramento voluto (es. ripartenza dei dati decisa dall'utente): le tabelle
# elencate (nomi senza schema, separati da spazio) possono perdere righe.
if [ -n "${PROMOTE_PERDITA_CONSENTITA:-}" ]; then
    echo "==> Perdita di righe consentita per: $PROMOTE_PERDITA_CONSENTITA"
    if [ -t 0 ]; then
        read -r -p "    Confermi l'azzeramento di queste tabelle in produzione? [s/N] " risposta
        [ "$risposta" = "s" ] || { echo "Annullato."; exit 1; }
    fi
fi

echo "==> Promuovo '$TARGET_REF' su stable"

cd "$STABLE_DIR"

if [ -n "$(git status --porcelain)" ]; then
    echo "ERRORE: il worktree stable ha modifiche non committate. Risolvi prima di promuovere." >&2
    git status --short
    exit 1
fi

# I documenti caricati (backend/storage) non sono nel dump del DB: archivio
# prima di aggiornare il codice. Il 2026-11-09 un commit che toglieva
# storage/ dall'indice git ha fatto cancellare al merge i file tracciati.
STORAGE_DIR="$STABLE_DIR/backend/storage"
STORAGE_STAMP="$(date +%Y%m%d_%H%M%S)"
STORAGE_ARCHIVE="$BACKUP_DIR/storage_${STORAGE_STAMP}.tgz"
STORAGE_LIST_BEFORE="$BACKUP_DIR/storage_${STORAGE_STAMP}.before.txt"
(umask 077; mkdir -p "$BACKUP_DIR")
if [ -d "$STORAGE_DIR" ]; then
    echo "==> Archivio documenti (backend/storage)"
    (umask 077; tar -C "$STABLE_DIR/backend" -czf "$STORAGE_ARCHIVE" storage)
    (umask 077; find "$STORAGE_DIR" -type f | LC_ALL=C sort > "$STORAGE_LIST_BEFORE")
    echo "    $STORAGE_ARCHIVE ($(wc -l < "$STORAGE_LIST_BEFORE") file)"
    ls -t "$BACKUP_DIR"/storage_*.tgz 2>/dev/null | tail -n +15 | while read -r old; do
        rm -f "$old" "${old%.tgz}.before.txt"
    done
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

if [ -f "$STORAGE_LIST_BEFORE" ]; then
    missing="$(LC_ALL=C comm -23 "$STORAGE_LIST_BEFORE" <(find "$STORAGE_DIR" -type f 2>/dev/null | LC_ALL=C sort))"
    if [ -n "$missing" ]; then
        echo "ERRORE: l'aggiornamento del codice ha tolto documenti da backend/storage:" >&2
        echo "$missing" | sed 's/^/    /' >&2
        echo "    DB non toccato, backend non fermato. Ripristino documenti:" >&2
        echo "    tar -C $STABLE_DIR/backend -xzf $STORAGE_ARCHIVE" >&2
        exit 1
    fi
fi

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

PSQL=(psql -X -q -At -v ON_ERROR_STOP=1 -h "$PGHOST" -p "$PGPORT" -U "$PGUSER" "$PROD_DB")
STAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP_FILE="$BACKUP_DIR/${PROD_DB}_${STAMP}.sql"
SNAP_BEFORE="$BACKUP_DIR/${PROD_DB}_${STAMP}.before.txt"
SNAP_AFTER="$BACKUP_DIR/${PROD_DB}_${STAMP}.after.txt"
SNAPSHOT_SQL="$STABLE_DIR/scripts/sql/db_snapshot.sql"

print_restore() {
    echo "    Ripristino dal backup (dopo: systemctl --user stop gestione-affitti-backend.service):" >&2
    echo "    dropdb -h $PGHOST -p $PGPORT -U $PGUSER $PROD_DB" >&2
    echo "    createdb -h $PGHOST -p $PGPORT -U $PGUSER $PROD_DB" >&2
    echo "    psql -h $PGHOST -p $PGPORT -U $PGUSER $PROD_DB < $BACKUP_FILE" >&2
}

# Backend fermo durante backup e migrazione: nessuna scrittura (scheduler
# compresi) tra la fotografia "prima", il dump e la migrazione.
echo "==> Arresto backend"
systemctl --user stop gestione-affitti-backend.service
# Fino all'inizio della migrazione il DB non e' stato toccato: su errore si
# riavvia il backend com'era.
trap 'echo "ERRORE prima della migrazione: DB non modificato, riavvio backend." >&2; systemctl --user start gestione-affitti-backend.service' ERR

echo "==> Backup del DB di produzione prima della migrazione"
# I dump contengono tutti i dati di produzione (hash password inclusi):
# leggibili solo dall'utente.
(umask 077; mkdir -p "$BACKUP_DIR")
chmod 700 "$BACKUP_DIR"
(umask 077; "${PSQL[@]}" -f "$SNAPSHOT_SQL" > "$SNAP_BEFORE" 2>/dev/null)
(umask 077; pg_dump -h "$PGHOST" -p "$PGPORT" -U "$PGUSER" "$PROD_DB" > "$BACKUP_FILE")
if [ ! -s "$BACKUP_FILE" ] || ! tail -n 20 "$BACKUP_FILE" | grep -q "PostgreSQL database dump complete"; then
    echo "ERRORE: backup incompleto ($BACKUP_FILE). Migrazione NON eseguita." >&2
    systemctl --user start gestione-affitti-backend.service
    exit 1
fi
echo "    backup verificato: $BACKUP_FILE ($(du -h "$BACKUP_FILE" | cut -f1), $(wc -l < "$SNAP_BEFORE") tabelle fotografate)"

# Tiene solo gli ultimi 14 backup (con le loro fotografie)
ls -t "$BACKUP_DIR"/${PROD_DB}_*.sql 2>/dev/null | tail -n +15 | while read -r old; do
    rm -f "$old" "${old%.sql}.before.txt" "${old%.sql}.after.txt" "${old%.sql}.started.txt"
done

# Da qui un errore lascia il backend fermo: va prima capito cosa e' successo.
trap 'echo "ERRORE durante la migrazione: backend lasciato fermo." >&2; print_restore' ERR

echo "==> Migrazione del DB di produzione: catena core (tutti gli schema)"
cd "$STABLE_DIR/backend"
alembic -x schema=all upgrade head

echo "==> Migrazioni e dati di base dei moduli (public + tenant)"
python scripts/sync_modules.py

trap - ERR

# confronta PRIMA DOPO: errore se una tabella sparisce o perde righe; le
# versioni alembic e le tabelle/righe nuove sono solo riportate. Le tabelle in
# PROMOTE_PERDITA_CONSENTITA possono perdere righe (azzeramento voluto).
confronta() {
    awk -v consentite="${PROMOTE_PERDITA_CONSENTITA:-}" -f "$STABLE_DIR/scripts/sql/confronta_snapshot.awk" "$1" "$2" | sort
    return "${PIPESTATUS[0]}"
}

echo "==> Verifica preservazione dati"
(umask 077; "${PSQL[@]}" -f "$SNAPSHOT_SQL" > "$SNAP_AFTER" 2>/dev/null)
if ! confronta "$SNAP_BEFORE" "$SNAP_AFTER"; then
    echo "ERRORE: dati persi durante la migrazione. Backend lasciato fermo." >&2
    echo "    Fotografie: $SNAP_BEFORE  $SNAP_AFTER" >&2
    print_restore
    exit 1
fi
echo "    nessuna tabella o riga persa"

echo "==> Avvio backend (il frontend e' servito da Apache direttamente da dist/)"
systemctl --user start gestione-affitti-backend.service

for _ in $(seq 1 30); do
    if curl -sf -m 2 http://127.0.0.1:8001/health > /dev/null; then
        break
    fi
    sleep 1
done
if ! curl -sf -m 2 http://127.0.0.1:8001/health > /dev/null; then
    echo "ERRORE: il backend non risponde su /health dopo 30s" >&2
    systemctl --user --no-pager status gestione-affitti-backend.service >&2 || true
    print_restore
    exit 1
fi
echo "    backend attivo, /health ok"

# L'avvio del backend esegue a sua volta seed e allineamenti (ruoli,
# permessi, menu): anche quelli non devono togliere dati.
echo "==> Verifica preservazione dati dopo l'avvio"
SNAP_STARTED="$BACKUP_DIR/${PROD_DB}_${STAMP}.started.txt"
(umask 077; "${PSQL[@]}" -f "$SNAPSHOT_SQL" > "$SNAP_STARTED" 2>/dev/null)
if ! confronta "$SNAP_AFTER" "$SNAP_STARTED"; then
    echo "ERRORE: l'avvio del backend ha tolto dati (backend attivo)." >&2
    echo "    Fotografie: $SNAP_AFTER  $SNAP_STARTED" >&2
    print_restore
    exit 1
fi
echo "    nessuna tabella o riga persa all'avvio"

echo
echo "==> Promozione completata."
echo "    Backup: $BACKUP_FILE"
echo "    Fotografie: $SNAP_BEFORE  $SNAP_AFTER  $SNAP_STARTED"
