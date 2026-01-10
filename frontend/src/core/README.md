# Core Components Documentation

## Overview

The core components system provides reusable, configuration-driven UI components that dramatically reduce development time for new modules. Instead of writing hundreds of lines of boilerplate code for each entity, you define a configuration and let the core components handle rendering, state management, validation, and API interactions.

## Quick Start

### Creating a New Entity Page

1. **Create the configuration file:**

```javascript
// modules/my_module/config/myEntity.config.js
export const myEntityConfig = {
  entity: 'my_entities',
  endpoint: '/my-entities/',

  table: {
    title: 'Gestione My Entities',
    columns: [
      { field: 'name', label: 'Nome', sortable: true },
      { field: 'email', label: 'Email' },
    ],
    rowActions: [
      { id: 'view', to: '/my-entities/:id' },
      { id: 'edit', action: 'edit' },
      { id: 'delete', action: 'delete' },
    ],
  },

  form: {
    sections: [
      {
        title: 'Informazioni',
        columns: 2,
        fields: [
          { name: 'name', label: 'Nome', type: 'text', required: true },
          { name: 'email', label: 'Email', type: 'email', required: true },
        ],
      },
    ],
  },
};
```

2. **Create the page component:**

```javascript
// modules/my_module/pages/MyEntityPage.jsx
import React from 'react';
import { DataTable, FormBuilder, FormModal } from '../../../core/components';
import { myEntityConfig } from '../config';

function MyEntityFormModal({ entity, onClose }) {
  return (
    <FormModal title={entity ? 'Modifica' : 'Nuovo'} onClose={onClose}>
      <FormBuilder
        config={myEntityConfig.form}
        entity={entity}
        apiEndpoint={myEntityConfig.endpoint}
        onSuccess={() => setTimeout(onClose, 1000)}
        onCancel={onClose}
      />
    </FormModal>
  );
}

function MyEntityPage() {
  return (
    <DataTable
      config={{
        endpoint: myEntityConfig.endpoint,
        title: myEntityConfig.table.title,
        columns: myEntityConfig.table.columns,
        rowActions: myEntityConfig.table.rowActions,
      }}
      FormComponent={MyEntityFormModal}
    />
  );
}

export default MyEntityPage;
```

That's it! You now have a fully functional CRUD page with:
- Data table with sorting and search
- Create/Edit form in modal
- Delete confirmation
- Loading states and error handling
- Pagination

---

## Components Reference

### DataTable

A configurable data table with sorting, filtering, pagination, and row actions.

#### Props

| Prop | Type | Description |
|------|------|-------------|
| `config` | Object | Table configuration (see below) |
| `FormComponent` | Component | Form component to render in modal |
| `onAdd` | Function | Custom add handler (overrides default modal) |
| `onEdit` | Function | Custom edit handler |
| `onView` | Function | Custom view handler |
| `onDelete` | Function | Custom delete handler |
| `onRowClick` | Function | Row click handler |
| `options` | Object | Additional options |

#### Config Object

```javascript
{
  endpoint: '/api/endpoint/',     // API endpoint for CRUD operations
  title: 'Page Title',            // Page title
  columns: [...],                 // Column definitions (see below)
  rowActions: [...],              // Row action buttons
  bulkActions: [...],             // Bulk action buttons
  defaultSort: { field, order }, // Default sort
  searchPlaceholder: 'Search...', // Search input placeholder
  emptyTitle: 'No data',          // Empty state title
  emptyMessage: 'No records...',  // Empty state message
  addButtonLabel: 'New',          // Add button label
}
```

#### Column Definition

```javascript
{
  field: 'name',           // Field name (supports nested: 'user.name')
  label: 'Name',           // Column header label
  type: 'text',            // Type: text|number|date|currency|badge|link|boolean
  sortable: true,          // Enable sorting
  filterable: true,        // Enable filtering
  width: 150,              // Column width
  align: 'left',           // Alignment: left|center|right
  visible: true,           // Default visibility
  render: (value, row) => {...},  // Custom render function

  // Type-specific options
  linkTo: '/entity/:id',   // For link type
  badgeMap: {...},         // For badge type
}
```

#### Row Action Definition

```javascript
{
  id: 'view',              // Unique identifier
  label: 'View',           // Button label
  action: 'view',          // Built-in action: view|edit|delete
  to: '/entity/:id',       // Link destination (for view)
  variant: 'primary',      // Button variant: primary|secondary|danger
  icon: 'eye',             // Icon (optional)
  onClick: (row) => {...}, // Custom click handler
}
```

#### Options

```javascript
{
  selectable: false,       // Enable row selection
  showSearch: true,        // Show search input
  showPagination: true,    // Show pagination
  showColumnSelector: false, // Show column visibility toggle
  pageSize: 20,            // Items per page
  exportable: false,       // Enable export (future)
}
```

---

### FormBuilder

A dynamic form generator that creates forms from configuration.

#### Props

| Prop | Type | Description |
|------|------|-------------|
| `config` | Object | Form configuration with sections |
| `entity` | Object | Entity data for editing (null for create) |
| `apiEndpoint` | String | API endpoint for save |
| `onSubmit` | Function | Custom submit handler |
| `onCancel` | Function | Cancel callback |
| `onSuccess` | Function | Success callback |
| `onError` | Function | Error callback |
| `submitLabel` | String | Submit button label |
| `cancelLabel` | String | Cancel button label |
| `showCancel` | Boolean | Show cancel button |

#### Config Object

```javascript
{
  sections: [
    {
      title: 'Section Title',   // Section header
      columns: 2,               // Grid columns (1-4)
      fields: [...],            // Field definitions
    },
  ],
}
```

#### Field Definition

```javascript
{
  name: 'email',               // Field name (matches API field)
  label: 'Email',              // Field label
  type: 'email',               // Type (see below)
  required: true,              // Required validation
  placeholder: 'Enter email',  // Placeholder text
  helpText: 'Help text...',    // Help text below field
  disabled: false,             // Disabled state
  readOnly: false,             // Read-only state
  defaultValue: '',            // Default value
  colSpan: 2,                  // Column span in grid

  // Validation
  validation: {
    minLength: 3,
    maxLength: 100,
    pattern: /regex/,
    custom: (value, formData) => null | 'error message',
  },

  // Type-specific options
  options: [...],              // For select
  optionValue: 'id',           // Option value field
  optionLabel: 'name',         // Option label field
  rows: 3,                     // For textarea
  min: 0,                      // For number/date
  max: 100,                    // For number/date
  step: 0.01,                  // For number

  // Conditional display
  showIf: (formData) => formData.type === 'SPECIAL',

  // Dynamic options
  optionsEndpoint: '/api/options/',
  optionsLoader: async (formData) => [...],
}
```

#### Field Types

| Type | Component | Description |
|------|-----------|-------------|
| `text` | TextField | Single-line text input |
| `email` | TextField | Email input with validation |
| `tel` | TextField | Phone number input |
| `password` | TextField | Password input |
| `url` | TextField | URL input |
| `number` | NumberField | Numeric input |
| `select` | SelectField | Dropdown select |
| `date` | DateField | Date picker |
| `textarea` | TextareaField | Multi-line text |
| `checkbox` | CheckboxField | Boolean checkbox |

---

### FormModal

A modal wrapper for forms.

#### Props

| Prop | Type | Description |
|------|------|-------------|
| `title` | String | Modal title |
| `children` | ReactNode | Modal content (typically FormBuilder) |
| `onClose` | Function | Close callback |
| `size` | String | Size: small|medium|large|fullscreen |
| `closeOnBackdrop` | Boolean | Close on backdrop click |
| `closeOnEscape` | Boolean | Close on Escape key |
| `showCloseButton` | Boolean | Show close button |

---

### Common Components

#### Badge

```jsx
import { Badge, StatusBadge } from '@/core/components';

<Badge variant="success">Active</Badge>
<StatusBadge status="ATTIVO" />
```

#### LoadingSpinner

```jsx
import { LoadingSpinner } from '@/core/components';

<LoadingSpinner message="Loading..." />
<LoadingSpinner overlay />
<LoadingSpinner size="small" inline />
```

#### EmptyState

```jsx
import { EmptyState } from '@/core/components';

<EmptyState
  icon="file"
  title="No data"
  message="No records found"
  action={<button>Add New</button>}
/>
```

#### ErrorMessage

```jsx
import { ErrorMessage } from '@/core/components';

<ErrorMessage
  message="An error occurred"
  onRetry={handleRetry}
  onDismiss={clearError}
/>
```

#### ConfirmDialog

```jsx
import { ConfirmDialog } from '@/core/components';

<ConfirmDialog
  isOpen={showConfirm}
  title="Confirm Delete"
  message="Are you sure?"
  variant="danger"
  onConfirm={handleDelete}
  onCancel={() => setShowConfirm(false)}
/>
```

---

## Hooks Reference

### useEntityCRUD

Generic CRUD operations hook.

```javascript
import { useEntityCRUD } from '@/core/hooks';

const {
  data,           // Array of entities
  loading,        // Loading state
  error,          // Error message
  pagination,     // { page, pageSize, total, totalPages }

  fetchAll,       // (params) => Promise
  fetchById,      // (id) => Promise
  create,         // (data) => Promise
  update,         // (id, data) => Promise
  remove,         // (id) => Promise
  bulkDelete,     // (ids) => Promise
  refresh,        // () => void
  clearError,     // () => void
} = useEntityCRUD('/api/endpoint/', {
  autoFetch: true,
  defaultParams: {},
  onError: (err) => {},
  onSuccess: (action, data) => {},
});
```

### useForm

Form state management hook.

```javascript
import { useForm } from '@/core/hooks';

const {
  values,         // Form values
  errors,         // Field errors
  touched,        // Touched fields
  isDirty,        // Has changes
  isValid,        // All validations pass
  isSubmitting,   // Submit in progress

  handleChange,   // (e) => void
  handleBlur,     // (e) => void
  handleSubmit,   // (onSubmit) => (e) => void
  setFieldValue,  // (name, value) => void
  setFieldError,  // (name, error) => void
  reset,          // (newValues?) => void
  validateAll,    // () => boolean
} = useForm(initialValues, validationRules, options);
```

### useDataTable

Data table state management hook.

```javascript
import { useDataTable } from '@/core/hooks';

const table = useDataTable({
  endpoint: '/api/endpoint/',
  columns: [...],
  defaultSort: { field: 'name', order: 'asc' },
  pageSize: 20,
});

// Access state
table.data;
table.loading;
table.error;
table.pagination;
table.sortField;
table.sortOrder;
table.filters;
table.searchTerm;
table.selectedIds;

// Call actions
table.handleSort('field');
table.setFilter('field', value);
table.setSearchTerm('query');
table.setPage(2);
table.toggleSelect(id);
table.selectAll();
table.refresh();
```

---

## Utilities Reference

### Formatters

```javascript
import { formatDate, formatCurrency, formatValue } from '@/core/utils';

formatDate('2024-01-15');           // "15/01/2024"
formatCurrency(1500);                // "1.500,00 EUR"
formatValue(value, 'date');          // Automatic formatting by type
```

### Validators

```javascript
import { validators } from '@/core/utils';

const rules = {
  email: validators.compose(
    validators.required,
    validators.email()
  ),
  codice_fiscale: validators.codiceFiscale(),
  cap: validators.cap(),
};
```

---

## Migration Guide

### Migrating an Existing List Component

**Before (150+ lines):**
```javascript
function EntityList() {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showForm, setShowForm] = useState(false);
  const [editing, setEditing] = useState(null);

  useEffect(() => { fetchData(); }, []);

  const fetchData = async () => {
    try {
      setLoading(true);
      const response = await api.getAll();
      setData(response.data);
    } catch (err) {
      setError('Error loading data');
    } finally {
      setLoading(false);
    }
  };

  // ... 100+ more lines of handlers, render logic, etc.
}
```

**After (~30 lines):**
```javascript
import { DataTable } from '@/core/components';
import { entityConfig } from '../config';

function EntityPage() {
  return (
    <DataTable
      config={entityConfig.table}
      FormComponent={EntityFormModal}
    />
  );
}
```

### Migrating an Existing Form Component

**Before (200+ lines):**
```javascript
function EntityForm({ entity, onClose }) {
  const [formData, setFormData] = useState({
    name: '', email: '', // ... many fields
  });
  const [error, setError] = useState(null);

  useEffect(() => {
    if (entity) setFormData(entity);
  }, [entity]);

  const handleChange = (e) => { /* ... */ };
  const handleSubmit = async (e) => { /* ... */ };

  return (
    <form onSubmit={handleSubmit}>
      {/* ... 150+ lines of form fields */}
    </form>
  );
}
```

**After (~10 lines + config):**
```javascript
import { FormBuilder, FormModal } from '@/core/components';
import { entityConfig } from '../config';

function EntityFormModal({ entity, onClose }) {
  return (
    <FormModal title={entity ? 'Edit' : 'New'} onClose={onClose}>
      <FormBuilder
        config={entityConfig.form}
        entity={entity}
        apiEndpoint={entityConfig.endpoint}
        onSuccess={() => onClose()}
        onCancel={onClose}
      />
    </FormModal>
  );
}
```

---

## Best Practices

### 1. Keep Configurations Separate

Put entity configurations in dedicated files:
```
modules/my_module/
  config/
    entity1.config.js
    entity2.config.js
    index.js
  pages/
    Entity1Page.jsx
```

### 2. Use Composition for Custom Features

For entity-specific features, compose core components:

```javascript
function EntityFormModal({ entity, onClose }) {
  return (
    <FormModal title="..." onClose={onClose}>
      <FormBuilder config={config} ... />

      {/* Custom feature for this entity */}
      {entity?.id && <DocumentSection entityId={entity.id} />}
    </FormModal>
  );
}
```

### 3. Leverage Custom Render Functions

For complex cell rendering, use the `render` prop:

```javascript
columns: [
  {
    field: 'status',
    label: 'Status',
    render: (value, row) => (
      <div className="status-cell">
        <StatusBadge status={value} />
        {row.urgent && <span className="urgent-badge">!</span>}
      </div>
    ),
  },
]
```

### 4. Use showIf for Conditional Fields

```javascript
fields: [
  {
    name: 'type',
    label: 'Type',
    type: 'select',
    options: ['A', 'B', 'C'],
  },
  {
    name: 'special_field',
    label: 'Special Field',
    type: 'text',
    showIf: (formData) => formData.type === 'C',
  },
]
```

---

## File Structure

```
frontend/src/core/
  components/
    DataTable/
      DataTable.jsx
      DataTable.css
      index.js
    FormBuilder/
      FormBuilder.jsx
      FormModal.jsx
      FormBuilder.css
      fields/
        TextField.jsx
        NumberField.jsx
        SelectField.jsx
        DateField.jsx
        TextareaField.jsx
        CheckboxField.jsx
        index.js
      index.js
    common/
      LoadingSpinner.jsx
      EmptyState.jsx
      ErrorMessage.jsx
      ConfirmDialog.jsx
      Badge.jsx
      common.css
      index.js
    index.js
  hooks/
    useEntityCRUD.js
    useForm.js
    useDataTable.js
    index.js
  utils/
    formatters.js
    validators.js
    index.js
  README.md
```
