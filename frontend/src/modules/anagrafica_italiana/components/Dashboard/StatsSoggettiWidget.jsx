import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { getSoggettiAnagrafici } from '../../services/anagraficaAPI';
import { renderIcon } from '../../../../components/Navigation/iconRegistry.jsx';
import '../../../../components/UI/Button.css';
import './StatsSoggettiWidget.css';

/**
 * StatsSoggettiWidget - Dashboard widget for anagrafica statistics
 *
 * Shows summary statistics and quick actions for registry management
 */
function StatsSoggettiWidget() {
  const [stats, setStats] = useState({
    totale: 0,
    persone_fisiche: 0,
    persone_giuridiche: 0,
    attivi: 0,
    inattivi: 0,
    con_ruoli: 0,
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadStats();
  }, []);

  const loadStats = async () => {
    try {
      setLoading(true);
      setError(null);

      // Get all soggetti
      const soggetti = await getSoggettiAnagrafici({ limit: 10000 });

      // Calculate statistics
      const totale = soggetti.length;
      const persone_fisiche = soggetti.filter(s => s.tipo_soggetto === 'PERSONA_FISICA').length;
      const persone_giuridiche = soggetti.filter(s => s.tipo_soggetto === 'PERSONA_GIURIDICA').length;
      const attivi = soggetti.filter(s => s.attivo).length;
      const inattivi = totale - attivi;

      setStats({
        totale,
        persone_fisiche,
        persone_giuridiche,
        attivi,
        inattivi,
        con_ruoli: 0, // Removed slow ruoli check
      });
    } catch (err) {
      console.error('Error loading stats:', err);
      setError('Errore nel caricamento delle statistiche');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="stats-soggetti-widget">
        <div className="widget-loading">Caricamento...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="stats-soggetti-widget">
        <div className="widget-error" role="alert">{error}</div>
      </div>
    );
  }

  return (
    <div className="stats-soggetti-widget">
      {/* Header */}
      <div className="widget-header">
        <h3 className="widget-title">
          <span className="widget-title-icon" aria-hidden="true">
            {renderIcon('users', { size: 18 })}
          </span>
          Anagrafiche
        </h3>
        <Link to="/anagrafiche/lista" className="view-all-link">
          Vedi tutto
        </Link>
      </div>

      {/* Stats Grid */}
      <div className="stats-grid">
        <Link to="/anagrafiche/lista" className="stat-card totale">
          <span className="stat-value">{stats.totale}</span>
          <span className="stat-label">Totale</span>
        </Link>

        <Link to="/anagrafiche/persone-fisiche" className="stat-card stat-card--row">
          <span className="stat-icon" aria-hidden="true">
            {renderIcon('user', { size: 22 })}
          </span>
          <span className="stat-content">
            <span className="stat-value">{stats.persone_fisiche}</span>
            <span className="stat-label">Persone Fisiche</span>
          </span>
        </Link>

        <Link to="/anagrafiche/persone-giuridiche" className="stat-card stat-card--row">
          <span className="stat-icon" aria-hidden="true">
            {renderIcon('building', { size: 22 })}
          </span>
          <span className="stat-content">
            <span className="stat-value">{stats.persone_giuridiche}</span>
            <span className="stat-label">Persone Giuridiche</span>
          </span>
        </Link>

        <Link to="/anagrafiche/lista" className="stat-card stat-card--attivi">
          <span className="stat-value">{stats.attivi}</span>
          <span className="stat-label">Attivi</span>
        </Link>

        <Link to="/anagrafiche/lista" className="stat-card stat-card--inattivi">
          <span className="stat-value">{stats.inattivi}</span>
          <span className="stat-label">Inattivi</span>
        </Link>
      </div>

      {/* Quick Action */}
      <div className="widget-actions">
        <Link to="/anagrafiche/nuovo" className="ds-btn ds-btn--secondary ds-btn--md widget-action-btn">
          {renderIcon('plus', { size: 16 })}
          Nuova Anagrafica
        </Link>
      </div>
    </div>
  );
}

export default StatsSoggettiWidget;
