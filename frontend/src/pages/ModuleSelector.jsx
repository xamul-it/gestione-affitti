import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import axios from 'axios';
import { renderIcon } from '../components/Navigation/iconRegistry.jsx';
import { loadLocalModuleManifests } from '../core/modules/localManifests.js';
import './ModuleSelector.css';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

/**
 * ModuleSelector - Home page per selezionare il modulo con cui lavorare
 *
 * Mostra tutti i moduli abilitati come card cliccabili che portano
 * alla dashboard del modulo specifico.
 */
function ModuleSelector() {
  const [modules, setModules] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [localManifests, setLocalManifests] = useState({});

  useEffect(() => {
    loadEnabledModules();
    loadLocalModuleManifests().then(setLocalManifests);
  }, []);

  const loadEnabledModules = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('access_token');
      const response = await axios.get(
        `${API_BASE_URL}/modules/enabled`,
        {
          headers: { 'Authorization': `Bearer ${token}` }
        }
      );
      setModules(response.data);
      setError(null);
    } catch (err) {
      console.error('Error loading modules:', err);
      setError(err.response?.data?.detail || err.message);
    } finally {
      setLoading(false);
    }
  };

  const MODULE_ICONS = {
    'anagrafica_italiana': 'id-card',
    'immobili': 'building',
    'affitti_lungo': 'file-contract',
    'condominio': 'building-2',
  };

  if (loading) {
    return (
      <div className="module-selector">
        <div className="loading-container">
          <div className="spinner"></div>
          <p>Caricamento moduli...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="module-selector">
        <div className="error-container">
          <i className="fas fa-exclamation-triangle"></i>
          <h2>Errore caricamento moduli</h2>
          <p>{error}</p>
          <button onClick={loadEnabledModules} className="retry-btn">
            Riprova
          </button>
        </div>
      </div>
    );
  }

  if (modules.length === 0) {
    return (
      <div className="module-selector">
        <div className="empty-container">
          <i className="fas fa-box-open"></i>
          <h2>Nessun Modulo Abilitato</h2>
          <p>Contatta l'amministratore per abilitare i moduli necessari.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="module-selector">
      <div className="hero-section">
        <h1>Benvenuto</h1>
        <p>Seleziona il modulo con cui vuoi lavorare</p>
      </div>

      <div className="modules-grid">
        {modules.map(module => {
          const local = localManifests[module.technical_name];
          const displayName = local?.displayName || module.name;
          const displayIcon = local?.icon || MODULE_ICONS[module.technical_name] || 'package';
          return (
            <Link
              key={module.technical_name}
              to={`/modules/${module.technical_name}/dashboard`}
              className="module-card"
            >
              <div className="module-icon">
                {renderIcon(displayIcon, { size: 28 })}
              </div>
              <div className="module-content">
                <h3>{displayName}</h3>
                <p className="module-version">v{module.version}</p>
              </div>
              <div className="module-arrow">
                <i className="fas fa-arrow-right"></i>
              </div>
            </Link>
          );
        })}
      </div>

      {/* Quick Links */}
      <div className="quick-links-section">
        <h2>Link Rapidi</h2>
        <div className="quick-links-grid">
          <Link to="/search" className="quick-link">
            <span className="quick-link-icon" aria-hidden="true">
              {renderIcon('search', { size: 18 })}
            </span>
            <span>Ricerca Globale</span>
          </Link>
          <Link to="/profile" className="quick-link">
            <span className="quick-link-icon" aria-hidden="true">
              {renderIcon('user', { size: 18 })}
            </span>
            <span>Il Mio Profilo</span>
          </Link>
        </div>
      </div>
    </div>
  );
}

export default ModuleSelector;
