import { Link, useNavigate } from 'react-router-dom';
import { useState, useEffect, useRef } from 'react';
import { useNavigation } from '../../contexts/NavigationContext';
import { useAuth } from '../../contexts/AuthContext';
import { useTenant } from '../../contexts/TenantContext';
import SearchBar from '../Search/SearchBar';
import ModuleTabs from '../Navigation/ModuleTabs';
import ScadenzaBadge from '../Platform/Scadenze/ScadenzaBadge';
import NotifichePanel from '../Platform/Scadenze/NotifichePanel';
import { Bug, Database, HardDrive, HelpCircle, Home, List, LogOut, Package, RefreshCw, Settings, ToggleRight, User, Users } from 'lucide-react';
import './TopBar.css';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

/**
 * TopBar - Thin utility bar (60px height)
 *
 * Contains:
 * - Hamburger menu button (mobile < 768px)
 * - Logo
 * - Search bar
 * - User menu (profile, settings, help, logout) - PLATFORM FUNCTIONS
 *
 * Responsive:
 * - Mobile: Hamburger | Logo | Search (icon) | User
 * - Desktop: Logo | Search (full) | User
 */

function TopBar() {
  const { toggleSidebar, toggleDrawer } = useNavigation();
  const { user, logout, isAuthenticated, hasPermission } = useAuth();
  const { currentTenant, availableTenants, hasMultipleTenants, clearTenantContext, switchTenant } = useTenant();
  const navigate = useNavigate();
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const [notificheOpen, setNotificheOpen] = useState(false);
  const [debugOpen, setDebugOpen] = useState(false);
  const [debugMenuOpen, setDebugMenuOpen] = useState(false);
  const [tenantMenuOpen, setTenantMenuOpen] = useState(false);
  const [debugView, setDebugView] = useState('access');
  const [modulePermissions, setModulePermissions] = useState([]);
  const [modulePermsLoading, setModulePermsLoading] = useState(false);
  const [modulePermsError, setModulePermsError] = useState(null);
  const dropdownRef = useRef(null);
  const debugRef = useRef(null);
  const tenantRef = useRef(null);

  // Detect if mobile (< 768px)
  const isMobile = window.innerWidth < 768;

  const handleMenuToggle = () => {
    if (isMobile) {
      toggleDrawer();
    } else {
      toggleSidebar();
    }
  };

  const toggleDropdown = () => {
    setDropdownOpen(prev => !prev);
  };

  const toggleTenantMenu = () => {
    setTenantMenuOpen(prev => !prev);
  };

  const decodeTokenPayload = (token) => {
    if (!token) return null;
    try {
      const payload = token.split('.')[1];
      if (!payload) return null;
      const normalized = payload.replace(/-/g, '+').replace(/_/g, '/');
      return JSON.parse(atob(normalized));
    } catch (err) {
      console.error('Failed to decode token payload:', err);
      return null;
    }
  };

  const copyToClipboard = async (text) => {
    if (!text) return;
    try {
      await navigator.clipboard.writeText(text);
      alert('Copiato negli appunti.');
    } catch (err) {
      console.error('Clipboard write failed:', err);
      alert('Impossibile copiare. Seleziona e copia manualmente.');
    }
  };

  const loadModulePermissions = async () => {
    try {
      setModulePermsLoading(true);
      setModulePermsError(null);
      const token = localStorage.getItem('access_token');
      const response = await fetch(`${API_BASE_URL}/modules/enabled`, {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      const data = await response.json();
      setModulePermissions(Array.isArray(data) ? data : []);
    } catch (err) {
      console.error('Failed to load module permissions:', err);
      setModulePermsError(err.message || 'Errore nel caricamento');
    } finally {
      setModulePermsLoading(false);
    }
  };

  const handleRefreshComuni = async () => {
    const proceed = window.confirm(
      "Aggiornare l'elenco dei comuni da fonte esterna?\n\n" +
      "L'operazione può richiedere qualche minuto."
    );
    if (!proceed) return;

    try {
      setDebugMenuOpen(false);
      const token = localStorage.getItem('access_token');
      const response = await fetch(`${API_BASE_URL}/anagrafica/domini/comuni/refresh`, {
        method: 'POST',
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      const data = await response.json();
      alert(
        `Aggiornamento comuni completato.\n\n` +
        `Totale fonte: ${data.source_rows}\n` +
        `Creati: ${data.created}\n` +
        `Aggiornati: ${data.updated}\n` +
        `Riattivati: ${data.reactivated}\n` +
        `Disattivati: ${data.deactivated}`
      );
    } catch (err) {
      console.error('Errore aggiornamento comuni:', err);
      alert('Errore durante aggiornamento comuni.');
    }
  };

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setDropdownOpen(false);
      }
      if (debugRef.current && !debugRef.current.contains(event.target)) {
        setDebugMenuOpen(false);
      }
      if (tenantRef.current && !tenantRef.current.contains(event.target)) {
        setTenantMenuOpen(false);
      }
    };

    if (dropdownOpen || debugMenuOpen || tenantMenuOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [dropdownOpen, debugMenuOpen, tenantMenuOpen]);

  // Close dropdown on ESC key
  useEffect(() => {
    const handleEscape = (event) => {
      if (event.key === 'Escape' && dropdownOpen) {
        setDropdownOpen(false);
      }
    };

    if (dropdownOpen) {
      document.addEventListener('keydown', handleEscape);
    }

    return () => {
      document.removeEventListener('keydown', handleEscape);
    };
  }, [dropdownOpen]);

  useEffect(() => {
    if (debugOpen && debugView === 'module-permissions') {
      loadModulePermissions();
    }
  }, [debugOpen, debugView]);

  return (
    <header className="top-bar" role="banner">
      <div className="top-bar-container">
        {/* Hamburger/Toggle Button */}
        <button
          className="top-bar-toggle"
          onClick={handleMenuToggle}
          aria-label={isMobile ? "Apri menu" : "Espandi/Riduci sidebar"}
          aria-expanded={false}
        >
          <span className="hamburger-icon">
            <span></span>
            <span></span>
            <span></span>
          </span>
        </button>

        {/* Logo */}
        <Link to="/" className="top-bar-logo" aria-label="Home">
          <span className="logo-icon" aria-hidden="true">
            <Home size={20} />
          </span>
          <span className="logo-text">Home</span>
        </Link>

        {/* Module Tabs */}
        {isAuthenticated && <ModuleTabs />}

        {/* Search Bar */}
        <div className="top-bar-search">
          <SearchBar />
        </div>

        {/* Active Tenant */}
        {isAuthenticated && currentTenant && (
          <div className="topbar-switcher" ref={tenantRef} title={`Database attivo: ${currentTenant.nome_display}`}>
            <button
              type="button"
              className="topbar-switcher-button"
              onClick={toggleTenantMenu}
              aria-haspopup="true"
              aria-expanded={tenantMenuOpen}
            >
              <span className="topbar-switcher-icon" aria-hidden="true">
                <HardDrive size={16} />
              </span>
              <span className="topbar-switcher-label">
                {currentTenant.nome_display}
              </span>
            </button>
            <button
              type="button"
              className="topbar-switcher-caret"
              onClick={(event) => {
                event.stopPropagation();
                toggleTenantMenu();
              }}
              aria-label="Apri menu database"
              aria-expanded={tenantMenuOpen}
            >
              <span className={`topbar-switcher-caret-icon ${tenantMenuOpen ? 'open' : ''}`} aria-hidden="true">
                ▼
              </span>
            </button>

            {tenantMenuOpen && (
              <div className="topbar-switcher-menu" role="menu">
                {availableTenants.length === 0 && (
                  <div className="topbar-switcher-empty">Nessun database</div>
                )}
                {availableTenants.map((tenant) => (
                  <button
                    key={tenant.id}
                    type="button"
                    className={`topbar-switcher-item ${tenant.id === currentTenant.id ? 'active' : ''}`}
                    role="menuitem"
                    onClick={() => {
                      setTenantMenuOpen(false);
                      if (tenant.id !== currentTenant.id) {
                        switchTenant(tenant.id);
                      }
                    }}
                  >
                    <span className="topbar-switcher-item-icon" aria-hidden="true">
                      <HardDrive size={14} />
                    </span>
                    <span className="topbar-switcher-item-label">{tenant.nome_display}</span>
                  </button>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Scadenze Badge */}
        {isAuthenticated && (
          <div className="top-bar-scadenze">
            <ScadenzaBadge
              autoLoad={true}
              onClick={() => setNotificheOpen(!notificheOpen)}
            />
          </div>
        )}

        {isAuthenticated && (
          <div className="topbar-switcher" ref={debugRef}>
            <button
              className="topbar-switcher-button"
              onClick={() => setDebugMenuOpen(prev => !prev)}
              aria-haspopup="true"
              aria-expanded={debugMenuOpen}
            >
              <span className="topbar-switcher-icon" aria-hidden="true">
                <Bug size={16} />
              </span>
              <span className="topbar-switcher-label">Debug</span>
            </button>
            <button
              type="button"
              className="topbar-switcher-caret"
              onClick={(event) => {
                event.stopPropagation();
                setDebugMenuOpen(prev => !prev);
              }}
              aria-label="Apri menu debug"
              aria-expanded={debugMenuOpen}
            >
              <span className={`topbar-switcher-caret-icon ${debugMenuOpen ? 'open' : ''}`} aria-hidden="true">
                ▼
              </span>
            </button>
            {debugMenuOpen && (
              <div className="topbar-switcher-menu" role="menu">
                <button
                  className="topbar-switcher-item"
                  onClick={() => {
                    setDebugView('access');
                    setDebugMenuOpen(false);
                    setDebugOpen(true);
                  }}
                  role="menuitem"
                >
                  Token
                </button>
                <button
                  className="topbar-switcher-item"
                  onClick={() => {
                    setDebugView('module-permissions');
                    setDebugMenuOpen(false);
                    setDebugOpen(true);
                  }}
                  role="menuitem"
                >
                  Permessi moduli
                </button>
                <Link
                  to="/admin/roles-debug"
                  className="topbar-switcher-item"
                  onClick={() => setDebugMenuOpen(false)}
                  role="menuitem"
                >
                  Debug ruoli
                </Link>
                <Link
                  to="/admin/document-parsing-debug"
                  className="topbar-switcher-item"
                  onClick={() => setDebugMenuOpen(false)}
                  role="menuitem"
                >
                  Debug parsing documenti
                </Link>
                <Link
                  to="/admin/tenant-maintenance"
                  className="topbar-switcher-item"
                  onClick={() => setDebugMenuOpen(false)}
                  role="menuitem"
                >
                  Reset tenant
                </Link>
                <Link
                  to="/admin/core-cleanup"
                  className="topbar-switcher-item"
                  onClick={() => setDebugMenuOpen(false)}
                  role="menuitem"
                >
                  Pulizia core
                </Link>
                {(user?.is_superuser || hasPermission('platform.admin')) && (
                  <button
                    className="topbar-switcher-item"
                    onClick={handleRefreshComuni}
                    role="menuitem"
                  >
                    Aggiorna comuni
                  </button>
                )}
                <button
                  className="topbar-switcher-item"
                  onClick={() => {
                    setDebugMenuOpen(false);
                    localStorage.removeItem('access_token');
                    window.location.reload();
                  }}
                  role="menuitem"
                >
                  Cancella Access Token
                </button>
              </div>
            )}
          </div>
        )}

        {/* User Menu - PLATFORM FUNCTIONS */}
        {isAuthenticated && (
          <div className="top-bar-user" ref={dropdownRef}>
            <button
              className="user-menu-button"
              onClick={toggleDropdown}
              aria-label="Menu utente"
              aria-haspopup="true"
              aria-expanded={dropdownOpen}
            >
              <span className="user-avatar" aria-hidden="true">
                {user?.username?.[0]?.toUpperCase() || '👤'}
              </span>
              <span className="user-name">{user?.username || 'User'}</span>
              <span className={`user-dropdown-arrow ${dropdownOpen ? 'open' : ''}`} aria-hidden="true">▼</span>
            </button>

            {/* User Dropdown - Platform Functions */}
            {dropdownOpen && (
              <div className="user-dropdown" role="menu">
                <Link
                  to="/profile"
                  className="user-dropdown-item"
                  onClick={() => setDropdownOpen(false)}
                  role="menuitem"
                >
                  <span className="dropdown-icon" aria-hidden="true"><User size={16} /></span>
                  Profilo
                </Link>
                <Link
                  to="/settings"
                  className="user-dropdown-item"
                  onClick={() => setDropdownOpen(false)}
                  role="menuitem"
                >
                  <span className="dropdown-icon" aria-hidden="true"><Settings size={16} /></span>
                  Impostazioni
                </Link>
                <hr className="user-dropdown-divider" />

                {/* Tenant Information */}
                {currentTenant && (
                  <>
                    <div className="user-dropdown-item tenant-info">
                      <span className="dropdown-icon" aria-hidden="true"><HardDrive size={16} /></span>
                      <div className="tenant-info-content">
                        <span className="tenant-info-label">Database:</span>
                        <span className="tenant-info-name">{currentTenant.nome_display}</span>
                      </div>
                    </div>
                    <button
                      onClick={() => {
                        setDropdownOpen(false);
                        navigate('/tenant-select');
                      }}
                      className="user-dropdown-item user-dropdown-item-left"
                      role="menuitem"
                    >
                      <span className="dropdown-icon" aria-hidden="true"><RefreshCw size={16} /></span>
                      {hasMultipleTenants() ? 'Cambia Database' : 'Impostazioni Database'}
                    </button>
                    {(user?.is_superuser || hasPermission('platform.admin')) && (
                      <Link
                        to="/admin/database"
                        className="user-dropdown-item"
                        onClick={() => setDropdownOpen(false)}
                        role="menuitem"
                      >
                        <span className="dropdown-icon" aria-hidden="true"><Database size={16} /></span>
                        Gestione Database
                      </Link>
                    )}
                    <hr className="user-dropdown-divider" />
                  </>
                )}

                {(user?.is_superuser || hasPermission('platform.admin') || hasPermission('tenant.admin')) && (
                  <>
                    {(user?.is_superuser || hasPermission('platform.admin')) && (
                      <Link
                        to="/admin/modules"
                        className="user-dropdown-item"
                        onClick={() => setDropdownOpen(false)}
                        role="menuitem"
                      >
                        <span className="dropdown-icon" aria-hidden="true"><Package size={16} /></span>
                        Gestione Moduli
                      </Link>
                    )}
                    {(user?.is_superuser || hasPermission('tenant.admin')) && (
                      <Link
                        to="/tenant/modules"
                        className="user-dropdown-item"
                        onClick={() => setDropdownOpen(false)}
                        role="menuitem"
                      >
                        <span className="dropdown-icon" aria-hidden="true"><ToggleRight size={16} /></span>
                        Abilitazione Moduli
                      </Link>
                    )}
                    {(user?.is_superuser || hasPermission('platform.admin')) && (
                      <Link
                        to="/admin/users"
                        className="user-dropdown-item"
                        onClick={() => setDropdownOpen(false)}
                        role="menuitem"
                      >
                        <span className="dropdown-icon" aria-hidden="true"><Users size={16} /></span>
                        Utenti e Permessi
                      </Link>
                    )}
                    {(user?.is_superuser || hasPermission('platform.admin')) && (
                      <Link
                        to="/admin/parsing-services"
                        className="user-dropdown-item"
                        onClick={() => setDropdownOpen(false)}
                        role="menuitem"
                      >
                        <span className="dropdown-icon" aria-hidden="true"><Settings size={16} /></span>
                        Servizi Parsing
                      </Link>
                    )}
                    {(user?.is_superuser || hasPermission('platform.admin')) && (
                      <Link
                        to="/admin/data"
                        className="user-dropdown-item"
                        onClick={() => setDropdownOpen(false)}
                        role="menuitem"
                      >
                        <span className="dropdown-icon" aria-hidden="true"><List size={16} /></span>
                        Amministrazione Dati
                      </Link>
                    )}
                    <hr className="user-dropdown-divider" />
                  </>
                )}
                <Link
                  to="/help"
                  className="user-dropdown-item"
                  onClick={() => setDropdownOpen(false)}
                  role="menuitem"
                >
                  <span className="dropdown-icon" aria-hidden="true"><HelpCircle size={16} /></span>
                  Aiuto
                </Link>
                <hr className="user-dropdown-divider" />
                <button
                  onClick={() => {
                    setDropdownOpen(false);
                    logout(clearTenantContext);
                  }}
                  className="user-dropdown-item user-dropdown-item-left logout-button"
                  role="menuitem"
                >
                  <span className="dropdown-icon" aria-hidden="true"><LogOut size={16} /></span>
                  Logout
                </button>
              </div>
            )}
          </div>
        )}

        {/* Login button if not authenticated */}
        {!isAuthenticated && (
          <Link to="/login" className="top-bar-login-btn">
            Login
          </Link>
        )}
      </div>

      {/* Notifiche Panel */}
      <NotifichePanel
        isOpen={notificheOpen}
        onClose={() => setNotificheOpen(false)}
      />

      {debugOpen && (
        <div className="debug-overlay" onClick={() => setDebugOpen(false)}>
          <div className="debug-modal" onClick={(e) => e.stopPropagation()}>
            <h3>{debugView === 'module-permissions' ? 'Permessi moduli' : 'Debug Token'}</h3>
            <p className="debug-help">
              {debugView === 'module-permissions'
                ? 'Elenco dei permessi dichiarati dai moduli abilitati per il tenant corrente.'
                : 'Mostra i payload decodificati dei token JWT.'}
            </p>
            {debugView === 'module-permissions' ? (
              <>
                {modulePermsLoading && <p>Caricamento permessi moduli...</p>}
                {modulePermsError && <p className="debug-error">Errore: {modulePermsError}</p>}
                {!modulePermsLoading && !modulePermsError && (
                  <div className="debug-section">
                    <div className="debug-title">Moduli e permessi</div>
                    <div className="debug-box">
                      {modulePermissions.length === 0 && (
                        <div>Nessun modulo restituito.</div>
                      )}
                      {modulePermissions.map((module) => {
                        const permissions = Array.isArray(module.permissions)
                          ? module.permissions
                          : [];
                        return (
                          <div key={module.technical_name} style={{ marginBottom: '12px' }}>
                            <strong>{module.name || module.technical_name}</strong>
                            <div style={{ fontSize: '12px', color: '#666', marginBottom: '4px' }}>
                              {module.technical_name}
                            </div>
                            {permissions.length === 0 ? (
                              <div>Nessun permesso dichiarato.</div>
                            ) : (
                              <ul>
                                {permissions.map((perm, index) => {
                                  const code = perm.code || perm.name || perm.permission || '';
                                  const label = perm.description || perm.name || perm.code || '';
                                  return (
                                    <li key={`${code}-${index}`}>
                                      {code}{label && label !== code ? ` - ${label}` : ''}
                                    </li>
                                  );
                                })}
                              </ul>
                            )}
                          </div>
                        );
                      })}
                    </div>
                  </div>
                )}
              </>
            ) : debugView === 'refresh' ? (
              <>
                <div className="debug-section">
                  <div className="debug-title">Refresh Token</div>
                  <pre className="debug-box">
                    {JSON.stringify(decodeTokenPayload(localStorage.getItem('refresh_token')), null, 2) || 'N/D'}
                  </pre>
                  <div className="debug-actions">
                    <button
                      className="btn btn-secondary btn-sm"
                      onClick={() => copyToClipboard(
                        JSON.stringify(decodeTokenPayload(localStorage.getItem('refresh_token')), null, 2)
                      )}
                    >
                      Copia
                    </button>
                  </div>
                </div>
                <div className="debug-section">
                  <div className="debug-title">Access Token</div>
                  <pre className="debug-box">
                    {JSON.stringify(decodeTokenPayload(localStorage.getItem('access_token')), null, 2) || 'N/D'}
                  </pre>
                  <div className="debug-actions">
                    <button
                      className="btn btn-secondary btn-sm"
                      onClick={() => copyToClipboard(
                        JSON.stringify(decodeTokenPayload(localStorage.getItem('access_token')), null, 2)
                      )}
                    >
                      Copia
                    </button>
                  </div>
                </div>
              </>
            ) : (
              <>
                <div className="debug-section">
                  <div className="debug-title">Access Token</div>
                  <pre className="debug-box">
                    {JSON.stringify(decodeTokenPayload(localStorage.getItem('access_token')), null, 2) || 'N/D'}
                  </pre>
                  <div className="debug-actions">
                    <button
                      className="btn btn-secondary btn-sm"
                      onClick={() => copyToClipboard(
                        JSON.stringify(decodeTokenPayload(localStorage.getItem('access_token')), null, 2)
                      )}
                    >
                      Copia
                    </button>
                  </div>
                </div>
                <div className="debug-section">
                  <div className="debug-title">Refresh Token</div>
                  <pre className="debug-box">
                    {JSON.stringify(decodeTokenPayload(localStorage.getItem('refresh_token')), null, 2) || 'N/D'}
                  </pre>
                  <div className="debug-actions">
                    <button
                      className="btn btn-secondary btn-sm"
                      onClick={() => copyToClipboard(
                        JSON.stringify(decodeTokenPayload(localStorage.getItem('refresh_token')), null, 2)
                      )}
                    >
                      Copia
                    </button>
                  </div>
                </div>
              </>
            )}
            <div className="debug-actions">
              <button className="btn btn-primary btn-sm" onClick={() => setDebugOpen(false)}>
                Chiudi
              </button>
            </div>
          </div>
        </div>
      )}
    </header>
  );
}

export default TopBar;
