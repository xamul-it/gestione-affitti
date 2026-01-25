/**
 * ElementiEsempioList - Main List Component
 *
 * Demonstrates the use of cross-cutting platform components:
 * - DataTable with configurable columns
 * - Column selector with drag-and-drop reordering
 * - Import/Export functionality
 * - Bulk actions (multi-select)
 * - Search and filtering
 */
import { useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { DataTable } from '../../../../core/components/DataTable';
import ImportButton from '../../../../components/Platform/ImportButton';
import ExportButton from '../../../../components/Platform/ExportButton';
import ElementoEsempioForm from './ElementoEsempioForm';
import './ElementiEsempioList.css';

// Stati disponibili per il badge
const STATO_BADGE_MAP = {
  'bozza': { label: 'Bozza', variant: 'secondary' },
  'attivo': { label: 'Attivo', variant: 'success' },
  'completato': { label: 'Completato', variant: 'info' },
  'annullato': { label: 'Annullato', variant: 'danger' },
};

function ElementiEsempioList() {
  const navigate = useNavigate();
  const [refreshKey, setRefreshKey] = useState(0);
  const [showForm, setShowForm] = useState(false);
  const [editingElement, setEditingElement] = useState(null);

  // DataTable configuration
  const config = {
    endpoint: '/esempio/elementi/',
    title: 'Elementi di Esempio',
    moduleName: 'esempio_componenti',  // For table config persistence
    entityName: 'ElementoEsempio',      // For table config persistence

    columns: [
      {
        field: 'codice',
        label: 'Codice',
        sortable: true,
        required: true,  // Cannot be hidden
      },
      {
        field: 'titolo',
        label: 'Titolo',
        sortable: true,
        required: true,
      },
      {
        field: 'categoria_nome',
        label: 'Categoria',
        sortable: false,
        render: (value, row) => (
          value ? (
            <span
              className="categoria-badge"
              style={{ borderLeftColor: row.categoria_colore || '#ccc' }}
            >
              {value}
            </span>
          ) : '-'
        ),
      },
      {
        field: 'priorita_nome',
        label: 'Priorità',
        sortable: false,
        render: (value, row) => (
          value ? (
            <span
              className="priorita-badge"
              style={{ backgroundColor: row.priorita_colore || '#ccc' }}
            >
              {value}
            </span>
          ) : '-'
        ),
      },
      {
        field: 'stato',
        label: 'Stato',
        type: 'badge',
        badgeMap: STATO_BADGE_MAP,
        sortable: true,
      },
      {
        field: 'quantita',
        label: 'Quantità',
        type: 'number',
        align: 'right',
        sortable: true,
      },
      {
        field: 'importo',
        label: 'Importo',
        type: 'currency',
        align: 'right',
        sortable: true,
      },
      {
        field: 'data_inizio',
        label: 'Data Inizio',
        type: 'date',
        format: 'DD/MM/YYYY',
        sortable: true,
        visible: false,  // Hidden by default
      },
      {
        field: 'data_fine',
        label: 'Data Fine',
        type: 'date',
        format: 'DD/MM/YYYY',
        sortable: true,
        visible: false,  // Hidden by default
      },
      {
        field: 'attivo',
        label: 'Attivo',
        type: 'boolean',
        sortable: true,
      },
      {
        field: 'created_at',
        label: 'Creato il',
        type: 'datetime',
        format: 'DD/MM/YYYY HH:mm',
        sortable: true,
        visible: false,  // Hidden by default
      },
    ],

    defaultSort: {
      field: 'created_at',
      order: 'desc',
    },

    rowActions: [
      { id: 'view', action: 'view', icon: '👁️', label: 'Visualizza' },
      { id: 'edit', action: 'edit', icon: '✏️', label: 'Modifica' },
      { id: 'delete', action: 'delete', icon: '🗑️', label: 'Elimina' },
    ],

    bulkActions: [
      { id: 'bulkDelete', action: 'bulkDelete', label: 'Elimina selezionati' },
    ],

    searchPlaceholder: 'Cerca per codice, titolo, descrizione...',
    addButtonLabel: 'Nuovo Elemento',
  };

  // Handlers
  const handleRefresh = useCallback(() => {
    setRefreshKey(k => k + 1);
  }, []);

  const handleAdd = useCallback(() => {
    setEditingElement(null);
    setShowForm(true);
  }, []);

  const handleView = useCallback((entity) => {
    // Could navigate to detail page or show a modal
    console.log('View:', entity);
    setEditingElement(entity);
    setShowForm(true);
  }, []);

  const handleEdit = useCallback((entity) => {
    setEditingElement(entity);
    setShowForm(true);
  }, []);

  const handleFormClose = useCallback(() => {
    setShowForm(false);
    setEditingElement(null);
  }, []);

  const handleFormSave = useCallback(() => {
    setShowForm(false);
    setEditingElement(null);
    handleRefresh();
  }, [handleRefresh]);

  return (
    <div className="elementi-esempio-list">
      <div className="page-header">
        <h1>Elementi di Esempio</h1>
        <p className="page-description">
          Questa pagina dimostra l'uso dei componenti trasversali della piattaforma:
          DataTable configurabile, Import/Export, selezione colonne.
        </p>
      </div>

      <DataTable
        key={refreshKey}
        config={config}
        options={{
          selectable: true,
          showSearch: true,
          showPagination: true,
          showColumnSelector: true,
          pageSize: 20,
        }}
        customActions={
          <>
            <ImportButton
              moduleName="esempio_componenti"
              entityName="ElementoEsempio"
              entityLabel="Elementi"
              onImportComplete={handleRefresh}
            />
            <ExportButton
              moduleName="esempio_componenti"
              entityName="ElementoEsempio"
              entityLabel="Elementi"
            />
          </>
        }
        onAdd={handleAdd}
        onView={handleView}
        onEdit={handleEdit}
        onRefresh={handleRefresh}
      />

      {showForm && (
        <ElementoEsempioForm
          elemento={editingElement}
          onClose={handleFormClose}
          onSave={handleFormSave}
        />
      )}
    </div>
  );
}

export default ElementiEsempioList;
