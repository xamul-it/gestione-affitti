/**
 * Module Loader Hook
 *
 * Loads modules from two sources:
 * 1. Local frontend modules with manifest.js files (new modular approach)
 * 2. Backend API for backward compatibility (legacy modules)
 *
 * Should be called once at app bootstrap.
 */
import { useEffect, useState } from 'react';
import moduleRegistry from './ModuleRegistry';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

/**
 * Dynamically import local frontend modules
 * This uses Vite's import.meta.glob feature for dynamic imports
 */
async function loadLocalModules() {
  console.log('[ModuleLoader] Loading local frontend modules...');

  const modules = [];

  try {
    // Dynamically import all manifest files from modules directory
    // NOTE: import.meta.glob is a Vite-specific feature
    const manifestModules = import.meta.glob('/src/modules/*/manifest.js');

    for (const path in manifestModules) {
      try {
        const manifestModule = await manifestModules[path]();
        const manifest = manifestModule.manifest || manifestModule.default;

        if (manifest && manifest.enabled !== false) {
          console.log(`[ModuleLoader] Discovered local module: ${manifest.id}`);
          modules.push({
            source: 'local',
            technical_name: manifest.id,
            name: manifest.displayName || manifest.name,
            version: manifest.version,
            enabled: manifest.enabled !== false,
            routes: manifest.routes || [],
            menu_items: manifest.menuItems || [],
            widgets: manifest.widgets || [],
            dependencies: manifest.dependencies || [],
            permissions: manifest.permissions || [],
            config: manifest.config || {},
          });
        }
      } catch (err) {
        console.error(`[ModuleLoader] Failed to load manifest from ${path}:`, err);
      }
    }

    console.log(`[ModuleLoader] Loaded ${modules.length} local modules`);
  } catch (err) {
    console.error('[ModuleLoader] Failed to load local modules:', err);
  }

  return modules;
}

/**
 * Load modules from backend API (legacy support)
 */
async function loadBackendModules() {
  console.log('[ModuleLoader] Fetching modules from backend...');

  try {
    const response = await fetch(`${API_BASE_URL}/modules/enabled`);
    if (!response.ok) {
      // Backend endpoint might not exist yet - this is OK
      console.log('[ModuleLoader] Backend module API not available (404) - skipping');
      return [];
    }

    const modulesData = await response.json();
    console.log(`[ModuleLoader] Received ${modulesData.length} modules from backend`);

    return modulesData.map(module => ({
      ...module,
      source: 'backend',
    }));
  } catch (err) {
    // Network error or API not implemented - this is OK during transition
    console.log('[ModuleLoader] Backend modules unavailable:', err.message);
    return [];
  }
}

/**
 * Register a module in the ModuleRegistry
 */
function registerModule(moduleData) {
  console.log(`[ModuleLoader] Registering module: ${moduleData.technical_name} (${moduleData.source})`);

  moduleRegistry.registerModule(moduleData.technical_name, {
    name: moduleData.name,
    version: moduleData.version,
    enabled: moduleData.enabled,
  });

  // Register routes from module
  if (moduleData.routes && moduleData.routes.length > 0) {
    moduleData.routes.forEach(route => {
      moduleRegistry.registerRoute(moduleData.technical_name, route);
    });
  }

  // Register menu items from module
  if (moduleData.menu_items && moduleData.menu_items.length > 0) {
    moduleData.menu_items.forEach(menuItem => {
      moduleRegistry.registerMenuItem(moduleData.technical_name, menuItem);
    });
  }

  // Register extension points from module
  if (moduleData.extension_points && moduleData.extension_points.length > 0) {
    moduleData.extension_points.forEach(ext => {
      moduleRegistry.registerExtension(
        moduleData.technical_name,
        ext.point,
        {
          component: ext.component,
          order: ext.order,
          props: ext.props || {}
        }
      );
    });
  }
}

export function useModuleLoader() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [modules, setModules] = useState([]);

  useEffect(() => {
    async function loadModules() {
      try {
        // Load from both sources
        const [localModules, backendModules] = await Promise.all([
          loadLocalModules(),
          loadBackendModules()
        ]);

        // Merge modules (local takes precedence over backend if same technical_name)
        const allModules = [...localModules];
        const localModuleIds = new Set(localModules.map(m => m.technical_name));

        backendModules.forEach(backendModule => {
          if (!localModuleIds.has(backendModule.technical_name)) {
            allModules.push(backendModule);
          } else {
            console.log(`[ModuleLoader] Skipping backend module ${backendModule.technical_name} (local version exists)`);
          }
        });

        console.log(`[ModuleLoader] Total modules to register: ${allModules.length}`);

        // Register each module
        allModules.forEach(registerModule);

        setModules(allModules);
        setLoading(false);

        console.log('[ModuleLoader] Module loading complete');
        console.log('[ModuleLoader] Registered routes:', moduleRegistry.getRoutes());
        console.log('[ModuleLoader] Registered menu items:', moduleRegistry.getMenuItems());

      } catch (err) {
        console.error('[ModuleLoader] Failed to load modules:', err);
        setError(err.message);
        setLoading(false);
      }
    }

    loadModules();
  }, []); // Run once on mount

  return { loading, error, modules };
}
