import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { ChevronRight, Info, Settings } from 'lucide-react';
import axios from 'axios';
import { renderIcon } from '../../components/Navigation/iconRegistry.jsx';
import './DataAdmin.css';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

/**
 * DataAdmin - Pagina di amministrazione dati di dominio
 *
 * Centralizza tutte le configurazioni dei dati di riferimento
 * per tutti i moduli (categorie catastali, tipi documento, ecc.)
 */
function DataAdmin() {
  const [activeTab, setActiveTab] = useState(null);
  const [domainData, setDomainData] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Carica domain data da backend
  useEffect(() => {
    loadDomainData();
  }, []);

  const loadDomainData = async () => {
    try {
      setLoading(true);
      setError(null);

      const token = localStorage.getItem('access_token');
      const response = await axios.get(`${API_BASE_URL}/platform/menu/domain-data`, {
        headers: {
          Authorization: `Bearer ${token}`
        }
      });

      setDomainData(response.data);

      // Imposta il primo modulo come tab attivo
      const firstModuleId = Object.keys(response.data)[0];
      if (firstModuleId) {
        setActiveTab(firstModuleId);
      }

      setLoading(false);
    } catch (err) {
      console.error('Error loading domain data:', err);
      setError(err.response?.data?.detail || 'Errore caricamento dati di dominio');
      setLoading(false);
    }
  };

  // Loading state
  if (loading) {
    return (
      <div className="data-admin">
        <div className="data-admin-header">
          <h1>
            <span className="header-icon" aria-hidden="true">
              <Settings size={26} strokeWidth={1.7} />
            </span>
            Amministrazione Dati
          </h1>
          <p>Caricamento dati di dominio...</p>
        </div>
        <div style={{ padding: '40px', textAlign: 'center' }}>
          <div className="loading-spinner"></div>
        </div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="data-admin">
        <div className="data-admin-header">
          <h1>
            <span className="header-icon" aria-hidden="true">
              <Settings size={26} strokeWidth={1.7} />
            </span>
            Amministrazione Dati
          </h1>
        </div>
        <div style={{ padding: '40px', textAlign: 'center', color: '#d32f2f' }}>
          <p>⚠️ {error}</p>
          <button onClick={loadDomainData} style={{ marginTop: '20px', padding: '10px 20px', cursor: 'pointer' }}>
            Riprova
          </button>
        </div>
      </div>
    );
  }

  // No domain data
  if (Object.keys(domainData).length === 0) {
    return (
      <div className="data-admin">
        <div className="data-admin-header">
          <h1>
            <span className="header-icon" aria-hidden="true">
              <Settings size={26} strokeWidth={1.7} />
            </span>
            Amministrazione Dati
          </h1>
        </div>
        <div style={{ padding: '40px', textAlign: 'center', color: '#666' }}>
          <p>Nessun dato di dominio disponibile</p>
        </div>
      </div>
    );
  }

  return (
    <div className="data-admin">
      <div className="data-admin-header">
        <h1>
          <span className="header-icon" aria-hidden="true">
            <Settings size={26} strokeWidth={1.7} />
          </span>
          Amministrazione Dati
        </h1>
        <p>Configura i dati di riferimento per tutti i moduli</p>
      </div>

      {/* Tabs per moduli */}
      <div className="module-tabs-admin">
        {Object.keys(domainData).map(moduleId => (
          <button
            key={moduleId}
            className={`module-tab-admin ${activeTab === moduleId ? 'active' : ''}`}
            onClick={() => setActiveTab(moduleId)}
          >
            {domainData[moduleId].module_name}
          </button>
        ))}
      </div>

      {/* Configurazioni del modulo selezionato */}
      {activeTab && domainData[activeTab] && (
        <div className="config-grid">
          {domainData[activeTab].items.map(item => (
            <Link
              key={item.id}
              to={item.path}
              className="config-card"
            >
              <div className="config-icon" aria-hidden="true">
                {renderIcon(item.icon || 'list', { size: 18, fallbackClassName: 'nav-emoji-icon' })}
              </div>
              <div className="config-content">
                <h3>{item.label}</h3>
                <p>{item.description}</p>
              </div>
              <div className="config-arrow">
                <ChevronRight size={16} strokeWidth={1.7} aria-hidden="true" />
              </div>
            </Link>
          ))}
        </div>
      )}

      {/* Info Box */}
      <div className="admin-info-box">
        <div className="info-icon" aria-hidden="true">
          <Info size={18} strokeWidth={1.7} />
        </div>
        <div className="info-content">
          <h4>Nota</h4>
          <p>Le modifiche ai dati di riferimento influenzano tutti gli utenti del sistema. Procedere con cautela.</p>
        </div>
      </div>
    </div>
  );
}

export default DataAdmin;
