# Guida Sistema DataTable - Piattaforma Gestione Affitti

## Panoramica

La piattaforma fornisce un sistema di tabelle dati standardizzato e riusabile che include:

- **Selezione colonne**: Mostra/nascondi colonne e riordinale
- **Ordinamento**: Click su header per ordinare asc/desc
- **Selezione multipla**: Checkbox per selezionare righe e applicare azioni batch
- **Paginazione**: Navigazione tra le pagine con selezione dimensione
- **Ricerca/filtri**: Ricerca full-text e filtri per colonna
- **Persistenza preferenze**: Le configurazioni utente vengono salvate nel backend

---

## Architettura

### Backend

```
backend/app/core/
├── models/
│   └── table_configuration.py    # Modello per preferenze utente
├── schemas/
│   └── table_configuration.py    # Schemi Pydantic (ColumnDefinition, TableDefinition)
├── routes/
│   └── table_configurations.py   # API REST
└── platform_services/
    └── table_registry.py         # Registry definizioni tabelle
```

### Frontend

```
frontend/src/core/
├── components/
│   └── DataTable/
│       ├── DataTable.jsx         # Componente principale
│       ├── DataTable.css         # Stili
│       ├── ColumnSelector.jsx    # Selettore colonne
│       ├── ColumnSelector.css    # Stili selettore
│       └── index.js              # Export
└── hooks/
    ├── useDataTable.js           # Hook gestione stato tabella
    └── useTableConfig.js         # Hook configurazione/persistenza
```

---

## Quick Start - Uso Base

### Configurazione Minima

```jsx
import { DataTable } from '../core/components/DataTable';

function MiaLista() {
  const config = {
    endpoint: '/api/v1/miei-dati/',
    title: 'I Miei Dati',
    columns: [
      { field: 'nome', label: 'Nome', sortable: true },
      { field: 'email', label: 'Email', sortable: true },
      { field: 'attivo', label: 'Stato', type: 'boolean' },
    ],
    rowActions: [
      { id: 'view', action: 'view', icon: '👁️', label: 'Visualizza' },
      { id: 'edit', action: 'edit', icon: '✏️', label: 'Modifica' },
      { id: 'delete', action: 'delete', icon: '🗑️', label: 'Elimina' },
    ],
  };

  return (
    <DataTable
      config={config}
      options={{ selectable: true }}
      onAdd={() => console.log('Nuovo')}
      onEdit={(entity) => console.log('Modifica', entity)}
      onDelete={(entity) => console.log('Elimina', entity)}
    />
  );
}
```

---

## Definizione Colonne

### Tipi di Colonna Supportati

| Tipo | Descrizione | Opzioni |
|------|-------------|---------|
| `text` | Testo semplice (default) | - |
| `number` | Numero formattato | `format: "0,0.00"` |
| `currency` | Valuta | `format: "€ 0,0.00"` |
| `date` | Data | `format: "DD/MM/YYYY"` |
| `datetime` | Data e ora | `format: "DD/MM/YYYY HH:mm"` |
| `boolean` | Si/No badge | - |
| `badge` | Badge colorato | `badgeMap: {...}` |
| `link` | Link cliccabile | `linkTo: "/entity/:id"` |

### Esempio Completo Colonne

```javascript
const columns = [
  // Colonna testo con link
  {
    field: 'nome',
    label: 'Nome',
    type: 'link',
    linkTo: '/anagrafiche/:id',
    sortable: true,
    required: true,  // Non può essere nascosta
  },

  // Colonna data
  {
    field: 'data_nascita',
    label: 'Data Nascita',
    type: 'date',
    format: 'DD/MM/YYYY',
    sortable: true,
  },

  // Colonna currency
  {
    field: 'importo',
    label: 'Importo',
    type: 'currency',
    align: 'right',
    sortable: true,
  },

  // Colonna badge con mappa stati
  {
    field: 'stato',
    label: 'Stato',
    type: 'badge',
    badgeMap: {
      'attivo': { label: 'Attivo', variant: 'success' },
      'sospeso': { label: 'Sospeso', variant: 'warning' },
      'chiuso': { label: 'Chiuso', variant: 'danger' },
    },
  },

  // Colonna con render custom
  {
    field: 'indirizzo',
    label: 'Indirizzo',
    render: (value, row) => (
      <span title={value}>
        {value?.substring(0, 30)}...
      </span>
    ),
  },

  // Colonna nascosta di default
  {
    field: 'note',
    label: 'Note',
    visible: false,
  },
];
```

---

## Selezione Colonne (ColumnSelector)

Il DataTable include un selettore colonne integrato che permette di:

- Mostrare/nascondere colonne
- Riordinare colonne tramite drag-and-drop
- Ripristinare configurazione default

### Abilitare il Selettore

```jsx
<DataTable
  config={config}
  options={{
    showColumnSelector: true,  // Mostra bottone "Colonne"
  }}
/>
```

### Persistenza Configurazione

Per salvare le preferenze utente nel backend, aggiungi `moduleName` e `entityName` al config:

```jsx
const config = {
  endpoint: '/api/v1/soggetti/',
  title: 'Soggetti Anagrafici',
  moduleName: 'anagrafica_italiana',  // <- Per persistenza
  entityName: 'SoggettoAnagrafico',   // <- Per persistenza
  columns: [...],
};
```

Le preferenze vengono automaticamente caricate e salvate per ogni utente.

---

## Selezione Multipla e Azioni Batch

### Abilitare Selezione

```jsx
<DataTable
  config={{
    ...config,
    bulkActions: [
      { id: 'bulkDelete', action: 'bulkDelete', label: 'Elimina selezionati' },
      {
        id: 'export',
        label: 'Esporta selezionati',
        variant: 'primary',
        onClick: (selectedItems) => {
          console.log('Esporta:', selectedItems);
        },
      },
    ],
  }}
  options={{ selectable: true }}
/>
```

### Accesso a Elementi Selezionati

Se usi `useDataTable` direttamente:

```jsx
import { useDataTable } from '../core/hooks';

function MiaLista() {
  const table = useDataTable({
    endpoint: '/api/v1/dati/',
    columns: [...],
  });

  const handleBulkAction = () => {
    const ids = Array.from(table.selectedIds);
    const items = table.selectedItems;
    console.log('Selezionati:', ids, items);
  };

  return (
    <div>
      <button onClick={handleBulkAction}>
        Azione su {table.selectedIds.size} elementi
      </button>
      {/* ... */}
    </div>
  );
}
```

---

## Ordinamento

### Ordinamento Base

Ogni colonna con `sortable: true` può essere ordinata cliccando sull'header.

```javascript
const columns = [
  { field: 'nome', label: 'Nome', sortable: true },
  { field: 'data', label: 'Data', sortable: true },
];
```

### Ordinamento Default

```javascript
const config = {
  columns: [...],
  defaultSort: {
    field: 'data',
    order: 'desc',  // 'asc' o 'desc'
  },
};
```

### Ordinamento Programmatico

```jsx
const table = useDataTable({ ... });

// Ordina per campo
table.handleSort('nome');  // Primo click: asc, secondo: desc

// Stato corrente
console.log(table.sortField, table.sortOrder);
```

---

## API Backend - Configurazioni Tabelle

### Registrare Definizione Tabella (Backend)

Nel modulo, registra la definizione della tabella:

```python
# modules/mio_modulo/__init__.py
from app.core.platform_services.table_registry import register_table

def register_module(app):
    # Registra definizione tabella
    register_table({
        "module_name": "mio_modulo",
        "entity_name": "MiaEntita",
        "title": "Le Mie Entità",
        "columns": [
            {"field": "nome", "label": "Nome", "type": "text", "required": True, "sortable": True},
            {"field": "email", "label": "Email", "type": "text", "sortable": True},
            {"field": "attivo", "label": "Attivo", "type": "boolean"},
            {"field": "data_creazione", "label": "Creato il", "type": "datetime", "visible": False},
        ],
        "default_visible": ["nome", "email", "attivo"],
        "default_sort_field": "nome",
        "default_sort_order": "asc",
        "selectable": True,
        "searchable": True,
        "exportable": True,
        "row_actions": ["view", "edit", "delete"],
        "bulk_actions": ["bulkDelete"],
    })
```

### Endpoint API

| Metodo | Endpoint | Descrizione |
|--------|----------|-------------|
| `GET` | `/tables/definitions` | Lista tutte le definizioni |
| `GET` | `/tables/definitions/{module}/{entity}` | Definizione singola |
| `GET` | `/tables/config/{module}/{entity}` | Config + preferenze utente |
| `PUT` | `/tables/config/{module}/{entity}` | Salva preferenze |
| `DELETE` | `/tables/config/{module}/{entity}` | Reset a default |
| `POST` | `/tables/config/{module}/{entity}/columns` | Aggiorna solo colonne visibili |

### Esempio Response Config

```json
{
  "definition": {
    "module_name": "anagrafica_italiana",
    "entity_name": "SoggettoAnagrafico",
    "title": "Soggetti Anagrafici",
    "columns": [
      {"field": "nome", "label": "Nome", "type": "text", "required": true},
      {"field": "email", "label": "Email", "type": "text"}
    ],
    "default_visible": ["nome", "email"],
    "selectable": true
  },
  "user_config": {
    "id": 1,
    "user_id": 5,
    "visible_columns": ["nome", "email", "telefono"],
    "sort_field": "nome",
    "sort_order": "asc",
    "page_size": 50
  }
}
```

---

## Hook useTableConfig

Per integrazione avanzata con persistenza:

```jsx
import { useTableConfig } from '../core/hooks';

function MiaTabella() {
  const {
    definition,      // Definizione tabella dal backend
    effectiveConfig, // Config effettivo (user o default)
    columns,         // Colonne con stato visibilità
    visibleColumns,  // Solo colonne visibili
    loading,
    saving,
    updateColumns,   // Aggiorna colonne visibili
    updateConfig,    // Aggiorna config completo
    resetConfig,     // Reset a default
  } = useTableConfig({
    moduleName: 'anagrafica_italiana',
    entityName: 'SoggettoAnagrafico',
  });

  if (loading) return <div>Caricamento...</div>;

  return (
    <div>
      <h1>{definition.title}</h1>

      <button onClick={() => updateColumns(['nome', 'email'])}>
        Mostra solo Nome ed Email
      </button>

      <button onClick={resetConfig}>
        Reset configurazione
      </button>

      {/* Usa visibleColumns per renderizzare */}
    </div>
  );
}
```

---

## Esempio Completo

```jsx
import { useState } from 'react';
import { DataTable } from '../core/components/DataTable';
import ImportButton from '../components/Platform/ImportButton';
import ExportButton from '../components/Platform/ExportButton';

function SoggettiAnagraficiList() {
  const [refreshKey, setRefreshKey] = useState(0);

  const config = {
    endpoint: '/anagrafica/soggetti/',
    title: 'Soggetti Anagrafici',
    moduleName: 'anagrafica_italiana',
    entityName: 'SoggettoAnagrafico',
    columns: [
      { field: 'nome', label: 'Nome', type: 'link', linkTo: '/anagrafiche/:id', required: true, sortable: true },
      { field: 'cognome', label: 'Cognome', sortable: true },
      { field: 'codice_fiscale', label: 'Codice Fiscale', sortable: true },
      { field: 'email', label: 'Email', sortable: true },
      { field: 'telefono', label: 'Telefono' },
      { field: 'citta', label: 'Città', sortable: true },
      { field: 'attivo', label: 'Stato', type: 'boolean' },
      { field: 'data_creazione', label: 'Creato', type: 'datetime', visible: false },
    ],
    defaultSort: { field: 'cognome', order: 'asc' },
    rowActions: [
      { id: 'view', action: 'view', to: '/anagrafiche/:id', icon: '👁️' },
      { id: 'edit', action: 'edit', icon: '✏️' },
      { id: 'delete', action: 'delete', icon: '🗑️' },
    ],
    bulkActions: [
      { id: 'bulkDelete', action: 'bulkDelete', label: 'Elimina selezionati' },
    ],
    searchPlaceholder: 'Cerca per nome, CF, email...',
    addButtonLabel: 'Nuovo Soggetto',
  };

  return (
    <DataTable
      key={refreshKey}
      config={config}
      options={{
        selectable: true,
        showSearch: true,
        showPagination: true,
        showColumnSelector: true,
        pageSize: 20,
      }}
      customActions={
        <>
          <ImportButton
            moduleName="anagrafica_italiana"
            entityName="SoggettoAnagrafico"
            entityLabel="Soggetti"
            onImportComplete={() => setRefreshKey(k => k + 1)}
          />
          <ExportButton
            moduleName="anagrafica_italiana"
            entityName="SoggettoAnagrafico"
            entityLabel="Soggetti"
          />
        </>
      }
      onAdd={() => navigate('/anagrafiche/nuovo')}
      onView={(entity) => navigate(`/anagrafiche/${entity.id}`)}
      onEdit={(entity) => navigate(`/anagrafiche/${entity.id}/modifica`)}
    />
  );
}
```

---

## Multi-Tenancy

Il sistema è completamente tenant-aware:

1. Le configurazioni utente sono salvate nello schema tenant
2. Il `user_id` nella configurazione è relativo al tenant
3. Le definizioni tabelle sono globali (dal registry in memoria)

---

## Riferimenti

| Risorsa | Path |
|---------|------|
| **DataTable Component** | `frontend/src/core/components/DataTable/` |
| **ColumnSelector** | `frontend/src/core/components/DataTable/ColumnSelector.jsx` |
| **useDataTable Hook** | `frontend/src/core/hooks/useDataTable.js` |
| **useTableConfig Hook** | `frontend/src/core/hooks/useTableConfig.js` |
| **Backend Routes** | `backend/app/core/routes/table_configurations.py` |
| **Table Registry** | `backend/app/core/platform_services/table_registry.py` |
| **Model** | `backend/app/core/models/table_configuration.py` |
| **Schemas** | `backend/app/core/schemas/table_configuration.py` |
