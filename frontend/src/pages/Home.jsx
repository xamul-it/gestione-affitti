import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { immobiliAPI, contrattiAPI, speseAPI, incassiAPI } from '../services/api';
import './Home.css';

function Home() {
  const [stats, setStats] = useState({
    immobili: 0,
    contratti: 0,
    spese: 0,
    incassi: 0,
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchStats();
  }, []);

  const fetchStats = async () => {
    try {
      setLoading(true);
      const [immobili, contratti, spese, incassi] = await Promise.all([
        immobiliAPI.getAll(),
        contrattiAPI.getAll(),
        speseAPI.getAll(),
        incassiAPI.getAll(),
      ]);

      setStats({
        immobili: immobili.data.length,
        contratti: contratti.data.length,
        spese: spese.data.length,
        incassi: incassi.data.length,
      });
    } catch (err) {
      console.error('Errore caricamento statistiche:', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="home">
        <div className="loading">Caricamento dashboard...</div>
      </div>
    );
  }

  return (
    <div className="home">
      <div className="hero">
        <h1>Dashboard Gestione Affitti</h1>
        <p>Panoramica completa delle tue proprietà immobiliari</p>
      </div>

      {/* Statistiche Principali */}
      <div className="stats-grid">
        <Link to="/immobili" className="stat-card blue">
          <div className="stat-icon">🏢</div>
          <div className="stat-content">
            <div className="stat-value">{stats.immobili}</div>
            <div className="stat-label">Immobili</div>
          </div>
        </Link>

        <Link to="/contratti" className="stat-card green">
          <div className="stat-icon">📄</div>
          <div className="stat-content">
            <div className="stat-value">{stats.contratti}</div>
            <div className="stat-label">Contratti Attivi</div>
          </div>
        </Link>

        <Link to="/spese" className="stat-card orange">
          <div className="stat-icon">💰</div>
          <div className="stat-content">
            <div className="stat-value">{stats.spese}</div>
            <div className="stat-label">Spese Registrate</div>
          </div>
        </Link>

        <Link to="/incassi" className="stat-card purple">
          <div className="stat-icon">💵</div>
          <div className="stat-content">
            <div className="stat-value">{stats.incassi}</div>
            <div className="stat-label">Incassi</div>
          </div>
        </Link>
      </div>

      {/* Quick Actions */}
      <div className="quick-actions">
        <h2>Azioni Rapide</h2>
        <div className="actions-grid">
          <Link to="/dashboard" className="action-card">
            <span className="action-icon">📊</span>
            <span>Dashboard & Widget</span>
          </Link>
          <Link to="/immobili" className="action-card">
            <span className="action-icon">➕</span>
            <span>Nuovo Immobile</span>
          </Link>
          <Link to="/contratti" className="action-card">
            <span className="action-icon">📝</span>
            <span>Nuovo Contratto</span>
          </Link>
          <Link to="/spese" className="action-card">
            <span className="action-icon">💸</span>
            <span>Registra Spesa</span>
          </Link>
          <Link to="/condomini" className="action-card">
            <span className="action-icon">🏘️</span>
            <span>Gestione Condomini</span>
          </Link>
        </div>
      </div>

      {/* Moduli Disponibili */}
      <div className="modules-section">
        <h2>Moduli Disponibili</h2>
        <div className="features">
          <div className="feature-card">
            <h3>📁 Anagrafica</h3>
            <p>Gestione completa di immobili, condomini, proprietari e affittuari</p>
            <div className="feature-links">
              <Link to="/immobili">Immobili</Link>
              <Link to="/condomini">Condomini</Link>
              <Link to="/proprietari">Proprietari</Link>
            </div>
          </div>

          <div className="feature-card">
            <h3>💼 Gestione Affitti</h3>
            <p>Contratti, spese e incassi per affitti a lungo termine</p>
            <div className="feature-links">
              <Link to="/contratti">Contratti</Link>
              <Link to="/spese">Spese</Link>
              <Link to="/incassi">Incassi</Link>
            </div>
          </div>

          <div className="feature-card">
            <h3>📊 Condominio</h3>
            <p>Tabelle millesimali e ripartizione spese condominiali</p>
            <div className="feature-links">
              <Link to="/tabelle-millesimali">Tabelle</Link>
              <Link to="/millesimi-immobile">Millesimi</Link>
            </div>
          </div>

          <div className="feature-card">
            <h3>🔧 Utilità</h3>
            <p>Tecnici, certificati energetici e documenti</p>
            <div className="feature-links">
              <Link to="/tecnici">Tecnici</Link>
              <Link to="/certificati-energetici">Certificati</Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Home;
