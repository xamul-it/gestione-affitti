# Beni catastali — Fase 2a: terreni come beni — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Il terreno diventa un bene (stesso id in `immo_beni`) con porzioni, scheda comune `/beni/:id`, documenti, diritti, conduttori, spese e scadenze come l'unità, e cancellazione vera.

**Architecture:** `Terreno(Bene)` con `polymorphic_identity="TERRENO"`, come `UnitaImmobiliare` in fase 1; nuova tabella `immo_terreni_porzioni`. Una migrazione converte `immo_terreni` dal vecchio layout senza perdere righe. API comune `/api/v1/beni/`; la scheda dell'unità diventa la scheda del bene, con la parte "Dati" che cambia col tipo.

**Tech Stack:** FastAPI, SQLAlchemy (joined inheritance), migrazioni di modulo in raw SQL, React + Vitest.

**Spec:** `docs/superpowers/specs/2026-11-10-beni-catastali-design.md` (Obiettivi 3, 5, 8; Modello; API; Interfaccia; Piano a fasi punto 2). Questo piano copre la parte "terreni" della fase 2; **collegamenti tra beni** e **riepilogo "chi paga cosa"** sono la fase 2b (piano successivo). Il **selettore unico dei beni** va con la fase 3/4, dove ha i suoi primi utilizzatori (contratti, caricamento unico): oggi nessun form sceglie un bene.

## Global Constraints

- Lo stesso id identifica bene e terreno: `immo_terreni.id` PK e FK → `immo_beni.id ON DELETE CASCADE`, senza sequenza propria (come l'unità, migrazione `2026111201_beni`).
- Passano dal terreno al bene: `codice, descrizione, indirizzo, comune, cap, provincia, sezione_catastale (→ sezione), foglio, particella, subalterno, note, attivo, created_at, updated_at`.
- Restano sul terreno: `tipologia_id, nome (diventa facoltativo), nazione`; nuove: `superficie_mq FLOAT` (somma delle porzioni, calcolata dal server), `edificabile BOOLEAN NOT NULL DEFAULT FALSE`, `esente_imu_montano BOOLEAN NOT NULL DEFAULT FALSE` (scelta manuale), `servitu TEXT`.
- Escono dal terreno (vanno nelle porzioni): `superficie, unita_misura_superficie, qualita_coltura, classe_catastale, reddito_dominicale, reddito_agrario`.
- `immo_terreni_porzioni`: `id SERIAL, terreno_id → immo_terreni(id) ON DELETE CASCADE, porzione VARCHAR(5) NULL (es. AA, AB), qualita VARCHAR(100) NOT NULL, classe VARCHAR(10), superficie_mq FLOAT NOT NULL CHECK (>= 0), reddito_dominicale NUMERIC(12,2), reddito_agrario NUMERIC(12,2), deduzioni VARCHAR(100)`.
- Un terreno ha **almeno una porzione** (anche "ENTE URBANO" senza classe né redditi). Le porzioni si mandano dentro create/update del terreno e sostituiscono quelle esistenti.
- API terreni: `sezione_catastale` resta il nome esposto (`synonym("sezione")`); la risposta ha `porzioni`, `superficie_mq`, `reddito_dominicale_totale`, `reddito_agrario_totale`.
- `DELETE /terreni/{id}` cancella davvero (bene, porzioni, diritti, assegnazioni, spese, variazioni); "Disattiva/Ripristina" usano `attivo` del bene.
- Superficie a video in ettari, are e centiare: `haAreCa(91896) === '9 ha 18 a 96 ca'`, `haAreCa(536) === '5 a 36 ca'`, `haAreCa(27) === '27 ca'`.
- I codici sono unici tra **tutti** i beni: un terreno con il codice di un'unità è un 400, non un 500.
- Commit con `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`; mai committare `deploy/`, `docs/visure/`, `notifiche-followup-fix-report.md`.

## Review Focus

1. Terreni già presenti nel vecchio layout (anche con `unita_misura_superficie = 'ha'`) vengono convertiti senza perdere righe, con superficie in m² → test in Task 1.
2. Un codice già usato da un'unità, scelto per un terreno (o viceversa), dà 400 con messaggio chiaro → test in Task 3.
3. Cancellare un terreno toglie bene, porzioni, diritti e assegnazioni → test in Task 2.
4. Link vecchi `/unita-immobiliari/:id` e `/terreni/:id` (relazioni, contratti, documenti) portano alla scheda del bene → test in Task 5.
5. Un terreno senza indirizzo ha comunque un'etichetta leggibile nelle relazioni e nei documenti (codice · comune) → test in Task 3.

---

### Task 1: migrazione — terreno come specializzazione del bene

**Files:**
- Create: `backend/modules/immobili/migrations/2026111301_terreni_beni.py` (revision `2026111301_terreni_beni`, down_revision `2026111201_beni`, `target_schema = "tenant"`)
- Modify: `backend/modules/immobili/migrations/2025022002_tenant_tables.py` (`EXCLUDED_TABLES` += `immo_terreni_porzioni`; ordine: `immo_beni` prima di `immo_terreni`)
- Modify: `backend/modules/immobili/__manifest__.py`, `backend/app/core/services/tenant_module_service.py` (liste tabelle += `immo_terreni_porzioni` dopo `immo_terreni`)
- Test: `backend/tests/integration/test_modules/test_immobili/test_migrazione_terreni.py`; aggiungi la revisione a `CATENA_TENANT` di `test_migrazione_beni.py`

**Interfaces:**
- Produces: nel modulo di migrazione `converti(conn) -> int` (terreni convertiti; 0 se il layout è già nuovo: si riconosce dalla colonna `comune` su `immo_terreni`) e `crea_porzioni(conn) -> None` (idempotente). `upgrade()` = `crea_porzioni` + `converti`; `downgrade()` solleva `NotImplementedError`.
- `converti`: rinomina `immo_terreni` in `immo_terreni_vecchi`, crea il nuovo `immo_terreni` (vincoli globali), per ogni riga vecchia inserisce il bene (`tipo_bene='TERRENO'`, campi comuni, `sezione` da `sezione_catastale`), la riga terreno con l'id del bene e una porzione (`qualita = coalesce(qualita_coltura, 'NON INDICATA')`, `superficie_mq = superficie * 10000` se `unita_misura_superficie = 'ha'`, altrimenti `superficie`), poi elimina `immo_terreni_vecchi`. Codice già usato da un bene → suffisso `-T`.

- [ ] **Step 1: test**
  - `test_converte_terreno_vecchio_layout`: in uno schema temporaneo (`CREATE SCHEMA tenant_pytest_terreni` nella transazione di `db_session`, `search_path` su quello) crea `immo_beni` come in `2026111201` e un `immo_terreni` col vecchio layout (colonne dell'attuale `models/terreno.py`), inserisce due terreni (`superficie=1.5, unita_misura_superficie='ha'` e `superficie=536, 'mq'`); `converti(conn) == 2`; `immo_beni` ha due righe `TERRENO` con gli stessi codici; porzioni con `superficie_mq` 15000 e 536; `immo_terreni_vecchi` non esiste.
  - `test_converti_su_layout_nuovo_non_fa_nulla`: su `tenant_qa_test` (già migrato) `converti(conn) == 0`.
  - `test_installazione_su_tenant_nuovo` (esistente) con la nuova revisione in coda: `immo_terreni` ha `superficie_mq` e non `comune`; `immo_terreni_porzioni` esiste.
- [ ] **Step 2:** `cd backend && pytest tests/integration/test_modules/test_immobili/test_migrazione_terreni.py tests/integration/test_modules/test_immobili/test_migrazione_beni.py -q --no-cov` → FAIL.
- [ ] **Step 3:** scrivi la migrazione e aggiorna le liste tabelle.
- [ ] **Step 4:** backup del DB di sviluppo in `~/apps/gestione-affitti-backups` (umask 077), poi `alembic -x schema=all upgrade head && python scripts/sync_modules.py`; test → PASS.
- [ ] **Step 5:** commit `feat(immobili): land parcels become beni with portions (migration)`.

### Task 2: modelli ORM — `Terreno(Bene)` e porzioni

**Files:**
- Create: `backend/modules/immobili/models/terreno_porzione.py`
- Modify: `backend/modules/immobili/models/{terreno,__init__}.py`
- Test: `backend/tests/integration/test_modules/test_immobili/test_terreno_bene.py`

**Interfaces:**
- Produces: `class Terreno(Bene)` (`polymorphic_identity="TERRENO"`, `sezione_catastale = synonym("sezione")`, relazione `porzioni` ordinata per `porzione`, `cascade="all, delete-orphan"`, `tipologia` come oggi; proprietà `reddito_dominicale_totale`, `reddito_agrario_totale` → `Decimal | None`, None se nessuna porzione ha il valore); `class TerrenoPorzione(Base)` (`__tablename__ = "immo_terreni_porzioni"`); `Terreno.ricalcola_superficie() -> None` imposta `superficie_mq` = somma delle porzioni.

- [ ] **Step 1: test**
  - `test_terreno_crea_bene_terreno`: `Terreno(codice="T-1", comune="Forlì", provincia="FC", porzioni=[TerrenoPorzione(porzione="AA", qualita="BOSCO CEDUO", classe="2", superficie_mq=363, reddito_dominicale=Decimal("0.25"), reddito_agrario=Decimal("0.09")), TerrenoPorzione(porzione="AB", qualita="PASCOLO", classe="2", superficie_mq=63, reddito_dominicale=Decimal("0.06"), reddito_agrario=Decimal("0.03"))])`; `ricalcola_superficie()`; flush → `immo_beni.tipo_bene == "TERRENO"`, `superficie_mq == 426`, `reddito_dominicale_totale == Decimal("0.31")`, `reddito_agrario_totale == Decimal("0.12")`; `db.get(Bene, id)` è un `Terreno`.
  - `test_cancellare_terreno_cancella_bene_porzioni_e_figli`: terreno + diritto + assegnazione; `db.delete(t)`; flush → nessuna riga in `immo_beni`, `immo_terreni`, `immo_terreni_porzioni`, diritti, assegnazioni per quell'id.
- [ ] **Step 2:** pytest su quel file → FAIL.
- [ ] **Step 3:** implementa.
- [ ] **Step 4:** test → PASS.
- [ ] **Step 5:** commit `feat(immobili): Terreno model as joined subclass of Bene`.

### Task 3: API — terreni con porzioni e `/beni`

**Files:**
- Modify: `backend/modules/immobili/schemas/terreno.py`, `routes/terreni.py`
- Create: `backend/modules/immobili/schemas/bene.py`, `backend/modules/immobili/routes/beni.py` (+ registrazione in `routes/__init__.py` e `get_routers()` di `__init__.py`)
- Modify: `backend/modules/immobili/routes/immobili.py` (variazioni: sposta su `/beni/{id}/variazioni-catastali`), `backend/modules/immobili/__manifest__.py` (tipologie documentali)
- Test: `backend/tests/integration/test_modules/test_immobili/test_terreni_api.py`, `test_beni_api.py`; aggiorna i test delle variazioni e dei terreni esistenti

**Interfaces:**
- Produces (contratto per il frontend, Task 4–5):
  - `TerrenoPorzioneIn/Out`: `porzione, qualita, classe, superficie_mq, reddito_dominicale, reddito_agrario, deduzioni` (+ `id` in uscita).
  - `TerrenoCreate`: `codice, nome?, descrizione?, tipologia_id?, indirizzo?, comune, cap?, provincia, sezione_catastale?, foglio?, particella?, subalterno?, note?, attivo?, edificabile?, esente_imu_montano?, servitu?, porzioni: list[TerrenoPorzioneIn]` (min 1). `TerrenoUpdate`: tutto facoltativo; se c'è `porzioni` le sostituisce. `TerrenoResponse`: i campi + `id, tipo_bene, superficie_mq, reddito_dominicale_totale, reddito_agrario_totale, porzioni, tipologia, created_at, updated_at`.
  - `DELETE /terreni/{id}` → 204, cancellazione vera; `PATCH /terreni/{id}/restore` resta e imposta `attivo=True`; disattivare = `PUT` con `attivo=false`.
  - `GET /beni/?tipo_bene=UNITA|TERRENO&q=&attivo=` → `list[BeneResponse]` (`id, tipo_bene, codice, comune, provincia, indirizzo, sezione, foglio, particella, subalterno, descrizione, attivo`); `q` cerca in codice, indirizzo, comune, `foglio/particella` (es. `"40/154"`). Permesso `immobile.view`.
  - `GET /beni/{id}` → `BeneResponse` o 404 `"Bene non trovato"`.
  - `GET /beni/{id}/variazioni-catastali` (sostituisce `/unita-immobiliari/{id}/variazioni-catastali`).
- Codice duplicato tra beni (create e update, unità e terreni) → 400 `"Codice '<X>' già usato da un altro bene"`.
- Tipologie documentali nuove (`entity_types: IMMOBILE`): `ESTRATTO_MAPPA` "Estratto di mappa" SOSTITUTIVO; `CDU` "Certificato di destinazione urbanistica" SOSTITUTIVO, `scadenza: {"mesi": 12, "da": "data_riferimento"}`, `promemoria_giorni: [30]`; `CONTRATTO_AFFITTO_AGRARIO` "Contratto di affitto agrario" CUMULATIVO. `VARIAZIONE_CATASTALE.sottotipi` += `"TIPO_MAPPALE"`.

- [ ] **Step 1: test**
  - `test_crea_terreno_con_porzioni`: POST con due porzioni (363 + 63 m²) → 201, `superficie_mq == 426`, `len(porzioni) == 2`, `tipo_bene == "TERRENO"`.
  - `test_crea_terreno_senza_porzioni_422`.
  - `test_update_sostituisce_porzioni`: PUT con una porzione da 1000 → `superficie_mq == 1000`, una sola porzione.
  - `test_codice_gia_usato_da_unita_400`: unità `X-1`, poi terreno `X-1` → 400 con `"già usato da un altro bene"`; e viceversa (unità con codice di un terreno).
  - `test_delete_terreno_cancella`: DELETE → 204, `GET /terreni/{id}` → 404.
  - `test_beni_elenco_filtra_e_cerca`: un'unità e un terreno (`foglio="40", particella="154"`); `tipo_bene=TERRENO` → solo il terreno; `q="40/154"` → il terreno; `GET /beni/{id}` dell'unità → `tipo_bene == "UNITA"`; id inesistente → 404.
  - `test_etichetta_terreno_senza_indirizzo`: `entity_label_registry.labels(db, "IMMOBILE", [t.id]) == {t.id: "T-9 · Forlì"}` (niente `None`, niente virgola penzolante): adegua `_immobile_labels` e `_DESCRIZIONI_CORE["IMMOBILE"]`/`relations._indirizzo` a `concat_ws(', ', indirizzo, comune)` che già salta i NULL, e il formato `codice · ` + parti non vuote.
- [ ] **Step 2:** `./run_tests.sh integration` sui file nuovi → FAIL.
- [ ] **Step 3:** implementa; route chiamate direttamente nei test come in `test_bene_model.py` (utente `SimpleNamespace(id=1)` dove serve).
- [ ] **Step 4:** `cd backend && pytest tests -q --no-cov` → tutto PASS.
- [ ] **Step 5:** commit `feat(immobili): land API with portions, /beni endpoints, land document types`.

### Task 4: frontend — formulario e lista dei terreni

**Files:**
- Modify: `frontend/src/modules/immobili/components/Terreni/{TerrenoForm,TerreniList}.jsx`, `frontend/src/modules/immobili/services/immobiliAPI.js` (`beniAPI`, `terreniAPI` invariato nei nomi)
- Create: `frontend/src/modules/immobili/components/Terreni/PorzioniEditor.jsx`, `frontend/src/modules/immobili/utils/superficie.js`
- Test: `superficie.test.js`, `PorzioniEditor.test.jsx`

**Interfaces:**
- Consumes: contratto Task 3.
- Produces: `haAreCa(mq: number) -> string` (vincolo globale); `beniAPI.getAll(params)`, `beniAPI.getById(id)`, `beniAPI.getVariazioni(id)`; `<PorzioniEditor value={porzioni} onChange={fn} />` (righe con porzione, qualità, classe, superficie m², redditi, deduzioni; aggiungi/togli riga; almeno una riga, il pulsante "togli" è disabilitato sull'ultima).
- Form terreno: campi comuni + tipologia, nome, edificabile, esente IMU montano, servitù, porzioni; niente più superficie/unità di misura/qualità/classe/redditi singoli. `Button` del design system, ordine Annulla poi Salva.
- Lista: colonna Codice come link a `/beni/:id`; Superficie con `haAreCa(superficie_mq)`; azione "Elimina" (conferma con `ConfirmDialog` se esiste nel design system, altrimenti `window.confirm` come oggi) che chiama `terreniAPI.delete`; "Disattiva/Ripristina" con `terreniAPI.update(id, {attivo})`.

- [ ] **Step 1: test** `haAreCa` (tre valori del vincolo, più `0 → '0 ca'`); `PorzioniEditor`: aggiunge una riga, non toglie l'ultima, `onChange` riceve `superficie_mq` numerico.
- [ ] **Step 2:** `cd frontend && npx vitest run src/modules/immobili` → FAIL.
- [ ] **Step 3:** implementa.
- [ ] **Step 4:** test → PASS; `npm run build` ok.
- [ ] **Step 5:** commit `feat(immobili-ui): land form with portions and clickable land list`.

### Task 5: frontend — scheda del bene

**Files:**
- Rename: `components/ImmobileScheda/ImmobileScheda.jsx` → `components/BeneScheda/BeneScheda.jsx` (con CSS, test, `VariazioniCatastali`, `formatters`); export `BeneScheda` da `modules/immobili/index.js`
- Create: `components/BeneScheda/DatiUnita.jsx`, `components/BeneScheda/DatiTerreno.jsx`
- Modify: `frontend/src/App.jsx` (route), `core/components/Relazioni/RelazioniSection.jsx:13`, `components/UnitaImmobiliari/UnitaImmobiliariList.jsx:42`, `components/Documenti/DocumentiImmobiliPage.jsx:113`, `pages/ContrattoDetail.jsx:357,525`, `pages/ImmobiliHome.jsx:115`, `components/UnitaImmobiliari/UnitaImmobiliareForm.jsx:384`
- Test: `BeneScheda.test.jsx` (da `ImmobileScheda.test.jsx`), `App` route test se esiste un pattern, altrimenti nel test della scheda con `MemoryRouter`

**Interfaces:**
- Consumes: `beniAPI.getById`, `unitaImmobiliariAPI.getById`, `terreniAPI.getById`, `beniAPI.getVariazioni`, `haAreCa`.
- Route: `/beni/:id` → `BeneScheda`; `/unita-immobiliari/:id` e `/terreni/:id` → `<Navigate to="/beni/:id" replace />` (componente `RedirectABene`). Tutti i link interni puntano a `/beni/${id}`.
- `BeneScheda`: carica `beniAPI.getById(id)`, poi i dati del tipo (`unitaImmobiliariAPI.getById` o `terreniAPI.getById`); intestazione `codice · tipo` (unità) o `codice · nome || 'Terreno'` (terreno); "Torna a" porta a `/unita-immobiliari` o `/terreni`; sezione Dati = `<DatiUnita>` (com'è oggi) o `<DatiTerreno>` (foglio/particella, sezione, tipologia, superficie `haAreCa`, redditi totali, edificabile, esente IMU montano, servitù, tabella porzioni con superficie in `haAreCa` e redditi in euro); "Modifica" apre `UnitaImmobiliareForm` o `TerrenoForm`; le altre sezioni (documenti `IMMOBILE`, variazioni, diritti, conduttori, spese, scadenze, extension point `immobile.detail.sections`) uguali per entrambi.

- [ ] **Step 1: test**
  - `mostra la tabella delle porzioni di un terreno`: mock `beniAPI.getById` → `{tipo_bene: 'TERRENO'}`, `terreniAPI.getById` → terreno con porzioni AA/AB → righe "BOSCO CEDUO", "3 a 63 ca", "PASCOLO"; intestazione col codice.
  - `mostra i dati dell'unità`: come il test attuale di `ImmobileScheda`.
  - `il vecchio link /terreni/:id porta alla scheda del bene`: `MemoryRouter initialEntries={['/terreni/7']}` con le route di App per beni → `beniAPI.getById` chiamato con `'7'`.
- [ ] **Step 2:** `npx vitest run src/modules/immobili` → FAIL.
- [ ] **Step 3:** implementa; nessun link rimasto a `/unita-immobiliari/${` o `/terreni/${` (`grep -rn` nel frontend, esclusi gli endpoint API).
- [ ] **Step 4:** test e build → PASS. Riavvia il backend dev (non ricarica `modules/`), crea via API un terreno con due porzioni e un diritto in `tenant_qa_test`, apri `/beni/:id` col crawler (scratchpad `crawl.mjs`): nessuna chiamata fallita, porzioni visibili; cancella i dati di prova.
- [ ] **Step 5:** commit `feat(immobili-ui): one detail page for units and land`.

### Task 6: documentazione, verifica, rilascio

**Files:**
- Modify: `docs/modules/immobili.md` (§2 terreni, beni, API `/beni`, tipologie nuove; §5 togli "terreni isolati"), spec beni (fase 2a fatta; 2b collegamenti e chi paga cosa), `docs/piattaforma.md` solo se cambia qualcosa di piattaforma

- [ ] **Step 1:** aggiorna i documenti; `bash scripts/controlla_documentazione.sh master HEAD` → ok.
- [ ] **Step 2:** revisione finale del ramo (revisore nuovo, Sonnet), correzioni con test RED→GREEN.
- [ ] **Step 3:** agente `verifica-test` → VERDE.
- [ ] **Step 4:** agente `rilascio` (niente `PROMOTE_PERDITA_CONSENTITA`: la migrazione non deve perdere righe; se il controllo segnala perdite, fermarsi).
