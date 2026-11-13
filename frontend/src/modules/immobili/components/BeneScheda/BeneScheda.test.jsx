import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, within } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import BeneScheda, { RedirectABene } from './BeneScheda';
import { beniAPI, unitaImmobiliariAPI, terreniAPI } from '../../services/immobiliAPI';

vi.mock('../../services/immobiliAPI', () => ({
  beniAPI: { getById: vi.fn() },
  unitaImmobiliariAPI: { getById: vi.fn() },
  terreniAPI: { getById: vi.fn() },
}));
vi.mock('../../../../core/components/Documenti/DocumentiPanel', () => ({
  default: ({ entityType, entityId }) => <div>Pannello documenti {entityType} {entityId}</div>,
}));
vi.mock('./VariazioniCatastali', () => ({ default: ({ beneId }) => <div>Variazioni {beneId}</div> }));
vi.mock('../DirittiImmobile/DirittiImmobileSection', () => ({ default: () => <div>Diritti</div> }));
vi.mock('../Conduttori/AssegnazioneConduttoreSection', () => ({ default: () => <div>Conduttori</div> }));
vi.mock('../SpeseRicorrenti/SpeseRicorrentiSection', () => ({ default: () => <div>Spese</div> }));
vi.mock('../../../../components/Platform/Scadenze/ScadenzeSection', () => ({ default: () => <div>Scadenze</div> }));
vi.mock('../UnitaImmobiliari/UnitaImmobiliareForm', () => ({ default: () => <div role="dialog">Form unità</div> }));
vi.mock('../Terreni/TerrenoForm', () => ({ default: () => <div role="dialog">Form terreno</div> }));

const unita = {
  id: 5, tipo_bene: 'UNITA', codice: 'MI-0001', tipo: 'Appartamento', indirizzo: 'VIALE UMBRIA n. 49 interno 23',
  citta: 'Milano', provincia: 'MI', cap: '20135', piano: '5-S1-7', foglio: '481', particella: '60',
  subalterno: '21', rendita_catastale: 821.17, superficie_mq: 142, locali: 6, categoria_catastale: { codice: 'A/3' },
};

const terreno = {
  id: 7, tipo_bene: 'TERRENO', codice: 'T-7', nome: null, comune: 'Forlì', provincia: 'FC', indirizzo: null,
  sezione_catastale: null, foglio: '40', particella: '154', tipologia: { nome: 'Agricolo' },
  superficie_mq: 426, reddito_dominicale_totale: '0.31', reddito_agrario_totale: '0.12',
  edificabile: false, esente_imu_montano: true, servitu: 'Passaggio a piedi',
  porzioni: [
    { id: 1, porzione: 'AA', qualita: 'BOSCO CEDUO', classe: '2', superficie_mq: 363,
      reddito_dominicale: '0.25', reddito_agrario: '0.09', deduzioni: null },
    { id: 2, porzione: 'AB', qualita: 'PASCOLO', classe: '2', superficie_mq: 63,
      reddito_dominicale: '0.06', reddito_agrario: '0.03', deduzioni: null },
  ],
};

function renderAt(path) {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <Routes>
        <Route path="/beni/:id" element={<BeneScheda />} />
        <Route path="/unita-immobiliari/:id" element={<RedirectABene />} />
        <Route path="/terreni/:id" element={<RedirectABene />} />
      </Routes>
    </MemoryRouter>,
  );
}

describe('BeneScheda', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    beniAPI.getById.mockImplementation((id) => Promise.resolve({
      data: { id: Number(id), tipo_bene: String(id) === '7' ? 'TERRENO' : 'UNITA' },
    }));
    unitaImmobiliariAPI.getById.mockResolvedValue({ data: unita });
    terreniAPI.getById.mockResolvedValue({ data: terreno });
  });

  it("mostra i dati dell'unità", async () => {
    renderAt('/beni/5');
    expect(await screen.findByRole('heading', { name: /MI-0001 · Appartamento/ })).toBeInTheDocument();
    expect(screen.getByText('481 / 60 / 21')).toBeInTheDocument();
    expect(screen.getByText('A/3')).toBeInTheDocument();
    expect(screen.getByText('€ 821,17')).toBeInTheDocument();
    expect(screen.getByText('Pannello documenti IMMOBILE 5')).toBeInTheDocument();
    expect(screen.getByText('Variazioni 5')).toBeInTheDocument();
    expect(unitaImmobiliariAPI.getById).toHaveBeenCalledWith('5');
    expect(terreniAPI.getById).not.toHaveBeenCalled();
    expect(screen.getByRole('link', { name: /unità immobiliari/i })).toHaveAttribute('href', '/unita-immobiliari');
  });

  it('mostra la tabella delle porzioni di un terreno', async () => {
    renderAt('/beni/7');
    expect(await screen.findByRole('heading', { name: /T-7 · Terreno/ })).toBeInTheDocument();
    const tabella = screen.getByRole('table', { name: /porzioni/i });
    expect(within(tabella).getByText('BOSCO CEDUO')).toBeInTheDocument();
    expect(within(tabella).getByText('3 a 63 ca')).toBeInTheDocument();
    expect(within(tabella).getByText('PASCOLO')).toBeInTheDocument();
    expect(within(tabella).getByText('€ 0,25')).toBeInTheDocument();
    expect(screen.getByText('4 a 26 ca')).toBeInTheDocument();
    expect(screen.getByText('40 / 154')).toBeInTheDocument();
    expect(screen.getByText('Passaggio a piedi')).toBeInTheDocument();
    expect(screen.getByText('Pannello documenti IMMOBILE 7')).toBeInTheDocument();
    expect(screen.getByText('Diritti')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /terreni/i })).toHaveAttribute('href', '/terreni');
  });

  it('apre il form del tipo giusto', async () => {
    renderAt('/beni/7');
    fireEvent.click(await screen.findByRole('button', { name: /modifica/i }));
    expect(screen.getByText('Form terreno')).toBeInTheDocument();
  });

  it('il vecchio link /terreni/:id porta alla scheda del bene', async () => {
    renderAt('/terreni/7');
    expect(await screen.findByRole('heading', { name: /T-7/ })).toBeInTheDocument();
    expect(beniAPI.getById).toHaveBeenCalledWith('7');
  });

  it('il vecchio link /unita-immobiliari/:id porta alla scheda del bene', async () => {
    renderAt('/unita-immobiliari/5');
    expect(await screen.findByRole('heading', { name: /MI-0001/ })).toBeInTheDocument();
    expect(beniAPI.getById).toHaveBeenCalledWith('5');
  });

  it('mostra un errore se il bene non esiste', async () => {
    beniAPI.getById.mockRejectedValue({ response: { status: 404, data: { detail: 'Bene non trovato' } } });
    renderAt('/beni/999');
    expect(await screen.findByRole('alert')).toHaveTextContent('Bene non trovato');
  });
});
