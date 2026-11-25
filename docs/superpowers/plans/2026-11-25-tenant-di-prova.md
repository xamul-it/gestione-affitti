# Tenant di prova: creazione da zero e aggiornamento continuo — Plan

Richiesta dell'utente del 2026-11-25: due tenant di prova nel DB di sviluppo.

- **`tenant_test_nuovo`**: a ogni esecuzione si cancella e si ricrea da
  zero. Si installano tutti i moduli con i loro dati di esempio. Prova che
  un tenant nuovo si installa e che lo schema prodotto dalle migrazioni
  coincide con i modelli.
- **`tenant_test_evolutivo`**: si crea una volta con i dati di esempio e
  poi non si azzera più. A ogni esecuzione riceve solo le migrazioni nuove,
  come la produzione. I conteggi per tabella vengono confrontati con la
  fotografia dell'esecuzione precedente: una tabella che perde righe o
  sparisce è un errore. Anche qui si confronta lo schema con i modelli.

I dati di dominio restano condivisi nello schema `public`. I dati di esempio
sono quelli che ogni modulo deve fornire con `seed_test_data=True`: oggi ne
hanno solo anagrafica e immobili, e in parte. Un errore nei dati di esempio
deve far fallire l'installazione, non essere ignorato.

## Passi

1. `backend/scripts/tenant_prova.py nuovo|evolutivo|stato`:
   - creazione: riga `core_tenants`, schema, migrazioni core
     (`alembic -x schema=X`), moduli in ordine di dipendenza con
     `install_module_for_tenant(..., seed_test_data=True)`, accesso
     dell'utente admin;
   - confronto schema/modelli per le tabelle di ogni modulo installato:
     colonne mancanti o in più, nullabilità, indici con nome;
   - fotografia per `evolutivo` nella tabella `zz_prova_fotografia` dello
     schema: conteggi per tabella e versioni alembic;
   - uscita 0 = verde, 1 = rosso; resoconto breve.
2. Dati di esempio completi per immobili, sui beni:
   - terreno con nuda proprietà, usufrutto e conduttore;
   - abitazione con pertinenza;
   - fabbricato su particella;
   - spesa ricorrente;
   - assegnazione conduttore.

   Gli errori dei dati di esempio non vengono più ignorati.
3. Dati di esempio di `affitti_lungo`: affittuario, contratto, incasso,
   spesa. Poi `affitti_brevi` (canali già presenti: prenotazione,
   soggiorno, ospite) e `gestione_pec` (casella senza credenziali vere).
4. `scripts/verifica.sh migrazioni`, passo da eseguire quando il ramo ha una
   migrazione. I due schema di prova escono dal controllo "DB invariato"
   dei test.
5. Documentazione: `docs/piattaforma.md`, guida di sviluppo (pipeline:
   ogni migrazione passa da `tenant_prova.py`).

Vincoli: mai toccare `tenant_produzione`, `tenant_principale` e
`tenant_qa_test`. Lo script rifiuta qualunque schema che non inizia per
`tenant_test_`.

## Stato al 2026-11-25

Fatti i passi 1-5:
- `tenant_prova.py` con `nuovo`, `evolutivo` e `stato`, più il controllo di
  idempotenza dei dati di esempio;
- dati di esempio di immobili (beni), affitti_lungo, affitti_brevi e
  gestione_pec; i soggetti di esempio dell'anagrafica si creano una volta
  sola;
- `verifica.sh` esegue i tenant di prova;
- documentazione aggiornata.

Residui:
- Tabelle ancora senza dati di esempio (16):
  - piattaforma: `core_relazioni`, `core_scadenze`, `core_scadenza_log`,
    `core_scadenza_destinatari`, `core_notifiche`;
  - override di dominio: `anag_*_overrides`,
    `immo_tipologie_terreno_overrides`;
  - anagrafica: `anag_documenti`, `anag_documenti_files`,
    `anag_ruoli_azienda`;
  - immobili: `immo_variazioni_catastali`,
    `immo_tipo_immobile_categoria_map`;
  - esempio_componenti: `elementi_esempio`.
- 9 differenze note tra migrazioni e modelli (`DIFFERENZE_NOTE`): enum del
  modello salvati come testo, JSON/JSONB, timestamp. Da allineare con un
  intervento a parte.
- Le righe di prova aggiunte prima del marcatore "Dato di esempio" (15
  soggetti in più) restano nel tenant evolutivo: non danno fastidio.

Trovati dai tenant di prova e corretti nello stesso ramo:
- `esem_002`: nessuna migrazione creava `elementi_esempio` nei tenant
  (esisteva solo grazie al fallback dell'installatore, ora intercettato).
- anagrafica `2026112501`: in un tenant nuovo le tabelle documenti
  restavano `anag_*` (la rinomina core gira prima che esistano) e il
  codice, che usa `core_documenti`, non le trovava: i documenti di un tenant
  creato da zero non funzionavano.

Trovato e non corretto: i tenant esistenti (principale, produzione,
qa_test) non hanno 24 chiavi esterne che un tenant nuovo ha (spese,
ripartizioni, tecnici, PEC, ...). Da valutare con una migrazione apposta
dopo aver controllato che i dati le rispettino.
