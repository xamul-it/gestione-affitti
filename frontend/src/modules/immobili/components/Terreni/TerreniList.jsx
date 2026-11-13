import { useState, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { DataTable } from '../../../../core/components';
import { terreniAPI } from '../../services/immobiliAPI';
import { haAreCa } from '../../utils/superficie';
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
    {
      field: 'codice',
      label: 'Codice',
      sortable: true,
      filterable: true,
      render: (value, row) => <Link to={`/beni/${row.id}`} className="table-link">{value}</Link>,
    },
    { field: 'nome', label: 'Nome', sortable: true, filterable: true, render: (value) => value || '-' },
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
      field: 'superficie_mq',
      label: 'Superficie',
      render: (value) => haAreCa(value),
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
  defaultSort: { field: 'codice', order: 'asc' },
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
          await terreniAPI.update(row.id, { attivo: !row.attivo });
          table.refresh();
        } catch (err) {
          console.error('Errore aggiornamento terreno:', err);
        }
      },
    },
    {
      // DataTable asks for confirmation (ConfirmDialog) and calls DELETE /terreni/{id}.
      id: 'delete',
      label: 'Elimina',
      action: 'delete',
      variant: 'danger',
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
