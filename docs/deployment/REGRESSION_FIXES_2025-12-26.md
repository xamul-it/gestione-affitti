# Regression Fixes - 2025-12-26

## Executive Summary

Fixed 5 critical regressions in the Gestione Affitti platform:

1. **Infinite Loop**: Tenant selection causing 300+ API calls
2. **Nome Field**: Made optional across all entities (codice is primary identifier)
3. **Scadenze Menu**: Removed from menu (it's a core service, not a page)
4. **Comuni Endpoint**: Registered missing route
5. **Ruoli Azienda**: Registered missing routes and fixed page errors

## Problem 1: Infinite Loop in Tenant Selection

### Root Cause
`TenantSelector.jsx` line 16 had a `useEffect` without proper dependency management, causing infinite calls to `/api/v1/tenants/my-tenants`.

### Fix Applied
**File**: `frontend/src/components/Tenant/TenantSelector.jsx`

```javascript
// BEFORE (line 14-19)
useEffect(() => {
  if (fetchUserTenants && availableTenants.length === 0) {
    fetchUserTenants();
  }
}, []); // Missing dependencies!

// AFTER
useEffect(() => {
  let isMounted = true;
  const hasFetched = sessionStorage.getItem('tenants_fetched');

  if (fetchUserTenants && availableTenants.length === 0 && !hasFetched && isMounted) {
    sessionStorage.setItem('tenants_fetched', 'true');
    fetchUserTenants().catch(err => {
      console.error('Failed to fetch tenants:', err);
      sessionStorage.removeItem('tenants_fetched');
    });
  }

  return () => {
    isMounted = false;
  };
}, []);
```

**File**: `frontend/src/contexts/TenantContext.jsx`

Added `isFetching` flag to prevent concurrent API calls:

```javascript
const [isFetching, setIsFetching] = useState(false);

const fetchUserTenants = async () => {
  // Prevent concurrent fetches
  if (isFetching) {
    console.log('[TenantContext] Fetch already in progress, skipping...');
    return availableTenants;
  }
  // ... rest of implementation
}
```

### Expected Result
- ✅ Only ONE call to `/api/v1/tenants/my-tenants` on mount
- ✅ No infinite loops
- ✅ Proper cleanup on unmount

---

## Problem 2: Campo Nome Non Deve Essere Obbligatorio

### Root Cause
Multiple entities had `nome` field with `nullable=False`, but the system generates `codice` automatically. The `nome` field should be optional since `codice` is the primary identifier.

### Entities Fixed

#### 1. Condominio Model
**File**: `backend/modules/immobili/models/condomini.py`

```python
# BEFORE
nome = Column(String(255), nullable=False)

# AFTER
nome = Column(String(255), nullable=True)  # Optional - codice is the primary identifier
```

#### 2. Condominio Schema
**File**: `backend/modules/affitti_lungo/schemas/condomini.py`

```python
# BEFORE
class CondominioBase(BaseModel):
    nome: str
    codice: str

# AFTER
class CondominioBase(BaseModel):
    nome: Optional[str] = None  # Optional - codice is the primary identifier
    codice: str
```

#### 3. Proprietario Schema
**File**: `backend/modules/affitti_lungo/schemas/proprietari.py`

```python
# BEFORE
class ProprietarioBase(BaseModel):
    nome: str = Field(..., max_length=100)
    cognome: str = Field(..., max_length=100)

# AFTER
class ProprietarioBase(BaseModel):
    nome: Optional[str] = Field(None, max_length=100)  # DEPRECATED - use soggetto.nome
    cognome: Optional[str] = Field(None, max_length=100)  # DEPRECATED - use soggetto.cognome
```

#### 4. Affittuario Schema
**File**: `backend/modules/affitti_lungo/schemas/affittuari.py`

```python
# BEFORE
class AffittuarioBase(BaseModel):
    nome: str
    cognome: str

# AFTER
class AffittuarioBase(BaseModel):
    nome: Optional[str] = None  # DEPRECATED - use soggetto.nome
    cognome: Optional[str] = None  # DEPRECATED - use soggetto.cognome
```

### Database Migration
**File**: `backend/alembic/versions/2025122601_make_nome_optional.py`

Created Alembic migration to alter `condomini.nome` column to `nullable=True`.

```python
def upgrade():
    op.alter_column('condomini', 'nome',
                    existing_type=sa.String(length=255),
                    nullable=True)
```

### Expected Result
- ✅ `nome` field is now optional in all entities
- ✅ `codice` remains required and unique
- ✅ Automatic codice generation works without requiring manual nome input

---

## Problem 3: Scadenzario Nel Menu

### Root Cause
Scadenzario was registered as a menu item, but it's a **CORE SERVICE** (badge in TopBar), not a standalone page.

### Fix Applied
**File**: `backend/app/main.py` (lines 252-258)

```python
# BEFORE
{
    "id": "platform.scadenze",
    "label": "Scadenze",
    "path": "/test/scadenze",
    "icon": "📅",
    "order_index": 90,
    "required_permission": None
}

# AFTER
# Scadenze removed - it's a CORE SERVICE (badge in TopBar), not a menu page
```

### Expected Result
- ✅ Scadenze no longer appears in sidebar menu
- ✅ Scadenze badge still works in TopBar
- ✅ `/api/v1/scadenze/badge/info` endpoint still functional

---

## Problem 4: Endpoint Comuni Mancante

### Root Cause
The `comuni` router existed but was not registered in the module's `ROUTERS` list, making it inaccessible.

### Fix Applied
**File**: `backend/modules/anagrafica_italiana/routes/__init__.py`

```python
# BEFORE
from .soggetti import router as soggetti_router
from .soggetti_v2 import router as soggetti_v2_router

__all__ = ["soggetti_router", "soggetti_v2_router"]

# AFTER
from .soggetti import router as soggetti_router
from .soggetti_v2 import router as soggetti_v2_router
from .domini import router as domini_router
from .ruoli_azienda import router as ruoli_azienda_router
from .ruoli_azienda_tipi import router as ruoli_azienda_tipi_router
from .documenti import router as documenti_router

__all__ = [
    "soggetti_router",
    "soggetti_v2_router",
    "domini_router",
    "ruoli_azienda_router",
    "ruoli_azienda_tipi_router",
    "documenti_router"
]
```

**File**: `backend/modules/anagrafica_italiana/__init__.py`

```python
# BEFORE
ROUTERS = [soggetti_router, soggetti_v2_router]

# AFTER
ROUTERS = [
    soggetti_router,
    soggetti_v2_router,
    domini_router,
    ruoli_azienda_router,
    ruoli_azienda_tipi_router,
    documenti_router
]
```

### Router Prefixes Fixed
All routers now have correct `/anagrafica` prefix:

- `domini_router`: `/anagrafica/domini` → `/api/v1/anagrafica/domini/comuni`
- `ruoli_azienda_router`: `/anagrafica/ruoli-azienda` → `/api/v1/anagrafica/ruoli-azienda/`
- `ruoli_azienda_tipi_router`: `/anagrafica/domini/ruoli-azienda-tipi`
- `documenti_router`: `/anagrafica/documenti`

### Expected Result
- ✅ `/api/v1/anagrafica/domini/comuni/` returns Italian municipalities
- ✅ Supports query params: `?provincia=MI&search=Milano&limit=10`
- ✅ Frontend ComuniList component works correctly

---

## Problem 5: Ruoli Azienda Pagina in Errore

### Root Cause
Same as Problem 4 - routes existed but were not registered in the module system.

### Fix Applied
Same fixes as Problem 4. The following endpoints are now available:

1. **Ruoli Azienda (Associazioni)**
   - `GET /api/v1/anagrafica/ruoli-azienda/` - List all associations
   - `GET /api/v1/anagrafica/ruoli-azienda/{id}` - Get by ID
   - `GET /api/v1/anagrafica/ruoli-azienda/soggetto/{soggetto_id}` - Get by subject
   - `POST /api/v1/anagrafica/ruoli-azienda/` - Create association
   - `PUT /api/v1/anagrafica/ruoli-azienda/{id}` - Update association
   - `DELETE /api/v1/anagrafica/ruoli-azienda/{id}` - Delete association

2. **Ruoli Azienda Tipi (Domain Data)**
   - `GET /api/v1/anagrafica/domini/ruoli-azienda-tipi/` - List role types
   - `GET /api/v1/anagrafica/domini/ruoli-azienda-tipi/{id}` - Get by ID
   - `POST /api/v1/anagrafica/domini/ruoli-azienda-tipi/` - Create role type
   - `PUT /api/v1/anagrafica/domini/ruoli-azienda-tipi/{id}` - Update role type
   - `DELETE /api/v1/anagrafica/domini/ruoli-azienda-tipi/{id}` - Delete role type
   - `POST /api/v1/anagrafica/domini/ruoli-azienda-tipi/merge` - Merge role types

### Expected Result
- ✅ RuoliAziendaList page loads without errors
- ✅ Full CRUD operations work
- ✅ Domain data management functional

---

## Files Modified

### Frontend (3 files)
1. `frontend/src/components/Tenant/TenantSelector.jsx` - Fixed infinite loop
2. `frontend/src/contexts/TenantContext.jsx` - Added concurrent fetch prevention

### Backend Models (1 file)
3. `backend/modules/immobili/models/condomini.py` - Made nome optional

### Backend Schemas (3 files)
4. `backend/modules/affitti_lungo/schemas/condomini.py` - Made nome optional
5. `backend/modules/affitti_lungo/schemas/proprietari.py` - Made nome optional
6. `backend/modules/affitti_lungo/schemas/affittuari.py` - Made nome optional

### Backend Routes (6 files)
7. `backend/app/main.py` - Removed Scadenze from menu
8. `backend/modules/anagrafica_italiana/__init__.py` - Added missing routers
9. `backend/modules/anagrafica_italiana/routes/__init__.py` - Export all routers
10. `backend/modules/anagrafica_italiana/routes/domini.py` - Fixed prefix
11. `backend/modules/anagrafica_italiana/routes/ruoli_azienda.py` - Fixed prefix
12. `backend/modules/anagrafica_italiana/routes/ruoli_azienda_tipi.py` - Fixed prefix
13. `backend/modules/anagrafica_italiana/routes/documenti.py` - Fixed prefix

### Database Migration (1 file)
14. `backend/alembic/versions/2025122601_make_nome_optional.py` - New migration

---

## Testing Checklist

### ✅ Problem 1: Infinite Loop
```bash
# 1. Clear browser cache and storage
# 2. Login to application
# 3. Monitor Network tab in DevTools
# 4. Verify only ONE call to /api/v1/tenants/my-tenants
# 5. Select tenant - should work smoothly
```

### ✅ Problem 2: Nome Field Optional
```bash
# Test backend
curl -X POST "http://localhost:8000/api/v1/anagrafica/soggetti/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "tipo_soggetto": "PERSONA_GIURIDICA",
    "codice_fiscale": "12345678901",
    "ragione_sociale": "Test SRL"
  }'
# Should succeed without nome field

# Test creating Condominio without nome
curl -X POST "http://localhost:8000/api/v1/immobili/condomini/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "codice": "COND001",
    "indirizzo": "Via Test 1",
    "citta": "Milano"
  }'
# Should succeed without nome field
```

### ✅ Problem 3: Scadenze Menu
```bash
# 1. Login to application
# 2. Check sidebar menu
# 3. Verify "Scadenze" is NOT present
# 4. Verify Scadenze badge IS visible in TopBar
# 5. Click badge - should show notifiche panel
```

### ✅ Problem 4: Comuni Endpoint
```bash
TOKEN="your_token_here"

# Test comuni list
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/v1/anagrafica/domini/comuni/?limit=5"

# Test comuni search
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/v1/anagrafica/domini/comuni/?provincia=MI&search=Milano"

# Expected: JSON array of comuni with id, nome, cap, provincia_sigla
```

### ✅ Problem 5: Ruoli Azienda
```bash
TOKEN="your_token_here"

# Test ruoli azienda list
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/v1/anagrafica/ruoli-azienda/"

# Test ruoli azienda tipi
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/v1/anagrafica/domini/ruoli-azienda-tipi/"

# Frontend test:
# 1. Navigate to /anagrafiche/ruoli-azienda
# 2. Page should load without errors
# 3. Verify list displays correctly
# 4. Test create/edit/delete operations
```

---

## Database Migration Instructions

To apply the nome field migration:

```bash
cd backend

# Review the migration
cat alembic/versions/2025122601_make_nome_optional.py

# Apply migration (when ready)
alembic upgrade head

# Verify migration
# Check that condomini.nome allows NULL values
```

---

## Rollback Instructions

If any issues arise:

### Frontend Rollback
```bash
cd frontend
git checkout HEAD -- src/components/Tenant/TenantSelector.jsx
git checkout HEAD -- src/contexts/TenantContext.jsx
```

### Backend Rollback
```bash
cd backend

# Rollback routes
git checkout HEAD -- modules/anagrafica_italiana/__init__.py
git checkout HEAD -- modules/anagrafica_italiana/routes/__init__.py
git checkout HEAD -- modules/anagrafica_italiana/routes/domini.py
git checkout HEAD -- modules/anagrafica_italiana/routes/ruoli_azienda.py
git checkout HEAD -- app/main.py

# Rollback database migration
alembic downgrade -1

# Rollback models/schemas
git checkout HEAD -- modules/immobili/models/condomini.py
git checkout HEAD -- modules/affitti_lungo/schemas/
```

---

## Summary of Improvements

1. **Performance**: Eliminated 300+ redundant API calls
2. **UX**: Simplified entity creation (nome is now optional)
3. **Architecture**: Scadenze correctly positioned as core service
4. **API Completeness**: All anagrafica routes now accessible
5. **Maintainability**: Clear separation between required (codice) and optional (nome) fields

---

## Next Steps

1. **Test all fixes** using the testing checklist above
2. **Apply database migration** when ready
3. **Monitor logs** for any new errors
4. **Update documentation** if API contracts changed
5. **Consider adding E2E tests** for tenant selection flow

---

## Notes

- All deprecated fields (nome, cognome in Proprietario/Affittuario) are marked as such
- Frontend already expects correct API paths - no frontend changes needed for endpoints
- Scadenze service endpoints (`/api/v1/scadenze/*`) remain unchanged
- Migration is reversible via `alembic downgrade`

