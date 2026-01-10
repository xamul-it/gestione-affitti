# Core Components Architecture - Gestione Affitti

## Executive Summary

This document describes the architecture for reusable core components that will dramatically reduce development time for new modules in the Gestione Affitti platform. Based on analysis of existing code, we identified significant code duplication across modules that can be eliminated through a configuration-driven approach.

## Current State Analysis

### Identified Patterns and Duplication

After analyzing the existing codebase, the following patterns were identified:

#### 1. List Components (DataTable Pattern)
All list components follow the same structure:
- `useState` for data, loading, error, showForm, editingEntity
- `useEffect` to fetch data on mount
- `fetchData()` async function with try/catch/finally
- `handleDelete()` with confirmation dialog
- `handleEdit()` to open form modal
- Table rendering with headers, body, action buttons
- Loading/error/empty states

**Examples of duplicated code:**
- `UnitaImmobiliariList.jsx` (132 lines)
- `ProprietariList.jsx` (152 lines)
- `AffittuariList.jsx` (121 lines)
- `ContrattiList.jsx` (169 lines)
- `PersoneFisicheList.jsx` (214 lines)

**Common boilerplate eliminated:** ~100-150 lines per list component

#### 2. Form Components (FormBuilder Pattern)
All form components share:
- `useState` for formData with initial empty values
- `useEffect` to populate form when editing
- `handleChange()` event handler
- `handleSubmit()` with API call (create/update)
- Modal overlay with header, error/success messages
- Form fields arranged in form-row/form-group structure
- Type conversion for numeric/date fields before submit

**Examples:**
- `UnitaImmobiliareForm.jsx` (399 lines)
- `AffittuarioForm.jsx` (227 lines)
- `ContrattoForm.jsx` (394 lines)
- `ProprietarioForm.jsx` (~180 lines)

**Common boilerplate eliminated:** ~100-200 lines per form component

#### 3. Detail View Components
Detail pages share:
- Header with back button, title, action buttons
- Main info card with icon, title, badges
- Quick stats row
- Tab navigation
- Tab content sections
- Related entity lists
- Loading/error states

**Example:** `AffittuarioDetail.jsx` (717 lines)

#### 4. API Services
All API services follow identical CRUD pattern:
```javascript
export const entityAPI = {
  getAll: () => api.get('/entity/'),
  getById: (id) => api.get(`/entity/${id}`),
  create: (data) => api.post('/entity/', data),
  update: (id, data) => api.put(`/entity/${id}`, data),
  delete: (id) => api.delete(`/entity/${id}`),
};
```

---

## Proposed Architecture

### Directory Structure

```
frontend/src/
├── core/
│   ├── components/
│   │   ├── DataTable/
│   │   │   ├── index.js                 # Main export
│   │   │   ├── DataTable.jsx            # Main component
│   │   │   ├── DataTableHeader.jsx      # Header with title, actions
│   │   │   ├── DataTableToolbar.jsx     # Search, filters, bulk actions
│   │   │   ├── DataTableBody.jsx        # Table body with rows
│   │   │   ├── DataTablePagination.jsx  # Pagination controls
│   │   │   ├── DataTableFilters.jsx     # Advanced filter panel
│   │   │   ├── ColumnSelector.jsx       # Column visibility toggle
│   │   │   ├── BulkActions.jsx          # Multi-select actions
│   │   │   └── DataTable.css            # Styles
│   │   │
│   │   ├── FormBuilder/
│   │   │   ├── index.js
│   │   │   ├── FormBuilder.jsx          # Main form component
│   │   │   ├── FormSection.jsx          # Grouped fields
│   │   │   ├── FormModal.jsx            # Modal wrapper
│   │   │   ├── fields/                  # Field components
│   │   │   │   ├── index.js
│   │   │   │   ├── TextField.jsx
│   │   │   │   ├── NumberField.jsx
│   │   │   │   ├── SelectField.jsx
│   │   │   │   ├── DateField.jsx
│   │   │   │   ├── TextareaField.jsx
│   │   │   │   ├── CheckboxField.jsx
│   │   │   │   ├── AutocompleteField.jsx
│   │   │   │   └── FileField.jsx
│   │   │   ├── validation/
│   │   │   │   ├── index.js
│   │   │   │   ├── validators.js
│   │   │   │   └── useValidation.js
│   │   │   └── FormBuilder.css
│   │   │
│   │   ├── DetailView/
│   │   │   ├── index.js
│   │   │   ├── DetailView.jsx           # Main detail component
│   │   │   ├── DetailHeader.jsx         # Header with back, title, actions
│   │   │   ├── DetailCard.jsx           # Info card component
│   │   │   ├── DetailTabs.jsx           # Tab navigation
│   │   │   ├── DetailSection.jsx        # Content section
│   │   │   ├── RelatedList.jsx          # Related entities table
│   │   │   ├── StatsRow.jsx             # Quick stats display
│   │   │   └── DetailView.css
│   │   │
│   │   ├── common/
│   │   │   ├── LoadingSpinner.jsx
│   │   │   ├── ErrorMessage.jsx
│   │   │   ├── EmptyState.jsx
│   │   │   ├── ConfirmDialog.jsx
│   │   │   ├── Badge.jsx
│   │   │   └── ActionButtons.jsx
│   │   │
│   │   └── index.js                     # Core components export
│   │
│   ├── hooks/
│   │   ├── useDataTable.js              # Table state management
│   │   ├── useEntityCRUD.js             # CRUD operations hook
│   │   ├── useFilters.js                # Filter state management
│   │   ├── useForm.js                   # Form state management
│   │   ├── usePagination.js             # Pagination logic
│   │   ├── useSort.js                   # Sorting logic
│   │   └── index.js
│   │
│   ├── services/
│   │   ├── entityService.js             # Generic CRUD service factory
│   │   ├── metadataService.js           # Fetch entity metadata
│   │   ├── exportService.js             # Export to CSV/Excel/PDF
│   │   └── index.js
│   │
│   └── utils/
│       ├── formatters.js                # Date, currency, number formatters
│       ├── validators.js                # Validation functions
│       ├── columnHelpers.js             # Column type renderers
│       └── index.js
│
└── modules/
    └── [module_name]/
        ├── config/
        │   ├── entities.js              # Entity configurations
        │   └── index.js
        ├── components/
        │   └── [CustomComponents]/       # Only custom UI needed
        └── pages/
            └── [EntityName]Page.jsx      # Uses core components
```

---

## Component Specifications

### 1. DataTable Component

#### Props Interface

```javascript
/**
 * DataTable - Configurable data table component
 *
 * @param {Object} config - Table configuration
 * @param {string} config.entity - Entity name for API calls
 * @param {string} config.title - Page title
 * @param {Array} config.columns - Column definitions
 * @param {Object} config.defaultSort - Default sorting
 * @param {Array} config.filters - Filter definitions
 * @param {Array} config.bulkActions - Bulk action definitions
 * @param {Array} config.rowActions - Row action definitions
 * @param {Function} config.onRowClick - Row click handler
 * @param {Object} options - Additional options
 * @param {boolean} options.selectable - Enable row selection
 * @param {boolean} options.exportable - Enable export
 * @param {boolean} options.paginated - Enable pagination (default: true)
 * @param {number} options.pageSize - Items per page (default: 20)
 */
```

#### Column Definition

```javascript
{
  field: 'nome',              // Field path (supports nested: 'proprietario.nome')
  label: 'Nome',              // Display label
  type: 'text',               // text|number|date|currency|select|badge|link|custom
  sortable: true,             // Enable sorting
  filterable: true,           // Enable filtering
  width: 150,                 // Column width (px or %)
  align: 'left',              // left|center|right
  visible: true,              // Default visibility

  // Type-specific options
  options: [],                // For select type
  format: 'dd/MM/yyyy',       // For date type
  currency: 'EUR',            // For currency type
  linkTo: '/entity/:id',      // For link type
  badgeMap: {},               // For badge type { value: 'variant' }
  render: (value, row) => {}, // For custom type
}
```

#### Filter Definition

```javascript
{
  field: 'stato',
  type: 'select',             // text|select|multiselect|date|daterange|number|numberrange
  label: 'Stato',
  options: [                  // For select/multiselect
    { value: 'ATTIVO', label: 'Attivo' },
    { value: 'INATTIVO', label: 'Inattivo' }
  ],
  defaultValue: null,
  placeholder: 'Tutti gli stati',
}
```

#### Usage Example

```jsx
import { DataTable } from '@/core/components';

const affittuariConfig = {
  entity: 'affittuari',
  title: 'Gestione Affittuari',
  apiEndpoint: '/affittuari/',

  columns: [
    { field: 'nome', label: 'Nome', sortable: true, filterable: true },
    { field: 'cognome', label: 'Cognome', sortable: true, filterable: true },
    { field: 'codice_fiscale', label: 'Codice Fiscale', width: 180 },
    { field: 'email', label: 'Email' },
    { field: 'telefono', label: 'Telefono', render: (v, row) => v || row.cellulare || '-' },
    { field: 'citta_residenza', label: 'Citta' },
  ],

  defaultSort: { field: 'cognome', order: 'asc' },

  filters: [
    { field: 'search', type: 'text', label: 'Cerca', placeholder: 'Nome, CF, email...' },
  ],

  rowActions: [
    { id: 'view', label: 'Dettagli', icon: 'eye', to: '/affittuari/:id' },
    { id: 'edit', label: 'Modifica', icon: 'edit', action: 'edit' },
    { id: 'delete', label: 'Elimina', icon: 'trash', action: 'delete', variant: 'danger' },
  ],

  bulkActions: [
    { id: 'delete', label: 'Elimina selezionati', action: 'bulkDelete', variant: 'danger' },
    { id: 'export', label: 'Esporta CSV', action: 'exportCSV' },
  ],
};

function AffittuariPage() {
  return (
    <DataTable
      config={affittuariConfig}
      FormComponent={AffittuarioForm}
      options={{
        selectable: true,
        exportable: true,
        pageSize: 20,
      }}
    />
  );
}
```

---

### 2. FormBuilder Component

#### Props Interface

```javascript
/**
 * FormBuilder - Dynamic form generator
 *
 * @param {Object} config - Form configuration
 * @param {Array} config.sections - Form sections with fields
 * @param {Object} entity - Entity data for editing (null for create)
 * @param {Function} onSubmit - Submit handler (receives cleaned data)
 * @param {Function} onCancel - Cancel handler
 * @param {Object} options - Additional options
 */
```

#### Field Definition

```javascript
{
  name: 'email',              // Field name (matches API field)
  label: 'Email',             // Display label
  type: 'email',              // text|email|tel|number|date|select|textarea|checkbox|file
  required: true,             // Validation
  placeholder: '',            // Placeholder text
  helpText: '',               // Help text below field
  disabled: false,            // Disabled state
  readOnly: false,            // Read-only state

  // Validation
  validation: {
    required: true,
    minLength: 3,
    maxLength: 100,
    pattern: /regex/,
    custom: (value, formData) => true | 'error message',
  },

  // Type-specific options
  options: [],                // For select
  rows: 3,                    // For textarea
  step: 0.01,                 // For number
  min: 0,                     // For number/date
  max: 100,                   // For number/date
  accept: '.pdf,.doc',        // For file

  // Conditional display
  showIf: (formData) => formData.tipo === 'PERSONA_FISICA',

  // Dependencies (re-fetch options when these fields change)
  dependsOn: ['provincia'],
  optionsLoader: async (formData) => fetchComuni(formData.provincia),
}
```

#### Usage Example

```jsx
import { FormBuilder, FormModal } from '@/core/components';

const affittuarioFormConfig = {
  sections: [
    {
      title: 'Dati Personali',
      columns: 2, // Grid columns
      fields: [
        { name: 'nome', label: 'Nome', type: 'text', required: true },
        { name: 'cognome', label: 'Cognome', type: 'text', required: true },
        { name: 'codice_fiscale', label: 'Codice Fiscale', type: 'text', required: true,
          validation: { maxLength: 16, pattern: /^[A-Z]{6}\d{2}[A-Z]\d{2}[A-Z]\d{3}[A-Z]$/i }
        },
        { name: 'data_nascita', label: 'Data di Nascita', type: 'date' },
        { name: 'luogo_nascita', label: 'Luogo di Nascita', type: 'text' },
      ]
    },
    {
      title: 'Contatti',
      columns: 2,
      fields: [
        { name: 'email', label: 'Email', type: 'email' },
        { name: 'telefono', label: 'Telefono', type: 'tel' },
        { name: 'cellulare', label: 'Cellulare', type: 'tel' },
      ]
    },
    {
      title: 'Residenza',
      columns: 3,
      fields: [
        { name: 'indirizzo_residenza', label: 'Indirizzo', type: 'text', colSpan: 3 },
        { name: 'citta_residenza', label: 'Citta', type: 'text' },
        { name: 'cap_residenza', label: 'CAP', type: 'text' },
        { name: 'provincia_residenza', label: 'Provincia', type: 'text', validation: { maxLength: 2 } },
      ]
    },
    {
      title: 'Note',
      fields: [
        { name: 'note', label: 'Note', type: 'textarea', rows: 3 },
      ]
    }
  ]
};

function AffittuarioFormModal({ entity, onClose, onSave }) {
  return (
    <FormModal
      title={entity ? 'Modifica Affittuario' : 'Nuovo Affittuario'}
      onClose={onClose}
    >
      <FormBuilder
        config={affittuarioFormConfig}
        entity={entity}
        apiEndpoint="/affittuari/"
        onSubmit={onSave}
        onCancel={onClose}
      />
    </FormModal>
  );
}
```

---

### 3. DetailView Component

#### Props Interface

```javascript
/**
 * DetailView - Configurable detail page component
 *
 * @param {Object} config - Detail view configuration
 * @param {string} config.entity - Entity name
 * @param {string} config.title - Dynamic title (supports :field placeholders)
 * @param {string} config.icon - Entity icon
 * @param {Array} config.headerBadges - Badge configurations
 * @param {Array} config.quickStats - Stats to display
 * @param {Array} config.tabs - Tab configurations
 * @param {Array} config.actions - Header action buttons
 */
```

#### Tab Definition

```javascript
{
  id: 'overview',
  label: 'Panoramica',
  icon: 'home',
  component: 'DetailSection',     // DetailSection|RelatedList|custom component
  config: {
    // For DetailSection
    sections: [
      {
        title: 'Informazioni Generali',
        layout: 'grid',           // grid|list
        columns: 2,
        fields: [
          { field: 'nome', label: 'Nome' },
          { field: 'cognome', label: 'Cognome' },
          { field: 'email', label: 'Email', type: 'email' },
          { field: 'data_nascita', label: 'Data Nascita', type: 'date' },
        ]
      }
    ],

    // For RelatedList
    entity: 'contratti',
    apiEndpoint: '/contratti/',
    filter: { affittuario_id: ':id' },
    columns: [...],
    emptyMessage: 'Nessun contratto trovato',
  }
}
```

#### Usage Example

```jsx
import { DetailView } from '@/core/components';

const affittuarioDetailConfig = {
  entity: 'affittuari',
  apiEndpoint: '/affittuari/',
  title: ':nome :cognome',
  icon: 'user',
  backLink: '/affittuari',

  headerBadges: [
    {
      field: 'attivo',
      trueLabel: 'Attivo',
      falseLabel: 'Inattivo',
      trueVariant: 'success',
      falseVariant: 'secondary'
    },
    { field: 'codice_fiscale', prefix: 'CF: ', variant: 'info' },
  ],

  quickStats: [
    { id: 'contratti', label: 'Contratti', value: ':contratti_count', icon: 'file-contract' },
    { id: 'attivi', label: 'Contratti Attivi', value: ':contratti_attivi_count', icon: 'check' },
    { id: 'totale', label: 'Totale Pagato', value: ':totale_pagato', format: 'currency', icon: 'euro' },
  ],

  actions: [
    { id: 'edit', label: 'Modifica', icon: 'edit', action: 'edit', variant: 'secondary' },
    { id: 'delete', label: 'Elimina', icon: 'trash', action: 'delete', variant: 'danger', confirm: true },
  ],

  tabs: [
    {
      id: 'overview',
      label: 'Panoramica',
      component: 'DetailSection',
      config: {
        sections: [
          {
            title: 'Dati Personali',
            fields: [
              { field: 'nome', label: 'Nome' },
              { field: 'cognome', label: 'Cognome' },
              { field: 'codice_fiscale', label: 'Codice Fiscale' },
              { field: 'data_nascita', label: 'Data di Nascita', type: 'date' },
            ]
          }
        ]
      }
    },
    {
      id: 'contratti',
      label: 'Contratti',
      badge: ':contratti_count',
      component: 'RelatedList',
      config: {
        entity: 'contratti',
        apiEndpoint: '/contratti/',
        filter: { affittuario_id: ':id' },
        columns: [
          { field: 'numero_contratto', label: 'Numero', linkTo: '/contratti/:id' },
          { field: 'data_inizio', label: 'Data Inizio', type: 'date' },
          { field: 'canone_mensile', label: 'Canone', type: 'currency' },
          { field: 'stato', label: 'Stato', type: 'badge' },
        ]
      }
    },
    {
      id: 'documenti',
      label: 'Documenti',
      badge: ':documenti_count',
      component: 'DocumentList',
      config: {
        entityType: 'AFFITTUARIO',
      }
    }
  ]
};

function AffittuarioDetailPage() {
  return <DetailView config={affittuarioDetailConfig} />;
}
```

---

## Core Hooks

### useEntityCRUD

```javascript
/**
 * Generic CRUD operations hook
 *
 * @param {string} apiEndpoint - API endpoint
 * @returns {Object} CRUD operations and state
 */
const {
  data,           // Array of entities
  loading,        // Loading state
  error,          // Error message
  pagination,     // { page, pageSize, total }

  fetchAll,       // (params) => Promise
  fetchById,      // (id) => Promise
  create,         // (data) => Promise
  update,         // (id, data) => Promise
  remove,         // (id) => Promise
  refresh,        // () => void
} = useEntityCRUD('/affittuari/');
```

### useDataTable

```javascript
/**
 * DataTable state management hook
 *
 * @param {Object} config - Table configuration
 * @param {Object} options - Options
 * @returns {Object} Table state and handlers
 */
const {
  // Data
  data,
  loading,
  error,

  // Pagination
  page,
  pageSize,
  totalItems,
  totalPages,
  setPage,
  setPageSize,

  // Sorting
  sortField,
  sortOrder,
  handleSort,

  // Filtering
  filters,
  setFilter,
  clearFilters,

  // Selection
  selectedIds,
  selectAll,
  toggleSelect,
  clearSelection,

  // Actions
  refresh,
  exportData,
} = useDataTable(config, options);
```

### useForm

```javascript
/**
 * Form state management hook
 *
 * @param {Object} initialValues - Initial form values
 * @param {Object} validationRules - Validation rules
 * @returns {Object} Form state and handlers
 */
const {
  values,         // Form values
  errors,         // Field errors
  touched,        // Touched fields
  isDirty,        // Has changes
  isValid,        // All validations pass
  isSubmitting,   // Submit in progress

  handleChange,   // (e) => void | (name, value) => void
  handleBlur,     // (e) => void
  handleSubmit,   // (onSubmit) => (e) => void
  setFieldValue,  // (name, value) => void
  setFieldError,  // (name, error) => void
  reset,          // () => void
  validate,       // () => boolean
} = useForm(initialValues, validationRules);
```

---

## Backend Support Services

### 1. Generic CRUD Endpoint (Optional Enhancement)

```python
# backend/app/core/routes/generic_crud.py

from fastapi import APIRouter, Depends, Query
from typing import Optional, List

router = APIRouter(prefix="/core/data", tags=["Generic CRUD"])

@router.get("/{entity}")
async def list_entities(
    entity: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    sort: Optional[str] = Query(None),  # field:asc or field:desc
    filters: Optional[str] = Query(None),  # JSON encoded filters
    db: Session = Depends(get_db)
):
    """
    Generic list endpoint with pagination, sorting, filtering
    """
    # Implementation...
```

### 2. Metadata Service

```python
# backend/app/core/routes/metadata.py

@router.get("/metadata/{entity}")
async def get_entity_metadata(entity: str):
    """
    Returns entity metadata for dynamic UI generation

    Response:
    {
        "entity": "affittuari",
        "displayName": "Affittuari",
        "fields": [
            {
                "name": "nome",
                "type": "string",
                "required": true,
                "maxLength": 100,
                "label": "Nome"
            },
            ...
        ],
        "display": {
            "table": ["nome", "cognome", "email", "telefono"],
            "form": ["nome", "cognome", "codice_fiscale", "email", ...],
            "detail": ["nome", "cognome", "codice_fiscale", ...]
        }
    }
    """
```

### 3. Export Service

```python
# backend/app/core/routes/export.py

@router.post("/export/{entity}")
async def export_entities(
    entity: str,
    format: str = Query("csv", enum=["csv", "xlsx", "pdf"]),
    columns: Optional[List[str]] = Query(None),
    filters: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Export entities to various formats
    """
```

---

## Migration Strategy

### Phase 1: Create Core Components (Week 1-2)
1. Implement DataTable component with basic features
2. Implement FormBuilder component
3. Implement core hooks (useEntityCRUD, useDataTable, useForm)
4. Add common utility components (LoadingSpinner, EmptyState, etc.)

### Phase 2: Migrate One Module as Proof of Concept (Week 2)
1. Choose `affittuari` module (simplest entity)
2. Create configuration files
3. Replace existing components with core components
4. Document the migration process

### Phase 3: Migrate Remaining Modules (Week 3-4)
1. Migrate `proprietari`
2. Migrate `unita_immobiliari`
3. Migrate `contratti`
4. Migrate remaining entities

### Phase 4: Add Advanced Features (Week 4-5)
1. Add export functionality
2. Add bulk actions
3. Add column reordering and visibility
4. Add saved filter presets

### Phase 5: Documentation and Training (Week 5)
1. Complete developer documentation
2. Create example module template
3. Write best practices guide

---

## Expected Benefits

### Code Reduction

| Component Type | Before (avg lines) | After (avg lines) | Reduction |
|---------------|-------------------|-------------------|-----------|
| List Page     | 130-200           | 20-40             | ~80%      |
| Form          | 180-400           | 30-60             | ~85%      |
| Detail Page   | 400-700           | 50-100            | ~85%      |
| API Service   | 30-40             | 5-10              | ~80%      |

### Development Time

| Task                    | Before    | After     | Reduction |
|------------------------|-----------|-----------|-----------|
| New list page          | 2-4 hours | 15-30 min | ~85%      |
| New form               | 3-6 hours | 30-60 min | ~85%      |
| New detail page        | 4-8 hours | 1-2 hours | ~75%      |
| New module (5 entities)| 3-5 days  | 0.5-1 day | ~80%      |

### Consistency Benefits
- Unified look and feel across all modules
- Consistent error handling
- Standardized loading/empty states
- Automatic accessibility compliance
- Responsive design by default

---

## Files to Create

1. **Core Components:**
   - `/frontend/src/core/components/DataTable/DataTable.jsx`
   - `/frontend/src/core/components/DataTable/DataTableToolbar.jsx`
   - `/frontend/src/core/components/DataTable/DataTableBody.jsx`
   - `/frontend/src/core/components/DataTable/DataTablePagination.jsx`
   - `/frontend/src/core/components/FormBuilder/FormBuilder.jsx`
   - `/frontend/src/core/components/FormBuilder/FormModal.jsx`
   - `/frontend/src/core/components/FormBuilder/fields/*.jsx`
   - `/frontend/src/core/components/DetailView/DetailView.jsx`
   - `/frontend/src/core/components/common/*.jsx`

2. **Core Hooks:**
   - `/frontend/src/core/hooks/useEntityCRUD.js`
   - `/frontend/src/core/hooks/useDataTable.js`
   - `/frontend/src/core/hooks/useForm.js`
   - `/frontend/src/core/hooks/usePagination.js`

3. **Core Services:**
   - `/frontend/src/core/services/entityService.js`
   - `/frontend/src/core/services/exportService.js`

4. **Utilities:**
   - `/frontend/src/core/utils/formatters.js`
   - `/frontend/src/core/utils/validators.js`

5. **Module Configuration Example:**
   - `/frontend/src/modules/affitti_lungo/config/affittuari.config.js`

---

## Next Steps

1. Review and approve this architecture document
2. Begin implementation of DataTable component
3. Create the first migrated module as proof of concept
4. Iterate based on feedback
