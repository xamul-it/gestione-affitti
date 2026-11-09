import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import ImmobileScheda from './ImmobileScheda';
import { unitaImmobiliariAPI } from '../../services/immobiliAPI';

vi.mock('../../services/immobiliAPI', () => ({
  unitaImmobiliariAPI: { getById: vi.fn() },
}));
vi.mock('../../../../core/components/Documenti/DocumentiPanel', () => ({
  default: ({ entityType, entityId }) => <div>Pannello documenti {entityType} {entityId}</div>,
}));
vi.mock('./VariazioniCatastali', () => ({ default: ({ unitaId }) => <div>Variazioni {unitaId}</div> }));
vi.mock('../DirittiImmobile/DirittiImmobileSection', () => ({ default: () => <div>Diritti</div> }));
vi.mock('../Conduttori/AssegnazioneConduttoreSection', () => ({ default: () => <div>Conduttori</div> }));
vi.mock('../SpeseRicorrenti/SpeseRicorrentiSection', () => ({ default: () => <div>Spese</div> }));
vi.mock('../../../../components/Platform/Scadenze/ScadenzeSection', () => ({ default: () => <div>Scadenze</div> }));
vi.mock('../UnitaImmobiliari/UnitaImmobiliareForm', () => ({ default: () => <div role="dialog">Form modifica</div> }));

const unita = {
  id: 5, codice: 'MI-0001', tipo: 'Appartamento', indirizzo: 'VIALE UMBRIA n. 49 interno 23', citta: 'Milano',
  provincia: 'MI', cap: '20135', piano: '5-S1-7', foglio: '481', particella: '60', subalterno: '21',
  rendita_catastale: 821.17, superficie_mq: 142, locali: 6, categoria_catastale: { codice: 'A/3' },
};

function renderAt(id = '5') {
  return render(
    <MemoryRouter initialEntries={[`/unita-immobiliari/${id}`]}>
      <Routes><Route path="/unita-immobiliari/:id" element={<ImmobileScheda />} /></Routes>
    </MemoryRouter>,
  );
}

describe('ImmobileScheda', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    unitaImmobiliariAPI.getById.mockResolvedValue({ data: unita });
  });

  it('shows the unit data, documents and catastal changes', async () => {
    renderAt();
    expect(await screen.findByRole('heading', { name: /MI-0001/ })).toBeInTheDocument();
    expect(screen.getByText('481 / 60 / 21')).toBeInTheDocument();
    expect(screen.getByText('A/3')).toBeInTheDocument();
    expect(screen.getByText('€ 821,17')).toBeInTheDocument();
    expect(screen.getByText('Pannello documenti IMMOBILE 5')).toBeInTheDocument();
    expect(screen.getByText('Variazioni 5')).toBeInTheDocument();
    expect(unitaImmobiliariAPI.getById).toHaveBeenCalledWith('5');
  });

  it('opens the edit form', async () => {
    renderAt();
    fireEvent.click(await screen.findByRole('button', { name: /modifica/i }));
    expect(screen.getByText('Form modifica')).toBeInTheDocument();
  });

  it('shows an error when the unit does not exist', async () => {
    unitaImmobiliariAPI.getById.mockRejectedValue({ response: { status: 404, data: { detail: 'non trovato' } } });
    renderAt('999');
    expect(await screen.findByRole('alert')).toBeInTheDocument();
  });
});
