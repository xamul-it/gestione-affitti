# Affitti Brevi - Guida Utente

**Versione:** 1.0
**Data:** 2025-12-28
**Modulo:** Gestione Affitti Brevi (Short-Term Rentals)

---

## Introduzione

Il modulo **Affitti Brevi** permette di gestire affitti turistici su più piattaforme (Booking.com, Airbnb, Vrbo) da un'unica interfaccia centralizzata.

### Funzionalità Principali

✅ **Calendario Multi-Piattaforma** - Visualizza tutte le prenotazioni in un'unica vista
✅ **Sincronizzazione iCal Automatica** - Importa automaticamente prenotazioni da Booking, Airbnb, Vrbo
✅ **Rilevamento Conflitti** - Identifica sovrapposizioni tra piattaforme
✅ **Calcolo Tassa di Soggiorno** - Calcolo automatico con 3 modalità (fisso, percentuale, scaglioni)
✅ **Gestione Scadenze** - Monitoraggio comunicazioni Polizia (24h) e report ISTAT mensili
✅ **Gestione Documenti** - Caricamento documenti per prenotazione

---

## 1. Configurazione Iniziale

### 1.1 Configurare i Calendari iCal

**Passo 1: Ottenere l'URL iCal dalle Piattaforme**

**Booking.com:**
1. Accedi al tuo account Booking.com Extranet
2. Vai su Alloggio → Calendario e Prezzi
3. Cerca "Esporta Calendario" o "iCal Link"
4. Copia l'URL del calendario (formato: `https://admin.booking.com/ical/...`)

**Airbnb:**
1. Accedi al tuo account Airbnb
2. Vai su Annunci → [Seleziona annuncio] → Disponibilità → Sincronizzazione calendari
3. Clicca su "Esporta calendario"
4. Copia l'URL del calendario (formato: `https://www.airbnb.com/calendar/ical/...`)

**Vrbo:**
1. Accedi al tuo account Vrbo
2. Vai su Calendario → Impostazioni Calendario
3. Cerca "Esporta Calendario" o "iCal Export"
4. Copia l'URL del calendario (formato: `https://www.vrbo.com/icalendar/...`)

**Passo 2: Aggiungere il Calendario nell'Applicazione**

1. Vai su **Affitti Brevi → Calendari iCal**
2. Clicca su **Nuovo Calendario**
3. Compila il form:
   - **Immobile**: Seleziona l'unità immobiliare
   - **Portale**: Scegli la piattaforma (Booking.com, Airbnb, Vrbo)
   - **URL iCal**: Incolla l'URL copiato
   - **Attivo**: Spunta per abilitare la sincronizzazione
4. Clicca **Salva**

**Nota:** Il sistema sincronizza automaticamente ogni 6 ore. La prima sincronizzazione avviene entro pochi minuti.

### 1.2 Configurare la Tassa di Soggiorno

**Prerequisito:** L'immobile deve avere un comune associato.

**Passo 1: Creare Configurazione Tassa**

1. Vai su **Affitti Brevi → Tasse di Soggiorno → Configurazioni**
2. Clicca su **Nuova Configurazione**
3. Compila il form:
   - **Comune**: Seleziona il comune dell'immobile
   - **Tipo Calcolo**: Scegli tra:
     - **FISSO**: Importo fisso per notte per ospite (es. €2,00/notte)
     - **PERCENTUALE**: Percentuale sul prezzo notte (es. 5%)
     - **SCAGLIONI**: Tariffe progressive per notte (es. prime 5 notti €2, poi €1)
   - **Data Inizio Validità**: Data di attivazione della tariffa
   - **Data Fine Validità**: (Facoltativo) Data di scadenza

**Esempio: Configurazione FISSO**
- Importo Fisso: €2,50
- Età Minima: 14 anni (under 14 esenti)
- Età Massima: (Nessuna)
- Notti Max Tassabili: 7 (dopo 7 notti, nessuna tassa aggiuntiva)

**Esempio: Configurazione SCAGLIONI**
1. Crea la configurazione base (tipo SCAGLIONI)
2. Clicca su **Gestisci Scaglioni**
3. Aggiungi scaglioni:
   - Notti 1-5: €2,00/notte
   - Notti 6-10: €1,50/notte
   - Notti 11+: €1,00/notte

4. Clicca **Salva**

**Nota:** Il sistema seleziona automaticamente la configurazione attiva per il comune al momento del check-in.

---

## 2. Gestione Quotidiana

### 2.1 Visualizzare il Calendario

1. Vai su **Affitti Brevi → Calendario Multi-Piattaforma**
2. Seleziona:
   - **Data Inizio**: Prima data da visualizzare
   - **Data Fine**: Ultima data da visualizzare
   - **Immobili**: (Facoltativo) Filtra per immobili specifici
3. Clicca **Carica Calendario**

**Legenda Visuale:**

**Colori Piattaforma:**
- 🔵 **Blu**: Booking.com
- 🔴 **Rosso**: Airbnb
- 🟢 **Verde**: Vrbo

**Stati Prenotazione:**
- **Badge Colorato Pieno**: PRENOTATO (es. "B" bianco su sfondo blu = Booking.com prenotato)
- **Badge Colorato Trasparente**: LIBERO (es. "A" nero su sfondo rosso chiaro = Airbnb libero)
- **Badge Barrato**: CHIUSO (es. "V̶" su verde = Vrbo chiuso per manutenzione)

**Esempio:**
- 15 Gennaio: "B" blu pieno → Booking.com prenotato
- 16 Gennaio: "A" rosso trasparente → Airbnb libero
- 17 Gennaio: "V̶" verde → Vrbo chiuso

### 2.2 Gestire i Conflitti

**Cosa sono i Conflitti?**
Un conflitto si verifica quando lo stesso immobile è prenotato su due piattaforme diverse per le stesse date (es. Booking.com E Airbnb per il 15-17 gennaio).

**Rilevare Conflitti:**
1. Vai su **Affitti Brevi → Calendario → Conflitti**
2. Il sistema mostra tutti i conflitti rilevati con:
   - Immobile coinvolto
   - Date sovrapposte
   - Prenotazioni in conflitto (codice, piattaforma, date)

**Risolvere un Conflitto:**
1. Clicca sul conflitto per vedere i dettagli
2. Verifica quale prenotazione è valida (controlla direttamente sulle piattaforme)
3. Per ogni prenotazione, scegli:
   - **MANTIENI**: Conferma che questa prenotazione è valida
   - **CANCELLA**: Marca come cancellata (la rimuove dal calendario)
4. Clicca **Risolvi Conflitto**

**Consiglio:** Disattiva il calendario iCal sulla piattaforma dove hai cancellato manualmente la prenotazione, altrimenti verrà reimportata alla prossima sincronizzazione.

### 2.3 Gestire Prenotazioni Manuali

**Quando Usare?**
- Prenotazione diretta (senza piattaforma)
- Prenotazione da piattaforma non supportata
- Correggere dati importati errati

**Creare una Prenotazione:**
1. Vai su **Affitti Brevi → Prenotazioni**
2. Clicca **Nuova Prenotazione**
3. Compila il form:
   - **Codice Prenotazione**: Identificativo univoco (es. "DIR-2025-001")
   - **Immobile**: Seleziona l'unità
   - **Portale Origine**: Scegli piattaforma (o "ALTRO" per prenotazioni dirette)
   - **Check-in**: Data arrivo
   - **Check-out**: Data partenza
   - **Numero Ospiti**: Totale ospiti
   - **Prezzo Totale**: Importo totale prenotazione
   - **Stato**: CONFERMATA, IN_ATTESA, CANCELLATA
4. Clicca **Salva**

**Nota:** Il calcolo della tassa di soggiorno avviene automaticamente al salvataggio.

### 2.4 Gestire Ospiti

**Aggiungere Ospiti a una Prenotazione:**
1. Vai su **Affitti Brevi → Prenotazioni**
2. Clicca sulla prenotazione
3. Nella sezione **Ospiti**, clicca **Aggiungi Ospite**
4. Compila:
   - **Nome e Cognome**
   - **Data di Nascita**: (Importante per tassa di soggiorno e comunicazioni Polizia)
   - **Codice Fiscale**: (Facoltativo ma consigliato per italiani)
   - **Documento**: Tipo e numero documento
   - **Capogruppo**: Spunta per l'ospite principale
5. Clicca **Salva**

**Nota:** Per le comunicazioni alla Polizia, è obbligatorio avere almeno il capogruppo con dati completi.

---

## 3. Tassa di Soggiorno

### 3.1 Calcolo Automatico

**Il calcolo avviene automaticamente quando:**
- Crei una nuova prenotazione
- Modifichi date o numero ospiti di una prenotazione esistente
- Aggiungi/rimuovi ospiti

**Visualizzare il Calcolo:**
1. Vai su **Affitti Brevi → Prenotazioni → [Seleziona prenotazione]**
2. Nella sezione **Tassa di Soggiorno**, vedi:
   - **Importo Totale**: Tassa calcolata
   - **Dettaglio Calcolo**: Breakdown del calcolo (notti tassabili, ospiti esenti, etc.)
   - **Configurazione Utilizzata**: Quale configurazione è stata applicata

**Esempio Dettaglio Calcolo (FISSO):**
```
Comune: Roma
Tipo Calcolo: FISSO
Importo Fisso: €2,50/notte
Notti Totali: 8
Notti Tassabili: 7 (max 7 notti per regolamento comunale)
Ospiti Totali: 4
Ospiti Esenti: 1 (under 14)
Ospiti Tassabili: 3

Calcolo: €2,50 × 7 notti × 3 ospiti = €52,50
```

### 3.2 Override Manuale

**Quando Usare?**
- Sconto applicato manualmente
- Errore nel calcolo automatico
- Esenzione speciale

**Applicare Override:**
1. Vai su **Affitti Brevi → Tasse → [Seleziona prenotazione]**
2. Clicca **Applica Override Manuale**
3. Compila:
   - **Nuovo Importo**: Importo corretto
   - **Motivo Override**: Spiegazione (es. "Sconto 50% per lungo soggiorno")
4. Clicca **Salva Override**

**Nota:** L'override sostituisce completamente il calcolo automatico. Per rimuoverlo, clicca **Rimuovi Override**.

### 3.3 Report per Comune

**Generare Report Mensile:**
1. Vai su **Affitti Brevi → Tasse → Report**
2. Seleziona:
   - **Mese**: Mese di riferimento
   - **Anno**: Anno di riferimento
   - **Comune**: Comune da rendicontare
3. Clicca **Genera Report**

**Il report include:**
- Totale tassa riscossa nel mese
- Numero prenotazioni
- Breakdown per immobile
- Dettaglio calcoli

**Formato Export:** PDF, Excel

---

## 4. Scadenze e Comunicazioni

### 4.1 Comunicazioni Polizia (Alloggiati Web)

**Obbligo Legale:** Entro 24 ore dal check-in, comunicare dati ospiti alla Questura.

**Scadenze Automatiche:**
Il sistema genera automaticamente una scadenza per ogni prenotazione confermata:
- **Data Scadenza**: Check-in + 24 ore
- **Tipo**: COMUNICAZIONE_POLIZIA
- **Stato**: DA_FARE → IN_SCADENZA (entro 7 giorni) → SCADUTA → COMPLETATA

**Gestire Comunicazione Polizia:**
1. Vai su **Affitti Brevi → Scadenze**
2. Filtra per **Tipo: COMUNICAZIONE_POLIZIA**
3. Clicca sulla scadenza per vedere i dettagli
4. Verifica che gli ospiti abbiano dati completi (documento, data nascita)
5. Clicca **Genera Comunicazione**
6. Il sistema crea un file con dati ospiti in formato Alloggiati Web
7. Vai su **Portale Alloggiati Web** della Questura
8. Carica il file generato
9. Torna nell'applicazione e clicca **Marca come Inviata**
10. Inserisci:
    - **Data Invio**: Data e ora invio
    - **Numero Protocollo**: (Se fornito dalla Questura)
11. Clicca **Salva**

**Badge Notifiche:**
- Un badge rosso appare nel menu quando ci sono comunicazioni in scadenza (entro 7 giorni)
- Il numero indica quante comunicazioni sono da completare

### 4.2 Report ISTAT

**Obbligo Legale:** Entro il 15 del mese successivo, inviare statistiche flussi turistici all'ISTAT.

**Scadenze Ricorrenti:**
Il sistema genera automaticamente una scadenza ogni mese:
- **Data Scadenza**: 15 del mese (es. 15 gennaio per dicembre)
- **Tipo**: REPORT_ISTAT
- **Ricorrente**: Sì (si rigenera ogni mese)

**Generare Report ISTAT:**
1. Vai su **Affitti Brevi → Scadenze**
2. Filtra per **Tipo: REPORT_ISTAT**
3. Clicca sulla scadenza (es. "Report ISTAT Dicembre 2025")
4. Clicca **Genera Report**
5. Seleziona:
   - **Mese**: Mese da rendicontare
   - **Anno**: Anno da rendicontare
6. Il sistema genera un file CSV/Excel con:
   - Numero arrivi
   - Numero partenze
   - Notti vendute
   - Breakdown per nazionalità ospiti
7. Scarica il file
8. Vai su **Portale ISTAT Turismo**
9. Carica i dati
10. Torna nell'applicazione e clicca **Marca come Completata**

### 4.3 Altre Scadenze

**Creare Scadenza Personalizzata:**
1. Vai su **Affitti Brevi → Scadenze**
2. Clicca **Nuova Scadenza**
3. Compila:
   - **Titolo**: Descrizione (es. "Rinnovo assicurazione immobile X")
   - **Tipo**: ALTRO
   - **Data Scadenza**: Data e ora
   - **Prenotazione**: (Facoltativo) Collega a prenotazione specifica
   - **Ricorrente**: Spunta se si ripete (es. ogni anno)
4. Clicca **Salva**

---

## 5. Gestione Documenti

### 5.1 Caricare Documenti

**Per Prenotazione:**
1. Vai su **Affitti Brevi → Prenotazioni → [Seleziona prenotazione]**
2. Nella sezione **Documenti**, clicca **Carica Documento**
3. Compila:
   - **Tipo Documento**: Contratto, Ricevuta, Documento Identità, Altro
   - **Descrizione**: Breve nota
   - **File**: Seleziona file (PDF, JPG, PNG, Excel, Word)
4. Clicca **Carica**

**Per Ospite:**
1. Vai su **Affitti Brevi → Prenotazioni → [Seleziona prenotazione] → Ospiti**
2. Clicca sull'ospite
3. Nella sezione **Documenti**, clicca **Carica Documento Identità**
4. Carica scansione fronte/retro documento

### 5.2 Visualizzare e Scaricare

1. Vai alla sezione **Documenti** dell'entità (prenotazione, ospite)
2. Clicca sul nome del documento per scaricarlo
3. Clicca sull'icona **Elimina** per rimuoverlo (richiede conferma)

---

## 6. FAQ

### 6.1 Sincronizzazione iCal

**Q: Quanto spesso si sincronizzano i calendari?**
A: Ogni 6 ore automaticamente. Puoi forzare una sincronizzazione manuale cliccando su "Sincronizza Ora" nella sezione Calendari iCal.

**Q: La sincronizzazione fallisce con errore "URL non raggiungibile"**
A: Verifica che l'URL iCal sia corretto e attivo. Alcune piattaforme rigenerano l'URL periodicamente - aggiorna l'URL nell'applicazione.

**Q: Le prenotazioni non compaiono dopo la sincronizzazione**
A: Controlla lo stato della sincronizzazione nella lista Calendari iCal. Se mostra "ERRORE", clicca per vedere il messaggio di errore dettagliato.

**Q: Il prezzo non viene importato correttamente**
A: Il sistema estrae il prezzo dal campo DESCRIPTION dell'iCal. Se il formato è non standard, potrebbe fallire. In questo caso, modifica manualmente il prezzo nella prenotazione.

### 6.2 Calendario

**Q: Come blocco un periodo per manutenzione?**
A: Vai su Affitti Brevi → Blocchi Calendario → Nuovo Blocco. Seleziona immobile, date, tipo blocco (MANUTENZIONE, PULIZIA, ALTRO), e piattaforma (o TUTTI per bloccare su tutte).

**Q: Il calendario è lento con molti immobili**
A: Il calendario è ottimizzato con cache di 1 ora. Se hai più di 50 immobili, considera di filtrare per specifici immobili invece di visualizzare tutto.

### 6.3 Tassa di Soggiorno

**Q: La tassa non viene calcolata**
A: Verifica che:
1. L'immobile abbia un comune associato
2. Esista una configurazione tassa attiva per quel comune alla data del check-in
3. La prenotazione abbia date e numero ospiti compilati

**Q: Come esentare un ospite dalla tassa?**
A: Inserisci la data di nascita dell'ospite. Se ha età fuori dal range configurato (es. under 14), verrà automaticamente escluso dal calcolo.

**Q: Posso avere configurazioni diverse per stagioni diverse?**
A: Sì. Crea più configurazioni con date validità diverse (es. Alta Stagione giugno-agosto, Bassa Stagione resto anno).

### 6.4 Scadenze

**Q: Come disabilito le scadenze automatiche per comunicazioni Polizia?**
A: Le scadenze sono generate automaticamente per conformità legale. Se non vuoi usarle, puoi semplicemente ignorarle - non influenzano altre funzionalità.

**Q: Posso modificare la scadenza di 24h per comunicazioni Polizia?**
A: No, è un obbligo legale fissato. Tuttavia, puoi spostare manualmente la data di una scadenza specifica se necessario (es. per festivi).

### 6.5 Documenti

**Q: Quale formato file posso caricare?**
A: PDF, JPG, PNG, JPEG, DOC, DOCX, XLS, XLSX. Dimensione massima: 10 MB per file.

**Q: Dove vengono salvati i documenti?**
A: I file sono salvati in `backend/storage/` sul server. Ogni tenant ha una directory separata per isolamento dati.

---

## 7. Best Practices

### 7.1 Setup Iniziale

1. **Configura tutti i calendari iCal subito** - Evita inserimenti manuali
2. **Configura tasse di soggiorno prima della stagione** - Evita ricalcoli retroattivi
3. **Testa con una prenotazione di prova** - Verifica che tutto funzioni correttamente

### 7.2 Gestione Quotidiana

1. **Controlla il calendario ogni mattina** - Rileva conflitti tempestivamente
2. **Gestisci le scadenze appena appaiono** - Non aspettare l'ultimo giorno
3. **Verifica comunicazioni Polizia entro 12h dal check-in** - Hai solo 24h totali
4. **Backup documenti importanti** - Scarica periodicamente documenti critici

### 7.3 Fine Mese

1. **Genera report ISTAT entro il 10** - Hai tempo fino al 15 ma meglio anticipare
2. **Verifica tutte le tasse calcolate** - Controllo qualità prima di inviare al comune
3. **Archivia comunicazioni Polizia completate** - Puoi eliminarle dopo 1 anno

---

## 8. Supporto

### Segnalazione Problemi

Se riscontri errori o malfunzionamenti:

1. **Raccogli informazioni:**
   - Cosa stavi cercando di fare?
   - Quale errore è apparso?
   - Screenshot (se possibile)

2. **Controlla i log:**
   - Backend: `backend/logs/`
   - Browser: Console (F12)

3. **Contatta il supporto tecnico** con tutte le informazioni raccolte

### Richieste di Funzionalità

Per richiedere nuove funzionalità o miglioramenti:
- Descrivi il caso d'uso
- Spiega come ti aiuterebbe
- Fornisci esempi concreti

---

## 9. Glossario

**iCal**: Formato standard per calendari (RFC 5545)
**Portale Origine**: Piattaforma di prenotazione (Booking.com, Airbnb, Vrbo)
**Check-in**: Data arrivo ospiti
**Check-out**: Data partenza ospiti
**Sovrapposizione**: Stesso immobile prenotato su 2+ piattaforme per stesse date
**Tassa di Soggiorno**: Imposta comunale sui pernottamenti turistici
**Alloggiati Web**: Sistema Polizia per comunicazione dati ospiti
**ISTAT**: Istituto Nazionale di Statistica (richiede report flussi turistici)
**Scaglione**: Fascia di notti con tariffa differenziata (es. 1-5 notti, 6-10 notti)
**Override**: Sostituzione manuale di un calcolo automatico
**Capogruppo**: Ospite principale responsabile della prenotazione

---

## 10. Changelog

### Versione 1.0 (2025-12-28)
- Prima release completa del modulo
- Supporto Booking.com, Airbnb, Vrbo
- Calcolo tassa di soggiorno (3 modalità)
- Gestione scadenze automatiche
- Sistema documenti

---

**Fine della Guida Utente**

Per domande o supporto, contatta l'amministratore di sistema.
