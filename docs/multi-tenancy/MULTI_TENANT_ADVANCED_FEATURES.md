# Multi-Tenant Advanced Features

**Date:** 9 December 2025
**Status:** Architectural Proposal - Extended Design

## Overview

This document extends the base multi-tenant proposal with advanced features:
1. Module data updates in shared schema
2. Domain data overlay (tenant-specific overrides)
3. Per-tenant module enablement
4. Module table cleanup on disable

---

## 1. Module Updates to Shared Schema

### Question: Can modules update data on the shared schema?

**Answer: YES** - Modules can and should update shared reference data when needed.

### Use Cases

**Scenario 1: Module Installation**
When a module is installed platform-wide, it may need to seed reference data:

```python
# modules/immobili/seeds/seed_categorie_catastali.py
def seed_categorie_catastali(db: Session):
    """Seed Italian cadastral categories into PUBLIC schema"""
    categories = [
        {"codice": "A/1", "descrizione": "Abitazioni di tipo signorile"},
        {"codice": "A/2", "descrizione": "Abitazioni di tipo civile"},
        # ... more categories
    ]

    for cat in categories:
        existing = db.query(CategoriaCatastale).filter_by(codice=cat["codice"]).first()
        if not existing:
            db.add(CategoriaCatastale(**cat))

    db.commit()
```

**Scenario 2: Module Updates Reference Data**
A module may need to update shared domain tables:

```python
# modules/immobili/services/categoria_service.py
def update_categoria_description(codice: str, new_description: str, db: Session):
    """Update shared reference data (affects all tenants)"""
    categoria = db.query(CategoriaCatastale).filter_by(codice=codice).first()
    if categoria:
        categoria.descrizione = new_description
        db.commit()
```

### Security Considerations

✅ **Allowed**: Modules can write to public schema reference tables
⚠️ **Careful**: Changes affect ALL tenants
❌ **Never**: Modules should NOT write to other tenants' schemas

### Recommendation

**YES**, allow modules to update shared schema with these rules:

1. **Reference data only** - Only domain/reference tables in public schema
2. **Module ownership** - Only the module that owns the table can write to it
3. **Versioned migrations** - Reference data updates via Alembic migrations
4. **Audit logging** - Log all changes to shared reference data

---

## 2. Domain Data Overlay (Tenant-Specific Overrides)

### Question: Can tenants have custom domain entries?

**Answer: YES** - This is a powerful feature but adds complexity.

### Architecture: Overlay Pattern

Allow tenants to override or extend shared reference data by checking tenant schema first, then falling back to public schema.

```
Query for categorie_catastali:
1. Check tenant_test.categorie_catastali (tenant-specific overrides)
2. Fallback to public.categorie_catastali (shared defaults)
3. Merge results (tenant overrides win)
```

### Implementation Approaches

#### Approach A: Union Query (Recommended)

```python
# Service layer handles overlay logic
class DomainDataService:
    @staticmethod
    def get_categorie_catastali(db: Session, tenant_schema: str) -> List[CategoriaCatastale]:
        """Get categories with tenant overrides"""

        # Query tenant-specific overrides
        tenant_categories = db.execute(text(f"""
            SELECT * FROM {tenant_schema}.categorie_catastali
        """)).fetchall()

        # Query shared defaults (exclude overridden ones)
        tenant_codes = [cat.codice for cat in tenant_categories]
        public_categories = db.query(CategoriaCatastale).filter(
            ~CategoriaCatastale.codice.in_(tenant_codes)
        ).all()

        # Merge: tenant overrides + public defaults
        return list(tenant_categories) + list(public_categories)
```

#### Approach B: View-Based (Alternative)

Create a database view per tenant that merges data:

```sql
-- Create view for tenant_test
CREATE VIEW tenant_test.v_categorie_catastali AS
SELECT * FROM tenant_test.categorie_catastali
UNION ALL
SELECT * FROM public.categorie_catastali
WHERE codice NOT IN (SELECT codice FROM tenant_test.categorie_catastali);
```

### Database Schema Changes

```sql
-- Add domain tables to tenant schemas (optional, empty by default)
CREATE TABLE tenant_test.categorie_catastali (LIKE public.categorie_catastali INCLUDING ALL);
CREATE TABLE tenant_test.comuni_italia (LIKE public.comuni_italia INCLUDING ALL);
CREATE TABLE tenant_test.tipo_immobile_categoria_map (LIKE public.tipo_immobile_categoria_map INCLUDING ALL);

-- Same for tenant_produzione
CREATE TABLE tenant_produzione.categorie_catastali (LIKE public.categorie_catastali INCLUDING ALL);
-- ... etc
```

### UI for Tenant Overrides

```javascript
// Frontend: Domain Data Management Page
export default function DomainDataManager() {
  const { currentTenant } = useTenant()

  return (
    <div>
      <h2>Categorie Catastali</h2>
      <p>
        Stai visualizzando:
        - {sharedCount} categorie condivise
        - {overrideCount} categorie personalizzate per {currentTenant.nome_display}
      </p>

      <button onClick={() => addTenantOverride()}>
        + Aggiungi Categoria Personalizzata
      </button>

      <table>
        {categories.map(cat => (
          <tr key={cat.codice}>
            <td>{cat.codice}</td>
            <td>{cat.descrizione}</td>
            <td>
              {cat.is_override ? (
                <span className="badge">Personalizzata</span>
              ) : (
                <span className="badge">Condivisa</span>
              )}
            </td>
          </tr>
        ))}
      </table>
    </div>
  )
}
```

### Pros & Cons

**Pros:**
✅ Maximum flexibility - tenants can customize domain data
✅ No data duplication by default (tables empty until override added)
✅ Tenant customization without affecting others

**Cons:**
⚠️ Query complexity - every domain query needs overlay logic
⚠️ Performance overhead - UNION queries are slower
⚠️ Maintenance complexity - two places to update domain data
⚠️ Migration complexity - domain table changes need to propagate

### Recommendation

**START WITHOUT OVERLAY**, add later if needed:

1. **Phase 1** (MVP): Domain data in public only, shared by all tenants
2. **Phase 2** (Optional): Add overlay feature if tenants request customization

**Rationale**: Domain data (categorie_catastali, comuni_italia) is standardized Italian national data that rarely needs customization. Adding overlay complexity upfront may be over-engineering.

**When to add overlay**:
- If tenants request custom categories
- If different tenants need different comune lists
- If business rules differ per tenant

---

## 3. Per-Tenant Module Enablement

### Question: Should each tenant enable different modules?

**Answer: YES** - Essential for flexible multi-tenant SaaS.

### Architecture

#### New Table: tenant_modules

```sql
CREATE TABLE public.tenant_modules (
    id SERIAL PRIMARY KEY,
    tenant_id INTEGER NOT NULL REFERENCES public.tenants(id) ON DELETE CASCADE,
    module_id VARCHAR(50) NOT NULL,  -- e.g., "immobili", "affitti_lungo"
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    installed_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    disabled_at TIMESTAMP,

    CONSTRAINT uq_tenant_module UNIQUE (tenant_id, module_id)
);

CREATE INDEX idx_tenant_modules_tenant ON tenant_modules(tenant_id);
CREATE INDEX idx_tenant_modules_enabled ON tenant_modules(tenant_id, enabled);
```

#### Module Installation Workflow

```python
# Service: TenantModuleService
class TenantModuleService:

    @staticmethod
    def install_module_for_tenant(tenant_id: int, module_id: str, db: Session):
        """Install module tables in tenant schema"""

        # Get tenant
        tenant = db.query(Tenant).get(tenant_id)
        if not tenant:
            raise ValueError(f"Tenant {tenant_id} not found")

        # Get module definition
        module = get_module_manifest(module_id)  # From module system
        if not module:
            raise ValueError(f"Module {module_id} not found")

        # Create module tables in tenant schema
        schema_name = tenant.schema_name
        for table_name in module.get("tables", []):
            db.execute(text(f"""
                CREATE TABLE IF NOT EXISTS {schema_name}.{table_name}
                (LIKE public.{table_name} INCLUDING ALL)
            """))

        db.commit()

        # Register module as enabled
        tenant_module = TenantModule(
            tenant_id=tenant_id,
            module_id=module_id,
            enabled=True
        )
        db.add(tenant_module)
        db.commit()

    @staticmethod
    def disable_module_for_tenant(tenant_id: int, module_id: str, db: Session):
        """Disable module (keep data)"""

        tenant_module = db.query(TenantModule).filter_by(
            tenant_id=tenant_id,
            module_id=module_id
        ).first()

        if tenant_module:
            tenant_module.enabled = False
            tenant_module.disabled_at = datetime.utcnow()
            db.commit()

    @staticmethod
    def uninstall_module_for_tenant(
        tenant_id: int,
        module_id: str,
        drop_tables: bool,
        db: Session
    ):
        """Uninstall module and optionally drop tables"""

        # Get tenant and module
        tenant = db.query(Tenant).get(tenant_id)
        module = get_module_manifest(module_id)

        if drop_tables:
            # Drop module tables from tenant schema
            schema_name = tenant.schema_name
            for table_name in reversed(module.get("tables", [])):  # Reverse for FK dependencies
                try:
                    db.execute(text(f"DROP TABLE IF EXISTS {schema_name}.{table_name} CASCADE"))
                except Exception as e:
                    print(f"Warning: Could not drop {schema_name}.{table_name}: {e}")

            db.commit()

        # Remove registration
        db.query(TenantModule).filter_by(
            tenant_id=tenant_id,
            module_id=module_id
        ).delete()

        db.commit()
```

#### API Endpoints

```python
# routes/tenant_modules.py
from fastapi import APIRouter, Depends

router = APIRouter(prefix="/tenant-modules", tags=["Tenant Modules"])

@router.get("/{tenant_id}/modules")
def get_tenant_modules(tenant_id: int, db: Session = Depends(get_db)):
    """Get all modules and their status for a tenant"""

    # All available modules
    all_modules = get_all_modules()

    # Enabled modules for this tenant
    enabled = db.query(TenantModule).filter_by(
        tenant_id=tenant_id,
        enabled=True
    ).all()

    enabled_ids = {tm.module_id for tm in enabled}

    return [
        {
            "module_id": m.id,
            "name": m.name,
            "enabled": m.id in enabled_ids,
            "installed_at": next((tm.installed_at for tm in enabled if tm.module_id == m.id), None)
        }
        for m in all_modules
    ]

@router.post("/{tenant_id}/modules/{module_id}/install")
def install_module(
    tenant_id: int,
    module_id: str,
    current_user = Depends(require_permission("tenant.manage")),
    db: Session = Depends(get_db)
):
    """Install module for tenant"""
    TenantModuleService.install_module_for_tenant(tenant_id, module_id, db)
    return {"status": "installed"}

@router.post("/{tenant_id}/modules/{module_id}/disable")
def disable_module(
    tenant_id: int,
    module_id: str,
    current_user = Depends(require_permission("tenant.manage")),
    db: Session = Depends(get_db)
):
    """Disable module (keep data)"""
    TenantModuleService.disable_module_for_tenant(tenant_id, module_id, db)
    return {"status": "disabled"}

@router.delete("/{tenant_id}/modules/{module_id}")
def uninstall_module(
    tenant_id: int,
    module_id: str,
    drop_tables: bool = False,
    current_user = Depends(require_permission("tenant.manage")),
    db: Session = Depends(get_db)
):
    """Uninstall module and optionally drop its tables"""
    TenantModuleService.uninstall_module_for_tenant(
        tenant_id, module_id, drop_tables, db
    )
    return {"status": "uninstalled", "tables_dropped": drop_tables}
```

#### Frontend: Module Manager

```javascript
// components/Admin/TenantModuleManager.jsx
export default function TenantModuleManager({ tenant }) {
  const [modules, setModules] = useState([])

  const handleInstall = async (moduleId) => {
    await api.post(`/tenant-modules/${tenant.id}/modules/${moduleId}/install`)
    loadModules()
  }

  const handleUninstall = async (moduleId) => {
    const dropTables = window.confirm(
      'Vuoi eliminare anche i dati del modulo? (ATTENZIONE: operazione irreversibile)'
    )

    await api.delete(`/tenant-modules/${tenant.id}/modules/${moduleId}`, {
      params: { drop_tables: dropTables }
    })
    loadModules()
  }

  return (
    <div className="module-manager">
      <h2>Moduli per {tenant.nome_display}</h2>

      <table>
        <thead>
          <tr>
            <th>Modulo</th>
            <th>Stato</th>
            <th>Installato il</th>
            <th>Azioni</th>
          </tr>
        </thead>
        <tbody>
          {modules.map(mod => (
            <tr key={mod.module_id}>
              <td>{mod.name}</td>
              <td>
                {mod.enabled ? (
                  <span className="badge badge-success">Attivo</span>
                ) : (
                  <span className="badge badge-secondary">Non installato</span>
                )}
              </td>
              <td>{mod.installed_at ? formatDate(mod.installed_at) : '-'}</td>
              <td>
                {mod.enabled ? (
                  <>
                    <button onClick={() => handleDisable(mod.module_id)}>
                      Disabilita
                    </button>
                    <button
                      onClick={() => handleUninstall(mod.module_id)}
                      className="btn-danger"
                    >
                      Disinstalla
                    </button>
                  </>
                ) : (
                  <button onClick={() => handleInstall(mod.module_id)}>
                    Installa
                  </button>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
```

### Module Dependencies

Handle dependencies when installing/uninstalling:

```python
def install_module_for_tenant(tenant_id: int, module_id: str, db: Session):
    """Install module and its dependencies"""

    module = get_module_manifest(module_id)

    # Install dependencies first
    for dep_id in module.get("dependencies", []):
        if not is_module_installed(tenant_id, dep_id, db):
            install_module_for_tenant(tenant_id, dep_id, db)

    # Then install this module
    # ... (installation code)

def uninstall_module_for_tenant(tenant_id: int, module_id: str, db: Session):
    """Check for dependent modules before uninstalling"""

    # Find modules that depend on this one
    dependent_modules = get_dependent_modules(tenant_id, module_id, db)

    if dependent_modules:
        raise ValueError(
            f"Cannot uninstall {module_id}. "
            f"These modules depend on it: {', '.join(dependent_modules)}"
        )

    # Safe to uninstall
    # ... (uninstall code)
```

---

## 4. Module Table Cleanup on Disable

### Workflow Options

#### Option A: Disable (Safe - Keep Data)

```
User clicks "Disable Module"
→ Module marked as disabled in tenant_modules
→ Tables remain in tenant schema with all data
→ Module features hidden from UI
→ Can re-enable later without data loss
```

#### Option B: Uninstall with Data (Destructive)

```
User clicks "Uninstall Module" + confirms data deletion
→ Module tables dropped from tenant schema: DROP TABLE tenant_x.contratti CASCADE
→ Module removed from tenant_modules
→ Cannot be undone
→ Re-installing module creates empty tables
```

#### Option C: Uninstall without Data (Safe)

```
User clicks "Uninstall Module" + keeps data
→ Module marked as uninstalled in tenant_modules
→ Tables remain but module is unregistered
→ Can re-install and reconnect to existing data
```

### UI Confirmation Dialog

```javascript
const handleUninstall = (moduleId) => {
  const result = window.confirm(
    `Vuoi disinstallare il modulo "${moduleName}"?\n\n` +
    `Scegli:\n` +
    `- OK = Mantieni i dati (potrai reinstallare)\n` +
    `- Annulla = Non disinstallare`
  )

  if (!result) return

  const dropTables = window.confirm(
    `ATTENZIONE: Vuoi anche ELIMINARE tutti i dati del modulo?\n\n` +
    `Questa operazione è IRREVERSIBILE!\n\n` +
    `- OK = ELIMINA i dati (non recuperabili)\n` +
    `- Annulla = MANTIENI i dati`
  )

  api.delete(`/tenant-modules/${tenantId}/modules/${moduleId}`, {
    params: { drop_tables: dropTables }
  })
}
```

### Cascade Delete Handling

When dropping module tables, handle foreign keys:

```sql
-- Drop in reverse dependency order
DROP TABLE IF EXISTS tenant_test.incassi CASCADE;        -- References contratti
DROP TABLE IF EXISTS tenant_test.contratti CASCADE;      -- References affittuari, unita_immobiliari
DROP TABLE IF EXISTS tenant_test.affittuari CASCADE;     -- References soggetti_anagrafici
-- etc.
```

Or use CASCADE to auto-drop dependent objects:

```python
def drop_module_tables(tenant_schema: str, module_tables: List[str], db: Session):
    """Drop module tables handling dependencies"""

    for table_name in reversed(module_tables):  # Reverse order for FK dependencies
        try:
            # CASCADE will drop dependent foreign keys
            db.execute(text(f"DROP TABLE IF EXISTS {tenant_schema}.{table_name} CASCADE"))
            print(f"✓ Dropped {tenant_schema}.{table_name}")
        except Exception as e:
            print(f"✗ Failed to drop {tenant_schema}.{table_name}: {e}")
            # Continue with other tables

    db.commit()
```

---

## 5. Updated Migration Strategy

### Initial Tenant Setup

```sql
-- Create tenant
INSERT INTO tenants (schema_name, nome_display) VALUES ('tenant_test', 'Test');

-- Create schema
CREATE SCHEMA tenant_test;

-- Install ONLY enabled modules
-- (Initially: anagrafica_italiana, immobili, affitti_lungo)

-- Record enabled modules
INSERT INTO tenant_modules (tenant_id, module_id, enabled)
VALUES
    (1, 'anagrafica_italiana', true),
    (1, 'immobili', true),
    (1, 'affitti_lungo', true);
```

### Module Installation Script

```python
# scripts/install_module_for_tenant.py
import sys
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.core.services.tenant_module_service import TenantModuleService

def install_module(tenant_id: int, module_id: str):
    db = SessionLocal()
    try:
        TenantModuleService.install_module_for_tenant(tenant_id, module_id, db)
        print(f"✓ Module {module_id} installed for tenant {tenant_id}")
    except Exception as e:
        print(f"✗ Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    tenant_id = int(sys.argv[1])
    module_id = sys.argv[2]
    install_module(tenant_id, module_id)
```

Usage:
```bash
python scripts/install_module_for_tenant.py 1 immobili
python scripts/install_module_for_tenant.py 2 anagrafica_italiana
```

---

## 6. Summary of Architectural Decisions

| Feature | Decision | Rationale |
|---------|----------|-----------|
| **Module updates shared schema** | ✅ YES | Necessary for reference data seeding |
| **Domain data overlay** | ⏸️ OPTIONAL (Phase 2) | Start simple, add if tenants request customization |
| **Per-tenant module enablement** | ✅ YES | Essential for flexible SaaS, reduces costs |
| **Module table cleanup** | ✅ YES (with confirmation) | Give users control, prevent data accumulation |

## 7. Updated Implementation Timeline

### Sprint 1: Platform Infrastructure (3-4 days)
- Create Tenant, UserTenant, **TenantModule** models
- Create TenantService + **TenantModuleService**
- Create tenant API endpoints
- Update JWT token
- Create TenantMiddleware

### Sprint 2: Database Migration (2-3 days)
- Run base migration (tenants, user_tenants, tenant_modules tables)
- Create initial tenant schemas
- Install modules per tenant (selective table creation)
- Migrate existing data

### Sprint 3: Module Management (2-3 days)
- Build TenantModuleService (install/uninstall/disable)
- Create tenant module API endpoints
- Build frontend TenantModuleManager
- Test module installation/cleanup

### Sprint 4: Frontend Integration (2-3 days)
- Create TenantContext + TenantSelector
- Update Layout/Header
- Test tenant + module switching

### Sprint 5: Testing & Documentation (2 days)
- Integration testing
- Update documentation

**Updated Total Timeline:** 11-15 days

---

## 8. Security & Privileges

### Platform Admin vs Tenant Admin

**Two distinct roles with different capabilities:**

#### Platform Admin (Superuser)
- Can create new tenants (requires DB schema creation privileges)
- Can modify shared domain data (public.categorie_catastali, public.comuni_italia)
- Can install/uninstall modules for any tenant
- Can manage all users and tenants
- Has `platform.admin` permission

#### Tenant Admin (Tenant-scoped)
- Can only manage their own tenant's data
- **CANNOT** create new tenants
- **CANNOT** modify shared domain data
- Can manage users within their tenant
- Can request module installation (subject to platform admin approval)
- Has `tenant.admin` permission

### Database Privileges Setup

**PostgreSQL user needs these privileges:**

```sql
-- Grant schema creation privilege to application user
ALTER USER affitti CREATEDB;

-- Or more specifically, just schema creation:
GRANT CREATE ON DATABASE gestione_affitti TO affitti;

-- Verify privileges
SELECT
    datname as database,
    datacl as privileges
FROM pg_database
WHERE datname = 'gestione_affitti';
```

### Domain Data Protection

**Shared domain data is READ-ONLY for tenants:**

```python
# routes/domini.py
from app.core.auth.dependencies import require_permission

router = APIRouter(prefix="/domini", tags=["Domini"])

@router.get("/categorie-catastali")
def get_categorie_catastali(
    current_user = Depends(get_current_user),  # Any authenticated user can read
    db: Session = Depends(get_db)
):
    """Get cadastral categories - READ-ONLY for tenants"""
    return db.query(CategoriaCatastale).all()

@router.post("/categorie-catastali")
def create_categoria_catastale(
    categoria: CategoriaCatastaleCreate,
    current_user = Depends(require_permission("platform.admin")),  # ONLY platform admin
    db: Session = Depends(get_db)
):
    """Create cadastral category - PLATFORM ADMIN ONLY"""
    nuova = CategoriaCatastale(**categoria.dict())
    db.add(nuova)
    db.commit()
    return nuova

@router.put("/categorie-catastali/{id}")
def update_categoria_catastale(
    id: int,
    categoria: CategoriaCatastaleUpdate,
    current_user = Depends(require_permission("platform.admin")),  # ONLY platform admin
    db: Session = Depends(get_db)
):
    """Update cadastral category - PLATFORM ADMIN ONLY"""
    existing = db.query(CategoriaCatastale).get(id)
    if not existing:
        raise HTTPException(404, "Categoria non trovata")

    for field, value in categoria.dict(exclude_unset=True).items():
        setattr(existing, field, value)

    db.commit()
    return existing
```

### Tenant Creation - Platform Admin Only

```python
# routes/tenants.py
@router.post("/", response_model=TenantResponse)
def create_tenant(
    tenant_data: TenantCreate,
    current_user = Depends(require_permission("platform.admin")),  # ONLY platform admin
    db: Session = Depends(get_db)
):
    """Create new tenant - PLATFORM ADMIN ONLY"""

    # Validate schema name
    if not tenant_data.schema_name.replace('_', '').isalnum():
        raise HTTPException(400, "Schema name must be alphanumeric with underscores")

    # Create tenant record
    tenant = Tenant(
        schema_name=tenant_data.schema_name,
        nome_display=tenant_data.nome_display,
        descrizione=tenant_data.descrizione
    )
    db.add(tenant)
    db.commit()
    db.refresh(tenant)

    # Create schema (requires CREATE privilege)
    try:
        db.execute(text(f"CREATE SCHEMA {tenant.schema_name}"))
        db.execute(text(f"GRANT ALL ON SCHEMA {tenant.schema_name} TO affitti"))
        db.commit()
    except Exception as e:
        db.rollback()
        db.delete(tenant)
        db.commit()
        raise HTTPException(500, f"Failed to create schema: {e}")

    return tenant
```

### Permission Matrix

| Action | Platform Admin | Tenant Admin | Tenant User |
|--------|---------------|--------------|-------------|
| Create tenant | ✅ YES | ❌ NO | ❌ NO |
| Delete tenant | ✅ YES | ❌ NO | ❌ NO |
| Modify domain data (public schema) | ✅ YES | ❌ NO | ❌ NO |
| Read domain data | ✅ YES | ✅ YES | ✅ YES |
| Install module for tenant | ✅ YES | 🟡 Request only | ❌ NO |
| Manage tenant data | ✅ YES (all tenants) | ✅ YES (own tenant) | 🟡 Limited |
| Create users in tenant | ✅ YES | ✅ YES | ❌ NO |

### Frontend: Platform Admin UI

```javascript
// pages/PlatformAdmin/TenantManagement.jsx
import { useAuth } from '../../contexts/AuthContext'

export default function TenantManagement() {
  const { user } = useAuth()

  // Only platform admins can access this page
  if (!user.permissions.includes('platform.admin')) {
    return <AccessDenied />
  }

  const handleCreateTenant = async () => {
    const schemaName = prompt('Schema name (e.g., tenant_cliente1):')
    const nomeDisplay = prompt('Display name (e.g., Cliente 1 S.r.l.):')

    try {
      const response = await api.post('/tenants/', {
        schema_name: schemaName,
        nome_display: nomeDisplay
      })

      alert(`Tenant creato! Schema: ${response.data.schema_name}`)
      loadTenants()
    } catch (error) {
      alert(`Errore: ${error.response.data.detail}`)
    }
  }

  return (
    <div className="platform-admin">
      <h1>Gestione Tenants (Platform Admin)</h1>

      <button onClick={handleCreateTenant} className="btn-primary">
        ➕ Crea Nuovo Tenant
      </button>

      <table>
        <thead>
          <tr>
            <th>Schema</th>
            <th>Nome Display</th>
            <th>Stato</th>
            <th>Creato</th>
            <th>Azioni</th>
          </tr>
        </thead>
        <tbody>
          {tenants.map(tenant => (
            <tr key={tenant.id}>
              <td><code>{tenant.schema_name}</code></td>
              <td>{tenant.nome_display}</td>
              <td>
                {tenant.active ? (
                  <span className="badge badge-success">Attivo</span>
                ) : (
                  <span className="badge badge-secondary">Disabilitato</span>
                )}
              </td>
              <td>{formatDate(tenant.created_at)}</td>
              <td>
                <button onClick={() => manageTenantModules(tenant)}>
                  Moduli
                </button>
                <button onClick={() => manageTenantUsers(tenant)}>
                  Utenti
                </button>
                <button
                  onClick={() => deleteTenant(tenant)}
                  className="btn-danger"
                >
                  Elimina
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
```

### Frontend: Domain Data Management (Platform Admin Only)

```javascript
// pages/PlatformAdmin/DomainDataManager.jsx
export default function DomainDataManager() {
  const { user } = useAuth()

  // Only platform admins can modify domain data
  const canEdit = user.permissions.includes('platform.admin')

  return (
    <div className="domain-data-manager">
      <h1>Dati di Dominio (Condivisi)</h1>

      {!canEdit && (
        <div className="alert alert-info">
          ℹ️ Solo Platform Admin può modificare i dati di dominio condivisi.
          Questi dati sono visibili a tutti i tenants.
        </div>
      )}

      <h2>Categorie Catastali</h2>

      {canEdit && (
        <button onClick={handleAddCategoria} className="btn-primary">
          ➕ Aggiungi Categoria
        </button>
      )}

      <table>
        <thead>
          <tr>
            <th>Codice</th>
            <th>Descrizione</th>
            {canEdit && <th>Azioni</th>}
          </tr>
        </thead>
        <tbody>
          {categorie.map(cat => (
            <tr key={cat.id}>
              <td><code>{cat.codice}</code></td>
              <td>{cat.descrizione}</td>
              {canEdit && (
                <td>
                  <button onClick={() => editCategoria(cat)}>✏️</button>
                  <button onClick={() => deleteCategoria(cat)}>🗑️</button>
                </td>
              )}
            </tr>
          ))}
        </tbody>
      </table>

      <div className="info-box">
        <strong>Note:</strong> Queste categorie sono condivise tra tutti i tenants.
        Le modifiche si rifletteranno immediatamente in tutti i database logici.
      </div>
    </div>
  )
}
```

### Updated Permission Seeding

```python
# app/core/auth/seed_permissions.py

def seed_platform_permissions(db: Session):
    """Seed platform-level permissions"""

    platform_perms = [
        # Platform admin permissions
        {"codice": "platform.admin", "nome": "Platform Administrator", "descrizione": "Full platform access"},
        {"codice": "platform.tenants.create", "nome": "Create Tenants", "descrizione": "Create new tenants"},
        {"codice": "platform.tenants.delete", "nome": "Delete Tenants", "descrizione": "Delete tenants"},
        {"codice": "platform.domains.write", "nome": "Modify Domain Data", "descrizione": "Modify shared domain data"},

        # Tenant admin permissions
        {"codice": "tenant.admin", "nome": "Tenant Administrator", "descrizione": "Full tenant access"},
        {"codice": "tenant.users.manage", "nome": "Manage Users", "descrizione": "Manage users in tenant"},
        {"codice": "tenant.modules.request", "nome": "Request Modules", "descrizione": "Request module installation"},

        # Regular permissions
        {"codice": "tenant.data.read", "nome": "Read Tenant Data", "descrizione": "Read access to tenant data"},
        {"codice": "tenant.data.write", "nome": "Write Tenant Data", "descrizione": "Write access to tenant data"},
    ]

    for perm_data in platform_perms:
        existing = db.query(Permission).filter_by(codice=perm_data["codice"]).first()
        if not existing:
            db.add(Permission(**perm_data))

    db.commit()

def create_platform_admin_role(db: Session):
    """Create Platform Admin role with full permissions"""

    role = Role(
        nome="Platform Administrator",
        descrizione="Full platform administration access"
    )
    db.add(role)
    db.flush()

    # Assign all platform.* permissions
    platform_perms = db.query(Permission).filter(
        Permission.codice.like("platform.%")
    ).all()

    for perm in platform_perms:
        db.add(RolePermission(role_id=role.id, permission_id=perm.id))

    db.commit()
    return role
```

## 9. Updated Implementation Checklist

### Sprint 1: Platform Infrastructure
- [ ] Create Tenant, UserTenant, TenantModule models
- [ ] **Grant CREATE SCHEMA privilege to DB user**
- [ ] **Seed platform.admin permissions**
- [ ] Create TenantService with privilege checks
- [ ] Create tenant creation API (platform.admin only)
- [ ] Protect domain data routes (platform.admin for write)

### Sprint 2: Database Migration
- [ ] Verify DB user has CREATE privilege
- [ ] Run migration script
- [ ] Create initial tenant schemas
- [ ] Test schema creation from API

### Sprint 3: Module Management
- [ ] Implement TenantModuleService
- [ ] Create module management API
- [ ] Permission checks (platform.admin vs tenant.admin)

### Sprint 4: Frontend Integration
- [ ] Platform Admin pages (tenant management, domain data)
- [ ] Tenant selector
- [ ] Permission-based UI rendering

### Sprint 5: Testing
- [ ] Test platform admin can create tenants
- [ ] Test tenant admin CANNOT modify domain data
- [ ] Test tenant isolation

---

## 10. Summary

**Key Security Rules:**

1. ✅ **Only Platform Admin can create tenants** (requires DB CREATE privilege)
2. ✅ **Only Platform Admin can modify domain data** (public schema tables)
3. ✅ **Tenant admins manage only their tenant's data**
4. ✅ **Tenants can READ but not WRITE shared domain data**

Ready to proceed with implementation?
