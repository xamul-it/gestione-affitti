import { useState, useCallback } from 'react';
import { DataTable } from '../../../../core/components';
import CategoriaCatastaleForm from './CategoriaCatastaleForm';
import './CategorieCatastali.css';

const categorieCatastaliTableConfig = {
  endpoint: '/categorie-catastali/',
  title: 'Categorie Catastali',
  searchPlaceholder: 'Cerca per codice, nome o gruppo...',
  emptyTitle: 'Nessuna categoria catastale trovata',
  emptyMessage: 'Non ci sono categorie catastali registrate.',
  addButtonLabel: 'Nuova Categoria',
  columns: [
    { field: 'codice', label: 'Codice', sortable: true, filterable: true },
    { field: 'nome', label: 'Nome', sortable: true, filterable: true },
    { field: 'gruppo', label: 'Gruppo', render: (value) => value || '-' },
    { field: 'descrizione', label: 'Descrizione', render: (value) => value || '-' },
    {
      field: 'ordinamento',
      label: 'Ordinamento',
      render: (value) => value ?? '-',
    },
    {
      field: 'attiva',
      label: 'Attiva',
      render: (value) => (
        <span className={`status-badge ${value ? 'active' : 'inactive'}`}>
          {value ? '✓' : '✗'}
        </span>
      ),
    },
  ],
  defaultSort: { field: 'ordinamento', order: 'asc' },
  rowActions: [
    {
      id: 'edit',
      label: 'Modifica',
      action: 'edit',
      variant: 'secondary',
    },
    {
      id: 'delete',
      label: 'Elimina',
      action: 'delete',
      variant: 'danger',
    },
  ],
};

function CategoriaCatastaleFormModal({ entity, onClose }) {
  return (
    <CategoriaCatastaleForm
      categoria={entity}
      onClose={onClose}
    />
  );
}

function CategorieCatastaliList() {
  const [showOnlyActive, setShowOnlyActive] = useState(false);

  const renderToolbar = useCallback(({ table }) => (
    <label className="filter-checkbox">
      <input
        type="checkbox"
        checked={showOnlyActive}
        onChange={(e) => {
          const checked = e.target.checked;
          setShowOnlyActive(checked);
          table.setFilter('attiva', checked ? true : '');
        }}
      />
      Mostra solo attive
    </label>
  ), [showOnlyActive]);

  return (
    <div className="container">
      <DataTable
        config={categorieCatastaliTableConfig}
        FormComponent={CategoriaCatastaleFormModal}
        toolbarContent={renderToolbar}
        options={{
          selectable: true,
          showSearch: true,
          showPagination: true,
          pageSize: 20,
        }}
      />
    </div>
  );
}

export default CategorieCatastaliList;
