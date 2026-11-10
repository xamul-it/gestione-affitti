# Relazioni di ruolo tra soggetti e oggetti — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Catalogo dei tipi di relazione dichiarati dai moduli, relazioni soggetto → ruolo → oggetto (CORE in tabella tenant, MODULO ricavate dai provider) con scadenza decisa dal tipo, e liste di soggetti riusabili con prefiltro per ruolo (Anagrafiche, Proprietari, Conduttori), sezione relazioni nell'anagrafica e amministratore del condominio.

**Architecture:** Il catalogo vive in `public.core_ruoli_disponibili`, sincronizzato dai manifest (`relation_types`) come le tipologie documentali. Le relazioni CORE stanno nella nuova tabella tenant `core_relazioni`, gestite da `RelazioneService` (flush, mai commit) che crea/chiude le `Scadenza` del core. Le relazioni MODULO sono `select` SQLAlchemy fornite dai moduli e unite a quelle CORE da `relazioni_query`.

**Tech Stack:** FastAPI, SQLAlchemy 2, Alembic (catena core, `target_schema`), PostgreSQL multi-schema; React + Vite, Vitest + Testing Library.

**Spec:** `docs/superpowers/specs/2026-11-10-relazioni-ruoli-soggetti-design.md`

## Global Constraints

- Dati di produzione (collaudo) intoccabili senza backup verificato; mai DROP/TRUNCATE; tabelle vecchie restano.
- Il catalogo è in `public`; le relazioni sono **tenant** (`core_relazioni`); `public.core_soggetti_ruoli` non si usa.
- Codici dei tipi in minuscolo: `proprietario`, `conduttore`, `affittuario`, `tecnico`, `amministratore_condominio`, `ruolo_azienda`.
- `scadenza`: `null` | `{"manuale": true}` | `{"mesi": n, "da": "data_inizio"}`; `amministratore_condominio` = `{"mesi": 12, "da": "data_inizio"}`, `unico_per_oggetto: true`, `permesso_oggetto: "condominio.view"`.
- "Corrente" = `data_fine` nulla o ≥ oggi.
- L'anagrafica non viene mai cancellata da un elenco di ruolo.
- Provider: verifica tabelle con `sqlalchemy.inspect(...).has_table(..., schema=tenant_schema)`, mai try/rollback (il rollback annulla `SET search_path`).
- Servizi: `flush`, mai `commit`; le route committano.
- Frontend: token del design system (`styles/tokens.css`), componenti UI condivisi, testi in italiano.

## Review Focus

1. Diritti con `data_inizio`/`data_fine` stringa vuota o non ISO (colonne `String(10)`): il provider non deve fallire, la data diventa nulla — test in Task 3.
2. Modulo non installato nel tenant (tabelle `immo_*` o `affittuari` assenti): `GET /relazioni` e soggetti-v2 rispondono senza errore e senza quelle righe — test in Task 3.
3. Utente senza `immobile.view`: vede il ruolo ma non la descrizione dell'immobile — test in Task 3.
4. Secondo amministratore aperto sullo stesso condominio: 422 con messaggio chiaro; chiudendo il primo si può creare — test in Task 2.
5. Pagina con 50 soggetti: `ruoli` calcolati senza una query per soggetto (una query per provider) — test in Task 5 (conteggio query ≤ provider + 2).

---

### Task 1: Catalogo dei tipi di relazione dai manifest

**Files:**
- Create: `backend/alembic/versions/2026111001_ruoli_disponibili_manifest_fields.py` (public, `down_revision = "2026110902"`)
- Modify: `backend/app/core/models/ruoli.py` (colonne su `RuoloDisponibile`)
- Create: `backend/app/core/platform_services/relation_type_registry.py`
- Create: `backend/app/core/platform_services/relation_type_sync.py`
- Modify: `backend/modules/immobili/__manifest__.py`, `backend/modules/affitti_lungo/__manifest__.py` (rimuovere `endpoints.register_roles`), `backend/modules/anagrafica_italiana/__manifest__.py` (rimuovere `ruoli_disponibili`)
- Modify: `backend/scripts/sync_modules.py` (passo "Tipi di relazione" dopo "Tipologie documentali"), `backend/app/core/module_system/loader.py` (`_sync_relation_types` solo nel percorso di installazione, accanto a `_sync_document_types`)
- Test: `backend/tests/integration/test_core/test_relation_type_sync.py`, `backend/tests/unit/test_modules/test_relation_types_manifests.py`

**Interfaces:**
- Produces: colonne `RuoloDisponibile.entity_types` (JSON), `fonte` (VARCHAR(10) NOT NULL DEFAULT 'CORE'), `provider` (VARCHAR(200)), `scadenza` (JSON), `promemoria_giorni` (JSON), `sottotipi_fonte` (VARCHAR(100)), `unico_per_oggetto` (BOOLEAN NOT NULL DEFAULT false), `permesso_oggetto` (VARCHAR(100)).
- Produces: `RelationTypeDefinition(codice, nome, modulo, descrizione=None, entity_types=None, fonte="CORE", provider=None, scadenza=None, promemoria_giorni=None, sottotipi_fonte=None, unico_per_oggetto=False, permesso_oggetto=None)`; `FONTI = ("CORE", "MODULO")`; `ValueError` se fonte sconosciuta, `entity_types` fuori da `EntityType`, `MODULO` senza `provider`, `scadenza` non valida (riusa `_valid_scadenza` ma `da` deve essere `"data_inizio"`), `scadenza` su `MODULO`.
- Produces: `sync_relation_types(db, manifests: Dict[str, dict], complete: bool = False) -> SyncReport` (riusa `SyncReport` di `document_type_sync`); upsert per (`codice`, `modulo_id`), `nome_display` = `nome`; disattiva con `complete=True` le righe attive non dichiarate di **qualsiasi** modulo, tranne quelle dei moduli che usano `endpoints.register_roles` (oggi `gestione_pec`): le loro righe restano.

- [ ] **Step 1: test sui manifest** — `test_relation_types_manifests.py`: ogni `relation_types` di immobili, affitti_lungo, anagrafica_italiana valida come `RelationTypeDefinition`; insiemi esatti: immobili `{"proprietario","conduttore","amministratore_condominio"}`, affitti_lungo `{"affittuario","tecnico"}`, anagrafica `{"ruolo_azienda"}`; `amministratore_condominio` ha `scadenza == {"mesi": 12, "da": "data_inizio"}`, `unico_per_oggetto is True`, `entity_types == ["CONDOMINIO"]`; `proprietario` e `conduttore` hanno `fonte == "MODULO"`, `entity_types == ["IMMOBILE"]`, `permesso_oggetto == "immobile.view"`; `ruolo_azienda` ha `entity_types == ["SOGGETTO_ANAGRAFICO"]`, `sottotipi_fonte == "anag_ruoli_azienda_tipi"`; `"ruoli_disponibili" not in anagrafica_manifest`; `"register_roles" not in affitti_manifest["endpoints"]`.
- [ ] **Step 2: test della sync** (integration, db_session rollback, codici con `unique_suffix`): crea e aggiorna (idempotente al secondo giro: `creati == aggiornati == []`); `complete=True` disattiva una riga orfana e una riga doppia di altro modulo con lo stesso codice; non disattiva una riga di `gestione_pec`; riattiva un tipo tornato nel manifest; definizione invalida → in `errori`, non scritta; `test_invalid_definition_rejected` parametrizzato (fonte "X", entity_types ["NO"], MODULO senza provider, scadenza `{"mesi":12,"da":"data_riferimento"}`, scadenza su MODULO).
- [ ] **Step 3: eseguire** `pytest tests/unit/test_modules/test_relation_types_manifests.py tests/integration/test_core/test_relation_type_sync.py -q` → FAIL (moduli mancanti).
- [ ] **Step 4: implementare** migrazione (pattern di `2026110901`: `ADD COLUMN IF NOT EXISTS`), modello, registry, sync, manifest. Provider path: `immobili.relations:proprietari`, `immobili.relations:conduttori`, `affitti_lungo.relations:affittuari`, `affitti_lungo.relations:tecnici` (implementati in Task 3; qui solo dichiarati). Nomi: "Proprietario", "Conduttore", "Amministratore condominio", "Affittuario", "Tecnico", "Ruolo in azienda". `promemoria_giorni` amministratore `[60, 30]`.
- [ ] **Step 5: sync_modules** — passo `==> Tipi di relazione` con lo stesso schema del passo tipologie (`complete = len(manifests) == len(registered)`), log `create/aggiornate/disattivate`; loader `_sync_relation_types` nel solo percorso install.
- [ ] **Step 6: eseguire** i test del passo 3 → PASS; `alembic upgrade head` sul dev; `python scripts/sync_modules.py` mostra le disattivazioni dei doppioni (`anagrafica_italiana`: proprietario, affittuario, tecnico; `affitti_lungo`: proprietario).
- [ ] **Step 7: commit** `feat(core): relation types declared in module manifests and synced to the catalog`

### Task 2: Relazioni CORE e `RelazioneService`

**Files:**
- Create: `backend/alembic/versions/2026111002_core_relazioni.py` (tenant, `down_revision = "2026111001"`)
- Create: `backend/app/core/platform/models/relazione.py` (registrare in `app/core/platform/models/__init__.py`)
- Create: `backend/app/core/platform_services/relazione_service.py`
- Test: `backend/tests/integration/test_core/test_relazione_service.py`

**Interfaces:**
- Consumes: `RuoloDisponibile` con le colonne del Task 1.
- Produces: tabella `core_relazioni(id, soggetto_id INT NOT NULL, ruolo_id INT NOT NULL → public.core_ruoli_disponibili.id, entity_type VARCHAR(50), entity_id INT, sottotipo VARCHAR(100), data_inizio DATE, data_fine DATE, data_scadenza DATE, scadenza_id INT, note TEXT, dati JSON, creato_da INT, created_at, updated_at)`, indici su `soggetto_id`, (`entity_type`, `entity_id`), `ruolo_id`.
- Produces: `RelazioneService(db, tenant_schema, user_id)` con `crea(soggetto_id, tipo_codice, *, entity_type=None, entity_id=None, sottotipo=None, data_inizio=None, data_fine=None, data_scadenza=None, note=None, dati=None) -> Relazione`, `aggiorna(relazione_id, **campi) -> Relazione`, `elimina(relazione_id) -> None`, `rinnova(relazione_id) -> Relazione`, `tipo(codice) -> RuoloDisponibile`. Errori: `LookupError` (relazione/tipo/oggetto inesistente → 404), `ValueError` (regole → 422).

- [ ] **Step 1: test** (fixture: soggetto anagrafico + condominio creati nel db_session; tipi sincronizzati con `sync_relation_types` dai manifest reali):
  - `test_crea_amministratore_calcola_scadenza`: `data_inizio=date(2026,1,15)` → `data_scadenza == date(2027,1,15)`; esiste una `Scadenza` ATTIVA con `modulo == "immobili"`, `entity_type == "CONDOMINIO"`, `entity_id == condominio.id`, `titolo == "Amministratore condominio — <nome soggetto>"`, `data_scadenza == date(2027,1,15)`.
  - `test_data_scadenza_manuale_ignorata_se_calcolata`: passando `data_scadenza=date(2030,1,1)` resta `2027-01-15`.
  - `test_unico_per_oggetto`: seconda relazione aperta sullo stesso condominio → `ValueError` con "già un amministratore"; dopo `aggiorna(prima, data_fine=date(2026,6,30))` la seconda si crea; la scadenza della prima è COMPLETATA.
  - `test_duplicato_aperto`: stesso soggetto/tipo/oggetto/sottotipo aperto → `ValueError`.
  - `test_tipo_modulo_rifiutato`: `crea(..., "proprietario")` → `ValueError` ("gestito dal modulo").
  - `test_entity_type_non_applicabile`: amministratore su `IMMOBILE` → `ValueError`.
  - `test_elimina_annulla_scadenza` e `test_rinnova_sposta_di_un_periodo` (2027-01-15 → 2028-01-15, stessa `Scadenza` aggiornata).
  - `test_manuale_senza_data_nessuna_scadenza`: tipo di test `{"manuale": true}` (sincronizzato con suffisso) senza data → nessuna `Scadenza`.
- [ ] **Step 2: eseguire** `pytest tests/integration/test_core/test_relazione_service.py -q` → FAIL.
- [ ] **Step 3: implementare.** Oggetto esistente: verifica per `CONDOMINIO` → `immo_condomini`, `IMMOBILE` → `immo_unita_immobiliari`, `SOGGETTO_ANAGRAFICO` → `anag_soggetti_anagrafici` (query testuale `SELECT 1 FROM <tabella> WHERE id = :id`, tabella da una mappa nel servizio). Calcolo con `dateutil.relativedelta(months=n)`. Scadenza creata/aggiornata/chiusa con lo stesso codice di `DocumentoService` (`ScadenzaLog`, `PrioritaScadenza.ALTA`), estrarre gli helper comuni in `app/core/platform_services/scadenze_collegate.py` (`apri_o_aggiorna(db, *, scadenza_id, modulo, entity_type, entity_id, titolo, descrizione, data, user_id) -> int`, `chiudi(db, scadenza_id, stato, note, user_id)`) e far usare gli stessi a `DocumentoService` (i suoi test devono restare verdi). Senza oggetto: scadenza su `SOGGETTO_ANAGRAFICO`/soggetto.
- [ ] **Step 4: eseguire** il test del passo 2 e `pytest tests/integration/test_core -q` → PASS.
- [ ] **Step 5: commit** `feat(core): core_relazioni and RelazioneService with type-driven scadenze`

### Task 3: Provider dei moduli e unione delle relazioni

**Files:**
- Create: `backend/app/core/platform_services/relazioni_query.py`
- Create: `backend/modules/immobili/relations.py`, `backend/modules/affitti_lungo/relations.py`
- Test: `backend/tests/integration/test_core/test_relazioni_query.py`

**Interfaces:**
- Provider: `funzione(db: Session, tenant_schema: str) -> Optional[Select]` con colonne etichettate esattamente `soggetto_id, entity_type, entity_id, descrizione, data_inizio, data_fine, record_id` (date come `Date`); `None` se le tabelle mancano.
- Produces in `relazioni_query.py`:
  - `relazioni_select(db, tenant_schema, *, tipo: Optional[str] = None) -> Optional[Select]`: `UNION ALL` di CORE (`core_relazioni` ⋈ catalogo, `descrizione` = nome dell'oggetto) e dei provider attivi, con colonne aggiuntive `tipo, tipo_nome, modulo, fonte, relazione_id (NULL per MODULO), sottotipo, data_scadenza, permesso_oggetto`.
  - `elenca(db, tenant_schema, *, permessi: set, soggetto_ids=None, tipo=None, entity_type=None, entity_id=None, solo_correnti=False) -> List[dict]`; se `permesso_oggetto` non è in `permessi` (e `"*"` non c'è) azzera `descrizione` ed `entity_id`.
  - `soggetti_con_ruolo(db, tenant_schema, tipo, solo_correnti=True) -> Select` (solo `soggetto_id`, per `IN`).
  - `ruoli_per_soggetti(db, tenant_schema, soggetto_ids) -> Dict[int, List[dict]]` con `{codice, nome, modulo, n}`, `n` = correnti; un soggetto con sole relazioni cessate ha `n == 0` ed è comunque elencato.
- Descrizioni: proprietario "<indirizzo>, <citta> — <tipo diritto> <quota>%" (quota omessa se nulla); conduttore "<indirizzo>, <citta>"; CORE condominio = `immo_condomini.nome`, persona giuridica = `ragione_sociale`.

- [ ] **Step 1: test**: proprietario con due diritti → 2 righe con `entity_type == "IMMOBILE"`; proprietario senza diritti → 1 riga con `entity_id is None`, corrente; diritto con `data_fine` `"2020-01-01"` non corrente e con `data_inizio == ""` → `data_inizio is None` (Review Focus 1); conduttore con assegnazione chiusa → non corrente; `elenca(permessi={"soggetto.view"})` → `descrizione is None` (RF 3), con `{"immobile.view"}` presente; provider con tabelle assenti: chiamare `immobili.relations.proprietari(db, "schema_inesistente")` → `None`, e `elenca` con un tenant senza `immo_proprietari` (monkeypatch del provider a `None`) non solleva (RF 2); `ruoli_per_soggetti` conta CORE + MODULO; `soggetti_con_ruolo("proprietario")` include il proprietario senza diritti.
- [ ] **Step 2: eseguire** `pytest tests/integration/test_core/test_relazioni_query.py -q` → FAIL.
- [ ] **Step 3: implementare.** Date stringa dei diritti: `CASE WHEN col ~ '^\d{4}-\d{2}-\d{2}$' THEN CAST(col AS DATE) END`. Provider caricati con `importlib` dal campo `provider` del catalogo (righe attive, `fonte = 'MODULO'`).
- [ ] **Step 4: eseguire** → PASS.
- [ ] **Step 5: commit** `feat(core): module relation providers and union query`

### Task 4: API `/relazioni`

**Files:**
- Create: `backend/app/core/routes/relazioni.py` (registrare in `app/main.py` con prefisso `settings.API_V1_STR`), `backend/app/core/schemas/relazioni.py`
- Test: `backend/tests/integration/test_core/test_relazioni_routes.py`

**Interfaces:**
- `GET /relazioni/tipi?entity_type=` (`soggetto.view`) → `List[TipoRelazioneOut{id,codice,nome,modulo,fonte,entity_types,scadenza,unico_per_oggetto,sottotipi_fonte}]`, solo tipi attivi di moduli installati nel tenant (`TenantModuleService.get_tenant_modules(tenant.id, db)`, tenant da `request.state.tenant_schema`).
- `GET /relazioni?soggetto_id=&tipo=&entity_type=&entity_id=&solo_correnti=` (`soggetto.view`) → `List[RelazioneOut]` da `elenca` con i permessi dell'utente (`current_user.get_permissions()`).
- `POST /relazioni`, `PUT /relazioni/{id}`, `DELETE /relazioni/{id}`, `POST /relazioni/{id}/rinnova` (`soggetto.edit` + `permesso_oggetto` del tipo con `.view` → `.edit`, es. `condominio.edit`); `LookupError` → 404, `ValueError` → 422; commit nella route.
- `RelazioneIn{soggetto_id, tipo, entity_type?, entity_id?, sottotipo?, data_inizio?, data_fine?, data_scadenza?, note?, dati?}`.

- [ ] **Step 1: test** con `TestClient` e override di `get_db`/`get_current_active_user` (schema di `test_unita_immobiliari_permessi.py`): 403 senza `soggetto.view`; POST amministratore senza `condominio.edit` → 403, con → 201 e `data_scadenza` calcolata; secondo POST aperto → 422; DELETE → 204; tipi filtrati per `entity_type=CONDOMINIO` contengono solo `amministratore_condominio`.
- [ ] **Step 2: eseguire** → FAIL. **Step 3: implementare.** **Step 4: eseguire** → PASS.
- [ ] **Step 5: commit** `feat(core): relazioni API`

### Task 5: Anagrafiche: filtro `ruolo` e campo `ruoli`

**Files:**
- Modify: `backend/modules/anagrafica_italiana/routes/soggetti_v2.py`
- Test: `backend/tests/integration/test_modules/test_soggetti_v2_ruoli.py`

**Interfaces:**
- `GET /anagrafica/soggetti-v2/?ruolo=<codice>&ruolo_anche_cessati=<bool>`; risposta: ogni soggetto ha `ruoli: List[{codice, nome, modulo, n}]` (da `ruoli_per_soggetti`); `RuoloInfo` esistente sostituito da questa forma.

- [ ] **Step 1: test**: `ruolo=proprietario` restituisce solo soggetti proprietari (incluso uno senza diritti); `ruolo=proprietario` esclude chi ha solo diritti cessati, `ruolo_anche_cessati=true` lo include; `ruoli` di un soggetto proprietario e amministratore contiene entrambi; numero di query per 50 soggetti ≤ numero di provider + 3 (contatore con `event.listen(engine, "before_cursor_execute")`) (RF 5).
- [ ] **Step 2: FAIL. Step 3: implementare** (`query.filter(SoggettoAnagrafico.id.in_(soggetti_con_ruolo(...)))`; togliere il `joinedload` di `ruoli_assegnati`). **Step 4: PASS.**
- [ ] **Step 5: commit** `feat(anagrafica): soggetti-v2 filter by role and computed roles`

### Task 6: Ruoli in azienda sul modello generale

**Files:**
- Create: `backend/modules/anagrafica_italiana/migrations/versions/<rev>_ruoli_azienda_relazioni.py` (catena del modulo, SQL raw, tenant) — copia `anag_ruoli_azienda` in `core_relazioni` (`sottotipo = ruolo_tipo_id::text`, `dati = {"ruolo": ruolo}` se `ruolo_tipo_id` nullo), idempotente (`dati.migrato_da` = id originale, salta se presente)
- Modify: `backend/modules/anagrafica_italiana/routes/ruoli_azienda.py` (facciata su `RelazioneService` + `core_relazioni`), `routes/ruoli_azienda_tipi.py` (merge aggiorna `core_relazioni.sottotipo`)
- Test: `backend/tests/integration/test_modules/test_ruoli_azienda_relazioni.py`

**Interfaces:**
- Le route `/anagrafica/ruoli-azienda` mantengono path, parametri e `RuoloAziendaResponse` (`id` = id della relazione). Validazione nel servizio per `ruolo_azienda`: soggetto `PERSONA_FISICA`, oggetto `PERSONA_GIURIDICA`, diversi → altrimenti `ValueError`.

- [ ] **Step 1: test**: POST/GET/PUT/DELETE della facciata scrivono e leggono `core_relazioni` con tipo `ruolo_azienda`; persona giuridica come soggetto → 422; merge di due tipi sposta il `sottotipo`; la migrazione eseguita due volte copia una riga sola (funzione `migra(conn)` esposta dal file di migrazione e caricata come nel test `test_documenti_storico_migration.py`).
- [ ] **Step 2: FAIL. Step 3: implementare. Step 4: PASS** + suite dei test esistenti dei ruoli azienda verde.
- [ ] **Step 5: commit** `feat(anagrafica): business roles stored as core relations`

### Task 7: `SoggettiTable` riusabile e Anagrafiche con ruoli

**Files:**
- Create: `frontend/src/services/relazioniAPI.js` (`getTipi(entityType)`, `list(params)`, `create(data)`, `update(id, data)`, `remove(id)`, `rinnova(id)`)
- Create: `frontend/src/modules/anagrafica_italiana/components/SoggettiAnagrafici/SoggettiTable.jsx` (+ export in `modules/anagrafica_italiana/index.js`)
- Modify: `SoggettiAnagraficiList.jsx` (diventa `<SoggettiTable title="Anagrafiche" ... />` con colonna "Ruoli" e filtro ruolo)
- Test: `SoggettiTable.test.jsx`

**Interfaces:**
- `SoggettiTable({ ruolo, title, extraColumns = [], rowActions, onAdd, onEdit, onDelete, addButtonLabel, emptyMessage, showRuoli = true, showFiltroRuolo = false, toolbarExtra })`: `DataTable` con `endpoint '/anagrafica/soggetti-v2/'`, `defaultParams: { limit: 1000, ruolo, ruolo_anche_cessati }`; colonne base attuali; colonna "Ruoli" = badge `nome` per ogni `ruoli[]` con `n > 0` (badge attenuato per `n == 0`); nome con link alla pagina dell'anagrafica come oggi; interruttore "Anche cessati" visibile quando `ruolo` è impostato; filtro ruolo (select da `GET /relazioni/tipi`) quando `showFiltroRuolo`.

- [ ] **Step 1: test** (mock di axios/DataTable fetch come negli altri test del repo): con `ruolo="proprietario"` la richiesta contiene `ruolo=proprietario`; i badge mostrano "Proprietario" e "Amministratore condominio"; `extraColumns` compaiono; l'interruttore aggiunge `ruolo_anche_cessati=true`.
- [ ] **Step 2: `npm run test:run -- SoggettiTable` → FAIL. Step 3: implementare. Step 4: PASS** + `npm run build` ok.
- [ ] **Step 5: commit** `feat(anagrafica): reusable SoggettiTable with role prefilter and roles column`

### Task 8: Pagine Proprietari e Conduttori

**Files:**
- Modify: `frontend/src/modules/immobili/components/Proprietari/ProprietariList.jsx`, `Conduttori/ConduttoriList.jsx`
- Test: `ProprietariList.test.jsx`, `ConduttoriList.test.jsx`

**Interfaces:**
- Consumes: `SoggettiTable`, `relazioniAPI.list({ tipo, soggetto_id })` (per la colonna), API esistenti `/proprietari/`, `/conduttori/`.
- `ProprietariList`: `SoggettiTable ruolo="proprietario" title="Proprietari"`; colonna "Immobili" = descrizioni delle relazioni `proprietario` del soggetto (una sola chiamata `relazioniAPI.list({ tipo: "proprietario" })` per la pagina, raggruppata per `soggetto_id`), "Note" da `/proprietari/` (mappa per `soggetto_id`); azioni: "Apri anagrafica" (link), "Modifica note" (form attuale `ProprietarioForm` sul record `immo_proprietari`), "Togli dai proprietari" (DELETE `/proprietari/{id}` con conferma "Togliere <nome> dai proprietari? Verranno rimossi anche i suoi diritti sulle unità immobiliari. L'anagrafica resta."); "Nuovo proprietario" = form attuale.
- `ConduttoriList`: identico con `ruolo="conduttore"`, colonna "Unità occupate", conferma "Togliere <nome> dai conduttori? Verranno rimosse anche le sue assegnazioni. L'anagrafica resta."

- [ ] **Step 1: test**: la tabella chiede `ruolo=proprietario`; la colonna Immobili mostra le descrizioni; "Togli dai proprietari" chiama `DELETE /proprietari/<id del record immo_proprietari>` e non `/anagrafica/...`.
- [ ] **Step 2: FAIL. Step 3: implementare. Step 4: PASS.**
- [ ] **Step 5: commit** `feat(immobili): owners and occupants lists on the shared soggetti table`

### Task 9: Sezione "Relazioni" nella pagina dell'anagrafica

**Files:**
- Create: `frontend/src/core/components/Relazioni/RelazioniSection.jsx` (+ css con token)
- Modify: `frontend/src/modules/anagrafica_italiana/components/SoggettiAnagrafici/SoggettoDetail.jsx` (sostituisce il blocco "Ruoli Assegnati" segnaposto)
- Test: `RelazioniSection.test.jsx`

**Interfaces:**
- `RelazioniSection({ soggettoId })`: `relazioniAPI.list({ soggetto_id })`; tabella raggruppata per tipo: oggetto (`descrizione`, link `/unita-immobiliari/:id` per IMMOBILE, `/condomini` per CONDOMINIO, `/anagrafiche/:id` per SOGGETTO_ANAGRAFICO; nessun link se `entity_id` nullo), periodo, scadenza, stato "In corso"/"Cessata"; vuoto: "Nessuna relazione: questa anagrafica non è ancora proprietaria, conduttrice o collegata ad altri oggetti."

- [ ] **Step 1: test**: rendering di proprietario + amministratore con link corretti; relazione cessata marcata "Cessata"; descrizione nulla mostra "—".
- [ ] **Step 2: FAIL. Step 3: implementare. Step 4: PASS.**
- [ ] **Step 5: commit** `feat(anagrafica): relations section on the soggetto page`

### Task 10: Amministratore del condominio

**Files:**
- Create: `frontend/src/modules/immobili/components/Condomini/AmministratoreSection.jsx`
- Modify: `frontend/src/modules/immobili/components/Condomini/CondominioForm.jsx` (sezione in modifica, non in creazione)
- Test: `AmministratoreSection.test.jsx`

**Interfaces:**
- `AmministratoreSection({ condominioId, legacy })`: legge `relazioniAPI.list({ tipo: "amministratore_condominio", entity_type: "CONDOMINIO", entity_id })`; se c'è un amministratore corrente mostra nome (link anagrafica), dal, scadenza mandato, azioni "Rinnova mandato" (`rinnova`) e "Chiudi incarico" (`update` con `data_fine` = oggi, conferma); altrimenti "Collega amministratore": scelta anagrafica (stesso selettore di `ProprietarioForm`) + data inizio → `create`; se `legacy.amministratore_nome` è valorizzato e non c'è collegamento mostra "Dati precedenti: <nome>, <telefono>, <email>". Errore 422 mostrato nel form.

- [ ] **Step 1: test**: con amministratore corrente mostra scadenza e "Rinnova mandato" chiama `rinnova(id)`; senza, il form chiama `create` con `{ tipo: "amministratore_condominio", entity_type: "CONDOMINIO", entity_id, soggetto_id, data_inizio }`; i dati precedenti compaiono solo senza collegamento.
- [ ] **Step 2: FAIL. Step 3: implementare. Step 4: PASS.**
- [ ] **Step 5: commit** `feat(immobili): link the condominium administrator as a soggetto with mandate expiry`

---

Dopo il Task 10: revisione UX (agente `revisione-ux` sui file frontend dei Task 7–10), revisione finale dell'intero branch con Sonnet, verifica-test, rilascio (merge ff su master, push, `scripts/promote.sh`; controllare nel log i passi "Tipi di relazione" e le migrazioni tenant).
