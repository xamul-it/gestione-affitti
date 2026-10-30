# Import unità immobiliari da visura catastale — Design

Data: 2026-10-30
Stato: bozza, in attesa di approvazione

## Perché

L'utente deve caricare nel sistema circa 10 immobili con i relativi proprietari. Tutti i dati sono già disponibili nei PDF delle visure catastali scaricate dall'Agenzia delle Entrate. Ricopiarli a mano è lento e porta a errori (foglio, particella, sub, rendita, codici fiscali, quote). L'obiettivo è che una visura caricata produca, dopo una revisione, unità immobiliari, anagrafiche e diritti già compilati, e che il PDF resti consultabile da ogni immobile come documento "Visura catastale".

## Formati supportati

I campioni si trovano in `docs/visure/`. Sono PDF con testo nativo, quindi niente OCR: `pdftotext -layout` li estrae in modo pulito.

| Formato | Esempio | Supportato |
|---|---|---|
| Visura attuale **sintetica** per soggetto | `docs/visure/Visura sintetica.pdf` | Sì |
| Visura attuale **analitica** per soggetto | `docs/visure/Visura analitica.pdf` | Sì |
| Riepilogo calcolo IMU/TASI | `docs/visure/riepilogo-immobili.pdf` | **No** (deciso dall'utente: per ora fuori) |

Caratteristiche da tenere presenti:
- Una visura è **per soggetto** e contiene **più immobili**: l'analitica di esempio ne ha 9. L'import ragiona quindi "una visura → N unità + i loro intestati".
- **Sintetica**: gli immobili sono raggruppati in blocchi numerati ("1. Immobili siti nel Comune di BOLOGNA (Codice A944) Catasto dei Fabbricati"). Ogni blocco ha una tabella (Sez. Urbana, Foglio, Numero, Sub, Zona cens., Micro zona, Categoria, Classe, Consistenza, Superficie catastale, Rendita, Indirizzo con piano, Dati derivanti da) seguita da "Intestazione degli immobili indicati al n.X" (nominativo, luogo e data di nascita, CF, "Diritti e oneri reali", per esempio `(2) Nuda proprieta' 1/1`, `(8) Usufrutto 1/1`, `(7) Uso 1/1 in regime di separazione dei beni`, `(1) Proprieta' 1/1`).
- **Analitica**: un blocco per immobile ("Immobile di catasto fabbricati - n.X") con Dati identificativi (Comune con codice catastale e provincia, Foglio, Particella, Subalterno), Indirizzo con piano, Dati di classamento (Rendita, Zona censuaria, Categoria, Classe, Consistenza), Dati di superficie. Poi "Intestazione attuale degli immobili dal n. A al n. B", con il diritto nella forma `Diritto di: Usufrutto per 1/1`. Il layout è a due colonne: la colonna destra ("Causali di aggiornamento ed annotazioni") va ignorata o separata.
- Gli intestati possono essere **enti senza CF** (es. "DEMANIO DELLO STATO - RAMO FERROVIA").
- Nella sintetica il CF degli intestati può avere un `*` finale, che va rimosso.
- Categorie con suffisso nota nell'analitica (`A/3a)`, `C/2c)`) vanno normalizzate (`A/3`, `C/2`).
- Le visure possono contenere anche il **Catasto Terreni**. Gli esempi contengono solo fabbricati.

## Obiettivi

1. Nella lista Unità Immobiliari, un'azione **"Carica da documento"**: l'utente sceglie il tipo di documento (per ora solo "Visura catastale"; il selettore esiste per poter aggiungere altri tipi in futuro) e carica il PDF.
2. Il sistema riconosce automaticamente se la visura è sintetica o analitica e ne estrae unità e intestati.
3. Viene mostrata una **proposta di modifiche** divisa in sezioni, ciascuna riga con una casella di selezione (selezionata per default) e i campi principali modificabili:
   - **Anagrafiche da aggiungere**: intestati non presenti in anagrafica.
   - **Immobili da aggiungere**: unità non presenti.
   - **Immobili da aggiornare**: unità già presenti, con il confronto valore attuale → valore da visura solo per i campi che cambiano.
   - **Diritti da aggiungere**, per ogni unità: soggetto, tipo diritto, quota.
   - Gli elementi già presenti e identici vengono mostrati come "già presenti, nessuna modifica" (compressi), così l'utente capisce che sono stati riconosciuti.
4. Alla conferma, tutto viene applicato in **una sola transazione**: se qualcosa fallisce, non viene salvato nulla.
5. Il PDF viene salvato come documento di tipo **Visura catastale** e collegato a **ogni unità creata o aggiornata** dall'import, così compare nella sezione documenti di ciascun immobile.

## Non obiettivi

- Riepilogo IMU/TASI e calcolo IMU.
- Import di **terreni** (catasto terreni) **in questa fase**. Se la visura ne contiene, vengono mostrati in un avviso ("N terreni trovati, non importati"). L'utente ha però confermato che **i terreni verranno dopo**, quindi il design deve preparare il terreno:
  - il parser e il modello `VisuraParsed` distinguono già "fabbricati" e "terreni" in liste separate, e l'intestazione è collegata a un immobile generico (fabbricato o terreno);
  - il servizio di import e la proposta sono organizzati per "tipo di bene", così i terreni (`Terreno`, che ha già foglio, particella, qualità, classe, redditi) si aggiungono come nuova sezione senza riscrivere il flusso;
  - per ora non serve estrarre i campi specifici dei terreni (non ci sono campioni): basta riconoscerli e contarli.
- Rimozione o chiusura automatica di diritti presenti a sistema ma assenti nella visura (vedi "Aggiornamenti").
- Scansioni o PDF senza testo (OCR).
- Import di più PDF in un'unica operazione: si carica una visura alla volta.
- Creazione automatica dei condomini.

## Anti-obiettivi (sarebbe un fallimento anche se "funziona")

- Scrivere dati senza che l'utente li abbia visti e confermati.
- Creare duplicati di persone (stesso CF) o di unità (stesso comune/foglio/particella/sub).
- Sovrascrivere in silenzio dati inseriti a mano che la visura non contiene (es. classe energetica, note, descrizione, condominio, tipo scelto dall'utente).
- Salvare a metà: alcune unità sì e altre no.

## Regole di riconoscimento (matching)

- **Soggetto**: per codice fiscale (normalizzato maiuscolo, senza `*`). Senza CF (enti), si cerca per `ragione_sociale` uguale ignorando maiuscole e minuscole tra i `PERSONA_GIURIDICA`. Se non c'è corrispondenza, il soggetto finisce tra quelli da aggiungere.
- **Unità**: per comune + foglio + particella + subalterno (stringhe normalizzate, senza zeri iniziali). Il comune si confronta tramite il codice catastale (es. `A944`) risolto su `comuni_italia` e poi sul nome città, perché `UnitaImmobiliare` oggi salva `citta`/`provincia` e non il codice catastale. Se c'è la sezione urbana, fa parte della chiave quando valorizzata.
- **Proprietario**: le unità si collegano ai soggetti tramite `Proprietario` (che punta a `soggetto_id`) e `DirittoImmobile`. Per ogni soggetto si riusa il `Proprietario` esistente collegato a quel `soggetto_id`, altrimenti se ne crea uno.
- **Diritto**: lo si considera già presente se esiste un `DirittoImmobile` con la stessa unità, lo stesso proprietario e lo stesso tipo diritto. Se la quota è diversa, il diritto non viene modificato e compare come avviso "quota diversa: sistema X%, visura Y%". *(Scelta mia.)*
- **Soggetto già esistente con dati diversi**: non si sovrascrive niente. I campi vuoti a sistema (nome, cognome, data e luogo di nascita) vengono proposti come aggiornamento "completa dati", deselezionabile. *(Scelta mia.)*
- **Persona fisica o giuridica**: un CF di 16 caratteri alfanumerici indica una persona fisica. Un CF di 11 cifre indica una persona giuridica: va in `codice_fiscale` e anche in `partita_iva`, mentre il nominativo va in `ragione_sociale`. Un intestato senza CF è una persona giuridica. *(Scelta mia.)*
- **Comune non trovato** in `comuni_italia`: l'unità viene proposta lo stesso, con `citta` presa dalla visura, `provincia` presa dalla visura (se presente) e un avviso. *(Scelta mia.)*

## Mappatura dei dati

**Unità (`UnitaImmobiliare`)**
| Visura | Campo |
|---|---|
| Foglio / Particella (Numero) / Subalterno | `foglio`, `particella`, `subalterno` |
| Comune (nome) e provincia | `citta`, `provincia` (provincia da `comuni_italia` se manca, come nella sintetica) |
| CAP | da `comuni_italia` se disponibile (la visura non lo riporta) |
| Indirizzo ("VIA EMILIA PONENTE n. 356") | `indirizzo` |
| Piano ("Piano 2-S1") | `piano` |
| Categoria | `categoria_catastale_id` (lookup su `immo_categorie_catastali`) |
| Rendita | `rendita_catastale` |
| Superficie: "Totale escluse aree scoperte", altrimenti "Totale" | `superficie_mq` |
| Consistenza in vani | `locali`: solo se il valore è intero, altrimenti si lascia vuoto e si annota |
| Classe, consistenza, zona censuaria, sezione urbana | in `note`, in forma leggibile (non esistono colonne dedicate). *(Scelta mia: niente migrazione per questi campi.)* |
| `tipo` (Appartamento, Box…) | proposto dalla categoria usando `immo_tipo_immobile_categoria_map` / regole di default (A/x → Appartamento, C/6 → Box, C/2 → Magazzino/Cantina…), modificabile in revisione. Se non si riesce a dedurlo, il campo resta vuoto ed è obbligatorio: "Importa" resta disabilitato finché l'utente non lo compila (`tipo` è NOT NULL). *(Scelta mia.)* |
| `codice` | generato con `CodiceGeneratorService` come avviene nella creazione manuale |

**Soggetto (`SoggettoAnagrafico`)**: persona fisica con cognome, nome, CF, data e luogo di nascita. Nella sintetica il cognome è in maiuscolo e il nome in maiuscolo/minuscolo ("ZANDERIGHI Luigi Matteo Massimiliano"). Si usa questo per separarli e il CF come verifica. Gli enti senza CF diventano `PERSONA_GIURIDICA` con `ragione_sociale`.

**Diritto (`DirittoImmobile`)**: la quota "a/b" diventa `quota_percentuale` = a/b × 100 (arrotondata a 2 decimali).
| Visura | `TipoDiritto` |
|---|---|
| Proprieta' 1/1 | `PROPRIETARIO` |
| Proprieta' con quota < 1 | `COMPROPRIETARIO` |
| Nuda proprieta' | `NUDA_PROPRIETA` |
| Usufrutto | `USUFRUTTUARIO` |
| Uso, Abitazione, Superficie, Enfiteusi, altri | si **estende l'enum** con `USO`, `ABITAZIONE`, `SUPERFICIE`, `ENFITEUSI`, con la migrazione del tipo enum PG nei tenant. Quello che resta non riconosciuto va in `ALTRO` con il testo originale in `note`. *(Scelta mia.)* |

Si importano **tutti** gli intestati con il loro diritto reale esatto, anche quando non sono proprietari pieni (es. il Demanio con proprietà 1/1 e l'utente con uso 1/1 sulla stessa unità; l'usufruttuario e il nudo proprietario). Nessun intestato viene scartato. Le regole su chi paga cosa (IMU, spese) verranno in seguito, partendo dal tipo di diritto. *(Deciso dall'utente.)*

Il testo originale del diritto (es. "Uso 1/1 in regime di separazione dei beni") viene sempre copiato in `note` del diritto.

## Aggiornamenti di unità esistenti

- Si aggiornano **solo i campi catastali** presi dalla visura: categoria, rendita, superficie, indirizzo, piano e la parte "dati catastali" delle note. Non si toccano `tipo`, `condominio_id`, `classe_energetica`, `descrizione`, `codice` né le parti delle note scritte dall'utente. *(Scelta mia: le note avranno un blocco delimitato "Dati catastali (da visura del gg/mm/aaaa)" che viene sostituito.)*
- Nella proposta ogni campo che cambia mostra attuale → nuovo e può essere deselezionato singolarmente.
- I diritti presenti a sistema ma non nella visura **non vengono rimossi**: compaiono come avviso ("diritto presente a sistema ma non in visura") perché l'utente decida a mano.

## Documento allegato

- Si aggiunge il tipo documento `VISURA_CATASTALE` al seed di `core_tipi_documento` (oggi esiste solo nell'enum legacy `TipoDocumentoEnum`). Categoria: `immobiliare` o equivalente, `richiede_scadenza = False`.
- `Documento` ha un solo `entity_type/entity_id`. Per collegare la visura a più unità senza modificare lo schema core si crea **un `Documento` per ogni unità importata** (`entity_type=IMMOBILE`), ciascuno con la propria copia del file salvata con `file_storage`, `descrizione` = "Visura catastale <sintetica|analitica> n. <numero visura> del <data>", e i dati estratti in `metadata_parsato`. *(Scelta mia: file piccoli, pochi immobili, nessun impatto su un modello core condiviso. Se in futuro servisse un documento "uno a molti", si introdurrà una tabella di collegamento.)*
- Niente duplicati: se un'unità ha già un documento Visura catastale con lo stesso numero di visura (es. `T234664/2025`, salvato in `metadata_parsato`), non se ne crea un altro. Il documento si allega anche alle unità con stato "nessuna modifica", purché non abbiano già quella visura. *(Scelta mia.)*
- Le anagrafiche create non ricevono il documento. L'utente non l'ha chiesto.

## Architettura

- **Backend, modulo `immobili`** (possiede unità, proprietari e diritti, e dipende già da `anagrafica_italiana`):
  - `services/visura_catastale_parser.py`: funzione pura `bytes PDF → VisuraParsed` (tipo visura, numero, data, soggetto richiesto, lista unità, lista intestati per unità, terreni ignorati, warning). Estrazione testo con `pdftotext -layout` (poppler è già presente per `pdf2image`) oppure con una libreria Python. La scelta è lasciata al builder, purché funzioni nel venv Python 3.13.
  - `services/visura_import_service.py`: confronta `VisuraParsed` con il DB del tenant e produce la proposta (`create`/`update`/`unchanged`, ogni elemento con un id locale); poi applica una proposta confermata in una transazione.
  - Route (es. `POST /immobili/import-visura/preview` multipart → proposta + `upload_token`; `POST /immobili/import-visura/apply` con token + selezioni/modifiche). Il PDF resta in un'area temporanea del tenant tra preview e apply. Il parsing è **sincrono**: si tratta di pochi millisecondi di testo, non serve il flusso asincrono `DocumentJob` usato per l'MRZ.
  - Permessi: gli stessi richiesti per creare unità e soggetti.
- **Frontend, modulo `immobili`**: pulsante "Carica da documento" in `UnitaImmobiliariList`, una modale o pagina con il passo 1 (tipo documento + upload) e il passo 2 (proposta a sezioni con caselle e campi modificabili, riepilogo dei conteggi, pulsante "Importa"), poi l'esito con i link alle unità create o aggiornate. Va usato lo stile dei componenti esistenti (FormModal/DataTable, vedi `docs/architecture/CORE_COMPONENTS_ARCHITECTURE.md`).

## Test

- Test unitari del parser sui tre PDF di `docs/visure/` (copiati in `backend/tests/fixtures/`): la sintetica deve dare 9 unità tra 3 blocchi con gli intestati corretti, compreso il Demanio senza CF; l'analitica deve dare 9 unità con superfici e piani. Il riepilogo IMU deve produrre un errore chiaro "formato non supportato".
- Test del servizio di import: soggetto esistente riconosciuto per CF; unità esistente → update solo dei campi che cambiano; idempotenza (un secondo import della stessa visura → nessuna modifica proposta, eccetto il documento); rollback in caso di errore.
- I PDF reali si usano come fixture così come sono: l'utente ha confermato che non ci sono problemi di privacy.

## Lasciato al builder

Libreria di estrazione testo, nomi esatti di route e schemi, layout preciso della schermata di revisione, gestione del file temporaneo tra preview e apply (TTL, pulizia).
