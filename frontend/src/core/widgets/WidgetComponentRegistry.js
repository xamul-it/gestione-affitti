/**
 * Widget Component Registry
 *
 * Dynamic registry for widget components that maintains platform independence.
 * Modules register their widget components at load time, and the platform
 * can lazy-load them without knowing about specific modules.
 *
 * Architecture:
 * - Platform: Domain-agnostic, no hardcoded module references
 * - Modules: Register their widgets on initialization
 * - Widgets: Loaded on-demand via dynamic imports
 */
class WidgetComponentRegistry {
  constructor() {
    this.components = new Map()
    this.loaders = new Map()
    this.initialized = false
  }

  /**
   * Register a widget component loader
   * Called by modules during initialization
   *
   * @param {string} componentName - Widget component name (e.g., 'ImmobiliStatsWidget')
   * @param {string} moduleId - Module identifier (e.g., 'immobili')
   * @param {Function} loader - Lazy loader: () => import('./Component')
   */
  registerWidget(componentName, moduleId, loader) {
    if (this.loaders.has(componentName)) {
      console.warn(`[WidgetRegistry] Widget ${componentName} already registered, skipping`)
      return
    }

    this.loaders.set(componentName, { moduleId, loader })
    console.log(`[WidgetRegistry] ✅ Registered widget: ${componentName} (module: ${moduleId})`)
  }

  /**
   * Get a widget component (lazy loads if not cached)
   *
   * @param {string} componentName - Widget component name
   * @returns {Promise<Component>} React component
   * @throws {Error} If widget not found or fails to load
   */
  async getComponent(componentName) {
    // Check cache first
    if (this.components.has(componentName)) {
      return this.components.get(componentName)
    }

    // Get loader registration
    const registration = this.loaders.get(componentName)
    if (!registration) {
      throw new Error(`Widget component not registered: ${componentName}`)
    }

    try {
      console.log(`[WidgetRegistry] Loading widget: ${componentName}...`)

      // Execute dynamic import
      const module = await registration.loader()

      // Extract component (supports both default and named exports)
      const Component = module.default || module[componentName]

      if (!Component) {
        throw new Error(
          `Component export not found in module. ` +
          `Expected: default export or named export "${componentName}"`
        )
      }

      // Cache the loaded component
      this.components.set(componentName, Component)
      console.log(`[WidgetRegistry] ✅ Loaded widget: ${componentName}`)

      return Component
    } catch (error) {
      console.error(
        `[WidgetRegistry] ❌ Failed to load widget ${componentName}:`,
        error
      )
      throw new Error(
        `Failed to load widget ${componentName}: ${error.message}`
      )
    }
  }

  /**
   * Check if a widget is registered
   *
   * @param {string} componentName - Widget component name
   * @returns {boolean}
   */
  hasWidget(componentName) {
    return this.loaders.has(componentName)
  }

  /**
   * Get all registered widget names
   *
   * @returns {string[]} Array of component names
   */
  getRegisteredWidgets() {
    return Array.from(this.loaders.keys())
  }

  /**
   * Get registration info for a widget
   *
   * @param {string} componentName - Widget component name
   * @returns {{moduleId: string, loaded: boolean} | null}
   */
  getWidgetInfo(componentName) {
    const registration = this.loaders.get(componentName)
    if (!registration) return null

    return {
      moduleId: registration.moduleId,
      loaded: this.components.has(componentName)
    }
  }

  /**
   * Clear all cached components (useful for hot-reload in development)
   */
  clearCache() {
    console.log('[WidgetRegistry] Clearing component cache')
    this.components.clear()
  }

  /**
   * Get registry statistics
   *
   * @returns {{registered: number, loaded: number, modules: Set<string>}}
   */
  getStats() {
    const modules = new Set(
      Array.from(this.loaders.values()).map(reg => reg.moduleId)
    )

    return {
      registered: this.loaders.size,
      loaded: this.components.size,
      modules: modules
    }
  }
}

// Export singleton instance
const widgetRegistry = new WidgetComponentRegistry()

// Expose to window for debugging in development
if (import.meta.env.DEV) {
  window.__widgetRegistry = widgetRegistry
}

export default widgetRegistry
