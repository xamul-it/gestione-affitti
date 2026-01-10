# UAT Navigation Refactoring - Complete Documentation Index

**Campaign**: Sidebar-Only Navigation Refactoring
**Campaign ID**: UAT-NAV-REFACTOR-2025-12-04
**Status**: READY FOR EXECUTION
**Created**: December 4, 2025

---

## Quick Navigation

| Document | Purpose | Target Audience | Size |
|----------|---------|-----------------|------|
| **[Executive Summary](#executive-summary)** | High-level overview and decision support | Tech Leads, PMs | 1 page |
| **[Quick Start Guide](#quick-start-guide)** | Launch instructions for operators | UAT Manager | 8 pages |
| **[Full Test Plan](#full-test-plan)** | Comprehensive test cases and procedures | UAT Operators | 44 pages |
| **[Operator Report Template](#operator-report-template)** | Report format for test results | UAT Operators | 6 pages |

---

## Document Descriptions

### Executive Summary
**File**: `/docs/uat/UAT_NAVIGATION_EXECUTIVE_SUMMARY.md`

**Purpose**: Provides stakeholders with a concise overview of the test campaign, pass/fail criteria, risk assessment, and recommendations.

**Key Sections**:
- Test objectives and scope
- 3 parallel operator focus areas
- Pass/fail criteria
- Risk assessment with mitigation strategies
- Deliverables and timeline
- Rollback plan
- Approval signatures

**Who Should Read**: Tech Leads, Product Owners, Project Managers, Stakeholders making go/no-go decisions

**When to Read**: Before test execution (for approval) and after test completion (for decision-making)

---

### Quick Start Guide
**File**: `/docs/uat/UAT_NAVIGATION_QUICK_START.md`

**Purpose**: Provides step-by-step instructions to launch the 3 UAT operators and execute the test campaign.

**Key Sections**:
- Environment verification checklist
- Operator launch instructions (with specific commands)
- Individual operator briefings (customized for each focus area)
- Pass/fail criteria summary
- Defect severity guide
- Common issues and quick fixes
- Post-test report collection process

**Who Should Read**: UAT Manager, Test Coordinators

**When to Read**: Immediately before launching operators

**Action Items**:
1. Verify test environment (frontend, backend, credentials)
2. Brief operators with specific instructions from this guide
3. Launch 3 operators in parallel
4. Monitor progress and collect reports

---

### Full Test Plan
**File**: `/docs/uat/UAT_NAVIGATION_REFACTORING_PLAN.md`

**Purpose**: Comprehensive test plan with detailed test cases, step-by-step procedures, success criteria, and defect reporting guidelines.

**Key Sections**:
- **TC-NAV-001 to TC-NAV-007**: Navigation Regression Tests (Operator #1)
  - Desktop sidebar behavior
  - Mobile drawer behavior
  - Menu data loading
  - Hierarchical navigation
  - Keyboard navigation & accessibility
  - TopBar utility components
  - Orphaned UI element verification

- **TC-UX-001 to TC-UX-008**: UI/UX Consistency Tests (Operator #2)
  - Responsive breakpoints
  - Touch target sizes
  - Visual consistency
  - Loading/error states
  - Animation smoothness
  - Focus/hover states
  - Color contrast
  - Layout shift (CLS)

- **TC-INT-001 to TC-INT-006**: Integration & E2E Tests (Operator #3)
  - Authentication integration
  - Cross-route navigation flows
  - Backend menu API integration
  - Module system integration
  - Browser compatibility
  - Performance and memory

**Who Should Read**: UAT Operators (all 3), Quality Assurance Engineers, Developers investigating defects

**When to Read**: During test execution (operators follow test cases step-by-step)

**How to Use**:
- Operator #1: Read TC-NAV-001 to TC-NAV-007 sections
- Operator #2: Read TC-UX-001 to TC-UX-008 sections
- Operator #3: Read TC-INT-001 to TC-INT-006 sections
- All operators: Read "Test Execution Guidelines" and "Defect Reporting" sections

---

### Operator Report Template
**File**: `/docs/uat/UAT_OPERATOR_REPORT_TEMPLATE.md`

**Purpose**: Standardized template for operators to document test results, defects, observations, and recommendations.

**Key Sections**:
- Executive summary (pass/fail, statistics)
- Test environment configuration
- Detailed test results (for each test case)
- Defect log (structured defect entries)
- Exploratory testing results
- Performance observations
- Accessibility observations
- Browser/device specific issues
- Positive findings
- Areas of concern
- Final assessment and recommendations

**Who Should Read**: UAT Operators (to fill out), UAT Manager (to review), Developers (to understand defects)

**When to Use**: After completing test execution, each operator copies this template and fills it out with their results

**Output Files**:
- `/docs/uat/UAT_NAV_OPERATOR_1_REPORT.md`
- `/docs/uat/UAT_NAV_OPERATOR_2_REPORT.md`
- `/docs/uat/UAT_NAV_OPERATOR_3_REPORT.md`

---

## Test Campaign Summary

### What Changed
A major frontend refactoring replaced the dual navigation system with a unified sidebar architecture:

**Removed Components**:
- `Navbar.jsx` (old top navigation)
- `DynamicMenu.jsx` (old sidebar implementation)

**Added Components**:
- `NavigationContext.jsx` - Centralized state management (sidebar/drawer state, menu data)
- `TopBar.jsx` - 60px utility bar (hamburger, logo, search, user menu)
- `Sidebar.jsx` - Desktop navigation (250px expanded, 60px collapsed)
- `Drawer.jsx` - Mobile navigation (slide-in overlay, 280px width)
- `NavigationItem.jsx` - Recursive menu component with accordion support

**Modified Components**:
- `App.jsx` - New AppLayout component integrating TopBar + Sidebar + Drawer

### Test Objectives
1. Verify ZERO functional regressions (all existing navigation features work)
2. Ensure UX consistency across all screen sizes (desktop, tablet, mobile)
3. Validate WCAG Level AA accessibility compliance (keyboard nav, ARIA, contrast)
4. Confirm backend menu API integration remains intact
5. Check performance (no degradation, no memory leaks)

### Test Coverage
- **21 test cases** across 3 focus areas
- **3 parallel operators** executing independently
- **Estimated duration**: 15 minutes (parallel execution)

### Pass/Fail Criteria
- **PASS**: 0 CRITICAL defects, ≤2 HIGH defects, all core flows functional
- **FAIL**: Any CRITICAL defect, >5 HIGH defects, accessibility violations

---

## Test Environment

### URLs
- **Frontend**: http://192.168.1.2:3002/
- **Backend**: http://192.168.1.2:8000/
- **API Base**: http://192.168.1.2:8000/api/v1

### Credentials
- **Admin**: `admin` / `admin123`

### Known Pre-existing Issues
- Backend has SQLAlchemy cross-module relationship error (NOT related to navigation refactor)
- Platform menu API may return limited items due to backend issue
- This is documented and will not block navigation UAT

### Environment Status (as of 2025-12-04)
- ✅ Frontend: Running and accessible (Status: 200 OK)
- ⚠️ Backend: DOWN (needs restart before testing)

### Pre-Test Checklist
- [ ] Backend server running: `curl http://192.168.1.2:8000/health`
- [ ] Frontend accessible: `curl http://192.168.1.2:3002/`
- [ ] Login credentials verified: admin / admin123
- [ ] Browser DevTools ready (F12)
- [ ] Screenshot tools prepared
- [ ] Test plan read by all operators
- [ ] Defect reporting format understood

---

## Operator Roles and Responsibilities

### Operator #1: Navigation Regression Testing
**Focus**: Core navigation functionality

**Test Cases**: TC-NAV-001 to TC-NAV-007 (7 test cases)

**Key Responsibilities**:
- Test desktop sidebar collapse/expand
- Test mobile drawer open/close
- Verify menu API integration
- Test hierarchical menu accordion
- Validate keyboard navigation (TAB, ESC, ENTER, ARROW)
- Test TopBar components
- Verify old navigation components removed

**Duration**: ~10 minutes

**Priority**: CRITICAL

**Output**: `/docs/uat/UAT_NAV_OPERATOR_1_REPORT.md`

---

### Operator #2: UI/UX Consistency Testing
**Focus**: Responsive design, visual consistency, user experience

**Test Cases**: TC-UX-001 to TC-UX-008 (8 test cases)

**Key Responsibilities**:
- Test all responsive breakpoints (320px to 1920px)
- Verify touch target sizes (≥44x44px on mobile)
- Check visual consistency across all routes
- Test loading and error states
- Validate animation smoothness (60fps target)
- Verify focus and hover states
- Check color contrast (WCAG AA compliance)
- Measure cumulative layout shift (CLS ≤0.1)

**Duration**: ~12 minutes

**Priority**: HIGH

**Output**: `/docs/uat/UAT_NAV_OPERATOR_2_REPORT.md`

---

### Operator #3: Integration & End-to-End Testing
**Focus**: Authentication integration, cross-route workflows, backend API

**Test Cases**: TC-INT-001 to TC-INT-006 (6 test cases)

**Key Responsibilities**:
- Test authentication integration (login/logout flows)
- Execute cross-route navigation workflows
- Verify backend menu API integration
- Test module system integration
- Check browser compatibility (Chrome, Firefox, Safari, Edge)
- Measure performance and memory usage

**Duration**: ~15 minutes

**Priority**: CRITICAL

**Output**: `/docs/uat/UAT_NAV_OPERATOR_3_REPORT.md`

---

## Defect Severity Definitions

### CRITICAL (🔴 P0)
**Definition**: Blocks core functionality, makes app unusable, causes data loss, or creates security vulnerability

**Examples**:
- Cannot open sidebar/drawer
- App crashes on navigation
- Menu doesn't load with no error message
- Authentication broken
- XSS vulnerability in menu rendering

**Response**: IMMEDIATE FIX REQUIRED - Block deployment, assign developer, fix within 1 hour

---

### HIGH (🟠 P1)
**Definition**: Major feature broken, no reasonable workaround, significantly impacts user experience

**Examples**:
- Active route highlighting broken on all routes
- Keyboard navigation completely non-functional
- Drawer doesn't close on overlay click (mobile)
- Menu API returns data but doesn't render
- Sidebar state not persisted in localStorage

**Response**: FIX BEFORE DEPLOY - Must fix or provide documented workaround

---

### MEDIUM (🟡 P2)
**Definition**: Feature partially works, workaround exists, minor impact on user experience

**Examples**:
- Animation stutters slightly on low-end devices
- Active state missing on one specific route
- Text overflows by 2px in collapsed mode
- Menu accordion animation not smooth
- Focus indicator barely visible

**Response**: FIX IN NEXT SPRINT - Deploy with issue, create GitHub issue, prioritize in backlog

---

### LOW (🟢 P3)
**Definition**: Cosmetic issue only, no functional impact, very minor UX issue

**Examples**:
- Icon alignment off by 2px
- Color contrast slightly below WCAG AA (but above Level A)
- Typo in error message
- Tooltip positioning slightly off
- Hover state transition 50ms slower than spec

**Response**: FIX WHEN CONVENIENT - Backlog, low priority, fix during refactoring or design updates

---

## Deliverables Timeline

### Before Test Execution
- ✅ Test Plan created: `/docs/uat/UAT_NAVIGATION_REFACTORING_PLAN.md`
- ✅ Quick Start Guide: `/docs/uat/UAT_NAVIGATION_QUICK_START.md`
- ✅ Executive Summary: `/docs/uat/UAT_NAVIGATION_EXECUTIVE_SUMMARY.md`
- ✅ Report Template: `/docs/uat/UAT_OPERATOR_REPORT_TEMPLATE.md`
- ✅ Screenshots directory: `/docs/uat/screenshots/nav-refactor/`
- ⏳ Environment verified
- ⏳ Operators briefed

### During Test Execution (parallel)
- ⏳ Operator #1 executes TC-NAV-001 to TC-NAV-007 (~10 min)
- ⏳ Operator #2 executes TC-UX-001 to TC-UX-008 (~12 min)
- ⏳ Operator #3 executes TC-INT-001 to TC-INT-006 (~15 min)
- ⏳ Real-time defect logs created
- ⏳ Screenshots captured for all defects

### After Test Execution
- ⏳ Operator reports completed (3 files)
- ⏳ Defect logs aggregated
- ⏳ Consolidated UAT report created
- ⏳ Executive summary updated with results
- ⏳ Pass/fail decision made
- ⏳ Stakeholder notification sent

---

## Success Metrics

### Quantitative Metrics
| Metric | Target | Measurement Method |
|--------|--------|-------------------|
| Test Pass Rate | ≥95% | (Passed tests / Total tests) × 100 |
| Defect Density | ≤2 defects/module | Critical + High defects / 3 operators |
| Zero Critical Defects | 0 | Count of CRITICAL severity defects |
| Performance Regression | ≤+10% | Compare load times before/after |
| Accessibility Score | ≥90/100 | Lighthouse Accessibility audit |
| Execution Time | ≤15 min | Actual parallel execution time |

### Qualitative Metrics
- Navigation feels intuitive and responsive
- Mobile drawer UX comparable to native apps
- No operator confusion about menu structure
- Keyboard navigation "just works"
- Visual consistency maintained across all routes

---

## Risk Assessment

### High-Risk Areas (Priority Testing)
1. **Mobile drawer functionality** (Medium likelihood, Critical impact)
   - Risk: Drawer doesn't open/close on mobile devices
   - Mitigation: Test on real devices, multiple browsers, swipe gestures

2. **Menu API integration failure** (Medium likelihood, Critical impact)
   - Risk: Menu doesn't load from backend, app becomes unusable
   - Mitigation: Mock responses, error handling tests, retry mechanisms

3. **Active route highlighting broken** (Low likelihood, High impact)
   - Risk: Users can't tell which page they're on
   - Mitigation: Test all routes, deep linking, browser back/forward

### Medium-Risk Areas
- Responsive breakpoint edge cases (767px vs 768px)
- Animation performance on low-end devices
- Browser compatibility (Safari webkit-specific bugs)
- Multi-tab localStorage sync issues
- Backend menu API returns unexpected format

### Low-Risk Areas
- Color contrast issues (already WCAG compliant in design)
- Minor CSS inconsistencies across routes
- Tooltip positioning edge cases
- Search bar functionality (if not yet implemented)

---

## Post-UAT Actions

### If PASS (0 CRITICAL, ≤2 HIGH defects)
1. ✅ Tech Lead approval and sign-off
2. ✅ Deploy to production (if applicable)
3. ✅ Update architecture documentation
4. ✅ Close refactor ticket in project management tool
5. ✅ Team retrospective (what went well, lessons learned)
6. ✅ Monitor production for 48 hours (watch for user-reported issues)
7. ✅ Create GitHub issues for MEDIUM/LOW defects (next sprint backlog)

### If FAIL (CRITICAL defects or >5 HIGH defects)
1. ❌ DO NOT DEPLOY - block production release
2. ❌ Triage all defects by severity
3. ❌ Assign ownership to developers
4. ❌ Fix CRITICAL defects (within 1-4 hours)
5. ❌ Execute targeted regression tests on fixes
6. ❌ If fixes extensive, re-run full UAT
7. ❌ If fixes impossible short-term, execute rollback plan
8. ❌ Document lessons learned, update refactor checklist

### Rollback Plan (if needed)
1. Revert to pre-refactor git commit (tag: `pre-nav-refactor`)
2. Restore old navigation files: `Navbar.jsx`, `DynamicMenu.jsx`
3. Re-run quick smoke test on old version
4. Deploy old version to unblock users
5. Schedule refactor fix for next sprint
6. Root cause analysis and retrospective

---

## Contact and Support

### For Questions About Test Plan
- **Author**: Claude Code QA Specialist
- **Test Plan Location**: `/docs/uat/UAT_NAVIGATION_REFACTORING_PLAN.md`
- **Documentation Index**: This file (`README_UAT_NAVIGATION.md`)

### For Environment Issues
- **Frontend not accessible**: Check `/docs/uat/UAT_NAVIGATION_QUICK_START.md` → "Common Issues and Quick Fixes"
- **Backend not responding**: Restart backend server (instructions in Quick Start)
- **Login issues**: Verify credentials admin/admin123, clear localStorage

### For Defect Reporting Issues
- **Template**: `/docs/uat/UAT_OPERATOR_REPORT_TEMPLATE.md`
- **Severity guide**: See "Defect Severity Definitions" section above
- **Screenshots location**: `/docs/uat/screenshots/nav-refactor/`

---

## Version History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-12-04 | Claude Code QA | Initial test plan creation |
| | | | - Created 4 documentation files |
| | | | - Defined 21 test cases |
| | | | - Established 3 operator roles |
| | | | - Set pass/fail criteria |

---

## File Locations Reference

### Planning Documents (Created)
```
/home/htpc/test/gestione-affitti/docs/uat/
├── README_UAT_NAVIGATION.md (this file)
├── UAT_NAVIGATION_REFACTORING_PLAN.md (44 pages)
├── UAT_NAVIGATION_QUICK_START.md (8 pages)
├── UAT_NAVIGATION_EXECUTIVE_SUMMARY.md (6 pages)
├── UAT_OPERATOR_REPORT_TEMPLATE.md (6 pages)
└── screenshots/
    └── nav-refactor/ (empty, ready for screenshots)
```

### Reports (To Be Created During/After Testing)
```
/home/htpc/test/gestione-affitti/docs/uat/
├── UAT_NAV_OPERATOR_1_REPORT.md (after testing)
├── UAT_NAV_OPERATOR_2_REPORT.md (after testing)
├── UAT_NAV_OPERATOR_3_REPORT.md (after testing)
├── UAT_NAVIGATION_CONSOLIDATED_REPORT.md (after testing)
└── NAV_DEFECTS_CONSOLIDATED.csv (if defects found)
```

### Source Code Reference
```
/home/htpc/test/gestione-affitti/frontend/src/
├── contexts/
│   └── NavigationContext.jsx (state management)
├── components/
│   ├── Layout/
│   │   └── TopBar.jsx (utility bar)
│   └── Navigation/
│       ├── Sidebar.jsx (desktop nav)
│       ├── Drawer.jsx (mobile nav)
│       └── NavigationItem.jsx (recursive menu)
└── App.jsx (layout integration)
```

---

## Quick Command Reference

### Check Environment
```bash
# Frontend status
curl -I http://192.168.1.2:3002/

# Backend status
curl http://192.168.1.2:8000/health

# Backend API docs
curl http://192.168.1.2:8000/docs
```

### Start Servers (if needed)
```bash
# Backend
cd /home/htpc/test/gestione-affitti/backend
source venv/bin/activate
python app/main.py

# Frontend
cd /home/htpc/test/gestione-affitti/frontend
npm run dev -- --port 3002 --host 0.0.0.0
```

### View Documentation
```bash
# Full test plan
cat /home/htpc/test/gestione-affitti/docs/uat/UAT_NAVIGATION_REFACTORING_PLAN.md | less

# Quick start
cat /home/htpc/test/gestione-affitti/docs/uat/UAT_NAVIGATION_QUICK_START.md | less

# Executive summary
cat /home/htpc/test/gestione-affitti/docs/uat/UAT_NAVIGATION_EXECUTIVE_SUMMARY.md | less
```

---

## Status: READY FOR EXECUTION

**Next Action**: Review this README, then proceed to Quick Start Guide to launch operators

**Confidence**: HIGH - Comprehensive test plan with realistic scenarios

**Recommendation**: PROCEED WITH UAT

---

**END OF DOCUMENTATION INDEX**
