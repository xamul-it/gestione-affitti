/**
 * Module Manifest: esempio_componenti
 *
 * Example Module - Demonstrates cross-cutting platform components:
 * - DataTable with configurable columns
 * - Import/Export functionality
 * - Domain data (shared across tenants)
 * - Tenant data (isolated per tenant)
 */

export const manifest = {
  // Module identification
  id: 'esempio_componenti',
  displayName: 'Esempio Componenti',
  version: '1.0.0',
  description: 'Modulo dimostrativo per esemplificare i componenti trasversali della piattaforma',

  // Module metadata
  author: 'Platform Team',
  category: 'base',
  icon: 'puzzle',

  // No dependencies - standalone module
  dependencies: [],

  // Routes provided by this module
  routes: [
    {
      path: '/esempio/elementi',
      component: 'ElementiEsempioList',
      label: 'Elementi',
      icon: 'list',
    },
    {
      path: '/esempio/categorie',
      component: 'CategorieEsempioList',
      label: 'Categorie',
      icon: 'tag',
    },
    {
      path: '/esempio/priorita',
      component: 'PrioritaEsempioList',
      label: 'Priorità',
      icon: 'alert-triangle',
    },
  ],

  // Menu items (to be registered with platform)
  menuItems: [
    {
      id: 'esempio.main',
      label: 'Esempio Componenti',
      path: '#',
      icon: 'puzzle',
      order: 100,
      children: [
        {
          id: 'esempio.elementi',
          label: 'Elementi',
          path: '/esempio/elementi',
          icon: 'list',
          order: 10,
          requiredPermission: 'esempio.view',
        },
        {
          id: 'esempio.categorie',
          label: 'Categorie',
          path: '/esempio/categorie',
          icon: 'tag',
          order: 20,
          requiredPermission: 'esempio.view',
          isDomainData: true,
        },
        {
          id: 'esempio.priorita',
          label: 'Priorità',
          path: '/esempio/priorita',
          icon: 'alert-triangle',
          order: 30,
          requiredPermission: 'esempio.view',
          isDomainData: true,
        },
      ],
    },
  ],

  // Widgets for dashboard
  widgets: [
    {
      id: 'esempio.stats',
      title: 'Statistiche Elementi',
      component: 'EsempioStatsWidget',
      defaultWidth: 4,
      defaultHeight: 3,
      category: 'stats',
      requiredPermission: 'esempio.view',
    },
  ],

  // Permissions required for this module
  permissions: [
    'esempio.view',
    'esempio.create',
    'esempio.edit',
    'esempio.delete',
    'esempio.import',
    'esempio.export',
  ],

  // Module configuration
  config: {
    enableImportExport: true,
    enableColumnSelector: true,
    defaultPageSize: 20,
  },

  // Module status
  enabled: true,
  experimental: false,
};

export default manifest;
