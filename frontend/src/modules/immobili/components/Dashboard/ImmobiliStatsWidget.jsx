import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { unitaImmobiliariAPI, proprietariAPI, condominAPI } from '../../services/immobiliAPI';
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
        <div className="widget-error">{error}</div>
      </div>
    );
  }

  return (
    <div className="immobili-stats-widget">
      {/* Header */}
      <div className="widget-header">
        <h3>🏢 Immobili</h3>
        <Link to="/immobili" className="view-all-link">
          Vedi tutto
        </Link>
      </div>

      {/* Stats Grid */}
      <div className="stats-grid">
        <div className="stat-card totale">
          <div className="stat-value">{stats.totale_immobili}</div>
          <div className="stat-label">Unità Immobiliari</div>
        </div>

        <div className="stat-card proprietari">
          <div className="stat-icon">👤</div>
          <div className="stat-content">
            <div className="stat-value">{stats.totale_proprietari}</div>
            <div className="stat-label">Proprietari</div>
          </div>
        </div>

        <div className="stat-card condomini">
          <div className="stat-icon">🏛️</div>
          <div className="stat-content">
            <div className="stat-value">{stats.totale_condomini}</div>
            <div className="stat-label">Condomini</div>
          </div>
        </div>

        <div className="stat-card liberi">
          <div className="stat-value">{stats.immobili_liberi}</div>
          <div className="stat-label">Liberi</div>
          <div className="stat-badge available">●</div>
        </div>

        <div className="stat-card affittati">
          <div className="stat-value">{stats.immobili_affittati}</div>
          <div className="stat-label">Affittati</div>
          <div className="stat-badge occupied">●</div>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="widget-actions">
        <Link to="/immobili/nuovo" className="btn btn-primary btn-block">
          + Nuova Unità Immobiliare
        </Link>
      </div>
    </div>
  );
}

export default ImmobiliStatsWidget;
