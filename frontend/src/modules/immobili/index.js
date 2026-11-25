/**
 * Immobili Module
 * Entry point for the Real Estate Properties module
 */

import { widgetRegistry } from '../../core/widgets'

// Register widgets with the platform registry
widgetRegistry.registerWidget(
  'ImmobiliStatsWidget',
  'immobili',
  () => import('./components/Dashboard/ImmobiliStatsWidget')
)

widgetRegistry.registerWidget(
  'CertificatiScadenzaWidget',
  'immobili',
  () => import('./components/Dashboard/CertificatiScadenzaWidget')
)

export { manifest } from './manifest.js';
export * from './services/immobiliAPI.js';

// ============================================================================
// COMPONENT EXPORTS
// ============================================================================

// UnitaImmobiliari
export { default as UnitaImmobiliariList } from './components/UnitaImmobiliari/UnitaImmobiliariList';
export { default as UnitaImmobiliareForm } from './components/UnitaImmobiliari/UnitaImmobiliareForm';

// Terreni
export { default as TerreniList } from './components/Terreni/TerreniList';
export { default as TerrenoForm } from './components/Terreni/TerrenoForm';

// Proprietari
export { default as ProprietariList } from './components/Proprietari/ProprietariList';

// Condomini
export { default as CondominList } from './components/Condomini/CondominList';
export { default as CondominioForm } from './components/Condomini/CondominioForm';

// Conduttori
export { default as ConduttoriList } from './components/Conduttori/ConduttoriList';

// Spese Ricorrenti (IMU, TARI, utenze)
export { default as SpeseRicorrentiSection } from './components/SpeseRicorrenti/SpeseRicorrentiSection';

// CertificatiEnergetici
export { default as DocumentiImmobiliPage } from './components/Documenti/DocumentiImmobiliPage';

// Scheda immobile
export { default as BeneScheda, RedirectABene } from './components/BeneScheda/BeneScheda';


// MillesimiImmobile
export { default as MillesimiImmobileList } from './components/MillesimiImmobile/MillesimiImmobileList';
export { default as MillesimiForm } from './components/MillesimiImmobile/MillesimiForm';

// TabelleMillesimali
export { default as TabelleMillesimaliList } from './components/TabelleMillesimali/TabelleMillesimaliList';
export { default as TabellaMillesimaleForm } from './components/TabelleMillesimali/TabellaMillesimaleForm';

// CategorieCatastali
export { default as CategorieCatastaliList } from './components/CategorieCatastali/CategorieCatastaliList';
export { default as CategoriaCatastaleForm } from './components/CategorieCatastali/CategoriaCatastaleForm';

// TipologieTerreno
export { default as TipologieTerrenoList } from './components/TipologieTerreno/TipologieTerrenoList';
export { default as TipologiaTerrenoForm } from './components/TipologieTerreno/TipologiaTerrenoForm';

// Dashboard Widgets
export { default as ImmobiliStatsWidget } from './components/Dashboard/ImmobiliStatsWidget';
export { default as CertificatiScadenzaWidget } from './components/Dashboard/CertificatiScadenzaWidget';
