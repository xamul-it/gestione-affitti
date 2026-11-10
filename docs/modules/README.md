# Documentazione dei moduli

Un documento vivo per modulo, `docs/modules/<modulo>.md`: requisiti, regole di
dominio, funzioni, documenti, limiti noti. Descrive com'è il modulo **oggi** e
si aggiorna nello stesso commit del codice. La piattaforma è in
[`../piattaforma.md`](../piattaforma.md).

| Modulo | Documento |
|---|---|
| immobili | [immobili.md](immobili.md) |
| anagrafica_italiana | da creare al prossimo lavoro sul modulo |
| affitti_lungo | da creare al prossimo lavoro sul modulo |
| affitti_brevi | da creare (materiale esistente in `backend/modules/affitti_brevi/*.md`) |
| gestione_pec | da creare (piano in [GESTIONE_PEC_PLAN.md](GESTIONE_PEC_PLAN.md)) |

`scripts/controlla_documentazione.sh` (lanciato al rilascio) segnala il codice
di un modulo cambiato senza aggiornare il suo documento.
