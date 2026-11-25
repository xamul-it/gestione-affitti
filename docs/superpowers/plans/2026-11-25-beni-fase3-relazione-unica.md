# Beni fase 3 — relazione unica soggetto ↔ bene: piano di implementazione

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** diritti reali, godimenti (conduttore, comodatario, affittuario agrario) e incarichi sui beni diventano relazioni CORE in `core_relazioni`, con tipi divisi in famiglie; spariscono `immo_proprietari`, `immo_conduttori`, `immo_diritti_immobile`, `immo_assegnazioni_conduttore`.

**Architecture:** il catalogo `core_ruoli_disponibili` guadagna `famiglia`, `ammette_quota`, `solo_beni`; `core_relazioni` guadagna `quota_percentuale`. Immobili dichiara i nuovi tipi nel manifest e un suo servizio (`services/relazioni_bene.py`) applica le regole del bene sopra `RelazioneService`. Chi paga cosa e import visure leggono/scrivono relazioni. Una migrazione di modulo sposta i dati e toglie le tabelle vecchie. Il frontend sostituisce le due sezioni della scheda con una sezione "Soggetti".

**Tech Stack:** FastAPI, SQLAlchemy, Alembic multi-schema (core in `backend/alembic/versions`, moduli in `backend/modules/<m>/migrations`), PostgreSQL, React + Vite, Vitest, pytest.

**Spec:** `docs/superpowers/specs/2026-11-10-beni-catastali-design.md` (sezioni "Relazione unica", "Chi paga cosa", "Documenti", "Migrazione dei dati", fase 3). Spec di piattaforma collegata: `docs/superpowers/specs/2026-11-10-relazioni-ruoli-soggetti-design.md`.

## Global Constraints

- Fase 3 **non** introduce i raggruppamenti: `solo_beni` si dichiara ma nessun tipo si aggancia ancora a `RAGGRUPPAMENTO` (fase 4).
- Tipi e famiglie esattamente come nella spec:
  - `diritti_reali` (quota sì, `solo_beni: true`): `proprieta`, `nuda_proprieta`, `usufrutto`, `uso`, `abitazione`, `superficie`, `enfiteusi`, `diritto_reale_altro`;
  - `godimento` (quota no): `conduttore`, `affittuario_agrario`, `comodatario`, `godimento_altro`;
  - `incarichi` (quota no): `manutentore`, `terzo_responsabile_impianto`, `responsabile_impianto`, `tecnico_incaricato`, `incarico_altro`.
- Tutti `fonte: "CORE"`, `entity_types: ["IMMOBILE"]`, `permesso_oggetto: "immobile.view"`.
- Mappa migrazione `tipo_diritto` → tipo: `PROPRIETARIO`, `COMPROPRIETARIO` → `proprieta`; `NUDA_PROPRIETA` → `nuda_proprieta`; `USUFRUTTUARIO` → `usufrutto`; `USO`, `ABITAZIONE`, `SUPERFICIE`, `ENFITEUSI` → omonimi minuscoli; `ALTRO` → `diritto_reale_altro`.
- `quota_percentuale`: `NUMERIC(5,2)`, nullable, solo per tipi `ammette_quota`; somma delle quote aperte dei diritti reali di un bene > 100 → **avviso**, non errore.
- Comodato: estremi di registrazione in `dati` con chiavi `registrazione_data` (ISO), `registrazione_ufficio`, `registrazione_numero`.
- Migrazione: si ferma ed elenca (nessuna scrittura) se trova due diritti aperti stesso soggetto+tipo+bene dopo la mappatura, o date diritti non `YYYY-MM-DD`; nessun azzeramento.
- Documenti `entity_type = PROPRIETARIO` → `SOGGETTO_ANAGRAFICO` con `entity_id` = `immo_proprietari.soggetto_id`.
- Proprietari senza nessun diritto e conduttori senza assegnazioni (ruolo senza bene): non migrati, contati nel log (scelta del piano: una relazione di immobili ha sempre un bene).
- Nessun calcolo d'imposta. Le voci di "chi paga cosa" e i nomi `ruoli_alla_data`, `RuoliBene`, `Soggetto`, `voci_riepilogo` restano stabili (li usa il registro costi/ricavi).
- Codice e commenti in inglese, testi a video in italiano; commit in inglese con `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.
- Aggiornare `docs/modules/immobili.md` e `docs/piattaforma.md` nello stesso commit del codice che descrivono.
- Dati di esempio e test autoconsistenti per modulo; tenant di prova `tenant_test_nuovo` e `tenant_test_evolutivo` devono migrare puliti.

## Review Focus

1. **Visura reimportata** dopo la migrazione: un soggetto che ha già `proprieta` aperta sul bene non deve ricevere un doppione né far fallire l'import (oggi si salta; deve restare così). → test in Task 5.
2. **`PROPRIETARIO` + `COMPROPRIETARIO` dello stesso soggetto sullo stesso bene** (dati storici): la migrazione deve fermarsi con l'elenco, non creare due `proprieta` (il core le rifiuterebbe a metà). → test in Task 6.
3. **Quota su un tipo che non la ammette** (es. `conduttore` con quota 50) dall'API generica `/relazioni`: errore 400 chiaro, non salvataggio silenzioso. → test in Task 1.
4. **Cancellazione di un'anagrafica** che ha solo relazioni di immobili: deve essere bloccata come oggi per le relazioni CORE (`conta_per_soggetto`), non lasciare relazioni orfane. → test in Task 3.
5. **Modulo immobili disattivato nel tenant**: le relazioni dei nuovi tipi spariscono dalle liste e "chi paga cosa" non è raggiungibile; riattivando tornano. → test in Task 3.

---

## File Structure

Backend
- `app/core/platform_services/relation_type_registry.py` — campi `famiglia`, `ammette_quota`, `solo_beni` nella definizione.
- `app/core/platform_services/relation_type_sync.py`, `app/core/models/ruoli.py` — nuove colonne del catalogo.
- `app/core/platform/models/relazione.py`, `app/core/platform_services/relazione_service.py`, `app/core/routes/relazioni.py`, `app/core/schemas/relazioni.py` — `quota_percentuale`, filtro `famiglia`.
- `app/core/platform/models/documento.py` — `EntityType.RELAZIONE`.
- `alembic/versions/2026112501_relazioni_famiglie_quota.py` — colonne + `ALTER TYPE … ADD VALUE 'RELAZIONE'`.
- `modules/immobili/__manifest__.py` — nuovi `relation_types`, via i provider.
- `modules/immobili/services/relazioni_bene.py` (nuovo) — regole del bene, elenco per famiglia.
- `modules/immobili/routes/beni.py` — `GET/POST /beni/{id}/relazioni`.
- `modules/immobili/services/ruoli_bene.py` — da relazioni.
- `modules/immobili/services/visura_import_service.py`, `services/lettura_documenti/abbinamento.py` — scrivono/leggono relazioni.
- `modules/immobili/migrations/2026112501_relazione_unica.py` (nuovo) — migrazione dati e drop.
- Da togliere: `models/{proprietari,conduttore,assegnazione_conduttore,diritti_immobile}.py`, `routes/{proprietari,conduttori,assegnazioni_conduttore,diritti_immobile}.py`, schemi relativi, `relations.py`; riferimenti in `anagrafica_italiana/models/soggetto_anagrafico.py`, `anagrafica_italiana/routes/{soggetti,soggetti_v2}.py`, `affitti_lungo/models/__init__.py`, `seeds/seed_tenant.py`.

Frontend (`frontend/src/modules/immobili/`)
- `components/BeneScheda/SoggettiSection.jsx` (+ `.test.jsx`) e `RelazioneBeneForm.jsx` — sostituiscono `DirittiImmobile/*` e `Conduttori/AssegnazioneConduttore*`.
- `services/immobiliAPI.js` — `beniAPI.getRelazioni`, `beniAPI.createRelazione`; via `proprietariAPI`, `conduttoriAPI`, `dirittiAPI`, `assegnazioniConduttoreAPI`.
- `components/Proprietari/ProprietariList.jsx`, `components/Conduttori/ConduttoriList.jsx`, `components/Soggetti/RuoloSoggettiPage.jsx` — filtro per famiglia, niente record di modulo.
- `components/Dashboard/ImmobiliStatsWidget.jsx` — conteggi dalle relazioni.
- `frontend/src/services/relazioniAPI.js` — parametro `famiglia`.

---

### Task 1: Catalogo con famiglie e quota sulle relazioni (core)

**Files:**
- Modify: `backend/app/core/platform_services/relation_type_registry.py`, `relation_type_sync.py`, `backend/app/core/models/ruoli.py`, `backend/app/core/platform/models/relazione.py`, `backend/app/core/platform_services/relazione_service.py`, `backend/app/core/routes/relazioni.py`, `backend/app/core/schemas/relazioni.py`, `backend/app/core/platform/models/documento.py`
- Create: `backend/alembic/versions/2026112501_relazioni_famiglie_quota.py` (public: colonne `famiglia VARCHAR(30)`, `ammette_quota BOOLEAN NOT NULL DEFAULT false`, `solo_beni BOOLEAN NOT NULL DEFAULT false` su `core_ruoli_disponibili`; `ALTER TYPE public.entitytype ADD VALUE IF NOT EXISTS 'RELAZIONE'` — verificare il nome del tipo con `\dT public.*`; tenant: `quota_percentuale NUMERIC(5,2)` su `core_relazioni`). `target_schema = "both"`, idempotente (`IF NOT EXISTS`).
- Test: `backend/tests/unit/test_core/test_relation_type_registry.py`, `backend/tests/integration/test_core/test_relazione_service.py` (estendere gli esistenti o crearli accanto)

**Interfaces:**
- Produces: `RelationTypeDefinition(famiglia: Optional[str], ammette_quota: bool = False, solo_beni: bool = False)`; `RuoloDisponibile.famiglia/ammette_quota/solo_beni`; `Relazione.quota_percentuale: Optional[Decimal]`; `RelazioneService.crea(..., quota_percentuale: Optional[Decimal] = None)`; `aggiorna` accetta `quota_percentuale`; `GET /relazioni/?famiglia=…` e `GET /relazioni/tipi?famiglia=…`; risposte con `quota_percentuale`, `famiglia`; `EntityType.RELAZIONE`.

- [ ] **Step 1: test che falliscono**
  - `test_definizione_famiglia_e_quota`: `RelationTypeDefinition(codice="x", nome="X", modulo="m", famiglia="godimento", ammette_quota=True).ammette_quota is True`; `famiglia` non stringa → `ValueError`.
  - `test_sync_scrive_famiglia`: dopo `sync_relation_types` un tipo dichiarato con `famiglia="diritti_reali", ammette_quota=True, solo_beni=True` ha le tre colonne valorizzate.
  - `test_crea_con_quota`: tipo con `ammette_quota` → `rel.quota_percentuale == Decimal("50.00")`.
  - `test_quota_rifiutata_se_non_ammessa`: tipo senza `ammette_quota` e `quota_percentuale=50` → `ValueError("Il tipo '…' non ammette una quota")`; via API → 400.
  - `test_quota_fuori_intervallo`: `0` o `100.01` → `ValueError`.
  - `test_list_filtra_per_famiglia`: due relazioni di famiglie diverse, `GET /relazioni/?famiglia=godimento` ne restituisce una.
- [ ] **Step 2:** `pytest tests/unit/test_core/test_relation_type_registry.py tests/integration/test_core/test_relazione_service.py -v` → FAIL.
- [ ] **Step 3:** implementare; la quota va in `_CAMPI_MODIFICABILI`; il filtro `famiglia` sulle relazioni MODULO si applica sul tipo del catalogo come gli altri filtri di `relazioni_query`.
- [ ] **Step 4:** stessi test → PASS; `alembic -x schema=tenant_test upgrade head` senza errori e rieseguibile.
- [ ] **Step 5:** aggiornare `docs/piattaforma.md` §5 (campi `famiglia`, `ammette_quota`, `solo_beni`, quota, filtro) e la tabella dei campi in `2026-11-10-relazioni-ruoli-soggetti-design.md`; commit `feat(platform): relation families and shares`.

### Task 2: Documenti su una relazione

**Files:**
- Modify: `backend/app/core/platform_services/documento_service.py` (validazione oggetto, se presente: `RELAZIONE` → `core_relazioni`), `backend/modules/immobili/__manifest__.py` (`document_types`: `ATTO_PROVENIENZA` e `CONTRATTO_AFFITTO_AGRARIO` valgono anche per `RELAZIONE`; nuove `CONTRATTO_COMODATO` cumulativo e `DELEGA_TERZO_RESPONSABILE` cumulativo su `RELAZIONE`), `frontend/src/core/components/Documenti/DocumentiPanel.jsx` solo se rifiuta entity_type sconosciuti
- Test: `backend/tests/integration/test_core/test_documenti_relazione.py`

**Interfaces:**
- Consumes: `EntityType.RELAZIONE` (Task 1).
- Produces: upload/list documenti con `entity_type=RELAZIONE`, `entity_id=<core_relazioni.id>`; eliminare la relazione (`RelazioneService.elimina`) elimina anche i suoi documenti come `elimina_bene` fa per il bene (file lasciati nello storage).

- [ ] **Step 1:** test `test_upload_su_relazione` (201, documento listato per quella relazione), `test_tipologia_non_ammessa_su_relazione` (`VISURA_CATASTALE` su `RELAZIONE` → 400), `test_elimina_relazione_toglie_documenti`.
- [ ] **Step 2:** eseguire → FAIL.
- [ ] **Step 3:** implementare.
- [ ] **Step 4:** eseguire → PASS; `pytest tests/unit/test_modules/test_document_types_manifests.py -v` PASS.
- [ ] **Step 5:** `docs/modules/immobili.md` §4 (nuove tipologie e oggetto RELAZIONE); commit `feat(platform): documents attached to a relation`.

### Task 3: Tipi di immobili e servizio delle relazioni del bene

**Files:**
- Modify: `backend/modules/immobili/__manifest__.py` (togliere i due tipi MODULO `proprietario`/`conduttore`, dichiarare i 17 tipi della Global Constraints; `conduttore` mantiene il codice), `backend/modules/immobili/routes/beni.py`
- Create: `backend/modules/immobili/services/relazioni_bene.py`, `backend/modules/immobili/schemas/relazioni_bene.py`
- Test: `backend/tests/integration/test_modules/test_immobili/test_relazioni_bene.py`, `backend/tests/unit/test_modules/test_relation_types_manifests.py`

**Interfaces:**
- Consumes: Task 1.
- Produces:
  - `FAMIGLIE = ("diritti_reali", "godimento", "incarichi")` in `relazioni_bene.py`;
  - `crea_relazione_bene(db, tenant_schema, user_id, bene_id: int, soggetto_id: int, tipo: str, *, quota_percentuale=None, data_inizio=None, data_fine=None, note=None, dati=None) -> tuple[Relazione, list[str]]` (relazione + avvisi);
  - `relazioni_del_bene(db, tenant_schema, bene_id: int, solo_correnti: bool = False) -> dict[str, list[dict]]` (chiave = famiglia; ogni riga: `id, tipo, tipo_nome, soggetto_id, soggetto_nome, quota_percentuale, data_inizio, data_fine, note, dati`);
  - `somma_quote_aperte(db, bene_id: int, tipo: str) -> Decimal`;
  - `GET /api/v1/beni/{id}/relazioni?solo_correnti=` → `{"diritti_reali": [...], "godimento": [...], "incarichi": [...]}`; `POST /api/v1/beni/{id}/relazioni` body `{soggetto_id, tipo, quota_percentuale?, data_inizio?, data_fine?, note?, dati?}` → `{"relazione": {...}, "avvisi": [...]}`. Modifica/chiusura/eliminazione restano su `/relazioni/{id}`.

- [ ] **Step 1:** test
  - `test_manifest_dichiara_famiglie`: ogni tipo di immobili ha `famiglia` in `FAMIGLIE`; i diritti reali hanno `ammette_quota` e `solo_beni`.
  - `test_crea_diritto_con_quota`: `proprieta` 50 → relazione con quota, avvisi `[]`.
  - `test_avviso_quote_oltre_cento`: due `proprieta` 60 + 50 di soggetti diversi → seconda creata, avvisi = `["Le quote di Proprietà sul bene superano il 100% (110%)"]`.
  - `test_tipo_di_altro_modulo_rifiutato`: `tipo="amministratore_condominio"` → 400.
  - `test_comodatario_con_registrazione`: `dati={"registrazione_data": "2026-01-10", "registrazione_ufficio": "TNX", "registrazione_numero": "123"}` salvati; `registrazione_data` non ISO → 400.
  - `test_relazioni_raggruppate_per_famiglia`.
  - `test_anagrafica_con_relazioni_non_eliminabile` (Review Focus 4): `DELETE` dell'anagrafica → bloccato.
  - `test_modulo_disattivato_nasconde` (Review Focus 5): disattivato immobili nel tenant, `GET /relazioni/?famiglia=diritti_reali` vuoto; riattivato, torna.
  - permessi: senza `immobile.view` → 403 su entrambe le rotte; scrittura con `immobile.update`.
- [ ] **Step 2:** eseguire → FAIL.
- [ ] **Step 3:** implementare; la validazione `dati` per `comodatario` sta in `relazioni_bene.py`; il servizio chiama `RelazioneService.crea` e non duplica le sue regole.
- [ ] **Step 4:** eseguire → PASS.
- [ ] **Step 5:** `docs/modules/immobili.md` §3 (tabella tipi per famiglia); commit `feat(immobili): relation types by family on beni`.

### Task 4: Chi paga cosa dalle relazioni

**Files:**
- Modify: `backend/modules/immobili/services/ruoli_bene.py`
- Test: `backend/tests/unit/test_modules/test_immobili/test_ruoli_bene.py` (adattare gli esistenti), `backend/tests/integration/test_modules/test_immobili/test_riepilogo_api.py`

**Interfaces:**
- Consumes: Task 3 (relazioni nel DB).
- Produces (nomi stabili): `ruoli_da_righe(relazioni: Iterable[RigaRelazione], d: date) -> RuoliBene`, dove `RigaRelazione` è un dataclass `(soggetto_id: int, nome: str, tipo: str, quota: Optional[Decimal], data_inizio: Optional[date], data_fine: Optional[date])`; `ruoli_alla_data(db, bene_id, d) -> RuoliBene` invariata come firma; `Soggetto.ruolo` = codice del tipo (`"proprieta"`, `"usufrutto"`, `"conduttore"`, `"comodatario"`…). `RuoliBene.conduttori` = tutti i godimenti personali aperti (conduttore, affittuario_agrario, comodatario, godimento_altro).
- Costanti: `GODIMENTO = ("usufrutto", "uso", "abitazione", "enfiteusi", "superficie")`, `PIENA_PROPRIETA = ("proprieta",)`, `PROPRIETA = ("nuda_proprieta", "proprieta")`, `STRAORDINARIE_AI_PROPRIETARI = ("usufrutto", "uso", "abitazione")`, `GODIMENTO_PERSONALE = ("conduttore", "affittuario_agrario", "comodatario", "godimento_altro")`.

- [ ] **Step 1:** riscrivere i test esistenti sui nuovi codici mantenendo gli stessi casi e attese; aggiungere `test_comodatario_paga_ordinarie` (bene con `proprieta` 100 + `comodatario`: spese ordinarie → comodatario, IMU → proprietario) e `test_incarichi_ignorati` (un `manutentore` non compare in nessuna voce); `diritto_reale_altro` produce l'avviso "ripartizione da decidere a mano" come `ALTRO` oggi.
- [ ] **Step 2:** eseguire → FAIL.
- [ ] **Step 3:** implementare leggendo `core_relazioni` (join `core_ruoli_disponibili` per codice e famiglia, `anag_soggetti_anagrafici` per il nome); `_quote_distinte` invariata nella logica.
- [ ] **Step 4:** eseguire → PASS, compreso `test_riepilogo_api.py`.
- [ ] **Step 5:** commit `refactor(immobili): who pays what reads relations`.

### Task 5: Import visure e abbinamento documenti sulle relazioni

**Files:**
- Modify: `backend/modules/immobili/services/visura_import_service.py` (`_proprietario_for`, `_diritti_esistenti`, blocco `db.add(DirittoImmobile(...))`), `backend/modules/immobili/services/lettura_documenti/abbinamento.py`
- Test: `backend/tests/integration/test_modules/test_immobili/test_visura_import.py`, `test_abbinamento_documenti.py`

**Interfaces:**
- Consumes: `crea_relazione_bene` (Task 3); `MAPPA_TIPO_DIRITTO: dict[str, str]` da definire in `relazioni_bene.py` con la mappa della Global Constraints (la usa anche la migrazione, Task 6, che però la copia: le migrazioni non importano codice applicativo).
- Produces: l'import crea relazioni dei diritti reali; `result.diritti_creati` conta le relazioni create.

- [ ] **Step 1:** adattare i test esistenti; aggiungere `test_reimport_non_duplica` (Review Focus 1): importare due volte la stessa visura → una sola `proprieta` per soggetto e bene, secondo import `diritti_creati == 0`; `test_comproprietario_diventa_proprieta` (visura con `COMPROPRIETARIO` → tipo `proprieta` con la quota).
- [ ] **Step 2:** eseguire → FAIL.
- [ ] **Step 3:** implementare; nessuna creazione di `Proprietario`.
- [ ] **Step 4:** eseguire → PASS, insieme a `pytest -m parsing`.
- [ ] **Step 5:** commit `refactor(immobili): visura import writes relations`.

### Task 6: Migrazione dei dati

**Files:**
- Create: `backend/modules/immobili/migrations/2026112501_relazione_unica.py` (`down_revision = "2026111401_collegamenti_beni"`, `target_schema = "tenant"`)
- Test: `backend/tests/integration/test_modules/test_immobili/test_migrazione_relazione_unica.py` (stesso schema di `test_migrazione_terreni.py`: schema temporaneo `tenant_pytest_relazioni` col vecchio layout, `converti(conn)` dentro la transazione annullata)

**Interfaces:**
- Consumes: colonne del Task 1 già presenti (la migrazione di modulo gira dopo `alembic -x schema=all upgrade head` del core; se `core_relazioni.quota_percentuale` manca, `RuntimeError` con messaggio chiaro); tipi del Task 3 già sincronizzati in `core_ruoli_disponibili` (se un codice manca, `RuntimeError` che dice di eseguire `scripts/sync_modules.py`).
- Produces: `converti(conn) -> dict` con i conteggi `{"diritti": n, "assegnazioni": n, "documenti_proprietario": n, "proprietari_senza_diritti": n, "conduttori_senza_assegnazioni": n}`; `upgrade()` chiama `converti` e poi elimina le quattro tabelle; `downgrade()` → `NotImplementedError` (si torna dal backup).

- [ ] **Step 1:** test
  - `test_diritti_diventano_relazioni`: 3 diritti (PROPRIETARIO 50, COMPROPRIETARIO 50 di un altro soggetto, USUFRUTTUARIO) → 3 relazioni con tipi, quote, date (`'2020-01-01'` → `date(2020,1,1)`), note.
  - `test_assegnazioni_diventano_conduttore`.
  - `test_note_ruolo_in_dati`: `note_proprietario` → `dati["note_ruolo"]` di ogni relazione di quel soggetto.
  - `test_documenti_proprietario_al_soggetto`.
  - `test_doppione_ferma` (Review Focus 2): stesso soggetto PROPRIETARIO + COMPROPRIETARIO aperti sullo stesso bene → `RuntimeError` che elenca bene e soggetto; nessuna riga scritta in `core_relazioni`.
  - `test_data_malformata_ferma`: `data_inizio = '01/02/2020'` → `RuntimeError` con l'id del diritto.
  - `test_conteggi_ruoli_senza_bene`.
  - `test_idempotente_su_schema_nuovo`: schema senza le vecchie tabelle (tenant creato da zero) → nessun errore, conteggi zero.
- [ ] **Step 2:** eseguire → FAIL.
- [ ] **Step 3:** implementare in SQL (`INSERT … SELECT`), controlli prima di qualunque scrittura, `DROP TABLE` solo dopo il confronto dei conteggi (righe migrate = diritti + assegnazioni).
- [ ] **Step 4:** eseguire → PASS; poi `alembic -x schema=tenant_test_evolutivo upgrade head` e `-x schema=tenant_test_nuovo` senza errori.
- [ ] **Step 5:** commit `feat(immobili): migrate rights and tenants to core relations`.

### Task 7: Togliere modelli, rotte e riferimenti vecchi; dati di esempio

**Files:**
- Delete: `backend/modules/immobili/models/{proprietari,conduttore,assegnazione_conduttore,diritti_immobile}.py`, `routes/{proprietari,conduttori,assegnazioni_conduttore,diritti_immobile}.py`, schemi omonimi in `schemas/`, `modules/immobili/relations.py`, `tests/integration/test_modules/test_immobili/test_proprietari.py` (i casi utili sono già in Task 3), `test_conduttori_spese_ricorrenti.py` per la parte conduttori
- Modify: `models/__init__.py`, `models/bene.py` (via `diritti`, `assegnazioni_conduttore`), `routes/__init__.py`, `services/elimina_bene.py` (non tocca più le tabelle tolte; le relazioni le toglie già `RelazioneService.elimina_per_oggetto`), `anagrafica_italiana/models/soggetto_anagrafico.py` (via `proprietari`, `conduttori`), `anagrafica_italiana/routes/soggetti.py:41`, `anagrafica_italiana/routes/soggetti_v2.py:21-27` (via le due voci), `affitti_lungo/models/__init__.py:12-13,45-46`, `app/core/services/role_registry.py` se registra ancora `proprietario`, `seeds/seed_tenant.py` (dati di esempio come relazioni: stessi soggetti, beni e quote di oggi, idempotenti), `app/core/tenant_tables.py` se elenca le tabelle tolte
- Test: `test_seed_esempio.py`, `test_elimina_bene.py`, `test_unita_immobiliare_cascade_delete.py`, `test_soggetti_v2_ruoli.py`

**Interfaces:**
- Consumes: Task 3-6.
- Produces: nessun riferimento a `Proprietario`, `Conduttore`, `DirittoImmobile`, `AssegnazioneConduttore` (`grep -rn` vuoto fuori da `migrations/`); il seed crea relazioni con `crea_relazione_bene`.

- [ ] **Step 1:** adattare `test_seed_esempio.py` (le relazioni di esempio esistono e la seconda esecuzione non ne aggiunge) e i test di cancellazione (cancellare un bene toglie le sue relazioni).
- [ ] **Step 2:** eseguire → FAIL.
- [ ] **Step 3:** togliere e aggiornare.
- [ ] **Step 4:** `./run_tests.sh` intero → PASS; `grep -rnE "DirittoImmobile|AssegnazioneConduttore|immo_proprietari|immo_conduttori" backend --include=*.py | grep -v migrations` vuoto.
- [ ] **Step 5:** `docs/modules/immobili.md` (tabella entità: via Proprietari/Conduttori come tabelle, rimando alle relazioni); commit `refactor(immobili): drop owner and tenant tables`.

### Task 8: Frontend — sezione "Soggetti" della scheda e liste

**Files:**
- Create: `frontend/src/modules/immobili/components/BeneScheda/SoggettiSection.jsx`, `SoggettiSection.test.jsx`, `RelazioneBeneForm.jsx`
- Modify: `BeneScheda.jsx:11-12,144-147` (una sola `<SoggettiSection beneId={beneId} onChange={…} />` al posto delle due sezioni; dopo una modifica ricarica `RiepilogoSection` come oggi con `versione`), `services/immobiliAPI.js`, `frontend/src/services/relazioniAPI.js` (`list` accetta `famiglia`), `components/Proprietari/ProprietariList.jsx`, `components/Conduttori/ConduttoriList.jsx`, `components/Soggetti/RuoloSoggettiPage.jsx` (prop `famiglia` al posto di `ruolo`; via `recordsAPI`, `noteField`, `FormComponent`), `components/Dashboard/ImmobiliStatsWidget.jsx` (proprietari = soggetti distinti con diritti reali correnti; conduttori = godimenti correnti), `components/ImportVisura/ImportVisuraModal.jsx` se nomina proprietari
- Delete: `components/DirittiImmobile/*`, `components/Conduttori/{AssegnazioneConduttoreForm,AssegnazioneConduttoreSection,AssegnazioneConduttoreSection.test,ConduttoreForm}.jsx`, `components/Proprietari/ProprietarioForm.jsx`

**Interfaces:**
- Consumes: `GET/POST /beni/{id}/relazioni` (Task 3), `PUT/DELETE /relazioni/{id}`, `GET /relazioni/tipi?entity_type=IMMOBILE&famiglia=…`, documenti con `entityType="RELAZIONE"` (Task 2).
- Produces: `beniAPI.getRelazioni(beneId, { soloCorrenti })`, `beniAPI.createRelazione(beneId, data)`.

Comportamento della sezione (decisioni del piano):
- tre blocchi nell'ordine "Diritti reali", "Godimento", "Incarichi"; ogni riga: anagrafica (link `/anagrafiche/:id`), tipo, quota (solo diritti reali, `50%`), periodo, azioni Modifica / Chiudi (data di fine) / Elimina con conferma, e "Documenti" che apre `DocumentiPanel` della relazione;
- interruttore "Mostra chiuse" (default spento: `solo_correnti`);
- "Aggiungi" per blocco apre `RelazioneBeneForm` con i tipi di quella famiglia; campo quota solo se `ammette_quota`; per `comodatario` i tre campi di registrazione; gli `avvisi` della risposta come toast di avviso;
- `SoggettoPicker` esistente per l'anagrafica; componenti `Button`, `ConfirmDialog`, `EmptyState` del design system.

- [ ] **Step 1:** test Vitest in `SoggettiSection.test.jsx`: rende i tre blocchi dai dati mock; quota visibile solo nei diritti reali; il form di `conduttore` non mostra la quota, quello di `comodatario` mostra i campi di registrazione; un avviso della risposta appare come toast; "Mostra chiuse" ricarica con `soloCorrenti=false`.
- [ ] **Step 2:** `npm run test:run -- SoggettiSection` → FAIL.
- [ ] **Step 3:** implementare; adattare `ProprietariList.test.jsx` alla nuova `RuoloSoggettiPage`.
- [ ] **Step 4:** `npm run test:run` e `npm run build` → PASS.
- [ ] **Step 5:** commit `feat(immobili): soggetti section on the bene page`.

### Task 9: Revisione, verifica, documentazione, rilascio

- [ ] **Step 1:** agente `revisione-ux` (Sonnet) sui file del Task 8; correggere i problemi gravi.
- [ ] **Step 2:** revisione del codice del branch (Sonnet); correggere.
- [ ] **Step 3:** agente `verifica-test` → VERDE.
- [ ] **Step 4:** spec: segnare la fase 3 come fatta con la data; memoria `project_beni_catastali.md` aggiornata.
- [ ] **Step 5:** contare le righe delle quattro tabelle in ogni schema di produzione (atteso 0 in `tenant_produzione` al 2026-11-25); agente `rilascio` con l'elenco esplicito delle tabelle eliminate per `promote.sh`; backup in `~/apps/gestione-affitti-backups`; verificare che tutti gli schema di produzione siano migrati.
