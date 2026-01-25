import { useState, useCallback } from 'react';
import { DataTable } from '../../../../core/components';
import './ComuniList.css';

const comuniTableConfig = {
  endpoint: '/anagrafica/domini/comuni',
  title: 'Comuni Italiani',
  searchPlaceholder: 'Cerca per nome comune...',
  emptyTitle: 'Nessun comune trovato',
  emptyMessage: 'Non ci sono comuni disponibili.',
  addButtonLabel: 'Nuovo Comune',
  defaultParams: {
    limit: 10000,
  },
  columns: [
    { field: 'nome', label: 'Comune', filterable: true, sortable: true },
    { field: 'provincia_sigla', label: 'Provincia', filterable: true, sortable: true },
    { field: 'regione', label: 'Regione', filterable: true },
    { field: 'cap', label: 'CAP', filterable: true },
    { field: 'codice_catastale', label: 'Codice Catastale' },
    { field: 'codice_istat', label: 'Codice ISTAT' },
    { field: 'attivo', label: 'Attivo' },
  ],
  defaultSort: { field: 'nome', order: 'asc' },
};

function ComuniList() {
  const [searchProvincia, setSearchProvincia] = useState('');
  const [searchCAP, setSearchCAP] = useState('');

  const renderToolbar = useCallback(({ table }) => (
    <div className="search-inputs">
      <input
        type="text"
        placeholder="Sigla provincia (es. MI, RM...)"
        value={searchProvincia}
        onChange={(e) => {
          const value = e.target.value.toUpperCase();
          setSearchProvincia(value);
          table.setFilter('provincia_sigla', value || '');
        }}
        maxLength={2}
        className="search-input provincia-input"
      />
      <input
        type="text"
        placeholder="CAP (es. 20100, 00100...)"
        value={searchCAP}
        onChange={(e) => {
          const value = e.target.value;
          setSearchCAP(value);
          table.setFilter('cap', value || '');
        }}
        maxLength={5}
        className="search-input cap-input"
      />
      {(searchProvincia || searchCAP) && (
        <button
          type="button"
          onClick={() => {
            setSearchProvincia('');
            setSearchCAP('');
            table.clearFilters();
          }}
          className="btn btn-secondary"
        >
          Reset
        </button>
      )}
    </div>
  ), [searchProvincia, searchCAP]);

  const columns = [
    {
      ...comuniTableConfig.columns[0],
      render: (value) => <strong>{value}</strong>,
    },
    {
      ...comuniTableConfig.columns[1],
      render: (value) => <span className="provincia-badge">{value || '-'}</span>,
    },
    {
      ...comuniTableConfig.columns[2],
      render: (value) => value || '-',
    },
    {
      ...comuniTableConfig.columns[3],
      render: (value) => <code className="cap-badge">{value || '-'}</code>,
    },
    {
      ...comuniTableConfig.columns[4],
      render: (value) => <code className="codice-badge">{value || '-'}</code>,
    },
    {
      ...comuniTableConfig.columns[5],
      render: (value) => <code className="codice-badge">{value || '-'}</code>,
    },
    {
      ...comuniTableConfig.columns[6],
      render: (value) => (
        <span className={`badge ${value ? 'badge-success' : 'badge-secondary'}`}>
          {value ? 'Sì' : 'No'}
        </span>
      ),
    },
  ];

  return (
    <div className="comuni-list-container">
      <DataTable
        config={{
          ...comuniTableConfig,
          columns,
        }}
        toolbarContent={renderToolbar}
        options={{
          selectable: false,
          showSearch: true,
          showPagination: true,
          pageSize: 50,
        }}
        hideAddButton
        customActions={<div className="info-badge"><span>Dati di Riferimento</span></div>}
      />
    </div>
  );
}

export default ComuniList;
