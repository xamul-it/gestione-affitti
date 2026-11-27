# Beni fase 4a — raggruppamenti (backend e interfaccia minima): piano di implementazione

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** i beni si raggruppano in rami ad albero (complesso, edificio, fondo, altro); godimenti e incarichi si agganciano anche a un ramo e valgono per tutto quello che contiene; "chi paga cosa" e la scheda del bene leggono le relazioni ereditate; i `PARTE_DI_FONDO` diventano rami `FONDO`.

**Architecture:** tabella di modulo `immo_raggruppamenti` (albero, `padre_id`) e colonna `immo_beni.raggruppamento_id`. Un servizio di immobili (`services/raggruppamenti.py`) gestisce albero, spostamenti, archiviazione e cancellazione; `services/relazioni_bene.py` guadagna `relazioni_effettive`, unico punto che somma le relazioni del bene e dei rami antenati. Le relazioni sui rami sono normali righe di `core_relazioni` con `entity_type = RAGGRUPPAMENTO`. Frontend: albero `/raggruppamenti`, scheda del ramo, percorso e relazioni ereditate sulla scheda del bene.

**Tech Stack:** FastAPI, SQLAlchemy, Alembic multi-schema (migrazioni di modulo in `backend/modules/immobili/migrations`), PostgreSQL, React + Vite, Vitest, pytest.

**Spec:** `docs/superpowers/specs/2026-11-10-beni-catastali-design.md` (sezioni "Raggruppamenti", "Collegamenti tra beni (ridotti)", "Relazione unica", "Eredità sui rami", "Chi paga cosa", "API", "Interfaccia", "Migrazione dei dati" punto 4, "Piano a fasi" 4a).

## Global Constraints

- **Fuori dalla 4a** (4b/4c): documenti sui rami e tipologie per `RAGGRUPPAMENTO`, documenti dei rami antenati sulla scheda del bene, relazioni ereditate sulla scheda del ramo, selettore unico paginato `/beni/cerca?rami=true`, "applica a tutti i beni del ramo". Nella 4a il ramo si sceglie da una tendina con la lista piatta dei rami.
- **Tipi di ramo**, esattamente: `COMPLESSO` "Complesso", `EDIFICIO` "Edificio", `FONDO` "Fondo", `ALTRO` "Altro". Elenco in codice (`TIPI_RAGGRUPPAMENTO` in `services/raggruppamenti.py`), non CHECK a DB, come `TIPI_COLLEGAMENTO`.
- **Niente date** sull'appartenenza: l'albero è quello attuale. `relazioni_effettive(…, d)` filtra le relazioni per data, non l'appartenenza. Limite noto, scritto nella spec.
- **Albero puro**: un ramo ha al più un padre, un bene al più un ramo. Niente cicli (un ramo non va sotto se stesso né sotto un suo discendente) → `ValueError` "Un raggruppamento non può stare dentro se stesso o un suo sottoraggruppamento".
- **Archiviare** = `attivo = false`, reversibile; il ramo resta con figli e relazioni, sparisce dall'albero e dalla tendina salvo `includi_archiviati=true`. Non si crea un figlio né si sposta qualcosa dentro un ramo archiviato (400 "Il raggruppamento è archiviato"). Le relazioni ereditate da un ramo archiviato restano valide.
- **Cancellare**: solo se il ramo non ha **nessuna** relazione (anche chiusa) né documenti → altrimenti 409 "Il raggruppamento ha relazioni o documenti: archivialo". I figli (rami e beni) salgono al padre del ramo cancellato (o alla radice).
- **Tipi di relazione sui rami**: famiglie `godimento` e `incarichi` hanno `entity_types: ["IMMOBILE", "RAGGRUPPAMENTO"]`; i `diritti_reali` restano `["IMMOBILE"]` (`solo_beni: true`), quindi un diritto reale su un ramo è rifiutato da `RelazioneService._verifica_oggetto` già oggi. `amministratore_condominio` invariato.
- **Nessuna regola di precedenza** tra relazioni del bene ed ereditate: si usano tutte così come sono (decisione dell'utente del 2026-11-25).
- **Permessi** (nessun permesso nuovo): ramo visibile con `immobile.view` **o** `terreno.view`; creare, modificare, spostare, archiviare, cancellare con `immobile.edit` **o** `terreno.edit`. Dentro un ramo si elencano solo i beni dei tipi visibili all'utente (`_tipi_visibili` di `routes/beni.py`). Relazioni del ramo: lettura con vista del ramo + `soggetto.view`, scrittura con edit del ramo + `soggetto.edit`. Spostare un bene richiede l'edit del bene e l'edit del ramo di destinazione.
- **Hook `object_permissions`** per `RAGGRUPPAMENTO`: restituisce **due righe per ramo** (`immobile.view` e `terreno.view`); `oggetto_visibile` e `permessi_modifica` devono funzionare con più righe per oggetto (verificare, Task 3).
- `EntityType` (Python) guadagna `RAGGRUPPAMENTO`: la colonna `core_documenti.entity_type` è `varchar` in tutti gli schemi tenant, quindi **nessun `ALTER TYPE`** (verificato il 2026-11-25). `TABELLE_OGGETTI["RAGGRUPPAMENTO"] = "immo_raggruppamenti"`.
- **Controllo `FONDO` "unità non rurali" escluso**: non esiste un dato "fabbricato rurale" sull'unità; si apre una issue (Task 7) invece di inventare una regola.
- Migrazione: si ferma ed elenca (nessuna scrittura) se trova `PARTE_DI_FONDO` chiusi, una particella in due fondi aperti, o un terreno che è sia principale sia collegato di `PARTE_DI_FONDO`. Nessun azzeramento.
- Nomi stabili usati dal registro costi/ricavi: `ruoli_alla_data(db, bene_id, d) -> RuoliBene` invariata come firma, ora con le relazioni ereditate.
- Codice e commenti in inglese, testi a video in italiano; commit in inglese con `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`. Branch `beni-fase4a`.
- Aggiornare `docs/modules/immobili.md` (e `docs/piattaforma.md` per `RAGGRUPPAMENTO` tra gli oggetti) nello stesso commit del codice che descrivono.
- Dati di esempio di immobili autoconsistenti e idempotenti; `tenant_test_nuovo` e `tenant_test_evolutivo` migrano puliti (`scripts/tenant_prova.py`).

## Review Focus

1. **Ciclo per spostamento indiretto**: spostare il complesso C sotto l'edificio E che sta dentro C → 400, albero invariato. → `test_sposta_sotto_discendente` in Task 2.
2. **Utente con solo `terreno.view`** apre un ramo misto: vede il ramo e solo i terreni dentro; sulla scheda del terreno vede le relazioni ereditate; `PATCH` di un'unità in quel ramo → 403. → test in Task 3.
3. **Cancellare un ramo con una relazione chiusa** (storia): 409, niente sparisce; un ramo vuoto con figli si cancella e i figli salgono al nonno. → test in Task 2 e 3.
4. **Bene in un ramo archiviato**: il conduttore del ramo continua a ricevere le spese ordinarie del bene nel riepilogo. → `test_ramo_archiviato_eredita` in Task 4.
5. **Diritto reale su un ramo dall'API generica `/relazioni`**: 400 chiaro, nessuna riga. → `test_diritto_reale_su_ramo_rifiutato` in Task 3.
6. **Migrazione con dati ambigui** (particella in due fondi): si ferma e li elenca, nessuna riga scritta. → Task 5.
7. **Anagrafica con relazioni solo su un ramo**: non eliminabile (`conta_per_soggetto`). → test in Task 3.

---

## File Structure

Backend
- `app/core/platform/models/documento.py` — `EntityType.RAGGRUPPAMENTO`.
- `app/core/platform_services/relazione_service.py` — `TABELLE_OGGETTI["RAGGRUPPAMENTO"]`.
- `modules/immobili/models/raggruppamento.py` (nuovo), `models/bene.py` (`raggruppamento_id`), `models/__init__.py`.
- `modules/immobili/services/raggruppamenti.py` (nuovo) — albero, spostamenti, archivia, cancella.
- `modules/immobili/services/relazioni_bene.py` — `relazioni_effettive`, relazioni del ramo, hook permessi del ramo.
- `modules/immobili/services/ruoli_bene.py` — `ruoli_alla_data` sulle relazioni effettive.
- `modules/immobili/services/collegamenti_beni.py` — via `PARTE_DI_FONDO`.
- `modules/immobili/routes/raggruppamenti.py` (nuovo), `schemas/raggruppamenti.py` (nuovo), `routes/beni.py`, `schemas/bene.py`, `schemas/relazioni_bene.py`, `__manifest__.py`.
- `modules/immobili/migrations/2026112502_raggruppamenti.py` (nuovo).
- `modules/immobili/seeds/seed_tenant.py` — un complesso di esempio.

Frontend (`frontend/src/modules/immobili/`)
- `components/Raggruppamenti/RaggruppamentiAlbero.jsx`, `RaggruppamentoScheda.jsx`, `RaggruppamentoForm.jsx` (+ test) — nuovi.
- `components/BeneScheda/BeneScheda.jsx`, `SoggettiSection.jsx`, `opzioniCollegamento.js` — percorso, ereditate, via `PARTE_DI_FONDO`.
- `services/immobiliAPI.js` — `raggruppamentiAPI`, `beniAPI.spostaInRamo`.
- `manifest.js` — rotte e voce di menu "Raggruppamenti".

---

### Task 1: Modello, tabella e migrazione dello schema

**Files:**
- Create: `backend/modules/immobili/models/raggruppamento.py`, `backend/modules/immobili/migrations/2026112502_raggruppamenti.py` (`down_revision = "2026112501_relazione_unica"`, `target_schema = "tenant"`; in questo task solo la parte di schema)
- Modify: `models/bene.py`, `models/__init__.py`, `__manifest__.py` (`models`, `tenant_tables`), `app/core/platform/models/documento.py`, `app/core/platform_services/relazione_service.py`
- Test: `backend/tests/integration/test_modules/test_immobili/test_migrazione_raggruppamenti.py` (stesso schema di `test_migrazione_relazione_unica.py`: schema temporaneo, `converti(conn)` in transazione annullata)

**Interfaces:**
- Produces:
  - `Raggruppamento` (`immo_raggruppamenti`): `id`, `tipo String(30) not null`, `nome String(200) not null`, `padre_id → immo_raggruppamenti.id ON DELETE RESTRICT, nullable, index`, `descrizione Text`, `note Text`, `attivo Boolean not null default true`, `created_at`, `updated_at`; CHECK `padre_id <> id`. Relazioni ORM `padre`, `figli`, `beni`.
  - `Bene.raggruppamento_id → immo_raggruppamenti.id ON DELETE RESTRICT, nullable, index`; `Bene.raggruppamento` relationship.
  - Nella migrazione: `crea_schema(conn)` (tabella + colonna, idempotente con `IF NOT EXISTS`) e `converti(conn) -> dict` (vuota qui, riempita nel Task 5); `upgrade()` le chiama in quest'ordine.

- [ ] **Step 1:** test `test_schema_creato` (dopo `crea_schema` esistono tabella, colonna, FK, CHECK) e `test_crea_schema_idempotente` (due volte senza errori).
- [ ] **Step 2:** eseguire `pytest tests/integration/test_modules/test_immobili/test_migrazione_raggruppamenti.py -v` → FAIL.
- [ ] **Step 3:** implementare modello, colonna, migrazione di schema, `EntityType.RAGGRUPPAMENTO`, `TABELLE_OGGETTI`.
- [ ] **Step 4:** eseguire → PASS; `alembic -x schema=tenant_test upgrade head` dalla catena di modulo come fa `scripts/sync_modules.py` senza errori.
- [ ] **Step 5:** commit `feat(immobili): raggruppamenti table`.

### Task 2: Servizio dell'albero

**Files:**
- Create: `backend/modules/immobili/services/raggruppamenti.py`
- Test: `backend/tests/integration/test_modules/test_immobili/test_raggruppamenti_service.py`

**Interfaces:**
- Consumes: Task 1.
- Produces (tutti flush, mai commit; `ValueError` = input non valido, `LookupError` = inesistente):
  - `TIPI_RAGGRUPPAMENTO: dict[str, str]` (codice → etichetta, Global Constraints);
  - `class RamoNonCancellabile(ValueError)`;
  - `crea_raggruppamento(db, tipo: str, nome: str, padre_id: Optional[int] = None, descrizione=None, note=None) -> Raggruppamento`;
  - `aggiorna_raggruppamento(db, ramo, *, tipo=None, nome=None, descrizione=None, note=None, attivo: Optional[bool] = None) -> Raggruppamento`;
  - `sposta_raggruppamento(db, ramo, padre_id: Optional[int]) -> Raggruppamento`;
  - `sposta_bene(db, bene: Bene, raggruppamento_id: Optional[int]) -> Bene`;
  - `antenati(db, raggruppamento_id: int) -> list[Raggruppamento]` (dalla radice al ramo stesso incluso; una CTE ricorsiva);
  - `discendenti_ids(db, raggruppamento_id: int) -> set[int]` (rami, ramo stesso incluso);
  - `cancella_raggruppamento(db, ramo) -> dict` (`{"rami_saliti": n, "beni_saliti": m}`); `RamoNonCancellabile` se esiste una riga di `core_relazioni` con `entity_type='RAGGRUPPAMENTO'` e `entity_id=ramo.id` o un `core_documenti` con lo stesso oggetto.

- [ ] **Step 1:** test
  - `test_crea_con_padre` e `test_tipo_non_valido` (`tipo="CONDOMINIO"` → `ValueError`), `test_nome_vuoto` (`"  "` → `ValueError`);
  - `test_antenati_dalla_radice`: complesso › edificio › altro → `[complesso, edificio, altro]`;
  - `test_sposta_sotto_se_stesso` e `test_sposta_sotto_discendente` (Review Focus 1) → `ValueError` col testo dei Global Constraints, `padre_id` invariato;
  - `test_sposta_alla_radice` (`padre_id=None`);
  - `test_dentro_ramo_archiviato`: creare un figlio, spostare un ramo o un bene dentro un ramo con `attivo=False` → `ValueError("Il raggruppamento è archiviato")`;
  - `test_archivia_e_riattiva`: figli e beni restano dove sono;
  - `test_cancella_figli_salgono` (Review Focus 3): C › E › {bene B, ramo F}; cancellare E → F e B hanno padre C, risultato `{"rami_saliti": 1, "beni_saliti": 1}`; cancellare C (radice) → figli alla radice;
  - `test_cancella_con_relazione_chiusa` → `RamoNonCancellabile`, ramo presente; `test_cancella_con_documento` idem.
- [ ] **Step 2:** eseguire → FAIL.
- [ ] **Step 3:** implementare.
- [ ] **Step 4:** eseguire → PASS.
- [ ] **Step 5:** commit `feat(immobili): raggruppamenti tree service`.

### Task 3: Relazioni sui rami, eredità, API e permessi

**Files:**
- Modify: `backend/modules/immobili/__manifest__.py` (`entity_types` di godimento/incarichi; `object_permissions["RAGGRUPPAMENTO"]`; router), `services/relazioni_bene.py`, `routes/beni.py`, `schemas/bene.py`, `schemas/relazioni_bene.py`
- Create: `backend/modules/immobili/routes/raggruppamenti.py`, `backend/modules/immobili/schemas/raggruppamenti.py`
- Test: `backend/tests/integration/test_modules/test_immobili/test_raggruppamenti_api.py`, `test_relazioni_bene.py` (aggiungere)

**Interfaces:**
- Consumes: Task 2.
- Produces:
  - in `relazioni_bene.py`:
    - `@dataclass RelazioneEffettiva(relazione: Relazione, tipo: RuoloDisponibile, provenienza: Optional[Raggruppamento])` (`None` = propria del bene);
    - `relazioni_effettive(db, bene_id: int, d: Optional[date] = None) -> list[RelazioneEffettiva]`: relazioni del bene più quelle dei rami antenati (`antenati` del Task 2), filtrate per famiglie di immobili; con `d` solo quelle valide in `d` (`data_inizio <= d` o nulla, `data_fine >= d` o nulla); due query in tutto;
    - `relazioni_del_bene(…)` invariata come firma: le righe guadagnano `provenienza: Optional[{"raggruppamento_id", "nome", "tipo"}]` e contengono anche le ereditate;
    - `crea_relazione_raggruppamento(db, tenant_schema, user_id, raggruppamento_id, soggetto_id, tipo, *, data_inizio=None, data_fine=None, note=None, dati=None) -> tuple[Relazione, list[str]]` (stesso controllo dei tipi di `_tipo_del_bene`, con `entity_type = "RAGGRUPPAMENTO"`);
    - `relazioni_del_raggruppamento(db, tenant_schema, raggruppamento_id, solo_correnti=False) -> dict[str, list[dict]]` (solo proprie, stesse chiavi e righe);
    - `permessi_vista_raggruppamenti(db, tenant_schema) -> sa.Select` (due righe per ramo: `immobile.view`, `terreno.view`).
  - API `/api/v1/raggruppamenti` (router in `routes/raggruppamenti.py`):
    - `GET /?vista=albero|piatta&tipo=&includi_archiviati=false` → albero: `[{id, tipo, nome, attivo, figli: [...], beni: [{id, codice, tipo_bene, descrizione}]}]`; piatta: `[{id, tipo, nome, attivo, percorso: "Complesso X › Edificio Y"}]` ordinata per percorso;
    - `GET /{id}` → `{id, tipo, nome, descrizione, note, attivo, padre_id, percorso: [{id, nome, tipo}], figli: [...], beni: [...]}`;
    - `POST /` `{tipo, nome, padre_id?, descrizione?, note?}` → 201; `PUT /{id}` `{tipo?, nome?, descrizione?, note?, attivo?}`; `POST /{id}/sposta` `{padre_id: int|null}`; `DELETE /{id}` → 204, 409 su `RamoNonCancellabile`;
    - `GET /{id}/relazioni?solo_correnti=`, `POST /{id}/relazioni` come quelle del bene.
  - `GET /api/v1/beni/{id}` guadagna `raggruppamento_id` e `percorso: [{id, nome, tipo}]`; `PATCH /api/v1/beni/{id}/raggruppamento` `{raggruppamento_id: int|null}` → `BeneResponse`.

- [ ] **Step 1:** test
  - `test_conduttore_su_ramo_ereditato`: `conduttore` sull'edificio, bene nell'edificio → `GET /beni/{id}/relazioni` lo contiene in `godimento` con `provenienza.nome = "Edificio A"`; la relazione propria ha `provenienza = null`;
  - `test_eredita_due_livelli`: `manutentore` sul complesso, bene in complesso › edificio → ereditato;
  - `test_stesso_tipo_bene_e_ramo`: `manutentore` sul bene e sull'edificio → due righe, provenienze diverse;
  - `test_effettive_alla_data`: relazione del ramo chiusa ieri → assente con `d=oggi`, presente con `d` di un mese fa;
  - `test_diritto_reale_su_ramo_rifiutato` (Review Focus 5): `POST /relazioni` generico e `POST /raggruppamenti/{id}/relazioni` con `tipo="proprieta"` → 400, nessuna riga;
  - permessi (Review Focus 2): utente con solo `terreno.view` + `soggetto.view` → `GET /raggruppamenti/{id}` mostra il ramo e solo i terreni; `GET /beni/{terreno}/relazioni` mostra le ereditate; `PATCH /beni/{unita}/raggruppamento` → 403; senza `immobile.view` né `terreno.view` → 403 sul ramo; scrittura ramo con `terreno.edit` sì, con solo `.view` → 403;
  - `test_hook_ramo_piu_righe`: `object_permissions.oggetto_visibile` e `permessi_modifica` su `RAGGRUPPAMENTO` con utente `immobile.view` e con utente `terreno.view` → visibile per entrambi, `permessi_modifica` = `{"immobile.edit", "terreno.edit"}`;
  - `test_delete_ramo_con_relazioni` → 409 col testo dei Global Constraints;
  - `test_anagrafica_con_relazione_su_ramo_non_eliminabile` (Review Focus 7);
  - `test_percorso_bene` e `test_patch_raggruppamento` (spostare, poi `null`).
- [ ] **Step 2:** eseguire → FAIL.
- [ ] **Step 3:** implementare. Le rotte riusano `_tipi_visibili` e il controllo `soggetto.view`/`soggetto.edit` di `_bene_per_relazioni`; per il ramo, vista = almeno uno tra `immobile.view` e `terreno.view`. Errori: `ValueError` → 400, `LookupError` → 404, `RamoNonCancellabile` → 409.
- [ ] **Step 4:** eseguire → PASS, insieme a `tests/integration/test_modules/test_immobili/` e `tests/unit/test_modules/test_immobili/`.
- [ ] **Step 5:** `docs/modules/immobili.md` (raggruppamenti, eredità, permessi, limite "niente date") e `docs/piattaforma.md` (`RAGGRUPPAMENTO` tra gli oggetti delle relazioni); commit `feat(immobili): relations on raggruppamenti and inheritance`.

### Task 4: Chi paga cosa con le relazioni ereditate

**Files:**
- Modify: `backend/modules/immobili/services/ruoli_bene.py` (`ruoli_alla_data`)
- Test: `backend/tests/integration/test_modules/test_immobili/test_riepilogo_api.py` (aggiungere)

**Interfaces:**
- Consumes: `relazioni_effettive` (Task 3).
- Produces: `ruoli_alla_data(db, bene_id, d) -> RuoliBene` invariata come firma; costruisce le `RigaRelazione` da `relazioni_effettive(db, bene_id)` (il filtro per data resta in `ruoli_da_righe`). `ruoli_da_righe` non cambia.

- [ ] **Step 1:** test
  - `test_conduttore_del_ramo_paga_ordinarie`: unità con `proprieta` 1/1 nell'edificio con `conduttore` → spese ordinarie al conduttore, IMU al proprietario;
  - `test_ramo_archiviato_eredita` (Review Focus 4): stesso caso con l'edificio archiviato → stesso risultato;
  - `test_incarico_del_ramo_ignorato`: `manutentore` sul ramo non compare nelle voci;
  - `test_affittuario_agrario_del_fondo`: terreno in un `FONDO` con `affittuario_agrario` sul ramo → reddito agrario all'affittuario.
- [ ] **Step 2:** eseguire → FAIL.
- [ ] **Step 3:** implementare.
- [ ] **Step 4:** eseguire → PASS, insieme a `tests/unit/test_modules/test_immobili/test_ruoli_bene.py`.
- [ ] **Step 5:** commit `feat(immobili): who pays what includes inherited relations`.

### Task 5: Migrazione dei `PARTE_DI_FONDO` e collegamenti ridotti

**Files:**
- Modify: `backend/modules/immobili/migrations/2026112502_raggruppamenti.py` (`converti`), `services/collegamenti_beni.py` (togliere `PARTE_DI_FONDO` e `_verifica_fondo`), `routes/beni.py` (se elenca i tipi), `seeds/seed_tenant.py`
- Test: `test_migrazione_raggruppamenti.py` (aggiungere), `test_collegamenti_beni*.py` esistenti (adattare)

**Interfaces:**
- Consumes: Task 1 (`crea_schema`).
- Produces: `converti(conn) -> dict` con `{"fondi_creati": n, "terreni_spostati": m, "collegamenti_rimossi": k}`; solleva `RuntimeError` con l'elenco (id dei collegamenti e codici dei beni) **prima di ogni scrittura** se c'è un caso dubbio dei Global Constraints.

- [ ] **Step 1:** test
  - `test_fondo_da_parte_di_fondo`: T1 principale con T2, T3 collegati → un ramo `FONDO` nome = codice di T1, con T1, T2, T3 dentro; i tre collegamenti rimossi; `PERTINENZA` e `FABBRICATO_SU_PARTICELLA` intatti;
  - `test_ferma_se_chiusi`: un `PARTE_DI_FONDO` con `data_fine` → `RuntimeError` che cita l'id, nessun ramo creato;
  - `test_ferma_particella_in_due_fondi` (Review Focus 6) e `test_ferma_principale_anche_collegato`;
  - `test_converti_senza_dati`: nessun `PARTE_DI_FONDO` → `{"fondi_creati": 0, …}`;
  - `test_tipo_parte_di_fondo_rifiutato`: `crea_collegamento(…, "PARTE_DI_FONDO")` → `CollegamentoNonValido`;
  - `test_seed_complesso_idempotente`: due esecuzioni dei dati di esempio → un solo complesso "Complesso di esempio" › "Edificio A" con due unità e un `manutentore` sull'edificio.
- [ ] **Step 2:** eseguire → FAIL.
- [ ] **Step 3:** implementare; la migrazione scrive con SQL (non importa codice applicativo).
- [ ] **Step 4:** eseguire → PASS; poi `python scripts/tenant_prova.py` sui due tenant di prova → migrano puliti (con `--perdita-consentita immo_beni_collegamenti` solo se l'evolutivo ha `PARTE_DI_FONDO`).
- [ ] **Step 5:** commit `feat(immobili): parte di fondo becomes a FONDO raggruppamento`.

### Task 6: Frontend — albero, scheda del ramo, percorso e ereditate

**Files:**
- Create: `frontend/src/modules/immobili/components/Raggruppamenti/{RaggruppamentiAlbero,RaggruppamentoScheda,RaggruppamentoForm}.jsx` + `.test.jsx`
- Modify: `services/immobiliAPI.js`, `manifest.js`, `components/BeneScheda/BeneScheda.jsx`, `SoggettiSection.jsx` (+ test), `opzioniCollegamento.js` (+ test)

**Interfaces:**
- Consumes: API del Task 3.
- Produces:
  - `raggruppamentiAPI = { getAll(params), getById(id), create(data), update(id, data), sposta(id, padreId), delete(id), getRelazioni(id, {soloCorrenti}), createRelazione(id, data) }`; `beniAPI.spostaInRamo(id, raggruppamentoId)`;
  - rotte `/raggruppamenti` (albero) e `/raggruppamenti/:id` (scheda), permesso di vista `immobile.view` o `terreno.view`; voce di menu "Raggruppamenti" accanto a Unità e Terreni;
  - `SoggettiSection` prende le prop `caricaRelazioni` e `creaRelazione` (default: quelle del bene) così la scheda del ramo la riusa; le righe con `provenienza` sono in sola lettura con "dal ramo X" e link a `/raggruppamenti/:id`; nella scheda del ramo il blocco "Diritti reali" non compare.

- [ ] **Step 1:** test (Vitest)
  - `RaggruppamentiAlbero`: mostra rami annidati coi beni; "Nuovo ramo" apre il form; "Mostra archiviati" ricarica con `includi_archiviati: true`;
  - `RaggruppamentoScheda`: percorso cliccabile, figli e beni; "Archivia" chiama `update(id, {attivo: false})`; "Elimina" mostra la conferma con il numero di rami e beni che salgono, e su 409 mostra il messaggio del server; "Sposta" con la tendina dei rami (lista piatta senza il ramo stesso e i suoi discendenti, presi dall'albero);
  - `BeneScheda`: percorso in alto se `percorso` non è vuoto; "Sposta in un ramo" chiama `beniAPI.spostaInRamo`;
  - `SoggettiSection`: una riga ereditata non ha i pulsanti Chiudi/Elimina e mostra "dal ramo Edificio A";
  - `opzioniCollegamento`: `PARTE_DI_FONDO` non c'è più.
- [ ] **Step 2:** `cd frontend && npm run test:run` → FAIL sui nuovi test.
- [ ] **Step 3:** implementare coi componenti UI condivisi (`components/UI`) e i token del design system, come le sezioni della scheda del bene.
- [ ] **Step 4:** `npm run test:run` e `npm run build` → verdi.
- [ ] **Step 5:** commit `feat(immobili): raggruppamenti tree and sheet`.

### Task 7: Revisione, verifica, documentazione, rilascio

- [ ] **Step 1:** agente `revisione-ux` (Sonnet) sui file del Task 6; correggere i problemi gravi.
- [ ] **Step 2:** revisione del codice del branch (Sonnet); correggere.
- [ ] **Step 3:** agente `verifica-test` → VERDE.
- [ ] **Step 4:** issue GitHub "Beni: avviso FONDO con unità non rurali (manca il dato fabbricato rurale)"; spec: segnare la 4a come fatta con la data; memoria `project_beni_catastali.md` aggiornata.
- [ ] **Step 5:** contare i `PARTE_DI_FONDO` in ogni schema di produzione (atteso 0 in `tenant_produzione`); agente `rilascio` (indicare `immo_beni_collegamenti` a `promote.sh` come tabella che può perdere righe se il conteggio non è 0); backup in `~/apps/gestione-affitti-backups`; verificare che tutti gli schema di produzione siano migrati.
