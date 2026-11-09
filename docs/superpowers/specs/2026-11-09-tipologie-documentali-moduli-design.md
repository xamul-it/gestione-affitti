# Tipologie documentali dei moduli, storico e documenti degli immobili

Data: 2026-11-09 — Stato: **bozza da approvare**

## Problema

Verifica del 2026-11-09: il problema è sia strutturale sia di interfaccia.

- Le tipologie documentali hanno due fonti che non coincidono:
  - i manifest dei moduli (`document_types`), letti in memoria da `DocumentTypeRegistry`;
  - la tabella `public.core_tipi_documento`, popolata da una lista fissa nel seed di `anagrafica_italiana` (`seed_tipi_documento.py`).
  Esempio: il manifest usa `PATENTE_GUIDA`, il seed `PATENTE`. La tabella non sa quale modulo possiede un tipo. È la tabella che Configurazioni mostra.
- Il modulo `immobili` non dichiara tipologie. `VISURA_CATASTALE` la crea il seed delle anagrafiche.
- Il certificato energetico non è un documento del core: è la tabella `immo_certificati_energetici` con un suo `file_path`.
- La sezione documenti generica (`components/Documenti/DocumentiSection` e `DocumentoUpload`) usa una lista di tipi fissa nel codice (`TipoDocumentoEnum`). Ignora le tipologie, la scadenza e i lettori. È visibile solo in fondo al modale di modifica dell'unità.
- Non c'è storico:
  - i documenti si accumulano senza sapere quale è in vigore;
  - l'import visura sovrascrive i dati catastali senza conservare i valori precedenti.

La gestione documentale "buona" esiste solo nelle anagrafiche: `DocumentoUpload` con tipi da DB, scadenza, multi-file e lettore MRZ.

## Obiettivo

Ogni modulo registra le proprie tipologie. Una tipologia può avere:
- una scadenza;
- un form dedicato al caricamento, eventualmente con un lettore che interpreta il file.

Una tipologia senza form carica solo il file (più la scadenza, se prevista).

Il core offre a tutti i moduli:
- caricamento;
- consultazione;
- storico;
- scadenze.

## Decisioni

### 1. Una sola fonte: il manifest

Ogni tipologia si dichiara in `document_types` del `__manifest__.py`. Campi:

| Campo | Significato |
|---|---|
| `codice`, `nome`, `categoria`, `descrizione` | come oggi |
| `entity_types` | a quali entità si applica, es. `["IMMOBILE"]`, `["SOGGETTO_ANAGRAFICO"]` |
| `regime` | `SOSTITUTIVO`: il nuovo documento sostituisce il precedente, che va in storico. `CUMULATIVO`: i documenti si accumulano. |
| `sottotipi` | opzionale. Il regime sostitutivo vale per entità + sottotipo (es. conformità impianto elettrico / gas / termico) |
| `scadenza` | `null` = nessuna; `{"manuale": true}` = data inserita a mano; `{"mesi": 120, "da": "data_riferimento"}` = calcolata |
| `promemoria_giorni` | es. `[90, 30]` |
| `form` | opzionale, chiave del form frontend che il modulo registra (es. `"immobili.ape"`) |
| `parsing_service`, `parsing_config` | come oggi (lettore) |

Sincronizzazione all'avvio (idempotente, schema `public`):
- upsert per `codice` in `core_tipi_documento`, con le nuove colonne `modulo`, `entity_types`, `regime`, `sottotipi`, `scadenza`, `promemoria_giorni`, `form`;
- un tipo che non compare più in nessun manifest diventa `attivo = false`. Non viene mai cancellato, perché i documenti lo referenziano;
- gli override per tenant (`core_tipi_documento_overrides`) restano e vincono su nome, scadenza e attivo.

Il seed delle anagrafiche viene rimosso. Le sue tipologie passano nel manifest delle anagrafiche e `VISURA_CATASTALE` passa a immobili. I codici già usati in DB restano invariati (`PATENTE`, non `PATENTE_GUIDA`). Configurazioni mostra la colonna "Modulo".

### 2. Tipologie del modulo immobili (fabbricato)

Fonte: ricerca con Archivio Fiscale del 2026-11-09. Quelle marcate *da verificare* vengono dalla memoria dell'esperto, non dall'archivio.

| Codice | Nome | Regime | Scadenza | Form / lettore |
|---|---|---|---|---|
| `VISURA_CATASTALE` | Visura catastale | SOSTITUTIVO | no (data riferimento = data visura) | sì: import visura esistente (lettore + revisione differenze) |
| `PLANIMETRIA_CATASTALE` | Planimetria catastale | SOSTITUTIVO | no | no (data presentazione, protocollo) |
| `VARIAZIONE_CATASTALE` | Variazione catastale (DOCFA, voltura, frazionamento, fusione) | CUMULATIVO | no | no; sottotipi: DOCFA, voltura, frazionamento, fusione |
| `APE` | Attestato di prestazione energetica | SOSTITUTIVO | 10 anni dalla data di emissione | sì: classe, EPgl,nren, codice identificativo, certificatore, data emissione, "decaduto per mancati controlli impianto" con data |
| `ATTO_PROVENIENZA` | Atto di provenienza | CUMULATIVO | no | no; sottotipi: compravendita, successione, donazione |
| `CONFORMITA_IMPIANTO` | Dichiarazione di conformità impianto (DM 37/2008) | SOSTITUTIVO per sottotipo | no | no; sottotipi: elettrico, gas, termico, idrico |
| `LIBRETTO_IMPIANTO` | Libretto impianto termico / rapporto di controllo | CUMULATIVO | manuale (prossimo controllo, *da verificare* la cadenza) | no |
| `AGIBILITA` | Agibilità / abitabilità | SOSTITUTIVO | no | no |
| `TITOLO_EDILIZIO` | Titolo edilizio (PdC, SCIA, CILA, condono) | CUMULATIVO | no | no |
| `POLIZZA_FABBRICATO` | Polizza assicurativa fabbricato | SOSTITUTIVO | manuale | no |
| `ALTRO_IMMOBILE` | Altro documento | CUMULATIVO | no | no |

Regolamento e tabelle millesimali appartengono al condominio e non entrano in questa fase.

### 3. Storico dei documenti

Nuove colonne in `core_documenti`:
- `data_riferimento` (Date): la data del documento, diversa dalla data di caricamento;
- `stato` (`CORRENTE` / `SOSTITUITO`);
- `sostituito_da_id`;
- `sottotipo`;
- `dati` (JSON): i dati confermati dall'utente nel form. `metadata_parsato` resta per l'output grezzo del lettore.

Regole per le tipologie SOSTITUTIVO, per entità + tipo (+ sottotipo):
- se il nuovo documento ha `data_riferimento` maggiore o uguale a quella del corrente, diventa CORRENTE e il precedente diventa SOSTITUITO;
- se è più vecchio (caricamento di un documento storico), entra direttamente come SOSTITUITO e non tocca il corrente;
- l'eliminazione del corrente ripromuove il più recente fra i sostituiti.

Le tipologie CUMULATIVO sono sempre CORRENTE.

Nessun file viene mai sovrascritto.

### 4. Registro delle variazioni catastali

Nuova tabella tenant `immo_variazioni_catastali`:
- `unita_immobiliare_id`, `documento_id` (nullable), `origine` (`VISURA` / `MANUALE`);
- `campo`, `valore_precedente`, `valore_nuovo`;
- `data_riferimento`, `created_at`, `utente_id`.

Viene scritta:
- dall'apply dell'import visura, per ogni campo modificato, collegandola alla visura;
- dalla modifica manuale dei campi catastali (categoria, classe, consistenza, superficie, rendita, identificativi, indirizzo, piano).

Lo storico è consultabile nella scheda immobile.

### 5. Caricamento unico del core

- Frontend: il `DocumentoUpload` delle anagrafiche diventa il componente del core `core/components/Documenti/DocumentoUpload`.
  - Mostra le tipologie applicabili all'entità (`entity_types`), lette dall'API, non da una lista fissa.
  - Supporta drag & drop multiplo e la scadenza (calcolata o manuale).
  - Se la tipologia ha un `form`, apre il form registrato dal modulo nel `manifest.js` (`documentForms: { 'immobili.ape': () => import(...) }`).
  - Visura: il form registrato è l'attuale `ImportVisuraModal`.
- Backend: `POST /api/v1/documenti/upload` accetta `tipo_documento_id`, `data_riferimento`, `sottotipo`, `data_scadenza`, `dati`, più file. Applica le regole di storico e scadenza. `GET /api/v1/documenti/tipi?entity_type=` restituisce le tipologie applicabili con gli override del tenant.
- `TipoDocumentoEnum` e la colonna `tipo_documento` restano solo come compatibilità di lettura: per i documenti esistenti la migrazione popola `tipo_documento_id` dove manca. Le route documenti delle anagrafiche restano invariate in questa fase. Il backend dei due stack si unifica in una fase successiva.

### 6. APE: da tabella a documento

Migrazione dati (tenant), nessuna cancellazione:
- ogni riga di `immo_certificati_energetici` diventa un `core_documenti` di tipo `APE`:
  - `dati` = classe, indice, protocollo, `tecnico_id`;
  - `data_riferimento` = emissione;
  - `data_scadenza` invariata;
- se `file_path` esiste, il file diventa un `core_documenti_files`;
- le regole di storico si applicano per unità.

La tabella vecchia resta in sola lettura. La sua eliminazione è una decisione successiva da chiedere all'utente. La lista "Certificati energetici" e il widget scadenze leggono dai documenti APE.

Migrazione verificata prima sulla replica di `tenant_produzione`, con conteggio righe prima e dopo.

### 7. Scadenze

Un documento CORRENTE con `data_scadenza` crea una `Scadenza` nel core (`ScadenzaService`):
- legata all'entità e al documento;
- con i promemoria della tipologia.

Quando il documento viene sostituito o eliminato, la scadenza viene chiusa. Per l'APE con "decaduto" valorizzato, la scadenza effettiva è la data di decadenza.

### 8. Consultazione

- **Scheda immobile** `/immobili/:id`, nuova. Il modale di modifica resta. Sezioni:
  - **Dati**: riepilogo in sola lettura;
  - **Documenti**: per tipologia il corrente con anteprima PDF/immagine, il link "storico (n)" e l'upload;
  - **Variazioni catastali**.
  La lista immobili apre la scheda.
- **Pagina Documenti del modulo immobili** `/immobili/documenti`: tutti i documenti degli immobili, filtrabili per tipologia, immobile, stato (correnti / anche sostituiti) e scadenza.
- In fondo al modale di modifica la vecchia `DocumentiSection` viene sostituita dal link alla scheda.

## Fuori ambito

Queste parti restano per fasi successive:
- terreni: tipologie visura terreni, CDU, estratto di mappa, con un nuovo `EntityType.TERRENO`;
- controllo "APE valido alla stipula" nel modulo `affitti_lungo`;
- flag "non applicabile" per tipologia ed entità (per evitare falsi allarmi di documenti mancanti);
- unificazione del backend documenti delle anagrafiche;
- eliminazione di `immo_certificati_energetici` e di `TipoDocumentoEnum`.

## Rischi e verifiche

- Migrazioni alembic in ordine:
  1. `core_tipi_documento` (public);
  2. `core_documenti` (tenant, colonne nullable);
  3. `immo_variazioni_catastali`;
  4. migrazione dati APE.
  Tutte vengono provate sulla replica di produzione.
- Test:
  - sincronizzazione manifest → tabella (aggiunta, disattivazione, override);
  - regole SOSTITUTIVO, compreso il caricamento di un documento storico e l'eliminazione del corrente;
  - scadenza calcolata;
  - variazioni scritte dall'import visura;
  - migrazione APE con conteggi.
- Revisione UX della scheda immobile, della pagina Documenti e dell'upload.

## Percorso

Percorso "grande": spec approvata → piano → sviluppo per fasi:
- A: backend tipologie e storico;
- B: APE;
- C: interfaccia;
- poi revisione UX → verifica-test → rilascio.
