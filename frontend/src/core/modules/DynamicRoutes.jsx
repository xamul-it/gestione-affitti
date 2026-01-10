/**
 * Dynamic Routes Component
 *
 * Renders routes registered by modules.
 * Uses React.lazy for code splitting.
 */
import { Route } from 'react-router-dom';
import { lazy, Suspense } from 'react';
import moduleRegistry from './ModuleRegistry';

// Map of module components (will be populated by modules)
const moduleComponents = {};

/**
 * Register a module component
 * @param {string} path - Component path (e.g., '@modules/hello_module/HelloPage')
 * @param {Component} component - React component
 */
export function registerModuleComponent(path, component) {
  moduleComponents[path] = component;
  console.log(`[DynamicRoutes] Registered component: ${path}`);
}

/**
 * Get component for a route
 * @param {string} componentPath - Component path from manifest
 * @returns {Component} React component or lazy-loaded component
 */
function getComponent(componentPath) {
  // Check if component is already registered
  if (moduleComponents[componentPath]) {
    return moduleComponents[componentPath];
  }

  // For now, return a placeholder
  // In production, this would use dynamic imports
  return () => (
    <div className="module-placeholder">
      <h2>Module Component</h2>
      <p>Component: {componentPath}</p>
      <p>Component not loaded yet. Register it using registerModuleComponent()</p>
    </div>
  );
}

/**
 * Loading fallback component
 */
function LoadingFallback() {
  return (
    <div className="loading-container" style={{ padding: '20px', textAlign: 'center' }}>
      <div>Loading module...</div>
    </div>
  );
}

/**
 * Error boundary for module routes
 */
function ModuleErrorBoundary({ children, routePath }) {
  try {
    return children;
  } catch (error) {
    console.error(`[DynamicRoutes] Error loading route ${routePath}:`, error);
    return (
      <div className="error-container" style={{ padding: '20px', color: 'red' }}>
        <h3>Error Loading Module</h3>
        <p>Route: {routePath}</p>
        <p>{error.message}</p>
      </div>
    );
  }
}

/**
 * Get dynamic route components (for use inside <Routes>)
 * Returns an array of <Route> components
 */
export function getDynamicRouteComponents() {
  const routes = moduleRegistry.getRoutes();

  console.log(`[DynamicRoutes] Rendering ${routes.length} dynamic routes`);

  return routes.map((route) => {
    const Component = getComponent(route.component);

    return (
      <Route
        key={`module-route-${route.path}`}
        path={route.path}
        element={
          <ModuleErrorBoundary routePath={route.path}>
            <Suspense fallback={<LoadingFallback />}>
              <Component />
            </Suspense>
          </ModuleErrorBoundary>
        }
      />
    );
  });
}

/**
 * Render dynamic routes from registered modules
 * @deprecated Use getDynamicRouteComponents() instead for direct inclusion in <Routes>
 */
export function DynamicRoutes() {
  return getDynamicRouteComponents();
}

export default DynamicRoutes;
