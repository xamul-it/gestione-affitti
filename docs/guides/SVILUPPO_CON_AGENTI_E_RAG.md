# Sviluppo di nuove funzioni: pipeline con agenti e Archivio Fiscale (RAG)

Stato al 2026-11-10. Questo documento serve per riprendere lo sviluppo da una
sessione nuova: come si lavora, con quali strumenti, cosa resta aperto.

## 1. Ruoli e ambienti

- **L'utente** chiede le funzioni quando gli servono e le **collauda usandole
  in produzione**. **Claude** segue lo sviluppo e i test, e quando sono verdi
  porta tutto in produzione senza chiedere conferma.
- **Sviluppo**: questo repository (`~/test/gestione-affitti`), DB
  `gestione_affitti`, backend su :8000, frontend su :3000.
- **Produzione** (collaudo e uso personale): worktree
  `~/apps/gestione-affitti-stable`, DB `gestione_affitti_prod`, backend :8001
  (servizio systemd `gestione-affitti-backend`), frontend servito da Apache.
- **`tenant_produzione` in produzione contiene i dati reali dell'utente**: deve
  restare pulito e ricevere ogni funzionalità, moduli compresi. Gli altri
  tenant (`tenant_principale`, `tenant_qa_test`) sono di prova.
- Immobili a **Bologna** (Emilia-Romagna), **Pré-Saint-Didier** (Valle
  d'Aosta) e **Castiglione della Pescaia** (Toscana): per le regole locali
  contano queste tre amministrazioni.

## 2. La pipeline

Il giudizio resta alla sessione principale, che ha il contesto. Il lavoro
meccanico e ripetibile va ad agenti economici guidati da script.

| Fase | Chi | Modello |
|---|---|---|
| Analisi dei requisiti | sessione principale + `search_docs` (Archivio Fiscale); ricerche lunghe con l'agente `esperto-gestione-immobiliare-ita` | Sonnet |
| Progettazione | sessione principale: spec in `docs/superpowers/specs/`, piano per le cose grandi | — |
| Sviluppo con TDD | sessione principale; sottoagenti in parallelo solo per compiti indipendenti | Sonnet |
| Documentazione | sessione principale, nello stesso commit del codice: `docs/piattaforma.md` e `docs/modules/<modulo>.md` (requisiti, regole, comportamento attuale, limiti) | — |
| Revisione UI/UX | agente `revisione-ux`, se la modifica tocca l'interfaccia | Sonnet |
| Revisione del codice | revisore, per le modifiche medie e grandi | Sonnet |
| Test | agente `verifica-test` → `scripts/verifica.sh` | Haiku |
| Rilascio | agente `rilascio` → commit, push, `scripts/promote.sh`; segnala con `scripts/controlla_documentazione.sh` il codice cambiato senza documento aggiornato (avviso, non blocca) | Haiku |
| Bachi su dati reali | `scripts/replica_produzione.sh` + sessione principale | — |
| Collaudo | l'utente | — |

**Percorsi in base alla dimensione della richiesta**
- *Piccola* (correzione, ritocco): sviluppo → `verifica-test` → `rilascio`.
- *Media* (funzione nuova in un modulo esistente): sviluppo → documentazione →
  revisione (+ `revisione-ux` se c'è interfaccia) → `verifica-test` → `rilascio`.
- *Grande* (modulo nuovo, come l'import visure): spec approvata dall'utente →
  piano → sviluppo → documentazione → UX → revisione → `verifica-test` →
  `rilascio`.

Niente sottoagenti su Opus senza chiedere (costo).

## 3. Agenti del progetto (`.claude/agents/`)

| Agente | Cosa fa | Non fa |
|---|---|---|
| `esperto-gestione-immobiliare-ita` | cerca nell'Archivio Fiscale, cita le fonti, traduce le norme in **regole per il software** distinguendo nazionale, regionale e comunale | non risponde dalla memoria senza dichiararlo |
| `revisione-ux` | confronta le modifiche al frontend con token (`frontend/src/styles/tokens.css`), componenti `components/UI` e `core/components`, `docs/ux/UX_GUIDELINES.md`, accessibilità; esito `OK` / `DA CORREGGERE` con file:riga | non modifica file |
| `verifica-test` | esegue `scripts/verifica.sh` e riporta `ESITO: VERDE/ROSSO` con i test falliti | non corregge e non rilancia per tentativi |
| `rilascio` | commit dei file indicati, merge ff in master, push, `promote.sh`, controllo documentazione, resoconto | non ripristina backup, non scrive mai in `tenant_produzione`, non scrive documentazione |

Si chiamano per nome solo dalla sessione successiva a quella in cui sono stati
creati o modificati. C'è anche la skill `/rilascio` per un rilascio manuale.

## 4. Strumenti

- **`scripts/verifica.sh [all|backend|frontend]`**: suite backend completa
  (unitari + integrazione su PostgreSQL), vitest, build. È **ROSSO** anche se i
  test lasciano righe nel DB di sviluppo o file in `backend/storage`. Al
  2026-11-09: 223 test backend (2 saltati), 33 frontend. Non ci sono
  fallimenti "noti" tollerati.
- **`scripts/promote.sh`** (produzione):
  1. archivia `backend/storage`, cioè i documenti caricati, che non stanno nel
     dump;
  2. aggiorna il codice (fast-forward) e si ferma se manca un file;
  3. ferma il backend, fa il backup verificato del DB e fotografa le righe di
     ogni tabella;
  4. esegue le migrazioni core e quelle dei moduli
     (`backend/scripts/sync_modules.py`, che installa anche i moduli abilitati
     ma mai installati e carica i seed pubblici);
  5. **si ferma se una tabella o una riga sparisce**; poi riavvia e controlla
     `/health`.

  Backup in `~/apps/gestione-affitti-backups` (mai dentro i worktree).
- **`scripts/replica_produzione.sh`**: copia schema, dati e documenti del
  `tenant_produzione` di produzione nel `tenant_produzione` di sviluppo, che è
  quindi una copia sacrificabile. Prima fa un backup, poi applica le migrazioni
  del codice di sviluppo. Serve per riprodurre bachi su dati reali, fare prove
  distruttive e provare le migrazioni sui dati veri. Legge da produzione senza
  scrivere. **Non è ancora mai stato eseguito.**

**Test di integrazione**: usano `tests/integration/conftest.py`, cioè
PostgreSQL reale dentro una transazione annullata alla fine. Il `get_db`
sostituito segue il tenant del token. I nuovi test scritti così non lasciano
dati.

## 5. Archivio Fiscale (RAG)

- **DocsGPT** in `~/containers/docsgpt`: pgvector, embedding
  `granite-embedding-311m-multilingual-r2` su GPU, ricerca ibrida.
- Esposto come connettore claude.ai **"Archivio Fiscale"** con un solo
  strumento: `search_docs(query, keywords, max_documents)`.
  - `query`: domanda in linguaggio tecnico;
  - `keywords`: riferimenti esatti ("articolo 13-ter", "L. 431/1998",
    "circolare 12/E");
  - fare 2-4 ricerche, guardare sempre la data, citare i link.
- **Contenuti**: circa 185 mila documenti fiscali e normativi (CeDEF, Agenzia
  delle Entrate, MEF, ADM, giurisprudenza) più 10 sorgenti **Locazioni**
  (61 documenti): nazionale affitti brevi e lungo termine; regioni
  Emilia-Romagna, Valle d'Aosta e Toscana; comuni di Bologna (con l'accordo
  territoriale 2024 completo), Pré-Saint-Didier e Castiglione della Pescaia;
  piattaforme; servizi PA.
- **Codice dell'estensione**: repository
  [`xamul-it/docsgpt-loader-it`](https://github.com/xamul-it/docsgpt-loader-it)
  (`loader/`, `notifier/`, `patches/`, `sql/`). L'elenco curato delle fonti
  sulle locazioni è `loader/fonti/locazioni.yaml`: si scaricano solo le voci
  con `verificato: "si"`.
- **Aggiornamento automatico** (container `notifier`): ogni 6 ore refresh degli
  enti, comprese le locazioni, delle quali riconfronta lo sha256; il 1° del mese
  ricarica tutto su DocsGPT. I documenti nuovi arrivano per email.
- **Aggiungere una fonte**:
  1. aggiungere la voce a `locazioni.yaml` e verificarla;
  2. `python3 downloader.py --target /mnt/Multimedia/circolari --source locazioni/<id> --mode refresh`;
  3. `python3 carica_docsgpt.py --target /mnt/Multimedia/circolari --source locazioni/<id> --replace --agent "Claude - archivio fiscale"`.

  Le fonti curate si presentano con lo User-Agent onesto `docsgpt-loader-it`:
  i siti istituzionali rifiutano quello "da browser".
- Il 2026-11-09 è stata aggiunta la colonna `tsv_it` (`sql/2026-11-09_tsv_it.sql`):
  la ricerca per parole chiave sulle sorgenti grandi passa da oltre 8 s, con
  timeout e nessun risultato, a meno di 0,4 s.

## 6. Come iniziare una nuova funzione (checklist)

1. Capire la richiesta: cosa serve, per quale immobile o tenant, da quando.
2. Se tocca norme, fisco o adempimenti: `search_docs` (o l'agente esperto) e
   scrivere le regole con le fonti nella spec.
3. Scegliere il percorso (piccola, media o grande); per le grandi far
   approvare la spec.
4. TDD: test che fallisce → codice → test verde.
5. Aggiornare `docs/piattaforma.md` e/o `docs/modules/<modulo>.md` (crearlo se è
   il primo lavoro sul modulo) con requisiti e comportamento implementato.
6. `revisione-ux` se c'è interfaccia; revisione per medie e grandi.
7. `verifica-test` → solo se VERDE, `rilascio`.
8. Comunicare all'utente cosa collaudare e dove.

Se qualcosa va in errore sui dati reali: `replica_produzione.sh`, riprodurre in
sviluppo, test che fallisce, correzione, pipeline normale. Mai correggere a
mano in produzione.

## 7. Attività aperte al 2026-11-10

**Da fare con l'utente**
- Prima esecuzione di `scripts/replica_produzione.sh`: il sistema dei permessi
  ne ha bloccato l'esecuzione automatica. Sostituisce anche le righe di test
  rimaste nel `tenant_produzione` di sviluppo.
- Due foto (probabili documenti d'identità) committate in passato restano
  nella **storia** git del gestionale su GitHub: per eliminarle serve
  riscrivere la storia e fare un force push.
- `gh auth login`, poi aprire su `docsgpt-loader-it` la issue sulla protezione
  di `/docs` (CSP sandbox, escape dei titoli).

**Da collaudare in produzione**
- Relazioni e ruoli dei soggetti (visibilità per permessi e per moduli
  attivi), blocco delle API dei moduli non attivi, permessi Manager/Viewer:
  vedi `docs/piattaforma.md` §3–5.
- Lettura MRZ dei documenti d'identità dalla scheda del soggetto (servizio
  `mrz-api`/`mrz-worker` attivo dal 2026-11-10).
- Import visure catastali ("Carica da documento" nelle unità immobiliari).
- Pagine Login, Impostazioni e Gestione database (design system, toast,
  dialoghi di conferma).
- Moduli affitti brevi, affitti lungo e PEC su `tenant_produzione`, installati
  il 2026-11-09. Esempio componenti è disabilitato.

**Sviluppo e dominio**
- Caricamento unico dei documenti degli immobili: spec
  `docs/superpowers/specs/2026-11-10-caricamento-unico-documenti-immobili-design.md`
  in attesa di approvazione; comprende la modalità "OCR testo + ricerca campi"
  del servizio in `~/Progetti/mrz`.
- Documentazione viva: `docs/piattaforma.md` e `docs/modules/immobili.md`
  esistono; gli altri moduli (anagrafica, affitti lungo/brevi, PEC) si
  documentano in `docs/modules/` al primo lavoro su ciascuno.
- DB di collaudo: collation version mismatch (glibc 2.42 → 2.43), indici sui
  testi da ricostruire con backup.
- Permessi di `affitti_brevi` senza punto (solo ruoli admin): da rinominare.
- `~/Progetti/mrz` contiene documenti personali reali accanto al codice: da
  spostare in una cartella separata.
- **D.Lgs. 19 giugno 2026, n. 117**: secondo Normattiva abroga gran parte
  dell'art. 4 DL 50/2017 (locazioni brevi). Va studiato con l'Archivio:
  impatta il modulo affitti brevi.
- Difetto noto nel servizio di somiglianza (nessuna azione consigliata per
  punteggi tra 0,50 e 0,70): test saltato in
  `tests/unit/test_modules/test_anagrafica_unit/test_similarity_service.py`.
- Problemi minori dell'import visure, elencati nella spec
  `docs/superpowers/specs/2026-10-30-import-visure-catastali-design.md` e nel
  messaggio di chiusura di quel lavoro: persona fisica senza CF salvata come
  ente, nomi tutti maiuscoli, sezione urbana ignorata, duplicati non rilevati,
  e altri.

**Archivio**
- Fonti ancora mancanti: regolamento dell'imposta di soggiorno di
  Pré-Saint-Didier (la vecchia URL dà 404), pagine di aiuto Airbnb (solo
  JavaScript), Booking (403), portali con login (BDSR, Alloggiati Web, RLI),
  delibere sui limiti alle locazioni brevi a Bologna e Castiglione.
- Facoltativo: togliere il vecchio indice `documents_text_fts_it_idx` di
  DocsGPT, non più usato, per recuperare spazio.
