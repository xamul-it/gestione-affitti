import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { scadenzeAPI } from '../../services/affittiBreviAPI';
import './ScadenzeWidget.css';

/**
 * ScadenzeWidget - Dashboard widget for upcoming deadlines
 *
 * Shows urgent and upcoming deadlines for affitti brevi
 */
function ScadenzeWidget() {
  const [stats, setStats] = useState({
    scadute: 0,
    inScadenza: 0,
    completate: 0,
  });
  const [upcomingScadenze, setUpcomingScadenze] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadScadenze();
  }, []);

  const loadScadenze = async () => {
    try {
      setLoading(true);
      setError(null);

      // Get all scadenze
      const response = await scadenzeAPI.getAll();
      const scadenze = response.data;

      // Calculate statistics
      const oggi = new Date();
      const setteDa = new Date();
      setteDa.setDate(oggi.getDate() + 7);

      const scadute = scadenze.filter(s => !s.completata && new Date(s.data_scadenza) < oggi);
      const inScadenza = scadenze.filter(s => {
        if (s.completata) return false;
        const dataScadenza = new Date(s.data_scadenza);
        return dataScadenza >= oggi && dataScadenza <= setteDa;
      });
      const completate = scadenze.filter(s => s.completata);

      setStats({
        scadute: scadute.length,
        inScadenza: inScadenza.length,
        completate: completate.length,
      });

      // Show next 5 upcoming deadlines
      const upcoming = [...scadute, ...inScadenza]
        .sort((a, b) => new Date(a.data_scadenza) - new Date(b.data_scadenza))
        .slice(0, 5);

      setUpcomingScadenze(upcoming);
    } catch (err) {
      console.error('Error loading scadenze:', err);
      setError('Errore nel caricamento delle scadenze');
    } finally {
      setLoading(false);
    }
  };

  const getTipoLabel = (tipo) => {
    const labels = {
      COMUNICAZIONE_POLIZIA: 'Polizia',
      REPORT_ISTAT: 'ISTAT',
      ALTRO: 'Altro'
    };
    return labels[tipo] || tipo;
  };

  const getTipoBadgeClass = (tipo) => {
    const classes = {
      COMUNICAZIONE_POLIZIA: 'tipo-badge-polizia',
      REPORT_ISTAT: 'tipo-badge-istat',
      ALTRO: 'tipo-badge-altro'
    };
    return classes[tipo] || 'tipo-badge-altro';
  };

  const getStatoLabel = (scadenza) => {
    const dataScadenza = new Date(scadenza.data_scadenza);
    const oggi = new Date();
    if (dataScadenza < oggi) return 'Scaduta';
    return 'In Scadenza';
  };

  const getStatoBadgeClass = (scadenza) => {
    const stato = getStatoLabel(scadenza);
    return stato === 'Scaduta' ? 'badge-danger' : 'badge-warning';
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('it-IT', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

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
      {/* Header */}
      <div className="widget-header">
        <h3>⏰ Scadenze Affitti Brevi</h3>
        <Link to="/affitti-brevi/scadenze" className="view-all-link">
          Vedi tutto
        </Link>
      </div>

      {/* Stats Summary */}
      <div className="stats-summary">
        <div className="stat-item stat-danger">
          <div className="stat-value">{stats.scadute}</div>
          <div className="stat-label">Scadute</div>
        </div>
        <div className="stat-item stat-warning">
          <div className="stat-value">{stats.inScadenza}</div>
          <div className="stat-label">In Scadenza</div>
        </div>
        <div className="stat-item stat-success">
          <div className="stat-value">{stats.completate}</div>
          <div className="stat-label">Completate</div>
        </div>
      </div>

      {/* Upcoming Scadenze List */}
      <div className="scadenze-list">
        <h4>Prossime Scadenze</h4>
        {upcomingScadenze.length === 0 ? (
          <div className="no-scadenze">
            <i className="fas fa-check-circle"></i>
            <p>Nessuna scadenza urgente</p>
          </div>
        ) : (
          <ul>
            {upcomingScadenze.map((scadenza) => (
              <li key={scadenza.id} className="scadenza-item">
                <div className="scadenza-header">
                  <span className={`tipo-badge ${getTipoBadgeClass(scadenza.tipo_scadenza)}`}>
                    {getTipoLabel(scadenza.tipo_scadenza)}
                  </span>
                  <span className={`badge ${getStatoBadgeClass(scadenza)}`}>
                    {getStatoLabel(scadenza)}
                  </span>
                </div>
                <div className="scadenza-title">{scadenza.titolo}</div>
                <div className="scadenza-date">
                  <i className="fas fa-clock"></i> {formatDate(scadenza.data_scadenza)}
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>

      {/* Quick Actions */}
      <div className="widget-actions">
        <Link to="/affitti-brevi/scadenze" className="btn btn-primary btn-block">
          Gestisci Scadenze
        </Link>
      </div>
    </div>
  );
}

export default ScadenzeWidget;
