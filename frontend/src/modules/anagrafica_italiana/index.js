/**
 * Anagrafica Italiana Module - Exports
 *
 * Exports components and services from the Italian Registry module
 */

import { widgetRegistry } from '../../core/widgets'

// Register widgets with the platform registry
widgetRegistry.registerWidget(
  'StatsSoggettiWidget',
  'anagrafica_italiana',
  () => import('./components/Dashboard/StatsSoggettiWidget')
)

// Components
export { default as SoggettiAnagraficiList } from './components/SoggettiAnagrafici/SoggettiAnagraficiList';
export { default as SoggettoDetail } from './components/SoggettiAnagrafici/SoggettoDetail';
export { default as SoggettoNew } from './components/SoggettiAnagrafici/SoggettoNew';

// Persone Fisiche Components
export { PersoneFisicheList, PersonaFisicaForm, PersonaFisicaDetail } from './components/PersoneFisiche';

// Persone Giuridiche Components
export { PersoneGiuridicheList, PersonaGiuridicaForm, PersonaGiuridicaDetail } from './components/PersoneGiuridiche';

// Comuni Components
export { ComuniList } from './components/Comuni';

// Ruoli Azienda Tipi Components (Domain Data)
export { default as RuoliAziendaTipiList } from './components/RuoliAziendaTipi/RuoliAziendaTipiList';

// Ruoli Azienda Components (Associations)
export { default as RuoliAziendaList } from './components/RuoliAzienda/RuoliAziendaList';

// Document Components
export { DocumentoUpload, DocumentoList } from './components/Documenti';

// Dashboard Widgets
export { default as StatsSoggettiWidget } from './components/Dashboard/StatsSoggettiWidget';

// Services
export * as anagraficaAPI from './services/anagraficaAPI';
export { default as anagraficaAPIDefault } from './services/anagraficaAPI';
