# UAT Test Plan - Sistema Gestione Affitti Modulare

**Date:** 2025-11-28
**Scope:** User Acceptance Testing per validare il sistema modulare completo
**Environment:** Development (Backend: 192.168.1.2:8000, Frontend: localhost:3002)

## Test Objectives

1. ✅ Validare funzionalità core dell'applicazione
2. ✅ Validare sistema modulare (backend + frontend)
3. ✅ Validare Platform Services Layer
4. ✅ Validare dependency resolution
5. ✅ Testare scenari di errore realistici
6. ✅ Validare UX e workflow completi

## Test Scenarios

### TC-001: Core System - Gestione Unità Immobiliari
**Priority:** Critical
**User Story:** Come amministratore, voglio gestire le unità immobiliari

**Test Steps:**
1. Elencare tutte le unità immobiliari
2. Filtrare per stato (libero/occupato)
3. Cercare unità per indirizzo
4. Visualizzare dettaglio unità
5. Creare nuova unità (con errori comuni: campo mancante, formato errato)
6. Modificare unità esistente
7. Cancellare unità

**Expected Results:**
- CRUD operations funzionanti
- Validazione input corretta
- Messaggi errore comprensibili
- Performance accettabile (<2s per operazione)

### TC-002: Core System - Gestione Contratti
**Priority:** Critical
**User Story:** Come amministratore, voglio gestire i contratti di locazione

**Test Steps:**
1. Elencare contratti attivi
2. Creare contratto (collegare unità + affittuario)
3. Tentare creare contratto con dati invalidi
4. Visualizzare dettaglio contratto con relazioni
5. Generare scadenzario canoni
6. Modificare termini contratto
7. Chiudere contratto

**Expected Results:**
- Relazioni unità-affittuario corrette
- Calcolo canoni accurato
- Validazione business rules (es: unità già occupata)

### TC-003: Module System - Module Discovery
**Priority:** Critical
**User Story:** Il sistema deve scoprire automaticamente i moduli disponibili

**Test Steps:**
1. Verificare moduli installati nel database
2. Controllare log di discovery moduli
3. Verificare manifest parsing
4. Controllare validazione manifest
5. Testare modulo con manifest invalido

**Expected Results:**
- Moduli scoperti automaticamente all'avvio
- Manifest parsato correttamente
- Errori manifest loggati chiaramente

### TC-004: Module System - Dependency Resolution
**Priority:** High
**User Story:** I moduli devono caricarsi nel corretto ordine rispettando le dipendenze

**Test Steps:**
1. Verificare ordine di caricamento moduli
2. Controllare advanced_hello carica dopo hello_module
3. Testare circular dependency (creare modulo test)
4. Testare missing dependency
5. Testare version constraint mismatch

**Expected Results:**
- Load order corretto: hello_module → advanced_hello
- Circular dependencies rilevate e bloccate
- Missing dependencies segnalate
- Version constraints validati

### TC-005: Module System - Backend Integration
**Priority:** Critical
**User Story:** I moduli devono esporre API endpoints funzionanti

**Test Steps:**
1. Chiamare GET /api/v1/hello/demo
2. Chiamare GET /api/v1/hello/unita-demo
3. Chiamare GET /api/v1/hello/stats-demo
4. Verificare uso Platform Services
5. Testare error handling degli endpoints

**Expected Results:**
- Tutti gli endpoints rispondono 200 OK
- Dati ritornati corretti
- Platform Services utilizzati (non query dirette DB)
- Errori gestiti correttamente

### TC-006: Module System - Frontend Integration
**Priority:** Critical
**User Story:** I moduli devono registrare route e menu items automaticamente

**Test Steps:**
1. Verificare chiamata API /api/v1/modules/enabled
2. Controllare registrazione route in ModuleRegistry
3. Controllare menu item "Hello Demo" nel navbar
4. Navigare a /hello-demo
5. Verificare rendering HelloPage component
6. Controllare chiamate API dal component

**Expected Results:**
- API modules/enabled ritorna configurazione corretta
- Route /hello-demo accessibile
- Menu item visibile e cliccabile
- Component renderizza senza errori
- Dati caricati da backend

### TC-007: Platform Services - EntityService
**Priority:** High
**User Story:** I moduli devono usare EntityService per operazioni CRUD

**Test Steps:**
1. Verificare proprietari.py usa EntityService
2. Testare get_all con filtri
3. Testare get_or_404 (success + 404)
4. Testare create con validazione
5. Testare update parziale vs completo
6. Testare delete

**Expected Results:**
- Nessuna query diretta db.query() nei routers refactored
- Filtri applicati correttamente
- 404 restituito quando non trovato
- Validazione Pydantic funziona
- Update parziale preserva campi non modificati

### TC-008: Platform Services - SearchService
**Priority:** High
**User Story:** Il sistema deve fornire ricerca avanzata con filtri

**Test Steps:**
1. Ricerca full-text su unità immobiliari
2. Applicare filtri multipli (città, stato, superficie)
3. Testare operatori (eq, gt, like, in)
4. Testare aggregazioni (count, sum, avg)
5. Testare autocomplete
6. Testare performance con grandi dataset

**Expected Results:**
- Ricerca full-text trova risultati corretti
- Filtri combinati correttamente (AND logic)
- Operatori funzionano come atteso
- Aggregazioni accurate
- Autocomplete veloce (<500ms)

### TC-009: Error Handling & Edge Cases
**Priority:** High
**User Story:** Il sistema deve gestire gracefully errori e casi limite

**Test Steps:**
1. Tentare creare record con campo required mancante
2. Tentare update record inesistente
3. Tentare delete record con foreign key constraints
4. Inviare payload JSON malformato
5. Testare rate limiting (se presente)
6. Simulare database connection failure
7. Testare frontend con backend down
8. Testare modulo con component non registrato

**Expected Results:**
- Errori validazione ritornano 422 con dettagli
- 404 per record non trovati
- 400/409 per constraint violations
- 400 per JSON malformato
- Frontend mostra errori user-friendly
- Graceful degradation quando backend non disponibile

### TC-010: Performance & Scalability
**Priority:** Medium
**User Story:** Il sistema deve performare adeguatamente con dati realistici

**Test Steps:**
1. Caricare 1000 unità immobiliari
2. Testare tempo risposta listing
3. Testare ricerca full-text
4. Testare caricamento moduli con 10+ moduli
5. Misurare tempo bootstrap frontend
6. Controllare N+1 query problems

**Expected Results:**
- Listing <2s con 1000 records
- Ricerca <1s
- Caricamento moduli <5s
- Bootstrap frontend <3s
- No N+1 queries (verificare SQL logs)

### TC-011: User Experience - Workflow Completo
**Priority:** High
**User Story:** Come amministratore, voglio completare un workflow realistico

**Scenario:** Nuovo affitto
1. Creare nuovo proprietario
2. Creare nuova unità immobiliare collegata a proprietario
3. Creare nuovo affittuario
4. Creare contratto collegando unità e affittuario
5. Verificare unità risulta "occupato"
6. Generare primo canone
7. Registrare incasso
8. Navigare al modulo hello_module
9. Verificare statistiche aggiornate

**Expected Results:**
- Workflow fluido senza interruzioni
- Relazioni create correttamente
- Stati aggiornati automaticamente
- Modulo mostra dati aggiornati

### TC-012: Security & Validation
**Priority:** Critical
**User Story:** Il sistema deve prevenire input malevoli e validare correttamente

**Test Steps:**
1. Tentare SQL injection nei campi search
2. Tentare XSS in campi testo
3. Verificare escape HTML in output
4. Testare CSRF protection (se presente)
5. Verificare validazione lunghezza campi
6. Testare upload file (se permesso)

**Expected Results:**
- SQL injection bloccato
- XSS sanitizzato
- HTML escaped in rendering
- Validazione lunghezze applicata
- File upload validato (tipo, dimensione)

## Test Execution Order

1. **Phase 1 - Core System** (TC-001, TC-002)
   - Validare funzionalità base prima di testare moduli

2. **Phase 2 - Module System Backend** (TC-003, TC-004, TC-005)
   - Validare infrastruttura moduli backend

3. **Phase 3 - Module System Frontend** (TC-006)
   - Validare integrazione frontend-backend moduli

4. **Phase 4 - Platform Services** (TC-007, TC-008)
   - Validare abstraction layer

5. **Phase 5 - Error & Edge Cases** (TC-009, TC-012)
   - Validare robustezza sistema

6. **Phase 6 - Performance & UX** (TC-010, TC-011)
   - Validare performance e workflow completi

## Success Criteria

- ✅ 90%+ test cases PASS
- ✅ Critical bugs: 0
- ✅ High priority bugs: <3
- ✅ Performance targets raggiunti
- ✅ No security vulnerabilities rilevate
- ✅ UX workflow completabili senza blocchi

## Test Environment

- **Backend:** Python 3.x, FastAPI, SQLAlchemy
- **Frontend:** React, Vite
- **Database:** PostgreSQL
- **Modules:** hello_module, advanced_hello

## Tools

- curl / Postman per API testing
- Browser DevTools per frontend
- PostgreSQL client per database verification
- Backend logs: /tmp/backend.log
- Frontend logs: /tmp/frontend.log (+ browser console)
