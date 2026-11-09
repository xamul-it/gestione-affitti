import { describe, it, expect } from 'vitest';
import { getDocumentForm } from './documentForms';

describe('getDocumentForm', () => {
  it('resolves the forms registered by the modules', () => {
    expect(getDocumentForm('immobili.ape')).not.toBeNull();
    expect(getDocumentForm('immobili.visura')).not.toBeNull();
    expect(getDocumentForm('immobili.ape')).toBe(getDocumentForm('immobili.ape'));
  });

  it('returns null for unknown or empty keys', () => {
    expect(getDocumentForm('nessuno.form')).toBeNull();
    expect(getDocumentForm(null)).toBeNull();
  });
});
