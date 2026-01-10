import { useState, useEffect, useRef } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { renderIcon } from './iconRegistry.jsx';
import './ModuleTabs.css';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

/**
 * ModuleTabs - Tab orizzontali per switching tra moduli
 *
 * Mostra i moduli abilitati come tab nella TopBar
 * Permette di passare rapidamente tra i moduli
 */
function ModuleTabs() {
  const [modules, setModules] = useState([]);
  const [loading, setLoading] = useState(true);
  const [menuOpen, setMenuOpen] = useState(false);
  const location = useLocation();
  const navigate = useNavigate();
  const switcherRef = useRef(null);

  useEffect(() => {
    loadModules();
  }, []);

  const loadModules = async () => {
    try {
      const token = localStorage.getItem('access_token');
      const response = await axios.get(
        `${API_BASE_URL}/modules/enabled`,
        {
          headers: { 'Authorization': `Bearer ${token}` }
        }
      );
      setModules(response.data);
    } catch (err) {
      console.error('Error loading modules for tabs:', err);
    } finally {
      setLoading(false);
    }
  };

  // Determina quale modulo è attivo in base al path corrente
  const getActiveModule = () => {
    const match = location.pathname.match(/\/modules\/([^/]+)/);
    if (match) return match[1];

    const path = location.pathname;

    if (path.startsWith('/anagrafiche')) return 'anagrafica_italiana';
    if (
      path.startsWith('/unita-immobiliari') ||
      path.startsWith('/proprietari') ||
      path.startsWith('/condomini') ||
      path.startsWith('/certificati-energetici') ||
      path.startsWith('/tabelle-millesimali') ||
      path.startsWith('/millesimi-immobile') ||
      path.startsWith('/categorie-catastali')
    ) {
      return 'immobili';
    }
    if (
      path.startsWith('/affittuari') ||
      path.startsWith('/contratti') ||
      path.startsWith('/spese') ||
      path.startsWith('/incassi') ||
      path.startsWith('/tecnici')
    ) {
      return 'affitti_lungo';
    }
    if (
      path.startsWith('/affitti-brevi') ||
      path.startsWith('/affitti-brevi/')
    ) {
      return 'affitti_brevi';
    }

    return null;
  };

  const activeModule = getActiveModule();
  const activeModuleData = modules.find(module => module.technical_name === activeModule) || null;
  const otherModules = activeModuleData
    ? modules.filter(module => module.technical_name !== activeModuleData.technical_name)
    : modules;

  useEffect(() => {
    if (!menuOpen) {
      return;
    }

    const handleClickOutside = (event) => {
      if (switcherRef.current && !switcherRef.current.contains(event.target)) {
        setMenuOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [menuOpen]);

  if (loading || modules.length === 0) {
    return null;
  }

  return (
    <div className="module-tabs">
      <div className="module-switcher" ref={switcherRef}>
        <button
          type="button"
          className="module-switcher-button"
          onClick={() => {
            if (activeModuleData) {
              navigate(`/modules/${activeModuleData.technical_name}/dashboard`);
            } else {
              setMenuOpen(prev => !prev);
            }
          }}
          aria-haspopup="true"
          aria-expanded={menuOpen}
        >
          <span className="module-switcher-icon" aria-hidden="true">
            {renderIcon(activeModuleData?.icon || 'package', { size: 18 })}
          </span>
          <span className="module-switcher-label">
            {activeModuleData?.name || 'Seleziona modulo'}
          </span>
        </button>
        <button
          type="button"
          className="module-switcher-caret"
          onClick={(event) => {
            event.stopPropagation();
            setMenuOpen(prev => !prev);
          }}
          aria-label="Apri menu moduli"
          aria-expanded={menuOpen}
        >
          <span className={`module-switcher-caret-icon ${menuOpen ? 'open' : ''}`} aria-hidden="true">
            ▾
          </span>
        </button>

        {menuOpen && (
          <div className="module-switcher-menu" role="menu">
            {otherModules.length === 0 && (
              <div className="module-switcher-empty">Nessun altro modulo</div>
            )}
            {otherModules.map(module => (
              <Link
                key={module.technical_name}
                to={`/modules/${module.technical_name}/dashboard`}
                className="module-switcher-item"
                role="menuitem"
                onClick={() => setMenuOpen(false)}
              >
                <span className="module-switcher-item-icon" aria-hidden="true">
                  {renderIcon(module.icon || 'package', { size: 16 })}
                </span>
                <span className="module-switcher-item-label">{module.name}</span>
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export default ModuleTabs;
