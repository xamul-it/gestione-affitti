import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import VariazioniCatastali from './VariazioniCatastali';
import { unitaImmobiliariAPI, categorieCatastaliAPI } from '../../services/immobiliAPI';

vi.mock('../../services/immobiliAPI', () => ({
  unitaImmobiliariAPI: { getVariazioniCatastali: vi.fn() },
  categorieCatastaliAPI: { getAll: vi.fn() },
}));

describe('VariazioniCatastali', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    categorieCatastaliAPI.getAll.mockResolvedValue({ data: [{ id: 3, codice: 'A/3' }, { id: 4, codice: 'A/2' }] });
  });

  it('lists changes with readable labels and values', async () => {
    unitaImmobiliariAPI.getVariazioniCatastali.mockResolvedValue({ data: [
      { id: 2, campo: 'rendita_catastale', valore_precedente: '500.0', valore_nuovo: '600.0', origine: 'VISURA',
        documento_id: 9, data_riferimento: '2024-04-04', created_at: '2026-11-09T10:00:00Z' },
      { id: 1, campo: 'categoria_catastale_id', valore_precedente: '3', valore_nuovo: '4', origine: 'MANUALE',
        documento_id: null, data_riferimento: '2026-11-01', created_at: '2026-11-01T10:00:00Z' },
    ] });
    render(<VariazioniCatastali unitaId={5} />);
    expect(await screen.findByText('Rendita catastale')).toBeInTheDocument();
    expect(screen.getByText('€ 500,00')).toBeInTheDocument();
    expect(screen.getByText('€ 600,00')).toBeInTheDocument();
    expect(await screen.findByText('A/3')).toBeInTheDocument();
    expect(screen.getByText('A/2')).toBeInTheDocument();
    expect(screen.getByText('Da visura')).toBeInTheDocument();
    expect(screen.getByText('Modifica manuale')).toBeInTheDocument();
    expect(unitaImmobiliariAPI.getVariazioniCatastali).toHaveBeenCalledWith(5);
  });

  it('shows the empty state', async () => {
    unitaImmobiliariAPI.getVariazioniCatastali.mockResolvedValue({ data: [] });
    render(<VariazioniCatastali unitaId={5} />);
    expect(await screen.findByText('Nessuna variazione registrata')).toBeInTheDocument();
  });
});
