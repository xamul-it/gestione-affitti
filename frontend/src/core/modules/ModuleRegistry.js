/**
 * Frontend Module Registry
 *
 * Manages frontend module registration and retrieval.
 * Mirrors the backend module system for frontend components.
 *
 * Features:
 * - Dynamic route registration
 * - Extension point system
 * - Menu item registration
 * - Component lazy loading
 */

class ModuleRegistry {
  constructor() {
    this.modules = new Map();
    this.routes = [];
    this.menuItems = [];
    this.extensionPoints = new Map();
    this.hooks = new Map();
  }

  /**
   * Register a module
   * @param {string} technicalName - Module technical name (e.g., 'hello_module')
   * @param {Object} config - Module configuration
   */
  registerModule(technicalName, config) {
    if (this.modules.has(technicalName)) {
      console.warn(`Module '${technicalName}' is already registered`);
      return;
    }

    this.modules.set(technicalName, {
      technicalName,
      name: config.name,
      version: config.version,
      enabled: config.enabled !== false,
      routes: config.routes || [],
      menuItems: config.menuItems || [],
      extensionPoints: config.extensionPoints || {},
      components: config.components || {},
    });

    console.log(`[ModuleRegistry] Registered module: ${technicalName}`);
  }

  /**
   * Register a route from a module
   * @param {string} moduleName - Module technical name
   * @param {Object} route - Route configuration { path, component, exact }
   */
  registerRoute(moduleName, route) {
    if (!this.modules.has(moduleName)) {
      console.error(`Cannot register route: module '${moduleName}' not found`);
      return;
    }

    const routeConfig = {
      ...route,
      moduleName,
    };

    this.routes.push(routeConfig);
    console.log(`[ModuleRegistry] Registered route: ${route.path} (${moduleName})`);
  }

  /**
   * Register a menu item from a module
   * @param {string} moduleName - Module technical name
   * @param {Object} menuItem - Menu item configuration { label, path, icon, order }
   */
  registerMenuItem(moduleName, menuItem) {
    if (!this.modules.has(moduleName)) {
      console.error(`Cannot register menu item: module '${moduleName}' not found`);
      return;
    }

    const menuConfig = {
      ...menuItem,
      moduleName,
      order: menuItem.order || 100,
    };

    this.menuItems.push(menuConfig);
    // Sort by order
    this.menuItems.sort((a, b) => a.order - b.order);

    console.log(`[ModuleRegistry] Registered menu item: ${menuItem.label} (${moduleName})`);
  }

  /**
   * Register an extension point component
   * @param {string} moduleName - Module technical name
   * @param {string} extensionPoint - Extension point name (e.g., 'immobile.detail.tabs')
   * @param {Object} component - Component configuration { component, order, props }
   */
  registerExtension(moduleName, extensionPoint, component) {
    if (!this.modules.has(moduleName)) {
      console.error(`Cannot register extension: module '${moduleName}' not found`);
      return;
    }

    if (!this.extensionPoints.has(extensionPoint)) {
      this.extensionPoints.set(extensionPoint, []);
    }

    const extensions = this.extensionPoints.get(extensionPoint);
    extensions.push({
      ...component,
      moduleName,
      order: component.order || 100,
    });

    // Sort by order
    extensions.sort((a, b) => a.order - b.order);

    console.log(`[ModuleRegistry] Registered extension: ${extensionPoint} (${moduleName})`);
  }

  /**
   * Register a hook callback
   * @param {string} moduleName - Module technical name
   * @param {string} hookName - Hook name (e.g., 'beforeSave', 'afterLoad')
   * @param {Function} callback - Hook callback function
   */
  registerHook(moduleName, hookName, callback) {
    if (!this.hooks.has(hookName)) {
      this.hooks.set(hookName, []);
    }

    this.hooks.get(hookName).push({
      moduleName,
      callback,
    });

    console.log(`[ModuleRegistry] Registered hook: ${hookName} (${moduleName})`);
  }

  /**
   * Execute hooks
   * @param {string} hookName - Hook name
   * @param {Object} data - Data to pass to hooks
   * @returns {Object} Modified data
   */
  async executeHooks(hookName, data) {
    const hooks = this.hooks.get(hookName) || [];
    let result = data;

    for (const hook of hooks) {
      try {
        result = await hook.callback(result);
      } catch (error) {
        console.error(`[ModuleRegistry] Hook error (${hookName}, ${hook.moduleName}):`, error);
      }
    }

    return result;
  }

  /**
   * Get all registered routes
   * @returns {Array} Array of route configurations
   */
  getRoutes() {
    return this.routes.filter(route => {
      const module = this.modules.get(route.moduleName);
      return module && module.enabled;
    });
  }

  /**
   * Get all registered menu items
   * @returns {Array} Array of menu item configurations
   */
  getMenuItems() {
    return this.menuItems.filter(item => {
      const module = this.modules.get(item.moduleName);
      return module && module.enabled;
    });
  }

  /**
   * Get extensions for a specific extension point
   * @param {string} extensionPoint - Extension point name
   * @returns {Array} Array of extension configurations
   */
  getExtensions(extensionPoint) {
    const extensions = this.extensionPoints.get(extensionPoint) || [];
    return extensions.filter(ext => {
      const module = this.modules.get(ext.moduleName);
      return module && module.enabled;
    });
  }

  /**
   * Get a module by technical name
   * @param {string} technicalName - Module technical name
   * @returns {Object|null} Module configuration or null
   */
  getModule(technicalName) {
    return this.modules.get(technicalName) || null;
  }

  /**
   * Get all enabled modules
   * @returns {Array} Array of enabled modules
   */
  getEnabledModules() {
    return Array.from(this.modules.values()).filter(m => m.enabled);
  }

  /**
   * Enable a module
   * @param {string} technicalName - Module technical name
   */
  enableModule(technicalName) {
    const module = this.modules.get(technicalName);
    if (module) {
      module.enabled = true;
      console.log(`[ModuleRegistry] Enabled module: ${technicalName}`);
    }
  }

  /**
   * Disable a module
   * @param {string} technicalName - Module technical name
   */
  disableModule(technicalName) {
    const module = this.modules.get(technicalName);
    if (module) {
      module.enabled = false;
      console.log(`[ModuleRegistry] Disabled module: ${technicalName}`);
    }
  }

  /**
   * Clear all registrations (for testing)
   */
  clear() {
    this.modules.clear();
    this.routes = [];
    this.menuItems = [];
    this.extensionPoints.clear();
    this.hooks.clear();
  }
}

// Export singleton instance
const moduleRegistry = new ModuleRegistry();
export default moduleRegistry;
