# UAT Navigation Refactoring - Quick Start Guide

**Test Campaign**: Sidebar-Only Navigation Refactoring
**Test Plan**: `/docs/uat/UAT_NAVIGATION_REFACTORING_PLAN.md`
**Status**: READY FOR EXECUTION

---

## TL;DR - What You Need to Know

We replaced the old dual navigation system (Navbar + DynamicMenu) with a unified sidebar-only architecture. We need to verify ZERO functional regressions.

**What Changed:**
- REMOVED: Old Navbar.jsx, DynamicMenu.jsx
- ADDED: NavigationContext, TopBar, Sidebar, Drawer, NavigationItem

**Test Objective**: Verify everything still works + better UX

---

## Quick Launch Instructions

### Step 1: Verify Test Environment (2 minutes)

```bash
# 1. Check backend is running
curl http://192.168.1.2:8000/health
# Expected: {"status": "healthy"}

# 2. Check frontend is running
curl -I http://192.168.1.2:3002/
# Expected: HTTP/1.1 200 OK

# 3. If either fails, start them:
# Backend:
cd /home/htpc/test/gestione-affitti/backend
source venv/bin/activate
python app/main.py &

# Frontend:
cd /home/htpc/test/gestione-affitti/frontend
npm run dev -- --port 3002 --host 0.0.0.0 &
```

### Step 2: Launch 3 UAT Operators in Parallel

You'll need to engage 3 separate UAT operator agents:

**Operator #1 - Navigation Regression**
- Focus: Core navigation functionality
- Test Cases: TC-NAV-001 to TC-NAV-007
- Duration: ~10 minutes
- Priority: CRITICAL

**Operator #2 - UI/UX Consistency**
- Focus: Responsive design, visual consistency
- Test Cases: TC-UX-001 to TC-UX-008
- Duration: ~12 minutes
- Priority: HIGH

**Operator #3 - Integration & E2E**
- Focus: Authentication, cross-route flows, backend integration
- Test Cases: TC-INT-001 to TC-INT-006
- Duration: ~15 minutes
- Priority: CRITICAL

### Step 3: Provide Operators with Context

Each operator should receive:
1. Full test plan document: `/docs/uat/UAT_NAVIGATION_REFACTORING_PLAN.md`
2. Their specific test case section
3. Credentials: `admin` / `admin123`
4. Frontend URL: http://192.168.1.2:3002/
5. Instructions: "Execute tests independently, report defects as you find them"

---

## Operator Instructions Template

Use this template when launching each operator:

```
You are UAT Operator #{N} testing the Sidebar-Only Navigation Refactoring.

**Your Mission**: Execute test cases TC-{PREFIX}-001 to TC-{PREFIX}-00X and report any defects.

**Test Environment**:
- Frontend: http://192.168.1.2:3002/
- Login: admin / admin123
- Test Plan: /home/htpc/test/gestione-affitti/docs/uat/UAT_NAVIGATION_REFACTORING_PLAN.md

**Your Focus Area**: {FOCUS_DESCRIPTION}

**Test Cases**: Read section "TC-{PREFIX}-001 to TC-{PREFIX}-00X" in test plan

**Instructions**:
1. Execute each test case sequentially
2. Mark as ✅ PASS or ❌ FAIL
3. For failures, capture:
   - Screenshot
   - Console errors
   - Detailed reproduction steps
4. Report defects immediately as you find them
5. After structured tests, spend 5 min on exploratory testing
6. Think like a real user - make mistakes, click rapidly, resize windows
7. Maximum autonomy - don't ask for permission, just test

**Defect Report Format**:
```
DEFECT ID: {PREFIX}-{NUMBER}
Severity: CRITICAL | HIGH | MEDIUM | LOW
Test Case: TC-{PREFIX}-{NUMBER}
Summary: One-line description
Steps to Reproduce: (numbered list)
Expected: What should happen
Actual: What actually happened
Screenshot: {filename}
Console Errors: (copy-paste)
```

**Acceptance**:
- CRITICAL = Blocks core functionality, must fix before deploy
- HIGH = Major feature broken, needs workaround
- MEDIUM = Partial functionality, cosmetic issues
- LOW = Minor, non-blocking

**Time Budget**: ~{DURATION} minutes (structured + exploratory)

**Report To**: Save report at `/docs/uat/UAT_NAV_OPERATOR_{N}_REPORT.md`

Ready? START TESTING!
```

---

## Operator #1 Specific Instructions

```
UAT Operator #1 - Navigation Regression Testing

**Focus**: Core navigation functionality (sidebar, drawer, menu loading)

**Test Cases**:
- TC-NAV-001: Desktop Sidebar Behavior
- TC-NAV-002: Mobile Drawer Behavior
- TC-NAV-003: Menu Data Loading
- TC-NAV-004: Hierarchical Menu Navigation
- TC-NAV-005: Keyboard Navigation & Accessibility
- TC-NAV-006: TopBar Utility Components
- TC-NAV-007: No Orphaned UI Elements

**Critical Tests** (prioritize if time limited):
- TC-NAV-002 (mobile drawer - HIGH RISK)
- TC-NAV-003 (menu API integration - CRITICAL)
- TC-NAV-005 (keyboard nav - accessibility)

**Testing Approach**:
1. Start with desktop viewport (1920x1080)
2. Test sidebar collapse/expand thoroughly
3. Switch to mobile (375px) and test drawer
4. Test keyboard navigation with TAB key
5. Verify no old navbar remnants

**Expected Duration**: 10 minutes
```

---

## Operator #2 Specific Instructions

```
UAT Operator #2 - UI/UX Consistency Testing

**Focus**: Responsive design, visual consistency, user experience

**Test Cases**:
- TC-UX-001: Responsive Breakpoints
- TC-UX-002: Touch Target Sizes (Mobile)
- TC-UX-003: Visual Consistency Across Routes
- TC-UX-004: Loading and Error States
- TC-UX-005: Animation and Transition Smoothness
- TC-UX-006: Focus and Hover States
- TC-UX-007: Color Contrast and Readability
- TC-UX-008: No Layout Shift (CLS)

**Critical Tests**:
- TC-UX-001 (responsive breakpoints - HIGH RISK)
- TC-UX-002 (touch targets - accessibility)
- TC-UX-005 (animation smoothness - performance)

**Testing Approach**:
1. Test all viewport sizes: 1920px, 992px, 768px, 375px, 320px
2. Measure touch targets on mobile (<44px = FAIL)
3. Test animations with DevTools Performance tab
4. Verify visual consistency across ALL routes
5. Check color contrast with Lighthouse

**Tools Needed**:
- Browser DevTools (F12)
- Device toolbar (Ctrl+Shift+M)
- Lighthouse (Performance tab)

**Expected Duration**: 12 minutes
```

---

## Operator #3 Specific Instructions

```
UAT Operator #3 - Integration & End-to-End Testing

**Focus**: Authentication integration, cross-route flows, backend API integration

**Test Cases**:
- TC-INT-001: Authentication Integration
- TC-INT-002: Cross-Route Navigation Flow
- TC-INT-003: Backend Menu API Integration
- TC-INT-004: Module System Integration
- TC-INT-005: Browser Compatibility
- TC-INT-006: Performance and Memory

**Critical Tests**:
- TC-INT-001 (auth integration - CRITICAL)
- TC-INT-002 (cross-route flows - HIGH RISK)
- TC-INT-003 (menu API - CRITICAL)

**Testing Approach**:
1. Test full authentication flow (logout → login → navigate)
2. Execute multi-step workflows (create property → create contract)
3. Verify backend menu API integration
4. Test browser back/forward navigation
5. Check performance with DevTools

**Multi-Step Workflow Example**:
- Login → Dashboard → Immobili → Create Property → View Property → Create Contract
- Verify navigation persists at each step
- Verify active state highlights correctly

**Expected Duration**: 15 minutes
```

---

## Pass/Fail Criteria Summary

### PASS Conditions (Deploy approved):
- ✅ Zero CRITICAL defects
- ✅ ≤2 HIGH defects with workarounds
- ✅ All core flows functional
- ✅ Accessibility compliant (keyboard nav works)
- ✅ Performance acceptable (<3s load time)

### FAIL Conditions (Rollback required):
- ❌ Any CRITICAL defect (navigation broken, app crashes)
- ❌ >5 HIGH defects
- ❌ Accessibility Level A violations
- ❌ Data loss or security issues

---

## Defect Severity Guide

**CRITICAL** - Blocks core functionality
- Examples: Can't open sidebar/drawer, app crashes, menu doesn't load

**HIGH** - Major feature broken
- Examples: Active state not highlighted, keyboard nav broken on specific route

**MEDIUM** - Partial functionality
- Examples: Animation stutters, text overflow in collapsed mode

**LOW** - Cosmetic only
- Examples: Icon alignment off by 2px, color contrast slightly low

---

## After Testing - Report Collection

Each operator should produce:

1. **Individual Report**: `/docs/uat/UAT_NAV_OPERATOR_{N}_REPORT.md`
   - Test summary (passed/failed counts)
   - Defects found (with severity)
   - Screenshots directory: `/docs/uat/screenshots/nav-refactor/`

2. **Defect Log** (if defects found): `/docs/uat/NAV_DEFECTS_{N}.md`

Then, UAT Manager will:
- Aggregate all 3 reports
- Create consolidated report
- Make PASS/FAIL decision
- Recommend next actions

---

## Common Issues and Quick Fixes

### Frontend not accessible
```bash
cd /home/htpc/test/gestione-affitti/frontend
npm run dev -- --port 3002 --host 0.0.0.0
```

### Backend not responding
```bash
cd /home/htpc/test/gestione-affitti/backend
source venv/bin/activate
python app/main.py
```

### Can't login (401 Unauthorized)
- Check backend is running: `curl http://192.168.1.2:8000/docs`
- Clear localStorage: Open DevTools → Console → `localStorage.clear()`
- Try login again with: admin / admin123

### Sidebar doesn't appear
- Check console for errors
- Verify at /home/htpc/test/gestione-affitti/frontend/src/App.jsx that NavigationProvider wraps AppLayout

---

## Ready to Launch?

Checklist before starting:
- [ ] Backend running and accessible at http://192.168.1.2:8000
- [ ] Frontend running and accessible at http://192.168.1.2:3002
- [ ] Login credentials verified: admin / admin123
- [ ] Test plan read and understood by all operators
- [ ] DevTools open (F12) for all operators
- [ ] Screenshot tool ready
- [ ] Defect report templates prepared

**Estimated Total Time**: 15 minutes (parallel execution)

**GO/NO-GO Decision**: If all checklist items checked, launch operators!

---

**File Locations**:
- Full Test Plan: `/home/htpc/test/gestione-affitti/docs/uat/UAT_NAVIGATION_REFACTORING_PLAN.md`
- Quick Start (this file): `/home/htpc/test/gestione-affitti/docs/uat/UAT_NAVIGATION_QUICK_START.md`
- Reports Directory: `/home/htpc/test/gestione-affitti/docs/uat/`
- Screenshots Directory: `/home/htpc/test/gestione-affitti/docs/uat/screenshots/nav-refactor/`

---

**Status**: READY FOR EXECUTION
**Next Action**: Launch 3 UAT operators with instructions above
