# Modulo Immobili — documento tecnico-funzionale

Stato al 2026-11-10. Descrive **com'è il modulo oggi**: requisiti, regole di
dominio, funzioni e limiti. Per la piattaforma (tenant, permessi, documenti,
relazioni, lettura automatica) vedi `docs/piattaforma.md`. L'analisi
funzionale originale è in `backend/modules/immobili/Gestione immobiliare.md`
(gennaio 2026, in parte superata da questo documento).

Regola: chi modifica il comportamento del modulo aggiorna questo documento
nello stesso commit.

- Codice: `backend/modules/immobili/`, `frontend/src/modules/immobili/`
- Dipende da: `anagrafica_italiana`. Ne dipende: `affitti_lungo`.
- Permessi (`risorsa.azione`): `immobile`, `proprietario`, `conduttore`,
  `condominio`, `terreno`, `certificato_energetico`, `spesa_ricorrente`, con
  azioni view/create/edit/delete.

## 1. Regole di dominio (dall'utente)

- Un immobile può essere in piena proprietà o in comproprietà per quote.
- Molti immobili fanno parte di complessi, palazzine o condomini.
- **Proprietario**: chi ha un diritto reale (proprietà, quota, usufrutto…).
- **Conduttore**: chi occupa o usa l'immobile, **indipendentemente** da un
  contratto di locazione (comodato, usufrutto, proprietario che ci abita).
  Il modulo affitti gestisce solo la parte contrattuale.
- Proprietario e conduttore possono coincidere ma si registrano come ruoli
  distinti; un soggetto può avere ruoli diversi su immobili diversi.
- Spese ordinarie → conduttore; straordinarie o legate alla proprietà →
  proprietario, che resta comunque responsabile in solido.
- Utenze centralizzate (contratto del condominio) si tracciano sul
  condominio, non sull'unità.
- **I dati dell'immobile sono l'aggregazione dei campi dei suoi documenti**
  (es. la classe energetica è dell'APE in vigore).

## 2. Entità e funzioni

| Area | Cosa fa | API (`/api/v1/…`) |
|---|---|---|
| Unità immobiliari | Anagrafica dell'unità: indirizzo, piano, interno, tipo, destinazione, dati catastali (comune, sezione, foglio, particella, subalterno, categoria, classe, consistenza, superficie, rendita), condominio. Scheda immobile `/immobili/:id`. | `unita-immobiliari` |
| Terreni | Foglio, particella, qualità, classe, redditi; tipologie di terreno. | `terreni`, `tipologie-terreno` |
| Proprietari e diritti | Proprietario (legato a un soggetto anagrafico) e diritti sull'unità con tipo diritto e quota. | `proprietari`, `diritti-immobile` |
| Conduttori | Conduttore e assegnazioni all'unità con periodo. | `conduttori`, `assegnazioni-conduttore` |
| Condomini | Condominio/complesso, tabelle millesimali e millesimi per unità; amministratore come relazione. | `condomini`, `tabelle-millesimali`, `millesimi-immobile` |
| Spese ricorrenti | Spese periodiche dell'unità o del condominio. | `spese-ricorrenti` |
| Categorie catastali | Catalogo (schema `public`). | `categorie-catastali` |
| Certificati energetici | Sola lettura, ricavati dagli APE (vedi 4). | `certificati-energetici` |

## 3. Relazioni (ruoli)

Tipi dichiarati dal modulo (`relation_types`), vedi `docs/piattaforma.md` §5:

| Tipo | Oggetto | Fonte |
|---|---|---|
| `proprietario` | IMMOBILE | MODULO: da proprietari e diritti |
| `conduttore` | IMMOBILE | MODULO: da conduttori e assegnazioni |
| `amministratore_condominio` | CONDOMINIO | CORE, scadenza 12 mesi da `data_inizio` (art. 1129 c.c., rinnovo tacito con "rinnova") |

Se il modulo viene disattivato nel tenant, l'amministratore di condominio
resta salvato ma nascosto e le sue scadenze vengono annullate; alla
riattivazione tornano. Il modulo non si può disattivare mentre
`affitti_lungo` è attivo.

## 4. Documenti dell'immobile

Tipologie dichiarate nel manifest (spec
`2026-11-09-tipologie-documentali-moduli-design.md`):

| Codice | Regime | Scadenza | Form / lettura |
|---|---|---|---|
| `VISURA_CATASTALE` | sostitutivo | — | import visure (lettura automatica) |
| `PLANIMETRIA_CATASTALE` | sostitutivo | — | — |
| `VARIAZIONE_CATASTALE` | cumulativo | — | sottotipi DOCFA, voltura, frazionamento, fusione |
| `APE` | sostitutivo | 10 anni dall'emissione | form `immobili.ape`: classe, EPgl,nren, codice, tecnico, decadenza |
| `ATTO_PROVENIENZA` | cumulativo | — | sottotipi compravendita, successione, donazione |
| `CONFORMITA_IMPIANTO` | sostitutivo per sottotipo | — | elettrico, gas, termico, idrico |
| `LIBRETTO_IMPIANTO` | cumulativo | manuale | — |
| `AGIBILITA` | sostitutivo | — | — |
| `TITOLO_EDILIZIO` | cumulativo | — | — |
| `POLIZZA_FABBRICATO` | sostitutivo | manuale | — |
| `ALTRO_IMMOBILE` | cumulativo | — | — |

- Per i sostitutivi è in vigore il documento con la data di riferimento più
  recente; un documento più vecchio caricato dopo va direttamente in storico.
- APE: la vecchia tabella `immo_certificati_energetici` è stata migrata a
  documenti ed è in sola lettura. La classe energetica dell'unità è quella
  dell'APE in vigore.
- Pagina di tutti i documenti del modulo: `/immobili/documenti`, filtri per
  tipo, storico e scadenza.

### 4.1 Import visure catastali

Spec: `2026-10-30-import-visure-catastali-design.md`.

- Da "Carica da documento" (lista unità) o caricando un documento di tipo
  visura. Formati: visura per soggetto **sintetica** e **analitica**, visura
  **per immobile**; PDF con testo (niente OCR).
- Proposta di modifiche da confermare: anagrafiche da aggiungere, unità da
  aggiungere o aggiornare (campo per campo), diritti da aggiungere.
- Abbinamento: soggetto per codice fiscale (enti senza CF per ragione
  sociale); unità per comune + foglio + particella + subalterno (zeri
  iniziali ignorati); diritto per unità + proprietario + tipo.
- Alla conferma tutto in una transazione; il PDF viene riletto lato server e
  allegato a ogni unità creata o aggiornata.
- Le modifiche ai campi catastali (da visura o a mano) vanno nel registro
  `immo_variazioni_catastali`, consultabile nella scheda immobile.

Limiti noti: persona fisica senza CF salvata come ente; nomi tutti
maiuscoli; sezione urbana ignorata; terreni solo contati, non importati;
riepilogo IMU/TASI non supportato.

## 5. In progettazione

- **Caricamento unico dei documenti** (spec
  `2026-11-10-caricamento-unico-documenti-immobili-design.md`, da approvare):
  un punto dove trascinare i documenti; il sistema riconosce il tipo, abbina
  l'unità, legge i dati (APE), segnala le differenze e propone di aggiornare
  l'unità; scarta i documenti di altri moduli (es. ricevuta RLI); le
  scansioni passano dall'OCR del servizio esterno.

## 6. Limiti e attività note

- Il campo `classe_energetica` dell'unità è ancora modificabile a mano nel
  form, in doppio con l'APE: da togliere con il caricamento unico.
- Calcolo IMU/TARI: fuori ambito per ora.
