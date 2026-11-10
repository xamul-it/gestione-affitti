import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import UnitaImmobiliareForm from './UnitaImmobiliareForm';

vi.mock('../../services/immobiliAPI', () => ({
  unitaImmobiliariAPI: { create: vi.fn(), update: vi.fn() },
  categorieCatastaliAPI: { getAll: vi.fn(() => Promise.resolve({ data: [] })) },
}));
vi.mock('../DirittiImmobile/DirittiImmobileSection', () => ({ default: () => null }));
vi.mock('../Conduttori/AssegnazioneConduttoreSection', () => ({ default: () => null }));
vi.mock('../SpeseRicorrenti/SpeseRicorrentiSection', () => ({ default: () => null }));

describe('UnitaImmobiliareForm', () => {
  it('il form non mostra la classe energetica (viene dall\'APE)', () => {
    const { container } = render(
      <MemoryRouter><UnitaImmobiliareForm onClose={() => {}} onSave={() => {}} /></MemoryRouter>,
    );
    expect(screen.getByText(/Rendita Catastale/i)).toBeInTheDocument();
    expect(container.querySelector('[name="classe_energetica"]')).toBeNull();
  });
});
