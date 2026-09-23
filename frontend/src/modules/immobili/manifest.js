/**
 * Module Manifest: immobili
 *
 * Real Estate Properties Module - Manages properties, ownership,
 * cadastral data, condominiums, and energy certificates
 */

export const manifest = {
  // Module identification
  id: 'immobili',
  displayName: 'Immobili',
  version: '1.0.0',
  description: 'Gestione immobili, proprietà, condomini e dati catastali',

  // Module metadata
  author: 'Gestione Affitti',
  category: 'Immobiliare',
  icon: 'building',

  // Dependencies
  dependencies: ['anagrafica_italiana'], // Depends on registry for Proprietario

  // Routes provided by this module
  routes: [
    {
      path: '/immobili',
      component: 'UnitaImmobiliariList',
      label: 'Unità Immobiliari',
      icon: 'building',
    },
    {
      path: '/terreni',
      component: 'TerreniList',
      label: 'Terreni',
      icon: 'leaf',
    },
    {
      path: '/proprietari',
      component: 'ProprietariList',
      label: 'Proprietari',
      icon: 'user-tie',
    },
    {
      path: '/condomini',
      component: 'CondominioList',
      label: 'Condomini',
      icon: 'building-columns',
    },
    {
      path: '/conduttori',
      component: 'ConduttoriList',
      label: 'Conduttori',
      icon: 'user-check',
    },
    {
      path: '/certificati-energetici',
      component: 'CertificatiEnergeticiList',
      label: 'Certificati Energetici',
      icon: 'zap',
    },
    {
      path: '/categorie-catastali',
      component: 'CategorieCatastaliList',
      label: 'Categorie Catastali',
      icon: 'list',
    },
    {
      path: '/tipologie-terreno',
      component: 'TipologieTerrenoList',
      label: 'Tipologie Terreno',
      icon: 'leaf',
    },
  ],

  // Menu items (to be registered with platform)
  menuItems: [
    {
      id: 'immobili.unita',
      label: 'Unità Immobiliari',
      path: '/immobili',
      icon: 'building',
      order: 10,
      requiredPermission: 'immobile.view',
    },
    {
      id: 'immobili.terreni',
      label: 'Terreni',
      path: '/terreni',
      icon: 'leaf',
      order: 15,
      requiredPermission: 'terreno.view',
    },
    {
      id: 'immobili.proprietari',
      label: 'Proprietari',
      path: '/proprietari',
      icon: 'user-tie',
      order: 20,
      requiredPermission: 'proprietario.view',
    },
    {
      id: 'immobili.condomini',
      label: 'Condomini',
      path: '/condomini',
      icon: 'building-columns',
      order: 30,
      requiredPermission: 'condominio.view',
    },
    {
      id: 'immobili.conduttori',
      label: 'Conduttori',
      path: '/conduttori',
      icon: 'user-check',
      order: 25,
      requiredPermission: 'conduttore.view',
    },
    {
      id: 'immobili.gestione',
      label: 'Gestione',
      path: '#',
      icon: 'cog',
      order: 40,
      children: [
        {
          id: 'immobili.certificati',
          label: 'Certificati Energetici',
          path: '/certificati-energetici',
          order: 1,
          requiredPermission: 'certificato_energetico.view',
        },
        {
          id: 'immobili.categorie',
          label: 'Categorie Catastali',
          path: '/categorie-catastali',
          order: 2,
          requiredPermission: 'categoria_catastale.view',
        },
        {
          id: 'immobili.tipologie_terreno',
          label: 'Tipologie Terreno',
          path: '/tipologie-terreno',
          order: 3,
          requiredPermission: 'categoria_catastale.view',
        },
      ],
    },
  ],

  // Widgets for dashboard
  widgets: [
    {
      id: 'immobili.stats',
      title: 'Statistiche Immobili',
      component: 'ImmobiliStatsWidget',
      defaultWidth: 6,
      defaultHeight: 4,
      category: 'stats',
      requiredPermission: 'immobile.view',
    },
    {
      id: 'immobili.certificati_scadenza',
      title: 'Certificati in Scadenza',
      component: 'CertificatiScadenzaWidget',
      defaultWidth: 6,
      defaultHeight: 4,
      category: 'alerts',
      requiredPermission: 'certificato_energetico.view',
    },
  ],

  // Permissions required for this module
  permissions: [
    'immobile.view',
    'immobile.create',
    'immobile.update',
    'immobile.delete',
    'terreno.view',
    'terreno.create',
    'terreno.update',
    'terreno.delete',
    'proprietario.view',
    'proprietario.create',
    'proprietario.update',
    'proprietario.delete',
    'condominio.view',
    'condominio.create',
    'condominio.update',
    'condominio.delete',
    'conduttore.view',
    'conduttore.create',
    'conduttore.update',
    'conduttore.delete',
    'certificato_energetico.view',
    'certificato_energetico.create',
    'certificato_energetico.update',
    'certificato_energetico.delete',
    'categoria_catastale.view',
    'categoria_catastale.create',
    'categoria_catastale.update',
    'categoria_catastale.delete',
  ],

  // Module configuration
  config: {
    enableCatastalValidation: true,
    enableAutoCodiceGeneration: true,
    defaultProvince: 'BO',
    requireEnergyPerformanceIndex: true,
  },

  // Module status
  enabled: true,
  experimental: false,
};

export default manifest;
