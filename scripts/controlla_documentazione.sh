#!/usr/bin/env bash
# Checks that a range of commits that changes platform or module code also
# updates the matching living document (docs/piattaforma.md,
# docs/modules/<modulo>.md). Prints warnings only: it never fails the release.
#
# Usage: scripts/controlla_documentazione.sh <da-commit> [<a-commit>]
set -uo pipefail

DA="${1:?uso: $0 <da-commit> [<a-commit>]}"
A="${2:-HEAD}"
cd "$(git rev-parse --show-toplevel)" || exit 0

FILES=$(git diff --name-only "$DA" "$A" 2>/dev/null) || { echo "documentazione: range $DA..$A non valido, controllo saltato"; exit 0; }
[ -z "$FILES" ] && { echo "documentazione: nessun file cambiato"; exit 0; }

is_code() { grep -vE '(^|/)tests?/|\.test\.jsx?$|/__pycache__/|\.md$' ; }
avvisi=0

# Platform
if echo "$FILES" | grep -E '^(backend/app/|frontend/src/core/|scripts/promote\.sh)' | is_code | grep -q .; then
  if ! echo "$FILES" | grep -qx 'docs/piattaforma.md'; then
    echo "ATTENZIONE documentazione: codice di piattaforma cambiato senza aggiornare docs/piattaforma.md"
    avvisi=1
  fi
fi

# Modules
moduli=$(echo "$FILES" | is_code | sed -nE 's#^(backend|frontend/src)/modules/([^/]+)/.*#\2#p' | sort -u)
for m in $moduli; do
  doc="docs/modules/$m.md"
  if [ ! -f "$doc" ]; then
    echo "NOTA documentazione: modulo $m cambiato, $doc non esiste ancora (da creare quando si lavora sul modulo)"
  elif ! echo "$FILES" | grep -qx "$doc"; then
    echo "ATTENZIONE documentazione: modulo $m cambiato senza aggiornare $doc"
    avvisi=1
  fi
done

[ "$avvisi" = 0 ] && echo "documentazione: ok"
exit 0
