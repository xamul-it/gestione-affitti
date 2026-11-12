# Beni catastali — Fase 1: bene comune — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Introdurre `immo_beni` come entità comune di cui l'unità immobiliare è specializzazione (stesso id), spostare diritti, assegnazioni conduttore, variazioni catastali e spese ricorrenti su `bene_id`, azzerando i dati del modulo come deciso dall'utente.

**Architecture:** Una migrazione tenant del modulo immobili azzera i dati (TRUNCATE esplicito, niente CASCADE) e ristruttura le tabelle; in SQLAlchemy `UnitaImmobiliare` eredita da `Bene` (joined-table inheritance, `polymorphic_on=tipo_bene`). Le API figlie passano a `bene_id`; il frontend segue. `promote.sh` impara a consentire perdite di righe solo per tabelle elencate esplicitamente.

**Tech Stack:** FastAPI, SQLAlchemy, Alembic (migrazioni di modulo in raw SQL), PostgreSQL multi-schema, React + Vitest, bash.

**Spec:** `docs/superpowers/specs/2026-11-10-beni-catastali-design.md` (sezioni "Modello", "Dati esistenti", "Piano a fasi" punto 1).

## Global Constraints

- Lo stesso id identifica il bene e la sua unità: `immo_unita_immobiliari.id` è PK **e** FK → `immo_beni.id ON DELETE CASCADE`, senza sequenza propria.
- `immo_beni` colonne: `id SERIAL PK, tipo_bene VARCHAR(10) NOT NULL CHECK (tipo_bene IN ('UNITA','TERRENO')), codice VARCHAR(50) NOT NULL UNIQUE, comune_codice VARCHAR(4), comune VARCHAR(100), provincia VARCHAR(2), indirizzo VARCHAR(255), cap VARCHAR(10), sezione VARCHAR(20), foglio VARCHAR(20), particella VARCHAR(20), denominatore VARCHAR(20), subalterno VARCHAR(20), partita VARCHAR(20), descrizione TEXT, note TEXT, attivo BOOLEAN NOT NULL DEFAULT TRUE, created_at TIMESTAMPTZ NOT NULL DEFAULT now(), updated_at TIMESTAMPTZ`.
- Colonne che lasciano `immo_unita_immobiliari` (passano al bene): `codice, indirizzo, citta(→comune), cap, provincia, foglio, particella, subalterno, descrizione, note`. Restano sull'unità: `tipo, condominio_id, superficie_mq, locali, piano, classe_energetica, rendita_catastale, categoria_catastale_id, codice_auto_generated, indirizzo_parsed_warnings, created_at, updated_at`.
- L'API delle unità non cambia forma: `citta` resta il nome esposto (`synonym("comune")`); `indirizzo` e `citta` restano obbligatori negli schemi Pydantic dell'unità.
- Restano su `unita_immobiliare_id` (non toccare): certificati energetici, millesimi, tutte le tabelle `affitti_brevi`, `affitti_lungo` (contratti, spese, ripartizioni — fase 3).
- `immo_terreni` non cambia struttura in questa fase (fase 2); viene solo svuotata.
- Azzeramento, tabelle (solo se esistono nello schema): `immo_diritti_immobile, immo_assegnazioni_conduttore, immo_variazioni_catastali, immo_spese_ricorrenti, immo_certificati_energetici, immo_millesimi_unita, immo_tabelle_millesimali, immo_proprietari, immo_conduttori, immo_terreni, immo_unita_immobiliari, immo_condomini, ripartizioni_spese, incassi, spese, contratti, ab_ospiti_soggiorni, ab_tasse_soggiorni, ab_comunicazioni, ab_soggiorni, ab_prenotazioni, ab_blocchi_calendario, ab_calendari_canali`. Righe core da eliminare: `core_documenti`, `core_scadenze`, `core_relazioni` con `lower(entity_type) IN ('immobile','condominio','spesa_ricorrente','contratto','comunicazione')` (figli in cascata: `core_documenti_files`, `core_scadenza_destinatari`, `core_scadenza_log`). I file nello storage restano.
- Restano intatti: `anag_*`, `affittuari`, `tecnici`, `ab_canali`, `ab_tasse_soggiorno_config/_scaglioni`, tabelle `public`, override e configurazioni.
- Il commit va con la riga `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`; mai committare `deploy/`, `docs/visure/`, `notifiche-followup-fix-report.md`.

## Review Focus

1. Tenant senza `affitti_brevi` o `affitti_lungo` installati: l'azzeramento salta le tabelle assenti invece di fallire → test in Task 2.
2. Soggetti dell'anagrafica e i loro documenti/scadenze sopravvivono all'azzeramento → test in Task 2.
3. Creare/modificare un'unità via API con `citta` funziona e la risposta riporta `citta`; la ricerca/filtri per città continuano a funzionare → test in Task 3.
4. Cancellare un'unità elimina anche la riga del bene, i diritti, le assegnazioni e le spese ricorrenti → test in Task 3 (aggiorna `test_unita_immobiliare_cascade_delete.py`).
5. Le etichette `IMMOBILE` (documenti, relazioni, scadenzario) si risolvono dal bene dopo che indirizzo e città hanno lasciato l'unità → test in Task 4 (`test_relazioni_query.py`).

---

### Task 1: `promote.sh` consente perdite di righe solo se elencate

**Files:**
- Create: `scripts/sql/confronta_snapshot.awk`
- Create: `scripts/tests/test_confronta_snapshot.sh`
- Modify: `scripts/promote.sh` (funzione `confronta`, righe ~154-172)

**Interfaces:**
- Produces: variabile d'ambiente `PROMOTE_PERDITA_CONSENTITA` — nomi di tabella senza schema, separati da spazio. Una tabella elencata che perde righe viene riportata come `  azzerata (consentito) <schema.tabella>: B -> A` e non fa fallire; tutte le altre regole restano.

- [ ] **Step 1: test** `scripts/tests/test_confronta_snapshot.sh`: crea in una cartella temporanea `before.txt` (`tenant_x.immo_beni rows=0`, `tenant_x.immo_proprietari rows=5`, `tenant_x.anag_soggetti_anagrafici rows=3`) e `after.txt` (`immo_proprietari rows=0`, resto uguale). Asserisce: senza variabile → exit ≠ 0 e output contiene `RIGHE PERSE tenant_x.immo_proprietari`; con `-v consentite="immo_proprietari"` → exit 0 e output contiene `azzerata (consentito)`; con `consentite="immo_proprietari"` ma `anag_soggetti_anagrafici rows=2` in after → exit ≠ 0.
- [ ] **Step 2:** `bash scripts/tests/test_confronta_snapshot.sh` → FAIL (file awk mancante).
- [ ] **Step 3:** sposta il corpo awk di `confronta` in `scripts/sql/confronta_snapshot.awk`, con `-v consentite="$PROMOTE_PERDITA_CONSENTITA"` (match sul nome dopo il primo punto). In `promote.sh`, se la variabile è valorizzata, stampa all'inizio `==> Perdita di righe consentita per: …` e chiede conferma solo se il terminale è interattivo (`[ -t 0 ]`).
- [ ] **Step 4:** test → PASS; `bash -n scripts/promote.sh` → nessun errore.
- [ ] **Step 5:** commit `chore(promote): allow listed tables to lose rows on purpose`.

### Task 2: migrazione — azzeramento e struttura del bene

**Files:**
- Create: `backend/modules/immobili/migrations/2026111201_beni.py` (revision `2026111201_beni`, down_revision `2026110902_ape_migrato`, `target_schema = "tenant"`, salta `public` come le altre)
- Test: `backend/tests/integration/test_modules/test_immobili/test_migrazione_beni.py`

**Interfaces:**
- Produces: nel modulo di migrazione, `TABELLE_AZZERATE: tuple[str, ...]` (ordine del vincolo globale), `ENTITY_TYPES_AZZERATI: tuple[str, ...]`, `azzera(conn) -> dict[str, int]` (tabella → righe tolte; solo tabelle esistenti, via `to_regclass`), `ristruttura(conn) -> None`. `upgrade()` = `azzera` + `ristruttura`; `downgrade()` solleva `NotImplementedError("ripristinare dal backup di promote.sh")`.
- `ristruttura`: crea `immo_beni` (vincolo globale) + indici su `(foglio, particella)` e `comune_codice`; su `immo_unita_immobiliari` toglie le colonne spostate, toglie il default/sequence dell'id, aggiunge `FOREIGN KEY (id) REFERENCES immo_beni(id) ON DELETE CASCADE`; su diritti, assegnazioni, variazioni, spese ricorrenti rinomina `unita_immobiliare_id` → `bene_id`, sostituisce la FK con `REFERENCES immo_beni(id) ON DELETE CASCADE`, rinomina gli indici `*_unita*` in `*_bene*`; ricrea il CHECK di `immo_spese_ricorrenti` (esattamente uno tra `bene_id` e `condominio_id`).
- `TRUNCATE` senza `CASCADE`: se una tabella che punta a quelle azzerate non è in lista, la migrazione fallisce invece di svuotare tabelle non previste.

- [ ] **Step 1: test** (carica il file con `importlib.util.spec_from_file_location`, lavora su `pg_session`, cioè `tenant_qa_test` nella transazione annullata a fine test):
  - `test_struttura_beni`: `information_schema` → `immo_beni` esiste; `immo_unita_immobiliari` non ha `indirizzo`, `citta`, `codice`; `immo_diritti_immobile`, `immo_assegnazioni_conduttore`, `immo_variazioni_catastali`, `immo_spese_ricorrenti` hanno `bene_id` e non `unita_immobiliare_id`; FK di `immo_unita_immobiliari.id` → `immo_beni`.
  - `test_azzera_svuota_beni_e_lascia_anagrafica`: inserisce un soggetto, un bene+unità, un diritto, un documento `IMMOBILE` e uno `SOGGETTO_ANAGRAFICO`; `azzera(conn)` → unità, diritto e documento IMMOBILE spariti; soggetto e suo documento presenti; il risultato riporta `immo_unita_immobiliari: 1`.
  - `test_azzera_salta_tabelle_assenti`: `DROP TABLE ab_ospiti_soggiorni` dentro la transazione, poi `azzera(conn)` non solleva e la chiave non compare nel risultato.
- [ ] **Step 2:** `cd backend && pytest tests/integration/test_modules/test_immobili/test_migrazione_beni.py -v` → FAIL.
- [ ] **Step 3:** scrivi la migrazione (raw SQL come `2026110901_variazioni_catastali.py`). Aggiungi `immo_beni` alle liste tabelle di `backend/modules/immobili/__manifest__.py` (righe ~119, ~138), di `backend/app/core/services/tenant_module_service.py:48` e alla docstring di `migrations/__init__.py`.
- [ ] **Step 4:** applica in sviluppo: `cd backend && alembic -x schema=all upgrade head && python scripts/sync_modules.py`; poi il test → PASS (struttura) e i test di azzeramento PASS.
- [ ] **Step 5:** commit `feat(immobili): immo_beni table and data reset for the common asset`.

### Task 3: modelli ORM — `Bene` e unità come specializzazione

**Files:**
- Create: `backend/modules/immobili/models/bene.py`
- Modify: `backend/modules/immobili/models/{__init__,unita_immobiliare,diritti_immobile,assegnazione_conduttore,variazioni_catastali,spesa_ricorrente}.py`
- Test: `backend/tests/integration/test_modules/test_immobili/test_bene_model.py`, aggiorna `test_unita_immobiliare_cascade_delete.py`

**Interfaces:**
- Produces: `class Bene(Base)` (`__tablename__ = "immo_beni"`, colonne del vincolo globale, `__mapper_args__ = {"polymorphic_on": tipo_bene}`, relazioni `diritti`, `assegnazioni_conduttore`, `variazioni_catastali`, `spese_ricorrenti` con `cascade="all, delete-orphan"`/`passive_deletes=True` come oggi sull'unità). `class UnitaImmobiliare(Bene)` (`id = Column(ForeignKey("immo_beni.id", ondelete="CASCADE"), primary_key=True)`, `polymorphic_identity="UNITA"`, `citta = synonym("comune")`). Modelli figli: attributo `bene_id` e relazione `bene` (back_populates sulle relazioni di `Bene`).
- `Bene` esportato da `immobili.models`.

- [ ] **Step 1: test**
  - `test_unita_crea_bene_con_lo_stesso_id`: `UnitaImmobiliare(codice="U-1", tipo="Appartamento", indirizzo="Via A 1", citta="Forlì")` → flush → riga in `immo_beni` con stesso id, `tipo_bene == "UNITA"`, `comune == "Forlì"`.
  - `test_filtro_per_citta`: `db.query(UnitaImmobiliare).filter(UnitaImmobiliare.citta == "Forlì").count() == 1`.
  - `test_cancellare_unita_cancella_bene_e_figli` (in `test_unita_immobiliare_cascade_delete.py`): unità + diritto + assegnazione + spesa ricorrente; `db.delete(unita)`; flush → nessuna riga in `immo_beni`, diritti, assegnazioni, spese per quell'id.
  - `test_api_unita_risponde_con_citta`: chiama la route di creazione unità di `routes/immobili.py` con payload come oggi → risposta con `citta == "Forlì"`.
- [ ] **Step 2:** pytest su questi file → FAIL.
- [ ] **Step 3:** implementa i modelli secondo l'Interfaces block.
- [ ] **Step 4:** test → PASS.
- [ ] **Step 5:** commit `feat(immobili): Bene model with UnitaImmobiliare as joined subclass`.

### Task 4: backend — tutto il modulo su `bene_id`

**Files:**
- Modify: `backend/modules/immobili/schemas/{diritti_immobile,assegnazione_conduttore,spesa_ricorrente}.py`, `routes/{diritti_immobile,assegnazioni_conduttore,spese_ricorrenti,immobili}.py`, `services/{variazioni_catastali,visura_import_service,migrazione_ape}.py`, `relations.py`, `__init__.py` (`_immobile_labels`), `seeds/seed_tenant.py`
- Modify: `backend/app/core/platform_services/relazioni_query.py:28`, `relazione_service.py:27`
- Test: aggiorna i 15 file in `backend/tests` che usano `unita_immobiliare_id` per queste quattro tabelle (lista: `grep -rl unita_immobiliare_id backend/tests`); i test di affitti_brevi/certificati/millesimi restano su `unita_immobiliare_id`.

**Interfaces:**
- Produces (contratto per il frontend, Task 5):
  - campi `bene_id` (al posto di `unita_immobiliare_id`) in create/update/response di diritti, assegnazioni, spese ricorrenti;
  - `GET /diritti-immobile/bene/{bene_id}`, `GET /assegnazioni-conduttore/bene/{bene_id}` (sostituiscono `/unita-immobiliare/{id}`);
  - query param `bene_id` su `GET /diritti-immobile/`, `/assegnazioni-conduttore/`, `/spese-ricorrenti/`;
  - `GET /unita-immobiliari/{id}/variazioni-catastali` invariato (filtra su `bene_id`).
- `IMMOBILE` in `relazioni_query.py` e `relazione_service.py` → tabella `immo_beni`, etichetta `concat_ws(', ', o.indirizzo, o.comune)`; `_immobile_labels` legge da `Bene` (`f"{codice} · {indirizzo}, {comune}"`).
- `seed_tenant.py`: l'insert raw delle unità di prova scrive prima `immo_beni` (`tipo_bene='UNITA'`) e poi `immo_unita_immobiliari` con lo stesso id.

- [ ] **Step 1:** aggiorna i test esistenti al nuovo contratto e aggiungi `test_relazione_immobile_etichetta_dal_bene` in `tests/integration/test_core/test_relazioni_query.py`: relazione su unità `indirizzo="Via A 1", citta="Forlì"` → etichetta `"Via A 1, Forlì"`.
- [ ] **Step 2:** `cd backend && ./run_tests.sh integration` → FAIL nei file toccati.
- [ ] **Step 3:** implementa secondo l'Interfaces block (`grep -rn unita_immobiliare_id backend/modules/immobili backend/app` deve restare solo su certificati, millesimi e route `/unita-immobiliari/{unita_immobiliare_id}`).
- [ ] **Step 4:** `./run_tests.sh` (unit + integration) → PASS.
- [ ] **Step 5:** commit `refactor(immobili): rights, tenants, cadastral changes and recurring costs belong to the bene`.

### Task 5: frontend su `bene_id`

**Files:**
- Modify: `frontend/src/modules/immobili/services/immobiliAPI.js` (righe ~78-81, ~181-193), `components/DirittiImmobile/DirittoForm.jsx`, `components/Conduttori/{AssegnazioneConduttoreForm,AssegnazioneConduttoreSection}.jsx`, `components/SpeseRicorrenti/{SpesaRicorrenteForm,SpeseRicorrentiSection}.jsx`, `components/Dashboard/ImmobiliStatsWidget.jsx`, `components/ImmobileScheda/ImmobileScheda.jsx`, `components/UnitaImmobiliari/UnitaImmobiliareForm.jsx`
- Test: `ImmobiliStatsWidget.test.jsx`, `AssegnazioneConduttoreSection.test.jsx`

**Interfaces:**
- Consumes: contratto del Task 4.
- Produces: `dirittiImmobileAPI.getByBene(beneId)`, `assegnazioniConduttoreAPI.getByBene(beneId)`, `getAll(beneId, …)` con param `bene_id`; i vecchi `getByImmobile`/`getByUnita` spariscono. Non toccare `affitti_brevi` e `affitti_lungo`.

- [ ] **Step 1:** nei due test sostituisci `unita_immobiliare_id` con `bene_id` nei dati finti; `ImmobiliStatsWidget` conta occupate le unità con assegnazione `bene_id` e senza `data_fine` (stesse attese: Occupati 1, Liberi 2).
- [ ] **Step 2:** `cd frontend && npm run test:run` → FAIL.
- [ ] **Step 3:** implementa; `grep -rn "unita_immobiliare_id" frontend/src/modules/immobili` resta solo su certificati e millesimi.
- [ ] **Step 4:** `npm run test:run && npm run build` → PASS. Riavvia il backend dev (non ricarica `modules/`) e apri una scheda unità: diritti, conduttori e spese si creano e compaiono.
- [ ] **Step 5:** commit `refactor(immobili-ui): child sections use bene_id`.

### Task 6: documentazione, verifica, rilascio con azzeramento

**Files:**
- Modify: `docs/modules/immobili.md` (modello: bene + unità, API `bene_id`, azzeramento del 2026-11-12), `docs/piattaforma.md` (`PROMOTE_PERDITA_CONSENTITA` nella sezione rilascio), `docs/superpowers/specs/2026-11-10-beni-catastali-design.md` (fase 1: fatto)

- [ ] **Step 1:** aggiorna i documenti; `scripts/controlla_documentazione.sh` → ok.
- [ ] **Step 2:** revisione UX (agente `revisione-ux`) sui file del Task 5, poi `verifica-test` → VERDE.
- [ ] **Step 3:** chiedi all'utente conferma che si può azzerare adesso (non deve aver caricato dati da tenere dopo il 2026-11-12).
- [ ] **Step 4:** rilascio (agente `rilascio`) con `PROMOTE_PERDITA_CONSENTITA="<tabelle del vincolo globale> core_documenti core_documenti_files core_scadenze core_scadenza_destinatari core_scadenza_log core_relazioni"`; atteso nel resoconto: solo righe `azzerata (consentito)`, `/health` ok, backup in `~/apps/gestione-affitti-backups`.
- [ ] **Step 5:** commit docs nello stesso rilascio.
