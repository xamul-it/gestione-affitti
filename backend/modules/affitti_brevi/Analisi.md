# Analisi Funzionale (NON tecnica)
## Modulo Anagrafiche + Modulo Property Management – Affitti Brevi

**Versione:** 0.1 (bozza)  
**Data:** 12 gennaio 2026  
**Obiettivo del documento:** descrivere requisiti funzionali, dati e comportamenti attesi per (i) Modulo Anagrafiche, (ii) Modulo Property Management, con dettaglio sul **Calendario Unificato** (cap. 3.1) e sui flussi check-in/check-out per **tassa di soggiorno** e **finalità di polizia**, inclusa la **schedulazione** delle comunicazioni obbligatorie (cap. 4.1).

---

## Indice
1. Scopo e perimetro  
2. Attori e ruoli  
3. Modulo Anagrafiche (funzioni e dati messi a disposizione)  
4. Modulo Property Management (funzioni e dati messi a disposizione)  
5. **Calendario Unificato** (dettaglio cap. 3.1)  
6. Prenotazioni, Check-in/Check-out e Tassa di Soggiorno (dettaglio cap. 3.3)  
7. **Comunicazioni obbligatorie e schedulazione attività** (dettaglio cap. 4.1)  
8. Capitoli fuori perimetro / lasciati vuoti (placeholder)

---

## 1. Scopo e perimetro

### 1.1 In perimetro
- Definizione dei dati e delle funzioni **esposte** da:
  - Modulo **Anagrafiche**
  - Modulo **Property Management**
- Calendario Unificato per appartamento:
  - **un solo calendario per appartamento**, che **aggrega** i dati di tutti i canali
  - in **un’unica videata** visibilità dello stato **per canale** (libero / prenotato / chiuso / …) con **convenzioni colori e simboli**
  - **non** richiesto overbooking
  - **non** richieste chiusure tecniche (interne)
- Gestione check-in/check-out per:
  - calcolo **tassa di soggiorno**
  - attivazione **notifiche** per acquisizione **numero ospiti** e **documenti identità** (finalità di polizia) all’inizio di un’occupazione
- Schedulazione attività per **comunicazioni obbligatorie** (cap. 4.1)

### 1.2 Fuori perimetro (per ora)
- 3.2 Pricing / Revenue management (esplicitamente non richiesto)
- Overbooking
- Chiusure tecniche interne (blocchi manutenzione, ecc.)
- Contrattualistica e template legali (placeholder)
- Contabilità, fiscalità e rendicontazione avanzata (placeholder)

---

## 2. Attori e ruoli

| Ruolo | Descrizione | Permessi chiave (alto livello) |
|---|---|---|
| Amministratore | Configura sistema e autorizzazioni | Setup canali, template, schedulazioni, policy |
| Property Manager | Gestione operativa immobili e prenotazioni | Calendario, prenotazioni, check-in/out, task |
| Operatore Front Desk | Supporto check-in/out e raccolta dati | Inserimento ospiti/documenti, verifica completamento |
| Proprietario | Visione performance e stato | Lettura calendario e report (se previsto) |
| Ospite (self-service) | Compila dati richiesti | Inserimento dati soggiorno e documenti (tramite link) |

---

## 3. Modulo Anagrafiche – Funzioni e dati messi a disposizione

### 3.1 Entità anagrafiche (dati gestiti)
**A. Soggetti**
- **Persona fisica**
  - Dati base: nome, cognome, data/nascita, luogo/nazione, cittadinanza, sesso (se richiesto), contatti
  - Residenza/domicilio (indirizzi strutturati)
  - Identificativi: CF (se disponibile), estremi documento
  - Consensi privacy / informative (stato, data, fonte)
- **Persona giuridica**
  - Ragione sociale, P.IVA/CF, sede legale, contatti
  - Referenti (collegamento a persone fisiche)

**B. Documenti di identità (associati a persona fisica)**
- Tipologia documento (CI, passaporto, patente, altro)
- Numero documento, ente rilascio, data rilascio/scadenza, nazionalità
- Immagini/scan (se previsto) e stato verifica (non verificato / verificato / scaduto)

**C. Profili/ruoli anagrafici (relazioni)**
- Proprietario, gestore, ospite, referente aziendale, contatto emergenza
- Relazioni: un soggetto può avere più ruoli su più immobili/contratti

**D. Dati di pagamento (se rilevanti)**
- IBAN (per proprietari/gestori), preferenze di pagamento (opzionale)

---

### 3.2 Funzioni del modulo Anagrafiche
**Gestione anagrafiche**
- Creazione / modifica / consultazione / disattivazione (non cancellazione fisica di default)
- Ricerca avanzata (nome, documento, email, telefono, CF, ecc.)
- Deduplicazione assistita (segnalazione possibili duplicati; merge con tracciatura)

**Gestione documenti**
- Inserimento estremi documento
- Scadenziario documenti (alert scadenza)
- Gestione allegati (se previsto dal sistema) e audit delle modifiche

**Consensi e compliance**
- Registrazione presa visione privacy/informative (data, canale, versione)
- Storico consensi (immutabile)

**Esposizione dati ad altri moduli**
- Messa a disposizione di:
  - schede soggetto
  - documenti e stato verifica
  - recapiti e indirizzi
  - ruolo/relazione con immobile/prenotazione

---

### 3.3 Dati “messi a disposizione” (output funzionale del modulo Anagrafiche)
Il modulo deve rendere disponibili agli altri moduli (in lettura e/o scrittura secondo ruoli):
- Identità soggetti (PF/PG) e recapiti
- Documenti di identità (metadati + eventuali allegati) e stato completezza
- Relazioni soggetto–immobile (proprietario/gestore) e soggetto–prenotazione (ospite)
- Stato compliance (consensi, informative)

---

## 4. Modulo Property Management – Funzioni e dati messi a disposizione

### 4.1 Entità gestite (dati)
**A. Portafoglio immobiliare**
- Struttura (es. “edificio/complesso”) → **appartamenti/unità**
- Caratteristiche unità: posti letto, indirizzo, dotazioni (minimo), regole casa (placeholder)
- Stato unità: attiva / sospesa (no “chiusura tecnica” interna)

**B. Canali e mapping**
- Canali (Airbnb, Booking, diretto, ecc.)
- Identificativo unità per canale (mapping univoco)
- Parametri di sincronizzazione calendario per canale (import)

**C. Prenotazioni e soggiorni**
- Prenotazione (per canale): date, stato, codice prenotazione canale, importi (se disponibili)
- Soggiorno operativo (derivato): check-in/check-out, numero ospiti, dati tassa, stato adempimenti (polizia/comune)

**D. Task operativi**
- Raccolta dati ospiti/documenti
- Comunicazioni obbligatorie (schedulate)
- Reminder e solleciti

---

### 4.2 Funzioni del modulo Property Management
**Gestione immobili/unità**
- Creare/aggiornare unità e attributi operativi
- Associare proprietario/gestore (tramite modulo Anagrafiche)
- Abilitare/disabilitare unità (sospensione)

**Gestione canali**
- Configurazione canali supportati
- Associazione unità↔canale (mapping)
- Import disponibilità/prenotazioni dal canale (sincronizzazione calendario)

**Gestione calendario (vedi cap. 5)**
- Vista unica per appartamento che aggrega canali
- Evidenza stato per canale nella stessa videata

**Gestione prenotazioni**
- Consultazione dettaglio prenotazione (dati canale + dati operativi)
- Allineamento stati (prenotato/cancellato/modificato)
- Gestione conflitti (senza overbooking): segnalazione e workflow di risoluzione

**Gestione check-in/check-out e dati soggiorno (vedi cap. 6)**
- Raccolta numero ospiti e documenti
- Supporto calcolo tassa soggiorno
- Notifiche automatiche a inizio occupazione

**Schedulazione adempimenti (vedi cap. 7)**
- Pianificazione, esecuzione, log e controlli scadenze

---

### 4.3 Dati “messi a disposizione” (output funzionale del Property Management)
- Calendario aggregato per unità (con dettaglio canali)
- Prenotazioni e soggiorni (stato, date, canale, codice, occupazione)
- Stato completezza dati (ospiti/documenti) e audit trail
- Dati per tassa di soggiorno (base imponibile, esenzioni, conteggi per notte/ospite, output per Comune)
- Registro comunicazioni obbligatorie (cosa, quando, esito, evidenze)

---

## 5. Calendario Unificato – Dettaglio (Cap. 3.1)

### 5.1 Obiettivo della videata
In **un’unica videata** l’operatore deve:
- selezionare un periodo (settimana/mese)
- vedere, **per ciascun appartamento**, **un solo calendario** che **aggrega** tutti i canali
- vedere **per ciascun canale** lo **stato** sul calendario (libero/prenotato/chiuso/…)
- aprire dettagli prenotazione e azioni operative (check-in/out, richiesta dati, ecc.)

**Vincoli richiesti**
- Overbooking: **NON** previsto (eventuali sovrapposizioni = conflitto da risolvere)
- Chiusure tecniche interne: **NON** previste (non esistono blocchi manutentivi gestiti internamente)

---

### 5.2 Stati e convenzioni visive (colori + simboli)

#### A. Stato per canale (visualizzato nella cella giorno)
Ogni cella giorno dell’appartamento deve poter contenere **indicatori per canale** (badge/marker).

**Canali (esempio, configurabili):**
- Airbnb → **Rosso** + simbolo **A**
- Booking → **Blu** + simbolo **B**
- Diretto → **Verde** + simbolo **D**

**Stati minimi per canale**
- **Libero**: marker contorno (solo bordo), senza riempimento
- **Prenotato**: marker pieno (riempito), con icona “●”
- **Chiuso (non disponibile dal canale)**: marker con **X**
  - Nota: “chiuso” qui significa “non disponibile secondo il canale”; non è una chiusura tecnica interna.

**Legenda (da rendere sempre visibile nella videata)**
- A rosso / B blu / D verde = canale
- ● = prenotato  
- X = chiuso/non disponibile  
- bordo = libero

#### B. Stato aggregato dell’appartamento (riassunto nella cella)
Oltre ai marker per canale, la cella deve avere uno **stato di sintesi**:
- **Occupato**: se esiste almeno una prenotazione confermata su almeno un canale
- **Libero**: se tutti i canali risultano liberi
- **Non disponibile**: se tutti i canali risultano chiusi/non disponibili
- **Conflitto**: se esistono sovrapposizioni tra canali (prenotazioni concorrenti)

**Conflitto**: evidenziare con simbolo **!** e bordo cella “alert”; click apre pannello risoluzione.

---

### 5.3 Layout funzionale della videata (descrizione)
**Header / Filtri**
- Selettore periodo: mese / settimana / intervallo custom
- Filtro: struttura, città, proprietario/gestore (opzionale)
- Ricerca appartamento per nome/codice
- Toggle: “Mostra dettagli canali” (di default ON, perché requisito “per ciascun canale”)

**Corpo – Calendario a griglia**
- Colonna sinistra: elenco appartamenti (nome, icone canali attivi, indicatori di alert)
- Griglia giorni: una riga per appartamento, colonne per giorno
- In ogni cella:
  - stato aggregato (sfondo o bordo)
  - marker per canale (A/B/D) con stato (bordo / pieno ● / X)

**Pannello laterale (drawer)**
- Click su una cella o su marker canale apre:
  - dettaglio prenotazione (se presente) o dettaglio disponibilità
  - azioni: “Apri soggiorno”, “Richiedi dati ospiti”, “Verifica documenti”, “Vai a check-in/out”

---

### 5.4 Regole di aggregazione (senza overbooking)
- Se un canale indica prenotazione e un altro indica libero:
  - stato aggregato = **Occupato**
- Se più canali indicano prenotazioni sovrapposte nello stesso intervallo:
  - stato aggregato = **Conflitto**
  - azione richiesta: risoluzione manuale (definizione del “soggiorno valido”)
- Se tutti i canali indicano chiuso/non disponibile:
  - stato aggregato = **Non disponibile**
- Se tutti i canali indicano libero:
  - stato aggregato = **Libero**

---

### 5.5 Comportamenti attesi
- Navigazione rapida mese↔settimana
- Evidenza “oggi”
- Tooltip su marker: canale, stato, codice prenotazione, ospite (se noto)
- Evidenza “dati mancanti”:
  - icona “documento” o “ospiti” se prenotazione prossima o iniziata con dati incompleti

---

## 6. Prenotazioni, Check-in/Check-out e Tassa di Soggiorno – Dettaglio (Cap. 3.3)

### 6.1 Obiettivo
- Gestire **inizio e fine occupazione** per abilitare:
  1) calcolo **tassa di soggiorno**
  2) raccolta **numero ospiti** e **documenti** per finalità di polizia
  3) tracciamento stato “compliance” del soggiorno

---

### 6.2 Dati richiesti al check-in (minimi)
Per ogni soggiorno:
- Data/ora check-in (eventuale) e check-out
- Numero ospiti (totale + eventuale dettaglio adulti/minori)
- Elenco ospiti nominativi (minimo: nome/cognome, data nascita, cittadinanza)
- Documento identità per ciascun ospite (estremi; allegato se previsto)
- Eventuali esenzioni tassa di soggiorno (categoria + motivazione)

---

### 6.3 Attivazione notifica a inizio occupazione (requisito chiave)
**Trigger funzionale**
- Quando il calendario indica **inizio occupazione** (primo giorno di prenotazione / check-in previsto), il sistema deve:
  - creare/attivare una **richiesta dati soggiorno**
  - inviare una **notifica** tramite le funzioni di piattaforma

**Destinatari notifiche (configurabili)**
- Primario: Property Manager / Operatore
- Opzionale: ospite (self-service) tramite link di compilazione

**Contenuto minimo notifica**
- Identificativo appartamento
- Date soggiorno
- Azione richiesta: “Inserire numero ospiti e documenti”
- Scadenza: “entro X ore dal check-in” (configurabile)
- Stato attuale: incompleto/completo

**Solleciti**
- Reminder automatici fino a completamento:
  - T0 (inizio occupazione)
  - T+N ore (1° sollecito)
  - T+M ore (2° sollecito)
- Escalation a Admin se non completato entro soglia (configurabile)

---

### 6.4 Calcolo tassa di soggiorno (supporto dati)
Il modulo deve consentire:
- configurazione parametri per Comune (placeholder, configurabile):
  - tariffa per notte/persona o per notte/unità
  - massimali notti
  - categorie esenzione/riduzione
- calcolo per soggiorno:
  - notti imponibili
  - ospiti imponibili
  - importo totale
- output:
  - prospetto per periodo (mensile) e dettaglio per soggiorno

---

### 6.5 Stati del soggiorno (funzionali)
- **Creato** (da sincronizzazione canale o inserimento manuale)
- **In attesa dati ospiti/documenti**
- **Dati completi**
- **Comunicazioni inviate** (polizia / comune) – vedi cap. 7
- **Chiuso** (post check-out, con consuntivo tassa)

---

## 7. Comunicazioni obbligatorie e schedulazione attività – Dettaglio (Cap. 4.1)

### 7.1 Obiettivo
Garantire che le comunicazioni obbligatorie siano:
- pianificate (schedulate)
- tracciate (log)
- verificabili (evidenze/esiti)
- sollecitate in caso di mancato adempimento

---

### 7.2 Tipologie di attività schedulabili (macro-categorie)
> Nota: l’elenco è funzionale e **configurabile** in base a Comune/Regione e modello operativo.

1) **Comunicazioni di pubblica sicurezza (Alloggiati)**
- Attività: invio dati ospiti per soggiorni iniziati nel periodo
- Vincolo: dipende dal completamento dati ospiti/documenti

2) **Imposta/tassa di soggiorno**
- Attività: generazione prospetto e/o invio dichiarazione periodica
- Periodicità: mensile/trimestrale (configurabile)

3) **Codici/adempimenti identificativi (CIR/CIN o equivalenti)**
- Attività: verifica presenza codice in annunci e anagrafiche immobile (controllo interno)
- Periodicità: settimanale/mensile (configurabile)

---

### 7.3 Motore di schedulazione (requisiti funzionali)
Per ogni attività schedulata:
- Nome attività e tipologia
- Periodicità (giornaliera/settimanale/mensile) e orario
- Ambito: struttura / appartamenti / canali
- Pre-condizioni (es. “dati ospiti completi”)
- Output atteso (report, invio, export, checklist)

**Stati attività**
- Pianificata
- In esecuzione
- Completata
- Fallita / Bloccata (con motivo)
- Richiede intervento (es. dati mancanti)

**Log e audit**
- Data/ora esecuzione
- Soggiorni inclusi/esclusi + motivazione (es. dati incompleti)
- Operatore responsabile (se intervento manuale)
- Evidenza allegabile (protocollo, ricevuta, file)

**Notifiche**
- Notifica di “attività in scadenza”
- Notifica di “attività fallita”
- Notifica di “attività completata”

---

## 8. Capitoli fuori perimetro / lasciati vuoti (placeholder)

### 3.2 Pricing / Revenue Management
_TBD / Fuori perimetro per ora._

### 4.2 Contrattualistica (contratti, privacy estesa, regolamento casa)
_TBD / Fuori perimetro per ora._

### 5. Gestione economico-finanziaria (ricavi/costi/margini)
_TBD / Fuori perimetro per ora._

### 6. Fiscalità (cedolare, impresa, IVA, ecc.)
_TBD / Fuori perimetro per ora._

### 7. Reportistica e KPI avanzati (RevPAR, ADR, ecc.)
_TBD / Fuori perimetro per ora._

### 8. Integrazioni esterne (OTA API, pagamenti, PMS esterni)
_TBD / Fuori perimetro per ora._

---

## Allegato A – Requisiti sintetici “Must Have” (estratto)
- Un solo calendario per appartamento, aggregato su tutti i canali
- Visibilità stato per canale nella stessa videata con colori/simboli
- No overbooking: conflitti evidenziati e gestibili
- Notifica automatica a inizio occupazione per raccolta ospiti/documenti
- Dati check-in/out a supporto calcolo tassa soggiorno
- Schedulazione comunicazioni obbligatorie con log, esiti e solleciti
