import { useEffect, useState, useCallback } from 'react';
import { DataTable } from '../../../../core/components';
import { condominAPI } from '../../services/immobiliAPI';
import TabellaMillesimaleForm from './TabellaMillesimaleForm';
import './TabelleMillesimali.css';

const tabelleMillesimaliTableConfig = {
  endpoint: '/tabelle-millesimali/',
  title: 'Gestione Tabelle Millesimali',
  searchPlaceholder: 'Cerca per codice o nome...',
  emptyTitle: 'Nessuna tabella millesimale trovata',
  emptyMessage: 'Non ci sono tabelle millesimali registrate.',
  addButtonLabel: 'Nuova Tabella',
  columns: [
    { field: 'codice', label: 'Codice', sortable: true, filterable: true },
    { field: 'nome', label: 'Nome', sortable: true, filterable: true },
    { field: 'condominio_id', label: 'Condominio' },
    { field: 'tipo_ripartizione', label: 'Tipo Ripartizione' },
    { field: 'percentuale_millesimi', label: '% Millesimi' },
    { field: 'percentuale_consumo', label: '% Consumo' },
    { field: 'percentuale_occupanti', label: '% Occupanti' },
    { field: 'attiva', label: 'Stato' },
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
      id: 'delete',
      label: 'Elimina',
      action: 'delete',
      variant: 'danger',
    },
  ],
};

function TabellaMillesimaleFormModal({ entity, onClose, condomini }) {
  return (
    <TabellaMillesimaleForm
      tabella={entity}
      condomini={condomini}
      onClose={onClose}
    />
  );
}

function TabelleMillesimaliList() {
  const [condomini, setCondomini] = useState([]);
  const [filtroCondominio, setFiltroCondominio] = useState('');

  useEffect(() => {
    const fetchCondomini = async () => {
      try {
        const response = await condominAPI.getAll(true);
        setCondomini(response.data || []);
      } catch (err) {
        console.error('Errore caricamento condomini:', err);
      }
    };
    fetchCondomini();
  }, []);

  const getTipoRipartizioneLabel = useCallback((tipo) => {
    const normalized = tipo ? tipo.toLowerCase() : '';
    const labels = {
      millesimi: 'Millesimi',
      millesimi_consumo: 'Millesimi + Consumo',
      occupanti: 'Occupanti',
      millesimi_piano: 'Millesimi + Piano',
      personalizzata: 'Personalizzata',
    };
    return labels[normalized] || tipo;
  }, []);

  const renderToolbar = useCallback(({ table }) => (
    <div className="filters">
      <div className="form-group">
        <label>Filtra per Condominio:</label>
        <select
          value={filtroCondominio}
          onChange={(e) => {
            const value = e.target.value;
            setFiltroCondominio(value);
            table.setFilter('condominio_id', value || '');
          }}
        >
          <option value="">Tutti i condomini</option>
          {condomini.map((cond) => (
            <option key={cond.id} value={cond.id}>
              {cond.nome}
            </option>
          ))}
        </select>
      </div>
    </div>
  ), [filtroCondominio, condomini]);

  const columns = [
    tabelleMillesimaliTableConfig.columns[0],
    tabelleMillesimaliTableConfig.columns[1],
    {
      ...tabelleMillesimaliTableConfig.columns[2],
      render: (value) => condomini.find(c => c.id === value)?.nome || '-',
    },
    {
      ...tabelleMillesimaliTableConfig.columns[3],
      render: (value) => getTipoRipartizioneLabel(value),
    },
    {
      ...tabelleMillesimaliTableConfig.columns[4],
      render: (value) => `${value}%`,
    },
    {
      ...tabelleMillesimaliTableConfig.columns[5],
      render: (value) => `${value}%`,
    },
    {
      ...tabelleMillesimaliTableConfig.columns[6],
      render: (value) => `${value}%`,
    },
    {
      ...tabelleMillesimaliTableConfig.columns[7],
      render: (value) => (
        <span className={`badge ${value ? 'success' : 'inactive'}`}>
          {value ? 'Attiva' : 'Non attiva'}
        </span>
      ),
    },
  ];

  return (
    <div className="tabelle-millesimali-container">
      <DataTable
        config={{
          ...tabelleMillesimaliTableConfig,
          columns,
        }}
        FormComponent={(props) => (
          <TabellaMillesimaleFormModal
            {...props}
            condomini={condomini}
          />
        )}
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

export default TabelleMillesimaliList;
