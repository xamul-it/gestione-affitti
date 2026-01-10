# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Gestione Affitti is a modular web application for managing rental properties. The project uses a FastAPI backend with PostgreSQL and a React frontend with Vite.

## Key Documentation

- **[WIDGET_DEVELOPMENT_GUIDE.md](./docs/guides/WIDGET_DEVELOPMENT_GUIDE.md)** - Complete guide for creating modular dashboard widgets
- **[CORE_COMPONENTS_ARCHITECTURE.md](./docs/architecture/CORE_COMPONENTS_ARCHITECTURE.md)** - Reusable core components architecture (DataTable, FormBuilder, FormModal)
- **[BACKEND_DOMAIN_REFACTORING_COMPLETED.md](./docs/architecture/BACKEND_DOMAIN_REFACTORING_COMPLETED.md)** - Backend modular architecture
- **[UX Guidelines](./docs/ux/)** - UX/UI guidelines, audit reports, and improvements
- **[Documentation Index](./docs/)** - Complete documentation portal with all guides and references

## Development Commands

### Backend (FastAPI + PostgreSQL)

```bash
# Setup
cd backend
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your DATABASE_URL and SECRET_KEY

# Run development server (with auto-reload)
python app/main.py
# or use the provided script:
./start.sh

# Run with gunicorn (production)
gunicorn -w 4 -k uvicorn.workers.UvicornWorker app.main:app
```

Backend runs on `http://localhost:8000`
API docs available at `http://localhost:8000/docs`

### Frontend (React + Vite)

```bash
# Setup
cd frontend
npm install

# Run development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

Frontend runs on `http://localhost:3000` (configured in vite.config.js)

## Architecture

### Backend Structure - Modular Platform

The backend is a **domain-agnostic platform** with pluggable business modules. The core provides only platform services, while all business logic lives in optional modules.

```
backend/
├── app/
│   ├── core/                       # PLATFORM CORE (domain-agnostic)
│   │   ├── config.py              # Settings (DATABASE_URL, CORS, etc)
│   │   ├── database.py            # SQLAlchemy setup (Base, get_db)
│   │   ├── auth/                  # Authentication & authorization
│   │   ├── module_system/         # Dynamic module loader
│   │   ├── platform_services/     # Menu, dashboard, widgets (generic)
│   │   └── models/
│   │       └── ruoli.py           # Platform-only: RuoloDisponibile, SoggettoRuolo
│   │
│   └── main.py                    # App initialization, module registration
│
└── modules/                        # BUSINESS MODULES (pluggable) ✓
    ├── anagrafica_italiana/        # Italian registry module
    │   ├── __manifest__.py        # Module metadata, dependencies
    │   ├── __init__.py            # register_module(app)
    │   ├── models/                # SoggettoAnagrafico, TipoSoggetto
    │   ├── schemas/
    │   └── routes/
    │
    ├── immobili/                   # Real estate properties module
    │   ├── __manifest__.py        # Dependencies: ["anagrafica_italiana"]
    │   ├── __init__.py
    │   ├── models/                # UnitaImmobiliare, Condominio, Proprietario
    │   │   ├── categoria_catastale.py
    │   │   ├── comune_italia.py
    │   │   └── ...
    │   ├── schemas/
    │   │   └── categoria_catastale.py
    │   ├── routes/
    │   │   └── categorie_catastali.py
    │   ├── services/              # Domain services
    │   │   ├── categoria_catastale_service.py
    │   │   └── codice_generator_service.py
    │   └── seeds/
    │       └── seed_categorie_catastali.py
    │
    └── affitti_lungo/             # Long-term rentals module
        ├── __manifest__.py        # Dependencies: ["immobili", "anagrafica_italiana"]
        ├── __init__.py
        ├── models/                # Affittuario, Contratto, Spesa, Incasso
        ├── schemas/
        ├── routes/
        └── roles.py
```

**✅ Module Consolidation Completed** (December 2025)

All business modules are now in a **single location**: `backend/modules/`
- ✅ anagrafica_italiana (Italian registry)
- ✅ immobili (Real estate properties + cadastral logic)
- ✅ affitti_lungo (Long-term rentals)

See `BACKEND_DOMAIN_REFACTORING_COMPLETED.md` for full refactoring details.

**Key Architecture Principles:**

1. **Core = Platform Only**
   - NO business logic in core
   - NO domain-specific models (no Italian data, no real estate)
   - Only: auth, module system, platform services, database setup

2. **Modules = Business Logic**
   - All domain logic in pluggable modules
   - Each module has: models, schemas, routes, manifest
   - Modules can depend on other modules

3. **Cross-Module Dependencies**
   ```python
   # affitti_lungo depends on immobili
   from immobili.models import UnitaImmobiliare, Condominio

   # immobili depends on anagrafica_italiana
   from anagrafica_italiana.models import SoggettoAnagrafico
   ```

4. **Module Structure**
   Every module must have:
   - `__manifest__.py` - Metadata (name, version, dependencies, permissions)
   - `__init__.py` - Export manifest and optional register_module()
   - `models/` - SQLAlchemy ORM models
   - `schemas/` - Pydantic validation schemas (optional)
   - `routes/` - FastAPI routers (optional)

**Key patterns:**

- **Database session:** Use `Depends(get_db)` to inject database sessions
- **Cross-module imports:** Add modules dir to sys.path, then import directly
- **Module registration:** Modules auto-discovered from `backend/modules/` directory
- **Dependencies:** Declared in manifest, loader ensures correct load order

### Frontend Structure - Modular Architecture ✅

The frontend is a **fully modular React SPA** mirroring the backend module system. Business logic is organized into self-contained modules, while shared platform components remain centralized.

```
frontend/src/
├── modules/                    # BUSINESS MODULES (self-contained) ✅
│   ├── anagrafica_italiana/    # Italian registry module
│   │   ├── components/        # (future - no UI yet)
│   │   ├── services/
│   │   │   └── anagraficaAPI.js
│   │   ├── manifest.js        # Module metadata, routes, permissions
│   │   └── index.js           # Module exports
│   │
│   ├── immobili/              # Real estate properties module ✅
│   │   ├── components/        # 8 directories, 24 files
│   │   │   ├── UnitaImmobiliari/
│   │   │   ├── Proprietari/
│   │   │   ├── Condomini/
│   │   │   ├── CertificatiEnergetici/
│   │   │   ├── DirittiImmobile/
│   │   │   ├── MillesimiImmobile/
│   │   │   ├── TabelleMillesimali/
│   │   │   └── CategorieCatastali/
│   │   ├── services/
│   │   │   └── immobiliAPI.js
│   │   ├── manifest.js
│   │   └── index.js           # Exports all components + APIs
│   │
│   └── affitti_lungo/         # Long-term rentals module ✅
│       ├── components/        # 6 directories, 18 files
│       │   ├── Affittuari/
│       │   ├── Contratti/
│       │   ├── Incassi/
│       │   ├── Spese/
│       │   ├── Tecnici/
│       │   └── Documenti/
│       ├── services/
│       │   └── affittiAPI.js
│       ├── manifest.js
│       └── index.js           # Exports all components + APIs
│
├── components/                # SHARED PLATFORM COMPONENTS
│   ├── Layout/                # Navigation and layout
│   ├── Platform/              # Dynamic menu, module system
│   ├── Auth/                  # Authentication components
│   └── Search/                # Global search
│
├── core/                      # PLATFORM CORE
│   └── modules/               # Module system infrastructure
│       ├── ModuleRegistry.js  # Dynamic module registration
│       ├── useModuleLoader.js # Auto-discovery via import.meta.glob
│       ├── DynamicRoutes.jsx  # Dynamic route system
│       └── ExtensionPoint.jsx # Extension point system
│
├── services/
│   └── api.js                 # Central API re-exports (backward compatibility)
│
├── pages/                     # Route-level page components
├── App.jsx                    # Router configuration
└── main.jsx                   # React entry point
```

**Key patterns:**

- **Module-first imports:** `import { UnitaImmobiliariList } from './modules/immobili'`
- **Module APIs:** Each module has its own API file (e.g., `immobiliAPI.js`, `affittiAPI.js`)
- **Central re-exports:** `services/api.js` re-exports all module APIs for backward compatibility
- **Auto-discovery:** Modules auto-discovered via `import.meta.glob('/src/modules/*/manifest.js')`
- **Cross-module dependencies:** Modules can import from each other (e.g., immobili → affitti_lungo for DocumentiSection)
- **Manifest-driven:** Each module declares routes, menu items, widgets, and permissions in manifest.js
- **Component organization:** Components grouped by module, then by entity
- **Lazy loading ready:** Module structure enables code splitting and lazy loading

**Module Benefits:**
- ✅ **Clear boundaries:** All property code in `immobili/`, all rental code in `affitti_lungo/`
- ✅ **Discoverability:** Easy to find code by domain
- ✅ **Maintainability:** Changes scoped to specific modules
- ✅ **Scalability:** Easy to add new modules following the pattern
- ✅ **Code splitting:** Modules can be lazy-loaded independently

### Current Modules

The platform currently has three business modules installed:

#### 1. Module: anagrafica_italiana
**Italian Registry for Persons and Companies**

- **Location:** `backend/modules/anagrafica_italiana/`
- **Dependencies:** None (fully independent)
- **Purpose:** Manages Italian persons (persone fisiche) and companies (persone giuridiche) with Italian-specific identifiers

**Entities:**
- **SoggettoAnagrafico**: Person or company with codice fiscale, partita IVA, contact info
- **TipoSoggetto**: Enum (PERSONA_FISICA, PERSONA_GIURIDICA)

**Key Features:**
- Codice Fiscale validation and uniqueness
- Partita IVA validation and uniqueness
- Unified registry for all subjects (can have multiple roles)
- Full CRUD API with permission checks

#### 2. Module: immobili
**Real Estate Property Management**

- **Location:** `backend/modules/immobili/`
- **Dependencies:** `anagrafica_italiana` (for Proprietario → SoggettoAnagrafico)
- **Purpose:** Manages properties, ownership, cadastral data, condominiums

**Entities:**
- **UnitaImmobiliare**: Property units (residential, commercial, etc.)
- **Condominio**: Condominium buildings
- **Proprietario**: Property owners (references SoggettoAnagrafico)
- **DirittoImmobile**: Property rights/ownership (links Proprietario to UnitaImmobiliare)
- **CertificatoEnergetico**: Energy performance certificates
- **TabellaMillesimale**: Millesimal tables for condominium expense distribution
- **MillesimiUnita**: Unit-level millesimal shares
- **CategoriaCatastale**: Italian cadastral categories (A/1, A/2, etc.)
- **ComuneItalia**: Italian municipalities for CAP lookup
- **TipoImmobileCategoriaMap**: Property type to cadastral category mappings

**Entity relationships:**
- UnitaImmobiliare → many DirittiImmobile, CertificatiEnergetici
- Condominio → many UnitaImmobiliare, TabellaMillesimale
- Proprietario → many DirittiImmobile (references SoggettoAnagrafico from anagrafica_italiana)

#### 3. Module: affitti_lungo
**Long-term Rental Management**

- **Location:** `backend/modules/affitti_lungo/`
- **Dependencies:** `immobili`, `anagrafica_italiana`
- **Purpose:** Manages rental contracts, tenants, income, and expenses

**Entities:**
- **Affittuario**: Tenants (references SoggettoAnagrafico)
- **Contratto**: Rental contracts (references UnitaImmobiliare and Affittuario)
- **Incasso**: Monthly rental income (linked to Contratto)
- **Spesa**: Property expenses with categories
- **Tecnico**: Maintenance technicians (references SoggettoAnagrafico)
- **RipartizioneSpesa**: Expense distribution among units
- **Documento**: Generic file attachments (polymorphic entity_type/entity_id)

**Entity relationships:**
- Contratto references UnitaImmobiliare (from immobili module)
- Contratto references Affittuario
- Contratto → many Incassi (one per month)
- UnitaImmobiliare → many Spese, RipartizioneSpesa

### Database

- **ORM:** SQLAlchemy with declarative base
- **Migrations:** Alembic configured (alembic.ini present)
- **Session management:** Use `get_db()` dependency for route handlers
- **Models:** All models inherit from `Base` defined in `app.core.database`
- **Table creation:** `Base.metadata.create_all(bind=engine)` in main.py creates tables automatically

### Multi-Tenancy

The platform implements **schema-based multi-tenancy** using PostgreSQL schemas for data isolation between different tenants (e.g., test vs production environments).

#### How It Works

1. **Database Structure**
   - Each tenant has its own PostgreSQL schema (e.g., `tenant_test`, `tenant_produzione`)
   - All tables are duplicated in each tenant schema
   - The `public` schema contains shared data (user accounts, tenant metadata)

2. **Tenant Context Management**
   - JWT tokens include a `tenant_schema` claim after tenant selection
   - `TenantMiddleware` (`app/core/middleware/tenant_middleware.py`) extracts tenant from JWT and stores it in `request.state.tenant_schema`
   - `get_tenant_schema(request: Request)` dependency extracts tenant from request state
   - `get_db()` depends on `get_tenant_schema` and automatically sets PostgreSQL `search_path` to tenant schema
   - Uses Starlette's `request.state` for request-scoped tenant storage (clean, FastAPI-native approach)

3. **Tenant Switching Flow**
   ```
   User Login → GET /tenants/my-tenants → User Selects Tenant →
   POST /tenants/switch → New JWT with tenant_schema →
   All queries execute in tenant schema
   ```

4. **Key Implementation Files**
   - `app/core/database.py` - `get_tenant_schema()` and `get_db()` dependencies with `search_path` setting
   - `app/core/middleware/tenant_middleware.py` - JWT extraction and `request.state.tenant_schema` setting
   - `app/core/routes/tenants.py` - Tenant switching API endpoints
   - `frontend/src/contexts/TenantContext.jsx` - Frontend tenant state management

5. **Implementation Details**
   ```python
   # Middleware extracts tenant from JWT and stores in request.state
   class TenantMiddleware(BaseHTTPMiddleware):
       async def dispatch(self, request: Request, call_next):
           # Extract token and decode
           payload = decode_token(token)
           if payload and payload.get("tenant_schema"):
               request.state.tenant_schema = payload["tenant_schema"]
           return await call_next(request)

   # Dependency chain: get_tenant_schema -> get_db
   def get_tenant_schema(request: Request) -> Optional[str]:
       return getattr(request.state, 'tenant_schema', None)

   def get_db(tenant_schema: Optional[str] = Depends(get_tenant_schema)):
       db = SessionLocal()
       if tenant_schema:
           db.execute(text(f"SET search_path TO {tenant_schema}, public"))
       yield db
   ```

#### Creating New Tenants

To add a new tenant schema:

```sql
-- Create new tenant schema
CREATE SCHEMA tenant_newclient;

-- Grant permissions
GRANT USAGE ON SCHEMA tenant_newclient TO your_app_user;
GRANT ALL ON ALL TABLES IN SCHEMA tenant_newclient TO your_app_user;

-- Run migrations in the new schema
SET search_path TO tenant_newclient, public;
-- Run your alembic migrations here
```

#### Tenant Isolation Rules

- ✅ **Data Isolation**: Each tenant sees only their own data (verified working December 2025)
- ✅ **Schema Automatic**: `search_path` set automatically per request via dependency injection
- ✅ **FastAPI Native**: Uses `request.state` for request-scoped storage (no async/sync conflicts)
- ✅ **Dependency Chain**: Clean separation of concerns with `get_tenant_schema` → `get_db`
- ⚠️ **Shared Tables**: Tables in `public` schema (users, tenants) are shared across all tenants
- ⚠️ **Manual Schema Creation**: New tenant schemas must be created manually in PostgreSQL

**Testing Multi-Tenancy:**
```bash
# 1. Login and get base token
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -d '{"username":"admin","password":"changeme123"}'

# 2. Switch to a specific tenant
curl -X POST "http://localhost:8000/api/v1/tenants/switch" \
  -H "Authorization: Bearer <token>" \
  -d '{"tenant_id": 1}'  # Returns token with tenant_schema

# 3. Access tenant-specific data
curl -X GET "http://localhost:8000/api/v1/anagrafica/soggetti/" \
  -H "Authorization: Bearer <tenant_token>"  # Only sees tenant's data
```

### Configuration

Backend configuration uses Pydantic Settings (`app/core/config.py`):

- Reads from `.env` file
- Required: `DATABASE_URL`, `SECRET_KEY`
- CORS origins: comma-separated string converted to list
- API prefix: `/api/v1`

#### Dynamic CORS Configuration

The backend uses a **custom DynamicCORSMiddleware** (`app/main.py:152-178`) that automatically accepts CORS requests from:

- **Configured origins** in `BACKEND_CORS_ORIGINS` (.env file)
- **Local network IPs** matching pattern `192.168.x.x` on ports 3000 or 5173
- **Localhost** (`localhost`, `127.0.0.1`) on ports 3000 or 5173

This eliminates the need to manually add every device IP to the CORS configuration during development. Simply access the frontend from any device on your local network and it will work automatically.

**Example:**
- ✅ `http://192.168.1.34:3000` - Auto-accepted
- ✅ `http://192.168.1.99:3000` - Auto-accepted
- ✅ `http://localhost:3000` - Auto-accepted
- ❌ `http://example.com:3000` - Rejected (not local network)

## Adding a New Module

The platform supports pluggable modules. To create a new module (e.g., "biblioteca" for library management):

### 1. Create Module Structure

```bash
cd backend/modules
mkdir -p biblioteca/{models,schemas,routes}
touch biblioteca/__init__.py
touch biblioteca/__manifest__.py
touch biblioteca/models/__init__.py
touch biblioteca/schemas/__init__.py
touch biblioteca/routes/__init__.py
```

### 2. Create Manifest (`__manifest__.py`)

```python
manifest = {
    "name": "Gestione Biblioteca",
    "technical_name": "biblioteca",
    "version": "1.0.0",
    "description": "Sistema di gestione biblioteca con libri, prestiti, utenti",
    "author": "Your Name",

    "category": "library",
    "sequence": 30,

    # Dependencies (if any)
    "dependencies": [],  # or ["anagrafica_italiana"] if using SoggettoAnagrafico

    # Models provided
    "models": ["libro", "prestito", "utente_biblioteca"],

    # API route prefix
    "api_prefix": "/biblioteca",
}
```

### 3. Create Models

```python
# biblioteca/models/libro.py
from sqlalchemy import Column, Integer, String, Date, Boolean
from app.core.database import Base

class Libro(Base):
    __tablename__ = "libri"

    id = Column(Integer, primary_key=True)
    titolo = Column(String(200), nullable=False)
    autore = Column(String(100))
    isbn = Column(String(13), unique=True)
    disponibile = Column(Boolean, default=True)
```

### 4. Create Module Init (`__init__.py`)

```python
"""
Biblioteca Module - Library Management
"""
from .__manifest__ import manifest

__all__ = ["manifest"]

def register_module(app):
    """Called by module loader"""
    print("[Biblioteca] Module registered!")
```

### 5. Auto-Discovery

The module loader automatically discovers modules in `backend/modules/`:
- Scans for directories with `__manifest__.py`
- Resolves dependencies
- Loads modules in correct order
- No manual registration needed!

### 6. Cross-Module Dependencies

If your module depends on another module's models:

```python
# Add modules directory to path
import sys
import os
modules_dir = os.path.join(os.path.dirname(__file__), '../../modules')
if modules_dir not in sys.path:
    sys.path.insert(0, modules_dir)

# Import from other module
from anagrafica_italiana.models import SoggettoAnagrafico
from immobili.models import UnitaImmobiliare
```

### 7. Frontend (Optional)

Add components in `frontend/src/components/Biblioteca/` and register routes in `App.jsx`. The platform will automatically discover menu items from the manifest.

## API Conventions

All endpoints follow REST conventions:

- `GET /api/v1/entity/` - List all (supports skip/limit pagination)
- `GET /api/v1/entity/{id}` - Get by ID
- `POST /api/v1/entity/` - Create new
- `PUT /api/v1/entity/{id}` - Update existing
- `DELETE /api/v1/entity/{id}` - Delete

Some entities have additional endpoints:
- `GET /api/v1/contratti/immobile/{immobile_id}` - Filter by relationship
- `GET /api/v1/certificati-energetici/immobile/{immobile_id}/valido` - Business logic queries

## File Uploads

Documents are handled via `app/core/file_storage.py`:

- Upload: `POST /api/v1/documenti/upload` with multipart/form-data
- Download: `GET /api/v1/documenti/{id}/download` returns blob
- Storage: Files saved to `backend/storage/` directory
- Metadata: Documento model tracks entity_type, entity_id for polymorphic associations

## Common Pitfalls

- **Environment variables:** The `start.sh` script removes DATABASE_URL and BACKEND_CORS_ORIGINS from environment to avoid conflicts with .env file
- **CORS:** The DynamicCORSMiddleware automatically accepts requests from localhost and 192.168.x.x networks on ports 3000/5173 - no manual configuration needed
- **Database sessions:** Always use `Depends(get_db)` - don't create sessions manually
- **Model relationships:** SQLAlchemy relationships are defined with `back_populates` for bidirectional access

## Troubleshooting

### CORS Errors: "CORS request did not succeed"

**Symptom:** Browser console shows `Cross-Origin Request Blocked` with status code `(null)`

**Common causes:**
1. **Backend not running** - Check if uvicorn is running on port 8000: `lsof -i :8000`
2. **Multiple backend processes** - Kill all Python processes and restart: `pkill -f "python.*app.main"`
3. **Wrong frontend URL** - The DynamicCORSMiddleware accepts `192.168.x.x` IPs automatically, but if you're using a different subnet, add it to `BACKEND_CORS_ORIGINS` in `.env`
4. **Backend crashed during startup** - Check backend logs for errors

**Solution:**
```bash
cd backend
pkill -f "python.*app.main"  # Kill old processes
source venv/bin/activate
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

The backend should now accept CORS requests from any device on your 192.168.x.x network automatically.

### Frontend API Configuration

**Problem:** When accessing the frontend from a remote client (e.g., from `192.168.1.34`), hardcoded `localhost:8000` URLs cause the browser to look for the backend on the client machine instead of the server.

**Solution:** The frontend uses `VITE_API_BASE_URL` environment variable configured in `frontend/.env`:

```env
VITE_API_BASE_URL=http://192.168.1.2:8000/api/v1
```

**All frontend code should use this variable:**

```javascript
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1'

// Then use it in API calls:
axios.get(`${API_BASE_URL}/platform/menu/`)
```

**Files already configured:**
- ✅ `src/services/api.js` - Central API client
- ✅ `src/contexts/AuthContext.jsx` - Authentication
- ✅ `src/components/Platform/DynamicMenu.jsx` - Dynamic menu
- ✅ `src/pages/Dashboard.jsx` - Dashboard widgets
- ✅ `src/core/modules/useModuleLoader.js` - Module loader
- ✅ `src/modules/hello_module/HelloPage.jsx` - Example module

**To test from remote client:**
1. Ensure `frontend/.env` has correct server IP: `VITE_API_BASE_URL=http://192.168.1.2:8000/api/v1`
2. Restart frontend dev server: `cd frontend && npm run dev`
3. Access from remote client: `http://192.168.1.2:3000`
4. All API calls will now go to `192.168.1.2:8000` instead of client's localhost
