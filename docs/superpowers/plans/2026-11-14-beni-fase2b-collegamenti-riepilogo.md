# Beni catastali — Fase 2b: collegamenti tra beni e "chi paga cosa" — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Un bene si può collegare a un altro (pertinenza, fabbricato su particella, parte di fondo) con un periodo, e la scheda di ogni bene mostra il riepilogo "chi paga cosa" ricavato da diritti e conduttori alla data.

**Architecture:** Nuova tabella `immo_beni_collegamenti` (migrazione di modulo), modello, un servizio con le regole per tipo e le API sotto `/beni/{id}/collegamenti`. Un secondo servizio, `ruoli_bene`, legge diritti e assegnazioni alla data e produce i ruoli (titolari del godimento, proprietari, conduttori). Su quei ruoli si costruisce `GET /beni/{id}/riepilogo`. Il registro costi e ricavi riuserà `ruoli_alla_data` per le quote. Nel frontend la scheda del bene ha due sezioni nuove, uguali per unità e terreni, e la lista unità mostra un'icona per le pertinenze.

**Tech Stack:** FastAPI, SQLAlchemy, migrazioni di modulo in raw SQL (`sync_modules.py`), React + Vitest.

**Spec:** `docs/superpowers/specs/2026-11-10-beni-catastali-design.md`. Sezioni coperte: Obiettivo 9, "Titolari, usufrutto e conduttore", "Collegamenti tra beni", "API" (collegamenti), "Piano a fasi" 2b. Collegata: `docs/superpowers/specs/2026-11-12-costi-ricavi-design.md` (il riepilogo dei ruoli è ciò che la fase 1 del registro aspetta).

Fuori da questo piano:
- la proposta delle pertinenze nel contratto (fase 3);
- il collegamento automatico dall'import delle visure (fase 4);
- qualsiasi importo d'imposta (Non obiettivi);
- i responsabili `USUFRUTTUARIO`/`NUDO_PROPRIETARIO` delle spese ricorrenti: li sostituiranno le quote per ruolo del registro.

## Global Constraints

- **Tabella** `immo_beni_collegamenti`:
  - colonne: `id SERIAL PK`, `bene_id INTEGER NOT NULL → immo_beni(id) ON DELETE CASCADE`, `bene_collegato_id INTEGER NOT NULL → immo_beni(id) ON DELETE CASCADE`, `tipo VARCHAR(30) NOT NULL`, `data_inizio DATE NULL`, `data_fine DATE NULL`, `note TEXT`, `created_at TIMESTAMPTZ NOT NULL DEFAULT now()`, `updated_at TIMESTAMPTZ`;
  - vincoli: `CHECK (bene_id <> bene_collegato_id)`, `CHECK (data_fine IS NULL OR data_inizio IS NULL OR data_fine >= data_inizio)`;
  - indici: su `bene_id` e su `bene_collegato_id`;
  - indice unico parziale `uq_immo_beni_collegamenti_aperto (bene_id, bene_collegato_id, tipo) WHERE data_fine IS NULL`;
  - indice unico parziale `uq_immo_beni_pertinenza_aperta (bene_collegato_id) WHERE tipo = 'PERTINENZA' AND data_fine IS NULL`: una pertinenza appartiene a una sola abitazione per volta.
- **Tipo** senza CHECK nel DB: l'elenco è in Python (`TIPI_COLLEGAMENTO`), così aggiungere un tipo non richiede una migrazione (spec: "un elenco che si può estendere").
- **Regole per tipo** (principale → collegato), violazione = 400 col messaggio fra virgolette:
  - `PERTINENZA`: unità di categoria `A/*` diversa da `A/10` → unità di categoria `C/2`, `C/6` o `C/7`. Messaggi: `"Una pertinenza si collega a un'abitazione (categoria A, tranne A/10)"`, `"Pertinenza: serve un'unità di categoria C/2, C/6 o C/7"`. Un'unità senza categoria non passa nessuno dei due controlli.
  - `FABBRICATO_SU_PARTICELLA`: terreno → unità. Messaggio `"Fabbricato su particella: il principale è un terreno, il collegato un'unità"`.
  - `PARTE_DI_FONDO`: terreno → terreno. Messaggio `"Parte di fondo: collega due terreni"`.
  - Collegamento aperto già presente → `"Collegamento già presente"`.
  - Pertinenza già aperta su un'altra abitazione → `"'<codice>' è già pertinenza di '<codice abitazione>'"`.
  - Un bene con sé stesso → `"Un bene non si collega a sé stesso"`.
- **Avvisi** (non bloccano; stringhe esatte):
  - `"Più pertinenze di categoria <C/x>: per l'IMU dell'abitazione principale ne conta una per categoria (L. 160/2019, c. 741)"`;
  - `"Titolari di '<codice pertinenza>' diversi da quelli dell'abitazione"`, calcolato confrontando gli insiemi di `proprietario_id` con diritto aperto oggi.
- **Permessi**:
  - lettura: il bene della route deve essere visibile come in `/beni` (`immobile.view` per le unità, `terreno.view` per i terreni; tipo non visibile → 404, nessun permesso → 403). Nell'elenco dei collegamenti spariscono quelli il cui altro bene non è visibile.
  - scrittura (crea, modifica, cancella): permesso `immobile.edit` o `terreno.edit` sul tipo del bene della route, più la visibilità dell'altro bene.
- **Ruoli alla data** `d`:
  - un diritto vale se `data_inizio` è vuota o `<= d` e `data_fine` è vuota o `>= d`. Le date dei diritti sono stringhe `YYYY-MM-DD`: il confronto fra stringhe va bene. Per le assegnazioni del conduttore vale la stessa regola, con colonne `Date`.
  - **titolari del godimento**: i diritti `USUFRUTTUARIO, USO, ABITAZIONE, ENFITEUSI, SUPERFICIE` se ce n'è almeno uno; altrimenti `PROPRIETARIO, COMPROPRIETARIO`.
  - **proprietari**: `NUDA_PROPRIETA, PROPRIETARIO, COMPROPRIETARIO`.
  - `ALTRO` non entra in nessun gruppo e produce l'avviso `"Diritto 'ALTRO' di <nome>: ripartizione da decidere a mano"`.
- **Quote**: `quota_percentuale` del diritto. Se manca e il soggetto è l'unico del gruppo vale 100; se manca e i soggetti sono più di uno vale `null`, con l'avviso `"Quote mancanti per <gruppo>"`. Un gruppo con quote tutte presenti la cui somma non è 100 dà l'avviso `"Le quote di <gruppo> sommano a <X>%"`. `<gruppo>` vale `titolari del godimento` o `proprietari`.
- **Voci del riepilogo**, nell'ordine: `codice | etichetta | a chi | norma`.
  - `RENDITA`: "Rendita catastale" per l'unità, "Reddito dominicale" per il terreno. Va ai titolari del godimento. Norma: "TUIR artt. 26, 27".
  - `REDDITO_AGRARIO`: solo per i terreni. Va ai conduttori in corso che non sono titolari; se non ce ne sono, ai titolari del godimento. Norma: "TUIR artt. 32, 33".
  - `IMU`: ai titolari del godimento. Norma: "L. 160/2019, c. 743".
  - `SPESE_ORDINARIE`: ai conduttori in corso se ci sono, altrimenti ai titolari del godimento. Norma: "c.c. art. 1004".
  - `SPESE_STRAORDINARIE`: ai proprietari se esiste un diritto di godimento diverso dalla proprietà, altrimenti ai titolari del godimento. Norma: "c.c. art. 1005".
  - `CANONE`: ai titolari del godimento. Norma: "chi concede il godimento (modulo affitti)".
- **Quota dei conduttori**: `null` quando i conduttori sono più di uno, 100 quando è uno solo.
- **Nessun importo**: il riepilogo dice a chi va ciascuna voce, non quanto.
- **Commit e file esclusi**: i commit chiudono con `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`; non si committano mai `deploy/`, `docs/visure/`, `notifiche-followup-fix-report.md`.
- **Lezioni della fase 1/2a**:
  - mai `query(...).delete()` in blocco su una sottoclasse;
  - la migrazione deve funzionare su un tenant nuovo: aggiornare `CATENA_TENANT`, `EXCLUDED_TABLES` e `TABELLE_AZZERATE`;
  - nessun residuo in `tenant_qa_test`;
  - il backend dev non ricarica `modules/`: va riavviato.

## Review Focus

1. Box già pertinenza dell'appartamento A e collegato ora all'appartamento B: deve dare un 400 che nomina A, non un 500 da violazione dell'indice unico → test in Task 3.
2. Collegamento chiuso (`data_fine` valorizzata) e poi riaperto sulla stessa coppia: deve essere permesso; il vecchio resta nello storico → test in Task 3.
3. Bene cancellato con collegamenti in entrambe le direzioni: i collegamenti spariscono e l'altro bene resta → test in Task 2.
4. Utente con solo `immobile.view` che apre un'unità costruita su una particella: non vede il terreno collegato e non ottiene un 404 sull'intera sezione → test in Task 3.
5. Nudo proprietario + usufruttuario + conduttore terzo sullo stesso terreno (caso Forlì):
   - rendita e IMU all'usufruttuario;
   - reddito agrario e spese ordinarie al conduttore;
   - spese straordinarie al nudo proprietario.

   Diritto scaduto ieri: non conta → test in Task 4.

---

### Task 1: migrazione e modello dei collegamenti

**Files:**
- Create: `backend/modules/immobili/migrations/2026111401_collegamenti_beni.py`
  - revision `2026111401_collegamenti_beni`, down_revision `2026111301_terreni_beni`, `target_schema = "tenant"`;
  - `upgrade()` crea tabella e indici con `IF NOT EXISTS`;
  - `downgrade()` fa `DROP TABLE IF EXISTS`.
- Create: `backend/modules/immobili/models/collegamento_beni.py`; export da `models/__init__.py`.
- Modify: liste delle tabelle, dopo `immo_beni`:
  - `migrations/2025022002_tenant_tables.py` (`EXCLUDED_TABLES`);
  - `migrations/2026111201_beni.py` (`TABELLE_AZZERATE`, con il commento "esiste solo da 2026111401");
  - `__manifest__.py`;
  - `backend/app/core/services/tenant_module_service.py`.
- Test:
  - `backend/tests/integration/test_modules/test_immobili/test_collegamenti_model.py`;
  - `CATENA_TENANT` di `test_migrazione_beni.py` += `"2026111401_collegamenti_beni"`.

**Interfaces:**
- Produces:
  - `class CollegamentoBeni(Base)` con `__tablename__ = "immo_beni_collegamenti"`, le colonne del vincolo globale, `bene = relationship("Bene", foreign_keys=[bene_id])`, `bene_collegato = relationship("Bene", foreign_keys=[bene_collegato_id])` e la proprietà `aperto -> bool` (`data_fine is None`);
  - nessuna relationship inversa su `Bene` con cascade ORM: la cancellazione la fa il DB (`ON DELETE CASCADE`). Se una relationship serve, va dichiarata `passive_deletes=True`.

- [ ] **Step 1: test**
  - `test_installazione_su_tenant_nuovo` (esistente, con la revisione in coda): esistono `immo_beni_collegamenti` e i due indici parziali (`pg_indexes`).
  - `test_stessa_pertinenza_due_abitazioni_viola_indice`: due collegamenti `PERTINENZA` aperti con lo stesso `bene_collegato_id` → `IntegrityError`; chiudendo il primo (`data_fine`), il secondo passa.
  - `test_bene_non_si_collega_a_se_stesso`: `IntegrityError` (CHECK).
  - `test_azzera_con_collegamenti`: `azzera()` della migrazione beni non fallisce se ci sono collegamenti.
- [ ] **Step 2:** `cd backend && pytest tests/integration/test_modules/test_immobili/test_collegamenti_model.py tests/integration/test_modules/test_immobili/test_migrazione_beni.py -q --no-cov` → FAIL.
- [ ] **Step 3:** scrivi migrazione e modello e aggiorna le liste.
- [ ] **Step 4:** backup del DB dev in `~/apps/gestione-affitti-backups` (umask 077), poi `alembic -x schema=all upgrade head && python scripts/sync_modules.py`. Controlla `alembic_version_IMMO` di `tenant_qa_test` = `2026111401_collegamenti_beni`. Test → PASS.
- [ ] **Step 5:** commit `feat(immobili): links between beni (table and model)`.

### Task 2: servizio dei collegamenti (regole e avvisi)

**Files:**
- Create: `backend/modules/immobili/services/collegamenti_beni.py`
- Test: `backend/tests/integration/test_modules/test_immobili/test_collegamenti_service.py`

**Interfaces:**
- Consumes: `CollegamentoBeni` (Task 1), `UnitaImmobiliare.categoria_catastale.codice`, `DirittoImmobile`.
- Produces:
  - `TIPI_COLLEGAMENTO: dict[str, dict]`, con chiave il tipo e valori `etichetta_principale`, `etichetta_collegato`, `verifica(principale: Bene, collegato: Bene) -> str | None` (messaggio d'errore o `None`). Etichette:
    - PERTINENZA: "Pertinenze" / "Pertinenza di";
    - FABBRICATO_SU_PARTICELLA: "Fabbricati sulla particella" / "Costruito sulla particella";
    - PARTE_DI_FONDO: "Particelle del fondo" / "Parte del fondo di".
  - `class CollegamentoNonValido(ValueError)`: la route lo traduce in 400 con `str(e)`.
  - `crea_collegamento(db, principale_id: int, collegato_id: int, tipo: str, data_inizio: date | None, note: str | None) -> CollegamentoBeni`:
    - fa tutti i controlli del vincolo globale prima del flush, così i messaggi sono quelli giusti;
    - cattura comunque l'`IntegrityError` degli indici parziali (corsa fra due richieste) e lo trasforma in `CollegamentoNonValido("Collegamento già presente")`.
  - `aggiorna_collegamento(db, collegamento, data_inizio, data_fine, note) -> CollegamentoBeni`:
    - estremi e tipo non cambiano;
    - riaprire un collegamento (`data_fine` → `None`) ripete i controlli di unicità.
  - `avvisi_collegamenti(db, bene_id: int, oggi: date) -> list[str]`: gli avvisi del vincolo globale per il bene, sia quando è l'abitazione sia quando è la pertinenza.

- [ ] **Step 1: test**, con fixture: abitazione `A/3`, box `C/6`, cantina `C/2`, secondo box `C/6`, ufficio `A/10`, terreno, unità sul terreno.
  - `test_pertinenza_valida`: abitazione → box → creato, `aperto is True`.
  - `test_pertinenza_regole`: ufficio → box, box → abitazione, abitazione → terreno, abitazione → unità senza categoria: ognuno dà `CollegamentoNonValido` col messaggio del vincolo.
  - `test_pertinenza_gia_di_altra_abitazione`: box di A, poi di B → messaggio `"'BOX-1' è già pertinenza di 'APP-A'"`.
  - `test_riapertura_dopo_chiusura`: chiudi con `data_fine`, crea di nuovo → ok; due righe, una aperta.
  - `test_fabbricato_e_fondo_regole`: terreno → unità ok; unità → terreno errore; terreno → terreno `PARTE_DI_FONDO` ok, terreno → unità `PARTE_DI_FONDO` errore.
  - `test_avviso_due_pertinenze_stessa_categoria`: abitazione con due `C/6` → l'avviso `C/6`; con un `C/6` e un `C/2` → nessun avviso.
  - `test_avviso_titolari_diversi`: abitazione di P1, box di P2 → avviso col codice del box, sia nella lista dell'abitazione sia in quella del box.
  - `test_cancellare_bene_toglie_collegamenti`: `elimina_bene(db, box, user_id)` → collegamento sparito, abitazione presente.
- [ ] **Step 2:** pytest sul file → FAIL.
- [ ] **Step 3:** implementa.
- [ ] **Step 4:** test → PASS.
- [ ] **Step 5:** commit `feat(immobili): link rules and warnings for pertinenze, buildings on parcels, farm parcels`.

### Task 3: API dei collegamenti

**Files:**
- Modify: `backend/modules/immobili/routes/beni.py`
- Create: `backend/modules/immobili/schemas/collegamento_beni.py`
- Modify: `backend/modules/immobili/routes/immobili.py`, che in `_risposte` aggiunge `ruolo_pertinenza`, e `schemas/immobili.py`, con `UnitaImmobiliareResponse.ruolo_pertinenza: Optional[Literal["PERTINENZA", "CON_PERTINENZE"]] = None`
- Test: `backend/tests/integration/test_modules/test_immobili/test_collegamenti_api.py`

**Interfaces:**
- Consumes: Task 2.
- Produces (contratto per il frontend, Task 5):
  - `GET /beni/{id}/collegamenti?storico=false` → `CollegamentiBeneResponse { collegamenti: list[CollegamentoOut], avvisi: list[str] }`.
    - `CollegamentoOut` = `id, tipo, questo_e ("PRINCIPALE" | "COLLEGATO"), etichetta` (l'etichetta del tipo vista da questo bene), `altro_bene: BeneResponse, data_inizio, data_fine, note, aperto`.
    - Senza `storico` solo gli aperti; con `storico=true` tutti, prima gli aperti e poi per `data_fine` decrescente.
  - `POST /beni/{id}/collegamenti` con body `CollegamentoCreate { altro_bene_id: int, tipo: str, questo_e: "PRINCIPALE" | "COLLEGATO" = "PRINCIPALE", data_inizio: date | None, note: str | None }` → 201 `CollegamentoOut`.
    - Si sceglie la direzione dal lato del bene della scheda: per esempio dal box, `questo_e="COLLEGATO"`.
    - Un tipo sconosciuto dà 400 `"Tipo di collegamento sconosciuto: <X>"`.
  - `PUT /beni/{id}/collegamenti/{cid}` con body `CollegamentoUpdate { data_inizio?, data_fine?, note? }` → `CollegamentoOut`. Un `cid` che non riguarda `{id}` (da nessuno dei due lati) dà 404 `"Collegamento non trovato"`.
  - `DELETE /beni/{id}/collegamenti/{cid}` → 204.
  - `ruolo_pertinenza` nella lista unità: `PERTINENZA` se l'unità è collegata da una `PERTINENZA` aperta, `CON_PERTINENZE` se ne ha. Una sola query per tutta la pagina.

- [ ] **Step 1: test.** Le route si chiamano direttamente come in `test_beni_api.py`, con utenti finti con permessi espliciti.
  - `test_crea_e_elenca_pertinenza`: POST dall'abitazione → 201. GET dall'abitazione → `questo_e == "PRINCIPALE"`, `etichetta == "Pertinenze"`; GET dal box → `"Pertinenza di"`, `altro_bene.codice == "APP-A"`.
  - `test_crea_dal_lato_collegato`: POST dal box con `questo_e="COLLEGATO"` → stesso risultato.
  - `test_pertinenza_doppia_400_non_500`: Review Focus 1.
  - `test_chiudi_e_riapri`: PUT `data_fine` → sparisce dagli aperti, presente con `storico=true`; POST di nuovo → 201 (Review Focus 2).
  - `test_data_fine_prima_di_inizio_400`: viene dalla validazione dello schema, quindi 422 o 400 secondo il pattern in uso; nessun 500.
  - `test_altro_bene_invisibile_nascosto`: utente con solo `immobile.view` → GET sull'unità costruita sul terreno → 200, `collegamenti == []` (Review Focus 4); POST verso il terreno → 404 `"Bene non trovato"`.
  - `test_scrittura_senza_edit_403`: `immobile.view` senza `immobile.edit` → POST 403.
  - `test_collegamento_di_altro_bene_404`: PUT/DELETE con `cid` di una coppia diversa → 404.
  - `test_lista_unita_ruolo_pertinenza`: `get_unita_immobiliari` → abitazione `CON_PERTINENZE`, box `PERTINENZA`, altra unità `None`.
- [ ] **Step 2:** pytest sul file → FAIL.
- [ ] **Step 3:** implementa e riusa `_bene_visibile`/`_tipi_visibili`. Aggiungi `_PERMESSO_MODIFICA = {"UNITA": "immobile.edit", "TERRENO": "terreno.edit"}`.
- [ ] **Step 4:** `cd backend && pytest tests -q --no-cov` → tutto PASS.
- [ ] **Step 5:** commit `feat(immobili): /beni/{id}/collegamenti API and pertinenza flag in unit list`.

### Task 4: ruoli alla data e riepilogo "chi paga cosa"

**Files:**
- Create: `backend/modules/immobili/services/ruoli_bene.py`
- Create: `backend/modules/immobili/schemas/riepilogo_bene.py`
- Modify: `backend/modules/immobili/routes/beni.py`
- Test: `backend/tests/unit/test_modules/test_immobili/test_ruoli_bene.py` (logica pura su oggetti in memoria, se `ruoli_da_righe` lo permette), `backend/tests/integration/test_modules/test_immobili/test_riepilogo_api.py`

**Interfaces:**
- Produces (il registro costi e ricavi riuserà `ruoli_alla_data`: nomi stabili):
  - `@dataclass Soggetto(soggetto_id: int, nome: str, ruolo: str, quota: Decimal | None)`. `ruolo` è il `tipo_diritto` oppure `"CONDUTTORE"`; `nome` = `soggetto.nome_completo`.
  - `@dataclass RuoliBene(titolari_godimento: list[Soggetto], proprietari: list[Soggetto], conduttori: list[Soggetto], usufrutto: bool, avvisi: list[str])`. `usufrutto` è True quando c'è un diritto di godimento diverso dalla proprietà.
  - `ruoli_da_righe(diritti, assegnazioni, d: date) -> RuoliBene`: puro, senza DB.
  - `ruoli_alla_data(db, bene_id: int, d: date) -> RuoliBene`: carica e delega.
  - `riepilogo_bene(db, bene: Bene, d: date) -> RiepilogoBene`, con `RiepilogoBene { data, voci: list[Voce], avvisi }` e `Voce { codice, etichetta, soggetti: list[Soggetto], norma }`, secondo le voci del vincolo globale.
  - `GET /beni/{id}/riepilogo?data=YYYY-MM-DD` (default oggi) → `RiepilogoBeneResponse`. Oltre alla visibilità del bene richiede `proprietario.view` e `conduttore.view` (mostra i nomi); senza → 403.

- [ ] **Step 1: verifica di dominio.** Agente `esperto-gestione-immobiliare-ita`, su Sonnet, con l'Archivio Fiscale. Domande:
  1. Tra i titolari del godimento vanno anche uso, abitazione, enfiteusi e superficie, per redditi fondiari (TUIR art. 26), IMU (L. 160/2019, c. 743) e spese (c.c. artt. 1004–1005, 1025, 960 e seguenti)?
  2. Le spese straordinarie con enfiteusi restano all'enfiteuta?
  3. Il reddito agrario di un conduttore che è anche contitolare?

  Se la risposta cambia una regola del vincolo globale: correggi il vincolo nel piano, scrivi la riga `Ruling:` nel ledger e aggiungi una riga alla spec ("Titolari, usufrutto e conduttore"). Quello che resta incerto va in "Da verificare con un professionista".
- [ ] **Step 2: test.**
  - `test_caso_forli`: nudo proprietario N (quota 100), usufruttuario U (100) e conduttore C su un terreno.
    - `RENDITA` = [U 100], `REDDITO_AGRARIO` = [C 100], `IMU` = [U], `SPESE_ORDINARIE` = [C], `SPESE_STRAORDINARIE` = [N], `CANONE` = [U].
    - Etichetta della prima voce: "Reddito dominicale".
  - `test_piena_proprieta_due_comproprietari_senza_conduttore`: unità, P1 50 e P2 50.
    - Ogni voce va a [P1 50, P2 50].
    - Niente `REDDITO_AGRARIO`; prima etichetta "Rendita catastale".
  - `test_conduttore_che_e_titolare`: il conduttore C è anche proprietario.
    - `REDDITO_AGRARIO` va ai titolari del godimento, perché C non è un terzo.
    - `SPESE_ORDINARIE` va a [C].
  - `test_diritto_scaduto_non_conta`: `data_fine` = ieri → escluso. Con `d` = due giorni fa → incluso.
  - `test_quote_mancanti_e_somma`: due comproprietari senza quota → quote `None` e avviso `"Quote mancanti per titolari del godimento"`; quote 50 + 40 → avviso `"... sommano a 90%"`.
  - `test_diritto_altro_avviso`.
  - `test_nessun_diritto`: voci con `soggetti == []` e avviso `"Nessun titolare registrato alla data"`.
  - API:
    - `test_riepilogo_api_data_default_oggi`;
    - `test_riepilogo_senza_proprietario_view_403`;
    - `test_riepilogo_terreno_con_solo_immobile_view_404`.
- [ ] **Step 3:** pytest sui due file → FAIL.
- [ ] **Step 4:** implementa.
- [ ] **Step 5:** `cd backend && pytest tests -q --no-cov` → PASS.
- [ ] **Step 6:** commit `feat(immobili): roles at a date and "who pays what" summary of a bene`.

### Task 5: frontend — sezioni "Beni collegati" e "Chi paga cosa", icona in lista

**Files:**
- Modify: `frontend/src/modules/immobili/services/immobiliAPI.js`, che aggiunge a `beniAPI`:
  - `getCollegamenti(id, storico=false)`;
  - `creaCollegamento(id, dati)`;
  - `aggiornaCollegamento(id, cid, dati)`;
  - `eliminaCollegamento(id, cid)`;
  - `getRiepilogo(id, data)`.
- Create: `frontend/src/modules/immobili/components/BeneScheda/CollegamentiSection.jsx`, `CollegamentoForm.jsx`, `opzioniCollegamento.js`, `RiepilogoSection.jsx`.
- Modify: `BeneScheda.jsx` (le due sezioni dopo "Dati" e prima di "Documenti"), `BeneScheda.css`, `components/UnitaImmobiliari/UnitaImmobiliariList.jsx`.
- Test: `opzioniCollegamento.test.js`, `CollegamentiSection.test.jsx`, `RiepilogoSection.test.jsx`, `BeneScheda.test.jsx` (mock delle due sezioni nuove), test della lista unità se esiste.

**Interfaces:**
- Consumes: contratti di Task 3 e Task 4.
- Produces: `opzioniCollegamento(bene) -> Array<{ tipo, questo_e, etichetta, tipoAltro: 'UNITA' | 'TERRENO' }>`, che dice cosa si può creare dalla scheda:
  - unità `A/*` tranne `A/10`: `PERTINENZA`, PRINCIPALE, "Aggiungi pertinenza", tipoAltro UNITA;
  - unità `C/2`, `C/6`, `C/7`: `PERTINENZA`, COLLEGATO, "È pertinenza di…", UNITA;
  - ogni unità: `FABBRICATO_SU_PARTICELLA`, COLLEGATO, "Costruita sulla particella…", TERRENO;
  - terreno:
    - `FABBRICATO_SU_PARTICELLA`, PRINCIPALE, "Aggiungi fabbricato", UNITA;
    - `PARTE_DI_FONDO`, PRINCIPALE, "Aggiungi particella del fondo", TERRENO;
    - `PARTE_DI_FONDO`, COLLEGATO, "È parte del fondo di…", TERRENO.

  Il server resta l'autorità: l'elenco serve solo a non offrire scelte impossibili.
- **`CollegamentiSection`** (`beneId`, `bene`):
  - titolo "Beni collegati";
  - righe raggruppate per `etichetta`, ciascuna con un link a `/beni/:altro_id`, `codice · descrizione` e il periodo;
  - avvisi in un box di avviso (`role="status"`);
  - azioni "Chiudi" (data fine, default oggi) ed "Elimina" (`ConfirmDialog`);
  - interruttore "Mostra storico";
  - stato vuoto "Nessun bene collegato".
- **`CollegamentoForm`**: modale con la scelta dell'opzione, poi la ricerca del bene (`beniAPI.getAll({ q, tipo_bene: tipoAltro })`, risultati in un elenco cliccabile, al massimo 20), data inizio e note.
  - Gli errori del server vanno in `role="alert"` con `formatApiError`.
  - Pulsanti Annulla poi Salva.
  - La ricerca è locale al form: il selettore unico dei beni è della fase 3, che la potrà sostituire.
- **`RiepilogoSection`** (`beneId`):
  - titolo "Chi paga cosa";
  - campo data (default oggi) e tabella `Voce | A chi | Quota | Riferimento`, con "—" se non ci sono soggetti e quota "—" se `null`;
  - avvisi come sopra;
  - nota fissa "Indica a chi spetta ciascuna voce, non calcola importi.";
  - un 403 nasconde la sezione senza errore, perché l'utente non ha i permessi sui nomi.
- **Lista unità**: colonna senza etichetta visibile con l'icona lucide `Link2` e `aria-label`/`title`: "Pertinenza di un'abitazione" o "Ha pertinenze".

- [ ] **Step 1: test**
  - `opzioniCollegamento`: `A/3`, `A/10` (solo FABBRICATO), `C/6`, terreno → gli elenchi attesi.
  - `CollegamentiSection`:
    - con mock di due collegamenti (uno da principale, uno da collegato) mostra le due etichette, link `href="/beni/9"` e l'avviso;
    - "Elimina" → conferma → `eliminaCollegamento(5, 3)` e ricarica;
    - stato vuoto.
  - `CollegamentoForm`: scegli "Aggiungi pertinenza", cerca "BOX", clicca il risultato, salva → `creaCollegamento(5, { altro_bene_id: 9, tipo: 'PERTINENZA', questo_e: 'PRINCIPALE', data_inizio: null, note: null })`. Un errore 400 mostra il messaggio del server.
  - `RiepilogoSection`:
    - riga "Spese straordinarie" con il nome del nudo proprietario;
    - quota `null` → "—";
    - cambio data → `getRiepilogo(5, '2025-01-01')`;
    - risposta 403 → la sezione non c'è.
- [ ] **Step 2:** `cd frontend && npx vitest run src/modules/immobili` → FAIL.
- [ ] **Step 3:** implementa con i componenti del design system (`Button`, `ConfirmDialog`, token CSS) e senza colori fissi.
- [ ] **Step 4:** test → PASS; `npm run build` ok.
- [ ] **Step 5:** riavvia il backend dev e prepara i dati in `tenant_qa_test` via API:
  - abitazione `A/3`, due box `C/6`, un terreno con un'unità sopra;
  - diritti: nuda proprietà, usufrutto e un conduttore sul terreno.

  Col crawler (scratchpad `crawl.mjs`, tenant da `current_tenant` nel localStorage) apri le schede e controlla:
  - nessuna chiamata fallita;
  - sezioni visibili;
  - avviso `C/6` presente;
  - icona in lista.

  Poi cancella tutti i dati di prova e controlla con una query che non resti nulla.
- [ ] **Step 6:** agente `revisione-ux` sui file frontend del task; correggi i problemi gravi.
- [ ] **Step 7:** commit `feat(immobili-ui): linked beni and "who pays what" on the bene page`.

### Task 6: documentazione, revisione, verifica, rilascio

**Files:**
- Modify:
  - `docs/modules/immobili.md`: collegamenti, regole, avvisi, API, riepilogo e permessi; togli le voci risolte da §5.
  - Spec beni: 2b fatta con la data; aggiunte di dominio dello Step 1 del Task 4.
  - Spec costi-ricavi: §"Ripartizione" punta a `immobili.services.ruoli_bene.ruoli_alla_data`.
  - `docs/piattaforma.md` solo se cambia qualcosa di piattaforma.

- [ ] **Step 1:** aggiorna i documenti; `bash scripts/controlla_documentazione.sh master HEAD` → ok.
- [ ] **Step 2:** revisione dell'intero ramo con un revisore nuovo su Sonnet; correzioni Critical/Important con test RED→GREEN e suite verde.
- [ ] **Step 3:** agente `verifica-test` → VERDE (backend, frontend, build, nessun residuo nel DB dev).
- [ ] **Step 4:** agente `rilascio` senza `PROMOTE_PERDITA_CONSENTITA`: la migrazione aggiunge solo una tabella. Se `promote.sh` segnala perdite, fermarsi e avvisare. Dopo il rilascio: backup verificato e tutti i tenant su `2026111401_collegamenti_beni`.
