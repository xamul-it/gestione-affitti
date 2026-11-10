# Relazioni di ruolo tra soggetti e oggetti dei moduli

Data: 2026-11-10 — Stato: **approvata in chat** (2026-11-10)

## Problema

- La pagina Proprietari (e Conduttori) mostra solo `soggetto_id`, note e data: non si vedono i dati anagrafici.
- Il ruolo di un soggetto non è un attributo della persona ma nasce da una **relazione con un oggetto**: la stessa persona è proprietaria di un'unità, conduttrice di un'altra, amministratrice di un condominio, ruolo in un'azienda.
- Il sistema ruoli del core esiste ma è inutilizzato e sporco:
  - `core_ruoli_disponibili` (**public**): catalogo con `codice`, `modulo_id`, `nome_display`, `tabella_specializzazione`. In collaudo "proprietario", "affittuario", "tecnico" sono registrati due volte (da `affitti_lungo` e da `anagrafica_italiana`), nessuno da `immobili`.
  - `core_soggetti_ruoli` (**public**, quindi condivisa fra tenant: non adatta a dati dei clienti): assegnazioni soggetto → ruolo, **0 righe** in collaudo; nessun modulo le scrive.
  - Il manifest di `anagrafica_italiana` ha anche una lista `ruoli_disponibili` letta da `modules_api`.
- La "tipologia ruoli" pensata come catalogo per modulo è diventata `anag_ruoli_azienda_tipi` (10 tipi, solo ruoli persona-azienda); i legami `anag_ruoli_azienda` sono 0 in collaudo.
- L'amministratore di condominio è testo libero (`amministratore_nome/telefono/email/indirizzo`), non un'anagrafica.

## Obiettivo

Un modello unico: **catalogo dei tipi di relazione dichiarati dai moduli** + **relazioni soggetto → ruolo → oggetto di un modulo**, con scadenza opzionale decisa dal tipo che finisce nello scadenziario. Le liste di soggetti (Anagrafiche, Proprietari, Conduttori, …) sono un solo componente riusabile con prefiltro per ruolo e personalizzazioni del modulo.

## Decisioni

### 1. Catalogo: `relation_types` nel manifest

Ogni modulo dichiara i suoi tipi di relazione nel `__manifest__.py`, come per `document_types`. Campi:

| Campo | Significato |
|---|---|
| `codice`, `nome`, `descrizione` | identificativo (minuscolo, es. `proprietario`) e testi |
| `entity_types` | su quali oggetti si applica (`EntityType`, es. `["IMMOBILE"]`, `["CONDOMINIO"]`, `["SOGGETTO_ANAGRAFICO"]`); `null` = ruolo senza oggetto (es. tecnico, ruoli PEC) |
| `fonte` | `CORE`: le relazioni stanno in `core_soggetti_ruoli` e si gestiscono col servizio del core. `MODULO`: le relazioni sono ricavate dalle tabelle del modulo tramite un *provider* (vedi 3) |
| `provider` | solo per `fonte = MODULO`: `"modulo.path:funzione"` |
| `scadenza` | `null` = nessuna; `{"manuale": true}` = data facoltativa inserita a mano; `{"mesi": n, "da": "data_inizio"}` = calcolata. Solo per `fonte = CORE` |
| `promemoria_giorni` | es. `[60, 30]`, salvato come per i documenti |
| `sottotipi_fonte` | opzionale: da dove vengono i sottotipi (vedi 5, ruoli in azienda) |

La scadenza è decisa dal **tipo** (approvato dall'utente). Ogni relazione ha comunque `data_inizio` / `data_fine`: la fine dice che la relazione è chiusa, la scadenza dice quando va rinnovata/verificata e solo quella va nello scadenziario.

Sincronizzazione: in `scripts/sync_modules.py` (a ogni promote) e all'installazione del modulo, come le tipologie documentali. Upsert per (`codice`, `modulo_id`) in `public.core_ruoli_disponibili` (catalogo condiviso, come `core_tipi_documento`), con le nuove colonne `entity_types`, `fonte`, `provider`, `scadenza`, `promemoria_giorni`, `sottotipi_fonte`. Un tipo non più dichiarato diventa `attivo = false` (mai cancellato: le relazioni lo referenziano), solo se tutti i manifest registrati sono stati letti. Le righe doppie esistenti (`proprietario`/`affittuario`/`tecnico` di `anagrafica_italiana`, `proprietario` di `affitti_lungo`) diventano `attivo = false`.

Il meccanismo `endpoints.register_roles` (usato da `gestione_pec` e `affitti_lungo`) resta funzionante; `affitti_lungo` passa ai `relation_types`; la lista `ruoli_disponibili` del manifest anagrafica viene rimossa. I ruoli PEC restano com'erano (senza oggetto).

### 2. Relazioni del core (`fonte = CORE`)

Nuova tabella **tenant** `core_relazioni` (non `public.core_soggetti_ruoli`, che è condivisa fra tenant; resta vuota e deprecata):
- `id`, `soggetto_id`, `ruolo_id` (FK `public.core_ruoli_disponibili`);
- `entity_type`, `entity_id`: l'oggetto;
- `sottotipo`;
- `data_inizio`, `data_fine` (Date);
- `data_scadenza`, `scadenza_id` (FK logica alla `Scadenza` del core);
- `dati` (JSON);
- `note`, `created_at`, `updated_at`, `creato_da`.

La stessa persona può avere lo stesso ruolo su oggetti diversi o in periodi diversi (nessun vincolo unico DB, regole nel servizio: vedi "Scelte").

`RelazioneService(db, tenant_schema, user_id)` (flush, mai commit), come `DocumentoService`:
- `crea(soggetto_id, tipo_codice, entity_type, entity_id, data_inizio, data_fine, data_scadenza, sottotipo, note, dati)`: valida che il tipo sia `CORE`, attivo e applicabile all'`entity_type`; calcola la scadenza se il tipo è `{"mesi", "da"}` (la data manuale vince solo per `{"manuale": true}`); crea la `Scadenza` del core legata alla relazione se c'è una scadenza e la relazione non è chiusa;
- `aggiorna(id, …)`: ricalcola la scadenza; se la relazione viene chiusa (`data_fine` valorizzata) la scadenza diventa COMPLETATA;
- `elimina(id)`: la scadenza diventa ANNULLATA;
- `rinnova(id)` per i tipi calcolati: sposta `data_scadenza` di un periodo e la scadenza del core di conseguenza (utile per il mandato amministratore, rinnovato tacitamente).

### 3. Relazioni ricavate dai moduli (`fonte = MODULO`)

Il modulo registra un provider: `funzione(db, filtri) -> query` che restituisce righe con `soggetto_id`, `entity_type`, `entity_id`, `descrizione` (testo leggibile dell'oggetto, es. "Via Roma 1, Milano — 50%"), `data_inizio`, `data_fine`, `record_id`. Filtri: `soggetto_ids`, `entity_type`, `entity_id`, `solo_correnti`.

Nessuna doppia scrittura: la verità resta nelle tabelle del modulo.

| Tipo | Modulo | Oggetto | Da dove |
|---|---|---|---|
| `proprietario` | immobili | IMMOBILE | `immo_proprietari` ⟕ `immo_diritti_immobile` (un proprietario senza diritti è comunque proprietario, senza oggetto) |
| `conduttore` | immobili | IMMOBILE | `immo_conduttori` ⟕ `immo_assegnazioni_conduttore` |
| `affittuario` | affitti_lungo | — | `affittuari` |
| `tecnico` | affitti_lungo | — | `tecnici` |
| `amministratore_condominio` | immobili | CONDOMINIO | **CORE**, scadenza `{"mesi": 12, "da": "data_inizio"}` (art. 1129 c.c.: incarico annuale, rinnovato per eguale durata) |
| `ruolo_azienda` | anagrafica_italiana | SOGGETTO_ANAGRAFICO (persona giuridica) | **CORE**, sottotipi da `anag_ruoli_azienda_tipi` |

Il provider di un modulo non attivo nel tenant (tabella assente) non restituisce nulla e non fa fallire la richiesta. Verificare con l'inspector prima della query, mai con try/rollback: un rollback annulla il `SET search_path` di `get_db()` (vedi `_has_role_records` in `soggetti_v2.py`).

### 4. API del core

- `GET /api/v1/relazioni/tipi?entity_type=` → tipi attivi (catalogo).
- `GET /api/v1/relazioni?soggetto_id=&entity_type=&entity_id=&tipo=&solo_correnti=` → unione delle relazioni CORE e dei provider, con `tipo`, `tipo_nome`, `modulo`, `fonte`, oggetto, `descrizione`, periodo, scadenza.
- `POST`, `PUT /{id}`, `DELETE /{id}`, `POST /{id}/rinnova` → solo relazioni CORE.
- Permessi: lettura `soggetto.view`; scrittura `soggetto.edit`, più il permesso del modulo proprietario dell'oggetto quando c'è (es. `condominio.edit` per l'amministratore).

### 5. Ruoli in azienda nel modello generale

- Un solo tipo `ruolo_azienda` (CORE, oggetto = persona giuridica, soggetto = persona fisica); il "ruolo" (Amministratore delegato, Segretaria…) è il **sottotipo**, preso dalla lista modificabile `anag_ruoli_azienda_tipi` che resta com'è (con override e merge).
- Le route `/anagrafica/ruoli-azienda` restano come facciata sul `RelazioneService` (stessa forma di risposta), così l'interfaccia esistente continua a funzionare.
- Migrazione: le righe di `anag_ruoli_azienda` (0 in collaudo) diventano relazioni CORE; la tabella resta, in sola lettura.

### 6. Anagrafiche: filtro e colonna ruoli

`GET /anagrafica/soggetti-v2/` accetta `ruolo=<codice>` (filtra i soggetti con almeno una relazione corrente di quel tipo, da qualsiasi fonte) e restituisce per ogni soggetto `ruoli: [{codice, nome, modulo, n}]` calcolati dalle relazioni, al posto degli attuali `ruoli_assegnati` vuoti.

### 7. Interfaccia

- **Componente riusabile `SoggettiTable`** (modulo `anagrafica_italiana`, esportato): l'attuale elenco Anagrafiche diventa questo componente. Props: `ruolo` (prefiltro), `title`, `extraColumns`, `rowActions` e handler, `onAdd`, `emptyMessage`. Mantiene ricerca, "Solo attivi", colonne attivabili, link alla pagina dell'anagrafica.
- **Anagrafiche**: colonna "Ruoli" (badge) e filtro per ruolo.
- **Proprietari** (`/immobili/proprietari` o la rotta attuale): `SoggettiTable ruolo="proprietario"` + colonna "Immobili" (descrizioni delle relazioni) + note. Azioni: apri anagrafica, modifica note, "Togli dai proprietari" (elimina il record `immo_proprietari` e i suoi diritti, con conferma; l'anagrafica non si cancella mai). "Nuovo proprietario" resta il form attuale.
- **Conduttori**: stesso schema con colonna "Unità occupate".
- **Pagina dell'anagrafica**: sezione "Relazioni" con tutti i ruoli della persona (tipo, oggetto con link, periodo, scadenza).
- **Condominio**: sezione "Amministratore" per collegare un'anagrafica (data inizio, scadenza calcolata e modificabile solo se il tipo lo consente, rinnovo, chiusura). I vecchi campi testo restano visibili come "dati precedenti" se valorizzati e non c'è un amministratore collegato.

## Scelte prese in fase di progetto (dopo la rilettura)

1. **Scadenza del core** di una relazione: `modulo` = modulo del tipo, `entity_type`/`entity_id` = l'**oggetto** (es. il condominio), titolo "<tipo> — <soggetto>" (es. "Mandato amministratore — Rossi Mario"), descrizione con l'id della relazione; ritrovata tramite `core_relazioni.scadenza_id`. Senza oggetto: `entity_type = SOGGETTO_ANAGRAFICO`, `entity_id` = soggetto.
2. **Duplicati**: errore se esiste già una relazione aperta (`data_fine` nulla) con stesso soggetto, tipo, oggetto e sottotipo. Il tipo può dichiarare `unico_per_oggetto: true` (vero per `amministratore_condominio`): una sola relazione aperta per oggetto; per cambiare amministratore si chiude il precedente.
3. **"Corrente"**: relazione senza `data_fine` o con `data_fine` ≥ oggi. Provider: un proprietario/conduttore registrato senza diritti/assegnazioni è corrente (senza oggetto); diritti con `data_fine` passata e assegnazioni chiuse non lo sono. Il prefiltro delle pagine Proprietari/Conduttori mostra i correnti; un interruttore "Anche cessati" mostra tutti. Il conteggio `n` in `ruoli` conta le relazioni correnti.
4. **Dati esistenti**: `public.core_soggetti_ruoli` e `anag_ruoli_azienda` hanno 0 righe in tutti i tenant di collaudo (verificato 2026-11-10); la migrazione dei ruoli in azienda copia comunque le eventuali righe. `register_roles` continua a scrivere nel catalogo con `fonte = CORE` e `entity_types = null` (ruoli PEC): nessuno ne scrive relazioni in questo giro.
5. **Ruoli in azienda**: il servizio verifica che l'oggetto sia una persona giuridica e il soggetto una persona fisica diversa. Il `sottotipo` è l'**id** di `anag_ruoli_azienda_tipi` come stringa; il testo libero storico (`ruolo` quando manca il tipo) va in `dati.ruolo`. Il merge dei tipi aggiorna anche il `sottotipo` delle relazioni. La facciata restituisce gli stessi campi di `RuoloAziendaResponse`.
6. **Permessi sulle descrizioni**: ogni tipo dichiara `permesso_oggetto` (es. `immobile.view`); se l'utente non lo ha, la relazione appare con tipo e periodo ma senza `descrizione` né link all'oggetto.
7. **Provider**: restituiscono una `select` SQLAlchemy componibile con colonne fisse; `ruolo=` in soggetti-v2 è un filtro `soggetto_id IN (subquery)` lato SQL, i `ruoli` della pagina si calcolano con una query per provider sui soli id della pagina.
8. **Completezza della sync**: il catalogo è in `public` e vale per tutti i tenant; la disattivazione dei tipi non dichiarati avviene solo se sono stati letti i manifest di tutti i moduli registrati (come per le tipologie documentali). I tipi di un modulo non installato in un tenant non compaiono in `GET /relazioni/tipi` di quel tenant (filtro sui moduli attivi del tenant) e i suoi provider non restituiscono nulla.

## Fuori ambito

- Eliminare `immo_proprietari`/`immo_conduttori`/`affittuari`/`tecnici` o i loro campi DEPRECATED.
- Eliminare `anag_ruoli_azienda` o il vecchio elenco `ruoli_disponibili` dei moduli in `modules_api`.
- Colonne calcolate oltre alla descrizione (numero unità, quote totali).
- Collegare il tecnico agli oggetti (es. tecnico dell'APE).
- Migrare i testi liberi dell'amministratore in anagrafiche.

## Rischi e verifiche

- Migrazioni tenant su `core_ruoli_disponibili` e `core_soggetti_ruoli` (colonne nullable, vincolo unico cambiato) provate sulla replica e con backup.
- Test: sync del catalogo (creazione, aggiornamento, disattivazione dei doppioni, completezza); scadenza calcolata/manuale/assente; chiusura/eliminazione/rinnovo con la scadenza del core; provider con modulo assente nel tenant; filtro `ruolo` e `ruoli` in soggetti-v2; facciata ruoli-azienda; permessi.
- Revisione UX di elenchi, pagina anagrafica e sezione amministratore.

## Percorso

Spec → piano → sviluppo in sessione (fasi: A catalogo e relazioni core; B provider, API e anagrafiche; C ruoli in azienda; D interfaccia; E amministratore condominio) → revisione UX → revisione finale con Sonnet → verifica-test → rilascio.
