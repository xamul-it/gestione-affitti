import { useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import { useNavigation } from '../../contexts/NavigationContext';
import NavigationItem from './NavigationItem';
import './Drawer.css';

/**
 * Drawer - Mobile navigation drawer (< 768px)
 *
 * Features:
 * - Slide-in panel from left
 * - Full-screen overlay
 * - Closes on navigation/outside click
 * - Swipe-to-close support
 * - Accessible with keyboard navigation
 * - WCAG Level AA compliant
 */

function Drawer() {
  const { drawerOpen, closeDrawer, menuItems, menuLoading, menuError, loadMenu } = useNavigation();
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

    // Test pages - return special value to hide drawer
    if (path.startsWith('/test/')) {
      return 'none';
    }

    return null;
  };

  const activeModule = getActiveModule();

  // Hide drawer for test pages and standalone pages
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

  // Close drawer on route change
  useEffect(() => {
    if (drawerOpen) {
      closeDrawer();
    }
  }, [location.pathname]);

  // Close drawer on ESC key
  useEffect(() => {
    const handleEscape = (e) => {
      if (e.key === 'Escape' && drawerOpen) {
        closeDrawer();
      }
    };

    if (drawerOpen) {
      document.addEventListener('keydown', handleEscape);
      // Prevent body scroll when drawer is open
      document.body.style.overflow = 'hidden';
    }

    return () => {
      document.removeEventListener('keydown', handleEscape);
      document.body.style.overflow = '';
    };
  }, [drawerOpen, closeDrawer]);

  // Swipe to close functionality
  useEffect(() => {
    if (!drawerOpen) return;

    let touchStartX = 0;
    let touchEndX = 0;

    const handleTouchStart = (e) => {
      touchStartX = e.changedTouches[0].screenX;
    };

    const handleTouchEnd = (e) => {
      touchEndX = e.changedTouches[0].screenX;
      // Swipe left to close (threshold: 50px)
      if (touchStartX - touchEndX > 50) {
        closeDrawer();
      }
    };

    const drawer = document.querySelector('.drawer-panel');
    if (drawer) {
      drawer.addEventListener('touchstart', handleTouchStart);
      drawer.addEventListener('touchend', handleTouchEnd);
    }

    return () => {
      if (drawer) {
        drawer.removeEventListener('touchstart', handleTouchStart);
        drawer.removeEventListener('touchend', handleTouchEnd);
      }
    };
  }, [drawerOpen, closeDrawer]);

  // Don't render on desktop (≥ 768px)
  if (typeof window !== 'undefined' && window.innerWidth >= 768) {
    return null;
  }

  if (!drawerOpen) {
    return null;
  }

  return (
    <div className="drawer-container">
      {/* Overlay - Click to close */}
      <div
        className="drawer-overlay"
        onClick={closeDrawer}
        aria-hidden="true"
      />

      {/* Drawer Panel */}
      <aside
        className="drawer-panel"
        role="navigation"
        aria-label="Mobile navigation"
        aria-modal="true"
      >
        {/* Drawer Header */}
        <div className="drawer-header">
          <div className="drawer-logo">
            <span className="drawer-logo-icon" aria-hidden="true">🏢</span>
            <span className="drawer-logo-text">Gestione Affitti</span>
          </div>
          <button
            className="drawer-close-btn"
            onClick={closeDrawer}
            aria-label="Chiudi menu"
          >
            <span aria-hidden="true">✕</span>
          </button>
        </div>

        {/* Drawer Content */}
        <nav className="drawer-nav">
          {menuLoading && (
            <div className="drawer-loading">
              <div className="loading-spinner" aria-label="Caricamento menu..."></div>
              <span>Caricamento...</span>
            </div>
          )}

          {menuError && (
            <div className="drawer-error">
              <p>Errore caricamento menu</p>
              <button onClick={loadMenu} className="retry-btn">
                Riprova
              </button>
            </div>
          )}

          {!menuLoading && !menuError && (
            <ul className="drawer-menu" role="menu">
              {/* Menu items normali */}
              {regularItems.map((item) => (
                <NavigationItem
                  key={item.id}
                  item={item}
                  collapsed={false}
                  currentPath={location.pathname}
                />
              ))}

              {/* Separatore Domini (se ci sono domain data items) */}
              {domainDataItems.length > 0 && (
                <>
                  <li className="menu-separator" role="separator">
                    <span className="separator-label">Domini</span>
                  </li>

                  {/* Domain data items */}
                  {domainDataItems.map((item) => (
                    <NavigationItem
                      key={item.id}
                      item={item}
                      collapsed={false}
                      currentPath={location.pathname}
                    />
                  ))}
                </>
              )}
            </ul>
          )}
        </nav>

        {/* Drawer Footer (Optional) */}
        <div className="drawer-footer">
          <div className="drawer-version">
            Versione 1.0.0
          </div>
        </div>
      </aside>
    </div>
  );
}

export default Drawer;
