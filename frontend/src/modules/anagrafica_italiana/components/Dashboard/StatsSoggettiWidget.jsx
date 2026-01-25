import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { getSoggettiAnagrafici, getSoggettoRuoli } from '../../services/anagraficaAPI';
import { renderIcon } from '../../../../components/Navigation/iconRegistry.jsx';
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
        <div className="widget-error">{error}</div>
      </div>
    );
  }

  return (
    <div className="stats-soggetti-widget">
      {/* Header */}
      <div className="widget-header">
        <h3 className="widget-title">
          <span className="widget-title-icon" aria-hidden="true">
            {renderIcon('users', { size: 18, className: 'widget-title-icon-svg', fallbackClassName: 'nav-emoji-icon' })}
          </span>
          Anagrafiche
        </h3>
        <Link to="/anagrafiche/lista" className="view-all-link">
          Vedi tutto
        </Link>
      </div>

      {/* Stats Grid */}
      <div className="stats-grid">
        <Link to="/anagrafiche/lista" className="stat-card-link">
          <div className="stat-card totale">
            <div className="stat-value">{stats.totale}</div>
            <div className="stat-label">Totale</div>
          </div>
        </Link>

        <Link to="/anagrafiche/persone-fisiche" className="stat-card-link">
          <div className="stat-card persone-fisiche">
            <div className="stat-icon" aria-hidden="true">
              {renderIcon('user', { size: 22, className: 'stat-icon-svg', fallbackClassName: 'nav-emoji-icon' })}
            </div>
            <div className="stat-content">
              <div className="stat-value">{stats.persone_fisiche}</div>
              <div className="stat-label">Persone Fisiche</div>
            </div>
          </div>
        </Link>

        <Link to="/anagrafiche/persone-giuridiche" className="stat-card-link">
          <div className="stat-card persone-giuridiche">
            <div className="stat-icon" aria-hidden="true">
              {renderIcon('building', { size: 22, className: 'stat-icon-svg', fallbackClassName: 'nav-emoji-icon' })}
            </div>
            <div className="stat-content">
              <div className="stat-value">{stats.persone_giuridiche}</div>
              <div className="stat-label">Persone Giuridiche</div>
            </div>
          </div>
        </Link>

        <Link to="/anagrafiche/lista" className="stat-card-link">
          <div className="stat-card attivi">
            <div className="stat-value">{stats.attivi}</div>
            <div className="stat-label">Attivi</div>
            <div className="stat-badge active">●</div>
          </div>
        </Link>

        <Link to="/anagrafiche/lista" className="stat-card-link">
          <div className="stat-card inattivi">
            <div className="stat-value">{stats.inattivi}</div>
            <div className="stat-label">Inattivi</div>
            <div className="stat-badge inactive">●</div>
          </div>
        </Link>
      </div>

      {/* Quick Action */}
      <div className="widget-actions">
        <Link to="/anagrafiche/nuovo" className="btn btn-primary btn-block">
          + Nuova Anagrafica
        </Link>
      </div>
    </div>
  );
}

export default StatsSoggettiWidget;
