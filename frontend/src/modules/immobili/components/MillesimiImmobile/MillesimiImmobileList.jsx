import { useEffect, useState, useCallback } from 'react';
import { DataTable } from '../../../../core/components';
import { tabelleMillesimaliAPI, unitaImmobiliariAPI, condominAPI } from '../../services/immobiliAPI';
import MillesimiForm from './MillesimiForm';
import './MillesimiImmobile.css';

const millesimiTableConfig = {
  endpoint: '/millesimi-immobile/',
  title: 'Gestione Millesimi Immobili',
  searchPlaceholder: 'Cerca per immobile o tabella...',
  emptyTitle: 'Nessun millesimo trovato',
  emptyMessage: 'Seleziona condominio e tabella per visualizzare i millesimi.',
  addButtonLabel: 'Aggiungi Millesimi',
  columns: [
    { field: 'immobile_id', label: 'Immobile' },
    { field: 'millesimi', label: 'Millesimi' },
    { field: 'piano', label: 'Piano' },
    { field: 'numero_occupanti', label: 'Occupanti' },
    { field: 'consumo', label: 'Consumo' },
  ],
  defaultSort: { field: 'millesimi', order: 'desc' },
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

function MillesimiFormModal({ entity, onClose, tabellaId, immobili, tabella }) {
  return (
    <MillesimiForm
      millesimo={entity}
      tabellaId={tabellaId}
      immobili={immobili}
      tabella={tabella}
      onClose={onClose}
    />
  );
}

function MillesimiImmobileList() {
  const [tabelle, setTabelle] = useState([]);
  const [immobili, setImmobili] = useState([]);
  const [condomini, setCondomini] = useState([]);
  const [filtroTabella, setFiltroTabella] = useState('');
  const [filtroCondominio, setFiltroCondominio] = useState('');

  useEffect(() => {
    const fetchSupportData = async () => {
      try {
        const [condRes, immRes] = await Promise.all([
          condominAPI.getAll(true),
          unitaImmobiliariAPI.getAll(),
        ]);
        setCondomini(condRes.data || []);
        setImmobili(immRes.data || []);
      } catch (err) {
        console.error('Errore caricamento dati:', err);
      }
    };
    fetchSupportData();
  }, []);

  const fetchTabelleByCondominio = useCallback(async (condominioId) => {
    try {
      const response = await tabelleMillesimaliAPI.getByCondominio(condominioId);
      setTabelle(response.data || []);
    } catch (err) {
      console.error('Errore caricamento tabelle:', err);
      setTabelle([]);
    }
  }, []);

  useEffect(() => {
    if (filtroCondominio) {
      fetchTabelleByCondominio(filtroCondominio);
    } else {
      setTabelle([]);
      setFiltroTabella('');
    }
  }, [filtroCondominio, fetchTabelleByCondominio]);

  const getImmobileInfo = useCallback((immobileId) => {
    const imm = immobili.find(i => i.id === immobileId);
    return imm ? `${imm.codice} - ${imm.indirizzo}` : '-';
  }, [immobili]);

  const renderToolbar = useCallback(({ table }) => (
    <div className="filters">
      <div className="form-row">
        <div className="form-group">
          <label>Condominio:</label>
          <select
            value={filtroCondominio}
            onChange={(e) => {
              const value = e.target.value;
              setFiltroCondominio(value);
              setFiltroTabella('');
              table.setFilter('tabella_id', () => false);
            }}
          >
            <option value="">Seleziona condominio</option>
            {condomini.map((cond) => (
              <option key={cond.id} value={cond.id}>
                {cond.nome}
              </option>
            ))}
          </select>
        </div>
        {filtroCondominio && (
          <div className="form-group">
            <label>Tabella Millesimale:</label>
            <select
              value={filtroTabella}
              onChange={(e) => {
                const value = e.target.value;
                setFiltroTabella(value);
                if (value) {
                  table.setFilter('tabella_id', parseInt(value, 10));
                } else {
                  table.setFilter('tabella_id', () => false);
                }
              }}
            >
              <option value="">Seleziona tabella</option>
              {tabelle.map((tab) => (
                <option key={tab.id} value={tab.id}>
                  {tab.nome}
                </option>
              ))}
            </select>
          </div>
        )}
        {filtroTabella && (
          <div className="info-box">
            Totale millesimi: {table.processedData.reduce((sum, m) => sum + m.millesimi, 0).toFixed(3)}
          </div>
        )}
      </div>
    </div>
  ), [filtroCondominio, filtroTabella, condomini, tabelle]);

  const columns = [
    {
      ...millesimiTableConfig.columns[0],
      render: (value) => getImmobileInfo(value),
    },
    {
      ...millesimiTableConfig.columns[1],
      render: (value) => <strong>{value}</strong>,
    },
    {
      ...millesimiTableConfig.columns[2],
      render: (value) => (value !== null && value !== undefined ? value : '-'),
    },
    {
      ...millesimiTableConfig.columns[3],
      render: (value) => value || '-',
    },
    {
      ...millesimiTableConfig.columns[4],
      render: (value, row) => (
        value ? `${value} ${row.unita_misura_consumo || ''}` : '-'
      ),
    },
  ];

  const tabellaId = filtroTabella ? parseInt(filtroTabella, 10) : null;

  return (
    <div className="millesimi-immobile-container">
      <DataTable
        config={{
          ...millesimiTableConfig,
          columns,
          defaultFilters: { tabella_id: () => false },
        }}
        FormComponent={(props) => (
          <MillesimiFormModal
            {...props}
            tabellaId={tabellaId}
            immobili={immobili.filter(i => i.condominio_id === parseInt(filtroCondominio, 10))}
            tabella={tabelle.find(t => t.id === tabellaId)}
          />
        )}
        toolbarContent={renderToolbar}
        addDisabled={!filtroTabella}
        options={{
          selectable: true,
          showSearch: true,
          showPagination: true,
          pageSize: 20,
        }}
      />
      {!filtroCondominio && (
        <div className="card">
          <p>Seleziona un condominio per visualizzare e gestire i millesimi.</p>
        </div>
      )}
      {filtroCondominio && !filtroTabella && (
        <div className="card">
          <p>Seleziona una tabella millesimale per visualizzare e gestire i millesimi.</p>
        </div>
      )}
    </div>
  );
}

export default MillesimiImmobileList;
