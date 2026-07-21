/**
 * Module Manifest: anagrafica_italiana
 *
 * Italian Registry Module - Manages Italian persons and companies
 * with Italian-specific identifiers (Codice Fiscale, Partita IVA)
 */

export const manifest = {
  // Module identification
  id: 'anagrafica_italiana',
  displayName: 'Anagrafica',
  version: '1.0.0',
  description: 'Gestione registro anagrafiche italiane con Codice Fiscale e Partita IVA',

  // Module metadata
  author: 'Gestione Affitti',
  category: 'Base',
  icon: 'id-card',

  // Dependencies (no dependencies - this is a foundational module)
  dependencies: [],

  // Routes provided by this module (to be implemented)
  routes: [
    // Future: when we centralize Proprietari/Affittuari/Tecnici to use SoggettoAnagrafico
    // {
    //   path: '/soggetti-anagrafici',
    //   component: 'SoggettiAnagraficiList',
    //   label: 'Soggetti Anagrafici',
    //   icon: 'id-card',
    // }
  ],

  // Menu items (to be registered with platform)
  menuItems: [
    {
      id: 'anagrafica.persone_fisiche',
      label: 'Persone Fisiche',
      path: '/anagrafiche/persone-fisiche',
      icon: 'user',
      orderIndex: 10,
      requiredPermission: 'soggetto.view',
      description: 'Gestione persone fisiche (individui con CF)',
    },
    {
      id: 'anagrafica.persone_giuridiche',
      label: 'Persone Giuridiche',
      path: '/anagrafiche/persone-giuridiche',
      icon: 'building',
      orderIndex: 11,
      requiredPermission: 'soggetto.view',
      description: 'Gestione persone giuridiche (aziende, società)',
    },
    // Comuni spostato in "Amministrazione Dati" - è un dato di riferimento
  ],

  // Widgets for dashboard
  widgets: [
    {
      id: 'anagrafica_italiana.stats_soggetti',
      title: 'Statistiche Anagrafiche',
      component: 'StatsSoggettiWidget',
      defaultWidth: 6,
      defaultHeight: 4,
      category: 'stats',
      requiredPermission: 'soggetto.view',
      description: 'Panoramica delle anagrafiche registrate (persone fisiche e giuridiche)',
    },
  ],

  // Permissions required for this module
  permissions: [
    'anagrafica.view',
    'anagrafica.create',
    'anagrafica.update',
    'anagrafica.delete',
  ],

  // Module configuration
  config: {
    enableCodiceFiscaleValidation: true,
    enablePartitaIVAValidation: true,
    requireCodiceFiscaleForPersons: true,
    requirePartitaIVAForCompanies: false,
  },

  // Module status
  enabled: true,
  experimental: false,
};

export default manifest;
