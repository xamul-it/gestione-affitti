import { DataTable } from '../../../../core/components';
import ConduttoreForm from './ConduttoreForm';
import './Conduttori.css';

const conduttoriTableConfig = {
  endpoint: '/conduttori/',
  title: 'Gestione Conduttori',
  searchPlaceholder: 'Cerca per note...',
  emptyTitle: 'Nessun conduttore trovato',
  emptyMessage: 'Non ci sono conduttori registrati. Clicca su "Nuovo Conduttore" per iniziare.',
  addButtonLabel: 'Nuovo Conduttore',
  columns: [
    { field: 'soggetto_id', label: 'ID Soggetto', width: 120 },
    { field: 'note', label: 'Note', render: (value) => value || '-' },
    {
      field: 'created_at',
      label: 'Registrato il',
      render: (value) => (value ? new Date(value).toLocaleDateString('it-IT') : '-'),
    },
  ],
  defaultSort: { field: 'created_at', order: 'desc' },
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
      confirmMessage: 'Eliminare questo conduttore? Verranno rimosse anche le sue assegnazioni alle unità immobiliari.',
    },
  ],
};

function ConduttoreFormModal({ entity, onClose }) {
  return <ConduttoreForm conduttore={entity} onClose={onClose} />;
}

function ConduttoriList() {
  return (
    <div className="conduttori-container">
      <DataTable
        config={conduttoriTableConfig}
        FormComponent={ConduttoreFormModal}
        options={{
          selectable: false,
          showSearch: true,
          showPagination: true,
          pageSize: 20,
        }}
      />
    </div>
  );
}

export default ConduttoriList;
