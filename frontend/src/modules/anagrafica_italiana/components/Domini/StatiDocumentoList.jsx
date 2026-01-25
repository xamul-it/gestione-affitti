import { DataTable } from '../../../../core/components';
import './DominiList.css';

const statiDocumentoTableConfig = {
  endpoint: '/anagrafica/domini/stati-documento/',
  title: 'Stati Documento',
  searchPlaceholder: 'Cerca per codice o nome...',
  emptyTitle: 'Nessuno stato documento disponibile',
  emptyMessage: 'Non ci sono stati documento registrati.',
  addButtonLabel: 'Nuovo Stato Documento',
  defaultParams: {
    limit: 200,
  },
  columns: [
    { field: 'codice', label: 'Codice', sortable: true, filterable: true },
    { field: 'nome', label: 'Nome', sortable: true, filterable: true },
    { field: 'descrizione', label: 'Descrizione', render: (value) => value || '-' },
    {
      field: 'attivo',
      label: 'Attivo',
      render: (value) => (value ? 'Si' : 'No'),
    },
  ],
  defaultSort: { field: 'nome', order: 'asc' },
};

function StatiDocumentoList() {
  return (
    <div className="domini-list-container">
      <DataTable
        config={statiDocumentoTableConfig}
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

export default StatiDocumentoList;
