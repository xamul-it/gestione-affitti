# Beni catastali: beni, raggruppamenti e relazioni con i soggetti — design

Data: 2026-11-10 · aggiornata il 2026-11-12 (collegamenti), il 2026-11-13
(fase 2a fatta), il 2026-11-25 (fase 2b fatta), **riscritta il 2026-11-25**
(perimetro ristretto ai beni; relazione unica; raggruppamenti ad albero) e
aggiornata il 2026-11-25 (fase 3 fatta).
Stato: fasi 1, 2a, 2b e 3 rilasciate; prossima la fase 4 (raggruppamenti).

## Perimetro

Questa spec tratta **solo i beni catastali e i loro legami**:

- il **bene** (foglia): unità immobiliare o terreno, coi dati catastali;
- il **raggruppamento** (ramo): complesso, edificio, abitazione con
  pertinenze, fondo…, che contiene beni e altri raggruppamenti;
- la **relazione** soggetto ↔ bene o raggruppamento, che dice quale diritto,
  godimento o incarico il soggetto ha;
- i **documenti** del bene, del raggruppamento e della relazione;
- il riepilogo "chi paga cosa" che si ricava dalle relazioni.

Fuori perimetro (decisione dell'utente del 2026-11-25): contratti di
locazione (`affitti_lungo`), affitti brevi, condominio e millesimi,
calcoli fiscali. Quando questi moduli hanno bisogno dei beni li leggono
tramite i servizi di immobili.

## Perché

- Il terreno "non è diverso da un immobile, è solo diverso il catasto"
  (fasi 1-2, fatte).
- Il legame tra soggetto e bene oggi è sparso: diritti reali in
  `immo_diritti_immobile` (via `immo_proprietari`), conduttori in
  `immo_assegnazioni_conduttore` (via `immo_conduttori`), amministratore in
  `core_relazioni`, tecnici in `affitti_lungo.tecnici` senza bene. Il
  comodatario non ha posto. L'utente vuole **una sola relazione** con un
  tipo, divisa in famiglie.
- I beni si raggruppano a più livelli. Caso reale dell'utente: un complesso
  di 3 edifici gestito **senza amministratore**, uno con 4 unità collegate a
  un terreno. Un incarico (es. il manutentore della caldaia centralizzata)
  riguarda l'edificio, non la singola unità.

## Obiettivi

1. **Bene** comune a unità e terreni (fatto, fasi 1-2a).
2. **Raggruppamenti ad albero**: un ramo ha un tipo, un nome e al più un
   ramo padre; un bene sta al più in un ramo. Albero puro (scelta
   dell'utente del 2026-11-25): niente beni o rami con due padri.
3. **Relazione unica** soggetto ↔ bene o ramo in `core_relazioni`, con i
   tipi in famiglie: **diritti reali**, **godimento**, **incarichi**
   (elenco estendibile). Sostituisce diritti e assegnazioni dei conduttori.
4. **Eredità**: una relazione su un ramo vale per tutto quello che il ramo
   contiene; la scheda del bene mostra anche le relazioni ereditate.
5. **Documenti** su bene, ramo e relazione.
6. **Chi paga cosa** dalle relazioni (diritti reali del bene + godimento
   del bene o ereditato).
7. **Selettore unico** dei beni e dei rami.
8. **Import visure dei terreni** (fase successiva, campioni disponibili).

## Non obiettivi (per ora)

- Contratti, canoni, registrazioni RLI: modulo `affitti_lungo`. Resta da
  decidere se un contratto registrato crei da sé la relazione di godimento
  (vedi Domande aperte).
- Spostare i **tecnici** di `affitti_lungo` tra gli incarichi: lavoro
  separato. Per ora gli incarichi su un bene si creano scegliendo
  un'anagrafica qualsiasi.
- **Condominio**: resta un'entità a sé con l'amministratore come relazione
  (`amministratore_condominio`). Unirlo ai raggruppamenti si valuterà quando
  servirà; l'utente oggi non ha amministratori.
- Calcoli fiscali (IMU, redditi, rivalutazioni): si registrano i dati, non
  i calcoli.
- Adempimenti del contratto agrario e dell'impianto termico (catasto
  regionale impianti, comunicazioni del terzo responsabile): si registra chi
  ha l'incarico e i documenti, non le scadenze normative.

## Anti-obiettivi

- Due modi di fare la stessa cosa: due tabelle di relazioni, due meccanismi
  di raggruppamento, componenti duplicati per unità e terreni.
- Un ramo che entra in un calcolo fiscale come se fosse un bene.
- Perdere dati di `tenant_produzione` (dati reali dell'utente): niente
  azzeramento, migrazione con conteggi verificati.

## Approcci considerati

- **A. Rami in una tabella propria** (`immo_raggruppamenti`), beni che
  puntano al ramo. `immo_beni` resta catasto puro. **Scelto dall'utente il
  2026-11-25.**
- B. Rami e beni come nodi della stessa tabella `immo_beni`: tutto ciò che
  punta a `bene_id` vale subito anche per i rami, ma ogni lista e calcolo
  deve escluderli e i dati catastali obbligatori non hanno senso sul ramo.
- Scartati: relazioni separate per famiglia (contro la relazione unica);
  ramo come testo nel bene (non regge l'annidamento).

Per la relazione unica, scelta di chi scrive la spec: **riusare
`core_relazioni`** della piattaforma (spec
`2026-11-10-relazioni-ruoli-soggetti-design.md`) invece di una tabella nuova
di immobili. Ha già soggetto, tipo da catalogo, oggetto
(`entity_type`/`entity_id`), periodo, sottotipo, dati, scadenze,
visibilità per permesso e modulo, e ci sta già l'amministratore. Diritti e
conduttori passano da relazioni "MODULO" (lette dalle tabelle di immobili)
a relazioni "CORE".

## Come funziona

### Bene (fatto)

```
immo_beni (id, tipo_bene UNITA|TERRENO, codice, comune_codice, comune, provincia,
           indirizzo/località, cap, sezione, foglio, particella, denominatore,
           subalterno, partita, descrizione, note, attivo, timestamp,
           raggruppamento_id → immo_raggruppamenti, nullable)   ← nuovo
   ├── immo_unita_immobiliari (id = immo_beni.id): categoria, rendita, superficie…
   └── immo_terreni (id = immo_beni.id): tipologia, uso, edificabile, esente IMU…
           └── immo_terreni_porzioni (qualità, classe, superficie m², redditi…)
```

Lo stesso id identifica il bene e la specializzazione (ereditarietà a
tabelle collegate). `entity_type = IMMOBILE` di documenti, scadenze e
relazioni significa "bene".

### Raggruppamenti

```
immo_raggruppamenti (id, tipo, nome, padre_id → immo_raggruppamenti nullable,
                     descrizione, note, attivo, timestamp)
```

- **Tipi** (elenco estendibile, dichiarato da immobili):
  `COMPLESSO`, `EDIFICIO`, `ABITAZIONE_CON_PERTINENZE`, `FONDO`, `ALTRO`.
- **Albero puro**: un ramo ha al più un padre, un bene al più un ramo
  (`immo_beni.raggruppamento_id`). Il servizio rifiuta i cicli (un ramo non
  può finire dentro un suo discendente).
- **Controlli per tipo** (avvisi, non blocchi, salvo dove detto):
  - `ABITAZIONE_CON_PERTINENZE`: contiene solo beni, nessun sotto-ramo
    (blocco); esattamente un'unità di categoria A (tranne A/10) e unità
    C/2, C/6, C/7; **avviso** se c'è più di una pertinenza della stessa
    categoria (IMU abitazione principale: una per categoria, L. 160/2019
    c. 741).
  - `FONDO`: avviso se contiene unità che non sono fabbricati rurali.
- **Cancellare un ramo**: i figli (beni e rami) salgono al padre del ramo
  cancellato; le relazioni e i documenti del ramo si eliminano come per il
  bene (i file restano nello storage). Si chiede conferma mostrando cosa
  sale e cosa si elimina.
- **Spostare** un bene o un ramo = cambiarne il padre (anche "nessuno").

### Collegamenti tra beni (ridotti)

`immo_beni_collegamenti` resta solo per il legame che **non è un
raggruppamento**: `FABBRICATO_SU_PARTICELLA` (particella del catasto terreni
"ente urbano" o area di corte ↔ unità costruita sopra: lo stesso pezzo di
terra visto dai due catasti). I tipi `PERTINENZA` e `PARTE_DI_FONDO`
diventano raggruppamenti (vedi Migrazione).

### Relazione unica

Ogni relazione è una riga di `core_relazioni`:

- `soggetto_id`: l'anagrafica;
- `ruolo_id`: il tipo, dal catalogo `core_ruoli_disponibili` (dichiarato in
  `relation_types` del manifest di immobili);
- `entity_type` + `entity_id`: `IMMOBILE` + id del bene, oppure
  **`RAGGRUPPAMENTO`** (nuovo) + id del ramo;
- `data_inizio`, `data_fine`, `note`, `dati`, scadenza se il tipo la
  prevede;
- **quota** come **frazione**, come la scrive l'Agenzia delle Entrate nelle
  visure ("Proprieta' per 1/2"): due colonne nuove `quota_numeratore` e
  `quota_denominatore` (interi, nullable insieme, `0 < num <= den`), solo
  per i tipi che la ammettono. Si salva come scritta, senza ridurla; somme e
  confronti sono esatti (tre terzi fanno 1). La percentuale si ricava solo
  dove un modello la chiede (decisione dell'utente del 2026-11-25).

Il catalogo guadagna tre campi nei `relation_types` (sincronizzati in
`core_ruoli_disponibili` come gli altri): `famiglia`, `ammette_quota`,
`solo_beni` (vero = non si aggancia a un ramo).

**Tipi di immobili** (tutti `fonte = CORE`):

| Famiglia | Tipi | Quota | Su |
|---|---|---|---|
| Diritti reali | `proprieta`, `nuda_proprieta`, `usufrutto`, `uso`, `abitazione`, `superficie`, `enfiteusi`, `diritto_reale_altro` | sì | solo beni |
| Godimento | `conduttore` (locazione), `affittuario_agrario`, `comodatario`, `godimento_altro` | no | bene o ramo |
| Incarichi | `manutentore`, `terzo_responsabile_impianto`, `responsabile_impianto`, `tecnico_incaricato`, `incarico_altro` | no | bene o ramo |

- I diritti reali stanno solo sui beni perché il catasto e l'IMU ragionano
  per bene; la quota è quella della visura.
- **"Applica a tutti i beni del ramo"** (scelta dell'utente del
  2026-11-25): dalla scheda del ramo si sceglie soggetto, tipo di diritto
  reale, quota e date, e il servizio crea la stessa relazione su ogni bene
  contenuto (anche nei sotto-rami). Prima mostra l'elenco dei beni e salta,
  segnalandoli, quelli dove il soggetto ha già quel diritto aperto o dove le
  quote supererebbero l'intero. Le relazioni create sono normali relazioni dei
  beni: nessun legame col ramo resta dopo.
- Il **titolo** del godimento è il tipo stesso (locazione, affitto agrario,
  comodato). Per il comodato scritto la relazione può portare in `dati` gli
  estremi di registrazione (data, ufficio, numero): servono per la riduzione
  IMU del comodato a parenti di primo grado e per le detrazioni dei lavori
  del comodatario (Ris. MEF 1/DF/2016; Circ. AdE 26/E/2015). La
  registrazione del comodato scritto va fatta entro 20 giorni, imposta fissa
  200 euro: qui si registra il dato, non si controlla il termine.
- **Impianto termico** (DPR 74/2013 art. 6; DPR 412/1993 art. 1): il
  responsabile è l'occupante o il proprietario, l'amministratore negli
  impianti centralizzati in condominio; può delegare un terzo responsabile
  con atto scritto (vietato per le singole unità residenziali con generatore
  non in locale tecnico dedicato). Il terzo responsabile e il manutentore si
  agganciano all'unità (caldaia autonoma) o al ramo (caldaia centralizzata
  dell'edificio). Qui non si controlla il divieto di delega: si registra.
- `amministratore_condominio` resta com'è (oggetto `CONDOMINIO`).
- Il codice `conduttore` resta lo stesso di oggi; `proprietario` diventa
  l'insieme dei tipi della famiglia "diritti reali" (le liste e i filtri
  "Proprietari" lo usano così).

**Regole del servizio** (in immobili, sopra `RelazioneService`):

- un tipo `solo_beni` su un ramo → errore;
- quota ammessa solo se `ammette_quota`; per i diritti reali le quote
  aperte dello stesso tipo sullo stesso bene non superano l'intero
  (**avviso**, come oggi);
- duplicati: come le relazioni del core (stesso soggetto, tipo, oggetto
  aperti → errore).

### Eredità sui rami

Le relazioni **effettive** di un bene alla data D sono le sue più quelle di
tutti i rami antenati, valide in D. Un servizio unico
(`relazioni_effettive(bene_id, d)`) le calcola e dice da dove viene
ciascuna. Lo usano la scheda, "chi paga cosa" e il registro costi/ricavi.

- La scheda del bene mostra le ereditate in sola lettura con "dal ramo X"
  e il link al ramo.
- La scheda del ramo mostra le relazioni proprie e quelle ereditate dai
  suoi antenati.
- Se lo stesso tipo è sia sul bene che su un ramo antenato valgono
  entrambe (es. manutentore della caldaia autonoma e manutentore
  dell'ascensore dell'edificio): la scheda le distingue per provenienza.

### Chi paga cosa

Stesse regole di oggi (`services/ruoli_bene.py`, verificate con l'esperto e
l'Archivio Fiscale il 2026-11-25), lette dalle relazioni effettive:

| Voce | A chi va |
|---|---|
| Reddito dominicale, rendita del fabbricato | titolare del godimento (pieno proprietario o usufruttuario/uso/abitazione/enfiteusi/superficie), per quota; al nudo proprietario nulla (TUIR artt. 26, 27) |
| Reddito agrario | chi conduce il terreno: affittuario agrario (o altro godimento) se c'è, anche se contitolare; altrimenti il titolare del godimento (TUIR artt. 32, 33) |
| IMU | titolare del diritto reale di godimento; mai il conduttore o il comodatario (L. 160/2019 c. 743; CGT Veneto 248/2024 per il comodato) |
| Spese ordinarie | chi ha il godimento personale (conduttore, affittuario, comodatario: c.c. art. 1808 per il comodato) se c'è; altrimenti il titolare del godimento (c.c. art. 1004) |
| Spese straordinarie | nudo proprietario con usufrutto, uso o abitazione (c.c. artt. 1005, 1026); enfiteuta (art. 960); superficiario (art. 952); altrimenti il proprietario |

Gli incarichi non entrano nel riepilogo. Senza godimento personale il bene
è condotto dai titolari. **Da verificare con l'esperto prima della fase
che lo implementa**: reddito agrario e spese ordinarie del comodatario di un
terreno; comodato di fabbricato (la rendita resta al proprietario). Regola
provvisoria fino alla verifica: il comodatario si tratta come gli altri
godimenti personali (tabella sopra).

### Documenti

- `EntityType` (enum PostgreSQL di `core_documenti`) guadagna
  `RAGGRUPPAMENTO` e `RELAZIONE`: serve un `ALTER TYPE … ADD VALUE` nella
  migrazione.
- Sul **bene**: le tipologie di oggi (visura, planimetria, APE…).
- Sul **ramo**: libretto della caldaia centralizzata, conformità impianti
  comuni, titoli edilizi dell'edificio, estratto di mappa del fondo, altro.
  Le tipologie dichiarano su quali `entity_type` valgono.
- Sulla **relazione**: atto di provenienza (diritto reale), contratto di
  comodato o di affitto agrario (godimento), delega al terzo responsabile
  e lettera d'incarico (incarichi).
- La scheda del bene elenca anche i documenti dei rami antenati, divisi
  per provenienza.

### API

- `/api/v1/raggruppamenti/`: lista (albero o piatta, filtro per tipo),
  dettaglio con figli, crea, modifica, sposta (cambia padre), cancella.
- `/api/v1/beni/{id}`: aggiunge `raggruppamento_id` e il percorso
  (complesso › edificio › …); `PATCH` per spostarlo.
- `/api/v1/beni/{id}/relazioni` e `/api/v1/raggruppamenti/{id}/relazioni`:
  relazioni proprie ed ereditate (con provenienza) e creazione;
  aggiornamento e chiusura via le rotte delle relazioni del core.
- Le rotte `/proprietari`, `/diritti-immobile`, `/conduttori`,
  `/assegnazioni-conduttore` spariscono a fine migrazione; il frontend
  passa alle relazioni.
- Selettore: `/api/v1/beni/cerca?q=…&rami=true` cerca tra unità, terreni e
  rami (codice, indirizzo, foglio/particella, nome del ramo), senza il
  limite di 20 di oggi (paginato).

### Interfaccia

- **Albero** `/raggruppamenti`: rami espandibili coi beni dentro; crea
  ramo, sposta (scegliendo il nuovo padre dal selettore), cancella.
- **Scheda del ramo** `/raggruppamenti/:id`: percorso, figli, relazioni
  (proprie ed ereditate), documenti.
- **Scheda del bene**: percorso del ramo in alto; sezione "Soggetti" unica
  con le relazioni divise per famiglia (diritti reali con quote,
  godimento, incarichi), le ereditate in sola lettura; "chi paga cosa";
  documenti propri e dei rami.
- **Proprietari** e **Conduttori** restano voci di menu: lista unica delle
  anagrafiche prefiltrata per famiglia (diritti reali / godimento), come
  previsto dalla spec delle relazioni.
- **Selettore unico** di beni e rami ovunque si sceglie un bene.

### Import visure

Le visure scrivono i diritti reali come relazioni (tipo dalla visura,
quota, date). La chiave del bene non cambia (comune + foglio + particella
+ denominatore + subalterno). Se una visura più recente cambia gli
intestatari, l'import propone di chiudere le relazioni vecchie con una
data di fine. L'import dei terreni (porzioni, intestatari) e la proposta
fabbricato ↔ particella dalle visure analitiche sono l'ultima fase.

## Migrazione dei dati

In ogni schema tenant, **senza azzerare** (prima backup in
`~/apps/gestione-affitti-backups`). Conteggio del 2026-11-25 in
`tenant_produzione`: 0 diritti, 0 assegnazioni, 0 proprietari, 0
conduttori, 0 collegamenti, 0 documenti `PROPRIETARIO` (l'utente non ha
ancora ricaricato dopo l'azzeramento della fase 1). La migrazione va
comunque scritta per i tenant che hanno dati (tenant di prova, dati di
esempio) e ricontata prima del rilascio.

Regole per i casi dubbi (scelte di chi scrive la spec): la migrazione **si
ferma e li elenca** invece di indovinare; in particolare due diritti
aperti dello stesso soggetto, tipo e bene (anche `PROPRIETARIO` +
`COMPROPRIETARIO`) e date non `YYYY-MM-DD`. Un soggetto ha **una sola
relazione** per tipo e bene, con la quota totale: il vincolo dei duplicati
del core resta com'è.

1. `immo_diritti_immobile` → `core_relazioni`: soggetto =
   `immo_proprietari.soggetto_id`; tipo da `tipo_diritto`
   (`PROPRIETARIO` e `COMPROPRIETARIO` → `proprieta`, `NUDA_PROPRIETA` →
   `nuda_proprieta`, `USUFRUTTUARIO` → `usufrutto`, `USO`, `ABITAZIONE`,
   `SUPERFICIE`, `ENFITEUSI` → omonimi, `ALTRO` → `diritto_reale_altro`);
   quota, date (oggi stringhe `YYYY-MM-DD` → Date), note.
2. `immo_assegnazioni_conduttore` → `core_relazioni` tipo `conduttore`,
   soggetto = `immo_conduttori.soggetto_id`, date e note.
3. Le note di `immo_proprietari.note_proprietario` e `immo_conduttori.note`
   non hanno un bene: finiscono in `dati.note_ruolo` di ciascuna relazione
   migrata di quel ruolo (sono 0-poche righe; la migrazione le conta).
4. Collegamenti `PERTINENZA` aperti → un ramo
   `ABITAZIONE_CON_PERTINENZE` per abitazione, nome = codice
   dell'abitazione, con abitazione e pertinenze dentro. `PARTE_DI_FONDO`
   aperti → un ramo `FONDO` col terreno principale e le particelle. I
   collegamenti chiusi (con data di fine) si perdono: la migrazione li
   elenca nel log e si ferma se ce ne sono, così si decide prima.
5. Documenti con `entity_type = PROPRIETARIO` (puntano a
   `immo_proprietari.id`, che sparisce) passano a `SOGGETTO_ANAGRAFICO` con
   l'id del soggetto.
6. Verifica: righe migrate = righe di partenza per diritti e assegnazioni;
   poi si eliminano `immo_diritti_immobile`, `immo_assegnazioni_conduttore`,
   `immo_proprietari`, `immo_conduttori` e i provider MODULO di immobili.
   `scripts/promote.sh` si ferma se una tabella perde righe: le tabelle
   eliminate gli vengono indicate esplicitamente.

Il core conosce le tabelle degli oggetti (`TABELLE_OGGETTI`, come già per
`immo_beni`): si aggiunge `immo_raggruppamenti` con lo stesso schema, senza
rendere registrabili gli `entity_types` (scelta di chi scrive la spec).
`affitti_lungo` non ha chiavi verso le tabelle eliminate: le riesporta solo
in `models/__init__.py`, da togliere. Nella fase 3 il `conduttore` si crea a
mano, come oggi.

Riferimenti da aggiornare: relazioni SQLAlchemy di `SoggettoAnagrafico`
(`proprietari`, `conduttori`), import di `Proprietario`/`DirittoImmobile`
in `affitti_lungo/models/__init__.py`, controllo tabelle in
`anagrafica_italiana/routes/soggetti.py`, `visura_import_service.py`,
`lettura_documenti/abbinamento.py`, `services/ruoli_bene.py`, dati di
esempio e tenant di prova (`tenant_test_nuovo`, `tenant_test_evolutivo`).

## Piano a fasi

Ogni fase si rilascia da sola.

1. **Bene comune** (fatta il 2026-11-12).
2. **Terreni come beni** (2a fatta il 2026-11-13) e **collegamenti + chi
   paga cosa** (2b fatta il 2026-11-25).
3. **Relazione unica** (fatta il 2026-11-25): tipi in famiglie nel catalogo, quota in
   `core_relazioni`, migrazione di diritti e conduttori, nuovi tipi di
   godimento (comodatario, affittuario agrario) e incarichi sui beni,
   sezione "Soggetti" della scheda, chi paga cosa dalle relazioni,
   import visure sulle relazioni, documenti sulla relazione.
4. **Raggruppamenti**: tabella, albero, scheda del ramo, relazioni e
   documenti sui rami, eredità, "applica a tutti i beni del ramo" per i
   diritti reali, migrazione di pertinenze e fondi in rami, selettore unico
   di beni e rami.
5. **Import visure dei terreni** e proposta fabbricato ↔ particella.

## Domande aperte

- Un contratto registrato in `affitti_lungo` deve creare da sé la relazione
  `conduttore` sul bene (tramite un servizio di immobili, come IMU e TARI
  col registro costi/ricavi) o restano separati? Da decidere con la
  pianificazione di `affitti_lungo`.
- Tecnici di `affitti_lungo` → incarichi di immobili: quando e come.

## Da verificare con un professionista

Elenco comuni esenti IMU (Circ. MEF 9/1993) per Bologna, Forlì,
Pré-Saint-Didier, Castiglione della Pescaia; esenzione IRPEF CD/IAP dal
2023; IMU su enfiteusi e superficie (L. 160/2019); regola "una pertinenza
per categoria" anche per prima casa e cedolare secca (qui solo avviso
IMU); diritto di superficie prima dell'ultimazione della costruzione;
spese straordinarie in enfiteusi; affitto tra comproprietari del fondo;
conduttore società di capitali; reddito agrario e spese del comodatario
di un terreno.

## Storia: azzeramento della fase 1 (2026-11-12)

La fase 1 è partita da zero per scelta dell'utente: le tabelle di immobili
e quelle dipendenti di `affitti_lungo` e `affitti_brevi` furono svuotate
(backup `gestione_affitti_prod_20261112_123707.sql`), restarono anagrafiche,
utenti, configurazioni e tabelle di dominio. Dalla fase 2a in poi le
migrazioni conservano i dati.
