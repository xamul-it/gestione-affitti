# CRITICAL FIX REQUIRED - SQLAlchemy Model Initialization

## Status: BLOCKING - Platform Cannot Start

## The Problem

Backend fails at startup with:
```
sqlalchemy.exc.InvalidRequestError: One or more mappers failed to initialize
- Mapper 'Mapper[SoggettoAnagrafico(soggetti_anagrafici)]' has no property 'affittuari'
```

This prevents ANY testing or deployment of the platform.

## Root Cause

Cross-module SQLAlchemy relationships are configured in the wrong order:
1. When routes import Affittuario model
2. Affittuario defines `back_populates="affittuari"` to SoggettoAnagrafico
3. SQLAlchemy tries to configure the relationship immediately
4. But SoggettoAnagrafico doesn't have an `affittuari` relationship property yet
5. Error occurs before the app even fully starts

## Recommended Fix (2-3 hours)

### Step 1: Create Model Initialization Module
Create file: `/home/htpc/test/gestione-affitti/backend/app/models_init.py`

```python
"""
Centralized model initialization to ensure all models are loaded
before any relationships are configured by SQLAlchemy.

This module must be imported FIRST in main.py, before any routes.
"""

# Import in dependency order:

# 1. Base registry models (platform core)
from app.core.module_system.models import (
    Module, ModuleDependency, ModulePermission, ModuleHook,
    ModuleExtension, ModuleEndpoint,
)
from app.core.auth.models import User, Role, Permission, user_roles, role_permissions
from app.core.models import RuoloDisponibile, SoggettoRuolo
from app.core.platform.models import MenuItem, Widget, UserDashboard

# 2. Anagrafica (has no dependencies on other business modules)
from anagrafica_italiana.models import SoggettoAnagrafico, TipoSoggetto

# 3. Immobili (depends on anagrafica_italiana)
from immobili.models import (
    CategoriaCatastale, TipoImmobileCategoriaMap, ComuneItalia,
    UnitaImmobiliare, Condominio, Proprietario, DirittoImmobile,
    CertificatoEnergetico, TabellaMillesimale, MillesimiUnita
)

# 4. Affitti Lungo (depends on immobili and anagrafica_italiana)
from affitti_lungo.models import (
    Affittuario, Tecnico, Contratto, Incasso, Spesa,
    RipartizioneSpesa, Documento
)

# 5. Explicitly configure the registry
# This ensures all relationships are resolved after all models are loaded
from app.core.database import Base
Base.registry.configure()

__all__ = [
    'SoggettoAnagrafico', 'TipoSoggetto',
    'UnitaImmobiliare', 'Condominio', 'Proprietario', 'DirittoImmobile',
    'CertificatoEnergetico', 'TabellaMillesimale', 'MillesimiUnita',
    'Affittuario', 'Tecnico', 'Contratto', 'Incasso', 'Spesa',
    'RipartizioneSpesa', 'Documento'
]
```

### Step 2: Update app/main.py

In `/home/htpc/test/gestione-affitti/backend/app/main.py`, move model imports to the VERY TOP:

**Change this:**
```python
# OLD - imports happen scattered throughout

# Import module system models
from app.core.module_system.models import (...)

# Import auth models
from app.core.auth.models import (...)

# Later: Import models from modules
import anagrafica_italiana.models
import immobili.models
import affitti_lungo.models
```

**To this:**
```python
# NEW - Initialize ALL models before anything else
# This must be the FIRST import to ensure SQLAlchemy relationship configuration
from app import models_init

# Then do platform setup
import logging
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.database import Base, engine, SessionLocal

# NOW import routes (which will import models again, but they're already configured)
from affitti_lungo import (
    immobili_router,
    affittuari_router,
    ...
)
```

### Step 3: Remove Redundant Imports

Remove these lines from app/main.py (they're now handled by models_init):
```python
# DELETE THESE - they're now in models_init.py
import anagrafica_italiana.models
import immobili.models
import affitti_lungo.models
```

### Step 4: Test

```bash
cd backend
source venv/bin/activate
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Application startup complete.
```

Then verify:
```bash
curl http://192.168.1.2:8000/api/v1/platform/health/
```

Should return JSON response (not error).

## Why This Works

1. **All models imported together** - SQLAlchemy has ALL model classes available
2. **Explicit registry.configure()** - Tells SQLAlchemy to resolve all relationships after all classes are loaded
3. **Single point of control** - All model imports go through one module, making dependency order clear
4. **Route imports happen after** - Routes can now safely import models; they're already configured

## Alternative Approaches (if above doesn't work)

### Option A: Use SQLAlchemy Event System
Use `@event.listens_for(Base.registry, 'configure')` to defer relationship configuration.

### Option B: Remove back_populates from cross-module relationships
Make relationships one-way only (removes convenience, but avoids configuration issues).

### Option C: Move models to a shared module
Create a single `models` package at `backend/models/` with all models, then have modules import from there.

## Verification Checklist

After applying the fix:

- [ ] Backend starts without errors
- [ ] API responds to health check endpoint
- [ ] Menu API endpoint works: `GET /api/v1/platform/menu/`
- [ ] No SQLAlchemy warnings in logs
- [ ] Module discovery works
- [ ] Can login with admin/admin123

## Estimated Fix Time

- **Implementation:** 1.5-2 hours
- **Testing:** 0.5-1 hour
- **Total:** 2-3 hours

## Priority

**CRITICAL** - Blocks all development and testing.

## Assigned To

Backend team - this is architectural and requires backend expertise.

---

For questions about this fix, see `UAT_TEST_EXECUTION_SUMMARY.md` for full context.
