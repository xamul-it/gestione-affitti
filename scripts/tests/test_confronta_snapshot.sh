#!/bin/bash
# Test del confronto prima/dopo usato da promote.sh (scripts/sql/confronta_snapshot.awk).
set -u
AWK="$(dirname "$0")/../sql/confronta_snapshot.awk"
T="$(mktemp -d)"; trap 'rm -rf "$T"' EXIT
fail=0
check() { if [ "$1" = ok ]; then echo "ok   - $2"; else echo "FAIL - $2"; fail=1; fi; }

printf 'tenant_x.anag_soggetti_anagrafici rows=3\ntenant_x.immo_beni rows=0\ntenant_x.immo_proprietari rows=5\n' > "$T/before"
printf 'tenant_x.anag_soggetti_anagrafici rows=3\ntenant_x.immo_beni rows=0\ntenant_x.immo_proprietari rows=0\n' > "$T/after"
printf 'tenant_x.anag_soggetti_anagrafici rows=2\ntenant_x.immo_beni rows=0\ntenant_x.immo_proprietari rows=0\n' > "$T/after_bad"

out="$(awk -f "$AWK" "$T/before" "$T/after")"; rc=$?
[ $rc -ne 0 ] && grep -q "RIGHE PERSE tenant_x.immo_proprietari" <<<"$out" && check ok "senza permesso la perdita blocca" || check ko "senza permesso la perdita blocca"

out="$(awk -v consentite="immo_beni immo_proprietari" -f "$AWK" "$T/before" "$T/after")"; rc=$?
[ $rc -eq 0 ] && grep -q "azzerata (consentito) tenant_x.immo_proprietari: 5 -> 0" <<<"$out" && check ok "tabella elencata: perdita consentita" || check ko "tabella elencata: perdita consentita ($out)"

out="$(awk -v consentite="immo_proprietari" -f "$AWK" "$T/before" "$T/after_bad")"; rc=$?
[ $rc -ne 0 ] && grep -q "RIGHE PERSE tenant_x.anag_soggetti_anagrafici" <<<"$out" && check ok "tabella non elencata blocca comunque" || check ko "tabella non elencata blocca comunque"

exit $fail
