import { createContext, useContext, useState, useEffect } from 'react';
import { useAuth } from './AuthContext';
import { useTenant } from './TenantContext';
import { refreshTokenSafe } from '../services/tokenService';

/**
 * NavigationContext - Centralized navigation state management
 *
 * Manages:
 * - Sidebar open/closed state (desktop)
 * - Drawer open/closed state (mobile)
 * - Menu data from backend API
 * - Active route highlighting
 * - User preferences (localStorage persistence)
 */

const NavigationContext = createContext(undefined);

export function NavigationProvider({ children }) {
  const { user } = useAuth();
  const { currentTenant } = useTenant();
  // Sidebar state (desktop) - default expanded, persisted in localStorage
  const [sidebarOpen, setSidebarOpen] = useState(() => {
    const saved = localStorage.getItem('sidebar-open');
    return saved !== null ? JSON.parse(saved) : true;
  });

  // Drawer state (mobile) - default closed
  const [drawerOpen, setDrawerOpen] = useState(false);

  // Menu data from backend
  const [menuItems, setMenuItems] = useState([]);
  const [menuLoading, setMenuLoading] = useState(true);
  const [menuError, setMenuError] = useState(null);

  // Active submenu (for accordion behavior)
  const [activeSubmenu, setActiveSubmenu] = useState(null);

  // Persist sidebar state to localStorage
  useEffect(() => {
    localStorage.setItem('sidebar-open', JSON.stringify(sidebarOpen));
  }, [sidebarOpen]);

  // Close drawer when window resizes above mobile breakpoint
  useEffect(() => {
    const handleResize = () => {
      if (window.innerWidth >= 768 && drawerOpen) {
        setDrawerOpen(false);
      }
    };

    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, [drawerOpen]);

  // Load menu from backend API when user logs in or tenant changes
  useEffect(() => {
    if (user) {
      loadMenu();
    } else {
      // Clear menu when user logs out
      setMenuItems([]);
      setMenuError(null);
    }
  }, [user, currentTenant]);

  const loadMenu = async () => {
    try {
      setMenuLoading(true);
      setMenuError(null);

      const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';
      let token = localStorage.getItem('access_token');

      let response = await fetch(`${API_BASE_URL}/platform/menu/`, {
        headers: {
          'Authorization': token ? `Bearer ${token}` : '',
        },
      });

      if (response.status === 401 || response.status === 403) {
        // Use centralized token refresh
        const newToken = await refreshTokenSafe();
        if (newToken) {
          token = newToken;
          response = await fetch(`${API_BASE_URL}/platform/menu/`, {
            headers: {
              'Authorization': `Bearer ${token}`,
            },
          });
        }
      }

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      setMenuItems(data);
    } catch (error) {
      console.error('Error loading menu:', error);
      setMenuError(error.message);
    } finally {
      setMenuLoading(false);
    }
  };

  // Toggle sidebar (desktop)
  const toggleSidebar = () => {
    setSidebarOpen(prev => !prev);
  };

  // Toggle drawer (mobile)
  const toggleDrawer = () => {
    setDrawerOpen(prev => !prev);
  };

  // Close drawer (mobile) - used when clicking outside or on link
  const closeDrawer = () => {
    setDrawerOpen(false);
  };

  // Toggle submenu (accordion behavior)
  const toggleSubmenu = (menuId) => {
    setActiveSubmenu(prev => prev === menuId ? null : menuId);
  };

  const value = {
    // Sidebar state
    sidebarOpen,
    setSidebarOpen,
    toggleSidebar,

    // Drawer state
    drawerOpen,
    setDrawerOpen,
    toggleDrawer,
    closeDrawer,

    // Menu data
    menuItems,
    menuLoading,
    menuError,
    loadMenu,

    // Submenu state
    activeSubmenu,
    toggleSubmenu,
  };

  return (
    <NavigationContext.Provider value={value}>
      {children}
    </NavigationContext.Provider>
  );
}

// Custom hook to use navigation context
export function useNavigation() {
  const context = useContext(NavigationContext);
  if (context === undefined) {
    throw new Error('useNavigation must be used within a NavigationProvider');
  }
  return context;
}

export default NavigationContext;
