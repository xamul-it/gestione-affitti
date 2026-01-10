# UAT Test Plans - Sistema Scadenzario
**Versione:** 1.0.0
**Data:** 2025-12-10
**UAT Manager:** Claude Code
**Ambiente:** http://192.168.1.2:3000
**Backend:** http://192.168.1.2:8000

---

## Test Plan TC-001: Badge TopBar

**Test ID:** TC-001
**Funzionalità:** Badge scadenze in TopBar
**Priorità:** CRITICAL
**Tempo stimato:** 10 minuti
**Prerequisiti:**
- Backend running on port 8000
- Frontend running on port 3000
- User: admin / password: changeme123
- Database tenant: tenant_test
- Almeno 1 scadenza attiva nel database

**Test Data:**
```json
{
  "test_scadenza": {
    "titolo": "Test UAT Badge - Scadenza Alta Priorità",
    "descrizione": "Scadenza di test per verificare badge TopBar",
    "data_scadenza": "2025-12-12",
    "priorita": "ALTA",
    "is_todo": true
  }
}
```

**Execution Steps:**

| Step | Action | Expected Result | Error Scenarios to Test |
|------|--------|-----------------|------------------------|
| 1 | Navigate to http://192.168.1.2:3000 | Login page loads | - |
| 2 | Enter username: "admin" | Field accepts input | Typo: "admni" then correct |
| 3 | Enter password: "changeme123" | Field accepts input (masked) | Wrong password first, then correct |
| 4 | Click "Accedi" button | Redirect to dashboard | - |
| 5 | Select tenant "tenant_test" | Tenant switches successfully | - |
| 6 | Locate badge in TopBar (between search and user menu) | Badge visible with count | - |
| 7 | Verify badge count matches scadenze | Count > 0 | - |
| 8 | Observe badge color | Color is red/yellow/green based on stato | - |
| 9 | Hover over badge | Tooltip appears with summary | - |
| 10 | Click badge | NotifichePanel opens | Click outside first, then badge |
| 11 | Wait 5 minutes | Badge auto-refreshes | - |

**Success Criteria:**
- Badge visible in TopBar
- Count accurate
- Color coding correct
- Click opens NotifichePanel
- Tooltip informative

**Failure Scenarios:**
- Badge not visible
- Count incorrect or zero when scadenze exist
- Wrong color displayed
- Click does nothing
- Tooltip missing

---

## Test Plan TC-002: Pannello Notifiche

**Test ID:** TC-002
**Funzionalità:** Dropdown notification panel
**Priorità:** CRITICAL
**Tempo stimato:** 15 minuti
**Prerequisiti:**
- User logged in as admin
- Tenant: tenant_test
- Test scadenze created:
  - 1 scadenza scaduta (data_scadenza: 2025-12-01)
  - 1 scadenza oggi (data_scadenza: today)
  - 1 scadenza domani (data_scadenza: today + 1)
  - 1 scadenza settimana prossima (data_scadenza: today + 5)

**Test Data:**
```json
{
  "scadenze_test": [
    {
      "titolo": "UAT-002-SCADUTA",
      "data_scadenza": "2025-12-01",
      "priorita": "ALTA",
      "is_todo": true
    },
    {
      "titolo": "UAT-002-OGGI",
      "data_scadenza": "2025-12-10",
      "priorita": "MEDIA",
      "is_todo": true
    },
    {
      "titolo": "UAT-002-DOMANI",
      "data_scadenza": "2025-12-11",
      "priorita": "BASSA",
      "is_todo": true
    },
    {
      "titolo": "UAT-002-SETTIMANA",
      "data_scadenza": "2025-12-15",
      "priorita": "MEDIA",
      "is_todo": true
    }
  ]
}
```

**Execution Steps:**

| Step | Action | Expected Result | Error Scenarios to Test |
|------|--------|-----------------|------------------------|
| 1 | Click badge TopBar | Panel opens as dropdown | Click twice accidentally |
| 2 | Verify panel layout | Sections visible: Scadute, Oggi, Domani, Settimana | - |
| 3 | Check "Scadute" section | Shows 1 item (UAT-002-SCADUTA) | - |
| 4 | Check "Oggi" section | Shows 1 item (UAT-002-OGGI) | - |
| 5 | Check "Domani" section | Shows 1 item (UAT-002-DOMANI) | - |
| 6 | Check "Questa Settimana" | Shows 1 item (UAT-002-SETTIMANA) | - |
| 7 | Click on scadenza "OGGI" | Modal opens with details | - |
| 8 | Close modal | Returns to panel | - |
| 9 | Click ✅ (completa) on "DOMANI" scadenza | Confirmation dialog appears | Cancel first time |
| 10 | Confirm completion | Scadenza marked as completata | - |
| 11 | Verify "DOMANI" removed from list | Item disappears from panel | - |
| 12 | Click ⏭️ (posticipa) on "SETTIMANA" | Date picker appears | - |
| 13 | Enter new date: today + 10 | Date field accepts input | Enter invalid date first: "99/99/9999" |
| 14 | Confirm postpone | Scadenza updated with new date | - |
| 15 | Click "Vedi tutte le scadenze" | Redirects to /test/scadenze | - |
| 16 | Click outside panel | Panel closes | - |
| 17 | Wait 2 minutes | Panel auto-refreshes data | - |

**Success Criteria:**
- Panel opens/closes correctly
- Scadenze grouped by time period
- Quick actions functional
- Modal opens from panel
- Redirect works

**Failure Scenarios:**
- Panel doesn't open
- Grouping incorrect
- Quick actions fail
- Modal doesn't open
- Redirect broken

---

## Test Plan TC-003: Pagina Test Scadenze

**Test ID:** TC-003
**Funzionalità:** Complete test page functionality
**Priorità:** CRITICAL
**Tempo stimato:** 25 minuti
**Prerequisiti:**
- User logged in as admin
- Tenant: tenant_test
- Access to /test/scadenze page

**Test Data:**
```json
{
  "todo_test": {
    "titolo": "UAT-003-TODO",
    "descrizione": "Test TODO standalone creation",
    "data_scadenza": "2025-12-11",
    "priorita": "ALTA"
  },
  "entity_linked_test": {
    "modulo": "affitti_lungo",
    "entity_type": "contratto",
    "entity_id": 1,
    "titolo": "UAT-003-CONTRATTO",
    "descrizione": "Test entity-linked scadenza",
    "data_scadenza": "2025-12-17",
    "priorita": "MEDIA"
  }
}
```

**Execution Steps:**

### Section 3.1: Statistiche

| Step | Action | Expected Result | Error Scenarios |
|------|--------|-----------------|-----------------|
| 1 | Navigate to /test/scadenze | Page loads completely | - |
| 2 | Locate statistics panel | Panel visible with counts | - |
| 3 | Verify "Attive" count | Shows number > 0 | - |
| 4 | Verify "Scadute" count | Shows accurate count | - |
| 5 | Verify "Alta Priorità" count | Shows accurate count | - |

### Section 3.2: Form Creazione TODO

| Step | Action | Expected Result | Error Scenarios |
|------|--------|-----------------|-----------------|
| 6 | Click "➕ Nuova Scadenza" button | Form modal opens | - |
| 7 | Verify "Standalone TODO" checkbox | Checkbox visible and checked | - |
| 8 | Leave all fields empty and click "Salva" | Validation errors shown | Test validation |
| 9 | Enter Titolo: "UAT-003-TODO" | Field accepts input | Typo: "UAT-033-TODO" then correct |
| 10 | Enter Descrizione: "Test TODO standalone creation" | Field accepts input | - |
| 11 | Click Data field | Date picker opens | - |
| 12 | Select tomorrow's date | Date populated | Select past date first, see error |
| 13 | Select Priorità: "ALTA" | Dropdown works | - |
| 14 | Click "✅ Crea Scadenza" | Success message appears | - |
| 15 | Verify TODO in list | New item visible with correct data | - |

### Section 3.3: Form Creazione Entity-Linked

| Step | Action | Expected Result | Error Scenarios |
|------|--------|-----------------|-----------------|
| 16 | Click "➕ Nuova Scadenza" | Form opens | - |
| 17 | Uncheck "Standalone TODO" | Entity fields appear | - |
| 18 | Select Modulo: "affitti_lungo" | Dropdown works | Select wrong one first |
| 19 | Select Entity Type: "contratto" | Dropdown works | - |
| 20 | Enter Entity ID: "1" | Field accepts input | Enter "abc" first, see validation |
| 21 | Enter Titolo: "UAT-003-CONTRATTO" | Field accepts input | - |
| 22 | Select date: today + 7 days | Date selected | - |
| 23 | Select Priorità: "MEDIA" | Dropdown works | - |
| 24 | Click "✅ Crea Scadenza" | Success message | - |
| 25 | Verify entity-linked scadenza in list | Item visible | - |

### Section 3.4: Quick Actions

| Step | Action | Expected Result | Error Scenarios |
|------|--------|-----------------|-----------------|
| 26 | Click ✅ on "UAT-003-TODO" | Confirm dialog appears | - |
| 27 | Confirm completion | Scadenza marked completed | - |
| 28 | Verify stato changed | Item shows "COMPLETATA" badge | - |
| 29 | Click ⏭️ on "UAT-003-CONTRATTO" | Date picker appears | - |
| 30 | Enter new date: today + 14 | Date field populated | - |
| 31 | Confirm postpone | Scadenza updated | - |
| 32 | Click 🗑️ on completed TODO | Confirm dialog | Cancel first |
| 33 | Confirm delete | Item removed from list | - |

### Section 3.5: Filtri

| Step | Action | Expected Result | Error Scenarios |
|------|--------|-----------------|-----------------|
| 34 | Click "⚠️ Solo Scadute" filter | Only overdue scadenze shown | - |
| 35 | Verify filter works | Count changes appropriately | - |
| 36 | Click "📋 Tutte (+ Completate)" | All scadenze including completed | - |
| 37 | Verify completed visible | Can see completed items | - |
| 38 | Click "🔄 Ricarica" | List refreshes from server | - |

### Section 3.6: Dettagli

| Step | Action | Expected Result | Error Scenarios |
|------|--------|-----------------|-----------------|
| 39 | Click on "UAT-003-CONTRATTO" | Modal opens | - |
| 40 | Verify modal shows full details | All fields visible | - |
| 41 | Verify JSON data visible | Raw data shown | - |
| 42 | Click ✖ to close | Modal closes | - |

**Success Criteria:**
- Statistics accurate
- TODO creation works
- Entity-linked creation works
- Quick actions functional
- Filters work correctly
- Details modal functional

**Failure Scenarios:**
- Statistics incorrect
- Form validation missing
- Creation fails
- Quick actions broken
- Filters not working
- Modal doesn't open

---

## Test Plan TC-004: ScadenzeSection in ContrattoDetail

**Test ID:** TC-004
**Funzionalità:** Scadenze integration in contract detail page
**Priorità:** HIGH
**Tempo stimato:** 15 minuti
**Prerequisiti:**
- User logged in
- At least 1 contratto exists (ID=1)
- Can navigate to /contratti/1

**Test Data:**
```json
{
  "contratto_scadenza": {
    "modulo": "affitti_lungo",
    "entity_type": "contratto",
    "entity_id": 1,
    "titolo": "UAT-004-Rinnovo Contratto",
    "data_scadenza": "2025-12-31",
    "priorita": "ALTA"
  }
}
```

**Execution Steps:**

| Step | Action | Expected Result | Error Scenarios |
|------|--------|-----------------|-----------------|
| 1 | Navigate to /contratti/1 | Contract detail page loads | Try /contratti/99999, see 404 |
| 2 | Scroll to "Scadenze Contratto" section | Section visible | - |
| 3 | Check for warning badges | Badges show if overdue/high priority | - |
| 4 | Click "▼" collapse toggle | Section collapses | - |
| 5 | Click "▼" again | Section expands | - |
| 6 | Click "➕ Nuova Scadenza" | Modal opens | - |
| 7 | Verify entity fields pre-filled | Modulo, Type, ID readonly | Try to edit, should be disabled |
| 8 | Enter Titolo: "UAT-004-Rinnovo Contratto" | Field accepts input | - |
| 9 | Select date: 2025-12-31 | Date selected | - |
| 10 | Select Priorità: ALTA | Dropdown works | - |
| 11 | Click "Salva" | Scadenza created | - |
| 12 | Verify appears in section list | New item visible | - |
| 13 | Click on scadenza in list | Modal opens with details | - |
| 14 | Close modal | Returns to contract page | - |
| 15 | Check "Mostra completate" checkbox | Completed scadenze appear | - |

**Success Criteria:**
- Section integrates seamlessly
- Entity pre-fill works
- Creation successful
- List updates dynamically

---

## Test Plan TC-009: Multi-Tenant Isolation

**Test ID:** TC-009
**Funzionalità:** Complete tenant data isolation
**Priorità:** CRITICAL (SECURITY)
**Tempo stimato:** 20 minuti
**Prerequisiti:**
- 2 tenants exist: tenant_test, tenant_produzione
- User has access to both tenants
- Backend running

**Test Data:**
```json
{
  "tenant_a_scadenza": {
    "titolo": "UAT-009-TENANT-A-SECRET",
    "descrizione": "This should NEVER be visible in tenant B",
    "data_scadenza": "2025-12-20",
    "priorita": "ALTA",
    "is_todo": true
  },
  "tenant_b_scadenza": {
    "titolo": "UAT-009-TENANT-B-SECRET",
    "descrizione": "This should NEVER be visible in tenant A",
    "data_scadenza": "2025-12-20",
    "priorita": "ALTA",
    "is_todo": true
  }
}
```

**Execution Steps:**

### Phase 1: Tenant A Testing

| Step | Action | Expected Result | Error Scenarios |
|------|--------|-----------------|-----------------|
| 1 | Login as admin | Dashboard loads | - |
| 2 | Select tenant "tenant_test" | Tenant switches | - |
| 3 | Verify TopBar shows "tenant_test" | Correct tenant displayed | - |
| 4 | Navigate to /test/scadenze | Page loads | - |
| 5 | Create scadenza "UAT-009-TENANT-A-SECRET" | Creation succeeds | - |
| 6 | Note the scadenza ID | Record: ID = ____ | - |
| 7 | Verify visible in list | Item appears | - |

### Phase 2: Switch to Tenant B

| Step | Action | Expected Result | Error Scenarios |
|------|--------|-----------------|-----------------|
| 8 | Click user menu → "Cambia Database" | Tenant selector opens | - |
| 9 | Select "tenant_produzione" | Tenant switches | - |
| 10 | Verify TopBar shows "tenant_produzione" | Correct tenant displayed | - |
| 11 | Navigate to /test/scadenze | Page loads | - |
| 12 | Search for "TENANT-A-SECRET" | NO RESULTS FOUND | **CRITICAL: Must be invisible** |
| 13 | Verify count excludes Tenant A data | Statistics don't include A data | - |

### Phase 3: Tenant B Testing

| Step | Action | Expected Result | Error Scenarios |
|------|--------|-----------------|-----------------|
| 14 | Create scadenza "UAT-009-TENANT-B-SECRET" | Creation succeeds | - |
| 15 | Note the scadenza ID | Record: ID = ____ | - |
| 16 | Verify visible in list | Item appears | - |
| 17 | Search for "TENANT-A-SECRET" again | Still NO RESULTS | **CRITICAL** |

### Phase 4: API Direct Test (Security Critical)

| Step | Action | Expected Result | Error Scenarios |
|------|--------|-----------------|-----------------|
| 18 | Get JWT token for tenant_test | Token obtained | - |
| 19 | curl GET /scadenze/{tenant_A_id} with tenant_test token | Returns scadenza data | - |
| 20 | Get JWT token for tenant_produzione | Token obtained | - |
| 21 | curl GET /scadenze/{tenant_A_id} with tenant_produzione token | **404 NOT FOUND** | **CRITICAL: Must reject** |
| 22 | curl GET /scadenze/{tenant_B_id} with tenant_produzione token | Returns scadenza data | - |
| 23 | curl GET /scadenze/{tenant_B_id} with tenant_test token | **404 NOT FOUND** | **CRITICAL: Must reject** |

### Phase 5: Switch Back Verification

| Step | Action | Expected Result | Error Scenarios |
|------|--------|-----------------|-----------------|
| 24 | Switch back to tenant_test | Tenant switches | - |
| 25 | Navigate to /test/scadenze | Page loads | - |
| 26 | Verify "TENANT-A-SECRET" visible | Item present | - |
| 27 | Search for "TENANT-B-SECRET" | NO RESULTS FOUND | **CRITICAL** |
| 28 | Verify statistics correct for tenant A only | Counts exclude tenant B | - |

**Success Criteria:**
- ✅ ZERO data leakage between tenants
- ✅ API enforces tenant isolation
- ✅ UI only shows current tenant data
- ✅ Switching works correctly

**CRITICAL Failure Scenarios:**
- ❌ Tenant A data visible in Tenant B
- ❌ Tenant B data visible in Tenant A
- ❌ API returns data from wrong tenant
- ❌ Statistics include other tenant's data

**Security Impact:**
This test is CRITICAL. Any failure indicates a severe security vulnerability that could expose confidential rental data between different organizations.

---

## Operator Assignment Plan

**Batch 1 - Critical UI Tests (Parallel):**
- Operator 1: TC-001 (Badge TopBar)
- Operator 2: TC-002 (Pannello Notifiche)
- Operator 3: TC-003 (Pagina Test Scadenze)

**Batch 2 - Integration Tests (Parallel):**
- Operator 4: TC-004 (ContrattoDetail Integration)

**Batch 3 - Security Test (High Priority):**
- Operator 5: TC-009 (Multi-Tenant Isolation) - CRITICAL SECURITY

---

## Reporting Instructions for Operators

Each operator must:
1. Execute test plan step-by-step
2. Introduce 1-2 realistic user errors per section
3. Document all actual vs expected results
4. Take screenshots of critical failures
5. Report back with structured report format
6. Mark overall result: PASS/FAIL/BLOCKED

**Critical Blockers:**
- Backend not responding
- Database not accessible
- Authentication broken
- Tenant switching broken

**Report deadline:** Within 30 minutes of test start

---

**Document Version:** 1.0.0
**Created by:** Claude Code UAT Manager
**Date:** 2025-12-10
