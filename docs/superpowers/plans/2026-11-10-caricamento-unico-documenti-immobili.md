# Caricamento unico documenti immobili — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Un punto unico in `/immobili/documenti` dove trascinare i documenti: il sistema riconosce il tipo, abbina l'unità, legge i dati, propone gli aggiornamenti dell'unità e salva solo dopo conferma.

**Architecture:** Le specifiche di lettura (frasi di riconoscimento + un'espressione per campo, gruppo `v`) sono dichiarate una volta nel modulo immobili e applicate da un piccolo motore: nel backend sui PDF con testo (`pdftotext`), nel servizio esterno `~/Progetti/mrz` (nuova modalità `testo`) sulle scansioni, via `DocumentParsingService`. Un'API in due tempi (analizza → conferma) come l'import visure: il file resta in un upload temporaneo con token ed è riletto lato server alla conferma.

**Tech Stack:** FastAPI, SQLAlchemy, PostgreSQL schema-per-tenant, pytest; React + Vitest; servizio FastAPI + RQ + Tesseract.

**Spec:** `docs/superpowers/specs/2026-11-10-caricamento-unico-documenti-immobili-design.md`

## Global Constraints

- Nessun salvataggio senza conferma; l'abbinamento si conferma sempre, anche se univoco.
- Aggiornamenti dell'unità solo per i campi selezionati dall'utente; le modifiche ai campi catastali passano da `registra_variazioni` (origine `DOCUMENTO`).
- APE in vigore = data di emissione più recente (regola già in `DocumentoService._applica_storico`); un APE più vecchio del corrente produce l'avviso "APE più vecchio di quello in vigore: verrà archiviato come storico".
- Documenti di altri moduli (RLI12) scartati con messaggio: "Ricevuta di registrazione del contratto: caricala dal contratto, nel modulo Affitti".
- La classe energetica dell'unità si legge dall'APE CORRENTE; il campo sparisce dal form; la colonna non si scrive più.
- OCR solo sul servizio locale; nessun dato di `docs/visure` nel repo o nei test (fixture con valori inventati: comune TORINO, codice L219, foglio 12, particella 345, sub 6).
- Tutto nello schema del tenant della richiesta; il lavoro OCR conserva il tenant.
- Backend: test con `source venv/bin/activate`; suite completa verde prima di ogni commit.

## Review Focus

1. PDF con testo che non corrisponde a nessun tipo → esito `scegli_tipo`, mai errore 500 (Task 3, `test_testo_sconosciuto_chiede_il_tipo`).
2. Stessi foglio/particella/sub in un altro comune → nessun abbinamento automatico (Task 2, `test_stesso_catasto_altro_comune_non_abbina`).
3. Token scaduto o di un altro tenant alla conferma → 404 "Caricamento scaduto o non trovato, ricarica il documento" (Task 3, `test_conferma_token_scaduto_404`).
4. Lavoro OCR fallito → riga "Lettura non riuscita", l'utente può scegliere tipo e immobile a mano (Task 4, `test_ocr_fallito_permette_scelta_manuale`).
5. APE confermato senza classe valida (A4…G) → 422 con messaggio, niente salvato (Task 3, `test_conferma_ape_senza_classe_422`).

---

### Task 1: Motore di lettura e lettori dei tipi

**Files:**
- Create: `backend/modules/immobili/services/lettura_documenti/__init__.py`, `motore.py`, `lettori.py`
- Test: `backend/tests/unit/test_modules/test_immobili_lettura/test_motore.py`, `test_lettori.py`, `fixtures.py` (testi inventati con la struttura dei campioni)

**Interfaces:**
- Produces:
  - `@dataclass SpecTipo(codice: str, riconosci: list[str], campi: dict[str, str], scarto: Optional[str] = None)`; `SpecTipo.to_dict() -> dict` (forma del contratto in spec: `codice`, `riconosci`, `campi`).
  - `applica(spec: SpecTipo, testo: str) -> RisultatoTipo` con `@dataclass RisultatoTipo(codice: str, riconosciuto: bool, campi: dict[str, str])`: riconosciuto se **tutte** le `riconosci` trovano corrispondenza (`re.search`, `re.I | re.S`); per ogni campo la prima corrispondenza, valore = gruppo `v` ripulito dagli spazi.
  - `riconosci_tipo(testo: str) -> Optional[RisultatoTipo]`: primo lettore di `LETTORI` riconosciuto.
  - `LETTORI: list[SpecTipo]` in ordine: `RLI12` (scarto, messaggio dei Global Constraints), `VISURA_CATASTALE` (solo riconoscimento: "Visura (attuale )?per (soggetto|immobile)"), `APE`, `PLANIMETRIA_CATASTALE`.
  - Campi APE: `codice_comune`, `foglio`, `particella`, `subalterno`, `comune`, `indirizzo`, `piano`, `classe`, `ep_gl_nren`, `rilasciato_il`, `valido_fino_al`. Planimetria: `comune`, `foglio`, `particella`, `subalterno`.
  - `normalizza(codice: str, campi: dict[str, str]) -> dict`: per l'APE `classe` in {A4,A3,A2,A1,B,C,D,E,F,G} o assente, `ep_gl_nren` float da "111,24", date ISO da "gg/mm/aaaa", `data_emissione` = `rilasciato_il`; per tutti gli identificativi senza zeri iniziali (`strip_zeros`).

- [ ] **Step 1: test del motore** — `test_riconosce_solo_se_tutte_le_frasi`, `test_campo_prima_corrispondenza_gruppo_v`, `test_campo_assente_non_compare`, `test_to_dict_forma_contratto` (`{"codice","riconosci","campi"}`).
- [ ] **Step 2:** `pytest tests/unit/test_modules/test_immobili_lettura -v` → FAIL (modulo assente).
- [ ] **Step 3:** implementa `motore.py`.
- [ ] **Step 4: test dei lettori** sulle fixture:
  - `test_ape_formato_emilia_romagna`: `{"codice_comune": "L219", "foglio": "12", "particella": "345", "subalterno": "6", "ep_gl_nren": 111.24, "data_emissione": "2021-02-23", "valido_fino_al": "2031-02-23"}` ⊆ `normalizza("APE", applica(...).campi)`. La fixture riproduce la tabella "Cod. Comune / Sezione / Foglio / Particella / Subalterno" con i valori sulla riga sotto (layout di `pdftotext -layout`).
  - `test_ape_classe_assente_se_grafica`: senza riga di classe testuale → `"classe" not in` risultato (nel formato ER la classe è un grafico).
  - `test_rli_scartato_con_messaggio`, `test_visura_riconosciuta`, `test_planimetria_identificativi`, `test_testo_qualsiasi_nessun_tipo`.
- [ ] **Step 5:** FAIL → implementa `lettori.py` → PASS; suite completa verde.
- [ ] **Step 6: Commit** `feat(immobili): document readers and field engine for the single upload point`.

### Task 2: Abbinamento dell'unità e differenze

**Files:**
- Create: `backend/modules/immobili/services/lettura_documenti/abbinamento.py`
- Modify: `backend/modules/immobili/services/visura_import_service.py` (`_resolve_comune` accetta codice, nome, provincia invece di `FabbricatoParsed`; le chiamate esistenti passano i campi)
- Test: `backend/tests/integration/test_modules/test_immobili/test_abbinamento_documenti.py`

**Interfaces:**
- Consumes: `normalizza` (Task 1); `_unit_key`, `_resolve_comune` dell'import visure.
- Produces:
  - `@dataclass Abbinamento(unita_id: Optional[int], candidati: list[dict])` — `candidati`: `{"id", "codice", "indirizzo", "citta", "foglio", "particella", "subalterno"}`.
  - `abbina_unita(db, dati: dict) -> Abbinamento`: comune da `codice_comune` o `comune` via `comuni_italia`; chiave comune+foglio+particella+sub; 1 risultato → `unita_id`; 0 → candidati con stesso comune+foglio+particella, poi stesso indirizzo normalizzato (max 10); >1 → candidati = tutti.
  - `differenze(unita: UnitaImmobiliare, dati: dict) -> list[CampoModifica]` sui campi `indirizzo`, `piano`, `foglio`, `particella`, `subalterno` (confronto normalizzato: maiuscole, spazi, zeri iniziali; nessuna differenza se il dato letto manca).

- [ ] **Step 1: test** — `test_abbina_per_catasto_e_codice_comune`, `test_abbina_per_nome_comune`, `test_stesso_catasto_altro_comune_non_abbina`, `test_nessuna_unita_propone_stesso_foglio_particella`, `test_piu_unita_restituisce_candidati`, `test_differenze_ignora_zeri_e_maiuscole`, `test_differenze_indirizzo_diverso` (`CampoModifica(campo="indirizzo", attuale="Via Po 1", nuovo="VIA PO 3")`).
- [ ] **Step 2:** FAIL → implementa → PASS; test import visure ancora verdi; suite verde.
- [ ] **Step 3: Commit** `feat(immobili): match units and diff fields from read documents`.

### Task 3: API analizza / conferma (PDF con testo)

**Files:**
- Create: `backend/modules/immobili/services/upload_temporanei.py` (spostati da `routes/visura_import.py`: `temp_root`, `purge_old_uploads`, `token_dir`, `salva(tenant, contenuto, nome) -> token`; la route visure li importa)
- Create: `backend/modules/immobili/services/lettura_documenti/caricamento.py`, `backend/modules/immobili/schemas/caricamento_documenti.py`, `backend/modules/immobili/routes/caricamento_documenti.py`
- Test: `backend/tests/integration/test_modules/test_immobili/test_caricamento_documenti_api.py` (PDF generati nel test con testo delle fixture, es. con `fitz`/PyMuPDF o reportlab se già presente; altrimenti monkeypatch di `pdf_to_text`)

**Interfaces:**
- Consumes: Task 1, Task 2, `DocumentoService.crea`, `registra_variazioni`.
- Produces:
  - Router prefix `/unita-immobiliari/caricamento-documenti`; permessi `documenti.write` + `immobile.edit`.
  - `POST /analizza` (multipart `file`) → `AnalisiDocumento`: `upload_token`, `nome_file`, `esito` ∈ {`pronto`, `scegli_tipo`, `scegli_immobile`, `scartato`, `visura`, `in_lettura`, `gia_presente`, `errore`}, `tipo_codice`, `messaggio`, `unita_id`, `candidati`, `dati`, `differenze: list[CampoModifica]`, `avvisi: list[str]`, `job_uuid`.
  - `POST /conferma` body `ConfermaDocumento`: `upload_token`, `tipo_codice`, `unita_id`, `dati: dict`, `differenze: list[CampoModifica]` (solo `selezionato` applicate), `forza_duplicato: bool = False` → `{"documento_id", "unita_id"}`.
  - `analizza_contenuto(db, tenant, contenuto: bytes, nome: str) -> AnalisiDocumento` (riusata dal Task 4 sul risultato OCR tramite `analizza_campi(db, risultato: RisultatoTipo | None, ...)`).
- Regole:
  - esito `visura` per `VISURA_CATASTALE` (il frontend apre l'import esistente; nessun salvataggio qui); se l'utente non ha i permessi dell'import visure (`REQUIRED_PERMISSIONS` di `routes/visura_import.py`) esito `scartato` con messaggio "Serve il permesso di import visure" (test `test_visura_senza_permesso_import`);
  - duplicato: sha256 del file uguale a quello di un file di un documento dell'unità abbinata → `gia_presente` (con `forza_duplicato` si salva);
  - APE: avviso se `data_emissione` < `data_riferimento` dell'APE CORRENTE dell'unità; alla conferma `classe` obbligatoria e valida, altrimenti 422 "Indica la classe energetica (A4…G)";
  - conferma: rilegge il file dal token, ricalcola i dati del documento (i valori letti vengono dal file; il client contribuisce `tipo_codice`, `unita_id`, campi mancanti come la classe, selezioni); applica le differenze selezionate con `registra_variazioni(origine="DOCUMENTO", documento_id=...)`, poi `DocumentoService.crea(entity_type=IMMOBILE, entity_id=unita_id, tipo_codice, files=[...], data_riferimento=data_emissione, dati=...)`; tutto in una transazione; token cancellato dopo il commit.

- [ ] **Step 1: test** — `test_ape_pronto_con_unita_e_dati`, `test_testo_sconosciuto_chiede_il_tipo`, `test_rli_scartato`, `test_visura_rimanda_all_import`, `test_unita_non_trovata_chiede_immobile`, `test_duplicato_gia_presente`, `test_conferma_salva_ape_e_aggiorna_campi_selezionati` (indirizzo selezionato aggiornato, piano non selezionato invariato, riga in `immo_variazioni_catastali` con origine `DOCUMENTO`), `test_conferma_ape_piu_vecchio_va_in_storico`, `test_conferma_ape_senza_classe_422`, `test_conferma_token_scaduto_404`, `test_senza_permesso_403`, `test_import_visure_invariato` (la suite visure esistente resta verde dopo lo spostamento degli helper).
- [ ] **Step 2:** FAIL → implementa → PASS; suite verde.
- [ ] **Step 3: Commit** `feat(immobili): analyze/confirm API for the single document upload point`.

### Task 4: Scansioni tramite il servizio esterno (backend)

**Files:**
- Modify: `backend/app/core/platform_services/document_parsing_service.py` (valori `dict`/`list` della `parsing_config` inviati come JSON nel form; `PARSING_SERVICES["ocr_testo"] = {"timeout": 600, "supported_formats": ["pdf", "jpg", "png"]}`; `_create_notification` usa `parsing_config["titolo_attivita"]` se presente)
- Modify: `caricamento.py`, `routes/caricamento_documenti.py` (Task 3)
- Test: `backend/tests/integration/test_modules/test_immobili/test_caricamento_documenti_ocr.py`, `backend/tests/integration/test_core/test_parsing_config_json.py`

**Interfaces:**
- Consumes: `DocumentParsingService.upload_and_parse(..., parsing_service_override="ocr_testo", parsing_config_override={"modalita": "testo", "tipi": [s.to_dict() for s in LETTORI], "titolo_attivita": "Documento immobile letto: <nome> — completa il caricamento"})` con `document_type_key="immobili.ALTRO_IMMOBILE"`.
- Produces:
  - `POST /analizza`: se `pdf_to_text` non trova testo o il file è un'immagine → salva l'upload temporaneo, crea il lavoro, esito `in_lettura` con `job_uuid`.
  - `GET /analizza/{upload_token}` → `AnalisiDocumento` dal lavoro: COMPLETED → dal `parsing_result["tipi"]` prende il primo `riconosciuto` e prosegue come Task 3 (normalizza, abbina, differenze); FAILED/TIMEOUT → esito `errore` con messaggio "Lettura non riuscita: scegli tipo e immobile"; altrimenti `in_lettura`. Il legame token → job sta in un file `job.json` nella cartella del token.
  - Alla conferma di un documento letto con OCR i dati vengono dal risultato del lavoro (non riletti).

- [ ] **Step 1: test** — `test_config_annidata_inviata_come_json` (httpx mockato: il campo `tipi` è una stringa JSON), `test_titolo_attivita_personalizzato`, `test_scansione_crea_lavoro_ocr` (servizio mockato, esito `in_lettura`, `job_uuid`), `test_risultato_ocr_produce_analisi` (lavoro COMPLETED con risultato nel formato del contratto → esito `pronto`, unità abbinata), `test_ocr_fallito_permette_scelta_manuale`.
- [ ] **Step 2:** FAIL → implementa → PASS; suite verde (compresi i test MRZ esistenti).
- [ ] **Step 3: Commit** `feat(immobili): scanned documents read through the external OCR text mode`.

### Task 5: Modalità `testo` del servizio OCR (`~/Progetti/mrz`)

**Files (fuori dal repository):**
- Create: `~/Progetti/mrz/campi.py` (copia identica del motore del Task 1, funzione `applica_spec(spec: dict, testo: str) -> dict` nel formato della risposta del contratto), `~/Progetti/mrz/testo.py` (`process_testo(file_path, tipi: list[dict]) -> dict`), `~/Progetti/mrz/tests/test_testo.py`, `.gitignore`
- Modify: `web_service.py` (`POST /testo`: form `file`, `tipi` JSON, `callback_url`; accoda `tasks.process_testo_job`), `tasks.py` (`process_testo_job`: stessa richiamata di `process_job`, payload `{"job_id", "status", "result", "error"}`)

**Interfaces:**
- Consumes: contratto della spec (richiesta `modalita/tipi`, risposta `testo/pagine/tipi[{codice, riconosciuto, campi{nome: {valore, pagina}}}]`).
- Produces: `process_testo` = `load_document_images(path, dpi=300)` + `ocr_text(img, lang="ita", psm=6)` per pagina (con `detect_orientation`), poi `applica_spec` su ciascuna pagina e sul testo intero; per ogni campo la prima pagina che lo trova.

- [ ] **Step 1:** `git init` in `~/Progetti/mrz` con `.gitignore` che esclude `*.pdf *.jpg *.png *.doc *.vcf jobs/ debug/ venv*/ __pycache__/ .env result.json` (i documenti personali non entrano mai nel repo); primo commit del codice esistente.
- [ ] **Step 2: test** — `test_applica_spec_come_backend` (stessi casi del Task 1 motore), `test_process_testo_su_immagine_generata` (PIL disegna "Foglio 12 Particella 345 Subalterno 6" in nero su bianco, 300 dpi; risultato `campi.foglio.valore == "12"`), `test_endpoint_testo_rifiuta_tipi_non_json` (400).
- [ ] **Step 3:** FAIL → implementa → PASS (`venv/bin/python -m pytest tests -q`).
- [ ] **Step 4:** commit nel repo del servizio; riavvio `mrz-api`/`mrz-worker` e riga `ocr_testo` in `public.core_parsing_services` (`http://127.0.0.1:8008/testo`, HTTP, 600 s) in collaudo: comandi da far eseguire all'utente se i permessi li bloccano.

### Task 6: Classe energetica ricavata dall'APE

**Files:**
- Modify: `backend/modules/immobili/routes/immobili.py` (liste e dettaglio unità), `backend/modules/immobili/schemas/immobili.py` (`classe_energetica` solo in uscita; ignorata in ingresso)
- Create: `backend/modules/immobili/services/ape.py` (`classi_da_ape(db, unita_ids: list[int]) -> dict[int, str]`, una query sui documenti APE CORRENTE)
- Modify: `frontend/src/modules/immobili/components/UnitaImmobiliari/UnitaImmobiliareForm.jsx` (rimuove il select `classe_energetica`)
- Test: `backend/tests/integration/test_modules/test_immobili/test_classe_da_ape.py`, test del form esistente

- [ ] **Step 1: test** — `test_classe_unita_viene_dall_ape_corrente`, `test_unita_senza_ape_classe_vuota`, `test_scrittura_classe_ignorata` (PUT con `classe_energetica` non cambia la colonna), test frontend `il form non mostra la classe energetica`.
- [ ] **Step 2:** FAIL → implementa → PASS; suite backend e frontend verdi.
- [ ] **Step 3: Commit** `feat(immobili): unit energy class derived from the current APE`.

### Task 7: Interfaccia del punto unico

**Files:**
- Create: `frontend/src/modules/immobili/components/Documenti/CaricamentoDocumenti.jsx`, `.css`, `.test.jsx`
- Modify: `DocumentiImmobiliPage.jsx` (area in testa alla pagina; ricarica la lista dopo ogni conferma), `services/immobiliAPI.js` (`caricamentoDocumentiAPI.analizza(file)`, `.stato(token)`, `.conferma(body)`)

**Interfaces:**
- Consumes: API dei Task 3–4; `ImportVisuraModal` con `embedded` e `initialFiles` per l'esito `visura`; componenti UI condivisi (`FormField`, `Badge`, `Button`, toast) e token del design system.
- Produces: area di trascinamento multi-file; una riga per file con stato (Letto · In lettura · Scegli il tipo · Scegli l'immobile · Già presente · Scartato · Errore); pannello della riga con tipo (select dei tipi IMMOBILE), immobile (candidati + ricerca per codice/indirizzo), dati letti modificabili (APE: classe obbligatoria se mancante), differenze con caselle, avvisi, Conferma; righe `in_lettura` interrogate ogni 10 s finché cambiano.

- [ ] **Step 1: test (Vitest, API mockate)** — `mostra una riga per file trascinato`, `esito pronto mostra immobile, dati e differenze`, `scegli_tipo chiede il tipo e rianalizza`, `scartato mostra il messaggio e nessun pulsante conferma`, `conferma invia solo le differenze selezionate`, `visura apre l'import visure`, `in_lettura si aggiorna quando il lavoro finisce`.
- [ ] **Step 2:** FAIL → implementa → PASS; `npm run test:run` e `npm run build` verdi.
- [ ] **Step 3:** agente `revisione-ux` sui file del task; correzioni.
- [ ] **Step 4: Commit** `feat(immobili): single drag-and-drop upload point for unit documents`.

### Task 8: Documentazione e prova in collaudo

**Files:**
- Modify: `docs/modules/immobili.md` (§4 caricamento unico implementato, §6 limiti aggiornati), `docs/piattaforma.md` (§7 modalità OCR testo e servizio `ocr_testo`)

- [ ] **Step 1:** aggiorna i due documenti; `scripts/controlla_documentazione.sh <base> HEAD` → `documentazione: ok`.
- [ ] **Step 2:** commit, push, `scripts/promote.sh`.
- [ ] **Step 3:** prova su `tenant_qa_test` in collaudo con APE, Visura 2b, Planimetria 2b (OCR) e ricevuta RLI di `docs/visure`, su un'unità di prova creata dalla visura; atteso: APE `pronto` (classe da indicare), visura → import, planimetria `in_lettura` poi abbinata o "scegli immobile", RLI scartata. Chiusura dei dati di prova.
