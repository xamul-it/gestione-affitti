# Sistema Scadenzario - Documentazione Tecnica

**Versione:** 1.0.0
**Data Completamento:** 10 Dicembre 2025
**Stato:** ✅ PRODUCTION READY

---

## 📋 Indice

1. [Panoramica](#panoramica)
2. [Architettura](#architettura)
3. [Backend API](#backend-api)
4. [Frontend Components](#frontend-components)
5. [Multi-Tenancy](#multi-tenancy)
6. [Deployment](#deployment)
7. [Testing](#testing)
8. [Maintenance](#maintenance)

---

## 🎯 Panoramica

Il Sistema Scadenzario è un **sistema universale di gestione scadenze e promemoria** integrato nella piattaforma. Permette di creare scadenze standalone (TODO) o collegate a qualsiasi entità del sistema (contratti, immobili, ecc.).

### Caratteristiche Principali

- ✅ **Multi-tenant isolation** - Completo isolamento dati tra tenant
- ✅ **Entity-agnostic** - Collegabile a qualsiasi entità (polimorfismo)
- ✅ **State machine** - Gestione stati con transizioni controllate
- ✅ **Audit trail** - Tracciamento completo modifiche
- ✅ **Multi-recipient** - Scadenze assegnabili a più utenti
- ✅ **Real-time notifications** - Sistema notifiche in-app
- ✅ **Rich UI** - 6 componenti UI integrati

### Casi d'Uso

1. **Scadenze contrattuali** - Rinnovi, disdette, pagamenti
2. **Certificazioni** - Scadenza certificati energetici, sicurezza
3. **Manutenzioni** - Programmazione interventi periodici
4. **TODO generici** - Promemoria non collegati a entità specifiche
5. **Workflow aziendali** - Step di processi con deadline

---

## 🏗️ Architettura

### Stack Tecnologico

**Backend:**
- FastAPI (Python 3.12+)
- SQLAlchemy ORM
- PostgreSQL 14+
- Alembic migrations
- Multi-tenant (schema-based)

**Frontend:**
- React 18
- React Router v6
- Axios HTTP client
- Custom hooks pattern
- CSS modules

### Schema Database

#### Tabella `scadenze`

```sql
CREATE TABLE scadenze (
    id SERIAL PRIMARY KEY,

    -- Riferimento entità (polymorphic)
    modulo VARCHAR(100),
    entity_type VARCHAR(100),
    entity_id INTEGER,
    is_todo BOOLEAN DEFAULT FALSE,

    -- Contenuto
    titolo VARCHAR(200) NOT NULL,
    descrizione TEXT,

    -- Timing
    data_scadenza DATE NOT NULL,
    priorita VARCHAR(20) DEFAULT 'MEDIA',

    -- Stato
    stato VARCHAR(50) DEFAULT 'ATTIVA',
    completed_at TIMESTAMP,

    -- Audit
    created_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    -- Multi-tenant
    -- (inherited from schema-based isolation)
);

CREATE INDEX idx_scadenze_entity ON scadenze(modulo, entity_type, entity_id);
CREATE INDEX idx_scadenze_stato ON scadenze(stato);
CREATE INDEX idx_scadenze_data ON scadenze(data_scadenza);
CREATE INDEX idx_scadenze_created_by ON scadenze(created_by);
```

#### Tabella `scadenze_destinatari`

```sql
CREATE TABLE scadenze_destinatari (
    id SERIAL PRIMARY KEY,
    scadenza_id INTEGER REFERENCES scadenze(id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES users(id),
    notificato BOOLEAN DEFAULT FALSE,
    letto BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_scadenze_dest_user ON scadenze_destinatari(user_id);
CREATE INDEX idx_scadenze_dest_scadenza ON scadenze_destinatari(scadenza_id);
```

#### Tabella `scadenze_log`

```sql
CREATE TABLE scadenze_log (
    id SERIAL PRIMARY KEY,
    scadenza_id INTEGER REFERENCES scadenze(id) ON DELETE CASCADE,
    azione VARCHAR(50) NOT NULL,
    user_id INTEGER REFERENCES users(id),
    data_vecchia DATE,
    data_nuova DATE,
    note TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_scadenze_log_scadenza ON scadenze_log(scadenza_id);
```

### State Machine

```
┌─────────┐
│ ATTIVA  │─────┐
└────┬────┘     │
     │          │
     │ expired  │ posticipa
     ▼          │
┌─────────┐     │
│ SCADUTA │◄────┘
└────┬────┘
     │
     │ completa
     ▼
┌────────────┐
│ COMPLETATA │
└────────────┘

     │ posticipa
     ▼
┌─────────────┐
│ POSTICIPATA │
└─────────────┘

     │ delete
     ▼
┌────────────┐
│ CANCELLATA │
└────────────┘
```

**Stati:**
- `ATTIVA` - Scadenza attiva, non ancora scaduta
- `SCADUTA` - Data scadenza passata, non completata
- `COMPLETATA` - Scadenza completata con successo
- `POSTICIPATA` - Scadenza posticipata a nuova data
- `CANCELLATA` - Scadenza cancellata (soft delete)

**Transizioni:**
- `completa()` - ATTIVA/SCADUTA → COMPLETATA
- `posticipa(nuova_data)` - ATTIVA/SCADUTA → POSTICIPATA (o ATTIVA se data futura)
- `riattiva()` - COMPLETATA/CANCELLATA → ATTIVA
- `delete()` - ANY → CANCELLATA (soft delete)

---

## 🔌 Backend API

### Base URL
```
http://localhost:8000/api/v1/scadenze
```

### Endpoints

#### 1. Create Scadenza (Entity-Linked)

```http
POST /scadenze/
Content-Type: application/json
Authorization: Bearer <token>

{
  "modulo": "affitti_lungo",
  "entity_type": "contratto",
  "entity_id": 123,
  "titolo": "Rinnovo contratto",
  "descrizione": "Contattare inquilino per rinnovo",
  "data_scadenza": "2025-12-31",
  "priorita": "ALTA",
  "destinatari_ids": [1, 2]
}

Response: 201 Created
{
  "id": 456,
  "modulo": "affitti_lungo",
  "entity_type": "contratto",
  "entity_id": 123,
  "titolo": "Rinnovo contratto",
  "stato": "ATTIVA",
  "is_scaduta": false,
  "is_todo": false,
  ...
}
```

#### 2. Create TODO

```http
POST /scadenze/todo
Content-Type: application/json
Authorization: Bearer <token>

{
  "titolo": "Chiamare tecnico",
  "descrizione": "Verificare disponibilità",
  "data_scadenza": "2025-12-15",
  "priorita": "MEDIA"
}

Response: 201 Created
{
  "id": 457,
  "titolo": "Chiamare tecnico",
  "is_todo": true,
  "stato": "ATTIVA",
  ...
}
```

#### 3. Get Scadenza by ID

```http
GET /scadenze/{id}
Authorization: Bearer <token>

Response: 200 OK
{
  "id": 456,
  "titolo": "Rinnovo contratto",
  "stato": "ATTIVA",
  "destinatari": [
    {"user_id": 1, "username": "admin", "notificato": true},
    {"user_id": 2, "username": "user2", "notificato": false}
  ],
  ...
}
```

#### 4. List Scadenze (with filters)

```http
GET /scadenze/?stato=ATTIVA&priorita=ALTA&skip=0&limit=20
Authorization: Bearer <token>

Response: 200 OK
[
  {...},
  {...}
]
```

**Query Parameters:**
- `stato` - Filter by stato (ATTIVA, SCADUTA, etc.)
- `priorita` - Filter by priorità (ALTA, MEDIA, BASSA)
- `modulo` - Filter by modulo
- `entity_type` - Filter by entity type
- `include_completed` - Include completed scadenze (default: false)
- `only_overdue` - Show only overdue (default: false)
- `skip` - Pagination offset
- `limit` - Pagination limit

#### 5. Get Scadenze by Entity

```http
GET /scadenze/entity/{modulo}/{entity_type}/{entity_id}
Authorization: Bearer <token>

Example:
GET /scadenze/entity/affitti_lungo/contratto/123

Response: 200 OK
[
  {...},
  {...}
]
```

#### 6. Get My Scadenze

```http
GET /scadenze/my/scadenze?include_completed=false&only_overdue=false
Authorization: Bearer <token>

Response: 200 OK
[
  {...}
]
```

Returns scadenze where user is creator or recipient.

#### 7. Complete Scadenza

```http
POST /scadenze/{id}/completa
Content-Type: application/json
Authorization: Bearer <token>

{
  "note": "Contratto rinnovato con successo"
}

Response: 200 OK
{
  "id": 456,
  "stato": "COMPLETATA",
  "completed_at": "2025-12-10T10:30:00",
  ...
}
```

#### 8. Postpone Scadenza

```http
POST /scadenze/{id}/posticipa
Content-Type: application/json
Authorization: Bearer <token>

{
  "nuova_data": "2026-01-31",
  "note": "Inquilino richiede posticipo"
}

Response: 200 OK
{
  "id": 456,
  "data_scadenza": "2026-01-31",
  "stato": "POSTICIPATA",
  ...
}
```

#### 9. Reactivate Scadenza

```http
POST /scadenze/{id}/riattiva
Authorization: Bearer <token>

Response: 200 OK
{
  "id": 456,
  "stato": "ATTIVA",
  ...
}
```

#### 10. Update Scadenza

```http
PUT /scadenze/{id}
Content-Type: application/json
Authorization: Bearer <token>

{
  "titolo": "Rinnovo contratto - URGENTE",
  "priorita": "ALTA",
  "descrizione": "Aggiornata descrizione"
}

Response: 200 OK
{
  "id": 456,
  "titolo": "Rinnovo contratto - URGENTE",
  ...
}
```

#### 11. Delete Scadenza

```http
DELETE /scadenze/{id}
Authorization: Bearer <token>

Response: 200 OK
{
  "message": "Scadenza cancellata con successo"
}
```

Note: Soft delete - stato → CANCELLATA

#### 12. Get Badge Info

```http
GET /scadenze/badge/info
Authorization: Bearer <token>

Response: 200 OK
{
  "count_attive": 5,
  "count_scadute": 2,
  "count_alta_priorita": 3,
  "color": "red",
  "tooltip": "2 scadenze scadute, 3 alta priorità"
}
```

#### 13. Get Statistics

```http
GET /scadenze/statistics/summary
Authorization: Bearer <token>

Response: 200 OK
{
  "totale": 10,
  "per_stato": {
    "ATTIVA": 5,
    "SCADUTA": 2,
    "COMPLETATA": 3
  },
  "per_priorita": {
    "ALTA": 3,
    "MEDIA": 4,
    "BASSA": 3
  }
}
```

#### 14. Get Audit Logs

```http
GET /scadenze/{id}/logs
Authorization: Bearer <token>

Response: 200 OK
[
  {
    "id": 1,
    "azione": "CREATA",
    "username": "admin",
    "created_at": "2025-12-01T10:00:00",
    "note": null
  },
  {
    "id": 2,
    "azione": "POSTICIPATA",
    "username": "admin",
    "data_vecchia": "2025-12-15",
    "data_nuova": "2025-12-31",
    "created_at": "2025-12-05T14:30:00",
    "note": "Richiesta posticipo"
  }
]
```

### Error Responses

All endpoints return standard error responses:

```json
{
  "detail": "Error message here"
}
```

**HTTP Status Codes:**
- `200` - Success
- `201` - Created
- `400` - Bad Request (validation error)
- `401` - Unauthorized (invalid token)
- `403` - Forbidden (insufficient permissions)
- `404` - Not Found
- `422` - Unprocessable Entity (validation error)
- `500` - Internal Server Error

---

## ⚛️ Frontend Components

### 1. ScadenzaBadge

**Purpose:** Visual badge showing scadenze count in TopBar.

**Props:**
```typescript
{
  autoLoad?: boolean;        // Auto-load on mount (default: true)
  onClick?: () => void;      // Click handler
  className?: string;        // Additional CSS classes
  showTooltip?: boolean;     // Show tooltip (default: true)
}
```

**Features:**
- Color-coded (red/yellow/green)
- Auto-refresh every 5 minutes
- Overdue counter badge
- Click opens NotifichePanel

**Usage:**
```jsx
import { ScadenzaBadge } from './components/Platform/Scadenze';

<ScadenzaBadge
  autoLoad={true}
  onClick={() => setNotificheOpen(true)}
/>
```

### 2. ScadenzeList

**Purpose:** Advanced list with filters, sorting, batch actions.

**Props:**
```typescript
{
  filters?: object;             // External filters
  onScadenzaClick?: (scadenza) => void;
  onScadenzaUpdated?: () => void;
  showFilters?: boolean;        // Show filter panel (default: true)
  viewMode?: 'grid'|'list'|'compact';
  pageSize?: number;            // Items per page (default: 20)
  enableBatchActions?: boolean; // Enable multi-select (default: true)
}
```

**Features:**
- Filters: stato, priorità, modulo, entity, dates, search
- Sorting: data, priorità, titolo, created_at
- View modes: grid, list, compact
- Batch selection & actions
- Pagination
- Quick actions per item

**Usage:**
```jsx
import { ScadenzeList } from './components/Platform/Scadenze';

<ScadenzeList
  showFilters={true}
  viewMode="grid"
  pageSize={20}
  onScadenzaClick={(scadenza) => openModal(scadenza)}
/>
```

### 3. ScadenzeModal

**Purpose:** Modal for create/edit/view scadenza.

**Props:**
```typescript
{
  isOpen: boolean;
  onClose: () => void;
  mode: 'create'|'edit'|'view';
  scadenza?: object;           // For edit/view mode
  entity?: {                   // Pre-fill for entity-linked
    modulo: string;
    entityType: string;
    entityId: number;
  };
  onSaved?: () => void;        // Callback after save
}
```

**Features:**
- Three modes: create, edit, view
- Form validation
- TODO vs entity-linked toggle
- Audit log display (view mode)
- Quick actions (complete, postpone, delete)

**Usage:**
```jsx
import { ScadenzeModal } from './components/Platform/Scadenze';

<ScadenzeModal
  isOpen={modalOpen}
  onClose={() => setModalOpen(false)}
  mode="create"
  entity={{ modulo: 'affitti_lungo', entityType: 'contratto', entityId: 123 }}
  onSaved={() => refresh()}
/>
```

### 4. ScadenzeSection

**Purpose:** Reusable section for entity detail pages.

**Props:**
```typescript
{
  modulo: string;
  entityType: string;
  entityId: number;
  title?: string;              // Section title (default: 'Scadenze')
  initialCollapsed?: boolean;  // Start collapsed (default: false)
  showCreateButton?: boolean;  // Show create button (default: true)
  showCompletedByDefault?: boolean;
}
```

**Features:**
- Auto-load scadenze for entity
- Collapsible section
- Warning badges (overdue, high priority)
- Create new scadenza linked to entity
- Click item opens modal

**Usage:**
```jsx
import { ScadenzeSection } from './components/Platform/Scadenze';

<ScadenzeSection
  modulo="affitti_lungo"
  entityType="contratto"
  entityId={contractId}
  title="Scadenze Contratto"
/>
```

### 5. ScadenzeWidget

**Purpose:** Dashboard widget showing upcoming scadenze.

**Props:**
```typescript
{
  maxItems?: number;           // Max items to show (default: 5)
  autoRefresh?: boolean;       // Auto-refresh (default: true)
  refreshInterval?: number;    // Refresh interval ms (default: 5min)
  showOnlyMyScadenze?: boolean;// Filter my scadenze (default: true)
  title?: string;              // Widget title
}
```

**Features:**
- Shows top N scadenze by date
- Highlights overdue
- Auto-refresh
- Quick actions inline
- Smart date formatting (Oggi, Domani)
- Click opens modal

**Usage:**
```jsx
import { ScadenzeWidget } from './components/Platform/Scadenze';

<ScadenzeWidget
  maxItems={5}
  autoRefresh={true}
  title="Prossime Scadenze"
/>
```

### 6. NotifichePanel

**Purpose:** Dropdown notification panel from TopBar.

**Props:**
```typescript
{
  isOpen: boolean;
  onClose: () => void;
  autoRefresh?: boolean;       // Auto-refresh (default: true)
  refreshInterval?: number;    // Refresh interval ms (default: 2min)
}
```

**Features:**
- Dropdown from TopBar badge
- Groups: scadute, oggi, domani, settimana, successive
- Quick actions per notification
- Auto-refresh
- Click notification opens modal

**Usage:**
```jsx
import { NotifichePanel } from './components/Platform/Scadenze';

<NotifichePanel
  isOpen={notificheOpen}
  onClose={() => setNotificheOpen(false)}
/>
```

### 7. useScadenze Hook

**Purpose:** State management and API operations.

**Return:**
```typescript
{
  // State
  scadenze: Scadenza[];
  loading: boolean;
  error: string | null;
  badgeInfo: BadgeInfo | null;

  // Load operations
  loadScadenze: (filters?) => Promise<Scadenza[]>;
  loadScadenzeByEntity: (modulo, type, id, includeCompleted) => Promise<Scadenza[]>;
  loadMyScadenze: (includeCompleted, onlyOverdue) => Promise<Scadenza[]>;
  loadBadgeInfo: () => Promise<BadgeInfo>;

  // CRUD operations
  createScadenza: (data) => Promise<Scadenza>;
  createTodo: (data) => Promise<Scadenza>;
  updateScadenza: (id, data) => Promise<Scadenza>;
  deleteScadenza: (id) => Promise<void>;

  // State transitions
  completaScadenza: (id, note?) => Promise<Scadenza>;
  posticipаScadenza: (id, nuovaData, note?) => Promise<Scadenza>;
  riattivaScadenza: (id) => Promise<Scadenza>;

  // Audit
  loadLogs: (id) => Promise<ScadenzaLog[]>;

  // Utilities
  refresh: () => Promise<void>;
}
```

**Usage:**
```jsx
import { useScadenze } from './components/Platform/Scadenze';

function MyComponent() {
  const {
    scadenze,
    loading,
    createScadenza,
    completaScadenza
  } = useScadenze({ autoLoad: true });

  return (
    // ...
  );
}
```

---

## 🏢 Multi-Tenancy

### Schema-Based Isolation

Il sistema scadenzario supporta **completo isolamento multi-tenant** attraverso schema PostgreSQL dedicati.

**Architettura:**
```
Database: gestione_affitti
├── Schema: public
│   ├── users (shared)
│   └── tenants (shared)
├── Schema: tenant_test
│   ├── scadenze
│   ├── scadenze_destinatari
│   └── scadenze_log
└── Schema: tenant_produzione
    ├── scadenze
    ├── scadenze_destinatari
    └── scadenze_log
```

**Funzionamento:**

1. **Login utente** → Token JWT senza tenant
2. **Selezione tenant** → Token JWT con `tenant_schema` claim
3. **API Request** → Middleware estrae tenant da JWT
4. **Database Query** → `SET search_path TO tenant_schema, public`
5. **Risposta** → Dati isolati per tenant

**Garanzie:**
- ✅ Isolamento completo dati tra tenant
- ✅ Foreign keys funzionanti (users in public)
- ✅ Zero possibilità data leakage
- ✅ Performance ottimale (no row-level filtering)

---

## 🚀 Deployment

### Backend Requirements

```bash
# Python dependencies
fastapi>=0.104.0
uvicorn>=0.24.0
sqlalchemy>=2.0.0
alembic>=1.12.0
psycopg2-binary>=2.9.9
python-jose>=3.3.0
passlib>=1.7.4
python-multipart>=0.0.6
```

### Frontend Requirements

```bash
# Node dependencies
react@18.x
react-dom@18.x
react-router-dom@6.x
axios@1.x
vite@5.x
```

### Environment Variables

**Backend (.env):**
```env
# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/gestione_affitti

# Security
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# CORS
BACKEND_CORS_ORIGINS=http://localhost:3000,http://192.168.1.2:3000
```

**Frontend (.env):**
```env
VITE_API_BASE_URL=http://192.168.1.2:8000/api/v1
```

### Database Migration

```bash
cd backend

# Generate migration
alembic revision --autogenerate -m "Add scadenzario tables"

# Run migration
alembic upgrade head

# For each tenant schema
psql -d gestione_affitti -c "SET search_path TO tenant_test, public;"
alembic upgrade head
```

### Production Deployment

**Backend:**
```bash
gunicorn -w 4 -k uvicorn.workers.UvicornWorker app.main:app \
  --bind 0.0.0.0:8000 \
  --timeout 120 \
  --log-level info
```

**Frontend:**
```bash
npm run build
# Serve dist/ with nginx or static server
```

---

## 🧪 Testing

### Manual Testing Checklist

#### Backend API Tests

- [ ] Create TODO: `POST /scadenze/todo`
- [ ] Create entity-linked: `POST /scadenze/`
- [ ] Get by ID: `GET /scadenze/{id}`
- [ ] List with filters: `GET /scadenze/?stato=ATTIVA`
- [ ] Get by entity: `GET /scadenze/entity/affitti_lungo/contratto/1`
- [ ] Get my scadenze: `GET /scadenze/my/scadenze`
- [ ] Complete: `POST /scadenze/{id}/completa`
- [ ] Postpone: `POST /scadenze/{id}/posticipa`
- [ ] Reactivate: `POST /scadenze/{id}/riattiva`
- [ ] Update: `PUT /scadenze/{id}`
- [ ] Delete: `DELETE /scadenze/{id}`
- [ ] Get badge: `GET /scadenze/badge/info`
- [ ] Get statistics: `GET /scadenze/statistics/summary`
- [ ] Get logs: `GET /scadenze/{id}/logs`

#### Frontend Component Tests

**ScadenzaBadge:**
- [ ] Badge shows correct count
- [ ] Badge color changes based on stato
- [ ] Click opens NotifichePanel
- [ ] Auto-refresh works (5 min)

**ScadenzeList:**
- [ ] Filters work correctly
- [ ] Sorting works
- [ ] View modes switch correctly
- [ ] Batch selection works
- [ ] Pagination works
- [ ] Quick actions work

**ScadenzeModal:**
- [ ] Create mode: form validation
- [ ] Create mode: TODO vs entity-linked
- [ ] Edit mode: updates scadenza
- [ ] View mode: shows audit log
- [ ] Quick actions work

**ScadenzeSection:**
- [ ] Loads entity scadenze
- [ ] Collapse/expand works
- [ ] Create button works
- [ ] Warning badges show
- [ ] Click item opens modal

**ScadenzeWidget:**
- [ ] Shows top N scadenze
- [ ] Highlights overdue
- [ ] Auto-refresh works
- [ ] Quick actions work
- [ ] Date formatting correct

**NotifichePanel:**
- [ ] Groups scadenze correctly
- [ ] Quick actions work
- [ ] Auto-refresh works
- [ ] Click opens modal

#### Multi-Tenant Tests

- [ ] Create scadenza in tenant_test
- [ ] Create scadenza in tenant_produzione
- [ ] Switch tenant → see only tenant scadenze
- [ ] Verify zero data leakage

---

## 🔧 Maintenance

### Performance Optimization

**Database Indexes:**
```sql
-- Already created
CREATE INDEX idx_scadenze_entity ON scadenze(modulo, entity_type, entity_id);
CREATE INDEX idx_scadenze_stato ON scadenze(stato);
CREATE INDEX idx_scadenze_data ON scadenze(data_scadenza);
CREATE INDEX idx_scadenze_created_by ON scadenze(created_by);
```

**Query Optimization:**
- Use `.filter()` before `.all()` in SQLAlchemy
- Limit result sets with `skip` and `limit`
- Eager load relationships with `.options(joinedload())`

### Monitoring

**Key Metrics:**
- Average scadenze per tenant
- Overdue scadenze rate
- API response times
- Error rates per endpoint

**Alerts:**
- High overdue count (> 10 per user)
- API errors (> 5% error rate)
- Slow queries (> 1s)

### Backup

```bash
# Backup all tenant schemas
pg_dump -n public -n tenant_test -n tenant_produzione \
  gestione_affitti > backup_scadenzario.sql

# Restore
psql gestione_affitti < backup_scadenzario.sql
```

### Cleanup

```sql
-- Archive old completed scadenze (> 1 year)
UPDATE scadenze
SET stato = 'ARCHIVIATA'
WHERE stato = 'COMPLETATA'
  AND completed_at < NOW() - INTERVAL '1 year';

-- Cleanup logs (> 2 years)
DELETE FROM scadenze_log
WHERE created_at < NOW() - INTERVAL '2 years';
```

---

## 📞 Support

**Documentazione:**
- Questo file: `/SCADENZARIO.md`
- Backend: `/backend/app/core/README.md`
- Frontend: `/frontend/README.md`

**Code Location:**
- Backend: `/backend/app/core/platform/models/scadenza*.py`
- Backend: `/backend/app/core/routes/scadenze.py`
- Backend: `/backend/app/core/platform_services/scadenza_service.py`
- Frontend: `/frontend/src/components/Platform/Scadenze/`

**Test Pages:**
- Test completo: `http://localhost:3000/test/scadenze`
- Contratto: `http://localhost:3000/contratti/{id}`
- Immobile: `http://localhost:3000/unita-immobiliari/{id}`

---

## 📜 License

Proprietario - Tutti i diritti riservati

---

**Versione:** 1.0.0
**Ultima Modifica:** 10 Dicembre 2025
**Autore:** Claude Code (Anthropic)
