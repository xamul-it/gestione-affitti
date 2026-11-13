# Beni catastali: unità immobiliari e terreni allo stesso livello — design

Data: 2026-11-10, aggiornata il 2026-11-12 (collegamenti tra beni) e il 2026-11-13 (fase 2a fatta) · Stato: approvata dall'utente il 2026-11-12.
Strada B (bene comune) scelta dall'utente il 2026-11-10.

## Perché

Oggi il terreno è un'entità isolata: ha i dati catastali in una riga, ma non
ha proprietari e diritti, conduttori, documenti, variazioni, scheda; l'import
visure lo **conta senza importarlo**; si può solo disattivare. Per l'utente
"non è diverso da un immobile, è solo diverso il catasto".

In più il modulo affitti è legato alla sola unità immobiliare
(`contratti.unita_immobiliare_id`): **un terreno non si può affittare** e un
contratto copre **un solo immobile**, mentre nella realtà ne copre spesso
più d'uno (appartamento + box + cantina, casa + terreno). Il modello RLI
(ed. 14/10/2025, Quadro C) prevede infatti più immobili per contratto, sia
del Catasto Fabbricati ("U") sia del Catasto Terreni ("T").

Regole di dominio: rapporto dell'agente esperto sull'Archivio Fiscale del
2026-11-10 (fonti tra parentesi).

## Obiettivi

1. **Bene catastale** come concetto comune: un bene è un'**unità
   immobiliare** (Catasto Fabbricati) o un **terreno** (Catasto Terreni).
   Proprietari e diritti, conduttori, documenti, variazioni catastali,
   spese ricorrenti (IMU, consorzi…), scadenze e relazioni si riferiscono al
   bene, quindi valgono per entrambi senza duplicare nulla.
2. **Identificazione catastale comune**: codice catastale del comune (es.
   A944) e nome, sezione, foglio, particella (anche numero/denominatore),
   subalterno, più indirizzo o località (Mod. RLI, Quadro C).
3. **Terreno completo**: una o più **porzioni** con qualità, classe,
   superficie, reddito dominicale e agrario, deduzioni (Circ. 9/1990; TUIR
   art. 30); uso del terreno, edificabile, esente IMU per montanità come
   scelta manuale; servitù come nota.
4. **Chi paga cosa**: dai diritti (piena proprietà, nuda proprietà,
   usufrutto, con le quote) e dal conduttore la scheda dice a chi vanno
   redditi, imposte e spese del bene (vedi "Titolari, usufrutto e
   conduttore"). Il conduttore resta quello di oggi (soggetto e periodo): il
   rapporto contrattuale è affare del modulo affitti, qui conta solo sapere
   **se il bene è condotto da qualcuno diverso dai titolari**.
5. **Scheda del bene**: la scheda dell'unità diventa la scheda del bene, con
   le stesse sezioni per unità e terreni; i dati specifici cambiano col tipo.
6. **Contratti di affitto con più beni** (modulo `affitti_lungo`): un
   contratto riguarda una lista di beni, unità e/o terreni.
7. **Import visure** anche dei terreni (fase dedicata, serve un campione).
8. **Documenti del terreno**: visura, estratto di mappa, certificato di
   destinazione urbanistica (scade un anno dal rilascio: L. 47/1985 art. 18;
   corrispondenza con art. 30 DPR 380/2001 da verificare), atto di
   provenienza, contratto di affitto agrario, tipo di frazionamento / tipo
   mappale, altro.
9. **Collegamenti tra beni** (richiesta dell'utente del 2026-11-12): un
   bene può essere legato a un altro, con un tipo e un periodo. Primo uso:
   le **pertinenze** (box, cantina, soffitta di un'abitazione); poi il
   fabbricato rurale sulla particella "ente urbano" e le particelle che
   formano un fondo.

## Non obiettivi (per ora)

- **Calcoli fiscali** dei terreni (rivalutazioni 80%/70% + 30% L. 228/2012,
  esenzione IRPEF CD/IAP, IMU agricola e aree fabbricabili): le fonti hanno
  buchi (esenzione IRPEF dal 2023, elenco comuni montani della Circ. MEF
  9/1993, IMU dopo L. 160/2019). Si registrano i dati, non i calcoli.
- **Adempimenti del contratto agrario** (registrazione RLI codici T1–T4,
  denuncia annuale di febbraio, comunicazione offerte a 90 giorni e
  prelazione, durata minima 15/6 anni): il contratto potrà riguardare un
  terreno, ma le regole specifiche dell'affitto agrario sono un lavoro
  successivo del modulo affitti.
- **Affitti brevi**: riguardano solo alloggi, restano legati alle unità.
- **Millesimi e spese condominiali** (`affitti_lungo.spese`,
  `ripartizione_spesa`): restano sulle unità.
- Collegamento **automatico** ente urbano ↔ unità dall'import delle visure
  ("Particelle corrispondenti al catasto terreni"): il collegamento si crea
  a mano in fase 2; l'import lo proporrà nella fase 4.
- Complessi senza amministratore (palazzine): si gestiscono come condominio,
  nessuna entità nuova. La scelta del condominio nel form dell'unità e la
  scheda del condominio sono un lavoro a parte (immobili.md §5).
- Tipo di conduzione e qualifica del conduttore agricolo (coltivatore
  diretto, IAP): servono solo ai calcoli fiscali, quindi più avanti.

## Anti-obiettivi

- Due copie di componenti, servizi o API per unità e terreni.
- Cancellare soggetti dell'anagrafica o dati di altri moduli che non
  dipendono dai beni (vedi Dati esistenti).

## Come funziona

### Modello: bene con unità e terreno come specializzazioni

```
immo_beni (id, tipo_bene UNITA|TERRENO, codice, comune_codice, comune, provincia,
           indirizzo/località, cap, sezione, foglio, particella, denominatore,
           subalterno, partita, descrizione, note, attivo, timestamp)
   ├── immo_unita_immobiliari (id = immo_beni.id) dati del fabbricato:
   │     categoria, rendita, superficie, locali, piano, condominio…
   └── immo_terreni (id = immo_beni.id) dati del terreno: tipologia, uso,
         edificabile, esente IMU montano, servitù
           └── immo_terreni_porzioni (qualità, classe, superficie m²,
                 reddito dominicale, reddito agrario, deduzioni)
```

**Lo stesso id identifica il bene e la sua specializzazione** (in
SQLAlchemy: ereditarietà a tabelle collegate). Conseguenze:

- tutto ciò che oggi punta a `immo_unita_immobiliari.id` (affitti brevi,
  spese condominiali, millesimi, documenti con `entity_type = IMMOBILE`,
  scadenze) **resta valido senza modifiche**;
- `IMMOBILE` come `entity_type` di documenti, scadenze e relazioni passa a
  significare "bene" e punta a `immo_beni`: un documento di un terreno è un
  documento `IMMOBILE` col suo id.

Tabelle che passano dall'unità al bene (`bene_id` al posto di
`unita_immobiliare_id`): diritti, assegnazioni dei conduttori, variazioni
catastali, spese ricorrenti (che poi lasciano il posto al registro costi e
ricavi, `2026-11-12-costi-ricavi-design.md`). `affitti_lungo`: nuova tabella
`contratto_beni (contratto_id, bene_id)`; `contratti.unita_immobiliare_id` sparisce.

I campi comuni (indirizzo, foglio, particella…) oggi duplicati in unità e
terreno si spostano nel bene. Il terreno guadagna la cancellazione vera
(oggi solo disattivazione), come l'unità.

### Titolari, usufrutto e conduttore

Su un bene possono esserci insieme tre ruoli: **nudo proprietario**,
**usufruttuario** e **conduttore** (caso reale delle visure dell'utente:
terreni e fabbricato rurale in usufrutto a uno e nuda proprietà a un
altro). I diritti e le quote esistono già (`NUDA_PROPRIETA`,
`USUFRUTTUARIO`, date di inizio e fine); il conduttore è l'assegnazione di
oggi. Il **titolare del godimento** è il pieno proprietario o, se c'è,
l'usufruttuario.

| Voce | A chi va |
|---|---|
| Reddito dominicale del terreno, rendita del fabbricato | titolare del godimento, per quota; al nudo proprietario nulla (TUIR artt. 26, 27) |
| Reddito agrario | chi conduce il terreno: il conduttore se c'è ed è diverso dai titolari, altrimenti il titolare del godimento (TUIR artt. 32, 33) |
| IMU | titolare del godimento, non il nudo proprietario (L. 160/2019, c. 743) |
| Spese ordinarie | conduttore se c'è; altrimenti titolare del godimento (c.c. art. 1004) |
| Spese straordinarie | nudo proprietario se c'è usufrutto, altrimenti proprietario (c.c. art. 1005) |
| Canone dell'affitto | a chi concede il godimento: l'usufruttuario se c'è (modulo affitti) |

Senza conduttore registrato il bene è condotto dai titolari stessi: non
serve un campo apposta. La scheda mostra questo riepilogo; le spese seguono la
tabella con le quote per ruolo del registro costi e ricavi
(`2026-11-12-costi-ricavi-design.md`), che sostituisce le spese ricorrenti. Nessun importo d'imposta viene calcolato (vedi Non obiettivi).

### Collegamenti tra beni

```
immo_beni_collegamenti (id, bene_id, bene_collegato_id, tipo, data_inizio,
                        data_fine, note, timestamp)
```

`bene_id` è il bene principale (es. l'abitazione), `bene_collegato_id` quello
che gli è legato (es. il box); entrambi con `ON DELETE CASCADE`. Un bene non
si collega a sé stesso, e la stessa coppia ha un solo collegamento aperto
per tipo. Tipi:

| Tipo | Principale → collegato | Controlli |
|---|---|---|
| `PERTINENZA` | abitazione (unità di categoria A, tranne A/10) → unità C/2, C/6 o C/7 | una pertinenza appartiene a una sola abitazione per volta; **avviso**, senza bloccare, se un'abitazione ha più di una pertinenza della stessa categoria (per l'IMU dell'abitazione principale ne conta una per categoria: L. 160/2019, c. 741) |
| `FABBRICATO_SU_PARTICELLA` | terreno (particella "ente urbano" o area di corte) → unità costruita sopra | nessuno |
| `PARTE_DI_FONDO` | terreno principale del fondo → altre particelle dello stesso fondo | nessuno |

Il tipo è un elenco che si può estendere. Il collegamento non sposta né
copia diritti o conduttori: ogni bene tiene i suoi, e la scheda segnala se
una pertinenza ha titolari diversi dalla sua abitazione. Dove serve, si usa:

- **scheda**: sezione "Beni collegati" in entrambe le direzioni (il box
  mostra "pertinenza di…", l'appartamento elenca le sue pertinenze);
- **contratti** (fase 3): scegliendo un'abitazione si propongono le sue
  pertinenze aperte da aggiungere al contratto;
- **liste**: l'unità mostra un'icona se è pertinenza o ne ha.

### API

- `/api/v1/beni/` lista e dettaglio comuni (filtro per tipo, ricerca per
  codice, indirizzo, foglio/particella), con i dati della specializzazione.
- `/unita-immobiliari` e `/terreni` restano per creare e modificare i dati
  specifici; leggono e scrivono anche la parte comune.
- Diritti, assegnazioni, variazioni, spese: parametro `bene_id`.
- `/api/v1/beni/{id}/collegamenti` elenco (in entrambe le direzioni),
  creazione, modifica, chiusura con data di fine, cancellazione.

### Interfaccia

- **Scheda** `/beni/:id` (i link `/unita-immobiliari/:id` e `/terreni/:id`
  vi rimandano): intestazione, dati comuni, dati del tipo (per il terreno
  la tabella delle porzioni, superficie in ha.are.ca), documenti,
  variazioni, diritti, conduttori, spese, scadenze.
- Liste unità e terreni restano separate (colonne diverse) e aprono la
  scheda; Proprietari e Conduttori mostrano "Beni" (unità e terreni).
- Scelta del bene (diritto, contratto, documento): un unico selettore che
  cerca tra unità e terreni.
- Contratto: elenco dei beni del contratto al posto dell'unità singola.

### Abbinamento e import visure

Chiave del bene: comune (codice catastale o nome) + foglio + particella
(+ denominatore, + subalterno), zeri iniziali ignorati; il tipo (U/T) viene
dalla sezione della visura. L'import dei terreni propone, come per le
unità, beni da aggiungere o aggiornare, porzioni, intestatari e diritti.

Campioni disponibili (`docs/visure/`, non versionati): visura per soggetto
in tabella (2016, fabbricati e terreni), visura attuale per soggetto
(2025, fabbricati e terreni, porzioni AA/AB con qualità, classe,
superficie, redditi e deduzioni, partita) e visure per immobile al catasto
terreni (ente urbano; particella soppressa con le particelle che ha
originato). I tre parser esistenti riconoscono già i blocchi dei terreni e
li contano: la fase 4 li estrae. Una particella soppressa non crea beni ma
può proporre una variazione su quelli che ha originato. Se una visura più recente cambia gli
intestatari (es. un altro usufruttuario), l'import propone di chiudere i
diritti vecchi con una data di fine invece di cancellarli.

## Dati esistenti

**Decisione dell'utente (2026-11-12): ripartenza.** I dati di questo giro
si buttano e l'utente ricarica pulito dalle visure e dal caricamento unico
dei documenti. Niente migrazione dei dati.

La migrazione della fase 1, in ogni schema tenant:

- svuota le tabelle del modulo immobili (unità, terreni, proprietari,
  diritti, conduttori e assegnazioni, variazioni, spese ricorrenti,
  certificati energetici, millesimi, condomini e tabelle millesimali) e
  quelle che vi dipendono negli altri moduli (contratti, spese e incassi di
  `affitti_lungo`; prenotazioni, soggiorni, blocchi, canali e comunicazioni
  di `affitti_brevi`);
- elimina le righe di documenti, scadenze e relazioni degli oggetti
  azzerati (`entity_type` IMMOBILE, CONDOMINIO, SPESA_RICORRENTE, CONTRATTO,
  comunicazione); i file restano nello storage (il backup del DB non li
  copre, così non si perde nulla per sbaglio);
- crea le tabelle nuove vuote.

Restano: soggetti dell'anagrafica, utenti, configurazioni e tabelle di
dominio (categorie catastali, tipologie, comuni). Il backup prima della
migrazione lo fa già `scripts/promote.sh`, che però si ferma se una tabella
perde righe: per questo rilascio le tabelle azzerate gli vengono indicate
esplicitamente; prima del rilascio si conferma
con l'utente che è il momento giusto (nel frattempo non deve caricare
dati che non vuole perdere).

## Piano a fasi

Ogni fase si rilascia da sola.

1. **Bene comune**: tabella `immo_beni`, unità come specializzazione,
   azzeramento dei dati (vedi Dati esistenti), diritti/assegnazioni/variazioni/spese su
   `bene_id`, relazioni e documenti su `immo_beni`. Per l'utente non cambia
   nulla (stesse pagine), è il fondamento.
2. **Terreni come beni**, in due rilasci:
   - **2a (fatta il 2026-11-13)**: specializzazione terreno, porzioni,
     scheda comune `/beni/:id` con la parte terreno, API `/beni`,
     tipologie documentali, cancellazione, lista cliccabile. Migrazione
     `2026111301_terreni_beni` senza perdita di righe (i terreni del vecchio
     layout diventano beni con una porzione; superficie sempre in m²).
     `/beni` mostra le unità con `immobile.view` e i terreni con
     `terreno.view`.
   - **2b**: **collegamenti tra beni** (pertinenze, fabbricato su
     particella, parte di fondo) e riepilogo "chi paga cosa" (anche per le
     unità).
   - Il **selettore unico dei beni** passa alla fase 3, dove ha i primi
     utilizzatori (contratti, caricamento unico).
3. **Contratti con più beni** in `affitti_lungo` (anche terreni), con la
   proposta delle pertinenze dell'abitazione scelta.
4. **Import visure dei terreni** e caricamento unico dei documenti anche
   per i terreni (campioni disponibili), con la proposta del collegamento
   fabbricato ↔ particella dalle visure analitiche.

## Domande ancora aperte

Nessuna. Risolte il 2026-11-12: ripartenza dei dati; la conduzione si
limita a "chi conduce" (il resto nel modulo affitti); i campioni con
terreni ci sono; i terreni dell'utente sono a Forlì (foglio 40), nessuna
regola valdostana da anticipare.

## Da verificare con un professionista

Elenco comuni esenti IMU (Circ. MEF 9/1993) per Bologna, Forlì,
Pré-Saint-Didier, Castiglione della Pescaia; esenzione IRPEF CD/IAP dal 2023 e maggiorazione
ridotta per CD/IAP; IMU su enfiteusi e superficie (L. 160/2019); regola
"una pertinenza per categoria" anche per agevolazioni prima casa e
cedolare secca (qui solo come avviso IMU); forma,
disdetta e art. 45 della L. 203/1982; regole regionali sulle zone montane.
