/**
 * Affitti Lungo Module
 * Entry point for the Long-term Rentals module
 */

export { manifest } from './manifest.js';
export * from './services/affittiAPI.js';

// ============================================================================
// COMPONENT EXPORTS
// ============================================================================

// Affittuari
export { default as AffittuariList } from './components/Affittuari/AffittuariList';
export { default as AffittuarioForm } from './components/Affittuari/AffittuarioForm';

// Contratti
export { default as ContrattiList } from './pages/ContrattiPage';  // New migrated version
export { default as ContrattoForm } from './components/Contratti/ContrattoForm';

// Incassi
export { default as IncassiList } from './components/Incassi/IncassiList';
export { default as IncassoForm } from './components/Incassi/IncassoForm';

// Spese
export { default as SpeseList } from './components/Spese/SpeseList';
export { default as SpesaForm } from './components/Spese/SpesaForm';

// Tecnici
export { default as TecniciList } from './components/Tecnici/TecniciList';
export { default as TecnicoForm } from './components/Tecnici/TecnicoForm';

// Documenti
export { default as DocumentiSection } from './components/Documenti/DocumentiSection';
export { default as DocumentoUpload } from './components/Documenti/DocumentoUpload';
