import { DataTable } from '../../../../core/components';
import CondominioForm from './CondominioForm';
import './Condomini.css';

const condominiTableConfig = {
  endpoint: '/condomini/',
  title: 'Gestione Condomini',
  searchPlaceholder: 'Cerca per codice, nome o citta...',
  emptyTitle: 'Nessun condominio trovato',
  emptyMessage: 'Non ci sono condomini registrati. Clicca su "Nuovo Condominio" per iniziare.',
  addButtonLabel: 'Nuovo Condominio',
  columns: [
    { field: 'codice', label: 'Codice', sortable: true, filterable: true },
    { field: 'nome', label: 'Nome', sortable: true, filterable: true },
    { field: 'indirizzo', label: 'Indirizzo', sortable: true, filterable: true },
    { field: 'citta', label: 'Citta', sortable: true, filterable: true },
    {
      field: 'amministratore_nome',
      label: 'Amministratore',
      render: (value) => value || '-',
    },
    {
      field: 'attivo',
      label: 'Stato',
      render: (value) => (
        <span className={`badge ${value ? 'success' : 'inactive'}`}>
          {value ? 'Attivo' : 'Non attivo'}
        </span>
      ),
    },
  ],
  defaultSort: { field: 'nome', order: 'asc' },
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

function CondominioFormModal({ entity, onClose }) {
  return (
    <CondominioForm
      condominio={entity}
      onClose={onClose}
    />
  );
}

function CondominList() {
  return (
    <div className="condomini-container">
      <DataTable
        config={condominiTableConfig}
        FormComponent={CondominioFormModal}
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

export default CondominList;
