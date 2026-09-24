import { DataTable } from '../../../../core/components';
import ProprietarioForm from './ProprietarioForm';
import './Proprietari.css';

const proprietariTableConfig = {
  endpoint: '/proprietari/',
  title: 'Gestione Proprietari',
  searchPlaceholder: 'Cerca per note...',
  emptyTitle: 'Nessun proprietario trovato',
  emptyMessage: 'Non ci sono proprietari registrati. Clicca su "Nuovo Proprietario" per iniziare.',
  addButtonLabel: 'Nuovo Proprietario',
  columns: [
    { field: 'soggetto_id', label: 'ID Soggetto', width: 120 },
    { field: 'note_proprietario', label: 'Note', filterable: true, render: (value) => value || '-' },
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
      confirmMessage: 'Eliminare questo proprietario? Verranno rimossi anche i suoi diritti sulle unità immobiliari.',
    },
  ],
};

function ProprietarioFormModal({ entity, onClose }) {
  return <ProprietarioForm proprietario={entity} onClose={onClose} />;
}

function ProprietariList() {
  return (
    <div className="proprietari-container">
      <DataTable
        config={proprietariTableConfig}
        FormComponent={ProprietarioFormModal}
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

export default ProprietariList;
