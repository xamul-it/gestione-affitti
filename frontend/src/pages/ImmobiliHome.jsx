import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { unitaImmobiliariAPI, condominAPI, proprietariAPI } from '../services/api';
import './ImmobiliHome.css';

function ImmobiliHome() {
  const [stats, setStats] = useState({
    unitaImmobiliari: 0,
    condomini: 0,
    proprietari: 0,
  });
  const [loading, setLoading] = useState(true);
  const [recentUnita, setRecentUnita] = useState([]);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      setLoading(true);
      const [unita, condomini, proprietari] = await Promise.all([
        unitaImmobiliariAPI.getAll(),
        condominAPI.getAll(),
        proprietariAPI.getAll(),
      ]);

      setStats({
        unitaImmobiliari: unita.data.length,
        condomini: condomini.data.length,
        proprietari: proprietari.data.length,
      });

      // Get 5 most recent properties
      const sortedUnita = [...unita.data].sort((a, b) =>
        new Date(b.created_at) - new Date(a.created_at)
      );
      setRecentUnita(sortedUnita.slice(0, 5));
    } catch (err) {
      console.error('Errore caricamento dati immobili:', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="immobili-home">
        <div className="loading">Caricamento...</div>
      </div>
    );
  }

  return (
    <div className="immobili-home">
      <div className="page-header">
        <h1>🏢 Immobili</h1>
        <p>Anagrafica completa del patrimonio immobiliare</p>
      </div>

      {/* Statistiche */}
      <div className="stats-grid">
        <Link to="/unita-immobiliari" className="stat-card blue">
          <div className="stat-icon">🏠</div>
          <div className="stat-content">
            <div className="stat-value">{stats.unitaImmobiliari}</div>
            <div className="stat-label">Unità Immobiliari</div>
          </div>
        </Link>

        <Link to="/condomini" className="stat-card green">
          <div className="stat-icon">🏘️</div>
          <div className="stat-content">
            <div className="stat-value">{stats.condomini}</div>
            <div className="stat-label">Condomini</div>
          </div>
        </Link>

        <Link to="/proprietari" className="stat-card orange">
          <div className="stat-icon">👤</div>
          <div className="stat-content">
            <div className="stat-value">{stats.proprietari}</div>
            <div className="stat-label">Proprietari</div>
          </div>
        </Link>
      </div>

      {/* Quick Actions */}
      <div className="quick-actions">
        <h2>Azioni Rapide</h2>
        <div className="actions-grid">
          <Link to="/unita-immobiliari" className="action-card">
            <span className="action-icon">➕</span>
            <span>Nuova Unità Immobiliare</span>
          </Link>
          <Link to="/condomini" className="action-card">
            <span className="action-icon">🏘️</span>
            <span>Nuovo Condominio</span>
          </Link>
          <Link to="/proprietari" className="action-card">
            <span className="action-icon">👤</span>
            <span>Nuovo Proprietario</span>
          </Link>
        </div>
      </div>

      {/* Recent Properties */}
      {recentUnita.length > 0 && (
        <div className="recent-section">
          <h2>Unità Immobiliari Recenti</h2>
          <div className="recent-list">
            {recentUnita.map((unita) => (
              <Link
                key={unita.id}
                to={`/unita-immobiliari/${unita.id}`}
                className="recent-item"
              >
                <div className="recent-icon">🏠</div>
                <div className="recent-info">
                  <div className="recent-title">
                    {unita.tipo} - {unita.codice}
                  </div>
                  <div className="recent-subtitle">
                    {unita.indirizzo}, {unita.citta}
                  </div>
                </div>
                <div className="recent-meta">
                  {unita.superficie_mq && <span>{unita.superficie_mq} m²</span>}
                  {unita.locali && <span>{unita.locali} locali</span>}
                </div>
              </Link>
            ))}
          </div>
          <Link to="/unita-immobiliari" className="view-all-link">
            Vedi tutte le unità immobiliari →
          </Link>
        </div>
      )}

      {/* Empty State */}
      {stats.unitaImmobiliari === 0 && (
        <div className="empty-state">
          <div className="empty-icon">🏢</div>
          <h3>Nessuna Unità Immobiliare</h3>
          <p>Inizia registrando la tua prima unità immobiliare</p>
          <Link to="/unita-immobiliari" className="btn-primary">
            Aggiungi Unità Immobiliare
          </Link>
        </div>
      )}

      {/* Module Navigation */}
      <div className="modules-section">
        <h2>Sezioni Disponibili</h2>
        <div className="modules-grid">
          <Link to="/unita-immobiliari" className="module-card">
            <div className="module-icon">🏠</div>
            <h3>Unità Immobiliari</h3>
            <p>Gestione di appartamenti, case, uffici e negozi</p>
            <div className="module-count">{stats.unitaImmobiliari} registrate</div>
          </Link>

          <Link to="/condomini" className="module-card">
            <div className="module-icon">🏘️</div>
            <h3>Condomini</h3>
            <p>Anagrafica dei condomini e gestione amministrativa</p>
            <div className="module-count">{stats.condomini} registrati</div>
          </Link>

          <Link to="/proprietari" className="module-card">
            <div className="module-icon">👤</div>
            <h3>Proprietari</h3>
            <p>Anagrafica proprietari e diritti immobiliari</p>
            <div className="module-count">{stats.proprietari} registrati</div>
          </Link>
        </div>
      </div>
    </div>
  );
}

export default ImmobiliHome;
