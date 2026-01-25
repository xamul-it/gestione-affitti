import { useState, useCallback } from 'react';
import { DataTable } from '../../../../core/components';
import TipologiaTerrenoForm from './TipologiaTerrenoForm';
import '../CategorieCatastali/CategorieCatastali.css';

const tipologieTerrenoTableConfig = {
  endpoint: '/tipologie-terreno/',
  title: 'Tipologie Terreno',
  searchPlaceholder: 'Cerca per codice o nome...',
  emptyTitle: 'Nessuna tipologia terreno trovata',
  emptyMessage: 'Non ci sono tipologie terreno registrate.',
  addButtonLabel: 'Nuova Tipologia',
  columns: [
    { field: 'codice', label: 'Codice', sortable: true, filterable: true },
    { field: 'nome', label: 'Nome', sortable: true, filterable: true },
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

function TipologiaTerrenoFormModal({ entity, onClose }) {
  return (
    <TipologiaTerrenoForm
      tipologia={entity}
      onClose={onClose}
    />
  );
}

function TipologieTerrenoList() {
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
        config={tipologieTerrenoTableConfig}
        FormComponent={TipologiaTerrenoFormModal}
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

export default TipologieTerrenoList;
