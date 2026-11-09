import { useMemo } from 'react';
import { DataTable } from '../../../../core/components';
import { useTableConfig } from '../../../../core/hooks';
import './DominiList.css';

// Fields owned by the module manifests (document_type_sync), shown in words.
const MANIFEST_RENDERERS = {
  modulo: (value) => value || '—',
  regime: (value) => (value === 'SOSTITUTIVO' ? 'Sostituisce il precedente' : 'Si accumulano'),
  scadenza: (value) => {
    if (!value) return '—';
    if (value.manuale) return 'Manuale';
    if (value.mesi) return value.mesi % 12 === 0 ? `${value.mesi / 12} anni` : `${value.mesi} mesi`;
    return '—';
  },
  form: (value) => (value ? 'Sì' : 'No'),
};

function TipiDocumentoList() {
  const moduleName = 'anagrafica_italiana';
  const entityName = 'TipoDocumento';

  const {
    columns: managedColumns,
    effectiveConfig,
  } = useTableConfig({ moduleName, entityName });

  const columns = useMemo(() => {
    if (!managedColumns || managedColumns.length === 0) {
      return [
        { field: 'codice', label: 'Codice', sortable: true, filterable: true },
        { field: 'nome', label: 'Nome', sortable: true, filterable: true },
        { field: 'categoria', label: 'Categoria', render: (value) => value || '-' },
        { field: 'modulo', label: 'Modulo', render: MANIFEST_RENDERERS.modulo },
        { field: 'regime', label: 'Nuovo documento', render: MANIFEST_RENDERERS.regime },
        { field: 'scadenza', label: 'Scadenza', render: MANIFEST_RENDERERS.scadenza },
        { field: 'form', label: 'Form dedicato', render: MANIFEST_RENDERERS.form },
        { field: 'parsing_service', label: 'Parsing Service', render: (value) => value || '-', visible: false },
        { field: 'parsing_callback_url', label: 'Callback URL', render: (value) => value || '-', visible: false },
        {
          field: 'parsing_config',
          label: 'Parsing Config',
          render: (value) => (value ? JSON.stringify(value) : '-'),
          visible: false,
        },
        {
          field: 'richiede_scadenza',
          label: 'Scadenza',
          render: (value) => (
            <span className={`badge ${value ? 'badge-success' : 'badge-secondary'}`}>
              {value ? 'Sì' : 'No'}
            </span>
          ),
        },
        {
          field: 'attivo',
          label: 'Attivo',
          render: (value) => (
            <span className={`badge ${value ? 'badge-success' : 'badge-secondary'}`}>
              {value ? 'Sì' : 'No'}
            </span>
          ),
        },
      ];
    }

    return managedColumns.map((column) => {
      if (MANIFEST_RENDERERS[column.field]) {
        return { ...column, render: MANIFEST_RENDERERS[column.field] };
      }
      if (column.field === 'richiede_scadenza') {
        return {
          ...column,
          render: (value) => (
            <span className={`badge ${value ? 'badge-success' : 'badge-secondary'}`}>
              {value ? 'Sì' : 'No'}
            </span>
          ),
        };
      }
      if (column.field === 'attivo') {
        return {
          ...column,
          render: (value) => (
            <span className={`badge ${value ? 'badge-success' : 'badge-secondary'}`}>
              {value ? 'Sì' : 'No'}
            </span>
          ),
        };
      }
      if (column.field === 'parsing_config') {
        return {
          ...column,
          render: (value) => (value ? JSON.stringify(value) : '-'),
        };
      }
      if (column.field === 'parsing_service' || column.field === 'parsing_callback_url') {
        return {
          ...column,
          render: (value) => value || '-',
        };
      }
      if (column.field === 'categoria') {
        return {
          ...column,
          render: (value) => value || '-',
        };
      }
      return column;
    });
  }, [managedColumns]);

  return (
    <div className="domini-list-container">
      <DataTable
        config={{
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
          moduleName,
          entityName,
          columns,
          defaultSort: effectiveConfig?.sortField
            ? { field: effectiveConfig.sortField, order: effectiveConfig.sortOrder || 'asc' }
            : { field: 'nome', order: 'asc' },
        }}
        options={{
          selectable: false,
          showSearch: true,
          showPagination: true,
          showColumnSelector: true,
          pageSize: 50,
        }}
        hideAddButton
        customActions={<span className="domini-badge">Dati di dominio</span>}
      />
    </div>
  );
}

export default TipiDocumentoList;
