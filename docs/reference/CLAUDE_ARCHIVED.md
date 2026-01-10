# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Gestione Affitti is a modular web application for managing rental properties. The project uses a FastAPI backend with PostgreSQL and a React frontend with Vite.

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

Frontend runs on `http://localhost:5173` (Vite default) or `http://localhost:3000`

## Architecture

### Backend Structure

The backend follows a modular architecture where each feature domain lives in its own module:

```
backend/app/
├── core/                    # Core functionality
│   ├── config.py           # Pydantic settings (DATABASE_URL, CORS, etc)
│   ├── database.py         # SQLAlchemy setup (engine, SessionLocal, Base, get_db)
│   └── file_storage.py     # File upload/download handling
│
├── modules/                # Feature modules
│   └── affitti_lungo/      # Long-term rental management module
│       ├── models/         # SQLAlchemy ORM models (inherit from Base)
│       ├── schemas/        # Pydantic validation schemas (Create, Update, Response)
│       └── routes/         # FastAPI routers (APIRouter with dependency injection)
│
└── main.py                 # FastAPI app initialization, CORS, router registration
```

**Key patterns:**

- **Database session:** Use `Depends(get_db)` to inject database sessions into route handlers
- **Models:** SQLAlchemy models in `models/` define database tables with relationships
- **Schemas:** Pydantic schemas in `schemas/` for request validation and response serialization
- **Routes:** Each entity (immobili, affittuari, contratti, etc.) has its own router file
- **Router registration:** All routers are imported in `modules/affitti_lungo/__init__.py` and registered in `main.py` with `app.include_router(router, prefix=settings.API_V1_STR)`

### Frontend Structure

The frontend is a React SPA using React Router for navigation:

```
frontend/src/
├── components/          # Feature components organized by domain
│   ├── Immobili/       # Properties management
│   ├── Affittuari/     # Tenants management
│   ├── Contratti/      # Contracts management
│   ├── Spese/          # Expenses tracking
│   ├── Incassi/        # Income tracking
│   ├── Tecnici/        # Technicians registry
│   ├── CertificatiEnergetici/  # Energy certificates
│   ├── Proprietari/    # Owners registry
│   ├── DirittiImmobile/  # Property rights/ownership
│   ├── Documenti/      # Document management
│   └── Layout/         # Navigation and layout components
│
├── services/
│   └── api.js          # Centralized API client (axios) with entity-specific exports
│
├── pages/              # Route-level page components
├── App.jsx             # Router configuration
└── main.jsx            # React entry point
```

**Key patterns:**

- **API client:** `services/api.js` exports entity-specific API objects (e.g., `immobiliAPI`, `contrattiAPI`) with CRUD methods
- **Base URL:** API base URL is `http://localhost:8000/api/v1` (configurable via `VITE_API_BASE_URL`)
- **Component organization:** Each entity has a dedicated folder with list, form, and detail components
- **Routing:** All routes defined in `App.jsx` using React Router v6

### Module: Affitti Lungo (Long-term Rentals)

The main module implements a complete rental property management system with these entities:

1. **Immobili** (Properties): Physical properties with cadastral data, location, characteristics
2. **Proprietari** (Owners): Property owners registry
3. **DirittiImmobile** (Property Rights): Ownership relationships linking properties to owners
4. **Affittuari** (Tenants): Tenant registry with personal and contact information
5. **Contratti** (Contracts): Rental contracts linking properties to tenants with terms and conditions
6. **Spese** (Expenses): Expenses tracked per property with categories and payment status
7. **Incassi** (Income): Monthly rental income linked to contracts
8. **Tecnici** (Technicians): Registry of maintenance technicians
9. **CertificatiEnergetici** (Energy Certificates): Energy performance certificates for properties
10. **Documenti** (Documents): File attachments linked to any entity (using entity_type/entity_id pattern)

**Entity relationships:**

- Immobile → many Contratti, Spese, CertificatiEnergetici, DirittiImmobile
- Proprietario → many DirittiImmobile
- Affittuario → many Contratti
- Contratto → many Incassi (one per month)
- Contratto references one Immobile and one Affittuario

### Database

- **ORM:** SQLAlchemy with declarative base
- **Migrations:** Alembic configured (alembic.ini present)
- **Session management:** Use `get_db()` dependency for route handlers
- **Models:** All models inherit from `Base` defined in `app.core.database`
- **Table creation:** `Base.metadata.create_all(bind=engine)` in main.py creates tables automatically

### Configuration

Backend configuration uses Pydantic Settings (`app/core/config.py`):

- Reads from `.env` file
- Required: `DATABASE_URL`, `SECRET_KEY`
- CORS origins: comma-separated string converted to list
- API prefix: `/api/v1`

## Adding a New Module

To add a new module (e.g., "affitti_brevi" for short-term rentals):

1. **Backend:**
   - Create `backend/app/modules/affitti_brevi/`
   - Add `models/`, `schemas/`, `routes/` subdirectories
   - Define SQLAlchemy models inheriting from `Base`
   - Create Pydantic schemas (Create, Update, Response)
   - Implement routers using `APIRouter(prefix="/entity", tags=["Entity"])`
   - Export routers in `__init__.py`
   - Import and register routers in `app/main.py`

2. **Frontend:**
   - Create `frontend/src/components/NewModule/`
   - Add API methods to `services/api.js`
   - Create routes in `App.jsx`
   - Add navigation links in `components/Layout/Navbar.jsx`

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
- **CORS:** Both `http://localhost:3000` and `http://localhost:5173` are whitelisted by default
- **Database sessions:** Always use `Depends(get_db)` - don't create sessions manually
- **Model relationships:** SQLAlchemy relationships are defined with `back_populates` for bidirectional access
