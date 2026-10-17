import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { scadenzeAPI } from '../../../../services/api';
import './ScadenzeWidget.css';

/**
 * ScadenzeWidget - Dashboard widget for upcoming affitti_brevi deadlines
 *
 * Legge le scadenze reali dal motore core (core_scadenze, filtrate per
 * modulo=affitti_brevi) — vedi docs/superpowers/specs/2026-09-28-affitti-
 * brevi-motore-scadenze-compliance-design.md. Sostituisce la versione
 * precedente, che chiamava endpoint /affitti-brevi/scadenze/* mai esistiti.
 */
function ScadenzeWidget() {
  const [scadenze, setScadenze] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadScadenze();
  }, []);

  const loadScadenze = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await scadenzeAPI.list({ modulo: 'affitti_brevi', limit: 100 });
      setScadenze(response.data);
    } catch (err) {
      console.error('Error loading scadenze:', err);
      setError('Errore nel caricamento delle scadenze');
    } finally {
      setLoading(false);
    }
  };

  const attive = scadenze.filter((s) => s.stato !== 'COMPLETATA' && s.stato !== 'CANCELLATA');
  const scadute = attive.filter((s) => s.is_scaduta);
  const inScadenza = attive.filter((s) => !s.is_scaduta);
  const completate = scadenze.filter((s) => s.stato === 'COMPLETATA');

  const upcoming = [...scadute, ...inScadenza]
    .sort((a, b) => new Date(a.data_scadenza) - new Date(b.data_scadenza))
    .slice(0, 5);

  const formatDate = (dateString) => new Date(dateString).toLocaleDateString('it-IT');

  if (loading) {
    return (
      <div className="scadenze-widget">
        <div className="widget-loading">Caricamento...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="scadenze-widget">
        <div className="widget-error">{error}</div>
      </div>
    );
  }

  return (
    <div className="scadenze-widget">
      <div className="widget-header">
        <h3>⏰ Scadenze Affitti Brevi</h3>
      </div>

      <div className="stats-summary">
        <div className="stat-item stat-danger">
          <div className="stat-value">{scadute.length}</div>
          <div className="stat-label">Scadute</div>
        </div>
        <div className="stat-item stat-warning">
          <div className="stat-value">{inScadenza.length}</div>
          <div className="stat-label">In Scadenza</div>
        </div>
        <div className="stat-item stat-success">
          <div className="stat-value">{completate.length}</div>
          <div className="stat-label">Completate</div>
        </div>
      </div>

      <div className="scadenze-list">
        <h4>Prossime Scadenze</h4>
        {upcoming.length === 0 ? (
          <div className="no-scadenze">
            <p>Nessuna scadenza urgente</p>
          </div>
        ) : (
          <ul>
            {upcoming.map((scadenza) => (
              <li key={scadenza.id} className="scadenza-item">
                <div className="scadenza-header">
                  <span className={`badge ${scadenza.is_scaduta ? 'badge-danger' : 'badge-warning'}`}>
                    {scadenza.is_scaduta ? 'Scaduta' : 'In Scadenza'}
                  </span>
                </div>
                <div className="scadenza-title">{scadenza.titolo}</div>
                <div className="scadenza-date">{formatDate(scadenza.data_scadenza)}</div>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}

export default ScadenzeWidget;
