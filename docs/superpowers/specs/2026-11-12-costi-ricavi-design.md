# Costi e ricavi dei beni: registro in immobili, calcoli nei moduli — design

Data: 2026-11-12 · Stato: bozza da approvare. Impostazione decisa con
l'utente il 2026-11-12: "in immobili c'è la struttura dei costi e ricavi ma
non calcola; si possono inserire a mano e altri moduli calcolano (IMU, TARI…)
e iniettano i valori aggiungendo le scadenze".

Collegata a `2026-11-10-beni-catastali-design.md` (beni, diritti, usufrutto,
conduttore, collegamenti) e alle regole di dominio di `docs/modules/immobili.md` §1.

## Perché

Oggi le spese sono in due posti che si sovrappongono:

- **spese ricorrenti** (immobili): IMU, TARI, utenze sul bene o sul
  condominio, con responsabile PROPRIETARIO/CONDUTTORE, scadenza, pagato e
  promemoria nello scadenzario;
- **spese** e **ripartizioni** (affitti_lungo): fatture legate alla sola unità,
  con flag "condominiale" e ripartizione per millesimi/consumi/occupanti; non
  sanno chi paga né dell'usufrutto.

I ricavi esistono solo come incassi dei canoni (affitti_lungo). Nessuno dei
due sa che chi **anticipa** una spesa non è sempre chi la **sostiene** (oneri
accessori anticipati dal locatore, quote condominiali pagate dal condomino),
né ripartisce tra nudo proprietario, usufruttuario e conduttore.

## Obiettivi

1. **Un solo registro di costi e ricavi** nel modulo immobili, per bene o per
   condominio, inseribile a mano.
2. **Catalogo delle voci** con natura e ripartizione predefinita, estendibile
   dai moduli tramite manifest.
3. **Chi anticipa e chi sostiene**: ripartizione per soggetto calcolata alla
   data dai ruoli del bene, correggibile; i **riaddebiti** (quote di chi non
   ha anticipato) si seguono fino al recupero.
4. **Contratto per i moduli di calcolo** (IMU, TARI, consorzi, bonus…): leggono
   i dati di immobili, scrivono costi calcolati con scadenza tramite un
   servizio di immobili; immobili non conosce quei moduli.
5. **Ricavi** dal modulo affitti (canoni) e affitti brevi (soggiorni) nello
   stesso registro, per avere costi e ricavi per bene e per soggetto.
6. Sostituire spese ricorrenti e le spese/ripartizioni di affitti_lungo.

## Non obiettivi

- **Calcoli fiscali** (importi IMU, TARI, consorzi, F24, redditi, bonus
  edilizi): moduli separati, ciascuno con la sua spec.
- Contabilità, fatturazione, pagamenti online, riconciliazione bancaria.
- Estrazione automatica dei dati da bollette e fatture (si potrà fare dopo,
  come per i documenti di anagrafica).
- Utenze intestate al conduttore: non si registrano (regola di dominio).

## Anti-obiettivi

- Immobili che contiene logica d'imposta o aliquote.
- Un ricalcolo che sovrascrive ciò che l'utente ha pagato o corretto a mano.
- Moduli di calcolo che scrivono nelle tabelle di immobili senza il servizio.
- Nascondere il proprietario quando la spesa è del conduttore: resta
  visibile, risponde in solido.

## Come funziona

### Voci e nature

Catalogo `voci` (dominio in `public`, override per tenant, sincronizzato dai
manifest come le tipologie documentali): `codice`, `nome`, `tipo`
(COSTO | RICAVO), `natura`, `ripartizione` predefinita, `modulo` che la
dichiara, `attivo`.

| Natura | Esempi | Sostiene (predefinito) |
|---|---|---|
| `IMPOSTA_BENE` | IMU, contributo consorzio di bonifica | titolare del godimento: usufruttuario o proprietario, per quota (c.c. art. 1008; L. 160/2019) |
| `ORDINARIA` / oneri accessori | condominio ordinario, ascensore, pulizie, acqua, riscaldamento, TARI | conduttore se il bene è condotto da altri, altrimenti titolare del godimento (L. 392/1978 art. 9; DM 16/01/2017 all. D; c.c. art. 1004) |
| `STRAORDINARIA` | lavori, rifacimenti, condominio straordinario | nudo proprietario se c'è usufrutto, altrimenti proprietario (c.c. artt. 1005, 1576) |
| `PICCOLA_MANUTENZIONE` | piccole riparazioni d'uso | conduttore (c.c. art. 1609) |
| `RICAVO_GODIMENTO` | canone, soggiorno breve, indennità | chi concede il godimento: usufruttuario o proprietario, per quota |

Una voce può avere una ripartizione fissa tra ruoli (es. portineria 90%
conduttore / 10% locatore): sta nella voce, non nel codice.

### Registro

```
immo_movimenti
  id, tipo COSTO|RICAVO, voce_codice,
  bene_id | condominio_id (esattamente uno), movimento_padre_id (quota di
  una spesa condominiale),
  competenza_dal, competenza_al, periodo, rata,
  importo, data_scadenza, controparte (fornitore / pagatore), documento_id,
  anticipato_da_soggetto_id, pagato, data_pagamento, metodo,
  origine MANUALE|MODULO, modulo, chiave_calcolo (unica), versione_calcolo,
  modificato_a_mano, scadenza_id, note, timestamp

immo_movimenti_quote
  id, movimento_id, soggetto_id, ruolo (PROPRIETARIO, USUFRUTTUARIO,
  NUDO_PROPRIETARIO, CONDUTTORE, ALTRO), percentuale, importo, manuale,
  stato_recupero (NON_DOVUTO | DA_CHIEDERE | CHIESTO | RECUPERATO),
  data_richiesta, data_recupero, rif_incasso
```

- **Ripartizione**: alla creazione, e quando cambiano i ruoli finché la voce
  non è pagata, le quote si calcolano dai ruoli alla data di competenza:
  quote dei diritti, usufrutto/nuda proprietà, conduttore in corso (come la
  tabella "Titolari, usufrutto e conduttore" della spec dei beni). Una quota
  corretta a mano (`manuale`) non si ricalcola.
- **Riaddebito**: una quota di un soggetto diverso da chi ha anticipato nasce
  `DA_CHIEDERE`; si porta a `CHIESTO` e `RECUPERATO` a mano o dal modulo
  affitti (conguaglio oneri accessori, da chiedere entro due mesi: L.
  392/1978 art. 9).
- **Condominio**: una spesa del condominio si ripartisce sulle unità con una
  tabella millesimale (o consumi/occupanti, come oggi); ogni quota è un
  movimento figlio sul bene, con la sua ripartizione per soggetto. Verso il
  condominio paga il condomino, proprietario o usufruttuario, in solido
  (c.c. art. 1123; disp. att. artt. 63, 67).
- **Ricorrenza**: un movimento con periodo si duplica sul periodo successivo
  (come "duplica" delle spese ricorrenti); nessuna generazione automatica.
- **Scadenza**: un costo non pagato con data di scadenza ha il suo promemoria
  nello scadenzario; pagato o cancellato lo chiude.

### Contratto per i moduli di calcolo

Un modulo di calcolo (es. `imu`) dipende da immobili, non il contrario.

- **Legge** con il servizio `immobili.services.dati_beni`:
  `beni_alla_data(db, data, bene_ids=None)` → per ogni bene: tipo, comune
  (codice catastale), categoria, rendita / redditi, superficie, quote dei
  diritti con ruolo, usufrutto, conduttori in corso, collegamenti
  (pertinenze). I dati propri del calcolo (aliquote, delibere, tariffe) sono
  del modulo.
- **Scrive** con `immobili.services.movimenti.registra_calcolato(db, modulo,
  chiave_calcolo, dati, quote=None, versione=None)`:
  - `chiave_calcolo` = modulo + bene + voce + periodo + rata: ricalcolare
    aggiorna, non duplica;
  - una voce **pagata** o **modificata a mano** non viene toccata: il
    servizio restituisce la differenza e la scheda la mostra ("il modulo IMU
    calcola 412 €, registrati 400 €");
  - `quote` opzionali (es. IMU per contribuente); senza, si usa la
    ripartizione predefinita della voce;
  - crea o aggiorna la scadenza collegata.
- **Dichiara** nel manifest le sue voci (`voci_economiche`), sincronizzate
  come le tipologie documentali.
- **Disattivato** il modulo: i movimenti scritti restano (origine visibile),
  non se ne creano di nuovi; la voce torna inseribile a mano.

Una voce senza modulo attivo si inserisce a mano; quando il modulo arriva,
la stessa voce diventa calcolata (le righe manuali restano manuali).

### Ricavi dai moduli affitti

`affitti_lungo` scrive i canoni (dagli incassi) e legge i riaddebiti dei
beni del contratto per il conguaglio; `affitti_brevi` scrive i soggiorni
incassati. Stesso servizio, origine MODULO. Gli incassi restano la verità
del modulo affitti; il registro ne è la vista per bene e soggetto.

### Interfaccia

- Scheda del bene: sezione **Costi e ricavi** (al posto di Spese ricorrenti),
  con filtro per anno, quote per soggetto, stato pagato e recupero, origine
  (manuale / modulo).
- Scheda del condominio: spese del condominio e ripartizione sulle unità.
- Pagina **Riaddebiti**: quote da chiedere o chieste, per soggetto.
- Riepilogo per soggetto e anno: costi sostenuti e ricavi per bene (base per
  un futuro modulo dichiarativo).

### Dati esistenti

Spese ricorrenti e spese di affitti_lungo sono state azzerate il
2026-11-12; quel che l'utente avrà inserito nel frattempo si migra (voce
dal tipo, quote dal responsabile). Le tabelle vecchie spariscono a fine
migrazione.

## Fasi

1. **Registro**: voci con natura, movimenti, quote per soggetto, scadenze,
   inserimento manuale, sezione nella scheda del bene; sostituisce le spese
   ricorrenti. Dopo la fase 2 dei beni (serve il riepilogo dei ruoli).
2. **Condominio**: spese del condominio ripartite sulle unità; sostituisce
   spese e ripartizioni di affitti_lungo.
3. **Riaddebiti e ricavi**: stato di recupero, pagina Riaddebiti, ricavi da
   affitti_lungo e affitti_brevi, conguaglio oneri accessori (con la fase 3
   dei beni, contratti su più beni).
4. **Contratto per i moduli**: `dati_beni`, `registra_calcolato`, voci dai
   manifest; primo modulo di calcolo da decidere (IMU è il candidato).

Effetto sulla spec dei beni: la fase 2 tiene il riepilogo "chi paga cosa";
i responsabili `USUFRUTTUARIO`/`NUDO_PROPRIETARIO` delle spese ricorrenti
non si fanno più lì, li sostituiscono le quote per ruolo di questa spec.

## Da verificare (agente esperto sull'Archivio Fiscale, poi professionista)

- Tabella oneri accessori del DM 16/01/2017 (all. D) voce per voce, e
  percentuali fisse (portineria, ascensore…), per il catalogo.
- TARI: soggetto passivo per locazioni oltre e sotto i sei mesi (L.
  147/2013), e caso dell'usufrutto.
- Contributo di bonifica con terreno in affitto agrario: chi lo sostiene.
- Ripartizione condominiale tra nudo proprietario e usufruttuario (disp.
  att. art. 67) e tra locatore e conduttore per le voci miste.
