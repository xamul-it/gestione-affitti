import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import ImmobiliStatsWidget from './ImmobiliStatsWidget';
import { unitaImmobiliariAPI, condominAPI } from '../../services/immobiliAPI';
import { relazioniAPI } from '../../../../services/relazioniAPI';

vi.mock('../../services/immobiliAPI', () => ({
  unitaImmobiliariAPI: { getAll: vi.fn() },
  condominAPI: { getAll: vi.fn() },
}));
vi.mock('../../../../services/relazioniAPI', () => ({ relazioniAPI: { list: vi.fn() } }));

describe('ImmobiliStatsWidget', () => {
  it('links to the units list (not back to the dashboard) and counts occupied units from current tenants', async () => {
    unitaImmobiliariAPI.getAll.mockResolvedValue({ data: [{ id: 1 }, { id: 2 }, { id: 3 }] });
    condominAPI.getAll.mockResolvedValue({ data: [] });
    relazioniAPI.list.mockImplementation(({ famiglia }) => Promise.resolve({ data: famiglia === 'diritti_reali'
      ? [{ soggetto_id: 4, entity_id: 1 }, { soggetto_id: 4, entity_id: 2 }, { soggetto_id: 5, entity_id: 2 }]
      : [{ soggetto_id: 9, entity_id: 1 }, { soggetto_id: 9, entity_id: 1 }] }));

    render(<MemoryRouter><ImmobiliStatsWidget /></MemoryRouter>);

    const occupati = await screen.findByText('Occupati');
    expect(occupati.closest('.stat-card')).toHaveTextContent('1');
    expect(screen.getByText('Liberi').closest('.stat-card')).toHaveTextContent('2');
    expect(screen.getByText('Titolari di diritti').closest('.stat-card')).toHaveTextContent('2');

    const hrefs = screen.getAllByRole('link').map((a) => a.getAttribute('href'));
    expect(hrefs).not.toContain('/immobili');
    expect(hrefs).toContain('/unita-immobiliari');
  });
});
