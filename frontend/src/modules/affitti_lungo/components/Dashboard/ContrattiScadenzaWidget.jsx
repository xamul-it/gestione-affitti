import React, { useState, useEffect } from 'react';
import { getContratti } from '../../services/affittiAPI';
import './AffittiWidgets.css';

/**
 * ContrattiScadenzaWidget - Dashboard widget for expiring contracts
 * Shows contracts expiring in the next 90 days
 */
function ContrattiScadenzaWidget() {
  const [contratti, setContratti] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadContratti();
  }, []);

  const loadContratti = async () => {
    try {
      setLoading(true);
      setError(null);

      // Get all contratti
      const data = await getContratti({ limit: 1000 });

      // Filter contracts expiring in next 90 days
      const today = new Date();
      const in90Days = new Date(today.getTime() + 90 * 24 * 60 * 60 * 1000);

      const scadenzaContratti = data.filter(c => {
        if (!c.data_fine_contratto) return false;
        const dataFine = new Date(c.data_fine_contratto);
        return dataFine >= today && dataFine <= in90Days;
      });

      setContratti(scadenzaContratti);
    } catch (err) {
      console.error('Error loading contratti:', err);
      setError('Errore nel caricamento dei contratti');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="affitti-widget">
        <div className="widget-loading">Caricamento...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="affitti-widget">
        <div className="widget-error">{error}</div>
      </div>
    );
  }

  return (
    <div className="affitti-widget contratti-scadenza-widget">
      <div className="widget-header">
        <h3>📋 Contratti in Scadenza</h3>
        <span className="badge-count">{contratti.length}</span>
      </div>

      <div className="widget-content">
        {contratti.length === 0 ? (
          <div className="empty-state">
            <p>✅ Nessun contratto in scadenza nei prossimi 90 giorni</p>
          </div>
        ) : (
          <ul className="contratti-list">
            {contratti.slice(0, 5).map(contratto => {
              const dataFine = new Date(contratto.data_fine_contratto);
              const giorni = Math.ceil((dataFine - new Date()) / (1000 * 60 * 60 * 24));

              return (
                <li key={contratto.id} className="contratto-item">
                  <div className="contratto-info">
                    <strong>{contratto.affittuario_nome || 'N/D'}</strong>
                    <small>{contratto.unita_indirizzo || 'Indirizzo N/D'}</small>
                  </div>
                  <div className={`giorni-badge ${giorni <= 30 ? 'urgente' : ''}`}>
                    {giorni} giorni
                  </div>
                </li>
              );
            })}
          </ul>
        )}
        {contratti.length > 5 && (
          <div className="widget-footer">
            <small>Altri {contratti.length - 5} contratti in scadenza</small>
          </div>
        )}
      </div>
    </div>
  );
}

export default ContrattiScadenzaWidget;
