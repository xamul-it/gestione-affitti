# Backend Module Structure

## Overview

The backend uses a **two-tier module system**:
1. **Platform Modules** (`backend/modules/`) - New pluggable modules
2. **Built-in Modules** (`backend/app/modules/`) - Legacy location for core business modules

## Directory Structure

```
backend/
├── app/
│   ├── core/                           # Platform core (domain-agnostic)
│   │   ├── auth/                      # Authentication & authorization
│   │   ├── module_system/             # Dynamic module loader
│   │   ├── platform_services/         # Platform services
│   │   └── models/
│   │       └── ruoli.py              # Platform-only models
│   │
│   ├── modules/                       # BUILT-IN MODULES (legacy)
│   │   └── affitti_lungo/            # Long-term rental management
│   │       ├── __manifest__.py       # Module metadata
│   │       ├── models/               # 7 rental-specific models
│   │       ├── schemas/
│   │       ├── routes/
│   │       └── __init__.py
│   │
│   └── main.py                        # FastAPI app, registers built-in modules
│
└── modules/                            # PLATFORM MODULES (pluggable)
    ├── anagrafica_italiana/           # Italian registry (independent)
    │   ├── __manifest__.py
    │   ├── __init__.py
    │   ├── models/
    │   ├── schemas/
    │   └── routes/
    │
    └── immobili/                      # Real estate properties
        ├── __manifest__.py
        ├── __init__.py
        ├── models/                    # 10+ property models
        ├── schemas/
        └── routes/
```

## Module Locations Explained

### ✅ Platform Modules (`backend/modules/`)
- **Location**: `backend/modules/`
- **Discovery**: Automatic (ModuleLoader scans this directory)
- **Purpose**: New pluggable business modules

**Current modules:**
- `anagrafica_italiana` - Italian person/company registry
- `immobili` - Real estate property management

### ⚠️ Built-in Modules (`backend/app/modules/`)
- **Location**: `backend/app/modules/`
- **Discovery**: Manual (hardcoded in main.py)
- **Purpose**: Legacy core business modules

**Current modules:**
- `affitti_lungo` - Long-term rental management (will migrate to backend/modules/ in future)

## Why Two Locations?

This is a **temporary transition state**:

- `affitti_lungo` was the original module before refactoring
- It's deeply integrated into `main.py` with hardcoded imports
- Moving it immediately would cause breaking changes
- New modules (`anagrafica_italiana`, `immobili`) are in the clean location

**Future**: All modules will be in `backend/modules/` with auto-discovery.

## Creating New Modules

**Always create new modules in `backend/modules/`** - See CLAUDE.md for guide.

## Summary

- Platform core: ✅ Domain-agnostic
- New modules: ✅ In `backend/modules/`
- Legacy module: ⚠️ In `app/modules/` (temporary)
- Migration: 🔄 In progress
