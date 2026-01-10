# UAT Test Plan: Import Wizard Sistema

## Test Scenario 1: Import con Template Standard
**Obiettivo**: Verificare import usando template CSV standard

**Precondizioni**:
- Backend running su localhost:8000
- Frontend running su localhost:3000
- File: /tmp/test_immobili_template.csv

**Steps**:
1. Naviga a http://localhost:3000/immobili
2. Click "Unità Immobiliari" card
3. Click bottone "📥 Importa"
4. Verifica apertura ImportWizard
5. Step 1: Select "Usa template standard"
6. Upload file /tmp/test_immobili_template.csv
7. Click "Analizza File"
8. Verifica che vada a Step 2 Mapping
9. Verifica mappatura automatica corretta
10. Click "Anteprima"
11. Verifica Step 3 Preview mostra 5 righe valide
12. Click "Importa"
13. Verifica Step 4 Results mostra successo
14. Click "Chiudi"
15. Verifica refresh lista con nuove unità

**Expected Results**:
- 5 righe importate con successo
- 0 errori
- Lista aggiornata con nuove unità immobiliari

---

## Test Scenario 2: Import CSV Generico con Mappatura
**Obiettivo**: Testare mappatura automatica su CSV con nomi colonne diversi

**Precondizioni**:
- Backend running
- Frontend running
- File: /tmp/test_immobili_generic.csv

**Steps**:
1. Click bottone "📥 Importa"
2. Step 1: Select "Carica CSV generico"
3. Upload /tmp/test_immobili_generic.csv
4. Click "Analizza File"
5. Step 2: Verifica mappatura suggerita:
   - "Indirizzo Completo" → "indirizzo" ✓
   - "Comune" → "citta" ✓
   - "Superficie" → "superficie_mq" ✓
   - "N. Vani" → "locali" ✓
6. Modifica mapping manuale se necessario
7. Spunta "Salva questa configurazione"
8. Inserisci nome: "Import Test Agenzia"
9. Click "Anteprima"
10. Step 3: Verifica 6 righe valide
11. Click "Importa"
12. Step 4: Verifica successo import + configurazione salvata
13. Click "Chiudi"

**Expected Results**:
- 6 righe importate
- Configurazione "Import Test Agenzia" salvata
- Mappatura corretta applicata

---

## Test Scenario 3: Gestione Errori di Validazione
**Obiettivo**: Verificare preview e gestione errori

**Precondizioni**:
- File: /tmp/test_immobili_errors.csv (con errori intenzionali)

**Steps**:
1. Click "📥 Importa"
2. Upload /tmp/test_immobili_errors.csv
3. Click "Analizza File"
4. Verifica mappatura automatica
5. Click "Anteprima"
6. Step 3: Verifica statistiche:
   - Total rows: 5
   - Valid rows: 3
   - Invalid rows: 2
7. Verifica errori mostrati per righe 2 e 3:
   - Riga 2: indirizzo mancante
   - Riga 3: superficie negativa
8. Verifica checkbox "Salta errori" è selezionato
9. Click "Importa"
10. Verifica import di solo 3 righe valide
11. Verifica report errori dettagliato

**Expected Results**:
- 3 righe valide importate
- 2 righe con errori saltate
- Errori chiaramente documentati

---

## Test Scenario 4: Riutilizzo Configurazione Salvata
**Obiettivo**: Testare caricamento e riuso configurazione

**Precondizioni**:
- Configurazione "Import Test Agenzia" salvata (da Scenario 2)
- File nuovo con stesso formato

**Steps**:
1. Click "📥 Importa"
2. Step 1: Select "Carica configurazione salvata"
3. Dropdown: Select "Import Test Agenzia"
4. Upload nuovo file CSV
5. Click "Analizza File"
6. Step 2: Verifica mappatura caricata automaticamente
7. Verifica nessuna modifica necessaria
8. Click "Anteprima"
9. Verifica validazione
10. Click "Importa"
11. Verifica successo

**Expected Results**:
- Mappatura applicata automaticamente dalla config salvata
- Import senza necessità di ri-mappare campi

---

## Test Scenario 5: UI/UX Validation
**Obiettivo**: Verificare usabilità e design

**Checks**:
- [ ] Wizard responsive (mobile + desktop)
- [ ] Step indicators chiari e funzionanti
- [ ] Bottoni Back/Next funzionano correttamente
- [ ] Drag-and-drop upload funziona
- [ ] File upload con click funziona
- [ ] Colori mappatura (verde/giallo/rosso) chiari
- [ ] Errori ben formattati e leggibili
- [ ] Loading states durante operazioni async
- [ ] Animazioni smooth
- [ ] Nessun errore console browser
- [ ] Accessibilità keyboard navigation

---

## Test Scenario 6: Edge Cases
**Obiettivo**: Testare casi limite

**Tests**:
1. Upload file non-CSV (dovrebbe rifiutare)
2. Upload CSV vuoto (dovrebbe gestire)
3. Upload CSV con solo header (nessuna riga dati)
4. CSV con encoding diverso (UTF-8, Latin-1)
5. CSV molto grande (>100 righe)
6. Campi obbligatori non mappati (warning rosso)
7. Cancellazione durante processo (bottone Annulla)
8. Network error durante import (gestione errore)

---

## Success Criteria

**Tutti i test devono passare con**:
- ✅ 0 errori JavaScript console
- ✅ 0 errori backend 500
- ✅ UI responsive e pulita
- ✅ Dati importati correttamente nel database
- ✅ Configurazioni salvate e riutilizzabili
- ✅ Errori gestiti gracefully con messaggi chiari

