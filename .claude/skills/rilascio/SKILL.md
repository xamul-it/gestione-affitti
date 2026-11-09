---
name: rilascio
description: Rilascia su "produzione" (collaudo personale) una modifica già testata - commit, merge in master, push, scripts/promote.sh e resoconto. Usala dopo che i test della modifica sono passati, o quando l'utente chiede di rilasciare, aggiornare produzione o promuovere.
model: haiku
---

# Rilascio in produzione

"Produzione" è `~/apps/gestione-affitti-stable` (DB `gestione_affitti_prod`, porta 8001). La usa solo l'utente, come collaudo e per uso personale: non serve chiedere conferma per commit, push e promozione. La preservazione dei dati invece non si discute mai.

In quel DB, **`tenant_produzione` contiene i dati reali dell'utente**. Deve restare pulito e ricevere tutte le funzionalità, moduli compresi. Gli altri tenant (`tenant_principale`, `tenant_qa_test`) sono di prova. Non scrivere mai a mano in `tenant_produzione`, nemmeno per "verificare" qualcosa.

## Prima di iniziare

La modifica deve aver passato `scripts/verifica.sh` in questa sessione con `ESITO: VERDE`, di solito tramite l'agente `verifica-test`. Se non è così, o se l'esito era ROSSO, fermati e dillo, senza rilasciare. Non esistono fallimenti noti tollerati: la suite completa deve essere verde.

## Passi

1. **Commit.** `git status`, poi committa solo i file della modifica. Le modifiche non committate dell'utente che non c'entrano restano fuori: non usare `git add -A` o `git add .`. Messaggio in stile conventional commit (`feat(modulo): ...`, `fix(...)`), con le righe di attribuzione richieste dalla sessione.
2. **Master.** Se sei su un branch di feature: `git checkout master && git merge --ff-only <branch>`. Se il fast-forward non è possibile, fermati e riporta. Non fare rebase e non usare force.
3. **Push.** `git push origin master`. Se viene rifiutato, fermati: non usare force.
4. **Promozione.** Dalla radice del repo lancia `scripts/promote.sh master` con timeout di 10 minuti. Lo script:
   - ferma il backend, fotografa il DB e fa il backup, verificando che il dump sia completo;
   - esegue le migrazioni core su tutti gli schema;
   - con `backend/scripts/sync_modules.py`, esegue le migrazioni dei moduli e carica i dati di base pubblici;
   - confronta le righe di ogni tabella prima e dopo, riavvia il backend e controlla `/health`.
5. **Leggi l'output.** Cerca:
   - `backup verificato:` con il percorso del backup;
   - le righe `migrata ...`, che indicano gli schema aggiornati;
   - `nessuna tabella o riga persa`;
   - le righe `ATTENZIONE`;
   - `backend attivo, /health ok`.

## Se qualcosa fallisce

- Lo script stampa `ERRORE` ed esce con codice diverso da 0. **Non ripristinare il backup e non rilanciare per tentativi.** Riporta all'utente l'errore esatto, se il backend è fermo e il comando di ripristino stampato dallo script. Decide l'utente.
- Un errore prima della migrazione lascia il DB intatto e riavvia il backend. Riportalo comunque.
- Non modificare mai a mano il DB di produzione per far passare il rilascio.

## Cose note, non sono errori

- `==> Installazione moduli abilitati ma mai installati` seguito da righe `<modulo> -> <tenant>`: `sync_modules.py` sta installando su quel tenant un modulo abilitato ma senza tabelle. È voluto. Le tabelle nuove compaiono come `nuova tabella` nel confronto.
- `ATTENZIONE: modulo <x> in stato 'broken', saltato`: il modulo è segnato come rotto nel registro. Riportalo nel resoconto.
- `WARNING: database ... versione di confronto non corrispondente` di psql: riguarda la collation del DB, non il rilascio.
- Qualunque errore nei log del backend su `tenant_produzione` dopo il riavvio va riportato. Da quando i moduli sono installati su tutti i tenant, non ce ne sono più di noti.

## Resoconto finale (in italiano, breve)

- cosa è stato rilasciato: commit, da `<vecchio>` a `<nuovo>`, e una riga di riassunto;
- percorso del backup;
- schema e moduli migrati, cioè le righe `migrata`, oppure "nessuna migrazione";
- tabelle o righe nuove, se ci sono;
- avvisi nuovi, cioè diversi da quelli noti qui sopra;
- cosa resta da provare a mano dal browser, se la modifica riguarda l'interfaccia.
