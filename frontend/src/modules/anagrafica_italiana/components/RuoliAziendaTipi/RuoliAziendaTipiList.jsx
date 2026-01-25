import { useState, useCallback, useRef } from 'react';
import { DataTable } from '../../../../core/components';
import {
  deleteRuoloAziendaTipo,
  mergeRuoliAziendaTipi,
} from '../../services/anagraficaAPI';
import RuoloAziendaTipoForm from './RuoloAziendaTipoForm';
import { renderIcon } from '../../../../components/Navigation/iconRegistry.jsx';
import './RuoliAziendaTipi.css';

const ruoliAziendaTipiTableConfig = {
  endpoint: '/anagrafica/domini/ruoli-azienda-tipi/',
  title: 'Ruoli Azienda',
  searchPlaceholder: 'Cerca per nome...',
  emptyTitle: 'Nessun ruolo trovato',
  emptyMessage: 'Non ci sono ruoli azienda registrati.',
  addButtonLabel: 'Nuovo Ruolo',
  defaultParams: {
    attivi_solo: false,
  },
  columns: [
    { field: 'nome', label: 'Nome', filterable: true, sortable: true },
    { field: 'descrizione', label: 'Descrizione' },
    { field: 'attivo', label: 'Attivo' },
    { field: 'created_at', label: 'Creato' },
  ],
  defaultSort: { field: 'nome', order: 'asc' },
  rowActions: [
    {
      id: 'edit',
      label: 'Modifica',
      action: 'edit',
      variant: 'secondary',
      icon: renderIcon('pencil', { size: 14 }),
    },
    {
      id: 'delete',
      label: 'Elimina',
      action: 'delete',
      variant: 'danger',
      icon: renderIcon('trash', { size: 14 }),
    },
  ],
};

function RuoloAziendaTipoFormModal({ entity, onClose }) {
  return (
    <RuoloAziendaTipoForm
      ruolo={entity}
      onClose={onClose}
    />
  );
}

function RuoliAziendaTipiList() {
  const [ruoli, setRuoli] = useState([]);
  const tableRef = useRef(null);
  const [showOnlyActive, setShowOnlyActive] = useState(false);
  const [showMerge, setShowMerge] = useState(false);
  const [mergeSource, setMergeSource] = useState('');
  const [mergeTarget, setMergeTarget] = useState('');

  const handleMerge = useCallback(async () => {
    if (!mergeSource || !mergeTarget) {
      alert('Seleziona sia il ruolo di origine che quello di destinazione');
      return;
    }

    if (mergeSource === mergeTarget) {
      alert('I ruoli devono essere diversi');
      return;
    }

    const sourceRuolo = ruoli.find(r => r.id === parseInt(mergeSource, 10));
    const targetRuolo = ruoli.find(r => r.id === parseInt(mergeTarget, 10));

    if (!sourceRuolo || !targetRuolo) {
      alert('Ruoli non validi');
      return;
    }

    if (window.confirm(
      `Vuoi unificare "${sourceRuolo.nome}" in "${targetRuolo.nome}"?\n\n` +
      `Tutte le associazioni che usano "${sourceRuolo.nome}" verranno spostate su "${targetRuolo.nome}", ` +
      `poi "${sourceRuolo.nome}" verrà eliminato.\n\n` +
      `Questa operazione non può essere annullata.`
    )) {
      try {
        const result = await mergeRuoliAziendaTipi(parseInt(mergeSource, 10), parseInt(mergeTarget, 10));
        alert(
          `Merge completato con successo!\n\n` +
          `"${result.source_nome}" è stato unificato in "${result.target_nome}".\n` +
          `Associazioni aggiornate: ${result.associazioni_aggiornate}`
        );
        setShowMerge(false);
        setMergeSource('');
        setMergeTarget('');
        tableRef.current?.refresh();
      } catch (err) {
        if (err.response?.data?.detail) {
          alert(`Errore nel merge: ${err.response.data.detail}`);
        } else {
          alert('Errore nel merge dei ruoli');
        }
        console.error(err);
      }
    }
  }, [mergeSource, mergeTarget, ruoli]);

  const renderToolbar = useCallback(({ table }) => (
    <div className="filters">
      <label className="filter-checkbox">
        <input
          type="checkbox"
          checked={showOnlyActive}
          onChange={(e) => {
            const checked = e.target.checked;
            setShowOnlyActive(checked);
            table.setFilter('attivo', checked ? true : '');
          }}
        />
        Mostra solo attivi
      </label>
      <button onClick={() => setShowMerge(!showMerge)} className="btn btn-secondary">
        {showMerge ? 'Annulla Merge' : 'Unifica Ruoli'}
      </button>
    </div>
  ), [showOnlyActive, showMerge]);

  const columns = [
    {
      ...ruoliAziendaTipiTableConfig.columns[0],
      render: (value) => <strong>{value}</strong>,
    },
    {
      ...ruoliAziendaTipiTableConfig.columns[1],
      render: (value) => value || '-',
    },
    {
      ...ruoliAziendaTipiTableConfig.columns[2],
      render: (value) => (
        <span className={`badge ${value ? 'badge-success' : 'badge-secondary'}`}>
          {value ? 'Sì' : 'No'}
        </span>
      ),
    },
    {
      ...ruoliAziendaTipiTableConfig.columns[3],
      render: (value) => value ? new Date(value).toLocaleDateString('it-IT') : '-',
    },
  ];

  return (
    <div className="container">
      {showMerge && (
        <div className="merge-panel">
          <h3>Unifica Ruoli Duplicati</h3>
          <p>Seleziona due ruoli per unificarli. Il ruolo di origine verrà eliminato e tutte le sue associazioni verranno spostate sul ruolo di destinazione.</p>
          <div className="merge-selects">
            <div className="form-group">
              <label>Ruolo di Origine (verrà eliminato):</label>
              <select
                value={mergeSource}
                onChange={(e) => setMergeSource(e.target.value)}
                className="form-control"
              >
                <option value="">-- Seleziona --</option>
                {ruoli.map(ruolo => (
                  <option key={ruolo.id} value={ruolo.id}>
                    {ruolo.nome} {!ruolo.attivo && '(inattivo)'}
                  </option>
                ))}
              </select>
            </div>
            <div className="merge-arrow">→</div>
            <div className="form-group">
              <label>Ruolo di Destinazione (sarà mantenuto):</label>
              <select
                value={mergeTarget}
                onChange={(e) => setMergeTarget(e.target.value)}
                className="form-control"
              >
                <option value="">-- Seleziona --</option>
                {ruoli.map(ruolo => (
                  <option key={ruolo.id} value={ruolo.id}>
                    {ruolo.nome} {!ruolo.attivo && '(inattivo)'}
                  </option>
                ))}
              </select>
            </div>
          </div>
          <button
            onClick={handleMerge}
            className="btn btn-primary"
            disabled={!mergeSource || !mergeTarget}
          >
            Unifica Ruoli
          </button>
        </div>
      )}

      <DataTable
        config={{
          ...ruoliAziendaTipiTableConfig,
          columns,
        }}
        FormComponent={RuoloAziendaTipoFormModal}
        toolbarContent={renderToolbar}
        onDelete={async (ruolo) => {
          if (!window.confirm(
            `Sei sicuro di voler eliminare il ruolo "${ruolo.nome}"?\n\n` +
            'ATTENZIONE: Non è possibile eliminare un ruolo se è utilizzato in associazioni esistenti. ' +
            'Usa la funzione di merge per unificare ruoli simili prima di eliminare.'
          )) {
            return;
          }
          await deleteRuoloAziendaTipo(ruolo.id);
          tableRef.current?.refresh();
        }}
        tableOptions={{
          onDataChange: (data) => {
            setRuoli(Array.isArray(data) ? data : []);
          },
        }}
        onTableReady={(table) => {
          tableRef.current = table;
        }}
        options={{
          selectable: true,
          showSearch: true,
          showPagination: true,
          pageSize: 50,
        }}
      />
    </div>
  );
}

export default RuoliAziendaTipiList;
