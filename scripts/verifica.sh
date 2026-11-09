#!/bin/bash
# Verifica dell'ambiente di sviluppo prima di un rilascio: suite backend
# completa (unitari + integrazione su PostgreSQL), test e build del frontend,
# e controllo che i test non lascino righe nel DB di sviluppo.
#
# La regola e' semplice: tutto deve passare e il DB deve restare identico.
# Non ci sono fallimenti "noti" da ignorare.
#
# Uso: scripts/verifica.sh [all|backend|frontend]   (default: all)
# Exit 0 = VERDE, 1 = ROSSO. I log completi restano nella cartella stampata.

set -uo pipefail

REPO="$(cd "$(dirname "$0")/.." && pwd)"
SCOPE="${1:-all}"
LOG_DIR="$(mktemp -d -t verifica-XXXXXX)"
ROSSO=0

case "$SCOPE" in all|backend|frontend) ;; *)
    echo "Uso: $0 [all|backend|frontend]" >&2; exit 2 ;;
esac

db_snapshot() {
    local url
    url="$(grep -E '^DATABASE_URL=' "$REPO/backend/.env" | cut -d= -f2- | sed 's/+psycopg2//')"
    psql "$url" -X -q -At -v ON_ERROR_STOP=1 -f "$REPO/scripts/sql/db_snapshot.sql" 2>/dev/null
}

if [ "$SCOPE" != frontend ]; then
    echo "==> Backend (pytest tests/)"
    db_snapshot > "$LOG_DIR/db_before.txt"
    touch "$LOG_DIR/storage_marker"
    (cd "$REPO/backend" && venv/bin/python -m pytest tests -q -p no:cacheprovider) > "$LOG_DIR/backend.log" 2>&1
    rc=$?
    db_snapshot > "$LOG_DIR/db_after.txt"
    echo "    $(grep -E '^=+ .*(passed|failed|error).* =+$' "$LOG_DIR/backend.log" | tail -1 | tr -d '=' | xargs)"
    if [ $rc -ne 0 ]; then
        ROSSO=1
        grep -E '^(FAILED|ERROR) ' "$LOG_DIR/backend.log" | cut -c1-200 | sed 's/^/    /'
    fi
    if ! diff -q "$LOG_DIR/db_before.txt" "$LOG_DIR/db_after.txt" > /dev/null; then
        ROSSO=1
        echo "    DB di sviluppo modificato dai test (righe lasciate o tolte):"
        diff "$LOG_DIR/db_before.txt" "$LOG_DIR/db_after.txt" | grep '^[<>]' | sed 's/^/      /'
    else
        echo "    DB di sviluppo invariato"
    fi
    # File di documenti scritti dai test nello storage e non rimossi
    leaked="$(find "$REPO/backend/storage" -type f -newer "$LOG_DIR/storage_marker" 2>/dev/null)"
    if [ -n "$leaked" ]; then
        ROSSO=1
        echo "    File lasciati dai test in backend/storage:"
        echo "$leaked" | sed "s|$REPO/||; s/^/      /"
    else
        echo "    storage invariato"
    fi
fi

if [ "$SCOPE" != backend ]; then
    echo "==> Frontend (vitest)"
    (cd "$REPO/frontend" && npx vitest run) > "$LOG_DIR/frontend.log" 2>&1
    rc=$?
    clean() { sed 's/\x1b\[[0-9;]*m//g' "$1"; }
    echo "    $(clean "$LOG_DIR/frontend.log" | grep -E '^\s+Tests ' | tail -1 | xargs)"
    if [ $rc -ne 0 ]; then
        ROSSO=1
        clean "$LOG_DIR/frontend.log" | grep -E '^\s+(×|FAIL) ' | sed 's/ [0-9]*ms$//' | sort -u | sed 's/^\s*/    /'
    fi

    echo "==> Frontend (build)"
    if (cd "$REPO/frontend" && npm run build) > "$LOG_DIR/build.log" 2>&1; then
        echo "    build ok"
    else
        ROSSO=1
        echo "    build FALLITA:"
        grep -iE 'error' "$LOG_DIR/build.log" | head -10 | sed 's/^/    /'
    fi
fi

echo
echo "Log completi: $LOG_DIR"
if [ $ROSSO -eq 0 ]; then
    echo "ESITO: VERDE"
else
    echo "ESITO: ROSSO"
fi
exit $ROSSO
