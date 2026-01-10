# Migration Guide - Module Architecture Refactoring

## Overview

The codebase has been refactored from a monolithic structure to a modular, domain-agnostic platform. This guide explains what changed and how to adapt your code.

## What Changed

### Before: Monolithic Architecture
- All domain logic mixed in `app/modules/affitti_lungo/`
- Italian-specific models in `app/core/models/`
- Core contaminated with business logic
- Single large module with 14+ models

### After: Modular Platform
- Core is domain-agnostic (no business logic)
- Business logic in pluggable modules:
  - `anagrafica_italiana` - Italian registry
  - `immobili` - Real estate properties
  - `affitti_lungo` - Rental management (refactored)
- Clean separation of concerns
- Cross-module dependencies properly declared

## Breaking Changes

### 1. Core Models No Longer Export Domain Entities

**Before:**
```python
from app.core.models import SoggettoAnagrafico, CategoriaCatastale, ComuneItalia
```

**After:**
```python
# Setup cross-module imports
import sys
import os
modules_dir = os.path.join(os.path.dirname(__file__), '../../modules')
if modules_dir not in sys.path:
    sys.path.insert(0, modules_dir)

# Import from appropriate module
from anagrafica_italiana.models import SoggettoAnagrafico
from immobili.models import CategoriaCatastale, ComuneItalia
```

### 2. Property Models Moved

All property-related models moved from `app/modules/affitti_lungo/models/` to `modules/immobili/models/`:

- `UnitaImmobiliare` → `immobili.models`
- `Condominio` → `immobili.models`
- `Proprietario` → `immobili.models`
- `DirittoImmobile` → `immobili.models`
- `CertificatoEnergetico` → `immobili.models`
- `TabellaMillesimale` → `immobili.models`
- `MillesimiUnita` → `immobili.models`
- `CategoriaCatastale` → `immobili.models`
- `ComuneItalia` → `immobili.models`

**Affitti_lungo now only contains:**
- `Affittuario` (tenants)
- `Contratto` (contracts)
- `Incasso` (income)
- `Spesa` (expenses)
- `Tecnico` (technicians)
- `RipartizioneSpesa` (expense distribution)
- `Documento` (documents)

### 3. Import Pattern for Cross-Module References

**Before (same module):**
```python
from .unita_immobiliare import UnitaImmobiliare
```

**After (different module):**
```python
import sys
import os
modules_dir = os.path.join(os.path.dirname(__file__), '../../../modules')
if modules_dir not in sys.path:
    sys.path.insert(0, modules_dir)

from immobili.models import UnitaImmobiliare
```

## Module Dependencies

The new architecture has clear dependency chains:

```
anagrafica_italiana (no dependencies)
    ↑
immobili (depends on anagrafica_italiana)
    ↑
affitti_lungo (depends on immobili, anagrafica_italiana)
```

## Migration Steps for Custom Code

If you have custom code that imports the moved models:

### Step 1: Identify Imports
Search your code for:
```bash
grep -r "from app.core.models import" your_code/
grep -r "from app.modules.affitti_lungo.models import.*Unita" your_code/
```

### Step 2: Update Imports
Follow the patterns in "Breaking Changes" section above.

### Step 3: Add sys.path Setup
Add the modules directory to Python path at the top of files that use cross-module imports:

```python
import sys
import os

# Add modules directory for cross-module imports
modules_dir = os.path.join(os.path.dirname(__file__), '../../modules')
if modules_dir not in sys.path:
    sys.path.insert(0, modules_dir)
```

### Step 4: Test
Run your application and verify all imports work correctly.

## New Module Structure

Each module now has a standard structure:

```
modules/module_name/
├── __init__.py          # Export manifest, optional register_module()
├── __manifest__.py      # Module metadata (name, version, dependencies)
├── models/              # SQLAlchemy ORM models
│   ├── __init__.py
│   └── model_name.py
├── schemas/             # Pydantic validation schemas (optional)
│   ├── __init__.py
│   └── schema_name.py
└── routes/              # FastAPI routers (optional)
    ├── __init__.py
    └── route_name.py
```

## Benefits of New Architecture

1. **Domain Agnostic Core**: Can reuse platform for any domain (not just real estate)
2. **Modularity**: Install only the modules you need
3. **Clear Dependencies**: Know exactly what depends on what
4. **Better Organization**: Related models grouped together
5. **Scalability**: Easy to add new modules without touching core
6. **Reusability**: Modules can be shared across projects

## Examples

### Example 1: Accessing SoggettoAnagrafico
```python
# OLD
from app.core.models import SoggettoAnagrafico

# NEW
import sys, os
modules_dir = os.path.join(os.path.dirname(__file__), '../../modules')
if modules_dir not in sys.path:
    sys.path.insert(0, modules_dir)
from anagrafica_italiana.models import SoggettoAnagrafico
```

### Example 2: Accessing UnitaImmobiliare
```python
# OLD (from affitti_lungo)
from .unita_immobiliare import UnitaImmobiliare

# NEW (cross-module import)
import sys, os
modules_dir = os.path.join(os.path.dirname(__file__), '../../../modules')
if modules_dir not in sys.path:
    sys.path.insert(0, modules_dir)
from immobili.models import UnitaImmobiliare
```

### Example 3: Creating a New Module
See CLAUDE.md section "Adding a New Module" for complete guide.

## Troubleshooting

### ImportError: cannot import name 'X' from 'app.core.models'
This means you're trying to import a domain-specific model that has been moved.

**Solution**: Update your import to use the new module location (see "Breaking Changes" section).

### ModuleNotFoundError: No module named 'immobili'
This means the modules directory is not in sys.path.

**Solution**: Add the sys.path setup code at the top of your file (see "Step 3" above).

### Table 'X' is already defined
This happens during development when modules are reloaded.

**Solution**: Restart the backend server to clear the SQLAlchemy metadata cache.

## Support

For questions about the migration, see:
- CLAUDE.md - Complete architecture documentation
- modules/*/README.md - Module-specific documentation (if available)
- Backend logs - Check for import errors and warnings

## Timeline

- **Phase 1-5**: Completed - All refactoring done
- **Current**: Migration period - Update custom code
- **Future**: Remove legacy compatibility layers
