import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { unitaImmobiliariAPI, proprietariAPI, condominAPI } from '../../services/immobiliAPI';
import '../../../../components/UI/Button.css';
import { renderIcon } from '../../../../components/Navigation/iconRegistry.jsx';
import './ImmobiliStatsWidget.css';

/**
 * ImmobiliStatsWidget - Dashboard widget for real estate statistics
 *
 * Shows summary statistics and quick actions for property management
 */
function ImmobiliStatsWidget() {
  const [stats, setStats] = useState({
    totale_immobili: 0,
    totale_proprietari: 0,
    totale_condomini: 0,
    immobili_liberi: 0,
    immobili_affittati: 0,
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

      // Get token
      const token = localStorage.getItem('access_token');

      // Configure axios interceptor for authentication
      const setupAuth = (apiCall) => {
        const originalRequest = apiCall;
        originalRequest.defaults = originalRequest.defaults || {};
        originalRequest.defaults.headers = originalRequest.defaults.headers || {};
        originalRequest.defaults.headers.common = originalRequest.defaults.headers.common || {};
        originalRequest.defaults.headers.common['Authorization'] = `Bearer ${token}`;
        return apiCall;
      };

      // Get all data in parallel
      const [immobiliRes, proprietariRes, condominiRes] = await Promise.all([
        setupAuth(unitaImmobiliariAPI).getAll(),
        setupAuth(proprietariAPI).getAll(),
        setupAuth(condominAPI).getAll(),
      ]);

      const immobili = immobiliRes.data;
      const proprietari = proprietariRes.data;
      const condomini = condominiRes.data;

      // Calculate statistics
      setStats({
        totale_immobili: immobili.length,
        totale_proprietari: proprietari.length,
        totale_condomini: condomini.length,
        immobili_liberi: immobili.filter(i => !i.affittato).length,
        immobili_affittati: immobili.filter(i => i.affittato).length,
      });
    } catch (err) {
      console.error('Error loading immobili stats:', err);
      setError('Errore nel caricamento delle statistiche');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="immobili-stats-widget">
        <div className="widget-loading">Caricamento...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="immobili-stats-widget">
        <div className="widget-error" role="alert">{error}</div>
      </div>
    );
  }

  return (
    <div className="immobili-stats-widget">
      {/* Header */}
      <div className="widget-header">
        <h3 className="widget-title">
          <span className="widget-title-icon" aria-hidden="true">
            {renderIcon('building', { size: 18 })}
          </span>
          Immobili
        </h3>
        <Link to="/immobili" className="view-all-link">
          Vedi tutto
        </Link>
      </div>

      {/* Stats Grid */}
      <div className="stats-grid">
        <Link to="/immobili" className="stat-card totale">
          <span className="stat-value">{stats.totale_immobili}</span>
          <span className="stat-label">Unità Immobiliari</span>
        </Link>

        <Link to="/proprietari" className="stat-card stat-card--row">
          <span className="stat-icon" aria-hidden="true">
            {renderIcon('user-tie', { size: 22 })}
          </span>
          <span className="stat-content">
            <span className="stat-value">{stats.totale_proprietari}</span>
            <span className="stat-label">Proprietari</span>
          </span>
        </Link>

        <Link to="/condomini" className="stat-card stat-card--row">
          <span className="stat-icon" aria-hidden="true">
            {renderIcon('building-columns', { size: 22 })}
          </span>
          <span className="stat-content">
            <span className="stat-value">{stats.totale_condomini}</span>
            <span className="stat-label">Condomini</span>
          </span>
        </Link>

        <div className="stat-card stat-card--liberi">
          <div className="stat-value">{stats.immobili_liberi}</div>
          <div className="stat-label">Liberi</div>
        </div>

        <div className="stat-card stat-card--affittati">
          <div className="stat-value">{stats.immobili_affittati}</div>
          <div className="stat-label">Affittati</div>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="widget-actions">
        <Link to="/immobili" className="ds-btn ds-btn--secondary ds-btn--md widget-action-btn">
          {renderIcon('building', { size: 16 })}
          Gestisci Unità Immobiliari
        </Link>
      </div>
    </div>
  );
}

export default ImmobiliStatsWidget;
