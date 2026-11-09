# Tipologie documentali dei moduli — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Modules declare their document types (scadenza, regime sostitutivo/cumulativo, optional form/reader) in the manifest. The core offers upload, history, scadenze and consultation. Immobili gets its own types (Visura, APE…), a document history, a log of catastal changes, a unit detail page and a documents page.

**Architecture:**
- Manifest `document_types` is the single source. `sync_document_types()` upserts them into `public.core_tipi_documento`. It runs when a module is registered/installed and on every `scripts/sync_modules.py` run (i.e. every `promote.sh`), **not** at every app start.
- A core `DocumentoService` applies the history rules (CORRENTE/SOSTITUITO) and keeps a linked core `Scadenza`.
- Frontend:
  - a core `DocumentiPanel` + `DocumentoUpload` reads types from the API;
  - module forms are discovered via `import.meta.glob('/src/modules/*/documentForms.js')`.

**Tech Stack:** FastAPI, SQLAlchemy, Alembic (core chain + module chains), PostgreSQL multi-schema; React + Vite, Vitest, lucide-react, design system tokens/components.

**Spec:** `docs/superpowers/specs/2026-11-09-tipologie-documentali-moduli-design.md`

## Global Constraints

- **Production data must be preserved.**
  - No migration drops or truncates.
  - `immo_certificati_energetici` and the `tipo_documento` enum column stay.
  - A type missing from every manifest becomes `attivo = false`, never deleted.
- Existing DB type codes stay unchanged. In particular it is `PATENTE`, not `PATENTE_GUIDA`.
- `regime` ∈ {`SOSTITUTIVO`, `CUMULATIVO`}.
- `stato` ∈ {`CORRENTE`, `SOSTITUITO`}.
- APE scadenza: `{"mesi": 120, "da": "data_riferimento"}`. Default `promemoria_giorni`: `[90, 30]`.
- Core chain migrations go in `backend/alembic/versions/`, with `target_schema` = `"public"` or `"tenant"` (see `2026103001_tipodiritto_extra_values.py`). Immobili tenant tables go in `backend/modules/immobili/migrations/`.
- UI:
  - design system only: tokens from `styles/tokens.css`, `components/UI` (Button, Badge, Card, FormField), icons via `renderIcon` / lucide;
  - no Font Awesome;
  - CSS scoped under the component root class;
  - `FormModal` imported from `core/components/FormBuilder/FormModal` directly.
- Italian UI copy. Code, identifiers and comments in English.
- Never commit `deploy/`, `docs/visure/`, `notifiche-followup-fix-report.md`.
- Bugs on real data are reproduced on the replica (`scripts/replica_produzione.sh`), never on prod.

## Review Focus

1. **Uploading an older document of a SOSTITUTIVO type** (e.g. a 2019 APE when a 2024 one exists). It must enter as SOSTITUITO and leave the current one and its scadenza untouched. Test in Task 4.
2. **Deleting the CORRENTE document** must re-promote the most recent SOSTITUITO and move the scadenza to it. Deleting the last one closes the scadenza. Test in Task 4.
3. **Re-running the sync** (twice in a row, or after a tenant override) must not duplicate rows and must not overwrite tenant overrides. A tenant override must still win on `nome` / `richiede_scadenza`. Test in Task 2.
4. **Re-running the APE migration**, or running it on a tenant without APE rows, must create no duplicate documents. Rows whose `file_path` points to a missing file still become documents, with no file. Test in Task 8.
5. **Legacy documents** (only the `tipo_documento` enum, `tipo_documento_id` NULL, no `stato`) must still be listed after the migration, under their mapped type or under `ALTRO_IMMOBILE` / `DOCUMENTO_GENERICO`. Test in Task 1.

---

## Phase A — Backend: types, history, scadenze, catastal log

### Task 1: Schema — new columns on types and documents

**Files:**
- Create: `backend/alembic/versions/2026110901_tipi_documento_manifest_fields.py` (`target_schema = "public"`, down_revision `2026103001`)
- Create: `backend/alembic/versions/2026110902_documenti_storico.py` (`target_schema = "tenant"`, down_revision `2026110901`)
- Modify: `backend/app/core/platform/models/tipo_documento.py`, `backend/app/core/platform/models/documento.py`
- Test: `backend/tests/integration/test_core/test_documenti_storico_migration.py`

**Interfaces:**
- Produces:
  - `TipoDocumento` gains:
    - `modulo: str|None`
    - `entity_types: list[str]|None` (JSON)
    - `regime: str` (default `'CUMULATIVO'`, server_default too)
    - `sottotipi: list[str]|None` (JSON)
    - `scadenza: dict|None` (JSON)
    - `promemoria_giorni: list[int]|None` (JSON)
    - `form: str|None` (String(100))
  - `Documento` gains:
    - `data_riferimento: date|None`
    - `stato: str` (String(20), server_default `'CORRENTE'`, indexed)
    - `sostituito_da_id: int|None` (FK `core_documenti.id`, ON DELETE SET NULL)
    - `sottotipo: str|None` (String(50))
    - `dati: dict|None` (JSON)
    - `scadenza_id: int|None` (FK core scadenze table, ON DELETE SET NULL)

- [ ] **Step 1:** Write test `test_backfill_legacy_documents`. On a test tenant, insert a `core_documenti` row with only `tipo_documento='VISURA_CATASTALE'`, `tipo_documento_id=NULL` and `metadata_parsato={"data_visura": "2024-05-10"}`. Run the tenant migration's backfill function `backfill(conn)`. Assert:
  - `stato == 'CORRENTE'`;
  - `data_riferimento == date(2024, 5, 10)`;
  - `tipo_documento_id` equals the id of code `VISURA_CATASTALE` in `public.core_tipi_documento`.
  Also: a row with an enum value without a matching code keeps `tipo_documento_id` NULL and gets `data_riferimento = created_at::date`.
- [ ] **Step 2:** Run `cd backend && source venv/bin/activate && pytest tests/integration/test_core/test_documenti_storico_migration.py -v`. Expected: FAIL (module/columns missing).
- [ ] **Step 3:** Implement both migrations (add-column only) and the model columns. The tenant migration exposes `backfill(conn)` and calls it in `upgrade()`. Backfill rules:
  - `stato` = `'CORRENTE'`;
  - `data_riferimento` = `COALESCE((metadata_parsato->>'data_visura')::date, created_at::date)`;
  - `tipo_documento_id` from `public.core_tipi_documento.codice = tipo_documento::text` where NULL.
- [ ] **Step 4:** Run the test (PASS), then `alembic -x schema=all upgrade head` on dev. Expected: no error.
- [ ] **Step 5:** Commit `feat(core-documenti): manifest fields on tipi documento, history columns on documenti`.

### Task 2: Manifest → table sync

**Files:**
- Create: `backend/app/core/platform_services/document_type_sync.py`
- Modify:
  - `backend/app/core/platform_services/document_type_registry.py` (`DocumentTypeDefinition` gets the new fields + validation);
  - `backend/app/core/module_system/loader.py:399` and `:606` (call sync after `register_from_manifest`, with the loader's db session, schema public);
  - `backend/scripts/sync_modules.py` (new step "==> Tipologie documentali" after the public seeds, over all registered manifests);
  - `backend/app/core/platform/` or the existing Configurazioni route that lists types: return `modulo`, `regime`, `scadenza`, `form`.
- Test: `backend/tests/unit/test_core/test_document_type_sync.py` (DB-backed, public schema of the test DB)

**Interfaces:**
- Produces:
  - `sync_document_types(db: Session, manifests: dict[str, dict]) -> SyncReport`, where `SyncReport` is a dataclass with `creati: list[str]`, `aggiornati: list[str]`, `disattivati: list[str]`.
  - `apply_override(tipo: TipoDocumento, override: TipoDocumentoOverride|None) -> dict|None`. It returns None when `is_deleted`. It is extracted from `anagrafica_italiana/routes/domini.py:list_tipi_documento`, which must now call it.
- `DocumentTypeDefinition` validation raises `ValueError` when:
  - `regime` is not in the allowed set;
  - an `entity_types` item is not an `EntityType` value;
  - `scadenza` is neither None, `{"manuale": True}` nor `{"mesi": int>0, "da": "data_riferimento"}`.
  `richiede_scadenza` is derived: `scadenza is not None`.

- [ ] **Step 1:** Write tests:
  - `test_sync_creates_and_updates`: two manifests produce rows with `modulo` set; calling it again yields `creati == []` and `aggiornati == []`.
  - `test_sync_deactivates_missing`: a pre-existing row whose code is in no manifest ends with `attivo is False` and still exists.
  - `test_sync_keeps_tenant_override`: an override with `nome='Mio nome'` still wins in `apply_override` after the sync.
  - `test_invalid_regime_rejected`: `ValueError`.
  - `test_duplicate_codice_across_modules`: the second module loses and the report/log names both.
- [ ] **Step 2:** Run `pytest tests/unit/test_core/test_document_type_sync.py -v`. Expected: FAIL.
- [ ] **Step 3:** Implement. Upsert key: `codice`. Fields owned by the manifest are overwritten on every sync: `nome, descrizione, categoria, modulo, entity_types, regime, sottotipi, scadenza, promemoria_giorni, form, parsing_service, parsing_config, richiede_scadenza`, plus `attivo = True`. Deactivation applies only to rows not produced by any manifest in the call **and** whose `modulo` is NULL or belongs to a module present in `manifests`. A partial call must not deactivate other modules' types.
- [ ] **Step 4:** Run the tests (PASS). Run `python scripts/sync_modules.py --dry-run`. Expected: the new step is listed.
- [ ] **Step 5:** Commit `feat(core-documenti): sync document types from module manifests`.

### Task 3: Declarations — anagrafica and immobili manifests

**Files:**
- Modify:
  - `backend/modules/anagrafica_italiana/__manifest__.py` (`document_types` = union of the current manifest list and `seeds/seed_tipi_documento.py`, using the **seed's codes**; entity_types `["SOGGETTO_ANAGRAFICO"]`; regime CUMULATIVO except identity documents, which are SOSTITUTIVO with sottotipo none; keep the existing `parsing_*`);
  - `backend/modules/anagrafica_italiana/seeds/seed_public.py` (stop calling the tipi documento seed; delete `seed_tipi_documento.py`);
  - `backend/modules/immobili/__manifest__.py` (`document_types`, table below).
- Test: `backend/tests/unit/test_modules/test_document_types_manifests.py`

Immobili types (all `entity_types: ["IMMOBILE"]`, `categoria: "immobiliare"`):

| codice | nome | regime | sottotipi | scadenza | form | parsing_service |
|---|---|---|---|---|---|---|
| VISURA_CATASTALE | Visura catastale | SOSTITUTIVO | – | None | `immobili.visura` | – |
| PLANIMETRIA_CATASTALE | Planimetria catastale | SOSTITUTIVO | – | None | – | – |
| VARIAZIONE_CATASTALE | Variazione catastale | CUMULATIVO | DOCFA, VOLTURA, FRAZIONAMENTO, FUSIONE | None | – | – |
| APE | Attestato di prestazione energetica | SOSTITUTIVO | – | `{"mesi":120,"da":"data_riferimento"}` | `immobili.ape` | – |
| ATTO_PROVENIENZA | Atto di provenienza | CUMULATIVO | COMPRAVENDITA, SUCCESSIONE, DONAZIONE | None | – | – |
| CONFORMITA_IMPIANTO | Dichiarazione di conformità impianto | SOSTITUTIVO | ELETTRICO, GAS, TERMICO, IDRICO | None | – | – |
| LIBRETTO_IMPIANTO | Libretto impianto termico / controllo | CUMULATIVO | – | `{"manuale":true}` | – | – |
| AGIBILITA | Agibilità / abitabilità | SOSTITUTIVO | – | None | – | – |
| TITOLO_EDILIZIO | Titolo edilizio | CUMULATIVO | – | None | – | – |
| POLIZZA_FABBRICATO | Polizza assicurativa fabbricato | SOSTITUTIVO | – | `{"manuale":true}` | – | – |
| ALTRO_IMMOBILE | Altro documento | CUMULATIVO | – | None | – | – |

- [ ] **Step 1:** Write tests:
  - `test_manifests_validate`: every entry of both manifests builds a `DocumentTypeDefinition` without error.
  - `test_existing_db_codes_preserved`: every code of the old seed file (list hard-coded in the test) is present in the anagrafica manifest.
  - `test_visura_owned_by_immobili`: `VISURA_CATASTALE` is in the immobili manifest only.
- [ ] **Step 2:** Run. Expected: FAIL.
- [ ] **Step 3:** Edit the manifests and the seed as described.
- [ ] **Step 4:** Run the tests (PASS). Run `python scripts/sync_modules.py` on dev. Expected: report with VISURA_CATASTALE `aggiornati` (modulo now `immobili`) and the 10 new immobili types `creati`.
- [ ] **Step 5:** Commit `feat(documenti): anagrafica and immobili declare their document types in the manifest`.

### Task 4: DocumentoService — creation, history, deletion, scadenza

**Files:**
- Create: `backend/app/core/platform_services/documento_service.py`
- Test: `backend/tests/integration/test_core/test_documento_service.py`

**Interfaces:**
- Consumes: Task 1 columns, Task 2 `apply_override`, `ScadenzaService` (`create_scadenza`, `update_scadenza`, `completa_scadenza`), `file_storage.save_file`, `DocumentoFile`.
- Produces:
  ```python
  @dataclass
  class FileInput: content: bytes; filename: str; mime_type: str | None

  class DocumentoService:
      def __init__(self, db: Session, tenant_schema: str, user_id: int | None): ...
      def tipi_per_entita(self, entity_type: EntityType) -> list[dict]  # active, override-merged, filtered by entity_types
      def crea(self, *, entity_type: EntityType, entity_id: int, tipo_codice: str,
               files: list[FileInput], data_riferimento: date | None = None,
               sottotipo: str | None = None, data_scadenza: date | None = None,
               dati: dict | None = None, descrizione: str | None = None,
               note: str | None = None, metadata_parsato: dict | None = None) -> Documento
      def elimina(self, documento_id: int) -> None
      def storico(self, documento_id: int) -> list[Documento]  # same entity+tipo(+sottotipo), newest first
      def scadenza_effettiva(self, documento: Documento) -> date | None
  ```
- Rules:
  - **Calculated scadenza:** `data_riferimento + mesi`, via `dateutil.relativedelta`.
  - **Manual scadenza:** `data_scadenza` is required, else `ValueError("Scadenza obbligatoria per <nome>")`.
  - **APE override:** `scadenza_effettiva` = `dati["decaduto_il"]` when present and earlier.
  - **Unknown or inactive `tipo_codice`:** ValueError.
  - **`sottotipo`:** must be in `tipo.sottotipi` when the latter is set.
  - **Missing `data_riferimento`:** defaults to today.
  - **SOSTITUTIVO group:** `(entity_type, entity_id, tipo_documento_id, sottotipo)`.
  - **Scadenza on create:** a CORRENTE document with an effective scadenza gets a `Scadenza`:
    - modulo = `tipo.modulo`, entity_type/entity_id = the document's entity;
    - titolo = `f"{tipo.nome} in scadenza"`, priorità ALTA;
    - destinatari empty.
  - **Scadenza on supersede:** the superseded document's scadenza is completed via `completa_scadenza` (note "Sostituito da documento <id>").
- [ ] **Step 1:** Write tests (unit = one test each):
  - `test_cumulativo_always_corrente`
  - `test_sostitutivo_newer_supersedes` (the old one gets `stato == 'SOSTITUITO'`, `sostituito_da_id == new.id`, and its scadenza completed)
  - `test_sostitutivo_older_goes_to_storico` (Review Focus 1)
  - `test_sottotipo_groups_independently` (ELETTRICO and GAS both CORRENTE)
  - `test_ape_scadenza_calcolata` (2024-03-15 → 2034-03-15)
  - `test_manual_scadenza_required`
  - `test_elimina_corrente_ripromuove` (Review Focus 2: the most recent SOSTITUITO becomes CORRENTE and gets a new open scadenza)
  - `test_elimina_ultimo_chiude_scadenza`
  - `test_tipi_per_entita_filters_and_overrides`
- [ ] **Step 2:** Run `pytest tests/integration/test_core/test_documento_service.py -v`. Expected: FAIL.
- [ ] **Step 3:** Implement. Files are saved with `file_storage.save_file`, one `DocumentoFile` each. Also fill the legacy `nome_file`/`file_path`/`mime_type`/`dimensione` from the first file. On any exception, delete the saved files, then re-raise (same pattern as `visura_import_service.apply_proposal`).
- [ ] **Step 4:** Run (PASS).
- [ ] **Step 5:** Commit `feat(core-documenti): DocumentoService with history rules and linked scadenze`.

### Task 5: Core documents API

**Files:**
- Modify: `backend/app/core/routes/documenti.py`, `backend/app/core/schemas/` (DocumentoResponse)
- Test: `backend/tests/integration/test_core/test_documenti_api.py`

**Interfaces:**
- Consumes: Task 4.
- Produces:
  - `GET /api/v1/documenti/tipi?entity_type=IMMOBILE` → `list[TipoDocumentoOut]`. Fields: `id, codice, nome, categoria, modulo, regime, sottotipi, scadenza, richiede_scadenza, form, parsing_service`.
  - `GET /api/v1/documenti?entity_type=&entity_id=&tipo_codice=&includi_sostituiti=false&modulo=&scadenza_entro_giorni=` → `list[DocumentoOut]`.
    - Without `entity_id` it lists across entities (used by the immobili documents page).
    - `modulo` filters by `tipo.modulo`.
  - `DocumentoOut` adds: `tipo_codice, tipo_nome, regime, data_riferimento, stato, sostituito_da_id, sottotipo, dati, data_scadenza_effettiva, files: [{id, nome_file, mime_type}]`.
  - `POST /api/v1/documenti/upload` (multipart):
    - fields: `files: list[UploadFile]`, `entity_type`, `entity_id`, `tipo_codice`, optional `data_riferimento`, `sottotipo`, `data_scadenza`, `dati` (JSON string), `descrizione`, `note`;
    - the old `file` + `tipo_documento` enum fields stay accepted: they are mapped to `files=[file]`, `tipo_codice=tipo_documento.value`, and to `ALTRO_IMMOBILE`/`DOCUMENTO_GENERICO` when the code has no row;
    - a ValueError from the service becomes 422 with the message.
  - `GET /api/v1/documenti/{id}/storico` → `list[DocumentoOut]`.
  - `DELETE /api/v1/documenti/{id}` → `DocumentoService.elimina`.
  - `GET /api/v1/documenti/files/{file_id}/view` → inline file (`Content-Disposition: inline`) for preview.
- [ ] **Step 1:** Write API tests:
  - upload APE without `data_riferimento` → 201 with today's date and scadenza +10y;
  - legacy single-file upload still works;
  - list hides SOSTITUITO by default and shows it with `includi_sostituiti=true`;
  - `tipi` for IMMOBILE contains APE and not CARTA_IDENTITA;
  - `dati` invalid JSON → 422;
  - view endpoint returns `inline`.
- [ ] **Step 2:** Run. Expected: FAIL.
- [ ] **Step 3:** Implement. Permissions: the same `documenti.write` / read deps as the existing routes.
- [ ] **Step 4:** Run (PASS). Run the whole `pytest tests/integration/test_core -q`: no regressions.
- [ ] **Step 5:** Commit `feat(core-documenti): API for types per entity, multi-file upload, history, preview`.

### Task 6: Catastal changes log + visura import on DocumentoService

**Files:**
- Create:
  - `backend/modules/immobili/migrations/2026110901_variazioni_catastali.py` (tenant, down_revision `2026092301`);
  - `backend/modules/immobili/models/variazioni_catastali.py` (`VariazioneCatastale`, table `immo_variazioni_catastali`);
  - `backend/modules/immobili/services/variazioni_catastali.py`.
- Modify:
  - `backend/modules/immobili/services/visura_import_service.py:apply_proposal`;
  - `backend/modules/immobili/routes/immobili.py:51` (PUT);
  - add `GET /unita-immobiliari/{id}/variazioni-catastali`.
- Test:
  - `backend/tests/integration/test_modules/test_immobili_visura/test_visura_import.py` (extend);
  - `backend/tests/integration/test_modules/test_variazioni_catastali.py`.

**Interfaces:**
- Columns: `id, unita_immobiliare_id (FK, indexed), documento_id (nullable, no FK across chains: plain Integer), origine ('VISURA'|'MANUALE'), campo, valore_precedente (Text), valore_nuovo (Text), data_riferimento (Date), created_at, utente_id`.
- `CAMPI_CATASTALI = ("categoria_catastale_id", "classe", "consistenza", "superficie_mq", "rendita_catastale", "foglio", "particella", "subalterno", "indirizzo", "piano")`. The implementer aligns these names with the actual `UnitaImmobiliare` columns; `UPDATABLE_FIELDS` of the visura service is the reference.
- `registra_variazioni(db, unita: UnitaImmobiliare, nuovi: dict, *, origine: str, documento_id: int|None, data_riferimento: date, utente_id: int|None) -> list[VariazioneCatastale]`. It compares the current values with `nuovi`, only for `CAMPI_CATASTALI`, writes one row per changed field and returns them. It does **not** set the attributes.
- In `apply_proposal`:
  - create the visura document **before** applying the changes, via `DocumentoService.crea(... tipo_codice="VISURA_CATASTALE", data_riferimento=proposta.data_visura, metadata_parsato={...as today...})`;
  - then `registra_variazioni(origine="VISURA", documento_id=doc.id)`;
  - then setattr.
  - The duplicate check `_has_visura` stays.
- PUT unit: `registra_variazioni(origine="MANUALE", documento_id=None, data_riferimento=date.today())` before applying the update.
- [ ] **Step 1:** Write tests:
  - `test_apply_logs_variazioni`: an existing unit with rendita 500 and a visura with 600 give one row `('rendita_catastale','500','600', origine='VISURA', documento_id=<visura doc>)`;
  - `test_apply_visura_older_than_current_goes_storico`: importing the 2022 visura after the 2024 one leaves the 2024 CORRENTE;
  - `test_put_logs_manual_change`;
  - `test_put_no_change_no_rows`;
  - `test_get_variazioni_newest_first`.
- [ ] **Step 2:** Run. Expected: FAIL.
- [ ] **Step 3:** Implement. Run `python scripts/sync_modules.py` on dev to apply the module migration.
- [ ] **Step 4:** Run these tests plus the full `pytest tests -k visura -q` (PASS).
- [ ] **Step 5:** Commit `feat(immobili): catastal changes log; visura import uses core DocumentoService`.

## Phase B — APE as a core document

### Task 7: APE data migration

**Files:**
- Create: `backend/modules/immobili/migrations/2026110902_ape_to_documenti.py` (tenant, down_revision `2026110901`; `downgrade` = no-op with a comment, because it never deletes)
- Test: `backend/tests/integration/test_modules/test_ape_migration.py`

**Interfaces:**
- `migra_ape(conn) -> dict` returns `{"letti": n, "creati": n, "saltati": n, "senza_file": n}`.
- Each `immo_certificati_energetici` row becomes:
  - `core_documenti`: entity IMMOBILE / `unita_immobiliare_id`, tipo APE;
  - `data_riferimento = data_emissione`, `data_scadenza` copied;
  - `dati = {"classe": ..., "ep_gl_nren": indice_prestazione_energetica, "codice_identificativo": numero_protocollo, "tecnico_id": ..., "certificato_id": row.id}`, `note` copied;
  - plus a `core_documenti_files` row pointing to the same `file_path` if the file exists on disk.
- Idempotent: skip rows whose `certificato_id` already appears in `dati`.
- After the insert, per unit, apply the SOSTITUTIVO rule in SQL: latest `data_riferimento` CORRENTE, others SOSTITUITO with `sostituito_da_id`.
- Scadenze for the CORRENTE ones: `DocumentoService.allinea_scadenze(tipo_codice)` (defined in this task, added to the service from Task 4). It creates the missing open scadenza for every CORRENTE document of that type that has an effective scadenza and no `scadenza_id`. `sync_modules.py` calls it for every type with `scadenza` set, per tenant, after the migrations; it is idempotent.
- [ ] **Step 1:** Write tests:
  - `test_migra_ape_counts` (3 certificates on 2 units → 3 docs, one unit with CORRENTE+SOSTITUITO);
  - `test_migra_ape_idempotent` (Review Focus 4: second run `creati == 0`);
  - `test_migra_ape_missing_file`;
  - `test_allinea_scadenze_idempotent`.
- [ ] **Step 2:** Run. Expected: FAIL.
- [ ] **Step 3:** Implement.
- [ ] **Step 4:** Run (PASS). Then on the **replica**: `bash scripts/replica_produzione.sh`, then `python scripts/sync_modules.py`. Check: count of `immo_certificati_energetici` == count of APE `core_documenti` in `tenant_produzione`.
- [ ] **Step 5:** Commit `feat(immobili): migrate energy certificates to core APE documents`.

### Task 8: APE endpoints for the immobili UI

**Files:**
- Modify:
  - `backend/modules/immobili/routes/certificati_energetici.py`: GET endpoints read APE documents. POST/PUT/DELETE return 410 with detail "Usa /documenti (tipo APE)";
  - the router keeps its path so the widget/list can switch gradually.
- Test: `backend/tests/integration/test_modules/test_certificati_energetici_api.py` (update existing)

**Interfaces:**
- `GET /certificati-energetici/` and `/unita-immobiliare/{id}` keep `CertificatoEnergeticoResponse`. They are built from CORRENTE APE documents:
  - `id` = documento id; `classe_energetica` = `dati.classe`; `indice_prestazione_energetica` = `dati.ep_gl_nren`;
  - `data_emissione` = `data_riferimento`; `data_scadenza` = effective scadenza; `numero_protocollo` = `dati.codice_identificativo`;
  - `tecnico_id` from `dati`.
- `/unita-immobiliare/{id}/valido` uses the effective scadenza.
- [ ] **Step 1:** Update the tests to create APE via `DocumentoService` and assert the same response shapes; POST → 410.
- [ ] **Step 2:** Run. Expected: FAIL.
- [ ] **Step 3:** Implement.
- [ ] **Step 4:** Run (PASS).
- [ ] **Step 5:** Commit `refactor(immobili): energy certificate endpoints read core APE documents`.

## Phase C — Frontend

### Task 9: Core documents UI — API, upload, panel, form registry

**Files:**
- Create:
  - `frontend/src/core/services/documentiAPI.js`;
  - `frontend/src/core/documenti/documentForms.js`;
  - `frontend/src/core/components/Documenti/DocumentoUpload.jsx` + `.css`;
  - `DocumentiPanel.jsx` + `.css`;
  - `DocumentoPreview.jsx`.
- Modify: `frontend/src/components/Documenti/DocumentiSection.jsx`. It becomes a wrapper: `({entityType, entityId}) => <DocumentiPanel .../>`, so contracts, condomini, affittuari etc. get the new panel. Delete the old `components/Documenti/DocumentoUpload.jsx`.
- Test: `frontend/src/core/components/Documenti/__tests__/DocumentiPanel.test.jsx`, `DocumentoUpload.test.jsx`

**Interfaces:**
- `documentiAPI`: `getTipi(entityType)`, `list(params)`, `upload(formData)`, `storico(id)`, `remove(id)`, `downloadUrl(id)`, `viewUrl(fileId)`.
- `getDocumentForm(key: string): React.LazyExoticComponent | null`. It reads `import.meta.glob('/src/modules/*/documentForms.js', { eager: true })`; each module file exports `default { '<key>': () => import('...') }`.
- Form contract (props every module form receives): `{ entityType, entityId, tipo, initialFiles: File[], onSaved: (documento) => void, onCancel: () => void }`.
- `DocumentoUpload` props: `{ entityType, entityId, tipi, initialTipoCodice?, onSaved, onCancel }`. Behaviour:
  1. type select grouped by `categoria`;
  2. drag & drop multi-file dropzone (same pattern/CSS tokens as `ImportVisuraModal`);
  3. if `tipo.form`, render the registered form with `initialFiles`;
  4. otherwise show `data_riferimento` (default today), the `sottotipo` select if `sottotipi`, and `data_scadenza` (required when `scadenza.manuale`; read-only computed preview when `scadenza.mesi`);
  5. submit via `documentiAPI.upload`.
- `DocumentiPanel` props: `{ entityType, entityId, modulo? }`.
  - One row per type that has documents: name, Badge "In vigore"/"Scaduto"/"In scadenza" (≤ 90 days), `data_riferimento`, preview/download buttons, link "Storico (n)" that expands the SOSTITUITO list.
  - Button "Carica documento" opens `DocumentoUpload` in `FormModal`.
  - Empty state "Nessun documento".
  - Legacy documents without a type go under "Altro".
- `DocumentoPreview`: modal with `<iframe>` for PDF / `<img>` for images from `viewUrl`.
- [ ] **Step 1:** Write vitest tests (mock `documentiAPI`):
  - panel groups by type and hides SOSTITUITO until "Storico (1)" is clicked;
  - badge "Scaduto" when the effective scadenza < today;
  - upload shows the date field required for a `{manuale:true}` type and blocks submit without it;
  - upload with `form: 'test.form'` renders the registered form (mock `getDocumentForm`);
  - dropping 2 files lists both.
- [ ] **Step 2:** Run `cd frontend && npx vitest run src/core/components/Documenti`. Expected: FAIL.
- [ ] **Step 3:** Implement.
- [ ] **Step 4:** Run (PASS) and `npm run test:run` (no regressions from the `DocumentiSection` wrapper).
- [ ] **Step 5:** Commit `feat(core-documenti): document panel, typed upload and module form registry`.

### Task 10: Immobili document forms (Visura, APE)

**Files:**
- Create:
  - `frontend/src/modules/immobili/documentForms.js`;
  - `frontend/src/modules/immobili/components/Documenti/ApeForm.jsx` + `.css`.
- Modify: `frontend/src/modules/immobili/components/ImportVisura/ImportVisuraModal.jsx` (accept optional `initialFiles` prop and pre-fill the queue). Delete `components/CertificatiEnergetici/CertificatoEnergeticoForm.jsx`.
- Test: `ApeForm.test.jsx`, extend `ImportVisuraModal.test.jsx`

**Interfaces:**
- `documentForms.js` default export: `{ 'immobili.visura': () => import('./components/Documenti/VisuraDocumentForm'), 'immobili.ape': () => import('./components/Documenti/ApeForm') }`.
- `VisuraDocumentForm` is a thin adapter to the form contract that renders `ImportVisuraModal` with `initialFiles`.
- `ApeForm`:
  - fields: classe (select A4…G), EPgl,nren (kWh/m²anno, decimal), codice identificativo, certificatore (select from tecnici API used by the old form), data emissione (required), decaduto il (optional, with hint "Compila se i controlli dell'impianto termico non sono stati fatti");
  - shows the computed scadenza (+10 years);
  - submits `documentiAPI.upload` with `tipo_codice=APE`, `data_riferimento`=emissione, `dati={classe, ep_gl_nren, codice_identificativo, tecnico_id, decaduto_il}`.
- [ ] **Step 1:** Write tests:
  - ApeForm requires classe and emissione;
  - it shows "Scade il 15/03/2034" for emissione 15/03/2024;
  - it posts the expected FormData fields;
  - ImportVisuraModal with `initialFiles` shows them in the queue.
- [ ] **Step 2:** Run. Expected: FAIL.
- [ ] **Step 3:** Implement.
- [ ] **Step 4:** Run (PASS).
- [ ] **Step 5:** Commit `feat(immobili): APE and visura forms registered as document forms`.

### Task 11: Unit detail page (scheda immobile)

**Files:**
- Move: `frontend/src/pages/ImmobileDetail.jsx` + `.css` → `frontend/src/modules/immobili/components/ImmobileScheda/ImmobileScheda.jsx` + `.css`.
- Create: `frontend/src/modules/immobili/components/ImmobileScheda/VariazioniCatastali.jsx`.
- Modify:
  - `frontend/src/modules/immobili/manifest.js` (route `/immobili/:id`);
  - `frontend/src/App.jsx` (`/unita-immobiliari/:id` → `<Navigate to="/immobili/:id">`);
  - `UnitaImmobiliariList.jsx` (row click / name link opens the scheda; edit stays in the actions);
  - `UnitaImmobiliareForm.jsx:~396` (replace `DocumentiSection` with a link "Documenti nella scheda immobile" when `unitaImmobiliare?.id`);
  - `immobiliAPI.js` (`getVariazioniCatastali(id)`).
- Test: `ImmobileScheda.test.jsx`, `VariazioniCatastali.test.jsx`

**Interfaces:**
- Sections, in this order:
  1. header (code, address, Button "Modifica" → existing `UnitaImmobiliareForm` modal);
  2. **Dati** (catastal summary);
  3. **Documenti** = `<DocumentiPanel entityType="IMMOBILE" entityId={id} />`;
  4. **Variazioni catastali**;
  5. existing sections (proprietari/quote, contratti, spese, `ScadenzeSection`).
- The old "certificati" section is removed: APE is in Documenti.
- Restyle everything to the design system: tokens, `Card`, `Badge`, `Button`, `renderIcon`, no emoji/Font Awesome icons.
- `VariazioniCatastali`: table data / campo (Italian label) / prima → dopo / origine (link to the visura document when `documento_id`). Empty state "Nessuna variazione registrata".
- [ ] **Step 1:** Write tests:
  - the scheda renders the Documenti and Variazioni sections for the given id (mock APIs);
  - "Modifica" opens the form;
  - VariazioniCatastali shows "Rendita catastale: 500,00 → 600,00" and the empty state.
- [ ] **Step 2:** Run. Expected: FAIL.
- [ ] **Step 3:** Implement.
- [ ] **Step 4:** Run (PASS) and `npm run build` (no unresolved imports from the move).
- [ ] **Step 5:** Commit `feat(immobili): unit detail page with documents and catastal changes`.

### Task 12: Immobili documents page, APE list, widget, Configurazioni

**Files:**
- Create: `frontend/src/modules/immobili/components/Documenti/DocumentiImmobiliPage.jsx` + `.css`.
- Modify:
  - `frontend/src/modules/immobili/manifest.js`: route `/immobili/documenti` declared **before** `/immobili/:id`; menu item "Documenti" under Immobili. The "Certificati energetici" menu entry now points to `/immobili/documenti?tipo=APE`;
  - `CertificatiEnergeticiList.jsx`: delete it and redirect `/certificati-energetici` to `/immobili/documenti?tipo=APE`;
  - `CertificatiScadenzaWidget.jsx`: read `documentiAPI.list({ modulo: 'immobili', tipo_codice: 'APE', scadenza_entro_giorni: 90 })`;
  - `frontend/src/modules/anagrafica_italiana/components/Domini/TipiDocumentoList.jsx`: columns Modulo, Regime ("Sostituisce il precedente"/"Si accumulano"), Scadenza ("10 anni"/"Manuale"/"—"), Form (yes/no). Manifest-owned fields are read-only in the edit form; overrides stay editable.
- Test: `DocumentiImmobiliPage.test.jsx`, update `CertificatiScadenzaWidget` test if present, `TipiDocumentoList` test.

**Interfaces:**
- Page:
  - `DataTable` over `documentiAPI.list({ entity_type: 'IMMOBILE', modulo: 'immobili', tipo_codice, includi_sostituiti, scadenza_entro_giorni })`;
  - columns: Immobile (link to scheda), Tipologia, Data, Scadenza (Badge), Stato, Azioni (anteprima, scarica);
  - filters synced to the URL query (`tipo`, `stato`, `scadenza`).
  - The list endpoint must return `entity_label`. Add it to Task 5's `DocumentoOut` via an optional per-module label resolver: `EntityLabelRegistry.register("IMMOBILE", fn)` in `immobili.register_module`; fallback `f"{entity_type} #{id}"`.
- [ ] **Step 1:** Write tests:
  - the page reads `?tipo=APE` and passes `tipo_codice='APE'`;
  - the "Mostra sostituiti" toggle sets `includi_sostituiti`;
  - the widget lists an APE expiring in 20 days as urgent;
  - TipiDocumentoList shows "immobili" in the Modulo column.
- [ ] **Step 2:** Run. Expected: FAIL.
- [ ] **Step 3:** Implement (backend `entity_label` resolver included, with a pytest in `test_documenti_api.py`: `test_list_includes_entity_label`).
- [ ] **Step 4:** Run frontend + backend tests (PASS).
- [ ] **Step 5:** Commit `feat(immobili): documents page, APE list and widget on core documents; module column in tipi documento`.

### Task 13: UX review, full verification, release

- [ ] **Step 1:** Run agent `revisione-ux` on the commit range of Tasks 9–12; fix every "alta"/"media" finding (one commit per fix group).
- [ ] **Step 2:** On the replica, run the end-to-end check by hand:
  - import the Milan visure again (they must be "invariato", no new document because of `_has_visura`);
  - upload an APE and a 2019 APE (the latter goes to storico);
  - open the scheda, the documents page, the variazioni.
- [ ] **Step 3:** Run agent `verifica-test`. Expected: VERDE.
- [ ] **Step 4:** Run the `rilascio` skill:
  - merge to master, push, `scripts/promote.sh master`;
  - check the promote output for "nessuna tabella o riga persa" and the "Tipologie documentali" step;
  - check the APE count equality on prod via the promote report.
