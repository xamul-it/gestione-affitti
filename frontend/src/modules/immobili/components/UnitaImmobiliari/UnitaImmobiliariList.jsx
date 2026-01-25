import { DataTable } from '../../../../core/components';
import UnitaImmobiliareForm from './UnitaImmobiliareForm';
import ImportButton from '../../../../components/Platform/ImportButton';
import './UnitaImmobiliari.css';

const unitaTableConfig = {
  endpoint: '/unita-immobiliari/',
  title: 'Gestione Unita Immobiliari',
  searchPlaceholder: 'Cerca per codice, indirizzo o citta...',
  emptyTitle: 'Nessuna unita immobiliare trovata',
  emptyMessage: 'Non ci sono unita immobiliari. Clicca su "Nuova Unita Immobiliare" per iniziare.',
  addButtonLabel: 'Nuova Unita Immobiliare',
  columns: [
    { field: 'codice', label: 'Codice', sortable: true, filterable: true },
    { field: 'tipo', label: 'Tipo', sortable: true, filterable: true },
    {
      field: 'categoria_catastale.codice',
      label: 'Categoria Catastale',
      render: (value) => value || '-',
    },
    { field: 'indirizzo', label: 'Indirizzo', sortable: true, filterable: true },
    { field: 'citta', label: 'Citta', sortable: true, filterable: true },
    {
      field: 'superficie_mq',
      label: 'Superficie',
      render: (value) => (value ? `${value} mq` : '-'),
    },
    {
      field: 'locali',
      label: 'Locali',
      render: (value) => value || '-',
    },
  ],
  defaultSort: { field: 'codice', order: 'asc' },
  rowActions: [
    {
      id: 'view',
      label: 'Dettagli',
      to: '/unita-immobiliari/:id',
      variant: 'primary',
    },
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

function UnitaImmobiliareFormModal({ entity, onClose }) {
  return (
    <UnitaImmobiliareForm
      unitaImmobiliare={entity}
      onClose={onClose}
    />
  );
}

function UnitaImmobiliariList() {
  return (
    <div className="unita-immobiliari-container">
      <DataTable
        config={unitaTableConfig}
        FormComponent={UnitaImmobiliareFormModal}
        options={{
          selectable: true,
          showSearch: true,
          showPagination: true,
          pageSize: 20,
        }}
        customActions={({ table }) => (
          <ImportButton
            moduleName="affitti_lungo"
            entityName="UnitaImmobiliare"
            entityLabel="Unita Immobiliari"
            onImportComplete={() => table.refresh()}
          />
        )}
      />
    </div>
  );
}

export default UnitaImmobiliariList;
