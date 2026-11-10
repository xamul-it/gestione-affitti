# Terreni allo stesso livello delle unità immobiliari — design

Data: 2026-11-10 · Stato: bozza da approvare (domande aperte in fondo)

## Perché

Oggi il terreno è un'entità isolata: ha i dati catastali in una sola riga
(foglio, particella, qualità, classe, redditi), ma non ha proprietari e
diritti, conduttori, documenti, registro delle variazioni, scheda di
dettaglio, e l'import visure lo **conta senza importarlo**. Per l'utente
"non è diverso da un immobile, è solo diverso il catasto": un terreno è un
bene del **Catasto Terreni** come l'unità è un bene del **Catasto
Fabbricati**, e deve avere tutto quello che ha l'unità.

Regole di dominio dall'Archivio Fiscale: rapporto dell'agente esperto del
2026-11-10 (fonti citate sotto, tra parentesi).

## Obiettivi

1. **Identificazione catastale completa** della particella: codice catastale
   del comune, sezione, foglio, particella (anche nella forma
   numero/denominatore), subalterno, partita (facoltativa); una o più
   **porzioni** con qualità, classe, superficie, reddito dominicale e agrario,
   deduzioni (Mod. RLI ed. 14/10/2025, Quadro C; Circ. 9/1990; TUIR art. 30).
2. **Proprietari e diritti** sul terreno come sulle unità, stesso elenco di
   diritti e quote (Circ. 18/E/2013: proprietà, nuda proprietà, usufrutto,
   uso, enfiteusi, superficie). Le servitù sono note sul terreno, non
   intestatari.
3. **Conduttori del terreno** (chi lo coltiva o lo usa), con il tipo di
   conduzione: affitto di fondo rustico, comodato, conduzione diretta del
   proprietario, altro; e la qualifica del conduttore: nessuna, coltivatore
   diretto, IAP, società agricola (L. 203/1982; D.Lgs. 99/2004 art. 1).
4. **Documenti del terreno** con le tipologie del manifest: visura,
   estratto di mappa, **certificato di destinazione urbanistica** (scade un
   anno dal rilascio: L. 47/1985 art. 18, oggi art. 30 DPR 380/2001 da
   verificare), atto di provenienza, contratto di affitto agrario, tipo di
   frazionamento / tipo mappale, altro.
5. **Registro delle variazioni** (variazione colturale, frazionamento, tipo
   mappale, voltura) come per le unità, con le modifiche manuali e da
   documento.
6. **Scheda del terreno** `/terreni/:id` con le stesse sezioni della scheda
   unità: dati, documenti, variazioni, diritti, conduttori, scadenze.
7. **Import visure**: i terreni della visura per soggetto e per immobile
   vengono proposti come le unità (aggiungi/aggiorna campo per campo,
   intestatari e diritti), abbinati per comune + foglio + particella
   (+ subalterno).
8. **Ruoli**: le pagine Proprietari e Conduttori e la scheda del soggetto
   mostrano anche i terreni (oggetto `TERRENO` nelle relazioni).

## Non obiettivi (per ora)

- Calcoli fiscali: rivalutazioni dei redditi (80%/70% + 30% L. 228/2012),
  esenzione IRPEF CD/IAP, IMU dei terreni agricoli e delle aree
  fabbricabili. Le fonti trovate hanno buchi (esenzione IRPEF dal 2023,
  elenco comuni montani della Circ. 9/1993, IMU dopo L. 160/2019): si
  registrano i **dati** che serviranno (uso del terreno, edificabile,
  esente IMU per montanità come scelta manuale), non i calcoli.
- Contratto di affitto agrario completo (canone, registrazione RLI codici
  T1–T4, denuncia annuale di febbraio, prelazione e comunicazione offerte a
  90 giorni): è materia di un modulo affitti, come per le unità. Qui solo il
  ruolo "conduttore" con periodo, tipo e qualifica.
- Eventi AGEA, porzioni "AA/AB" come sigle standard (non confermate dalle
  fonti), livelli storici (mappati a "Altro").

## Anti-obiettivi

- Duplicare per i terreni componenti e servizi delle unità (sezioni
  della scheda, diritti, conduttori, variazioni, documenti): vanno resi
  generici sul "bene" e riusati.
- Rompere `affitti_lungo`, che dipende dalle unità immobiliari.

## Come funziona

### Scelta di fondo: estendere, non unificare

Due strade:

- **A — estendere (consigliata).** Il terreno resta una tabella sua; le
  tabelle collegate alle unità (diritti, assegnazioni dei conduttori,
  variazioni catastali) ricevono una colonna `terreno_id` accanto a
  `unita_immobiliare_id`, con il vincolo "esattamente uno dei due". I
  documenti usano un nuovo `entity_type = TERRENO`. Lato interfaccia, le
  sezioni della scheda ricevono `bene = { tipo: 'unita' | 'terreno', id }`.
- **B — entità comune "bene catastale"** da cui derivano unità e terreno.
  Più pulita a lungo termine, ma tocca tutte le chiavi esterne, il modulo
  affitti e i dati in produzione.

Si propone **A**: meno rischio, stesse funzioni per l'utente.

### Dati

`immo_terreni` (esistente) — si aggiungono:
`codice_catastale_comune` (4 caratteri, es. A944), `denominatore`,
`partita`, `uso_terreno` (AGRICOLO, INCOLTO, AREA_EDIFICABILE, ENTE_URBANO,
ALTRO), `edificabile` (sì/no), `esente_imu_montano` (scelta manuale, nullo =
non indicato), `servitu` (note). La superficie si salva in m² e si mostra
in ha.are.ca.

`immo_terreni_porzioni` (nuova): terreno, etichetta (facoltativa), qualità,
classe, superficie m², reddito dominicale, reddito agrario, deduzioni
(testo). I campi di porzione attuali del terreno (qualità, classe, redditi)
migrano nella prima porzione.

`immo_diritti_immobile`, `immo_assegnazioni_conduttore`,
`immo_variazioni_catastali`: `terreno_id` nullable + vincolo. Le
assegnazioni guadagnano `tipo_conduzione` e `qualifica_conduttore`
(nulli per le unità).

### Abbinamento e import visure

Chiave del terreno: codice catastale del comune (o nome) + foglio +
particella (+ denominatore, + subalterno), zeri iniziali ignorati, come per
le unità. Nelle visure analitiche delle unità compare anche "Particelle
corrispondenti al catasto terreni": sarà la base per collegare un ente
urbano alle sue unità (fase successiva, non in questo lavoro).

### Interfaccia

- Lista terreni: riga cliccabile verso la scheda; colonne comune, foglio/
  particella, qualità prevalente, superficie in ha, conduttore attuale.
- Scheda terreno con le sezioni comuni.
- Caricamento unico dei documenti: abbinamento anche ai terreni.
- Proprietari/Conduttori: colonna "Beni" con unità e terreni.

## Piano a fasi

1. Modello e migrazioni (colonne, porzioni, vincoli, `entity_type` TERRENO,
   tipologie documentali del manifest).
2. Scheda terreno e sezioni generiche (diritti, conduttori, variazioni,
   documenti), lista cliccabile.
3. Import visure dei terreni (serve un campione).
4. Relazioni e pagine Proprietari/Conduttori; caricamento unico.

Ogni fase si rilascia da sola.

## Domande aperte per l'utente

1. **Strada A (estendere) o B (bene comune)?** Proposta: A.
2. **Conduzione**: bastano tipo di conduzione e qualifica, con il contratto
   agrario rimandato a un modulo affitti? Oppure vuoi già canone e scadenze
   del contratto sul terreno?
3. **Campione**: serve una visura (per soggetto o per immobile) che contenga
   terreni; in `docs/visure` ci sono solo fabbricati.
4. **Quali terreni hai** (comuni)? Serve per capire se la montanità della
   Valle d'Aosta (esenzione IMU, affitto particellare a 6 anni) entra subito.
5. **Unità**: nello stesso lavoro aggiungo codice catastale del comune e
   sezione anche alle unità, per avere la stessa chiave nei due catasti?
   Proposta: sì, sono gli stessi campi.

## Da verificare con un professionista

Elenco comuni esenti IMU (Circ. MEF 9/1993) per Bologna, Pré-Saint-Didier,
Castiglione della Pescaia; esenzione IRPEF CD/IAP dal 2023; IMU su
enfiteusi e superficie (L. 160/2019); forma, disdetta e art. 45 della
L. 203/1982; regole regionali sulle zone montane.
