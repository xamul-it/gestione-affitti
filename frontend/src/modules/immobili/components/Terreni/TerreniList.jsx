import { useState, useCallback } from 'react';
import { DataTable } from '../../../../core/components';
import { terreniAPI } from '../../services/immobiliAPI';
import TerrenoForm from './TerrenoForm';
import './Terreni.css';

// Mapping tipologia to display label
const TIPOLOGIA_LABELS = {
  AGR: 'Agricolo',
  EDI: 'Edificabile',
  BOS: 'Bosco/Forestale',
  IND: 'Industriale',
  ALT: 'Altro',
};

const terreniTableConfig = {
  endpoint: '/terreni/',
  title: 'Gestione Terreni',
  searchPlaceholder: 'Cerca per codice, nome o comune...',
  emptyTitle: 'Nessun terreno trovato',
  emptyMessage: 'Non ci sono terreni registrati. Clicca su "Nuovo Terreno" per iniziare.',
  addButtonLabel: 'Nuovo Terreno',
  columns: [
    { field: 'codice', label: 'Codice', sortable: true, filterable: true },
    { field: 'nome', label: 'Nome', sortable: true, filterable: true },
    {
      field: 'tipologia',
      label: 'Tipologia',
      render: (value) => {
        const tipologiaCode = typeof value === 'string' ? value : value?.codice;
        const tipologiaLabel = typeof value === 'string' ? value : value?.nome;
        const badgeKey = tipologiaCode ? tipologiaCode.toLowerCase() : 'alt';
        return (
          <span className={`badge tipologia-${badgeKey}`}>
            {TIPOLOGIA_LABELS[tipologiaCode] || tipologiaLabel || '-'}
          </span>
        );
      },
    },
    { field: 'comune', label: 'Comune', sortable: true, filterable: true },
    { field: 'provincia', label: 'Provincia', sortable: true, filterable: true },
    {
      field: 'superficie',
      label: 'Superficie',
      render: (value, row) => {
        if (!value) return '-';
        const unita = row.unita_misura_superficie || 'mq';
        return `${value.toLocaleString('it-IT')} ${unita}`;
      },
    },
    {
      field: 'foglio',
      label: 'Foglio/Particella',
      render: (value, row) => (value && row.particella ? `${value}/${row.particella}` : '-'),
    },
    {
      field: 'attivo',
      label: 'Stato',
      render: (value) => (
        <span className={`badge ${value ? 'active' : 'inactive'}`}>
          {value ? 'Attivo' : 'Inattivo'}
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
      id: 'toggle',
      label: (row) => (row.attivo ? 'Disattiva' : 'Ripristina'),
      variant: (row) => (row.attivo ? 'danger' : 'success'),
      onClick: async (row, table) => {
        try {
          if (row.attivo) {
            const confirm = window.confirm('Sei sicuro di voler disattivare questo terreno?');
            if (!confirm) return;
            await terreniAPI.delete(row.id);
          } else {
            await terreniAPI.restore(row.id);
          }
          table.refresh();
        } catch (err) {
          console.error('Errore aggiornamento terreno:', err);
        }
      },
    },
  ],
};

function TerrenoFormModal({ entity, onClose }) {
  return (
    <TerrenoForm
      terreno={entity}
      onClose={onClose}
    />
  );
}

function TerreniList() {
  const [filtroTipologia, setFiltroTipologia] = useState('');
  const [filtroAttivi, setFiltroAttivi] = useState(false);

  const renderToolbar = useCallback(({ table }) => (
    <div className="terreni-filters">
      <div className="filter-group">
        <label>Tipologia:</label>
        <select
          value={filtroTipologia}
          onChange={(e) => {
            const value = e.target.value;
            setFiltroTipologia(value);
            table.setFilter('tipologia', value || '');
          }}
        >
          <option value="">Tutte</option>
          <option value="AGR">Agricolo</option>
          <option value="EDI">Edificabile</option>
          <option value="BOS">Bosco/Forestale</option>
          <option value="IND">Industriale</option>
          <option value="ALT">Altro</option>
        </select>
      </div>
      <label className="checkbox-label">
        <input
          type="checkbox"
          checked={filtroAttivi}
          onChange={(e) => {
            const checked = e.target.checked;
            setFiltroAttivi(checked);
            table.setFilter('attivo', checked ? true : '');
          }}
        />
        Solo attivi
      </label>
    </div>
  ), [filtroTipologia, filtroAttivi]);

  return (
    <div className="terreni-container">
      <DataTable
        config={terreniTableConfig}
        FormComponent={TerrenoFormModal}
        toolbarContent={renderToolbar}
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

export default TerreniList;
