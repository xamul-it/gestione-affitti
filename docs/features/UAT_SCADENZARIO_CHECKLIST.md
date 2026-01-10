# UAT Scadenzario - Checklist Testing

**Versione:** 1.0.0
**Data:** 10 Dicembre 2025
**Ambiente Test:** http://192.168.1.2:3000

---

## 🎯 Obiettivo UAT

Verificare la funzionalità completa del Sistema Scadenzario in ambiente di test, garantendo:
- Corretto funzionamento di tutti i componenti
- Isolamento multi-tenant
- Usabilità e UX
- Performance accettabili

---

## ✅ Pre-Requisiti

- [ ] Backend in esecuzione su `http://192.168.1.2:8000`
- [ ] Frontend in esecuzione su `http://192.168.1.2:3000`
- [ ] Database con almeno 2 tenant (tenant_test, tenant_produzione)
- [ ] Almeno 2 utenti test
- [ ] Almeno 1 contratto test
- [ ] Almeno 1 immobile test

---

## 📝 Test Cases

### TC-001: Badge TopBar

**Obiettivo:** Verificare visualizzazione e funzionalità badge scadenze in TopBar

**Pre-condizioni:**
- Utente loggato
- Almeno 1 scadenza attiva

**Steps:**
1. [ ] Accedere all'applicazione
2. [ ] Verificare badge visibile in TopBar (tra search e user menu)
3. [ ] Verificare count corretto
4. [ ] Verificare colore badge (verde/giallo/rosso)
5. [ ] Click su badge
6. [ ] Verificare apertura NotifichePanel

**Expected Result:**
- Badge mostra count corretto
- Colore appropriato allo stato scadenze
- Click apre pannello notifiche

**Status:** ⬜ Not Tested | ✅ Passed | ❌ Failed

**Notes:**
```
[Inserire eventuali note]
```

---

### TC-002: Pannello Notifiche

**Obiettivo:** Verificare pannello notifiche dropdown

**Pre-condizioni:**
- Utente loggato
- Scadenze di test: 1 scaduta, 1 oggi, 1 domani, 1 settimana prossima

**Steps:**
1. [ ] Click su badge TopBar
2. [ ] Verificare apertura pannello
3. [ ] Verificare raggruppamento scadenze:
   - [ ] Sezione "Scadute" con 1 item
   - [ ] Sezione "Oggi" con 1 item
   - [ ] Sezione "Domani" con 1 item
   - [ ] Sezione "Questa Settimana" con 1 item
4. [ ] Click su una scadenza
5. [ ] Verificare apertura modal dettagli
6. [ ] Click su ✅ (completa) per una scadenza
7. [ ] Verificare scadenza completata
8. [ ] Click su ⏭️ (posticipa) per una scadenza
9. [ ] Inserire nuova data
10. [ ] Verificare scadenza posticipata
11. [ ] Click "Vedi tutte le scadenze"
12. [ ] Verificare redirect a `/test/scadenze`

**Expected Result:**
- Pannello si apre correttamente
- Scadenze raggruppate per tempo
- Quick actions funzionano
- Modal si apre correttamente

**Status:** ⬜ Not Tested | ✅ Passed | ❌ Failed

**Notes:**
```
[Inserire eventuali note]
```

---

### TC-003: Pagina Test Scadenze

**Obiettivo:** Verificare funzionalità pagina test completa

**Pre-condizioni:**
- Utente loggato

**Steps:**

**3.1 Statistiche:**
1. [ ] Navigare a `/test/scadenze`
2. [ ] Verificare pannello statistiche visibile
3. [ ] Verificare count "Attive"
4. [ ] Verificare count "Scadute"
5. [ ] Verificare count "Alta Priorità"

**3.2 Form Creazione TODO:**
1. [ ] Click "➕ Nuova Scadenza"
2. [ ] Verificare apertura form
3. [ ] Selezionare checkbox "Standalone TODO"
4. [ ] Compilare:
   - Titolo: "Test TODO UAT"
   - Descrizione: "Test descrizione"
   - Data: domani
   - Priorità: ALTA
5. [ ] Click "✅ Crea Scadenza"
6. [ ] Verificare messaggio successo
7. [ ] Verificare TODO appare nella lista

**3.3 Form Creazione Entity-Linked:**
1. [ ] Click "➕ Nuova Scadenza"
2. [ ] Deselezionare checkbox "Standalone TODO"
3. [ ] Compilare:
   - Modulo: "affitti_lungo"
   - Entity Type: "contratto"
   - Entity ID: "1"
   - Titolo: "Test Scadenza Contratto"
   - Data: oggi + 7 giorni
   - Priorità: MEDIA
4. [ ] Click "✅ Crea Scadenza"
5. [ ] Verificare scadenza creata

**3.4 Quick Actions:**
1. [ ] Click ✅ su una scadenza
2. [ ] Confermare completamento
3. [ ] Verificare scadenza completata
4. [ ] Click ⏭️ su una scadenza
5. [ ] Inserire nuova data
6. [ ] Verificare scadenza posticipata
7. [ ] Click 🗑️ su una scadenza
8. [ ] Confermare cancellazione
9. [ ] Verificare scadenza rimossa

**3.5 Filtri:**
1. [ ] Click "⚠️ Solo Scadute"
2. [ ] Verificare solo scadenze scadute visualizzate
3. [ ] Click "📋 Tutte (+ Completate)"
4. [ ] Verificare tutte le scadenze visualizzate
5. [ ] Click "🔄 Ricarica"
6. [ ] Verificare lista aggiornata

**3.6 Dettagli:**
1. [ ] Click su una scadenza
2. [ ] Verificare apertura modal dettagli
3. [ ] Verificare visualizzazione JSON completo
4. [ ] Click ✖ per chiudere

**Expected Result:**
- Tutte le operazioni CRUD funzionano
- Statistiche aggiornate in tempo reale
- Filtri funzionano correttamente
- UI responsiva e fluida

**Status:** ⬜ Not Tested | ✅ Passed | ❌ Failed

**Notes:**
```
[Inserire eventuali note]
```

---

### TC-004: ScadenzeSection in ContrattoDetail

**Obiettivo:** Verificare integrazione scadenze in pagina dettaglio contratto

**Pre-condizioni:**
- Almeno 1 contratto test con ID noto

**Steps:**
1. [ ] Navigare a `/contratti/{id}`
2. [ ] Scroll in basso fino a "Scadenze Contratto"
3. [ ] Verificare sezione visibile
4. [ ] Verificare badge warnings se ci sono scadenze scadute/alta priorità
5. [ ] Click "▼" per espandere/collassare
6. [ ] Verificare funzionamento collapse
7. [ ] Click "➕ Nuova Scadenza"
8. [ ] Verificare modal aperto con entity pre-compilata:
   - Modulo: "affitti_lungo"
   - Entity Type: "contratto"
   - Entity ID: {id contratto}
9. [ ] Creare scadenza test
10. [ ] Verificare scadenza appare nella sezione
11. [ ] Click su scadenza nella lista
12. [ ] Verificare apertura modal dettagli
13. [ ] Verificare checkbox "Mostra completate"
14. [ ] Selezionare checkbox
15. [ ] Verificare scadenze completate visibili

**Expected Result:**
- Sezione integrata correttamente
- Scadenze caricate automaticamente
- Creazione scadenza collegata funziona
- UI coerente con resto applicazione

**Status:** ⬜ Not Tested | ✅ Passed | ❌ Failed

**Notes:**
```
[Inserire eventuali note]
```

---

### TC-005: ScadenzeSection in ImmobileDetail

**Obiettivo:** Verificare integrazione scadenze in pagina dettaglio immobile

**Pre-condizioni:**
- Almeno 1 immobile test con ID noto

**Steps:**
1. [ ] Navigare a `/unita-immobiliari/{id}`
2. [ ] Scroll in basso fino a "Scadenze Immobile"
3. [ ] Verificare sezione visibile
4. [ ] Click "➕ Nuova Scadenza"
5. [ ] Verificare modal aperto con entity pre-compilata:
   - Modulo: "immobili"
   - Entity Type: "unita_immobiliare"
   - Entity ID: {id immobile}
6. [ ] Creare scadenza:
   - Titolo: "Verifica impianto elettrico"
   - Data: tra 30 giorni
   - Priorità: ALTA
7. [ ] Verificare scadenza creata e visibile
8. [ ] Click su scadenza
9. [ ] Verificare dettagli corretti

**Expected Result:**
- Sezione integrata correttamente
- Scadenza collegata all'immobile
- Entity fields read-only in modal

**Status:** ⬜ Not Tested | ✅ Passed | ❌ Failed

**Notes:**
```
[Inserire eventuali note]
```

---

### TC-006: ScadenzeList Component

**Obiettivo:** Verificare lista avanzata con tutti i filtri

**Pre-condizioni:**
- Almeno 10 scadenze di test con vari stati e priorità

**Steps:**

**6.1 View Modes:**
1. [ ] Aprire pagina test scadenze
2. [ ] Click icona "◫" (grid)
3. [ ] Verificare layout griglia
4. [ ] Click icona "☰" (list)
5. [ ] Verificare layout lista
6. [ ] Click icona "≡" (compact)
7. [ ] Verificare layout compatto

**6.2 Filtri:**
1. [ ] Inserire testo in campo search
2. [ ] Verificare filtro funziona
3. [ ] Selezionare stato "ATTIVA"
4. [ ] Verificare solo scadenze attive
5. [ ] Selezionare priorità "ALTA"
6. [ ] Verificare solo alta priorità
7. [ ] Selezionare "Solo TODO"
8. [ ] Verificare solo TODO standalone
9. [ ] Inserire date range
10. [ ] Verificare filtro date
11. [ ] Click "✖" reset filtri
12. [ ] Verificare tutti i filtri azzerati

**6.3 Sorting:**
1. [ ] Click "Data ↑"
2. [ ] Verificare ordinamento per data crescente
3. [ ] Click "Data ↓"
4. [ ] Verificare ordinamento decrescente
5. [ ] Click "Priorità"
6. [ ] Verificare ordinamento per priorità
7. [ ] Click "Titolo"
8. [ ] Verificare ordinamento alfabetico

**6.4 Batch Actions:**
1. [ ] Selezionare checkbox su 3 scadenze
2. [ ] Verificare barra "X selezionate" appare
3. [ ] Click "Deseleziona tutto"
4. [ ] Verificare selezione azzerata
5. [ ] Selezionare 2 scadenze
6. [ ] Click "🗑️ Cancella selezionate"
7. [ ] Confermare
8. [ ] Verificare scadenze cancellate

**6.5 Pagination:**
1. [ ] Verificare "Pagina 1 di N"
2. [ ] Click "Successiva →"
3. [ ] Verificare pagina 2
4. [ ] Click "← Precedente"
5. [ ] Verificare ritorno pagina 1

**Expected Result:**
- Tutti i filtri funzionano
- Sorting corretto
- Batch actions funzionano
- Pagination funziona
- Performance accettabile (< 2s)

**Status:** ⬜ Not Tested | ✅ Passed | ❌ Failed

**Notes:**
```
[Inserire eventuali note]
```

---

### TC-007: ScadenzeModal CRUD

**Obiettivo:** Verificare modal in tutti i modi (create/edit/view)

**Pre-condizioni:**
- Almeno 1 scadenza esistente

**Steps:**

**7.1 Create Mode:**
1. [ ] Aprire modal in mode create
2. [ ] Verificare campi vuoti
3. [ ] Tentare submit senza compilare
4. [ ] Verificare validazione errori
5. [ ] Compilare tutti i campi obbligatori
6. [ ] Click "💾 Salva"
7. [ ] Verificare scadenza creata

**7.2 Edit Mode:**
1. [ ] Aprire modal in mode edit con scadenza esistente
2. [ ] Verificare campi pre-compilati
3. [ ] Modificare titolo e priorità
4. [ ] Click "💾 Salva"
5. [ ] Verificare modifiche salvate
6. [ ] Verificare entity fields disabled (non modificabili)

**7.3 View Mode:**
1. [ ] Aprire modal in mode view
2. [ ] Verificare tutti i campi read-only
3. [ ] Verificare sezione metadata visibile
4. [ ] Verificare sezione "📜 Storico Modifiche"
5. [ ] Verificare log entries presenti
6. [ ] Click "✅ Completa"
7. [ ] Verificare scadenza completata
8. [ ] Riaprire modal
9. [ ] Click "⏭️ Posticipa"
10. [ ] Inserire nuova data
11. [ ] Verificare scadenza posticipata
12. [ ] Click "🗑️ Cancella"
13. [ ] Confermare
14. [ ] Verificare scadenza cancellata

**Expected Result:**
- Validazione form funziona
- Tutti i modi funzionano correttamente
- Quick actions funzionano
- Audit log visibile
- Modal responsive

**Status:** ⬜ Not Tested | ✅ Passed | ❌ Failed

**Notes:**
```
[Inserire eventuali note]
```

---

### TC-008: ScadenzeWidget Dashboard

**Obiettivo:** Verificare widget per dashboard

**Pre-condizioni:**
- Almeno 5 scadenze prossime

**Steps:**
1. [ ] Integrare ScadenzeWidget in dashboard
2. [ ] Verificare widget visibile
3. [ ] Verificare top 5 scadenze mostrate
4. [ ] Verificare scadenze ordinate per data
5. [ ] Verificare scadenze scadute evidenziate
6. [ ] Verificare date formattate (Oggi, Domani)
7. [ ] Hover su scadenza
8. [ ] Verificare quick actions appaiono
9. [ ] Click ✅ su una scadenza
10. [ ] Verificare completamento
11. [ ] Click su una scadenza
12. [ ] Verificare apertura modal
13. [ ] Click "Vedi tutte le scadenze →"
14. [ ] Verificare redirect a pagina scadenze
15. [ ] Attendere 5 minuti
16. [ ] Verificare auto-refresh

**Expected Result:**
- Widget compatto e leggibile
- Top N scadenze corrette
- Quick actions funzionano
- Auto-refresh funziona
- Performance buone

**Status:** ⬜ Not Tested | ✅ Passed | ❌ Failed

**Notes:**
```
[Inserire eventuali note]
```

---

### TC-009: Multi-Tenant Isolation

**Obiettivo:** Verificare completo isolamento dati tra tenant

**Pre-condizioni:**
- 2 tenant: tenant_test, tenant_produzione
- Utente con accesso a entrambi i tenant
- Scadenze create in entrambi i tenant

**Steps:**

**9.1 Tenant Test:**
1. [ ] Login utente
2. [ ] Selezionare tenant "tenant_test"
3. [ ] Creare scadenza: "Test Tenant A - Scadenza 1"
4. [ ] Verificare scadenza visibile
5. [ ] Annotare ID scadenza: `____`

**9.2 Switch Tenant:**
1. [ ] Click menu utente → "Cambia Database"
2. [ ] Selezionare tenant "tenant_produzione"
3. [ ] Verificare tenant cambiato (check TopBar)

**9.3 Tenant Produzione:**
1. [ ] Verificare "Test Tenant A - Scadenza 1" NON visibile
2. [ ] Creare scadenza: "Test Tenant B - Scadenza 1"
3. [ ] Verificare solo scadenze tenant B visibili
4. [ ] Annotare ID scadenza: `____`

**9.4 API Direct Test:**
1. [ ] Ottenere token tenant A
2. [ ] Fare request: `GET /scadenze/{id_tenant_A}`
3. [ ] Verificare scadenza trovata
4. [ ] Ottenere token tenant B
5. [ ] Fare request: `GET /scadenze/{id_tenant_A}`
6. [ ] Verificare 404 NOT FOUND (data isolation)
7. [ ] Fare request: `GET /scadenze/{id_tenant_B}`
8. [ ] Verificare scadenza trovata

**9.5 Switch Back:**
1. [ ] Cambiare di nuovo a tenant_test
2. [ ] Verificare solo scadenze tenant A visibili
3. [ ] Verificare "Test Tenant A - Scadenza 1" presente
4. [ ] Verificare "Test Tenant B - Scadenza 1" NON presente

**Expected Result:**
- ✅ Zero data leakage tra tenant
- ✅ Switch tenant funziona correttamente
- ✅ API rispetta isolamento
- ✅ UI mostra solo dati tenant corrente

**Status:** ⬜ Not Tested | ✅ Passed | ❌ Failed

**Notes:**
```
[Inserire eventuali note]
```

---

### TC-010: Performance & Load

**Obiettivo:** Verificare performance con carico elevato

**Pre-condizioni:**
- Database con 100+ scadenze

**Steps:**

**10.1 Lista Grande:**
1. [ ] Creare 100 scadenze di test
2. [ ] Aprire pagina lista scadenze
3. [ ] Misurare tempo caricamento: `____` sec
4. [ ] Verificare < 3 secondi
5. [ ] Applicare filtri
6. [ ] Misurare tempo filtro: `____` sec
7. [ ] Verificare < 1 secondo

**10.2 Pagination:**
1. [ ] Navigare tra pagine
2. [ ] Verificare caricamento fluido
3. [ ] Verificare no lag UI

**10.3 Auto-Refresh:**
1. [ ] Badge TopBar auto-refresh (5 min)
2. [ ] NotifichePanel auto-refresh (2 min)
3. [ ] Widget auto-refresh (5 min)
4. [ ] Verificare no impatto performance visibile

**10.4 Batch Operations:**
1. [ ] Selezionare 50 scadenze
2. [ ] Click "Cancella selezionate"
3. [ ] Misurare tempo: `____` sec
4. [ ] Verificare < 5 secondi

**Expected Result:**
- Performance accettabili anche con carico
- UI rimane responsive
- No memory leaks
- Auto-refresh non impatta UX

**Status:** ⬜ Not Tested | ✅ Passed | ❌ Failed

**Notes:**
```
[Inserire eventuali note]
```

---

### TC-011: Mobile Responsive

**Obiettivo:** Verificare UI responsive su mobile

**Pre-condizioni:**
- Device mobile o Chrome DevTools mobile view

**Steps:**
1. [ ] Aprire app su mobile (viewport < 768px)
2. [ ] Verificare TopBar responsive
3. [ ] Verificare badge scadenze visibile
4. [ ] Click badge → verifica pannello notifiche responsive
5. [ ] Aprire pagina test scadenze
6. [ ] Verificare filtri in colonna
7. [ ] Verificare cards responsive
8. [ ] Verificare modal responsive
9. [ ] Test quick actions su touch screen
10. [ ] Verificare gesture funzionano

**Expected Result:**
- UI completamente responsive
- Touch-friendly (bottoni grandi)
- No horizontal scroll
- Modals utilizzabili su mobile

**Status:** ⬜ Not Tested | ✅ Passed | ❌ Failed

**Notes:**
```
[Inserire eventuali note]
```

---

## 🐛 Bug Tracking

### Bug Report Template

```markdown
**Bug ID:** BUG-XXX
**Severity:** Critical | High | Medium | Low
**Component:** [Nome componente]
**Test Case:** TC-XXX

**Description:**
[Descrizione bug]

**Steps to Reproduce:**
1. ...
2. ...

**Expected Result:**
[Cosa dovrebbe succedere]

**Actual Result:**
[Cosa succede realmente]

**Screenshots:**
[Se applicabile]

**Environment:**
- Browser: ...
- OS: ...
- Tenant: ...

**Notes:**
[Note aggiuntive]
```

### Bugs Found

| ID | Severity | Component | Description | Status |
|----|----------|-----------|-------------|--------|
| - | - | - | - | Open/Fixed |

---

## ✅ Sign-Off

### Test Execution Summary

**Test Date:** _______________
**Tester Name:** _______________
**Environment:** _______________

**Results:**
- Total Test Cases: 11
- Passed: ___
- Failed: ___
- Not Tested: ___

**Pass Rate:** ____%

### Acceptance Criteria

- [ ] All Critical test cases passed
- [ ] No Critical/High bugs open
- [ ] Performance metrics met
- [ ] Multi-tenant isolation verified
- [ ] Mobile responsive verified

### Approval

**Tester Signature:** _______________
**Date:** _______________

**Project Manager Signature:** _______________
**Date:** _______________

---

**Document Version:** 1.0.0
**Last Updated:** 10 Dicembre 2025
