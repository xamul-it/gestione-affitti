import { DataTable } from '../../../../core/components';
import './DominiList.css';

const tipiDocumentoTableConfig = {
  endpoint: '/anagrafica/domini/tipi-documento/',
  title: 'Tipi Documento',
  searchPlaceholder: 'Cerca per codice, nome o categoria...',
  emptyTitle: 'Nessun tipo documento disponibile',
  emptyMessage: 'Non ci sono tipi documento registrati.',
  addButtonLabel: 'Nuovo Tipo Documento',
  defaultParams: {
    attivi_solo: false,
    limit: 200,
  },
  columns: [
    { field: 'codice', label: 'Codice', sortable: true, filterable: true },
    { field: 'nome', label: 'Nome', sortable: true, filterable: true },
    { field: 'categoria', label: 'Categoria', render: (value) => value || '-' },
    {
      field: 'richiede_scadenza',
      label: 'Scadenza',
      render: (value) => (value ? 'Si' : 'No'),
    },
    {
      field: 'attivo',
      label: 'Attivo',
      render: (value) => (value ? 'Si' : 'No'),
    },
  ],
  defaultSort: { field: 'nome', order: 'asc' },
};

function TipiDocumentoList() {
  return (
    <div className="domini-list-container">
      <DataTable
        config={tipiDocumentoTableConfig}
        options={{
          selectable: false,
          showSearch: true,
          showPagination: true,
          pageSize: 50,
        }}
        hideAddButton
        customActions={<span className="domini-badge">Dati di dominio</span>}
      />
    </div>
  );
}

export default TipiDocumentoList;
