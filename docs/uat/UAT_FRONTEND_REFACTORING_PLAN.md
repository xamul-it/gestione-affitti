# UAT - Frontend Refactoring Non-Regression Test Plan

**Test Campaign ID**: `UAT-FRONTEND-REFACTOR-2025-12-04`
**Test Date**: December 4, 2025
**Refactoring Scope**: Frontend Modular Architecture Migration (Week 1-4)
**Objective**: Verify ZERO regressions after migrating 42 components to modular structure

---

## Executive Summary

After completing the frontend modular refactoring (Weeks 1-4), we need to verify that:
- ✅ All existing functionality still works (NO REGRESSIONS)
- ✅ All imports are correctly resolved
- ✅ All API calls function properly
- ✅ All cross-module dependencies work
- ✅ Build and runtime performance is acceptable

**Refactoring Changes**:
- 42 components migrated to modules
- 18 files moved to `affitti_lungo` module
- 24 files moved to `immobili` module
- All API imports updated
- Cross-module dependencies established

---

## Test Strategy

### Parallel Testing Approach

We will use **3 UAT Operators in parallel** to maximize coverage and simulate real concurrent user load:

1. **UAT Operator #1** - Immobili Module Tests (TC-001)
2. **UAT Operator #2** - Affitti Lungo Module Tests (TC-002)
3. **UAT Operator #3** - Platform & Integration Tests (TC-003)

Each operator will execute independently and report back to the UAT Manager.

---

## Test Environment

```
Frontend:  http://192.168.1.2:5173 (Vite dev server)
Backend:   http://192.168.1.2:8000
Database:  PostgreSQL on port 5433
Browser:   Chromium (Playwright headless)
```

**Test User Credentials**:
- Admin: `admin` / `admin123`
- Regular User: (if needed for permission tests)

---

## Test Cases Overview

| Test Case | Module | Operator | Priority | Duration |
|-----------|--------|----------|----------|----------|
| TC-001 | Immobili (Properties) | Operator #1 | Critical | ~5 min |
| TC-002 | Affitti Lungo (Rentals) | Operator #2 | Critical | ~6 min |
| TC-003 | Platform & Integration | Operator #3 | High | ~4 min |

**Total Estimated Duration**: ~15 minutes (parallel execution = ~6 min actual)

---

## TC-001: Immobili Module Non-Regression Test

**Operator**: UAT Operator #1
**Module**: `modules/immobili/`
**Components Tested**: 24 files (8 directories)

### Test Scope

1. **UnitaImmobiliari (Properties)**
   - List view with data loading
   - Create new property form
   - Edit existing property
   - Delete property
   - Form validation
   - Categoria catastale dropdown
   - Tipo auto-fill from categoria

2. **Proprietari (Owners)**
   - List view
   - Create/Edit owner form
   - Link to SoggettoAnagrafico
   - Search functionality

3. **Condomini (Condominiums)**
   - List view
   - Create/Edit condominium
   - Tabelle millesimali

4. **Diritti Immobile (Property Rights)**
   - View property rights
   - Add new right
   - Edit/Delete right

5. **Certificati Energetici (Energy Certificates)**
   - List certificates
   - Upload certificate
   - View details
   - Associate with property

6. **Documenti Upload** (via cross-module import)
   - Upload documents from property form
   - Verify DocumentiSection renders
   - File upload functionality

### Critical Paths

```
1. Login → UnitaImmobiliari List → Create Property → Save → Verify in List
2. UnitaImmobiliari List → Edit Property → Change categoria → Verify tipo auto-fill
3. Property Detail → Add Diritto → Save → Verify ownership
4. Property Detail → Upload Documento → Verify in list
5. Navigate through all submenu items without errors
```

### Success Criteria

- ✅ All 8 immobili components load without errors
- ✅ CRUD operations work correctly
- ✅ API calls to `modules/immobili/services/immobiliAPI.js` succeed
- ✅ Cross-module import from affitti_lungo (DocumentiSection) works
- ✅ CSS imports resolve correctly
- ✅ No console errors related to imports

---

## TC-002: Affitti Lungo Module Non-Regression Test

**Operator**: UAT Operator #2
**Module**: `modules/affitti_lungo/`
**Components Tested**: 18 files (6 directories)

### Test Scope

1. **Affittuari (Tenants)**
   - List view with pagination
   - Create new tenant
   - Edit tenant details
   - Link to SoggettoAnagrafico
   - Search and filter

2. **Contratti (Contracts)**
   - List contracts
   - Create new contract
   - Link to UnitaImmobiliare (cross-module dependency!)
   - Link to Affittuario
   - Date validation
   - Contract status

3. **Incassi (Income)**
   - List income records
   - Create income entry
   - Link to contract
   - Monthly generation
   - Payment tracking

4. **Spese (Expenses)**
   - List expenses
   - Create expense
   - Link to UnitaImmobiliare (cross-module dependency!)
   - Expense categories
   - Ripartizione spese

5. **Tecnici (Technicians)**
   - List technicians
   - Create/Edit technician
   - CSS cross-import verification (imports from immobili!)

6. **Documenti (Documents)**
   - Upload documents
   - List by entity type
   - Download documents
   - Delete documents

### Critical Paths

```
1. Login → Affittuari List → Create Tenant → Save → Verify
2. Contratti List → Create Contract → Select Property (cross-module!) → Save
3. Contratto Detail → Generate Incassi → Verify monthly records
4. Spese List → Create Expense → Select Property (cross-module!) → Save
5. Tecnici List → Verify CSS styling (cross-module CSS import!)
6. Document Upload → Verify storage and retrieval
```

### Success Criteria

- ✅ All 6 affitti_lungo components load without errors
- ✅ CRUD operations work correctly
- ✅ API calls to `modules/affitti_lungo/services/affittiAPI.js` succeed
- ✅ Cross-module API imports work (unitaImmobiliariAPI from immobili)
- ✅ CSS cross-import from immobili module works (Tecnici.css)
- ✅ Documenti component works in both modules
- ✅ No console errors

---

## TC-003: Platform & Integration Tests

**Operator**: UAT Operator #3
**Module**: Platform services + cross-cutting concerns
**Focus**: System-wide integration and shared components

### Test Scope

1. **Authentication Flow**
   - Login with valid credentials
   - Token storage in localStorage
   - Protected routes enforcement
   - Logout functionality

2. **Dynamic Menu**
   - Menu loads from backend API
   - Hierarchical menu structure
   - Module-based menu items
   - Navigation to all routes

3. **Dashboard**
   - Dashboard loads
   - Widgets display correctly
   - Module widgets function
   - Layout persistence

4. **Module System**
   - Module auto-discovery (useModuleLoader)
   - Local manifests load correctly
   - Backend module API sync
   - No duplicate modules

5. **Shared Components**
   - Layout components (Navbar)
   - Platform components (ImportButton, Search)
   - Auth components (ProtectedRoute)

6. **Build & Performance**
   - Build completes without errors
   - Bundle size acceptable
   - Page load times reasonable
   - No memory leaks

### Critical Paths

```
1. Login → Dashboard → Verify widgets load
2. Menu → Expand Immobili → Navigate to all subitems
3. Menu → Expand Affitti → Navigate to all subitems
4. Admin → Modules page → Verify module list
5. Navigate between modules multiple times → Check memory
```

### Success Criteria

- ✅ Authentication works end-to-end
- ✅ Menu shows correct structure from both local and backend
- ✅ Dashboard widgets render without errors
- ✅ Module auto-discovery finds all 3 modules
- ✅ All shared components work correctly
- ✅ Build passes in <10 seconds
- ✅ No console errors across entire app

---

## Test Execution Workflow

### Phase 1: Setup (1 minute)

```bash
# 1. Ensure backend is running
cd backend
source venv/bin/activate
python app/main.py

# 2. Ensure frontend dev server is running
cd frontend
npm run dev

# 3. Verify both accessible
curl http://192.168.1.2:8000/docs
curl http://192.168.1.2:5173
```

### Phase 2: Parallel Operator Execution (6 minutes)

Launch all 3 UAT operators in parallel:

```bash
# Terminal 1 - Operator #1 (Immobili)
cd frontend
node uat-operator-immobili.mjs

# Terminal 2 - Operator #2 (Affitti)
node uat-operator-affitti.mjs

# Terminal 3 - Operator #3 (Platform)
node uat-operator-platform.mjs
```

Each operator will:
1. Execute its test cases independently
2. Generate step-by-step logs
3. Capture screenshots on failures
4. Report defects with severity
5. Save detailed JSON report

### Phase 3: Report Aggregation (2 minutes)

UAT Manager will:
1. Collect reports from all 3 operators
2. Aggregate results
3. Identify common issues
4. Generate executive summary
5. Create consolidated defect list

---

## Defect Severity Classification

| Severity | Impact | Example |
|----------|--------|---------|
| **CRITICAL** | App unusable, data loss, security issue | Login broken, API 500 errors, build fails |
| **HIGH** | Major feature broken, no workaround | CRUD operations fail, import errors, cross-module dependency broken |
| **MEDIUM** | Feature partially works, workaround exists | UI glitch, slow performance, minor validation issue |
| **LOW** | Cosmetic only, no functional impact | Alignment issue, color contrast, typo |

---

## Pass/Fail Criteria

### Overall Test Campaign: PASS if:

1. ✅ All 3 test cases complete without CRITICAL defects
2. ✅ Zero HIGH-severity defects related to refactoring
3. ✅ Build completes successfully
4. ✅ All CRUD operations work in both modules
5. ✅ Cross-module dependencies function correctly
6. ✅ No import resolution errors
7. ✅ No console errors during normal usage
8. ✅ Performance within acceptable range (±10% of pre-refactor)

### Overall Test Campaign: FAIL if:

- ❌ Any CRITICAL defect found
- ❌ More than 3 HIGH-severity defects
- ❌ Build fails
- ❌ Any component fails to load
- ❌ Import errors present
- ❌ Cross-module dependencies broken

---

## Rollback Plan

If test campaign FAILS with critical issues:

1. **Immediate**: Stop deployment, rollback to pre-refactor commit
2. **Investigate**: Identify root cause of failures
3. **Fix**: Apply targeted fixes
4. **Retest**: Execute UAT again
5. **Document**: Update migration guide with lessons learned

**Rollback Git Commit**: (to be tagged before starting UAT)

---

## Test Deliverables

1. **Individual Operator Reports** (3 files)
   - `uat-report-immobili-{timestamp}.json`
   - `uat-report-affitti-{timestamp}.json`
   - `uat-report-platform-{timestamp}.json`

2. **Consolidated UAT Report**
   - `UAT_FRONTEND_REFACTOR_CONSOLIDATED_REPORT.md`

3. **Executive Summary**
   - `UAT_EXECUTIVE_SUMMARY.txt`

4. **Defect Log** (if any)
   - `DEFECTS_FOUND.csv`

5. **Screenshots** (failures only)
   - `test-screenshots/operator-{n}-step-{m}-{description}.png`

---

## Sign-Off

| Role | Name | Date | Signature |
|------|------|------|-----------|
| UAT Manager | Claude Code | 2025-12-04 | _________ |
| UAT Operator #1 | Automated | 2025-12-04 | _________ |
| UAT Operator #2 | Automated | 2025-12-04 | _________ |
| UAT Operator #3 | Automated | 2025-12-04 | _________ |
| Tech Lead | User | 2025-12-04 | _________ |

---

## Next Steps

1. ✅ Review and approve this test plan
2. ⏳ Create 3 UAT operator scripts
3. ⏳ Execute parallel UAT session
4. ⏳ Review consolidated report
5. ⏳ Sign-off or remediate defects
6. ⏳ Deploy to production (if PASS)

---

**Status**: READY FOR EXECUTION
**Estimated Total Time**: 15 minutes (6 min parallel + 9 min setup/reporting)
