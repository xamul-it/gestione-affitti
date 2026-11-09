import { describe, it, expect, vi } from 'vitest';
import { render } from '@testing-library/react';
import TipiDocumentoList from './TipiDocumentoList';

let captured = null;
vi.mock('../../../../core/components', () => ({
  DataTable: ({ config }) => { captured = config; return null; },
}));
vi.mock('../../../../core/hooks', () => ({
  useTableConfig: () => ({ columns: [
    { field: 'codice', label: 'Codice' },
    { field: 'modulo', label: 'Modulo' },
    { field: 'regime', label: 'Regime' },
    { field: 'scadenza', label: 'Scadenza' },
    { field: 'form', label: 'Form' },
  ], effectiveConfig: null }),
}));

const col = (field) => captured.columns.find((c) => c.field === field);
const text = (node) => {
  const { container } = render(<>{node}</>);
  return container.textContent;
};

describe('TipiDocumentoList', () => {
  it('describes manifest fields in words', () => {
    render(<TipiDocumentoList />);
    expect(text(col('modulo').render('immobili'))).toBe('immobili');
    expect(text(col('regime').render('SOSTITUTIVO'))).toBe('Sostituisce il precedente');
    expect(text(col('regime').render('CUMULATIVO'))).toBe('Si accumulano');
    expect(text(col('scadenza').render({ mesi: 120, da: 'data_riferimento' }))).toBe('10 anni');
    expect(text(col('scadenza').render({ mesi: 6, da: 'data_riferimento' }))).toBe('6 mesi');
    expect(text(col('scadenza').render({ manuale: true }))).toBe('Manuale');
    expect(text(col('scadenza').render(null))).toBe('—');
    expect(text(col('form').render('immobili.ape'))).toBe('Sì');
  });
});
