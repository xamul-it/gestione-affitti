/**
 * Registry of the document forms that modules attach to their document types.
 *
 * A document type declared in a backend manifest can name a form
 * (`"form": "immobili.ape"`). Each frontend module registers its forms in
 * `src/modules/<module>/documentForms.js`:
 *
 *   export default { 'immobili.ape': () => import('./components/Documenti/ApeForm') };
 *
 * Every form receives: { entityType, entityId, tipo, initialFiles, onSaved, onCancel }.
 */
import { lazy } from 'react';

const registries = import.meta.glob('/src/modules/*/documentForms.js', { eager: true });

const loaders = Object.values(registries).reduce(
  (all, mod) => ({ ...all, ...(mod.default || {}) }),
  {},
);

const cache = {};

export function getDocumentForm(key) {
  if (!key || !loaders[key]) return null;
  if (!cache[key]) cache[key] = lazy(loaders[key]);
  return cache[key];
}

export default getDocumentForm;
