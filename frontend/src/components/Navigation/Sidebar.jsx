import { Link, useLocation } from 'react-router-dom';
import { useNavigation } from '../../contexts/NavigationContext';
import NavigationItem from './NavigationItem';
import './Sidebar.css';

/**
 * Sidebar - Main navigation sidebar (desktop ≥768px)
 *
 * Features:
 * - 250px width when expanded, 60px when collapsed
 * - Hierarchical menu from backend API
 * - Context-aware: mostra solo funzioni del modulo corrente
 * - Collapsible with localStorage persistence
 * - Active route highlighting
 * - WCAG Level AA accessible
 */

function Sidebar() {
  const { sidebarOpen, menuItems, menuLoading, menuError, loadMenu } = useNavigation();
  const location = useLocation();

  // Determina quale modulo è attivo in base al path corrente
  const getActiveModule = () => {
    // Check for /modules/:moduleName pattern
    const moduleMatch = location.pathname.match(/\/modules\/([^/]+)/);
    if (moduleMatch) return moduleMatch[1];

    // Check for specific module routes by path
    const path = location.pathname;

    // Platform admin routes - return 'platform' to show only platform items
    if (path.startsWith('/admin/') ||
        path.startsWith('/modules') ||
        path.startsWith('/settings') ||
        path.startsWith('/users') ||
        path === '/dashboard' ||
        path === '/') {
      return 'platform';
    }

    // Anagrafica Italiana module routes
    if (path.startsWith('/anagrafiche')) return 'anagrafica_italiana';

    // Immobili module routes
    if (path.startsWith('/unita-immobiliari') ||
        path.startsWith('/terreni') ||
        path.startsWith('/proprietari') ||
        path.startsWith('/condomini') ||
        path.startsWith('/certificati-energetici') ||
        path.startsWith('/tabelle-millesimali') ||
        path.startsWith('/millesimi-immobile') ||
        path.startsWith('/categorie-catastali') ||
        path.startsWith('/tipologie-terreno')) {
      return 'immobili';
    }

    // Affitti Lungo module routes
    if (path.startsWith('/affittuari') ||
        path.startsWith('/contratti') ||
        path.startsWith('/spese') ||
        path.startsWith('/incassi') ||
        path.startsWith('/tecnici')) {
      return 'affitti_lungo';
    }

    // Test pages - show platform menu
    if (path.startsWith('/test/')) {
      return 'platform';
    }

    return null;
  };

  const activeModule = getActiveModule();

  // Hide sidebar for test pages and standalone pages
  if (activeModule === 'none' || activeModule === null) {
    return null;
  }

  // Filtra menu items per mostrare solo quelli del modulo corrente
  const filteredMenuItems = menuItems.filter(
    item => item.module_id === activeModule || item.module_id === 'platform'
  );

  // Separa menu items normali da domain data, escludendo l'amministrazione duplicata
  const regularItems = filteredMenuItems.filter(
    item => !item.is_domain_data && item.id !== 'platform.admin' && item.parent_id !== 'platform.admin'
  );
  const domainDataItems = filteredMenuItems.filter(item => item.is_domain_data);

  // Don't render on mobile (< 768px)
  if (typeof window !== 'undefined' && window.innerWidth < 768) {
    return null;
  }

  return (
    <aside
      className={`sidebar ${sidebarOpen ? 'sidebar-open' : 'sidebar-collapsed'}`}
      role="navigation"
      aria-label="Main navigation"
    >
      <nav className="sidebar-nav">
        {menuLoading && (
          <div className="sidebar-loading">
            <div className="loading-spinner" aria-label="Caricamento menu..."></div>
            {sidebarOpen && <span>Caricamento...</span>}
          </div>
        )}

        {menuError && (
          <div className="sidebar-error">
            {sidebarOpen && (
              <>
                <p>Errore caricamento menu</p>
                <button onClick={loadMenu} className="retry-btn">
                  Riprova
                </button>
              </>
            )}
            {!sidebarOpen && <span>⚠️</span>}
          </div>
        )}

        {!menuLoading && !menuError && (
          <ul className="sidebar-menu" role="menu">
            {/* Menu items normali */}
            {regularItems.map((item) => (
              <NavigationItem
                key={item.id}
                item={item}
                collapsed={!sidebarOpen}
                currentPath={location.pathname}
              />
            ))}

            {/* Separatore Domini (se ci sono domain data items) */}
            {domainDataItems.length > 0 && (
              <>
                <li className="menu-separator" role="separator">
                  {sidebarOpen && <span className="separator-label">Domini</span>}
                  {!sidebarOpen && <hr className="separator-line" />}
                </li>

                {/* Domain data items */}
                {domainDataItems.map((item) => (
                  <NavigationItem
                    key={item.id}
                    item={item}
                    collapsed={!sidebarOpen}
                    currentPath={location.pathname}
                  />
                ))}
              </>
            )}
          </ul>
        )}
      </nav>
    </aside>
  );
}

export default Sidebar;
