/**
 * Module Manifest: affitti_lungo
 *
 * Long-term Rentals Module - Manages rental contracts, tenants,
 * income, expenses, and maintenance
 */

export const manifest = {
  // Module identification
  id: 'affitti_lungo',
  displayName: 'Affitti',
  version: '1.0.0',
  description: 'Gestione affitti residenziali a lungo termine, contratti, incassi e spese',

  // Module metadata
  author: 'Affitti',
  category: 'Immobiliare',
  icon: 'file-contract',

  // Dependencies
  dependencies: ['immobili', 'anagrafica_italiana'],

  // Routes provided by this module
  routes: [
    {
      path: '/affittuari',
      component: 'AffittuariList',
      label: 'Affittuari',
      icon: 'users',
    },
    {
      path: '/contratti',
      component: 'ContrattiList',
      label: 'Contratti',
      icon: 'file-contract',
    },
    {
      path: '/incassi',
      component: 'IncassiList',
      label: 'Incassi',
      icon: 'money-bill-wave',
    },
    {
      path: '/spese',
      component: 'SpeseList',
      label: 'Spese',
      icon: 'receipt',
    },
    {
      path: '/tecnici',
      component: 'TecniciList',
      label: 'Tecnici',
      icon: 'wrench',
    },
  ],

  // Menu items (to be registered with platform)
  menuItems: [
    {
      id: 'affitti.contratti',
      label: 'Contratti',
      path: '/contratti',
      icon: 'file-contract',
      order: 10,
      requiredPermission: 'contratto.view',
    },
    {
      id: 'affitti.affittuari',
      label: 'Affittuari',
      path: '/affittuari',
      icon: 'users',
      order: 20,
      requiredPermission: 'affittuario.view',
    },
    {
      id: 'affitti.gestione',
      label: 'Gestione',
      path: '#',
      icon: 'cog',
      order: 30,
      children: [
        {
          id: 'affitti.incassi',
          label: 'Incassi',
          path: '/incassi',
          order: 1,
          requiredPermission: 'incasso.view',
        },
        {
          id: 'affitti.spese',
          label: 'Spese',
          path: '/spese',
          order: 2,
          requiredPermission: 'spesa.view',
        },
        {
          id: 'affitti.tecnici',
          label: 'Tecnici',
          path: '/tecnici',
          order: 3,
          requiredPermission: 'tecnico.view',
        },
      ],
    },
  ],

  // Widgets for dashboard
  widgets: [
    {
      id: 'affitti.contratti_scadenza',
      title: 'Contratti in Scadenza',
      component: 'ContrattiScadenzaWidget',
      defaultWidth: 6,
      defaultHeight: 4,
      category: 'alerts',
      requiredPermission: 'contratto.view',
    },
    {
      id: 'affitti.incassi_stats',
      title: 'Statistiche Incassi',
      component: 'IncassiStatsWidget',
      defaultWidth: 6,
      defaultHeight: 4,
      category: 'stats',
      requiredPermission: 'incasso.view',
    },
    {
      id: 'affitti.spese_mese',
      title: 'Spese del Mese',
      component: 'SpeseMeseWidget',
      defaultWidth: 6,
      defaultHeight: 4,
      category: 'stats',
      requiredPermission: 'spesa.view',
    },
  ],

  // Permissions required for this module
  permissions: [
    'affittuario.view',
    'affittuario.create',
    'affittuario.update',
    'affittuario.delete',
    'contratto.view',
    'contratto.create',
    'contratto.update',
    'contratto.delete',
    'incasso.view',
    'incasso.create',
    'incasso.update',
    'incasso.delete',
    'spesa.view',
    'spesa.create',
    'spesa.update',
    'spesa.delete',
    'tecnico.view',
    'tecnico.create',
    'tecnico.update',
    'tecnico.delete',
    'documento.view',
    'documento.create',
    'documento.update',
    'documento.delete',
  ],

  // Module configuration
  config: {
    enableMonthlyIncassoGeneration: true,
    enableAutomaticExpenseDistribution: true,
    defaultContractDuration: 48, // months
    notifyContractExpiryDays: 90,
    enableDocumentAttachments: true,
  },

  // Module status
  enabled: true,
  experimental: false,
};

export default manifest;
