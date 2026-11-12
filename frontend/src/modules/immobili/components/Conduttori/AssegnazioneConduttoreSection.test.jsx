import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import AssegnazioneConduttoreSection from './AssegnazioneConduttoreSection';
import { assegnazioniConduttoreAPI } from '../../services/immobiliAPI';

vi.mock('../../services/immobiliAPI', () => ({
  assegnazioniConduttoreAPI: { getByBene: vi.fn() },
  conduttoriAPI: { getAll: vi.fn() },
}));

describe('AssegnazioneConduttoreSection', () => {
  it("shows the tenant's name linked to the anagrafica, not the record id", async () => {
    assegnazioniConduttoreAPI.getByBene.mockResolvedValue({ data: [
      { id: 905, conduttore_id: 979, soggetto_id: 9501, conduttore_nome: 'Lucia Inquilina',
        data_inizio: '2026-01-01', data_fine: null },
    ] });
    render(<MemoryRouter><AssegnazioneConduttoreSection unitaImmobiliareId={1} /></MemoryRouter>);
    const link = await screen.findByRole('link', { name: 'Lucia Inquilina' });
    expect(link).toHaveAttribute('href', '/anagrafiche/9501');
    expect(screen.queryByText(/Conduttore #979/)).toBeNull();
    expect(screen.getByRole('button', { name: 'Elimina assegnazione' })).toBeInTheDocument();
  });
});
