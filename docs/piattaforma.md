# Piattaforma — documento tecnico-funzionale

Stato al 2026-11-10. Descrive **com'è il sistema oggi**: requisiti, regole e
comportamento della piattaforma (il "core", `backend/app/core`). I progetti
in `docs/superpowers/specs/` restano lo storico delle decisioni; qui si
rimanda a loro per i dettagli. I moduli di dominio hanno ciascuno il proprio
documento in `docs/modules/`.

Regola: chi modifica il comportamento della piattaforma aggiorna questo
documento nello stesso commit (vedi `docs/guides/SVILUPPO_CON_AGENTI_E_RAG.md`).

## 1. Principio

La piattaforma è agnostica rispetto al dominio. Fornisce autenticazione,
tenant, moduli, documenti, relazioni tra soggetti e oggetti, scadenze,
notifiche, lettura automatica dei documenti. Tutta la logica immobiliare sta
nei moduli (`backend/modules/`, `frontend/src/modules/`).

Moduli attuali: `anagrafica_italiana`, `immobili` (dipende da anagrafica),
`affitti_lungo` (immobili, anagrafica), `affitti_brevi`, `gestione_pec`,
`esempio_componenti` (dimostrativo).

Comunicazione tra moduli: servizi del core usati direttamente; tra moduli di
dominio l'API pubblica del modulo è il confine (spec
`2026-09-14-module-communication-architecture-design.md`).

## 2. Tenant

- Un tenant = uno schema PostgreSQL (`tenant_produzione`, …). Lo schema
  `public` contiene i dati di piattaforma (utenti, tenant, moduli, catalogo
  tipi documento e relazioni, comuni, categorie catastali).
- Il JWT porta `tenant_schema`; `TenantMiddleware` lo mette nella richiesta,
  `get_db()` imposta `search_path = <tenant>, public`.
- Il `search_path` impostato su una sessione viene ricordato e riapplicato a
  ogni transazione (`app/core/database.py`): una connessione del pool non
  porta mai lo schema di un'altra richiesta.
- Richieste senza utente (richiamate dei servizi esterni) devono impostare da
  sé lo schema del tenant a cui appartiene il dato (es. la richiamata di
  lettura documenti usa il tenant del lavoro).

## 3. Moduli

### 3.1 Manifest

Ogni modulo dichiara nel `__manifest__.py`: nome, versione, `dependencies`,
permessi, `document_types`, `relation_types`, ruoli. Il frontend ha il suo
`manifest.js` (rotte, menu, widget, form dei documenti).

La sincronizzazione (`scripts/sync_modules.py`, a ogni rilascio, e
all'installazione del modulo) allinea in `public`: moduli, permessi,
tipologie documentali, tipi di relazione.

### 3.2 Moduli per tenant (`core_tenant_modules`)

Un modulo può essere **attivo**, **disattivato** (tabelle e dati restano) o
**disinstallato** (con o senza cancellazione delle tabelle).

| Azione | Effetto |
|---|---|
| Disattivare / disinstallare senza cancellare le tabelle | Le relazioni CORE del modulo restano ma sono nascoste e non modificabili; le loro scadenze vengono annullate. |
| Riattivare | Le relazioni tornano visibili; le scadenze delle relazioni ancora correnti vengono riaperte. Non vengono riaperte quelle chiuse a mano dall'utente. |
| Disinstallare cancellando le tabelle | Le relazioni CORE del modulo vengono eliminate (scadenze annullate), poi si cancellano le tabelle. |
| Disattivare / disinstallare un modulo da cui dipende un modulo attivo | Rifiutato (errore 400 con il nome del modulo dipendente). |

Codice: `app/core/platform_services/relazioni_moduli.py`,
`app/core/services/tenant_module_service.py`.

### 3.3 Blocco delle API dei moduli non attivi

Le API di un modulo rispondono solo ai tenant in cui il modulo è attivo;
altrimenti 403 "Modulo X non attivo per questo tenant".

- Il modulo di una rotta si ricava dal pacchetto Python dell'endpoint, non
  dall'URL (alcuni moduli montano su `/api/v1` senza prefisso proprio).
- Rotte di piattaforma (`app.*`): mai bloccate.
- Richieste senza tenant (login, link pubblici): decide l'autenticazione
  della rotta.
- Tenant sconosciuto: 403.
- Nessuna cache: i moduli attivi si leggono a ogni richiesta (una query
  indicizzata), così la disattivazione ha effetto immediato.

Codice: `app/core/middleware/module_gate.py`.

## 4. Utenti, ruoli e permessi

- Permessi nella forma `risorsa.azione` (es. `immobile.view`), dichiarati dai
  moduli nel manifest.
- Ruoli predefiniti e permessi dei moduli:

| Ruolo | Permessi dei moduli |
|---|---|
| Admin, Platform Administrator, Tenant Administrator | tutti |
| Manager | solo `risorsa.azione` con azione in view, read, create, edit, reply, import, export (niente delete né admin) |
| Viewer | solo `risorsa.azione` con azione view o read |

- Permessi con più di due segmenti (es. `pec.audit.view`) o senza punto vanno
  solo ai ruoli di amministrazione.
- A ogni sincronizzazione i permessi dei moduli che Manager e Viewer non
  dovrebbero avere vengono revocati; i ruoli di amministrazione possono solo
  guadagnarne.
- L'avvio del backend aggiunge solo ciò che manca ai ruoli predefiniti: non
  toglie mai i permessi assegnati dalla sincronizzazione.

Codice: `app/core/auth/init_data.py`, `app/core/auth/seed_platform_permissions.py`.

Limite noto: i permessi di `affitti_brevi` non hanno il punto e quindi vanno
solo ai ruoli di amministrazione (da rinominare).

## 5. Relazioni tra soggetti e oggetti

Spec: `2026-11-10-relazioni-ruoli-soggetti-design.md`.

- Catalogo dei tipi (`public.core_ruoli_disponibili`) dai `relation_types`
  dei manifest: proprietario, conduttore, amministratore di condominio,
  ruolo in azienda, affittuario, tecnico…
- Due fonti:
  - **CORE**: relazioni in `core_relazioni` (tenant), gestite da
    `RelazioneService` (crea, aggiorna, rinnova, elimina), con eventuale
    scadenza e promemoria;
  - **MODULO**: ricavate dalle tabelle del modulo tramite un provider (es.
    proprietari da `immo_diritti_immobile`); nessuna doppia scrittura.
- API: `GET /api/v1/relazioni` (unione delle due fonti), `GET /relazioni/tipi`,
  scrittura solo per le CORE.
- **Visibilità**: un tipo di relazione si vede solo se l'utente ha il
  permesso dichiarato dal tipo (`permesso_oggetto`) e solo se il modulo del
  tipo è attivo nel tenant. Un tenant noto senza moduli attivi non vede
  nessuna relazione.
- Le anagrafiche (elenco e dettaglio) mostrano i ruoli del soggetto con le
  stesse regole di visibilità; tutte le rotte delle anagrafiche richiedono
  `soggetto.view` / `create` / `edit` / `delete`.

Limite noto: un'anagrafica con relazioni nascoste da un modulo disattivato
non si può eliminare.

## 6. Documenti

Spec: `2026-11-09-tipologie-documentali-moduli-design.md`.

- **Tipologie** dichiarate nei manifest (`document_types`), sincronizzate in
  `public.core_tipi_documento`; override per tenant possibili. Un tipo non più
  dichiarato diventa inattivo, non viene cancellato.
- Ogni tipologia ha: entità a cui si applica, **regime** (`SOSTITUTIVO`: il
  documento con data di riferimento più recente è il CORRENTE, gli altri
  vanno in storico; `CUMULATIVO`: si accumulano), sottotipi, regola di
  scadenza (nessuna / manuale / calcolata da data di riferimento), giorni di
  promemoria, form dedicato nel frontend.
- Caricamento unico del core: `POST /api/v1/documenti/upload` con tipo, data
  di riferimento, sottotipo, scadenza, `dati` (JSON confermati dall'utente) e
  più file. Nessun file viene mai sovrascritto.
- Un documento CORRENTE con scadenza crea una scadenza del core; sostituirlo
  o eliminarlo la chiude.

## 7. Lettura automatica dei documenti

Due percorsi:

1. **Nel backend, sincrono**: PDF con testo letti con `pdftotext` e
   interpretati dai lettori del modulo (oggi: import visure catastali,
   `modules/immobili/services/visura/`).
2. **Servizio esterno, asincrono**: per immagini e scansioni.
   - Orchestrazione: `DocumentParsingService`. Un lavoro
     (`core_document_jobs`) viene inviato al servizio configurato in
     `public.core_parsing_services` (HTTP o coda Redis).
   - Il servizio risponde su `POST /api/v1/document-parsing/callback/{job_uuid}?token=…`.
   - **Sicurezza**: il token è un HMAC del lavoro con `SECRET_KEY`. Senza
     token valido la richiamata riceve 403; sui lavori già conclusi riceve 409
     (nessun riuso). Il token non viene mai salvato nei log
     (`core_document_parsing_logs`).
   - La richiamata lavora nello schema del tenant del lavoro. Il risultato
     va sul lavoro e sul documento collegato; viene creata un'attività
     "da rivedere" e una notifica.
   - L'indirizzo della richiamata viene da `API_BASE_URL` (in collaudo
     `http://127.0.0.1:8001/api/v1`, nel `.env` del backend di collaudo).

Servizio MRZ (documenti d'identità): progetto separato in `~/Progetti/mrz`,
servizi utente `mrz-api` (porta 8008) e `mrz-worker` (Redis/RQ), Tesseract
con lingua italiana. Attivo in collaudo dal 2026-11-10 per il tipo
`anagrafica_italiana.*` con `parsing_service: "mrz"`. Limite noto: l'OCR
sbaglia alcuni caratteri della MRZ, quindi il risultato è sempre da rivedere.

**Modalità OCR testo** (`parsing_service: "ocr_testo"`, stesso servizio,
`POST /testo`): il chiamante manda il file e, nel campo `tipi`, una lista di
specifiche `{codice, riconosci: [espressioni], campi: {nome: espressione con
gruppo v}}`; il servizio fa l'OCR di ogni pagina e restituisce `{pagine, tipi:
[{codice, riconosciuto, campi: {nome: {valore, pagina}}}]}`; il testo completo
(`testo`) solo se richiesto con `includi_testo` (dati personali: il
gestionale non lo chiede e non lo salva). Un lavoro senza risposta dopo 30
minuti viene trattato come fallito.
Il motore che applica le specifiche è identico nel backend
(`modules/immobili/services/lettura_documenti/motore.py`) e nel servizio
(`~/Progetti/mrz/campi.py`): vanno cambiati insieme. I valori annidati della
`parsing_config` viaggiano come JSON nel form; `titolo_attivita` nella
configurazione personalizza il titolo dell'attività di revisione.

Sicurezza del servizio (dal 2026-11-10): ascolta solo su 127.0.0.1; accetta
solo PDF e immagini; manda le richiamate solo agli host in
`MRZ_CALLBACK_HOSTS` (predefinito 127.0.0.1, localhost); al massimo 20
specifiche, 40 espressioni, 500 caratteri ciascuna, 600 s per lavoro; le
immagini di debug solo con `MRZ_DEBUG` lato server. Il servizio ha un suo
repository git locale in `~/Progetti/mrz`; i documenti personali presenti in
quella cartella sono esclusi da `.gitignore`.

Pagina di debug per gli amministratori: `/admin/document-parsing-debug`.

## 8. Scadenze e notifiche

- Scadenziario del core (`core_scadenze`): scadenze collegate a entità,
  documenti, relazioni, lavori di lettura; stati ATTIVA, COMPLETATA,
  CANCELLATA. Documentazione: `docs/features/SCADENZARIO*.md`.
- Notifiche e promemoria: spec `2026-09-14-notification-service-design.md`.

## 9. Ambienti e rilascio

- Sviluppo: `~/test/gestione-affitti`, backend sulla porta 8000.
- "Produzione" = collaudo personale dell'utente: `~/apps/gestione-affitti-stable`,
  backend sulla porta 8001 (servizio utente `gestione-affitti-backend`),
  frontend servito da Apache, DB `gestione_affitti_prod`. In
  `tenant_produzione` ci sono i dati reali dell'utente.
- Rilascio con `scripts/promote.sh`:
  1. fotografia delle righe per tabella prima;
  2. backup in `~/apps/gestione-affitti-backups`;
  3. migrazioni Alembic e sincronizzazione moduli;
  4. fotografia dopo e confronto: se mancano righe si ferma e lascia il
     backend spento;
  5. avvio del backend, `/health`;
  6. nuova fotografia dopo l'avvio e confronto.

  Il controllo blocca anche le cancellazioni volute (es. revoca di permessi):
  in quel caso si verifica a mano e si riavvia il backend. Per un
  azzeramento deciso dall'utente si lancia
  `PROMOTE_PERDITA_CONSENTITA="tab1 tab2 …" scripts/promote.sh`: solo quelle
  tabelle (nomi senza schema) possono perdere righe, riportate come
  "azzerata (consentito)"; in un terminale chiede conferma. Test del
  confronto: `scripts/tests/test_confronta_snapshot.sh`.
- Agenti e pipeline: `docs/guides/SVILUPPO_CON_AGENTI_E_RAG.md`.

## 10. Limiti e attività note

- Il database di collaudo segnala collation version mismatch (glibc 2.42 →
  2.43): gli indici sui testi vanno ricostruiti (`REINDEX` +
  `ALTER DATABASE … REFRESH COLLATION VERSION`), con backup.
- Permessi di `affitti_brevi` senza punto (vedi 4).
- Anagrafica non eliminabile se ha relazioni nascoste (vedi 5).
- **Interfaccia comune** (revisione del 2026-11-10):
  - icone: `components/Navigation/iconRegistry.jsx`; un test controlla che
    ogni icona dichiarata nei manifest (frontend e backend) sia registrata; un
    nome sconosciuto mostra un'icona neutra (e un avviso in sviluppo), un
    emoji resta testo;
  - widget della dashboard: si registrano con `widgetRegistry.registerWidget`
    nell'`index.js` del modulo, non con `registerModuleComponent`;
  - `useEntityCRUD.fetchAll` ignora le richieste annullate da una più recente;
  - la regola globale su `button` in `index.css` (padding, sfondo blu) colpisce
    ogni pulsante senza stile proprio: usare `Button` di `components/UI`; i
    pulsanti-icona devono azzerare il padding. Togliere la regola globale
    richiede di migrare prima le pagine vecchie.
