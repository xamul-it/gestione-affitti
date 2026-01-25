import { useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { DataTable } from '../../../../core/components';
import './SoggettiAnagraficiList.css';

const soggettiTableConfig = {
  endpoint: '/anagrafica/soggetti-v2/',
  title: 'Anagrafiche',
  searchPlaceholder: 'Cerca per nome, ragione sociale, CF o email...',
  emptyTitle: 'Nessuna anagrafica trovata',
  emptyMessage: 'Non ci sono anagrafiche registrate.',
  addButtonLabel: 'Nuova Anagrafica',
  defaultParams: {
    limit: 1000,
  },
  columns: [
    { field: 'tipo_soggetto', label: 'Tipo' },
    { field: 'nome_completo', label: 'Nome / Ragione Sociale', sortable: true },
    { field: 'codice_fiscale', label: 'Codice Fiscale', filterable: true },
    { field: 'partita_iva', label: 'Partita IVA', filterable: true },
    { field: 'email', label: 'Email', filterable: true },
    { field: 'telefono', label: 'Telefono', filterable: true },
    { field: 'citta', label: 'Citta', filterable: true },
    { field: 'attivo', label: 'Stato' },
    { field: 'nome', label: 'Nome', filterable: true, visible: false },
    { field: 'cognome', label: 'Cognome', filterable: true, visible: false },
    { field: 'ragione_sociale', label: 'Ragione Sociale', filterable: true, visible: false },
  ],
  defaultSort: { field: 'nome', order: 'asc' },
  rowActions: [
    {
      id: 'view',
      label: 'Dettagli',
      action: 'view',
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

function SoggettiAnagraficiList() {
  const navigate = useNavigate();
  const [attiviSolo, setAttiviSolo] = useState(false);

  const getTipoLabel = useCallback((tipo) => (
    tipo === 'PERSONA_FISICA' ? 'Persona Fisica' : 'Persona Giuridica'
  ), []);

  const getTipoIcon = useCallback((tipo) => (
    tipo === 'PERSONA_FISICA' ? '👤' : '🏢'
  ), []);

  const getNomeCompleto = useCallback((soggetto) => {
    if (soggetto.tipo_soggetto === 'PERSONA_FISICA') {
      return `${soggetto.nome || ''} ${soggetto.cognome || ''}`.trim() || '(Non specificato)';
    }
    return soggetto.ragione_sociale || '(Non specificato)';
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
      ...soggettiTableConfig.columns[0],
      render: (value) => (
        <span className="tipo-badge" title={getTipoLabel(value)}>
          {getTipoIcon(value)}
        </span>
      ),
    },
    {
      ...soggettiTableConfig.columns[1],
      render: (_, row) => (
        <span className="soggetto-name">
          {getNomeCompleto(row)}
        </span>
      ),
    },
    {
      ...soggettiTableConfig.columns[2],
      render: (value) => value || '-',
    },
    {
      ...soggettiTableConfig.columns[3],
      render: (value) => value || '-',
    },
    {
      ...soggettiTableConfig.columns[4],
      render: (value) => value || '-',
    },
    {
      ...soggettiTableConfig.columns[5],
      render: (value, row) => value || row.cellulare || '-',
    },
    {
      ...soggettiTableConfig.columns[6],
      render: (value) => value || '-',
    },
    {
      ...soggettiTableConfig.columns[7],
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
          ...soggettiTableConfig,
          columns,
        }}
        toolbarContent={renderToolbar}
        onAdd={() => navigate('/anagrafiche/nuovo')}
        onView={(row) => navigate(`/anagrafiche/${row.id}`)}
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

export default SoggettiAnagraficiList;
