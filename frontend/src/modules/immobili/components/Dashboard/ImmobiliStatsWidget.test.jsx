import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import ImmobiliStatsWidget from './ImmobiliStatsWidget';
import {
  unitaImmobiliariAPI, proprietariAPI, condominAPI, assegnazioniConduttoreAPI,
} from '../../services/immobiliAPI';

vi.mock('../../services/immobiliAPI', () => ({
  unitaImmobiliariAPI: { getAll: vi.fn() },
  proprietariAPI: { getAll: vi.fn() },
  condominAPI: { getAll: vi.fn() },
  assegnazioniConduttoreAPI: { getAll: vi.fn() },
}));

describe('ImmobiliStatsWidget', () => {
  it('links to the units list (not back to the dashboard) and counts occupied units from current tenants', async () => {
    unitaImmobiliariAPI.getAll.mockResolvedValue({ data: [{ id: 1 }, { id: 2 }, { id: 3 }] });
    proprietariAPI.getAll.mockResolvedValue({ data: [{ id: 1 }] });
    condominAPI.getAll.mockResolvedValue({ data: [] });
    assegnazioniConduttoreAPI.getAll.mockResolvedValue({ data: [
      { id: 10, unita_immobiliare_id: 1, data_fine: null },
      { id: 11, unita_immobiliare_id: 1, data_fine: null },
      { id: 12, unita_immobiliare_id: 2, data_fine: '2025-01-01' },
    ] });

    render(<MemoryRouter><ImmobiliStatsWidget /></MemoryRouter>);

    const occupati = await screen.findByText('Occupati');
    expect(occupati.closest('.stat-card')).toHaveTextContent('1');
    expect(screen.getByText('Liberi').closest('.stat-card')).toHaveTextContent('2');

    const hrefs = screen.getAllByRole('link').map((a) => a.getAttribute('href'));
    expect(hrefs).not.toContain('/immobili');
    expect(hrefs).toContain('/unita-immobiliari');
  });
});
