# Caricamento unico dei documenti degli immobili — design

Data: 2026-11-10 · Stato: bozza da approvare (domande del revisore risolte)

## Perché

Oggi ogni documento di un immobile si carica dalla scheda dell'unità scegliendo
a mano tipo e immobile, e i dati (classe APE, EPgl…) si ricopiano a mano. Solo
la visura catastale viene letta in automatico. L'utente vuole **un unico punto
dove trascinare i documenti**: il sistema capisce il tipo e l'immobile, legge
i dati, chiede solo quello che non riesce a capire.

Principio di dominio (dell'utente): **i dati dell'immobile sono l'aggregazione
dei campi dei suoi documenti.** La classe energetica è dell'APE; la scheda
dell'immobile la mostra ricavandola dall'APE in vigore.

## Obiettivi

1. Un punto di caricamento nel modulo immobili (pagina Documenti immobili,
   `/immobili/documenti`) che accetta uno o più file trascinati.
2. Per ogni file:
   - **riconosce il tipo** dal testo; se non lo riconosce, chiede il tipo
     (elenco dei tipi documento del modulo immobili);
   - **scarta** i documenti riconosciuti di altri moduli con un messaggio che
     dice dove caricarli (es. ricevuta RLI → "caricala dal contratto, modulo
     Affitti");
   - **abbina l'unità immobiliare** dai dati letti; se non la trova o ne trova
     più d'una, chiede di sceglierla (proponendo le più simili);
   - **legge i dati** del tipo (per l'APE: classe, EPgl,nren, codice
     identificativo, data di emissione/validità);
   - **segnala le differenze** tra i dati letti e quelli dell'unità abbinata
     e **propone di aggiornare l'unità** (campo per campo, selezionabile);
   - mostra un **riepilogo da confermare**; solo alla conferma allega il
     documento all'unità (con i suoi dati) e applica gli aggiornamenti scelti.
3. La visura catastale riconosciuta apre l'import visure esistente (che può
   creare unità e intestatari): nessuna logica duplicata.
4. I PDF scansionati (senza testo) passano dall'OCR del servizio esterno;
   il loro riepilogo arriva più tardi, con una notifica.
5. Classe energetica: una sola fonte, l'APE. Il campo `classe_energetica`
   dell'unità smette di essere modificabile a mano e viene mostrato ricavato
   dall'APE in vigore.

## Non obiettivi

- Documenti delle anagrafiche e dei contratti (RLI, contratti): restano nei
  loro moduli; qui si riconoscono solo per scartarli.
- Lettura di atti notarili in prosa (atto di provenienza): solo tipo scelto a
  mano + abbinamento manuale, nessuna estrazione.
- Estrazione con modelli linguistici.
- Creazione di nuove unità da documenti diversi dalla visura.

## Anti-obiettivi (sarebbe un fallimento anche se funziona)

- Un documento allegato all'unità sbagliata senza che l'utente l'abbia visto:
  l'abbinamento si conferma **sempre**, anche se automatico e univoco.
- Dati dell'unità sovrascritti senza conferma campo per campo.
- Documenti personali o immobiliari inviati a servizi esterni non nostri: l'OCR
  gira solo sul servizio locale.

## Campioni (docs/visure, non versionati)

Tutti relativi alla stessa unità (Bologna, A944, foglio 99, particella 666,
sub 10), utili per i test end-to-end:

| File | Tipo | Testo | Note |
|---|---|---|---|
| `Certificato_57508_1876709.pdf` | APE (formato Emilia-Romagna) | sì | Cod. comune/Sezione/Foglio/Particella/Subalterno in tabella; classe C; EPgl,nren 111,24; "VALIDO FINO AL 23/02/2031" |
| `Visura 2b.pdf` | Visura per immobile | sì | gestita dall'import esistente |
| `Planimetria 2b.pdf` | Planimetria catastale | **no** (immagine JPEG) | serve OCR |
| `ZANRIZ24_0_RLI12_dcm.rel.pdf` | Ricevuta RLI12 | sì | da scartare (modulo affitti) |

I test automatici non devono dipendere da `docs/visure` (non versionato, dati
reali): usano testi di fixture anonimizzati ricavati da questi campioni.

## Come funziona

### Lettori per tipo (nel modulo immobili)

Un lettore per tipo di documento, dichiarato dal modulo, con:

- `riconosce(testo) -> bool`: frasi tipiche del tipo (APE: "ATTESTATO DI
  PRESTAZIONE ENERGETICA" / "CERTIFICAZIONE ENERGETICA" + "EP gl,nren";
  planimetria: intestazione catastale della planimetria; visura: le stesse
  firme già usate da `parse_visura`);
- `estrai(testo) -> dati`: identificativi per l'abbinamento (comune o codice
  comune, sezione, foglio, particella, subalterno, indirizzo, piano) e dati del
  documento (per l'APE: classe, ep_gl_nren, codice_identificativo,
  data_emissione o validità).

Lettori "di scarto" per i documenti noti di altri moduli (prima: RLI12),
che restituiscono solo il messaggio con il modulo giusto.

Lettura per parole chiave/espressioni regolari sul testo, come i parser delle
visure esistenti (`services/visura/`).

### Estrazione del testo

- PDF con testo: `pdftotext -layout` nel backend, risposta immediata.
- PDF senza testo / immagini: servizio di parsing esterno (stesso impianto del
  MRZ: `DocumentParsingService`, lavoro asincrono, richiamata con token,
  notifica), con una nuova modalità **OCR testo + ricerca campi** (decisione
  dell'utente: il servizio riceve cosa cercare e restituisce i valori trovati).
  Va aggiunta nel servizio in `~/Progetti/mrz` (fuori da questo repository,
  la costruisce Claude in questo stesso lavoro).

### Contratto della modalità OCR testo

Richiesta (oltre al file e alla `callback_url`):

```json
{"modalita": "testo",
 "tipi": [
   {"codice": "APE",
    "riconosci": ["ATTESTATO DI PRESTAZIONE ENERGETICA|CERTIFICAZIONE\\s+ENERGETICA"],
    "campi": {"foglio": "Foglio\\s*[:.]?\\s*(?P<v>\\d+)", "classe": "..."}}
 ]}
```

- `riconosci`: espressioni che devono comparire tutte perché il testo sia di
  quel tipo; `campi`: un'espressione per campo, il valore è il gruppo `v`.
- Il backend manda le specifiche di tutti i tipi del modulo (alla lettura il
  tipo non è ancora noto).

Risposta (nella richiamata):

```json
{"testo": "...", "pagine": 1,
 "tipi": [{"codice": "APE", "riconosciuto": true,
           "campi": {"foglio": {"valore": "99", "pagina": 1}}}]}
```

Le specifiche (etichette ed espressioni) sono dichiarate **una sola volta**
nei lettori del modulo immobili e usate identiche sia dal backend sui PDF con
testo (stesso formato, stesso semplice motore: espressione Python `re`,
gruppo `v`, prima corrispondenza) sia dal servizio sulle scansioni.
I valori restituiti dal servizio passano comunque dalla normalizzazione e
dall'abbinamento del backend.

### Abbinamento dell'unità

Stessa regola dell'import visure: comune + foglio + particella + subalterno,
zeri iniziali ignorati. Il comune può arrivare come codice catastale (A944) o
come nome: si normalizza tramite `comuni_italia`. Esiti:

- una sola unità → proposta (da confermare);
- nessuna → l'utente sceglie l'unità; si propongono quelle con stesso comune +
  foglio + particella, poi stesso indirizzo;
- più di una → l'utente sceglie tra quelle.

### Differenze e aggiornamento dell'unità

Per i campi che il documento conosce e l'unità ha (indirizzo, piano, interno,
dati catastali), il riepilogo mostra attuale → letto, ciascuno selezionabile,
come `CampoModifica` dell'import visure. Alla conferma si applicano solo i
campi scelti. La classe energetica non è un campo dell'unità da aggiornare:
viene dall'APE stesso.

### Salvataggio

Alla conferma il documento si salva con il servizio documenti esistente (tipo,
`entity_type=IMMOBILE`, `entity_id`, `data_riferimento`, `dati`). Per l'APE
(decisione dell'utente): è **in vigore l'APE con la data di emissione più
recente**, non l'ultimo caricato. Un APE più vecchio di quello in vigore si
salva come storico (sostituito) e il riepilogo lo avvisa prima della
conferma; uno più recente sostituisce quello in vigore. La scadenza segue
dalle regole del tipo. Questa regola esiste già nel servizio documenti per
tutti i tipi sostitutivi (spec 2026-11-09, §3): va solo verificata con un
test sull'APE e resa visibile nel riepilogo. Il file letto viene
riletto lato server alla conferma (come l'import visure: i valori vengono dal
PDF, il client contribuisce solo scelte e campi modificati).

### Interfaccia

Nella pagina Documenti immobili: un'area di trascinamento (più file). Ogni
file diventa una riga con stato: "letto" / "in lettura (OCR)" / "da
completare: scegli tipo" / "da completare: scegli immobile" / "scartato: …".
Aprendo la riga: tipo, immobile, dati letti, differenze con l'unità; pulsante
Conferma. La visura apre il riepilogo dell'import visure già esistente.

## Vincoli

- Tenant: tutto nello schema del tenant della richiesta; il lavoro OCR
  conserva il tenant (vedi correzione richiamata del 2026-11-10).
- Permessi: quelli dei documenti immobili esistenti (caricamento e modifica
  unità).
- Il gate per modulo vale: il punto unico è una rotta del modulo immobili.
- Nessun dato di `docs/visure` nel repository né nei test.

## Decisioni prese da Claude (da verificare)

- **Classe energetica dell'unità**: calcolata in lettura dall'APE CORRENTE
  dell'unità (nessuna colonna denormalizzata da tenere allineata). Il campo
  sparisce dal form dell'unità; la colonna `classe_energetica` resta nel DB
  ma non viene più scritta né letta. Verificato in collaudo il 2026-11-10:
  nessuna unità ha oggi una classe scritta a mano (tenant_produzione 17 unità,
  0 valorizzate), quindi nessun dato si perde e non serve migrazione.
  `routes/certificati_energetici.py` resta in sola lettura com'è.
- **Duplicati**: alla lettura si calcola l'hash del file; se un documento con
  lo stesso hash è già allegato a quell'unità, la riga dice "già presente"
  e non si salva (l'utente può forzare).
- **Planimetria da OCR**: testo rumoroso, l'abbinamento automatico può
  fallire spesso; atteso, si ricade su "scegli immobile". Nessun abbinamento
  tollerante in questa fase.
- **Permessi visura**: la visura riconosciuta apre l'import esistente con i
  suoi permessi attuali; chi non li ha vede la riga "serve il permesso di
  import visure".

## Lasciato a chi costruisce

- Struttura interna dei lettori (registro, classi o funzioni).
- Dove vive il file tra lettura e conferma (oggi l'import visure usa un
  upload temporaneo con token: riusabile).
- Dettagli dell'interfaccia nel rispetto del design system del progetto.
