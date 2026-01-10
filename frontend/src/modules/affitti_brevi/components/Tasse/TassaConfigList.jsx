import { useState, useEffect } from 'react';
import { tasseAPI } from '../../services/affittiBreviAPI';
import TassaConfigForm from './TassaConfigForm';
import './Tasse.css';

function TassaConfigList() {
  const [configs, setConfigs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showForm, setShowForm] = useState(false);
  const [editingConfig, setEditingConfig] = useState(null);
  const [expandedConfigId, setExpandedConfigId] = useState(null);
  const [scaglioni, setScaglioni] = useState({});

  useEffect(() => {
    fetchConfigs();
  }, []);

  const fetchConfigs = async () => {
    try {
      setLoading(true);
      const response = await tasseAPI.getConfigs();
      setConfigs(response.data);
      setError(null);
    } catch (err) {
      setError('Errore nel caricamento delle configurazioni tassa');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const fetchScaglioni = async (configId) => {
    try {
      const response = await tasseAPI.getScaglioni(configId);
      setScaglioni(prev => ({
        ...prev,
        [configId]: response.data
      }));
    } catch (err) {
      console.error('Errore nel caricamento scaglioni:', err);
    }
  };

  const handleDelete = async (id) => {
    if (window.confirm('Sei sicuro di voler eliminare questa configurazione? Verranno eliminati anche tutti gli scaglioni associati.')) {
      try {
        await tasseAPI.deleteConfig(id);
        fetchConfigs();
      } catch (err) {
        setError('Errore nell\'eliminazione della configurazione');
        console.error(err);
      }
    }
  };

  const handleEdit = (config) => {
    setEditingConfig(config);
    setShowForm(true);
  };

  const handleFormClose = () => {
    setShowForm(false);
    setEditingConfig(null);
    fetchConfigs();
  };

  const toggleScaglioni = async (configId) => {
    if (expandedConfigId === configId) {
      setExpandedConfigId(null);
    } else {
      setExpandedConfigId(configId);
      if (!scaglioni[configId]) {
        await fetchScaglioni(configId);
      }
    }
  };

  const getTipoCalcoloLabel = (tipo) => {
    const labels = {
      FISSO: 'Fisso',
      PERCENTUALE: 'Percentuale',
      SCAGLIONI: 'Scaglioni'
    };
    return labels[tipo] || tipo;
  };

  const getTipoCalcoloBadgeClass = (tipo) => {
    const classes = {
      FISSO: 'badge-info',
      PERCENTUALE: 'badge-warning',
      SCAGLIONI: 'badge-primary'
    };
    return classes[tipo] || 'badge-secondary';
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'Indefinita';
    return new Date(dateString).toLocaleDateString('it-IT');
  };

  const formatAmount = (amount) => {
    if (!amount) return '-';
    return `€ ${parseFloat(amount).toFixed(2)}`;
  };

  if (loading) return <div className="loading">Caricamento...</div>;
  if (error) return <div className="error">{error}</div>;

  return (
    <div className="tasse-container">
      <div className="header">
        <h1>Configurazioni Tassa di Soggiorno</h1>
        <div className="header-actions">
          <button onClick={() => setShowForm(true)} className="btn btn-primary">
            + Nuova Configurazione
          </button>
        </div>
      </div>

      {showForm && (
        <TassaConfigForm
          config={editingConfig}
          onClose={handleFormClose}
        />
      )}

      <div className="configs-list">
        {configs.length === 0 ? (
          <div className="empty-state">
            <p>Nessuna configurazione trovata</p>
            <button onClick={() => setShowForm(true)} className="btn btn-primary">
              Crea la prima configurazione
            </button>
          </div>
        ) : (
          configs.map((config) => (
            <div key={config.id} className={`config-card ${!config.attiva ? 'inactive' : ''}`}>
              <div className="config-header">
                <div className="config-title">
                  <h3>{config.comune_nome}</h3>
                  <span className={`badge ${getTipoCalcoloBadgeClass(config.tipo_calcolo)}`}>
                    {getTipoCalcoloLabel(config.tipo_calcolo)}
                  </span>
                  {!config.attiva && <span className="badge badge-secondary">Inattiva</span>}
                </div>
                <div className="config-actions">
                  <button onClick={() => handleEdit(config)} className="btn btn-sm btn-secondary">
                    Modifica
                  </button>
                  <button onClick={() => handleDelete(config.id)} className="btn btn-sm btn-danger">
                    Elimina
                  </button>
                </div>
              </div>

              <div className="config-body">
                <div className="config-details">
                  <div className="detail-row">
                    <span className="detail-label">Validità:</span>
                    <span className="detail-value">
                      {formatDate(config.data_inizio_validita)} - {formatDate(config.data_fine_validita)}
                    </span>
                  </div>

                  {config.tipo_calcolo === 'FISSO' && (
                    <div className="detail-row">
                      <span className="detail-label">Importo Fisso:</span>
                      <span className="detail-value">{formatAmount(config.importo_fisso)} / notte / persona</span>
                    </div>
                  )}

                  {config.tipo_calcolo === 'PERCENTUALE' && (
                    <div className="detail-row">
                      <span className="detail-label">Percentuale:</span>
                      <span className="detail-value">{config.percentuale}%</span>
                    </div>
                  )}

                  {config.tipo_calcolo === 'SCAGLIONI' && (
                    <div className="detail-row">
                      <button
                        onClick={() => toggleScaglioni(config.id)}
                        className="btn btn-sm btn-link"
                      >
                        {expandedConfigId === config.id ? '▼' : '▶'} Mostra Scaglioni
                      </button>
                    </div>
                  )}

                  {config.eta_minima > 0 && (
                    <div className="detail-row">
                      <span className="detail-label">Età Minima:</span>
                      <span className="detail-value">{config.eta_minima} anni</span>
                    </div>
                  )}

                  {config.eta_massima && (
                    <div className="detail-row">
                      <span className="detail-label">Età Massima:</span>
                      <span className="detail-value">{config.eta_massima} anni</span>
                    </div>
                  )}

                  {config.notti_max && (
                    <div className="detail-row">
                      <span className="detail-label">Massimo Notti Tassabili:</span>
                      <span className="detail-value">{config.notti_max}</span>
                    </div>
                  )}

                  {config.note && (
                    <div className="detail-row">
                      <span className="detail-label">Note:</span>
                      <span className="detail-value">{config.note}</span>
                    </div>
                  )}
                </div>

                {expandedConfigId === config.id && scaglioni[config.id] && (
                  <div className="scaglioni-table">
                    <h4>Scaglioni</h4>
                    <table className="data-table-sm">
                      <thead>
                        <tr>
                          <th>Notte Da</th>
                          <th>Notte A</th>
                          <th>Importo</th>
                        </tr>
                      </thead>
                      <tbody>
                        {scaglioni[config.id].map((scaglione) => (
                          <tr key={scaglione.id}>
                            <td>{scaglione.notte_da}</td>
                            <td>{scaglione.notte_a || '∞'}</td>
                            <td>{formatAmount(scaglione.importo)} / notte / persona</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}

export default TassaConfigList;
