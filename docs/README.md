# Gestione Affitti Documentation

Welcome to the comprehensive documentation portal for Gestione Affitti - a modular web application for managing rental properties with a FastAPI backend and React frontend.

## Quick Start

| Progetto | README |
|----------|--------|
| **Frontend** | [frontend/README.md](../frontend/README.md) - Installazione e avvio React |
| **Backend** | [backend/README.md](../backend/README.md) - Installazione e avvio FastAPI |
| **Tests** | [tests/README.md](../tests/README.md) - Esecuzione test UAT |

## Quick Navigation by Role

### For New Developers
1. Start with `/README.md` (project overview)
2. Read `/CLAUDE.md` (development patterns and architecture)
3. Review `setup/DEPLOYMENT_GUIDE.md` (environment setup)
4. Explore `architecture/` (system design)

### For Backend Developers
1. `architecture/BACKEND_DOMAIN_REFACTORING_COMPLETED.md` - Module architecture
2. `guides/MODULE_DEVELOPMENT_GUIDE.md` - Creating new modules
3. `architecture/MODULE_STRUCTURE.md` - Module patterns and conventions
4. `guides/TESTING.md` - Testing strategies

### For Frontend Developers
1. `guides/WIDGET_DEVELOPMENT_GUIDE.md` - Widget system and dashboard components
2. `guides/IMPORT_WIZARD_IMPLEMENTATION.md` - Import system frontend
3. `guides/TESTING.md` - Frontend testing
4. `features/` - Feature-specific implementation details

### For DevOps / System Administrators
1. `setup/DEPLOYMENT_GUIDE.md` - Production deployment
2. `multi-tenancy/` - Multi-tenancy architecture and setup
3. `setup/MIGRATION.md` - Database migrations

### For Product Managers / QA
1. `features/` - Feature documentation and requirements
2. `uat/` - User acceptance testing reports and results
3. `ux/` - UX audit and improvement reports

## Documentation Structure

```
docs/
├── README.md                           # This file - documentation portal
├── FILE_INDEX.md                       # Complete index of all docs
│
├── setup/                              # Installation & Deployment
│   ├── README.md
│   ├── DEPLOYMENT_GUIDE.md            # Production deployment guide
│   ├── MIGRATION.md                   # Database migrations
│   ├── IMPORT_AUTOMATISMI_QUICK_START.md
│   └── MIGRAZIONE_SOGGETTI_ANAGRAFICI.md
│
├── architecture/                       # System Design & Architecture
│   ├── README.md
│   ├── CORE_COMPONENTS_ARCHITECTURE.md # Reusable core components (NEW)
│   ├── BACKEND_DOMAIN_REFACTORING_COMPLETED.md  # Module architecture
│   ├── MODULE_STRUCTURE.md             # Module patterns
│   ├── SYSTEM_CONSOLIDATION_REPORT.md  # System consolidation
│   ├── MODULE_SYSTEM_TEST_REPORT.md    # Module system testing
│   ├── NAVIGATION_ARCHITECTURE_DECISION.md
│   ├── NAVIGATION_QUICK_REFERENCE.md
│   └── NAVIGATION_COMPARISON.md
│
├── multi-tenancy/                      # Multi-Tenancy Implementation (NEW)
│   ├── README.md                       # Multi-tenancy overview
│   ├── MULTI_TENANT_MIGRATION_ANALYSIS.md
│   ├── MULTI_TENANT_IMPLEMENTATION_PROGRESS.md
│   ├── MULTI_TENANT_ADVANCED_FEATURES.md
│   └── MULTI_TENANT_STATUS.md
│
├── guides/                             # Development Guides
│   ├── README.md
│   ├── MODULE_DEVELOPMENT_GUIDE.md     # How to create modules
│   ├── WIDGET_DEVELOPMENT_GUIDE.md     # Widget system (NEW LOCATION)
│   ├── IMPORT_WIZARD_IMPLEMENTATION.md # Import system frontend
│   ├── IMPORT_WIZARD_FRONTEND_README.md
│   ├── IMPORT_WIZARD_FRONTEND_QUICKSTART.md
│   ├── CHANGELOG_IMPORT_WIZARD.md
│   └── TESTING.md                      # Testing strategies
│
├── api/                                # API Documentation
│   ├── README.md
│   ├── IMPORT_SYSTEM_DESIGN.md         # Import API design
│   ├── ANALISI_FUNZIONALE_AUTOMATISMI_IMPORT.md
│   ├── IMPORT_WIZARD_QUICK_REFERENCE.md # API quick reference
│   └── IMPORT_WIZARD_IMPROVEMENTS.md
│
├── features/                           # Feature Documentation
│   ├── README.md
│   ├── DESIGN_ARCHITETTURALE_AUTOMATISMI.md   # Automatismi design
│   ├── REPORT_FINALE_AUTOMATISMI_IMPORT.md    # Import system report
│   ├── REPORT_TEST_COMPLETO_AUTOMATISMI.md    # Test results
│   ├── GUIDA_COMUNI_E_INDIRIZZI.md            # Address normalization
│   ├── UX_REVIEW_IMPORT_WIZARD.md              # UX review
│   ├── ANAGRAFICA_ANALISI_TECNICO_FUNZIONALE.md
│   ├── ANAGRAFICA_GAP_ANALYSIS.md
│   ├── ANAGRAFICA_RUOLI_AZIENDA.md
│   ├── ANAGRAFICA_USER_INTEGRATION.md
│   ├── ANAGRAFICA_VERIFICA_IMPLEMENTAZIONE.md
│   ├── SCADENZARIO_ANALISI_TECNICO_FUNZIONALE.md
│   ├── SCADENZARIO.md
│   ├── SCADENZARIO_PROJECT_COMPLETION_REPORT.md
│   ├── UAT_SCADENZARIO_CHECKLIST.md
│   └── UAT_TEST_PLANS_SCADENZARIO.md
│
├── reference/                          # Technical Reference & Reports
│   ├── README.md
│   ├── IMPLEMENTATION_PLAN.md           # Implementation planning
│   ├── IMPLEMENTATION_SUMMARY.md        # Implementation summary
│   ├── IMPLEMENTAZIONE_SISTEMA_IMPORT_REPORT.md
│   ├── FRONTEND_TESTING_REPORT.md       # Frontend testing results
│   ├── FRONTEND_REFACTORING_COMPLETE.md # Frontend refactoring
│   ├── REPORT_FIX_UAT_ISSUES.md         # UAT issue fixes
│   ├── REPORT_FRONTEND_INTEGRATION.md   # Frontend integration
│   ├── DOCUMENTATION_REORGANIZATION_SUMMARY.md
│   ├── CRITICAL_FIX_REQUIRED.md
│   ├── TEST_RESULTS_INDEX.md
│   ├── TEST_EXECUTION_COMPLETE.txt
│   ├── DELIVERABLES.txt
│   ├── FINAL_TEST_REPORT_SUMMARY.txt
│   ├── refactoring_report.md
│   └── CLAUDE_ARCHIVED.md
│
├── uat/                                # User Acceptance Testing (NEW LOCATION)
│   ├── README.md
│   ├── UAT_CONSOLIDATED_REPORT_FINAL.md
│   ├── UAT_EXECUTIVE_SUMMARY.txt
│   ├── UAT_NAVIGATION_EXECUTIVE_SUMMARY.md
│   ├── UAT_NAVIGATION_REFACTORING_PLAN.md
│   ├── UAT_FIXES_APPLIED.md
│   ├── UAT_AFFITTI_LUNGO_REGRESSION_MANUAL.md
│   ├── UAT_TEST_EXECUTION_TC-001_2025-12-10.md
│   ├── UAT_REPORT_TC-004.md
│   ├── UAT_IMMOBILI_EXECUTIVE_SUMMARY.md
│   └── [More UAT reports...]
│
├── ux/                                 # UX & Design
│   ├── README.md
│   ├── UX_REVIEW_REPORT_2025-12-25.md   # Core components UX review (NEW)
│   ├── UX_GUIDELINES.md                 # UI/UX guidelines (NEW)
│   ├── UX_IMPROVEMENTS_IMPLEMENTED.md   # Implementation summary (NEW)
│   ├── UX_AUDIT_REPORT_2025-12-04.md   # UX audit findings
│   ├── UX_OPTIMIZATION_PLAN.md          # Optimization recommendations
│   ├── UX_QUICK_FIXES.md                # Quick fix implementations
│   ├── QUICK_FIXES_IMPLEMENTED.md       # Implementation status
│   ├── ALL_QUICK_FIXES_COMPLETED.md     # Completion summary
│   └── UX_IMPROVEMENTS_SUMMARY.txt
│
├── modules/                            # Module Documentation
│   ├── README.md                       # Module index and links
│   └── [Future: Module-specific docs]
│
├── frontend/                           # Frontend Documentation (NEW)
│   └── README.md                       # Frontend architecture and conventions
│
├── deployment/                         # Deployment & Fixes (NEW)
│   ├── DEPLOYMENT_CHECKLIST.md        # Pre-deployment checklist
│   ├── FIXES_SUMMARY.md               # Summary of bug fixes
│   ├── README_FIXES.md                # Fix documentation
│   └── REGRESSION_FIXES_2025-12-26.md # Regression fixes
│
└── obsolete/                           # Archived Documentation
    ├── README.md                       # Why docs are archived
    ├── 2025-12-04/                     # Dated archive
    │   └── [Old UAT reports and superseded documentation]
    └── 2025-12-10/                     # Dated archive (for future use)
```

## Key Features by Section

### Setup (Getting Started)
- Environment setup and configuration
- Database setup and migrations
- Deployment procedures for production
- Data migration guides

### Architecture (System Design)
- Module system and patterns
- Backend domain refactoring details
- Navigation architecture decisions
- System consolidation progress
- Multi-tenancy implementation

### Multi-Tenancy (NEW)
- Schema-based tenant isolation
- Tenant context management
- JWT-based tenant switching
- Advanced features and configuration

### Guides (Development How-Tos)
- Creating new modules
- Widget development and dashboard components
- Import wizard implementation (frontend)
- Testing strategies and conventions

### API Documentation
- Import system API design
- Functional analysis of automatisms
- Quick reference for API integration

### Features (Feature Documentation)
- Import automatisms design and testing
- Address normalization guide
- Anagrafica (Italian registry) analysis and implementation
- Scadenzario (Scheduler) requirements and testing
- UX reviews and user feedback

### Reference (Technical Details)
- Implementation plans and summaries
- Frontend testing and refactoring reports
- Issue fix documentation
- Code consolidation reports

### UAT (Testing & Validation)
- User acceptance test reports
- Test execution summaries
- Navigation refactoring results
- Regression test results
- Executive summaries for stakeholders

### UX (User Experience)
- UX audit findings and recommendations
- Quick fix implementations and tracking
- Improvements summary

### Modules (Module-Specific Info)
- Index of all modules
- Module-specific documentation
- Links to module development guides

### Obsolete (Historical)
- Superseded UAT reports
- Old documentation archived by date
- Historical reference material

## Important Core Files (Root Level)

| File | Purpose |
|------|---------|
| **README.md** | Project overview, features, and installation steps |
| **CLAUDE.md** | Developer guide with architecture patterns and conventions |

Always start with these files for project context.

## Recent Changes (December 2025)

### December 26 - Core Components & UX Documentation
**New Files Added:**
- Moved `CORE_COMPONENTS_ARCHITECTURE.md` to `docs/architecture/` - Reusable frontend components
- Moved `UX_REVIEW_REPORT.md` to `docs/ux/UX_REVIEW_REPORT_2025-12-25.md` - Core components UX review
- Moved `UX_GUIDELINES.md` to `docs/ux/` - UI/UX development guidelines
- Moved `UX_IMPROVEMENTS_IMPLEMENTED.md` to `docs/ux/` - Implementation summary of UX fixes

**Archival (December 26):**
- Archived `DOCUMENTATION_COMPLETE.md` to `docs/obsolete/2025-12-26/`
- Archived `DOCUMENTATION_REORGANIZATION_2025-12-10.md` to `docs/obsolete/2025-12-26/`
- Archived `REORGANIZATION_SUMMARY.txt` to `docs/obsolete/2025-12-26/`
- Created `docs/obsolete/2025-12-26/README.md` to explain archived content

**Updates:**
- Updated `CLAUDE.md` with new documentation links
- Updated `docs/architecture/README.md` with core components info
- Updated `docs/ux/README.md` with new UX files
- Cleaned up project root - only essential README.md and CLAUDE.md remain

### Previous Changes (December 10)
### Documentation Reorganization
- Moved WIDGET_DEVELOPMENT_GUIDE.md to `docs/guides/`
- Moved all MULTI_TENANT_*.md files to new `docs/multi-tenancy/` directory
- Consolidated ANAGRAFICA_*.md files in `docs/features/`
- Consolidated SCADENZARIO_*.md files in `docs/features/`
- Consolidated all UAT_*.md and UAT_*.txt files in `docs/uat/`
- Consolidated reference reports in `docs/reference/`
- Created comprehensive README files for new directories
- Updated CLAUDE.md with new file paths

### New Directory Structure
- `docs/multi-tenancy/` - Complete multi-tenancy documentation
- `docs/modules/` - Module documentation index
- Enhanced `docs/README.md` with role-based navigation

## Navigation Tips

1. **By Task:**
   - Need to deploy? → `setup/DEPLOYMENT_GUIDE.md`
   - Need to add a module? → `guides/MODULE_DEVELOPMENT_GUIDE.md`
   - Need to create widgets? → `guides/WIDGET_DEVELOPMENT_GUIDE.md`
   - Need to understand architecture? → `architecture/BACKEND_DOMAIN_REFACTORING_COMPLETED.md`

2. **By Feature:**
   - Import System: `features/` + `api/`
   - Multi-Tenancy: `multi-tenancy/`
   - Module Development: `architecture/` + `guides/`
   - Widgets & Dashboard: `guides/WIDGET_DEVELOPMENT_GUIDE.md`
   - Address Management: `features/GUIDA_COMUNI_E_INDIRIZZI.md`

3. **By Document Type:**
   - Quick Start: Look for files with "QUICK" or "QUICKSTART" in the name
   - Executive Summary: Look for "EXECUTIVE_SUMMARY" or "SUMMARY" in the name
   - Test Results: See `uat/` and `reference/` directories
   - Architecture: See `architecture/` and `multi-tenancy/` directories

4. **Search:**
   - Use `Ctrl+F` to search this README for keywords
   - See `FILE_INDEX.md` for a complete index of all documentation files

## For Questions or Updates

- Refer to the root-level `CLAUDE.md` file for development patterns
- Check the specific README files in each documentation directory
- See individual documents for detailed information

---

**Last Updated:** January 5, 2026
**Status:** Production Ready
**Next Review:** As needed after feature implementations
