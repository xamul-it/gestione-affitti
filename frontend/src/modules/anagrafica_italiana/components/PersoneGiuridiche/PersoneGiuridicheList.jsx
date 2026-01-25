import { useState, useCallback } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { renderIcon } from '../../../../components/Navigation/iconRegistry.jsx';
import { DataTable } from '../../../../core/components';
import ImportButton from '../../../../components/Platform/ImportButton';
import ExportButton from '../../../../components/Platform/ExportButton';
import '../SoggettiAnagrafici/SoggettiAnagraficiList.css';

const personeGiuridicheTableConfig = {
  endpoint: '/anagrafica/soggetti-v2/',
  title: 'Persone Giuridiche',
  searchPlaceholder: 'Cerca per ragione sociale, CF o email...',
  emptyTitle: 'Nessuna persona giuridica trovata',
  emptyMessage: 'Non ci sono persone giuridiche registrate.',
  addButtonLabel: 'Nuova Persona Giuridica',
  defaultParams: {
    limit: 1000,
  },
  defaultFilters: {
    tipo_soggetto: (value) => value === 'PERSONA_GIURIDICA',
  },
  columns: [
    { field: 'ragione_sociale', label: 'Ragione Sociale', filterable: true, sortable: true },
    { field: 'partita_iva', label: 'Partita IVA', filterable: true },
    { field: 'email', label: 'Email', filterable: true },
    { field: 'telefono', label: 'Telefono', filterable: true },
    { field: 'codice_fiscale', label: 'Codice Fiscale', filterable: true, visible: false },
    { field: 'citta', label: 'Citta', filterable: true, visible: false },
    { field: 'attivo', label: 'Stato', visible: false },
  ],
  defaultSort: { field: 'ragione_sociale', order: 'asc' },
  rowActions: [
    {
      id: 'view',
      label: 'Dettagli',
      action: 'view',
      variant: 'secondary',
      icon: renderIcon('info', { size: 14 }),
    },
    {
      id: 'edit',
      label: 'Modifica',
      action: 'edit',
      variant: 'secondary',
      icon: renderIcon('pencil', { size: 14 }),
    },
    {
      id: 'delete',
      label: 'Elimina',
      action: 'delete',
      variant: 'danger',
      icon: renderIcon('trash', { size: 14 }),
    },
  ],
};

function PersoneGiuridicheList() {
  const navigate = useNavigate();
  const [attiviSolo, setAttiviSolo] = useState(false);

  const renderToolbar = useCallback(({ table }) => (
    <label className="filter-checkbox">
      <input
        type="checkbox"
        checked={attiviSolo}
        onChange={(e) => {
          const checked = e.target.checked;
          setAttiviSolo(checked);
          table.setFilter('attivo', checked ? true : '');
        }}
      />
      <span>Solo attivi</span>
    </label>
  ), [attiviSolo]);

  const columns = [
    {
      ...personeGiuridicheTableConfig.columns[0],
      render: (value, row) => (
        <Link to={`/anagrafiche/persone-giuridiche/${row.id}`} className="table-link">
          {value || '(Non specificato)'}
        </Link>
      ),
    },
    {
      ...personeGiuridicheTableConfig.columns[1],
      render: (value) => value || '-',
    },
    {
      ...personeGiuridicheTableConfig.columns[2],
      render: (value) => value || '-',
    },
    {
      ...personeGiuridicheTableConfig.columns[3],
      render: (value, row) => value || row.cellulare || '-',
    },
    {
      ...personeGiuridicheTableConfig.columns[4],
      render: (value) => value || '-',
    },
    {
      ...personeGiuridicheTableConfig.columns[5],
      render: (value) => value || '-',
    },
    {
      ...personeGiuridicheTableConfig.columns[6],
      render: (value) => (
        <span className={`status-badge ${value ? 'active' : 'inactive'}`}>
          {value ? 'Attivo' : 'Inattivo'}
        </span>
      ),
    },
  ];

  return (
    <div className="soggetti-list-container">
      <DataTable
        config={{
          ...personeGiuridicheTableConfig,
          columns,
        }}
        toolbarContent={renderToolbar}
        customActions={({ table }) => (
          <>
            <ImportButton
              moduleName="anagrafica_italiana"
              entityName="SoggettoAnagrafico"
              entityLabel="Persone Giuridiche"
              onImportComplete={() => table.refresh()}
            />
            <ExportButton
              moduleName="anagrafica_italiana"
              entityName="SoggettoAnagrafico"
              entityLabel="Persone Giuridiche"
            />
          </>
        )}
        onAdd={() => navigate('/anagrafiche/persone-giuridiche/nuovo')}
        onView={(row) => navigate(`/anagrafiche/persone-giuridiche/${row.id}`)}
        onEdit={(row) => navigate(`/anagrafiche/persone-giuridiche/${row.id}/modifica`)}
        options={{
          selectable: true,
          showSearch: true,
          showPagination: true,
          pageSize: 50,
        }}
      />
    </div>
  );
}

export default PersoneGiuridicheList;
