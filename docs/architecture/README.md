# Architecture & System Design Documentation

This directory contains comprehensive documentation of the Gestione Affitti system architecture, module structure, and major refactoring initiatives.

## Quick Navigation

For understanding the system architecture:

1. **Start Here:** `BACKEND_DOMAIN_REFACTORING_COMPLETED.md` - Overview of the modular architecture
2. **Core Components:** `CORE_COMPONENTS_ARCHITECTURE.md` - Reusable frontend components (DataTable, FormBuilder, FormModal)
3. **System Structure:** `MODULE_STRUCTURE.md` - Detailed module organization
4. **Consolidation Details:** `SYSTEM_CONSOLIDATION_REPORT.md` - How modules were consolidated
5. **Testing:** `MODULE_SYSTEM_TEST_REPORT.md` - Test results for module system

## Files in This Directory

### CORE_COMPONENTS_ARCHITECTURE.md
Documentation of the reusable core components architecture that eliminates duplication across the frontend.

**Contents:**
- Analysis of code duplication patterns in existing modules
- Architecture for DataTable (list components with pagination, filtering, actions)
- Architecture for FormBuilder (configuration-driven form generation)
- Architecture for FormModal (reusable modal component)
- Configuration-driven approach to reduce repetitive code
- Benefits of the core components approach
- Implementation examples

**Key Sections:**
- List Components Pattern - DataTable for displaying entity lists
- Form Components Pattern - FormBuilder for dynamic form generation
- Modal Pattern - FormModal with lifecycle management
- Configuration Schema - How to define components declaratively

**For:** Frontend developers, architects, anyone building new modules

### BACKEND_DOMAIN_REFACTORING_COMPLETED.md
Complete documentation of the backend refactoring that established the current modular architecture.

**Contents:**
- Overview of the modular platform architecture
- Core system (platform-agnostic) vs. Business modules (pluggable)
- Three-module setup: anagrafica_italiana, immobili, affitti_lungo
- Module dependency structure
- Cross-module relationships and patterns
- Database consolidation
- Migration from old architecture
- Key architectural principles

**Key Sections:**
- Platform Core Design - Database setup, authentication, module system
- Module Dependencies - How modules depend on each other
- Entity Relationships - Cross-module entity linking
- Module Patterns - Standard module structure and conventions

**For:** Architects, senior developers, anyone understanding system structure

### MODULE_STRUCTURE.md
Detailed reference for the module directory structure and layout.

**Contents:**
- Directory organization
- File structure for each module
- Required files and patterns
- Location of models, schemas, routes
- How modules are discovered and loaded
- Configuration and metadata

**For:** Developers creating new modules, code reviewers

### SYSTEM_CONSOLIDATION_REPORT.md
Report on the consolidation of modules into unified locations.

**Contents:**
- Consolidation goals and approach
- Changes made to module structure
- Migration procedures
- Before and after comparisons
- Impact on development workflow
- Benefits of consolidation

**For:** Developers who need to understand changes, DevOps engineers

### MODULE_SYSTEM_TEST_REPORT.md
Testing and validation report for the modular system.

**Contents:**
- Test plan and scope
- Test results
- Module loading and discovery tests
- Dependency resolution tests
- Cross-module communication tests
- Performance metrics

**For:** QA engineers, developers validating system changes

## Architecture Overview

The Gestione Affitti platform follows a **modular platform architecture**:

```
PLATFORM (Domain-Agnostic Core)
├── Authentication & Authorization
├── Database Management
├── Module System & Discovery
├── Platform Services (Menu, Dashboard)
└── Configuration

BUSINESS MODULES (Pluggable)
├── anagrafica_italiana (Persons & Companies)
├── immobili (Real Estate Properties)
└── affitti_lungo (Rental Management)
    ├── Depends on: immobili, anagrafica_italiana
    ├── Models: Contratto, Affittuario, Incasso, Spesa
    └── Routes: RESTful API endpoints
```

## Key Concepts

### 1. Platform Core
The core provides only platform-level services:
- Database connection management
- Authentication/Authorization
- Module discovery and loading system
- Generic platform services (menu, dashboard)

### 2. Business Modules
Modules contain all business logic:
- Domain-specific models (Contratto, Immobile, etc.)
- API routes and endpoints
- Services for business logic
- Database migrations for module tables

### 3. Module Dependencies
Modules declare dependencies in `__manifest__.py`:
- `affitti_lungo` depends on `immobili` and `anagrafica_italiana`
- `immobili` depends on `anagrafica_italiana`
- `anagrafica_italiana` has no dependencies

### 4. Cross-Module Communication
Modules can import models from dependent modules:
```python
from immobili.models import UnitaImmobiliare
from anagrafica_italiana.models import SoggettoAnagrafico
```

## Module Details

### anagrafica_italiana (Italian Registry)
- **Purpose:** Manages persons (persone fisiche) and companies (persone giuridiche)
- **Location:** `backend/modules/anagrafica_italiana/`
- **Key Models:** SoggettoAnagrafico, TipoSoggetto
- **Dependencies:** None

### immobili (Real Estate Properties)
- **Purpose:** Manages properties, ownership, cadastral data, condominiums
- **Location:** `backend/modules/immobili/`
- **Key Models:** UnitaImmobiliare, Condominio, Proprietario, CategoriaCatastale, ComuneItalia
- **Dependencies:** anagrafica_italiana

### affitti_lungo (Long-term Rentals)
- **Purpose:** Manages rental contracts, tenants, income, expenses
- **Location:** `backend/modules/affitti_lungo/`
- **Key Models:** Contratto, Affittuario, Incasso, Spesa, Tecnico, Documento
- **Dependencies:** immobili, anagrafica_italiana

## Adding New Modules

To create a new module:

1. Create directory in `backend/modules/{module_name}/`
2. Create `__manifest__.py` with module metadata
3. Create subdirectories: `models/`, `schemas/`, `routes/`
4. Define SQLAlchemy models
5. Implement API routes
6. Module is auto-discovered at startup

See `docs/guides/MODULE_DEVELOPMENT_GUIDE.md` for detailed instructions.

## Database Schema

Each module manages its own database tables and migrations:

- **Platform tables:** Core database tables (users, roles, etc.)
- **Module tables:** Each module defines its own tables
- **Shared tables:** Some tables (e.g., categorie_catastali) are used by multiple modules

## Development Patterns

### 1. Database Sessions
All route handlers receive database session via dependency injection:
```python
from app.core.database import get_db

@router.get("/items/")
async def list_items(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return db.query(Item).offset(skip).limit(limit).all()
```

### 2. Cross-Module Imports
Modules can import from their dependencies:
```python
import sys
import os
modules_dir = os.path.join(os.path.dirname(__file__), '../../modules')
if modules_dir not in sys.path:
    sys.path.insert(0, modules_dir)

from immobili.models import UnitaImmobiliare
```

### 3. Module Registration
Each module implements optional `register_module(app)` function called at startup:
```python
def register_module(app):
    """Called by module loader during startup"""
    print(f"[{manifest['name']}] Module registered!")
```

## Testing the Architecture

To verify the modular architecture:

1. Check module discovery: Start backend and verify all modules load
2. Validate dependencies: Modules load in correct order
3. Test cross-module queries: Query entities from different modules
4. Performance check: Ensure no performance degradation

See `MODULE_SYSTEM_TEST_REPORT.md` for test results.

## Common Issues & Solutions

### Module Not Loading
- Check `__manifest__.py` exists and is valid
- Verify module is in `backend/modules/` directory
- Check for circular dependencies

### Cross-Module Import Errors
- Verify dependent module exists and is loaded
- Check sys.path is set up correctly in module
- Ensure models are properly exported from modules

### Database Connection Issues
- Verify DATABASE_URL environment variable is set
- Check PostgreSQL is running
- Review database migration status

## References

- Root `CLAUDE.md` - Development patterns and conventions
- `docs/guides/MODULE_DEVELOPMENT_GUIDE.md` - Creating new modules
- `docs/setup/DEPLOYMENT_GUIDE.md` - Deployment information
- `docs/features/DESIGN_ARCHITETTURALE_AUTOMATISMI.md` - Import system architecture

---

**Last Updated:** 2025-12-26
**Architecture Version:** 2.0 (Modular Platform)
**Status:** Production Ready
**Core Components:** Added December 26, 2025
