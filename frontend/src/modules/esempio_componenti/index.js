/**
 * Esempio Componenti Module - Main Entry Point
 *
 * This module demonstrates the use of cross-cutting platform components:
 * - DataTable with configurable columns and column selector
 * - Import/Export functionality (CSV/Excel)
 * - Domain data (categories, priorities - shared across tenants)
 * - Tenant data (elementi - isolated per tenant)
 */

// Module manifest
import { manifest } from './manifest';
export { manifest, default as manifestDefault } from './manifest';

// Components
export { ElementiEsempioList, ElementoEsempioForm } from './components/Elementi';

// API Service
export { default as esempioAPI } from './services/esempioAPI';
export * from './services/esempioAPI';

// Default export for module loader
export default {
  manifest,
  components: {
    ElementiEsempioList: () => import('./components/Elementi/ElementiEsempioList'),
  },
};
