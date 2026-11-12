# Confronta due fotografie di db_snapshot.sql (prima, dopo) per promote.sh.
# Errore (exit 1) se una tabella sparisce o perde righe; le versioni alembic
# e le tabelle/righe nuove sono solo riportate. Con -v consentite="t1 t2"
# (nomi senza schema) la perdita di righe di quelle tabelle e' voluta
# (es. un azzeramento deciso dall'utente) e viene solo riportata.
BEGIN { n = split(consentite, c, /[ ,]+/); for (i = 1; i <= n; i++) if (c[i] != "") ok[c[i]] = 1 }
NR == FNR { before[$1] = $2; next }
{ after[$1] = $2 }
END {
    bad = 0
    for (t in before) {
        if (!(t in after)) { print "  PERSA tabella " t " (" before[t] ")"; bad = 1; continue }
        if (before[t] ~ /^rows=/) {
            b = substr(before[t], 6) + 0; a = substr(after[t], 6) + 0
            nome = t; sub(/^[^.]*\./, "", nome)
            if (a < b) {
                if (nome in ok) print "  azzerata (consentito) " t ": " b " -> " a
                else { print "  RIGHE PERSE " t ": " b " -> " a; bad = 1 }
            }
            else if (a > b) print "  righe aggiunte " t ": " b " -> " a
        } else if (before[t] != after[t]) print "  migrata " t ": " substr(before[t], 9) " -> " substr(after[t], 9)
    }
    for (t in after) if (!(t in before)) print "  nuova tabella " t
    exit bad
}
