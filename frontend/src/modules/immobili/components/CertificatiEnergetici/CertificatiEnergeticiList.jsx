import { useEffect, useState, useCallback, useMemo } from 'react';
import { DataTable } from '../../../../core/components';
import { certificatiEnergeticiAPI, unitaImmobiliariAPI } from '../../services/immobiliAPI';
import { tecniciAPI } from '../../../../services/api';
import CertificatoEnergeticoForm from './CertificatoEnergeticoForm';
import './CertificatiEnergetici.css';

const certificatiTableConfig = {
  endpoint: '/certificati-energetici/',
  title: 'Certificati Energetici',
  searchPlaceholder: 'Cerca per immobile, tecnico o protocollo...',
  emptyTitle: 'Nessun certificato trovato',
  emptyMessage: 'Non ci sono certificati energetici registrati.',
  addButtonLabel: 'Nuovo Certificato',
  columns: [
    { field: 'immobile_id', label: 'Immobile' },
    { field: 'tecnico_id', label: 'Tecnico' },
    { field: 'classe_energetica', label: 'Classe' },
    { field: 'indice_prestazione_energetica', label: 'IPE' },
    { field: 'data_emissione', label: 'Emissione' },
    { field: 'data_scadenza', label: 'Scadenza' },
    { field: 'numero_protocollo', label: 'Protocollo' },
    { field: 'stato', label: 'Stato' },
  ],
  defaultSort: { field: 'data_scadenza', order: 'desc' },
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

function CertificatoEnergeticoFormModal({ entity, onClose, immobili, tecnici }) {
  return (
    <CertificatoEnergeticoForm
      certificato={entity}
      immobili={immobili}
      tecnici={tecnici}
      onClose={onClose}
    />
  );
}

function CertificatiEnergeticiList() {
  const [immobili, setImmobili] = useState([]);
  const [tecnici, setTecnici] = useState([]);
  const [validiSolo, setValidiSolo] = useState(true);

  useEffect(() => {
    const fetchSupportData = async () => {
      try {
        const [immResponse, tecResponse] = await Promise.all([
          unitaImmobiliariAPI.getAll(),
          tecniciAPI.getAll(true),
        ]);
        setImmobili(immResponse.data || []);
        setTecnici(tecResponse.data || []);
      } catch (err) {
        console.error('Errore nel caricamento support data:', err);
      }
    };

    fetchSupportData();
  }, []);

  const getImmobileInfo = useCallback((id) => {
    const immobile = immobili.find(i => i.id === id);
    return immobile ? `${immobile.codice} - ${immobile.indirizzo}` : '-';
  }, [immobili]);

  const getTecnicoInfo = useCallback((id) => {
    const tecnico = tecnici.find(t => t.id === id);
    return tecnico ? `${tecnico.nome} ${tecnico.cognome}` : '-';
  }, [tecnici]);

  const isScaduto = useCallback((dataScadenza) => {
    return new Date(dataScadenza) < new Date();
  }, []);

  const renderToolbar = useCallback(({ table }) => (
    <label className="filter-checkbox">
      <input
        type="checkbox"
        checked={validiSolo}
        onChange={(e) => {
          const checked = e.target.checked;
          setValidiSolo(checked);
          table.setFilter('data_scadenza', checked ? (value) => !isScaduto(value) : '');
        }}
      />
      Solo validi
    </label>
  ), [validiSolo, isScaduto]);

  const columns = [
    {
      ...certificatiTableConfig.columns[0],
      render: (value) => getImmobileInfo(value),
    },
    {
      ...certificatiTableConfig.columns[1],
      render: (value) => getTecnicoInfo(value),
    },
    {
      ...certificatiTableConfig.columns[2],
      render: (value) => (
        <span className={`classe-badge classe-${value?.toLowerCase()}`}>
          {value || '-'}
        </span>
      ),
    },
    {
      ...certificatiTableConfig.columns[3],
      render: (value) => (value ? `${value} kWh/m²a` : '-'),
    },
    {
      ...certificatiTableConfig.columns[4],
      render: (value) => (value ? new Date(value).toLocaleDateString('it-IT') : '-'),
    },
    {
      ...certificatiTableConfig.columns[5],
      render: (value) => (value ? new Date(value).toLocaleDateString('it-IT') : '-'),
    },
    {
      ...certificatiTableConfig.columns[6],
      render: (value) => value || '-',
    },
    {
      ...certificatiTableConfig.columns[7],
      render: (value, row) => (
        <span className={`badge ${isScaduto(row.data_scadenza) ? 'badge-danger' : 'badge-success'}`}>
          {isScaduto(row.data_scadenza) ? 'Scaduto' : 'Valido'}
        </span>
      ),
    },
  ];

  const tableConfig = useMemo(() => ({
    ...certificatiTableConfig,
    columns,
    defaultFilters: validiSolo ? { data_scadenza: (value) => !isScaduto(value) } : {},
  }), [columns, validiSolo, isScaduto]);

  return (
    <div className="certificati-container">
      <DataTable
        config={tableConfig}
        FormComponent={(props) => (
          <CertificatoEnergeticoFormModal
            {...props}
            immobili={immobili}
            tecnici={tecnici}
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

export default CertificatiEnergeticiList;
