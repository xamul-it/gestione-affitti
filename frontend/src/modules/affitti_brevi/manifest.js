/**
 * Module Manifest: affitti_brevi
 *
 * Short-Term Rentals Module - Manages short-term bookings, iCal synchronization,
 * multi-platform calendar, tourist tax, and legal deadlines
 */

export const manifest = {
  // Module identification
  id: 'affitti_brevi',
  displayName: 'Affitti Brevi',
  version: '1.0.0',
  description: 'Gestione affitti brevi con sincronizzazione iCal, calendario multi-piattaforma, calcolo tassa di soggiorno e scadenze legali',

  // Module metadata
  author: 'Gestione Affitti',
  category: 'Immobiliare',
  icon: 'calendar-alt',

  // Dependencies
  dependencies: ['immobili', 'anagrafica_italiana'],

  // Routes provided by this module
  routes: [
    {
      path: '/affitti-brevi/calendario',
      component: 'CalendarioMultiPiattaforma',
      label: 'Calendario',
      icon: 'calendar',
    },
    {
      path: '/affitti-brevi/prenotazioni',
      component: 'PrenotazioniList',
      label: 'Prenotazioni',
      icon: 'calendar-check',
    },
    {
      path: '/affitti-brevi/calendari',
      component: 'CalendariList',
      label: 'Calendari iCal',
      icon: 'calendar-alt',
    },
    // Phase 4: Tourist Tax
    {
      path: '/affitti-brevi/tasse',
      component: 'TassaConfigList',
      label: 'Tasse Soggiorno',
      icon: 'euro-sign',
    },
    {
      path: '/affitti-brevi/comunicazioni/:id',
      component: 'ComunicazioneDetail',
      label: 'Comunicazione',
      hideFromMenu: true,
    },
  ],

  // Menu items (to be registered with platform)
  menuItems: [
    {
      id: 'affitti_brevi.calendario',
      label: 'Calendario',
      path: '/affitti-brevi/calendario',
      icon: 'calendar',
      order: 5,
      requiredPermission: 'affitti_brevi.view',
    },
    {
      id: 'affitti_brevi.prenotazioni',
      label: 'Prenotazioni',
      path: '/affitti-brevi/prenotazioni',
      icon: 'calendar-check',
      order: 10,
      requiredPermission: 'affitti_brevi.view',
    },
    {
      id: 'affitti_brevi.calendari',
      label: 'Calendari iCal',
      path: '/affitti-brevi/calendari',
      icon: 'calendar-alt',
      order: 20,
      requiredPermission: 'affitti_brevi.view',
    },
    // Phase 4: Tourist Tax
    {
      id: 'affitti_brevi.tasse',
      label: 'Tasse Soggiorno',
      path: '/affitti-brevi/tasse',
      icon: 'euro-sign',
      order: 25,
      requiredPermission: 'affitti_brevi.view',
    },
    // Phase 5: Deadlines (to be added)
    // {
    //   id: 'affitti_brevi.scadenze',
    //   label: 'Scadenze',
    //   path: '/affitti-brevi/scadenze',
    //   icon: 'bell',
    //   order: 30,
    //   requiredPermission: 'affitti_brevi.view',
    // },
  ],

  // Widgets for dashboard
  widgets: [
    {
      id: 'affitti_brevi.scadenze',
      title: 'Scadenze Affitti Brevi',
      component: 'ScadenzeWidget',
      description: 'Monitoraggio scadenze urgenti: comunicazioni polizia, ISTAT e adempimenti',
      defaultWidth: 6,
      defaultHeight: 4,
      category: 'alerts',
      requiredPermission: 'affitti_brevi.view',
    },
    {
      id: 'affitti_brevi.calendario',
      title: 'Calendario Prenotazioni',
      component: 'CalendarioWidget',
      description: 'Panoramica prenotazioni prossimi 7 giorni e conflitti da risolvere',
      defaultWidth: 6,
      defaultHeight: 4,
      category: 'stats',
      requiredPermission: 'affitti_brevi.view',
    },
  ],

  // Permissions required for this module
  permissions: [
    'affitti_brevi.view',
    'affitti_brevi.create',
    'affitti_brevi.edit',
    'affitti_brevi.delete',
    'affitti_brevi.sync',
  ],

  // Module configuration
  config: {
    // Phase 2: iCal synchronization settings
    enableICalSync: true,
    icalSyncIntervalHours: 6,

    // Phase 4: Tourist tax settings
    enableTouristTax: true,  // ✅ Phase 4 completed

    // Phase 5: Deadlines settings
    enablePoliceDeadlines: false,  // Will be enabled in Phase 5
    enableISTATDeadlines: false,  // Will be enabled in Phase 5
  },

  // Module status
  enabled: true,
  experimental: false,
};

export default manifest;
