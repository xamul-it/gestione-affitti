# Import unità immobiliari da visura catastale — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Upload a catasto visura PDF (sintetica or analitica), review a proposal of anagrafiche/unità/diritti to create or update, apply it in one transaction, and attach the PDF as "Visura catastale" to every touched unit.

**Architecture:** Pure parser (`pdftotext -layout` text → dataclasses) inside the `immobili` backend module; an import service that diffs the parsed visura against the tenant DB into a JSON proposal and applies a confirmed proposal transactionally; two routes (preview/apply) with the PDF held in tenant temp storage between them; a React modal in the immobili frontend module opened from a "Carica da documento" button on the unità list.

**Tech Stack:** FastAPI, SQLAlchemy, PostgreSQL (schema-per-tenant), Alembic (raw-SQL migrations), poppler `pdftotext` via `subprocess`, React + Vite + Vitest.

**Spec:** `docs/superpowers/specs/2026-10-30-import-visure-catastali-design.md`

## Global Constraints

- Supported formats: visura attuale **sintetica** and **analitica** per soggetto. Riepilogo IMU/TASI → explicit "formato non supportato" error.
- Terreni: not imported in this phase; parser recognises and counts them (`terreni_count`) and the proposal shows a warning. Data structures are organised per "tipo di bene" so a terreni section can be added later.
- No OCR. Text extraction via `pdftotext -layout` (poppler already installed for `pdf2image`); no new Python dependency. Venv is Python 3.13 (uv).
- Nothing is written before the user confirms; apply runs in **one transaction** (all or nothing).
- Never overwrite user-entered fields on existing units: only `categoria_catastale_id`, `rendita_catastale`, `superficie_mq`, `indirizzo`, `piano`, and the delimited "Dati catastali" block in `note`. Never touch `tipo`, `condominio_id`, `classe_energetica`, `descrizione`, `codice`.
- Never delete/close existing diritti; quota mismatch → warning only.
- Existing soggetti: never overwrite; only propose filling empty `nome`, `cognome`, `data_nascita`, `luogo_nascita`.
- One `Documento` per touched unit (`entity_type=IMMOBILE`), each with its own file copy; skip if the unit already has a visura document with the same `numero_visura` in `metadata_parsato`.
- Real PDFs from `docs/visure/` are used as committed test fixtures (user approved).
- Backups/dumps never inside worktrees (`~/apps/gestione-affitti-backups`).
- Migrations: raw SQL via `op.execute()` (see docstring in `backend/modules/immobili/migrations/2026092301_conduttori_spese.py` for why).

## Review Focus

1. **Re-importing the same visura** → proposal shows everything "invariato", no new soggetti/unità/diritti, no duplicate document. Test: Task 5 `test_reimport_is_noop`.
2. **Intestato without CF that already exists as PERSONA_GIURIDICA** (Demanio on second import) → matched by case-insensitive `ragione_sociale`, not duplicated. Test: Task 4 `test_ente_senza_cf_matched_by_ragione_sociale`.
3. **Apply with an expired/unknown upload token or a tampered proposal referencing ids of another unit** → 404/422, nothing written. Test: Task 6 `test_apply_unknown_token_404`.
4. **Unit with unresolvable `tipo`** (category not in default map, e.g. D/1) → apply refuses with 422 if `tipo` still empty. Test: Task 5 `test_apply_rejects_missing_tipo`.
5. **Failure mid-apply** (e.g. file storage error on the 3rd unit) → DB rolled back, files already written deleted. Test: Task 5 `test_apply_rolls_back_on_error`.

---

## File Structure

Backend (`backend/modules/immobili/`):
- `models/diritti_immobile.py` — modify: extend `TipoDiritto`.
- `migrations/2026103001_tipodiritto_extra.py` — create: add enum values.
- `services/visura/__init__.py` — create: re-exports.
- `services/visura/models.py` — create: parsed dataclasses.
- `services/visura/text.py` — create: `pdf_to_text`, `detect_formato`, shared regex helpers (diritto, quota, CF, numbers).
- `services/visura/parser_sintetica.py`, `services/visura/parser_analitica.py` — create.
- `services/visura/parser.py` — create: `parse_visura(pdf_bytes)` dispatch.
- `services/visura_import_service.py` — create: `build_proposal`, `apply_proposal`.
- `schemas/visura_import.py` — create: Pydantic proposal/apply schemas.
- `routes/visura_import.py` — create; register in `routes/__init__.py` and `__init__.py:get_routers`.

Backend other:
- `backend/modules/anagrafica_italiana/seeds/seed_tipi_documento.py` — modify: add `VISURA_CATASTALE`.
- `backend/tests/fixtures/visure/{sintetica,analitica,riepilogo_imu}.pdf` — copies of `docs/visure/*`.
- `backend/tests/unit/test_modules/test_immobili/test_visura_parser.py` — create (+ `__init__.py`).
- `backend/tests/integration/test_modules/test_immobili/test_visura_import.py` — create.

Frontend (`frontend/src/modules/immobili/`):
- `services/immobiliAPI.js` — modify: `visuraImportAPI`.
- `components/ImportVisura/ImportVisuraModal.jsx` + `.css` + `ImportVisuraModal.test.jsx` — create.
- `components/UnitaImmobiliari/UnitaImmobiliariList.jsx` — modify: add "Carica da documento" button in `customActions`.

---

### Task 1: Tipi diritto estesi + tipo documento VISURA_CATASTALE

**Files:**
- Modify: `backend/modules/immobili/models/diritti_immobile.py:13-18`
- Create: `backend/modules/immobili/migrations/2026103001_tipodiritto_extra.py`
- Modify: `backend/modules/anagrafica_italiana/seeds/seed_tipi_documento.py` (list, before "Altri documenti")
- Test: `backend/tests/integration/test_modules/test_immobili/test_visura_import.py` (created here, extended in Task 4–5)

**Interfaces:**
- Produces: `TipoDiritto.USO`, `.ABITAZIONE`, `.SUPERFICIE`, `.ENFITEUSI`; `core_tipi_documento` row `codice="VISURA_CATASTALE"`.

- [ ] **Step 1: Write failing test** `test_diritto_uso_persisted`: create `SoggettoAnagrafico` + `Proprietario` + `UnitaImmobiliare` + `DirittoImmobile(tipo_diritto=TipoDiritto.USO, quota_percentuale=100)` on `pg_session` (same fixtures pattern as `test_proprietari.py`: `TENANT="tenant_qa_test"`, shadow `override_get_db`), commit, reload, `assert d.tipo_diritto == TipoDiritto.USO`. Also `test_tipo_documento_visura_catastale_seeded`: `seed_tipi_documento(pg_session)` then query `TipoDocumento` by codice `VISURA_CATASTALE` → not None, `richiede_scadenza is False`.
- [ ] **Step 2: Run** `cd backend && pytest tests/integration/test_modules/test_immobili/test_visura_import.py -v` → FAIL (`AttributeError: USO`).
- [ ] **Step 3: Implement.** Add the four enum members (values equal names). Migration: `revision="2026103001_tipodiritto_extra"`, `down_revision="2026092301_conduttori_spese"`, `target_schema="public"` (the PG type `tipodiritto` lives in `public`; verified with `pg_type`), upgrade runs only when schema is `public`/None: `ALTER TYPE public.tipodiritto ADD VALUE IF NOT EXISTS '<V>'` for each (wrap in `op.get_context().autocommit_block()`). Downgrade: no-op with comment (PG can't drop enum values). Seed entry: `{"codice": "VISURA_CATASTALE", "nome": "Visura Catastale", "descrizione": "Visura catastale Agenzia delle Entrate", "categoria": "immobiliare", "richiede_scadenza": False}`.
- [ ] **Step 4: Run** `cd backend && alembic upgrade head && pytest tests/integration/test_modules/test_immobili/test_visura_import.py -v` → PASS.
- [ ] **Step 5: Commit** `feat(immobili): tipi diritto uso/abitazione/superficie/enfiteusi e tipo documento visura catastale`.

---

### Task 2: Parser — modelli, estrazione testo, visura sintetica

**Files:**
- Create: `backend/modules/immobili/services/visura/{__init__,models,text,parser_sintetica,parser}.py`
- Create: `backend/tests/fixtures/visure/` (copy the three PDFs: `sintetica.pdf`, `analitica.pdf`, `riepilogo_imu.pdf`)
- Test: `backend/tests/unit/test_modules/test_immobili/{__init__,test_visura_parser}.py`

**Interfaces (Produces):**
```python
# models.py
class FormatoVisura(str, Enum): SINTETICA="SINTETICA"; ANALITICA="ANALITICA"
class VisuraFormatError(ValueError): ...   # message shown to user, Italian

@dataclass
class IntestatoParsed:
    nominativo: str                     # as printed, without CF
    cognome: str | None; nome: str | None; ragione_sociale: str | None
    codice_fiscale: str | None          # upper, no '*'
    persona_giuridica: bool             # no CF, or CF of 11 digits
    data_nascita: date | None; luogo_nascita: str | None
    diritto_testo: str                  # e.g. "Uso 1/1 in regime di separazione dei beni"
    tipo_diritto: TipoDiritto
    quota_percentuale: Decimal | None   # a/b*100, 2 decimals

@dataclass
class FabbricatoParsed:
    comune: str; codice_catastale_comune: str; provincia: str | None
    sezione_urbana: str | None; foglio: str; particella: str; subalterno: str | None
    zona_censuaria: str | None; micro_zona: str | None
    categoria: str                      # normalised "A/3"
    classe: str | None; consistenza: str | None   # "4,5 vani", "19 m2"
    vani: Decimal | None
    superficie_totale: Decimal | None; superficie_escluse_aree: Decimal | None
    rendita: Decimal | None
    indirizzo: str | None; piano: str | None
    intestati: list[IntestatoParsed]

@dataclass
class VisuraParsed:
    formato: FormatoVisura; numero: str; data: date
    soggetto_cf: str | None
    fabbricati: list[FabbricatoParsed]
    terreni_count: int
    warnings: list[str]

# text.py
def pdf_to_text(pdf_bytes: bytes) -> str            # subprocess ["pdftotext", "-layout", "-", "-"], timeout 30s; VisuraFormatError if not a PDF / empty text
def detect_formato(text: str) -> FormatoVisura      # "Visura attuale sintetica per soggetto" / "Visura attuale per soggetto"; else VisuraFormatError("Formato non supportato: carica una visura catastale sintetica o analitica")
def parse_diritto(testo: str) -> tuple[TipoDiritto, Decimal | None]
# parser.py
def parse_visura(pdf_bytes: bytes) -> VisuraParsed
```

`parse_diritto` mapping (case-insensitive, accepts `'` or `à`): "Proprieta'" + quota 1/1 → `PROPRIETARIO`; "Proprieta'" + quota <1 → `COMPROPRIETARIO`; "Nuda proprieta'" → `NUDA_PROPRIETA`; "Usufrutto" → `USUFRUTTUARIO`; "Uso" → `USO`; "Abitazione" → `ABITAZIONE`; "Superficie" → `SUPERFICIE`; "Enfiteusi" → `ENFITEUSI`; else `ALTRO`. Check "Nuda proprieta'" before "Proprieta'".

Sintetica notes: blocks start with `^\s*\d+\. Immobili siti nel Comune di (.+) \(Codice (\w{4})\) Catasto dei Fabbricati`; rows are multi-line (indirizzo line above the numeric row, superficie split over lines); intestati block `Intestazione degli immobili indicati al n.X` applies to every unit of block X; CF ends with `*`; page headers repeat and must be skipped; a block may continue across a page break. Name split: leading run of fully uppercase words = cognome, rest = nome. "Catasto dei Terreni" blocks increment `terreni_count`.

- [ ] **Step 1: Write failing tests** in `test_visura_parser.py` (load fixtures via `Path(__file__).parents[3] / "fixtures/visure"`):
  - `test_detect_formato_riepilogo_imu_rejected`: `parse_visura(riepilogo_imu)` raises `VisuraFormatError`.
  - `test_sintetica_header`: `formato == SINTETICA`, `numero == "T234664/2025"`, `data == date(2025,12,16)`, `soggetto_cf == "ZNDLMT73E17F205F"`, `len(fabbricati) == 9`, `terreni_count == 0`.
  - `test_sintetica_unit_592_2`: the fabbricato with `(foglio, particella, subalterno) == ("99","592","2")` has `codice_catastale_comune=="A944"`, `comune=="BOLOGNA"`, `categoria=="C/2"`, `classe=="2"`, `superficie_totale==Decimal("118")`, `rendita==Decimal("548.58")`, `indirizzo=="VIA EMILIA PONENTE n. 2"`, `piano=="T"`; intestati: `[("DEMANIO DELLO STATO - RAMO FERROVIA", None, True, PROPRIETARIO, Decimal("100.00")), ("ZANDERIGHI Luigi Matteo Massimiliano", "ZNDLMT73E17F205F", False, USO, Decimal("100.00"))]` as `(nominativo, codice_fiscale, persona_giuridica, tipo_diritto, quota_percentuale)`; second intestato `cognome=="ZANDERIGHI"`, `nome=="Luigi Matteo Massimiliano"`, `data_nascita==date(1973,5,17)`, `luogo_nascita=="MILANO"`.
  - `test_sintetica_unit_666_9`: `categoria=="A/3"`, `classe=="1"`, `vani==Decimal("4.5")`, `superficie_escluse_aree==Decimal("80")`, `rendita==Decimal("499.67")`, `piano=="2-S1"`, `indirizzo=="VIA EMILIA PONENTE n. 356"`; intestati tipi `[USUFRUTTUARIO, NUDA_PROPRIETA]`, first CF `"ZNDLCN38R19F205K"`.
  - `test_sintetica_unit_666_19`: `vani==Decimal("10.0")`, `superficie_escluse_aree==Decimal("294")`, `rendita==Decimal("1316.97")`, `indirizzo=="VIA EMILIA PONENTE n. 354"`, `piano=="S1-T - 1"`.
  - `test_parse_diritto` parametrized: `"Proprieta' 1/1"→(PROPRIETARIO,100)`, `"Proprieta' 1/2"→(COMPROPRIETARIO,50)`, `"Nuda proprieta' 1/1"→(NUDA_PROPRIETA,100)`, `"Usufrutto 1/3"→(USUFRUTTUARIO,33.33)`, `"Uso 1/1 in regime di separazione dei beni"→(USO,100)`, `"Diritto del concedente 1/1"→(ALTRO,100)`.
- [ ] **Step 2: Run** `cd backend && pytest tests/unit/test_modules/test_immobili/test_visura_parser.py -v` → FAIL (ImportError).
- [ ] **Step 3: Implement** the files above. `parse_visura` → `pdf_to_text` → `detect_formato` → `parse_sintetica(text)` (analitica branch raises `NotImplementedError` until Task 3).
- [ ] **Step 4: Run** same command → PASS.
- [ ] **Step 5: Commit** `feat(immobili): parser visura catastale sintetica`.

---

### Task 3: Parser — visura analitica

**Files:**
- Create: `backend/modules/immobili/services/visura/parser_analitica.py`
- Modify: `backend/modules/immobili/services/visura/parser.py`
- Test: `backend/tests/unit/test_modules/test_immobili/test_visura_parser.py`

**Interfaces:** Consumes Task 2 dataclasses/helpers. Produces `parse_analitica(text: str) -> VisuraParsed`.

Analitica notes: two-column layout; the right column ("Causali di aggiornamento ed annotazioni") must be dropped — determine the column start per page from the `Causali di aggiornamento` header offset (or the first line where the left content ends) and keep only text left of it. Unit blocks: `Immobile di catasto fabbricati - n.N`; `Comune di BOLOGNA (A944) (BO)`; `Foglio X Particella Y Subalterno Z`; `Indirizzo` next line `<via> Piano <p>`; `Rendita: Euro 1.316,97`; `Zona censuaria 2,`; `Categoria A/3a), Classe 2, Consistenza 10,0 vani` (strip the note letter + `)`); superficie `Totale: 294 m2` / `Totale escluse aree scoperte b): 294 m2`. Intestati: `Intestazione attuale degli immobili dal n. A al n. B` or `dell'immobile n. N`; entries `N. NOME`, optional `(CF XXX)`, `nato a CITTA (PR) il dd/mm/yyyy` or `sede in ...`, `Diritto di: <testo> per a/b (deriva ...)` possibly wrapped on two lines — normalise to the same `diritto_testo` shape as the sintetica (`"Uso 1/1 in regime di separazione dei beni"`). Header `Numero Pratica: T233852/2025`; `Totale immobili: di catasto fabbricati N` / `Catasto Terreni Totale immobili: N` → `terreni_count`.

- [ ] **Step 1: Write failing tests:**
  - `test_analitica_header`: `formato==ANALITICA`, `numero=="T233852/2025"`, `data==date(2025,12,16)`, `len(fabbricati)==9`, `terreni_count==0`.
  - `test_analitica_matches_sintetica`: for both fixtures build `{(f.foglio,f.particella,f.subalterno): (f.categoria, f.classe, f.rendita, f.indirizzo, f.piano, [(i.codice_fiscale, i.tipo_diritto, i.quota_percentuale) for i in f.intestati])}` → the two dicts are equal. (Superficie excluded: the formats legitimately differ.)
  - `test_analitica_unit_666_19`: `zona_censuaria=="2"`, `categoria=="A/3"`, `consistenza=="10,0 vani"`, `superficie_escluse_aree==Decimal("294")`, and no string field contains `"FRAZIONAMENTO"` (right column leaked).
- [ ] **Step 2: Run** → FAIL.
- [ ] **Step 3: Implement** `parse_analitica`; wire into `parse_visura`.
- [ ] **Step 4: Run** `pytest tests/unit/test_modules/test_immobili/test_visura_parser.py -v` → all PASS.
- [ ] **Step 5: Commit** `feat(immobili): parser visura catastale analitica`.

---

### Task 4: Import service — costruzione proposta

**Files:**
- Create: `backend/modules/immobili/schemas/visura_import.py`
- Create: `backend/modules/immobili/services/visura_import_service.py`
- Test: `backend/tests/integration/test_modules/test_immobili/test_visura_import.py`

**Interfaces (Produces):**
```python
# schemas/visura_import.py  (Pydantic v2)
Azione = Literal["crea", "aggiorna", "invariato"]

class SoggettoProposta(BaseModel):
    key: str                      # "s0", "s1", ... local id
    azione: Azione
    soggetto_id: int | None       # existing match
    persona_giuridica: bool
    cognome: str | None; nome: str | None; ragione_sociale: str | None
    codice_fiscale: str | None; data_nascita: date | None; luogo_nascita: str | None
    campi_da_completare: list[str]   # only for "aggiorna": empty fields filled from visura
    selezionato: bool = True

class CampoModifica(BaseModel):
    campo: str; attuale: Any; nuovo: Any; selezionato: bool = True

class DirittoProposta(BaseModel):
    soggetto_key: str; tipo_diritto: TipoDiritto
    quota_percentuale: Decimal | None; note: str
    azione: Literal["crea", "invariato"]; selezionato: bool = True

class UnitaProposta(BaseModel):
    key: str                      # "u0", ...
    azione: Azione
    unita_id: int | None
    foglio: str; particella: str; subalterno: str | None; sezione_urbana: str | None
    # values for create (editable in UI):
    tipo: str | None; indirizzo: str; citta: str; provincia: str | None; cap: str | None
    piano: str | None; superficie_mq: float | None; locali: int | None
    rendita_catastale: float | None; categoria_catastale_id: int | None; categoria: str
    note_catastali: str
    modifiche: list[CampoModifica]    # only for "aggiorna"
    diritti: list[DirittoProposta]
    avvisi: list[str]                 # quota diversa / diritto non in visura / comune non trovato
    selezionato: bool = True

class VisuraProposta(BaseModel):
    upload_token: str | None = None   # set by route
    formato: FormatoVisura; numero_visura: str; data_visura: date
    soggetti: list[SoggettoProposta]
    unita: list[UnitaProposta]
    avvisi: list[str]                 # global: terreni ignorati, parser warnings

# services/visura_import_service.py
def build_proposal(db: Session, visura: VisuraParsed) -> VisuraProposta
```

Rules (from spec "Regole di riconoscimento" and "Mappatura"):
- Soggetto match: by `codice_fiscale`; without CF by `PERSONA_GIURIDICA` with `func.lower(ragione_sociale) == nominativo.lower()`. Same person appearing in several units → one `SoggettoProposta` (dedupe by CF, else by nominativo).
- Unit match: resolve `ComuneItalia` by `codice_catastale` (public); key = (`citta` ilike comune nome, `foglio`, `particella`, `subalterno`) with values compared after `lstrip("0")`; if `sezione_urbana` present also require it in the "Dati catastali" note block — sezione is absent in samples, keep it simple: ignore sezione in matching but write it in the note. If comune not in `comuni_italia`: `citta` = visura comune, warning "Comune <X> (<cod>) non trovato nell'anagrafica comuni".
- `cap`/`provincia` from `ComuneItalia` (`cap` first value if multiple, split on `,`/`-`).
- `superficie_mq` = `superficie_escluse_aree` else `superficie_totale`; `locali` = `int(vani)` if `vani` is integral else None (+ text in note).
- `tipo` default by categoria: `A/1`–`A/9`,`A/11` → "Appartamento"; `A/10` → "Ufficio"; `C/1` → "Negozio"; `C/2` → "Magazzino"; `C/6` → "Box"; `C/7` → "Posto auto"; first check `TipoImmobileCategoriaMap` for a user-defined mapping of that categoria; else None.
- `note_catastali` block (exact format, replaced on update by regex on the delimiters):
  ```
  --- Dati catastali (da visura {numero} del {dd/mm/yyyy}) ---
  Categoria {categoria}, Classe {classe}, Consistenza {consistenza}
  Zona censuaria {zona}[, Micro zona {mz}][, Sezione urbana {sez}]
  --- fine dati catastali ---
  ```
- Update diff only on: `categoria_catastale_id`, `rendita_catastale`, `superficie_mq`, `indirizzo`, `piano`, note block. Unit is "invariato" if no diff and all diritti "invariato".
- Diritto "invariato" if a `DirittoImmobile` exists with same unit, the soggetto's `Proprietario`, same `tipo_diritto`; if quota differs add unit avviso `"Quota diversa per <nominativo>: sistema X%, visura Y%"`. Existing diritti on the unit whose (soggetto, tipo) is not in the visura → avviso `"Diritto <tipo> di <nominativo> presente a sistema ma non in visura"`.
- `visura.terreni_count > 0` → global avviso `"{n} terreni trovati nella visura: non importati"`.

- [ ] **Step 1: Write failing tests** (use `parse_visura` on the sintetica fixture; clean up created rows in fixtures):
  - `test_proposal_empty_db_creates_all`: in a clean state for these CFs/fogli, `build_proposal` → `len(unita)==9` all `azione=="crea"`; soggetti = 3 (`"ZNDLMT73E17F205F"`, `"ZNDLCN38R19F205K"`, Demanio with `persona_giuridica True`), all `crea`; unit 592/2 has `tipo=="Magazzino"`, `citta=="BOLOGNA"`, `provincia=="BO"`, diritti `[PROPRIETARIO, USO]`.
  - `test_soggetto_matched_by_cf`: pre-create soggetto with CF `ZNDLCN38R19F205K` and `data_nascita=None` → its proposta has `azione=="aggiorna"`, `soggetto_id` set, `"data_nascita" in campi_da_completare`.
  - `test_ente_senza_cf_matched_by_ragione_sociale`: pre-create `PERSONA_GIURIDICA` `ragione_sociale="Demanio dello Stato - Ramo Ferrovia"` → matched, `azione=="invariato"`.
  - `test_unit_matched_shows_diff`: pre-create unit `citta="BOLOGNA", foglio="99", particella="666", subalterno="19", rendita_catastale=1000.0, tipo="Villa", classe_energetica="B"` → `azione=="aggiorna"`, `modifiche` contains `CampoModifica(campo="rendita_catastale", attuale=1000.0, nuovo=1316.97)`, no `modifiche` entry for `tipo`.
  - `test_quota_mismatch_warning`: existing diritto PROPRIETARIO 50% on matched unit for a soggetto who in visura has PROPRIETARIO 100% → unit `avvisi` contains `"Quota diversa"`.
- [ ] **Step 2: Run** `cd backend && pytest tests/integration/test_modules/test_immobili/test_visura_import.py -v` → FAIL.
- [ ] **Step 3: Implement** schemas + `build_proposal`.
- [ ] **Step 4: Run** → PASS.
- [ ] **Step 5: Commit** `feat(immobili): proposta di import da visura catastale`.

---

### Task 5: Import service — applicazione proposta e documenti

**Files:**
- Modify: `backend/modules/immobili/services/visura_import_service.py`
- Test: `backend/tests/integration/test_modules/test_immobili/test_visura_import.py`

**Interfaces:**
- Consumes: `VisuraProposta` (Task 4), `parse_visura`, `file_storage.save_file(file, entity_type, entity_id, filename, tenant_schema) -> str`, `file_storage.delete_file(path, tenant_schema)`, `CodiceGeneratorService(db).generate_codice(provincia, UnitaImmobiliare)`.
- Produces:
```python
class VisuraImportError(ValueError): ...   # → 422

@dataclass
class ImportResult:
    soggetti_creati: int; soggetti_aggiornati: int
    unita_create: list[int]; unita_aggiornate: list[int]
    diritti_creati: int; documenti_allegati: int

def apply_proposal(db: Session, proposta: VisuraProposta, pdf_bytes: bytes,
                   filename: str, tenant_schema: str) -> ImportResult
```

Behaviour:
- Re-validate before writing: every selected `UnitaProposta` with `azione=="crea"` must have non-empty `tipo`, `indirizzo`, `citta` → else `VisuraImportError("Tipo mancante per l'unità foglio X particella Y sub Z")`. For `aggiorna`/`invariato`, `unita_id`/`soggetto_id` must exist and (for unità) still match foglio/particella/sub → else `VisuraImportError`. Rights referencing an unselected or missing soggetto are skipped.
- Order: soggetti → `Proprietario` (reuse by `soggetto_id`, else create) → unità (create with generated `codice`, `codice_auto_generated=True`; update only selected `modifiche`; replace note block) → diritti (`note` = `diritto_testo`) → documenti.
- Documento per touched unit (crea/aggiorna/invariato, if selected), skipped if a `Documento` with `entity_type=IMMOBILE`, `entity_id=unit`, `metadata_parsato["numero_visura"] == numero` exists. Fields: `tipo_documento=TipoDocumentoEnum.VISURA_CATASTALE`, `tipo_documento_id` = id of `VISURA_CATASTALE` `TipoDocumento`, `nome_file=filename`, `file_path`, `mime_type="application/pdf"`, `dimensione`, `descrizione=f"Visura catastale {formato.lower()} n. {numero} del {dd/mm/yyyy}"`, `metadata_parsato={"numero_visura", "data_visura", "formato"}` (mirrors the legacy fields `upload_documento` in `backend/app/core/routes/documenti.py` sets, so `DocumentiSection` shows it).
- Single transaction: `db.flush()` along the way, one `db.commit()` at the end; on any exception `db.rollback()`, delete every file saved so far, re-raise.

- [ ] **Step 1: Write failing tests:**
  - `test_apply_creates_everything`: `build_proposal` on sintetica (clean DB) → `apply_proposal` → `len(unita_create)==9`, `soggetti_creati==3`, `diritti_creati==18`, `documenti_allegati==9`; unit 666/19 has `rendita_catastale==1316.97`, `superficie_mq==294`, note contains `"--- Dati catastali (da visura T234664/2025 del 16/12/2025) ---"`; its documenti query returns one with `tipo_documento==VISURA_CATASTALE`.
  - `test_reimport_is_noop`: apply sintetica, then `build_proposal` again → every unit and soggetto `azione=="invariato"`, all diritti `invariato`; `apply_proposal` → `diritti_creati==0`, `documenti_allegati==0`.
  - `test_analitica_after_sintetica_attaches_new_document_only`: apply sintetica, then analitica proposal → no unit `crea`, `apply` → `documenti_allegati==9`, `unita_create==[]`.
  - `test_apply_rejects_missing_tipo`: set one `crea` unit's `tipo=None` → `VisuraImportError`, and DB has none of the 9 units.
  - `test_apply_respects_deselection`: deselect one unit and the `rendita_catastale` modifica on an updated unit → that unit not created; rendita unchanged.
  - `test_apply_rolls_back_on_error`: monkeypatch `file_storage.save_file` to raise on the 3rd call → exception; no units/soggetti created; `file_storage.delete_file` called for the 2 saved paths.
  - `test_existing_user_fields_untouched`: unit pre-existing with `tipo="Villa"`, `classe_energetica="B"`, `descrizione="mia"`, note `"nota utente"` → after apply those are unchanged and note still starts with `"nota utente"`.
- [ ] **Step 2: Run** → FAIL.
- [ ] **Step 3: Implement** `apply_proposal`.
- [ ] **Step 4: Run** `pytest tests/integration/test_modules/test_immobili/test_visura_import.py -v` → PASS.
- [ ] **Step 5: Commit** `feat(immobili): applicazione import visura con allegato documento`.

---

### Task 6: Route preview/apply

**Files:**
- Create: `backend/modules/immobili/routes/visura_import.py`
- Modify: `backend/modules/immobili/routes/__init__.py`, `backend/modules/immobili/__init__.py` (`get_routers`)
- Test: `backend/tests/integration/test_modules/test_immobili/test_visura_import.py`

**Interfaces (Produces):**
- `router = APIRouter(prefix="/unita-immobiliari/import-visura", tags=["Import visura catastale"])` — register **before** `immobili_router` in `get_routers` so `/{unita_immobiliare_id}` doesn't shadow it.
- `POST /preview` multipart `file: UploadFile`, `tipo_documento: str = Form("VISURA_CATASTALE")` → `VisuraProposta` with `upload_token`. Only `VISURA_CATASTALE` accepted (else 422). Max 10 MB, `.pdf` only. Save PDF with `file_storage.save_temp_file(file, job_uuid=upload_token, filename, tenant_schema)`; `upload_token = uuid4().hex`. `VisuraFormatError` → 422 with its message.
- `POST /apply` JSON `{"upload_token": str, "proposta": VisuraProposta}` → `ImportResult` as JSON. Token resolves the temp file for the current tenant (404 `"Upload scaduto o non trovato, ricarica la visura"` if missing); re-parse the PDF and check `numero`/`formato` equal the proposal (422 otherwise); `VisuraImportError` → 422; delete the temp file after success.
- Both: `Depends(get_db)`, `Depends(get_tenant_schema)` (400 if missing), `Depends(require_permission("documenti.write"))`.
- Temp files older than 24h for this tenant are removed at the start of each `/preview` call (simple glob on the temp dir).

- [ ] **Step 1: Write failing tests** (call route functions directly with `pg_session`, like `test_proprietari.py`; build `UploadFile(filename="sintetica.pdf", file=BytesIO(bytes))`; pass a stub user):
  - `test_preview_returns_token_and_proposal`: 9 unità, `upload_token` 32 hex chars.
  - `test_preview_rejects_riepilogo_imu`: `HTTPException` 422, detail contains `"Formato non supportato"`.
  - `test_apply_unknown_token_404`.
  - `test_apply_end_to_end`: preview then apply → 9 units created; temp file removed.
- [ ] **Step 2: Run** → FAIL.
- [ ] **Step 3: Implement** route + registration.
- [ ] **Step 4: Run** the integration file → PASS; also `cd backend && ./run_tests.sh module immobili` → PASS.
- [ ] **Step 5: Commit** `feat(immobili): endpoint preview/apply import visura catastale`.

---

### Task 7: Frontend — modale "Carica da documento"

**Files:**
- Modify: `frontend/src/modules/immobili/services/immobiliAPI.js`
- Create: `frontend/src/modules/immobili/components/ImportVisura/ImportVisuraModal.jsx`, `ImportVisuraModal.css`, `ImportVisuraModal.test.jsx`
- Modify: `frontend/src/modules/immobili/components/UnitaImmobiliari/UnitaImmobiliariList.jsx` (`customActions`)

**Interfaces:**
- Consumes: Task 6 endpoints.
- Produces: `visuraImportAPI = { preview: (file, tipoDocumento) => api.post('/unita-immobiliari/import-visura/preview', FormData, {headers: {'Content-Type': 'multipart/form-data'}}), apply: (uploadToken, proposta) => api.post('/unita-immobiliari/import-visura/apply', {upload_token: uploadToken, proposta}) }` (also added to default export); `<ImportVisuraModal onClose={fn} onImported={fn} />`.

UI (follow existing modal/button styles; reuse `.btn-import` look for the button "Carica da documento", icon `file-text` or `upload` via `renderIcon`):
1. Step "Documento": select "Tipo documento" with the single option "Visura catastale" + file input (accept `application/pdf`) + "Analizza". Show API error `detail` text on failure.
2. Step "Revisione": header with formato/numero/data and global avvisi; sections **Anagrafiche da aggiungere** (soggetti `crea`), **Anagrafiche da completare** (`aggiorna`), **Immobili da aggiungere** (unità `crea`: editable `tipo` text input — required, highlighted when empty — plus indirizzo, piano; read-only foglio/particella/sub/categoria/rendita; diritti list), **Immobili da aggiornare** (per-campo checkbox `attuale → nuovo`, diritti da aggiungere), **Già presenti** (collapsed `<details>` with count). Every row has a checkbox bound to `selezionato`. Unit `avvisi` shown inline. Footer: counts summary and "Importa" disabled while any selected `crea` unit has empty `tipo`.
3. Step "Esito": counts from `ImportResult`, "Chiudi" calls `onImported()` (list refreshes via `table.refresh()`).

- [ ] **Step 1: Write failing tests** (Vitest + Testing Library, mock `visuraImportAPI`):
  - `renders upload step with Visura catastale option`.
  - `shows sections after preview`: mocked preview with 1 soggetto `crea`, 1 unità `crea` (`tipo: null`), 1 unità `invariato` → headings "Anagrafiche da aggiungere", "Immobili da aggiungere", "Già presenti" visible; "Importa" disabled.
  - `enables import when tipo filled and sends deselections`: type "Appartamento", uncheck the soggetto, click "Importa" → `apply` called with proposta where `unita[0].tipo === "Appartamento"` and `soggetti[0].selezionato === false`.
  - `shows backend error detail`: preview rejects with `{response:{data:{detail:"Formato non supportato: ..."}}}` → text visible.
- [ ] **Step 2: Run** `cd frontend && npx vitest run src/modules/immobili/components/ImportVisura` → FAIL.
- [ ] **Step 3: Implement** API, modal, button.
- [ ] **Step 4: Run** same command → PASS; `npm run build` → success.
- [ ] **Step 5: Commit** `feat(immobili): modale carica da documento per visure catastali`.

---

### Task 8: Verifica end-to-end nell'app

- [ ] **Step 1:** Run migrations on the dev tenants: `cd backend && alembic upgrade head && alembic -x schema=all upgrade head`.
- [ ] **Step 2:** Start backend + frontend (dev), log in on the test tenant, open Unità Immobiliari → "Carica da documento", upload `docs/visure/Visura sintetica.pdf`: expect 9 immobili da aggiungere, 3 anagrafiche, Demanio as ente; fill missing tipi if any, Importa → 9 units visible, each unit's Documenti section lists "Visura catastale sintetica n. T234664/2025 del 16/12/2025" and downloads the PDF.
- [ ] **Step 3:** Upload `docs/visure/Visura analitica.pdf`: expect 0 da aggiungere, units "invariato"/"aggiorna" only for superficie differences, Importa → second document attached per unit, no duplicates. Upload `riepilogo-immobili.pdf` → "Formato non supportato" message.
- [ ] **Step 4:** Full suites: `cd backend && ./run_tests.sh` and `cd frontend && npm run test:run` → green (report any pre-existing failures separately, don't hide them).
