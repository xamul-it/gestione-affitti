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
      // Richiede solo gli stati non terminali (ATTIVA/SCADUTA) via due
      // chiamate separate, invece di un limit=100 ordinato per priorita
      // senza filtro stato: con abbastanza scadenze completate accumulate
      // (mai cancellate) nel tempo, le ultime 100 righe erano quasi tutte
      // vecchie scadenze POLIZIA completate, e le scadenze attive reali
      // (di qualsiasi tipo) finivano fuori dal risultato — vedi review
      // finale del motore scadenze compliance.
      const [attiveResp, scaduteResp] = await Promise.all([
        scadenzeAPI.list({ modulo: 'affitti_brevi', stato: 'ATTIVA', limit: 100 }),
        scadenzeAPI.list({ modulo: 'affitti_brevi', stato: 'SCADUTA', limit: 100 }),
      ]);
      setScadenze([...attiveResp.data, ...scaduteResp.data]);
    } catch (err) {
      console.error('Error loading scadenze:', err);
      setError('Errore nel caricamento delle scadenze');
    } finally {
      setLoading(false);
    }
  };

  const scadute = scadenze.filter((s) => s.is_scaduta);
  const inScadenza = scadenze.filter((s) => !s.is_scaduta);

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
