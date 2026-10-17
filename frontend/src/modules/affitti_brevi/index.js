/**
 * Affitti Brevi Module
 * Entry point for the Short-term Rentals module
 */

import { widgetRegistry } from '../../core/widgets'

// Register widgets with the platform registry
widgetRegistry.registerWidget(
  'ScadenzeWidget',
  'affitti_brevi',
  () => import('./components/Dashboard/ScadenzeWidget')
)

widgetRegistry.registerWidget(
  'CalendarioWidget',
  'affitti_brevi',
  () => import('./components/Dashboard/CalendarioWidget')
)

export { manifest } from './manifest.js';
export * from './services/affittiBreviAPI.js';

// ============================================================================
// COMPONENT EXPORTS
// ============================================================================

// Prenotazioni
export { default as PrenotazioniList } from './components/Prenotazioni/PrenotazioniList';
export { default as PrenotazioneForm } from './components/Prenotazioni/PrenotazioneForm';

// Calendari iCal
export { default as CalendariList } from './components/CalendariIcal/CalendariList';
export { default as CalendarioForm } from './components/CalendariIcal/CalendarioForm';

// Calendario Multi-Piattaforma (Phase 3)
export { default as CalendarioMultiPiattaforma } from './components/Calendario/CalendarioMultiPiattaforma';

// Tasse Soggiorno (Phase 4)
export { TassaConfigList, TassaConfigForm, TassaPrenotazioneDetail } from './components/Tasse';

// Comunicazioni Compliance
export { default as ComunicazioneDetail } from './components/Comunicazioni/ComunicazioneDetail';

// Dashboard Widgets
export { default as ScadenzeWidget } from './components/Dashboard/ScadenzeWidget';
export { default as CalendarioWidget } from './components/Dashboard/CalendarioWidget';
