import { useState, useEffect } from 'react';
import { tasseAPI } from '../../services/affittiBreviAPI';
import './Tasse.css';

function TassaPrenotazioneDetail({ prenotazioneId, onClose }) {
  const [tassa, setTassa] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [calculating, setCalculating] = useState(false);
  const [showOverrideForm, setShowOverrideForm] = useState(false);
  const [overrideData, setOverrideData] = useState({
    importo_manuale: '',
    note_manuale: ''
  });

  useEffect(() => {
    loadTassa();
  }, [prenotazioneId]);

  const loadTassa = async () => {
    try {
      setLoading(true);
      const response = await tasseAPI.getTassaByPrenotazione(prenotazioneId);
      setTassa(response.data);
      setError(null);
    } catch (err) {
      if (err.response?.status === 404) {
        // No tax calculated yet
        setTassa(null);
        setError('Tassa non ancora calcolata per questa prenotazione');
      } else {
        setError('Errore nel caricamento della tassa');
        console.error(err);
      }
    } finally {
      setLoading(false);
    }
  };

  const handleCalculate = async (forceRecalculate = false) => {
    try {
      setCalculating(true);
      setError(null);
      const response = await tasseAPI.calculateTax(prenotazioneId, forceRecalculate);
      setTassa(response.data.tassa);
    } catch (err) {
      setError(err.response?.data?.detail || 'Errore nel calcolo della tassa');
      console.error(err);
    } finally {
      setCalculating(false);
    }
  };

  const handleOverride = async (e) => {
    e.preventDefault();

    if (!overrideData.importo_manuale || !overrideData.note_manuale) {
      setError('Importo e note sono obbligatori per l\'override');
      return;
    }

    try {
      const response = await tasseAPI.overrideTassa(prenotazioneId, {
        importo_manuale: parseFloat(overrideData.importo_manuale),
        note_manuale: overrideData.note_manuale
      });
      setTassa(response.data);
      setShowOverrideForm(false);
      setOverrideData({ importo_manuale: '', note_manuale: '' });
      setError(null);
    } catch (err) {
      setError(err.response?.data?.detail || 'Errore nell\'override della tassa');
      console.error(err);
    }
  };

  const handleRemoveOverride = async () => {
    if (!window.confirm('Sei sicuro di voler rimuovere l\'override manuale?')) {
      return;
    }

    try {
      const response = await tasseAPI.removeOverride(prenotazioneId);
      setTassa(response.data);
      setError(null);
    } catch (err) {
      setError('Errore nella rimozione dell\'override');
      console.error(err);
    }
  };

  const formatAmount = (amount) => {
    if (!amount) return '€ 0.00';
    return `€ ${parseFloat(amount).toFixed(2)}`;
  };

  const formatDate = (dateString) => {
    if (!dateString) return '-';
    return new Date(dateString).toLocaleDateString('it-IT', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const renderBreakdown = (dettaglio) => {
    if (!dettaglio) return null;

    return (
      <div className="breakdown-section">
        <h4>Dettaglio Calcolo</h4>

        <div className="breakdown-detail">
          <span className="breakdown-label">Tipo Calcolo:</span>
          <span className="breakdown-value">{dettaglio.tipo_calcolo}</span>
        </div>

        {dettaglio.tipo_calcolo === 'FISSO' && (
          <>
            <div className="breakdown-detail">
              <span className="breakdown-label">Importo Fisso:</span>
              <span className="breakdown-value">{formatAmount(dettaglio.importo_fisso)}</span>
            </div>
            <div className="breakdown-detail">
              <span className="breakdown-label">Formula:</span>
              <span className="breakdown-value">{dettaglio.calcolo}</span>
            </div>
          </>
        )}

        {dettaglio.tipo_calcolo === 'PERCENTUALE' && (
          <>
            <div className="breakdown-detail">
              <span className="breakdown-label">Percentuale:</span>
              <span className="breakdown-value">{dettaglio.percentuale}%</span>
            </div>
            <div className="breakdown-detail">
              <span className="breakdown-label">Prezzo Totale Booking:</span>
              <span className="breakdown-value">{formatAmount(dettaglio.prezzo_totale_booking)}</span>
            </div>
            <div className="breakdown-detail">
              <span className="breakdown-label">Prezzo per Notte:</span>
              <span className="breakdown-value">{formatAmount(dettaglio.prezzo_notte)}</span>
            </div>
            <div className="breakdown-detail">
              <span className="breakdown-label">Formula:</span>
              <span className="breakdown-value">{dettaglio.calcolo}</span>
            </div>
          </>
        )}

        {dettaglio.tipo_calcolo === 'SCAGLIONI' && (
          <>
            <table className="data-table-sm">
              <thead>
                <tr>
                  <th>Notti</th>
                  <th>Count</th>
                  <th>Importo/Notte</th>
                  <th>Ospiti</th>
                  <th>Subtotale</th>
                </tr>
              </thead>
              <tbody>
                {dettaglio.scaglioni.map((scaglione, index) => (
                  <tr key={index}>
                    <td>{scaglione.notti}</td>
                    <td>{scaglione.notti_count}</td>
                    <td>{formatAmount(scaglione.importo_notte)}</td>
                    <td>{scaglione.ospiti}</td>
                    <td>{formatAmount(scaglione.subtotale)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </>
        )}

        <div className="breakdown-detail">
          <span className="breakdown-label">Notti Totali:</span>
          <span className="breakdown-value">{dettaglio.notti_totali}</span>
        </div>

        <div className="breakdown-detail">
          <span className="breakdown-label">Notti Tassabili:</span>
          <span className="breakdown-value">{dettaglio.notti_tassabili}</span>
        </div>

        {dettaglio.ospiti_totali !== undefined && (
          <>
            <div className="breakdown-detail">
              <span className="breakdown-label">Ospiti Totali:</span>
              <span className="breakdown-value">{dettaglio.ospiti_totali}</span>
            </div>
            <div className="breakdown-detail">
              <span className="breakdown-label">Ospiti Tassabili:</span>
              <span className="breakdown-value">{dettaglio.ospiti_tassabili}</span>
            </div>
            {dettaglio.ospiti_esenti > 0 && (
              <div className="breakdown-detail">
                <span className="breakdown-label">Ospiti Esenti:</span>
                <span className="breakdown-value">{dettaglio.ospiti_esenti}</span>
              </div>
            )}
          </>
        )}

        <div className="breakdown-total">
          <span className="breakdown-label">Importo Totale:</span>
          <span className="breakdown-value">{formatAmount(dettaglio.importo_totale)}</span>
        </div>
      </div>
    );
  };

  if (loading) {
    return (
      <div className="modal-overlay" onClick={onClose}>
        <div className="modal-content" onClick={(e) => e.stopPropagation()}>
          <div className="modal-body">
            <div className="loading">Caricamento...</div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content tassa-detail-modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>Tassa di Soggiorno - Prenotazione #{prenotazioneId}</h2>
          <button onClick={onClose} className="btn btn-sm btn-secondary">✕</button>
        </div>

        <div className="modal-body">
          {error && <div className="error">{error}</div>}

          {!tassa ? (
            <div className="empty-state-inline">
              <p>Nessuna tassa calcolata per questa prenotazione</p>
              <button
                onClick={() => handleCalculate(false)}
                className="btn btn-primary"
                disabled={calculating}
              >
                {calculating ? 'Calcolo...' : 'Calcola Tassa'}
              </button>
            </div>
          ) : (
            <>
              <div className="tassa-summary">
                <div className="summary-card">
                  <h3>Importo Finale</h3>
                  <div className="amount-display">
                    {formatAmount(tassa.importo_finale)}
                  </div>
                  {tassa.is_overridden && (
                    <span className="badge badge-warning">Override Manuale</span>
                  )}
                </div>

                {tassa.is_overridden && (
                  <div className="override-info">
                    <div className="detail-row">
                      <span className="detail-label">Importo Calcolato:</span>
                      <span className="detail-value">{formatAmount(tassa.importo_totale)}</span>
                    </div>
                    <div className="detail-row">
                      <span className="detail-label">Importo Manuale:</span>
                      <span className="detail-value">{formatAmount(tassa.importo_manuale)}</span>
                    </div>
                    <div className="detail-row">
                      <span className="detail-label">Motivo Override:</span>
                      <span className="detail-value">{tassa.note_manuale}</span>
                    </div>
                  </div>
                )}

                <div className="detail-row">
                  <span className="detail-label">Ultimo Calcolo:</span>
                  <span className="detail-value">{formatDate(tassa.data_ultimo_calcolo)}</span>
                </div>
              </div>

              {renderBreakdown(tassa.dettaglio_calcolo)}

              <div className="tassa-actions">
                <button
                  onClick={() => handleCalculate(true)}
                  className="btn btn-secondary"
                  disabled={calculating}
                >
                  {calculating ? 'Ricalcolo...' : 'Ricalcola'}
                </button>

                {!showOverrideForm ? (
                  <>
                    <button
                      onClick={() => setShowOverrideForm(true)}
                      className="btn btn-warning"
                    >
                      Override Manuale
                    </button>

                    {tassa.is_overridden && (
                      <button
                        onClick={handleRemoveOverride}
                        className="btn btn-danger"
                      >
                        Rimuovi Override
                      </button>
                    )}
                  </>
                ) : (
                  <form onSubmit={handleOverride} className="override-form">
                    <div className="form-group">
                      <label>Importo Manuale (€)</label>
                      <input
                        type="number"
                        value={overrideData.importo_manuale}
                        onChange={(e) => setOverrideData(prev => ({ ...prev, importo_manuale: e.target.value }))}
                        step="0.01"
                        min="0"
                        required
                      />
                    </div>
                    <div className="form-group">
                      <label>Motivo Override</label>
                      <textarea
                        value={overrideData.note_manuale}
                        onChange={(e) => setOverrideData(prev => ({ ...prev, note_manuale: e.target.value }))}
                        rows={3}
                        required
                      />
                    </div>
                    <div className="form-actions">
                      <button type="button" onClick={() => setShowOverrideForm(false)} className="btn btn-secondary">
                        Annulla
                      </button>
                      <button type="submit" className="btn btn-success">
                        Applica Override
                      </button>
                    </div>
                  </form>
                )}
              </div>
            </>
          )}
        </div>

        <div className="modal-footer">
          <button onClick={onClose} className="btn btn-secondary">
            Chiudi
          </button>
        </div>
      </div>
    </div>
  );
}

export default TassaPrenotazioneDetail;
