# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Gestione Affitti is a modular web application for managing rental properties. FastAPI backend + PostgreSQL, React + Vite frontend.

## Development Commands

### Backend

```bash
cd backend
source venv/bin/activate
python app/main.py          # dev server with auto-reload (localhost:8000)
./start.sh                  # alternative (removes env vars that conflict with .env)
```

#### Running Tests

```bash
cd backend
./run_tests.sh              # all tests
./run_tests.sh unit         # unit tests only
./run_tests.sh integration  # integration tests (requires DB)
./run_tests.sh coverage     # with HTML coverage report
./run_tests.sh module anagrafica  # tests for a specific module
./run_tests.sh ci           # CI mode: coverage + fail-under=80

# Single test file or function:
pytest tests/unit/test_core/test_auth.py -v
pytest tests/unit/test_core/test_auth.py::TestAuth::test_login -v

# By marker:
pytest -m tenant            # multi-tenancy tests
pytest -m parsing           # document parsing tests
pytest -m security
```

Available pytest markers: `unit`, `integration`, `e2e`, `slow`, `tenant`, `parsing`, `security`, `performance`, `contract`.

### Frontend

```bash
cd frontend
npm run dev                 # dev server (localhost:3000)
npm run build               # production build
npm run test:run            # run tests once (Vitest)
npm run test                # watch mode
npm run test:coverage       # with coverage
npm run test:e2e            # Playwright E2E tests
npm run test:all            # unit + e2e
```

### Full Test Suite

```bash
./run_all_tests.sh          # backend coverage + frontend tests
./run_all_tests.sh fast     # skip slow/e2e tests
./run_all_tests.sh ci       # CI mode
```

### Database Migrations (Alembic multi-schema)

```bash
cd backend
alembic upgrade head                        # migrate public schema
alembic -x schema=all upgrade head          # migrate public + all tenant schemas
alembic -x schema=tenant_test upgrade head  # migrate specific tenant

# New migration:
alembic revision --autogenerate -m "description"
# Set target_schema = "public" | "tenant" | "both" in the migration file
```

## Architecture

### Core Principle: Platform + Pluggable Modules

The backend is a **domain-agnostic platform**; all business logic lives in `backend/modules/`. The frontend mirrors this structure with modules in `frontend/src/modules/`.

```
backend/
├── app/
│   ├── core/           # Platform only: auth, module_system, platform_services, database
│   └── main.py         # Auto-discovers and loads modules
└── modules/            # All business logic
    ├── anagrafica_italiana/
    ├── immobili/
    └── affitti_lungo/

frontend/src/
├── modules/            # Self-contained business modules
├── components/         # Shared platform components (Layout, Auth, Search)
├── core/modules/       # Module system infrastructure (registry, loader, dynamic routes)
├── services/api.js     # Re-exports all module APIs (backward compat)
└── App.jsx
```

### Business Modules

| Module | Backend location | Frontend location | Depends on |
|---|---|---|---|
| `anagrafica_italiana` | `backend/modules/anagrafica_italiana/` | `frontend/src/modules/anagrafica_italiana/` | — |
| `immobili` | `backend/modules/immobili/` | `frontend/src/modules/immobili/` | anagrafica_italiana |
| `affitti_lungo` | `backend/modules/affitti_lungo/` | `frontend/src/modules/affitti_lungo/` | immobili, anagrafica_italiana |

**Each backend module requires:** `__manifest__.py` (metadata + dependencies), `__init__.py`, `models/`, `schemas/`, `routes/`

**Each frontend module requires:** `manifest.js` (routes, menu items, widgets, permissions), `index.js` (exports), `services/<name>API.js`

### Multi-Tenancy (PostgreSQL schema-based)

- Each tenant has its own PG schema (`tenant_test`, `tenant_produzione`, etc.)
- `public` schema holds platform data (users, tenants) and shared domain data (categorie_catastali, comuni_italia, tipi_documento)
- Tenant schemas hold business data + override tables (e.g., `tipi_documento_overrides`)
- **No `tenant_id` column needed** — isolation is via `search_path`

**Request flow:** JWT contains `tenant_schema` claim → `TenantMiddleware` stores it in `request.state.tenant_schema` → `get_db()` sets `SET search_path TO {tenant_schema}, public`

Key files: `app/core/database.py`, `app/core/middleware/tenant_middleware.py`, `app/core/routes/tenants.py`

### Key Patterns

**Backend:**
- Database session: always use `Depends(get_db)` — never instantiate manually
- Cross-module imports: modules dir is on `sys.path`, import directly (`from immobili.models import UnitaImmobiliare`)
- Models inherit from `Base` in `app.core.database`; tables created automatically at startup
- Domain data seeded at startup via `seed_all_domain_data(db)` (idempotent, always uses `search_path = public`)

**Frontend:**
- Module auto-discovery via `import.meta.glob('/src/modules/*/manifest.js')`
- All API calls use `import.meta.env.VITE_API_BASE_URL` (configure in `frontend/.env` for remote access)
- Import from modules: `import { UnitaImmobiliariList } from './modules/immobili'`

### Adding a New Module

1. Create `backend/modules/<name>/{__manifest__.py,__init__.py,models/,schemas/,routes/}`
2. Define `manifest` dict in `__manifest__.py` with `name`, `technical_name`, `version`, `dependencies`, `api_prefix`
3. Export `manifest` from `__init__.py` — auto-discovery handles registration, no manual registration needed
4. Create `frontend/src/modules/<name>/{manifest.js,index.js,services/<name>API.js}`

### Configuration

- Backend: Pydantic Settings from `.env` — required: `DATABASE_URL`, `SECRET_KEY`
- CORS: `DynamicCORSMiddleware` auto-accepts `192.168.x.x:3000/5173` and localhost — no manual config needed for LAN dev
- `start.sh` unsets env vars to prevent conflicts with `.env` file

### File Uploads

`app/core/file_storage.py` — files stored in `backend/storage/`, metadata in `Documento` model (polymorphic: `entity_type`/`entity_id`)

- Upload: `POST /api/v1/documenti/upload` (multipart/form-data)
- Download: `GET /api/v1/documenti/{id}/download`

## Key Documentation

- `docs/guides/WIDGET_DEVELOPMENT_GUIDE.md` — creating modular dashboard widgets
- `docs/architecture/CORE_COMPONENTS_ARCHITECTURE.md` — DataTable, FormBuilder, FormModal
- `docs/ux/` — UX/UI guidelines and audit reports
