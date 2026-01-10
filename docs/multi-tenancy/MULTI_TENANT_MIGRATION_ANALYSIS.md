# Multi-Tenant Migration Analysis

**Date:** 9 December 2025
**Status:** Planning Phase
**Architecture:** Schema-based Multi-tenancy (PostgreSQL)

## Executive Summary

This document analyzes the current database structure (38 tables) and provides a comprehensive migration plan for implementing schema-based multi-tenancy in the Gestione Affitti platform.

**Key Decisions:**
- ✅ **Approach:** Schema-based multi-tenancy (separate PostgreSQL schemas per tenant)
- ✅ **Tenant Selection:** Post-login (better UX, supports auto-selection and defaults)
- ✅ **OAuth Compatible:** Architecture fully supports future OAuth integration

## Current Database Structure (38 Tables)

### Table Categorization

The 38 tables have been categorized into three groups based on their purpose:

#### 1. Platform Tables (Stay in PUBLIC schema) - 15 tables

These tables are shared across ALL tenants and contain platform-level data:

| Table | Purpose | Why Public? |
|-------|---------|-------------|
| `users` | User authentication | Users can access multiple tenants |
| `roles` | Platform roles | Shared role definitions |
| `permissions` | Platform permissions | Shared permission registry |
| `role_permissions` | Role-permission associations | Platform-level associations |
| `user_roles` | User-role assignments | Platform-level assignments |
| `modules` | Installed modules | Modules are platform-wide |
| `module_dependencies` | Module dependency graph | Platform configuration |
| `module_endpoints` | Module API endpoints | Platform configuration |
| `module_extensions` | Module extension points | Platform configuration |
| `module_hooks` | Module hooks registry | Platform configuration |
| `module_permissions` | Module-defined permissions | Platform configuration |
| `platform_menu_items` | Dynamic menu structure | Platform navigation |
| `platform_widgets` | Available dashboard widgets | Widget catalog |
| `import_configurations` | Data import configs | Platform utility |
| `tipi_documento` | Document type registry | Shared document types |

**New Tables to Add (Public):**
- `tenants` - Tenant registry (schema_name, nome_display, active)
- `user_tenants` - User ↔ Tenant many-to-many (includes is_default flag)

#### 2. Tenant-Specific Business Data (Move to TENANT schemas) - 20 tables

These tables contain business data that should be isolated per tenant:

**Anagrafica Module (5 tables):**
- `soggetti_anagrafici` - People and companies
- `ruoli_azienda` - Person-company work relationships
- `ruoli_azienda_tipi` - Work role types
- `ruoli_disponibili` - Available business roles
- `soggetti_ruoli` - Subject-role assignments

**Immobili Module (10 tables):**
- `unita_immobiliari` - Property units
- `condomini` - Condominium buildings
- `proprietari` - Property owners
- `diritti_immobile` - Property rights/ownership
- `certificati_energetici` - Energy certificates
- `tabelle_millesimali` - Millesimal tables
- `millesimi_unita` - Unit millesimal shares
- `documenti` - File attachments (polymorphic)
- `platform_user_dashboards` - User dashboard configurations

**Affitti_Lungo Module (5 tables):**
- `affittuari` - Tenants
- `contratti` - Rental contracts
- `incassi` - Rental income
- `spese` - Property expenses
- `ripartizioni_spese` - Expense distributions
- `tecnici` - Maintenance technicians

#### 3. Reference/Domain Data (Stay in PUBLIC, optionally copied) - 3 tables

These tables contain reference data that could be shared OR copied per tenant:

| Table | Purpose | Recommendation |
|-------|---------|----------------|
| `categorie_catastali` | Italian cadastral categories (A/1, A/2...) | **PUBLIC** - Static national data |
| `comuni_italia` | Italian municipalities (8000+ rows) | **PUBLIC** - Static national data |
| `tipo_immobile_categoria_map` | Property type mappings | **PUBLIC** - Business rules |

**Rationale:** These contain Italian national reference data that:
- Never changes per tenant
- Would be identical across all tenants
- Saves disk space by sharing
- Can be referenced from tenant schemas via `public.comuni_italia`

## Migration Strategy

### Phase 1: Add Tenant Infrastructure (Platform Core)

**1.1 Create Tenant Models**

Location: `backend/app/core/models/tenant.py`

```python
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base

class Tenant(Base):
    """Tenant (logical database) in the platform."""
    __tablename__ = "tenants"
    __table_args__ = {'schema': 'public'}

    id = Column(Integer, primary_key=True)
    schema_name = Column(String(63), unique=True, nullable=False, index=True)
    nome_display = Column(String(100), nullable=False)
    descrizione = Column(String(255))
    active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user_tenants = relationship("UserTenant", back_populates="tenant")

class UserTenant(Base):
    """Association User ↔ Tenant (many-to-many with metadata)."""
    __tablename__ = "user_tenants"
    __table_args__ = (
        UniqueConstraint('user_id', 'tenant_id', name='uq_user_tenant'),
        {'schema': 'public'}
    )

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    tenant_id = Column(Integer, ForeignKey("public.tenants.id", ondelete="CASCADE"), nullable=False)
    is_default = Column(Boolean, default=False, nullable=False)
    access_granted_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="tenants")
    tenant = relationship("Tenant", back_populates="user_tenants")
```

**1.2 Update User Model**

Location: `backend/app/core/auth/models.py`

Add relationship:
```python
from sqlalchemy.orm import relationship

class User(Base):
    # ... existing fields ...

    # Add new relationship
    tenants = relationship("UserTenant", back_populates="user")
```

**1.3 Create Tenant Service**

Location: `backend/app/core/services/tenant_service.py`

```python
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Optional
from app.core.models.tenant import Tenant, UserTenant

class TenantService:
    """Service for managing multi-tenant operations."""

    @staticmethod
    def set_tenant_context(schema_name: str, db: Session):
        """Set PostgreSQL search_path to tenant schema."""
        # Validate schema name (security)
        if not schema_name.replace('_', '').isalnum():
            raise ValueError(f"Invalid schema name: {schema_name}")

        db.execute(text(f"SET search_path TO {schema_name}, public"))
        db.commit()

    @staticmethod
    def create_tenant_schema(tenant: Tenant, db: Session):
        """Create PostgreSQL schema for new tenant."""
        schema_name = tenant.schema_name

        # Create schema
        db.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema_name}"))
        db.commit()

        # Copy table structure from public (business tables only)
        # This will be done via Alembic migrations with --schema flag

    @staticmethod
    def get_user_tenants(user_id: int, db: Session) -> List[dict]:
        """Get all tenants accessible by a user."""
        user_tenants = db.query(UserTenant, Tenant).join(
            Tenant, UserTenant.tenant_id == Tenant.id
        ).filter(
            UserTenant.user_id == user_id,
            Tenant.active == True
        ).all()

        return [
            {
                "id": tenant.id,
                "schema_name": tenant.schema_name,
                "nome_display": tenant.nome_display,
                "descrizione": tenant.descrizione,
                "is_default": user_tenant.is_default
            }
            for user_tenant, tenant in user_tenants
        ]

    @staticmethod
    def get_default_tenant(user_id: int, db: Session) -> Optional[dict]:
        """Get user's default tenant."""
        user_tenants = TenantService.get_user_tenants(user_id, db)

        # Find default
        default = next((t for t in user_tenants if t["is_default"]), None)

        # If no default but only one tenant, use that
        if not default and len(user_tenants) == 1:
            return user_tenants[0]

        return default
```

**1.4 Create Tenant Middleware**

Location: `backend/app/core/middleware/tenant_middleware.py`

```python
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from app.core.services.tenant_service import TenantService
from app.core.database import SessionLocal

class TenantMiddleware(BaseHTTPMiddleware):
    """Middleware to set tenant context based on JWT token."""

    async def dispatch(self, request: Request, call_next):
        # Extract tenant_id from JWT token
        tenant_schema = request.state.tenant_schema if hasattr(request.state, 'tenant_schema') else None

        if tenant_schema:
            # Set search_path for this request
            db = SessionLocal()
            try:
                TenantService.set_tenant_context(tenant_schema, db)
            finally:
                db.close()

        response = await call_next(request)
        return response
```

**1.5 Update JWT Token**

Location: `backend/app/core/auth/dependencies.py`

Add `tenant_schema` to JWT payload:
```python
def create_access_token(data: dict, tenant_schema: Optional[str] = None):
    to_encode = data.copy()
    if tenant_schema:
        to_encode.update({"tenant_schema": tenant_schema})
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt
```

**1.6 Create Tenant API Endpoints**

Location: `backend/app/core/routes/tenant.py`

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.auth.dependencies import get_current_user
from app.core.services.tenant_service import TenantService

router = APIRouter(prefix="/tenants", tags=["Tenants"])

@router.get("/my-tenants")
def get_my_tenants(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all tenants accessible by current user."""
    return TenantService.get_user_tenants(current_user.id, db)

@router.get("/default")
def get_default_tenant(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's default tenant."""
    tenant = TenantService.get_default_tenant(current_user.id, db)
    if not tenant:
        raise HTTPException(status_code=404, detail="No default tenant found")
    return tenant

@router.post("/switch")
def switch_tenant(
    tenant_id: int,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Switch to a different tenant (returns new JWT token)."""
    # Verify user has access
    tenants = TenantService.get_user_tenants(current_user.id, db)
    tenant = next((t for t in tenants if t["id"] == tenant_id), None)

    if not tenant:
        raise HTTPException(status_code=403, detail="Access denied to this tenant")

    # Create new token with tenant_schema
    from app.core.auth.dependencies import create_access_token
    access_token = create_access_token(
        data={"sub": str(current_user.id)},
        tenant_schema=tenant["schema_name"]
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "tenant": tenant
    }
```

### Phase 2: Migrate Existing Data

**2.1 Create Initial Tenants**

Create two initial tenants:
```sql
-- Tenant for test data (current data)
INSERT INTO public.tenants (schema_name, nome_display, descrizione, active)
VALUES ('tenant_test', 'Dati di Test', 'Database di test con dati demo', true);

-- Tenant for production data (empty initially)
INSERT INTO public.tenants (schema_name, nome_display, descrizione, active)
VALUES ('tenant_produzione', 'Dati di Produzione', 'Database di produzione per dati reali', true);
```

**2.2 Create Tenant Schemas**

```sql
-- Create schemas
CREATE SCHEMA IF NOT EXISTS tenant_test;
CREATE SCHEMA IF NOT EXISTS tenant_produzione;

-- Grant permissions
GRANT ALL ON SCHEMA tenant_test TO affitti;
GRANT ALL ON SCHEMA tenant_produzione TO affitti;
```

**2.3 Copy Table Structure**

For each of the 20 business tables, create structure in tenant schemas:

```sql
-- Example for soggetti_anagrafici
CREATE TABLE tenant_test.soggetti_anagrafici (LIKE public.soggetti_anagrafici INCLUDING ALL);
CREATE TABLE tenant_produzione.soggetti_anagrafici (LIKE public.soggetti_anagrafici INCLUDING ALL);

-- Repeat for all 20 business tables...
```

**2.4 Migrate Existing Data to tenant_test**

```sql
-- Move data from public to tenant_test
INSERT INTO tenant_test.soggetti_anagrafici SELECT * FROM public.soggetti_anagrafici;
INSERT INTO tenant_test.ruoli_azienda SELECT * FROM public.ruoli_azienda;
-- ... repeat for all 20 business tables

-- Verify migration
SELECT COUNT(*) FROM tenant_test.soggetti_anagrafici;
SELECT COUNT(*) FROM public.soggetti_anagrafici; -- Should match

-- After verification, drop public tables
DROP TABLE public.soggetti_anagrafici CASCADE;
-- ... repeat for all 20 business tables
```

**2.5 Update SQLAlchemy Models**

Add `__table_args__` to all business models to support dynamic schema:

```python
# Example: modules/anagrafica_italiana/models/soggetto_anagrafico.py
from sqlalchemy.ext.declarative import declared_attr

class SoggettoAnagrafico(Base):
    __tablename__ = "soggetti_anagrafici"

    @declared_attr
    def __table_args__(cls):
        # Schema will be set dynamically via search_path
        return {}

    # ... rest of model
```

### Phase 3: Update Frontend

**3.1 Create Tenant Context**

Location: `frontend/src/contexts/TenantContext.jsx`

```javascript
import React, { createContext, useContext, useState, useEffect } from 'react'
import axios from 'axios'

const TenantContext = createContext()

export function TenantProvider({ children }) {
  const [tenants, setTenants] = useState([])
  const [currentTenant, setCurrentTenant] = useState(null)
  const [loading, setLoading] = useState(true)

  const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1'

  useEffect(() => {
    loadTenants()
  }, [])

  const loadTenants = async () => {
    try {
      const token = localStorage.getItem('access_token')
      if (!token) return

      const response = await axios.get(`${API_BASE_URL}/tenants/my-tenants`, {
        headers: { Authorization: `Bearer ${token}` }
      })

      setTenants(response.data)

      // Auto-select if only one tenant or has default
      if (response.data.length === 1) {
        await switchTenant(response.data[0].id)
      } else {
        const defaultTenant = response.data.find(t => t.is_default)
        if (defaultTenant) {
          await switchTenant(defaultTenant.id)
        }
      }
    } catch (error) {
      console.error('Error loading tenants:', error)
    } finally {
      setLoading(false)
    }
  }

  const switchTenant = async (tenantId) => {
    try {
      const token = localStorage.getItem('access_token')
      const response = await axios.post(
        `${API_BASE_URL}/tenants/switch`,
        { tenant_id: tenantId },
        { headers: { Authorization: `Bearer ${token}` } }
      )

      // Update token with tenant info
      localStorage.setItem('access_token', response.data.access_token)
      setCurrentTenant(response.data.tenant)

      // Reload page to apply new tenant context
      window.location.reload()
    } catch (error) {
      console.error('Error switching tenant:', error)
      throw error
    }
  }

  return (
    <TenantContext.Provider value={{
      tenants,
      currentTenant,
      loading,
      switchTenant
    }}>
      {children}
    </TenantContext.Provider>
  )
}

export function useTenant() {
  return useContext(TenantContext)
}
```

**3.2 Create Tenant Selector Component**

Location: `frontend/src/components/Platform/TenantSelector.jsx`

```javascript
import React, { useState } from 'react'
import { useTenant } from '../../contexts/TenantContext'
import './TenantSelector.css'

export default function TenantSelector() {
  const { tenants, currentTenant, switchTenant } = useTenant()
  const [showDropdown, setShowDropdown] = useState(false)

  if (tenants.length <= 1) return null // No need to show if only one tenant

  const handleSwitch = async (tenantId) => {
    try {
      await switchTenant(tenantId)
      setShowDropdown(false)
    } catch (error) {
      alert('Errore nel cambio tenant')
    }
  }

  return (
    <div className="tenant-selector">
      <button
        className="tenant-current"
        onClick={() => setShowDropdown(!showDropdown)}
      >
        <span className="tenant-icon">🏢</span>
        <span className="tenant-name">{currentTenant?.nome_display || 'Seleziona Database'}</span>
        <span className="tenant-arrow">▼</span>
      </button>

      {showDropdown && (
        <div className="tenant-dropdown">
          {tenants.map(tenant => (
            <button
              key={tenant.id}
              className={`tenant-option ${tenant.id === currentTenant?.id ? 'active' : ''}`}
              onClick={() => handleSwitch(tenant.id)}
            >
              <div className="tenant-option-name">{tenant.nome_display}</div>
              <div className="tenant-option-desc">{tenant.descrizione}</div>
              {tenant.is_default && <span className="tenant-default-badge">Default</span>}
            </button>
          ))}
        </div>
      )}
    </div>
  )
}
```

**3.3 Update Layout to Include Tenant Selector**

Location: `frontend/src/components/Layout/Header.jsx`

```javascript
import TenantSelector from '../Platform/TenantSelector'

export default function Header() {
  return (
    <header className="app-header">
      <div className="header-left">
        {/* Logo, menu, etc */}
      </div>

      <div className="header-right">
        <TenantSelector />
        {/* User menu, notifications, etc */}
      </div>
    </header>
  )
}
```

**3.4 Wrap App with TenantProvider**

Location: `frontend/src/main.jsx`

```javascript
import { TenantProvider } from './contexts/TenantContext'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <AuthProvider>
      <TenantProvider>
        <App />
      </TenantProvider>
    </AuthProvider>
  </React.StrictMode>
)
```

## Implementation Timeline

### Sprint 1: Platform Infrastructure (3-4 days)
- [ ] Create Tenant and UserTenant models
- [ ] Create TenantService
- [ ] Create tenant API endpoints
- [ ] Update JWT token to include tenant_schema
- [ ] Create TenantMiddleware
- [ ] Add tenants to main.py router
- [ ] Write unit tests

### Sprint 2: Database Migration (2-3 days)
- [ ] Create Alembic migration for tenant tables
- [ ] Create initial tenant_test and tenant_produzione schemas
- [ ] Write migration script to copy table structures
- [ ] Migrate existing data to tenant_test
- [ ] Verify data integrity
- [ ] Drop public business tables (after verification)
- [ ] Update all SQLAlchemy models with dynamic schema support

### Sprint 3: Frontend Integration (2-3 days)
- [ ] Create TenantContext
- [ ] Create TenantSelector component
- [ ] Update Layout/Header
- [ ] Update login flow
- [ ] Add tenant display in UI
- [ ] Test tenant switching
- [ ] Handle tenant switching UX (reload vs SPA update)

### Sprint 4: Testing & Documentation (2 days)
- [ ] Integration testing with multiple tenants
- [ ] Test all CRUD operations in both schemas
- [ ] Test user with multiple tenants
- [ ] Test user with single tenant (auto-select)
- [ ] Test default tenant behavior
- [ ] Update API documentation
- [ ] Update user documentation

**Total Estimated Time:** 9-12 days

## Benefits of This Approach

✅ **Complete data isolation** - Each tenant has its own schema
✅ **Performance** - No tenant_id filtering on every query
✅ **Simple queries** - No changes to existing queries
✅ **Scalability** - Easy to add new tenants
✅ **Backup/Restore** - Can backup individual tenant schemas
✅ **OAuth ready** - Architecture supports any auth provider
✅ **Better UX** - Post-login selection with auto-select and defaults

## Cross-Schema Foreign Keys Analysis

**✅ Analysis Complete:** The migration has been validated for foreign key relationships.

### Foreign Keys from Tenant Tables → Public Tables (4 found)

These are **intentional and correct** cross-schema references:

| Tenant Table | Column | References | Reason |
|--------------|--------|------------|--------|
| `unita_immobiliari` | `categoria_catastale_id` | `public.categorie_catastali.id` | Reference data (Italian cadastral categories) |
| `documenti` | `tipo_documento_id` | `public.tipi_documento.id` | Reference data (document types) |
| `platform_user_dashboards` | `user_id` | `public.users.id` | User authentication data |
| `soggetti_anagrafici` | `user_id` | `public.users.id` | User authentication data |

**Why this is correct:**
- PostgreSQL fully supports foreign keys across schemas
- Reference data (`categorie_catastali`, `tipi_documento`) should be shared across all tenants
- User authentication (`users`) must be in public schema for cross-tenant access
- No modifications needed to foreign key constraints during migration

### Foreign Keys Within Tenant Tables (14 relationships)

All business logic foreign keys stay within the same tenant schema and will work correctly:
- Affittuari → Soggetti Anagrafici
- Contratti → Affittuari, Unità Immobiliari
- Proprietari → Soggetti Anagrafici
- Diritti Immobile → Proprietari, Unità Immobiliari
- Ruoli Azienda → Soggetti Anagrafici (persona fisica + giuridica)
- And 9 more...

**Result:** The schema-based multi-tenancy approach is fully compatible with the existing foreign key structure.

## Security Considerations

1. **Schema name validation** - Always validate schema names to prevent SQL injection
2. **User-tenant verification** - Always verify user has access to tenant before switching
3. **JWT security** - Tenant info in JWT prevents tenant hopping without re-auth
4. **search_path isolation** - Each request sets its own search_path
5. **Cross-schema FK security** - Foreign keys to public tables are intentional and secure

## Next Steps

Once approved, implementation will proceed according to the timeline above. The recommended approach is to:

1. Start with Sprint 1 (platform infrastructure)
2. Test thoroughly in development
3. Proceed to Sprint 2 (migration) only after Sprint 1 is stable
4. Keep frontend (Sprint 3) last to avoid blocking backend work

## Questions to Resolve

- [ ] Should we allow users to create new tenants? (Admin-only vs self-service)
- [ ] Should tenant_produzione be pre-populated with anything?
- [ ] Do we need tenant-level settings/configuration?
- [ ] Should we implement tenant soft-delete or hard-delete?
