import { useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { DataTable } from '../../../../core/components';
import ImportButton from '../../../../components/Platform/ImportButton';
import ExportButton from '../../../../components/Platform/ExportButton';
import '../SoggettiAnagrafici/SoggettiAnagraficiList.css';

const personeFisicheTableConfig = {
  endpoint: '/anagrafica/soggetti-v2/',
  title: 'Persone Fisiche',
  searchPlaceholder: 'Cerca per nome, CF, email o telefono...',
  emptyTitle: 'Nessuna persona fisica trovata',
  emptyMessage: 'Non ci sono persone fisiche registrate.',
  addButtonLabel: 'Nuova Persona Fisica',
  defaultParams: {
    limit: 1000,
  },
  defaultFilters: {
    tipo_soggetto: (value) => value === 'PERSONA_FISICA',
  },
  columns: [
    { field: 'nome_completo', label: 'Nome Completo', sortable: true },
    { field: 'codice_fiscale', label: 'Codice Fiscale', filterable: true },
    { field: 'data_nascita', label: 'Data Nascita' },
    { field: 'luogo_nascita', label: 'Luogo Nascita', filterable: true },
    { field: 'email', label: 'Email', filterable: true },
    { field: 'telefono', label: 'Telefono', filterable: true },
    { field: 'citta', label: 'Citta', filterable: true },
    { field: 'partita_iva', label: 'P.IVA', filterable: true },
    { field: 'attivo', label: 'Stato' },
    { field: 'nome', label: 'Nome', filterable: true, visible: false },
    { field: 'cognome', label: 'Cognome', filterable: true, visible: false },
  ],
  defaultSort: { field: 'cognome', order: 'asc' },
  rowActions: [
    { id: 'view', label: 'Dettagli', action: 'view', variant: 'secondary' },
    { id: 'edit', label: 'Modifica', action: 'edit', variant: 'secondary' },
    { id: 'delete', label: 'Elimina', action: 'delete', variant: 'danger' },
  ],
};

function PersoneFisicheList() {
  const navigate = useNavigate();
  const [attiviSolo, setAttiviSolo] = useState(false);

  const getNomeCompleto = useCallback((persona) => (
    `${persona.nome || ''} ${persona.cognome || ''}`.trim() || '(Non specificato)'
  ), []);

  const formatDate = useCallback((dateString) => {
    if (!dateString) return '-';
    return new Date(dateString).toLocaleDateString('it-IT');
  }, []);

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
      ...personeFisicheTableConfig.columns[0],
      render: (_, row) => (
        <span className="soggetto-name">
          {getNomeCompleto(row)}
        </span>
      ),
    },
    {
      ...personeFisicheTableConfig.columns[1],
      render: (value) => <code className="cf-badge">{value || '-'}</code>,
    },
    {
      ...personeFisicheTableConfig.columns[2],
      render: (value) => formatDate(value),
    },
    {
      ...personeFisicheTableConfig.columns[3],
      render: (value) => value || '-',
    },
    {
      ...personeFisicheTableConfig.columns[4],
      render: (value) => value || '-',
    },
    {
      ...personeFisicheTableConfig.columns[5],
      render: (value, row) => value || row.cellulare || '-',
    },
    {
      ...personeFisicheTableConfig.columns[6],
      render: (value) => value || '-',
    },
    {
      ...personeFisicheTableConfig.columns[7],
      render: (value) => value ? <code className="piva-badge">{value}</code> : '-',
    },
    {
      ...personeFisicheTableConfig.columns[8],
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
          ...personeFisicheTableConfig,
          columns,
        }}
        toolbarContent={renderToolbar}
        customActions={({ table }) => (
          <>
            <ImportButton
              moduleName="anagrafica_italiana"
              entityName="SoggettoAnagrafico"
              entityLabel="Persone Fisiche"
              onImportComplete={() => table.refresh()}
            />
            <ExportButton
              moduleName="anagrafica_italiana"
              entityName="SoggettoAnagrafico"
              entityLabel="Persone Fisiche"
            />
          </>
        )}
        onAdd={() => navigate('/anagrafiche/persone-fisiche/nuovo')}
        onView={(row) => navigate(`/anagrafiche/persone-fisiche/${row.id}`)}
        onEdit={(row) => navigate(`/anagrafiche/persone-fisiche/${row.id}/modifica`)}
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

export default PersoneFisicheList;
