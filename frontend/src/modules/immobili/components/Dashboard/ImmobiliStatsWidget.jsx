import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { unitaImmobiliariAPI, condominAPI } from '../../services/immobiliAPI';
import { relazioniAPI } from '../../../../services/relazioniAPI';
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
    immobili_occupati: 0,
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

      // Relations need soggetto.view: without it the counts degrade to 0.
      const correnti = (famiglia) => relazioniAPI
        .list({ famiglia, entity_type: 'IMMOBILE', solo_correnti: true })
        .catch(() => ({ data: [] }));
      const [immobiliRes, dirittiRes, condominiRes, godimentoRes] = await Promise.all([
        unitaImmobiliariAPI.getAll(),
        correnti('diritti_reali'),
        condominAPI.getAll(),
        correnti('godimento'),
      ]);

      const immobili = immobiliRes.data;
      // A unit is occupied when it has a current enjoyment relation (tenancy, loan...).
      const occupate = new Set(godimentoRes.data.map((r) => r.entity_id));
      // Owners = distinct subjects holding a current right in rem.
      const titolari = new Set(dirittiRes.data.map((r) => r.soggetto_id));
      const occupati = immobili.filter((i) => occupate.has(i.id)).length;

      setStats({
        totale_immobili: immobili.length,
        totale_proprietari: titolari.size,
        totale_condomini: condominiRes.data.length,
        immobili_liberi: immobili.length - occupati,
        immobili_occupati: occupati,
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
        <Link to="/unita-immobiliari" className="view-all-link">
          Vedi tutto
        </Link>
      </div>

      {/* Stats Grid */}
      <div className="stats-grid">
        <Link to="/unita-immobiliari" className="stat-card totale">
          <span className="stat-value">{stats.totale_immobili}</span>
          <span className="stat-label">Unità Immobiliari</span>
        </Link>

        <Link to="/proprietari" className="stat-card stat-card--row">
          <span className="stat-icon" aria-hidden="true">
            {renderIcon('user-tie', { size: 22 })}
          </span>
          <span className="stat-content">
            <span className="stat-value">{stats.totale_proprietari}</span>
            <span className="stat-label">Titolari di diritti</span>
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
          <div className="stat-value">{stats.immobili_occupati}</div>
          <div className="stat-label">Occupati</div>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="widget-actions">
        <Link to="/unita-immobiliari" className="ds-btn ds-btn--secondary ds-btn--md widget-action-btn">
          {renderIcon('building', { size: 16 })}
          Gestisci Unità Immobiliari
        </Link>
      </div>
    </div>
  );
}

export default ImmobiliStatsWidget;
