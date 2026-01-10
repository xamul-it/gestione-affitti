# Module Documentation

This directory is reserved for module-specific documentation that doesn't fit into other categories.

## Current Status

As of December 2025, module documentation is organized as follows:

### Module-Level Documentation
Each module includes its own README in the source code:
- `backend/modules/{module-name}/README.md` - Module overview and structure
- `backend/modules/{module-name}/__manifest__.py` - Module metadata

### Architecture Documentation
For comprehensive module system architecture, see:
- `docs/architecture/MODULE_STRUCTURE.md` - Module structure and patterns
- `docs/architecture/BACKEND_DOMAIN_REFACTORING_COMPLETED.md` - Backend refactoring details
- `docs/guides/MODULE_DEVELOPMENT_GUIDE.md` - How to create new modules

## Modules in the Platform

### 1. anagrafica_italiana
**Location**: `backend/modules/anagrafica_italiana/`
- Italian registry for persons and companies
- Dependencies: None (independent)
- Entities: SoggettoAnagrafico, TipoSoggetto

### 2. immobili
**Location**: `backend/modules/immobili/`
- Real estate property management
- Dependencies: anagrafica_italiana
- Entities: UnitaImmobiliare, Condominio, Proprietario, and more

### 3. affitti_lungo
**Location**: `backend/modules/affitti_lungo/`
- Long-term rental management
- Dependencies: immobili, anagrafica_italiana
- Entities: Affittuario, Contratto, Incasso, Spesa, etc.

## Module Development

To add new module-specific documentation here:
1. Create a subdirectory with the module name
2. Add a README explaining the module's features
3. Link to architecture docs in the parent directories

## See Also

- `docs/architecture/` - System design and architecture patterns
- `docs/guides/MODULE_DEVELOPMENT_GUIDE.md` - Module creation guide
- `backend/modules/` - Source code and manifests for all modules
