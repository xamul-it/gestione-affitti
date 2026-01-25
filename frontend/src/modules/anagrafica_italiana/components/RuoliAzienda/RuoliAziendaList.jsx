import { useEffect, useState, useCallback, useRef } from 'react';
import {
  getSoggettiAnagrafici,
  deleteRuoloAzienda,
  createRuoloAzienda,
  updateRuoloAzienda,
} from '../../services/anagraficaAPI';
import { DataTable } from '../../../../core/components';
import RuoloAziendaForm from './RuoloAziendaForm';
import './RuoliAzienda.css';

const ruoliAziendaTableConfig = {
  endpoint: '/anagrafica/ruoli-azienda/',
  title: 'Ruoli Azienda',
  searchPlaceholder: 'Cerca per persona, azienda o ruolo...',
  emptyTitle: 'Nessun ruolo trovato',
  emptyMessage: 'Non ci sono associazioni ruolo persona-azienda registrate.',
  addButtonLabel: 'Nuovo Ruolo',
  defaultParams: {
    limit: 1000,
  },
  columns: [
    { field: 'persona_fisica', label: 'Persona' },
    { field: 'persona_giuridica', label: 'Azienda' },
    { field: 'ruolo', label: 'Ruolo', filterable: true },
    { field: 'data_inizio', label: 'Data Inizio' },
    { field: 'data_fine', label: 'Data Fine' },
    { field: 'stato', label: 'Stato' },
    { field: 'ruolo_tipo_nome', label: 'Ruolo Tipo', filterable: true, visible: false },
  ],
  defaultSort: { field: 'data_inizio', order: 'desc' },
  rowActions: [
    { id: 'edit', label: 'Modifica', action: 'edit', variant: 'secondary' },
    { id: 'delete', label: 'Elimina', action: 'delete', variant: 'danger' },
  ],
};

export default function RuoliAziendaList() {
  const [soggetti, setSoggetti] = useState([]);
  const [filterPersona, setFilterPersona] = useState('');
  const [filterAzienda, setFilterAzienda] = useState('');
  const [filterAttiviOnly, setFilterAttiviOnly] = useState(true);
  const [showEditModal, setShowEditModal] = useState(false);
  const [ruoloToEdit, setRuoloToEdit] = useState(null);
  const [soggettoCorrente, setSoggettoCorrente] = useState(null);
  const tableRef = useRef(null);

  useEffect(() => {
    const loadSoggetti = async () => {
      try {
        const soggettiData = await getSoggettiAnagrafici();
        setSoggetti(soggettiData || []);
      } catch (err) {
        console.error('Errore nel caricamento dei soggetti:', err);
      }
    };
    loadSoggetti();
  }, []);

  const getSoggettoNome = useCallback((soggetto) => {
    if (!soggetto) return '(Sconosciuto)';
    if (soggetto.tipo_soggetto === 'PERSONA_FISICA') {
      return `${soggetto.nome || ''} ${soggetto.cognome || ''}`.trim();
    }
    return soggetto.ragione_sociale || '';
  }, []);

  const formatDate = useCallback((dateString) => {
    if (!dateString) return '-';
    return new Date(dateString).toLocaleDateString('it-IT');
  }, []);

  const isAttivo = useCallback((ruolo) => {
    if (!ruolo.data_fine) return true;
    const oggi = new Date().toISOString().split('T')[0];
    return ruolo.data_fine >= oggi;
  }, []);

  const handleEdit = useCallback((ruolo) => {
    const soggetto = ruolo.persona_fisica || ruolo.persona_giuridica;
    setSoggettoCorrente(soggetto);
    setRuoloToEdit(ruolo);
    setShowEditModal(true);
  }, []);

  const handleSaveRuolo = useCallback(async (dataToSave, ruoloId) => {
    if (ruoloId) {
      await updateRuoloAzienda(ruoloId, dataToSave);
    } else {
      await createRuoloAzienda(dataToSave);
    }
    setShowEditModal(false);
    setRuoloToEdit(null);
    tableRef.current?.refresh();
  }, []);

  const renderToolbar = useCallback(({ table }) => (
    <div className="filters">
      <div className="filter-group">
        <label htmlFor="filterPersona">Persona:</label>
        <select
          id="filterPersona"
          value={filterPersona}
          onChange={(e) => {
            const value = e.target.value;
            setFilterPersona(value);
            table.setFilter('persona_fisica', value ? (_, row) => row.persona_fisica?.id === parseInt(value, 10) : '');
          }}
          className="form-control"
        >
          <option value="">-- Tutte --</option>
          {soggetti.filter(s => s.tipo_soggetto === 'PERSONA_FISICA').map(p => (
            <option key={p.id} value={p.id}>{getSoggettoNome(p)}</option>
          ))}
        </select>
      </div>

      <div className="filter-group">
        <label htmlFor="filterAzienda">Azienda:</label>
        <select
          id="filterAzienda"
          value={filterAzienda}
          onChange={(e) => {
            const value = e.target.value;
            setFilterAzienda(value);
            table.setFilter('persona_giuridica', value ? (_, row) => row.persona_giuridica?.id === parseInt(value, 10) : '');
          }}
          className="form-control"
        >
          <option value="">-- Tutte --</option>
          {soggetti.filter(s => s.tipo_soggetto === 'PERSONA_GIURIDICA').map(p => (
            <option key={p.id} value={p.id}>{getSoggettoNome(p)}</option>
          ))}
        </select>
      </div>

      <div className="filter-checkbox">
        <input
          type="checkbox"
          id="filterAttivi"
          checked={filterAttiviOnly}
          onChange={(e) => {
            const checked = e.target.checked;
            setFilterAttiviOnly(checked);
            table.setFilter('data_fine', checked ? (value) => !value || value >= new Date().toISOString().split('T')[0] : '');
          }}
        />
        <label htmlFor="filterAttivi">Solo attivi</label>
      </div>
    </div>
  ), [filterPersona, filterAzienda, filterAttiviOnly, soggetti, getSoggettoNome]);

  const columns = [
    {
      ...ruoliAziendaTableConfig.columns[0],
      render: (value) => (
        <>
          {getSoggettoNome(value)}
          {value?.codice_fiscale && (
            <div className="text-muted">{value.codice_fiscale}</div>
          )}
        </>
      ),
    },
    {
      ...ruoliAziendaTableConfig.columns[1],
      render: (value) => (
        <>
          {getSoggettoNome(value)}
          {value?.codice_fiscale && (
            <div className="text-muted">{value.codice_fiscale}</div>
          )}
        </>
      ),
    },
    {
      ...ruoliAziendaTableConfig.columns[2],
      render: (value, row) => (
        <>
          <span className="ruolo-badge">
            <strong>{row.ruolo_tipo_nome || value || '(Non specificato)'}</strong>
          </span>
          {!row.ruolo_tipo_id && value && (
            <small className="text-warning" title="Ruolo personalizzato non collegato ai domini">
              {' '}⚠ Custom
            </small>
          )}
        </>
      ),
    },
    {
      ...ruoliAziendaTableConfig.columns[3],
      render: (value) => formatDate(value),
    },
    {
      ...ruoliAziendaTableConfig.columns[4],
      render: (value) => formatDate(value),
    },
    {
      ...ruoliAziendaTableConfig.columns[5],
      render: (_, row) => (
        isAttivo(row)
          ? <span className="badge badge-success">Attivo</span>
          : <span className="badge badge-secondary">Cessato</span>
      ),
    },
  ];

  return (
    <div className="ruoli-azienda-container">
      <DataTable
        config={{
          ...ruoliAziendaTableConfig,
          columns,
        }}
        toolbarContent={renderToolbar}
        onEdit={handleEdit}
        onDelete={async (ruolo) => {
          if (!window.confirm('Sei sicuro di voler eliminare questo ruolo?')) {
            return;
          }
          await deleteRuoloAzienda(ruolo.id);
          tableRef.current?.refresh();
        }}
        onTableReady={(table) => {
          tableRef.current = table;
          if (filterAttiviOnly) {
            table.setFilter('data_fine', (value) => !value || value >= new Date().toISOString().split('T')[0]);
          }
        }}
        hideAddButton
        options={{
          selectable: true,
          showSearch: true,
          showPagination: true,
          pageSize: 50,
        }}
      />

      {showEditModal && soggettoCorrente && (
        <RuoloAziendaForm
          soggettoCorrente={soggettoCorrente}
          ruoloToEdit={ruoloToEdit}
          onClose={() => {
            setShowEditModal(false);
            setRuoloToEdit(null);
          }}
          onSave={handleSaveRuolo}
        />
      )}
    </div>
  );
}
