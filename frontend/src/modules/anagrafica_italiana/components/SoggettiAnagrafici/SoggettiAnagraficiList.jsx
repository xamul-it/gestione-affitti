import { useState, useCallback } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { DataTable } from '../../../../core/components';
import { renderIcon } from '../../../../components/Navigation/iconRegistry.jsx';
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
    { field: 'partita_iva', label: 'Partita IVA', filterable: true },
    { field: 'email', label: 'Email', filterable: true },
    { field: 'telefono', label: 'Telefono', filterable: true },
    { field: 'codice_fiscale', label: 'Codice Fiscale', filterable: true, visible: false },
    { field: 'citta', label: 'Citta', filterable: true, visible: false },
    { field: 'attivo', label: 'Stato', visible: false },
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

function SoggettiAnagraficiList() {
  const navigate = useNavigate();
  const [attiviSolo, setAttiviSolo] = useState(false);

  const getTipoLabel = useCallback((tipo) => (
    tipo === 'PERSONA_FISICA' ? 'Persona Fisica' : 'Persona Giuridica'
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
          {renderIcon(value === 'PERSONA_FISICA' ? 'user' : 'building', { size: 14 })}
        </span>
      ),
    },
    {
      ...soggettiTableConfig.columns[1],
      render: (_, row) => (
        <Link
          to={row.tipo_soggetto === 'PERSONA_FISICA'
            ? `/anagrafiche/persone-fisiche/${row.id}`
            : `/anagrafiche/persone-giuridiche/${row.id}`
          }
          className="table-link"
        >
          {getNomeCompleto(row)}
        </Link>
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
      render: (value, row) => value || row.cellulare || '-',
    },
    {
      ...soggettiTableConfig.columns[5],
      render: (value) => value || '-',
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
        onEdit={(row) => navigate(`/anagrafiche/${row.id}/modifica`)}
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
