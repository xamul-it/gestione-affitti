// Document forms of the immobili module, keyed by the `form` declared on the
// document types in backend/modules/immobili/__manifest__.py.
// See core/documenti/documentForms.js.
export default {
  'immobili.visura': () => import('./components/Documenti/VisuraDocumentForm'),
  'immobili.ape': () => import('./components/Documenti/ApeForm'),
};
