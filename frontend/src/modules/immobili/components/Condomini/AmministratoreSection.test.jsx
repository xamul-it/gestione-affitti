import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import AmministratoreSection from './AmministratoreSection';
import { relazioniAPI } from '../../../../services/relazioniAPI';
import { getSoggettiAnagrafici } from '../../../anagrafica_italiana/services/anagraficaAPI';

vi.mock('../../../../services/relazioniAPI', () => ({
  relazioniAPI: { list: vi.fn(), create: vi.fn(), update: vi.fn(), rinnova: vi.fn() },
}));
vi.mock('../../../anagrafica_italiana/services/anagraficaAPI', async (importOriginal) => ({
  ...(await importOriginal()),
  soggettiAnagraficiAPI: {},
  getSoggettiAnagrafici: vi.fn(),
  getSoggettoById: vi.fn().mockResolvedValue({ id: 3, tipo_soggetto: 'PERSONA_FISICA', nome: 'Mario', cognome: 'Rossi' }),
}));

const corrente = {
  relazione_id: 11, soggetto_id: 3, tipo: 'amministratore_condominio', entity_type: 'CONDOMINIO', entity_id: 4,
  data_inizio: '2026-01-15', data_fine: null, data_scadenza: '2027-01-15', corrente: true,
};

const renderIt = (props = {}) => render(
  <MemoryRouter><AmministratoreSection condominioId={4} legacy={{}} {...props} /></MemoryRouter>,
);

describe('AmministratoreSection', () => {
  beforeEach(() => vi.clearAllMocks());

  it('shows the current administrator with mandate expiry and renews it', async () => {
    relazioniAPI.list.mockResolvedValue({ data: [corrente] });
    relazioniAPI.rinnova.mockResolvedValue({ data: { ...corrente, data_scadenza: '2028-01-15' } });
    renderIt();
    expect(await screen.findByRole('link', { name: 'Mario Rossi' })).toHaveAttribute('href', '/anagrafiche/3');
    expect(screen.getByText('15/01/2027')).toBeInTheDocument();
    expect(relazioniAPI.list).toHaveBeenCalledWith({
      tipo: 'amministratore_condominio', entity_type: 'CONDOMINIO', entity_id: 4, solo_correnti: true,
    });
    fireEvent.click(screen.getByRole('button', { name: 'Rinnova mandato' }));
    fireEvent.click(screen.getByRole('button', { name: 'Rinnova' }));
    await waitFor(() => expect(relazioniAPI.rinnova).toHaveBeenCalledWith(11));
  });

  it('closes the appointment after confirmation', async () => {
    relazioniAPI.list.mockResolvedValue({ data: [corrente] });
    relazioniAPI.update.mockResolvedValue({ data: {} });
    renderIt();
    fireEvent.click(await screen.findByRole('button', { name: 'Chiudi incarico' }));
    fireEvent.click(screen.getByRole('button', { name: 'Chiudi' }));
    await waitFor(() => expect(relazioniAPI.update).toHaveBeenCalledWith(11, { data_fine: expect.stringMatching(/^\d{4}-\d{2}-\d{2}$/) }));
  });

  it('links an anagrafica as administrator', async () => {
    relazioniAPI.list.mockResolvedValue({ data: [] });
    relazioniAPI.create.mockResolvedValue({ data: {} });
    getSoggettiAnagrafici.mockResolvedValue([{ id: 8, tipo_soggetto: 'PERSONA_GIURIDICA', ragione_sociale: 'Studio Bianchi' }]);
    renderIt({ legacy: { amministratore_nome: 'Studio Bianchi', amministratore_telefono: '02 123' } });
    expect(await screen.findByText(/Dati precedenti:.*Studio Bianchi.*02 123/)).toBeInTheDocument();
    fireEvent.change(screen.getByLabelText('Amministratore'), { target: { value: 'Bian' } });
    fireEvent.click(await screen.findByRole('button', { name: 'Studio Bianchi' }));
    fireEvent.change(screen.getByLabelText('In carica dal'), { target: { value: '2026-02-01' } });
    fireEvent.click(screen.getByRole('button', { name: 'Collega amministratore' }));
    await waitFor(() => expect(relazioniAPI.create).toHaveBeenCalledWith({
      tipo: 'amministratore_condominio', entity_type: 'CONDOMINIO', entity_id: 4, soggetto_id: 8,
      data_inizio: '2026-02-01',
    }));
  });

  it('shows the server error', async () => {
    relazioniAPI.list.mockResolvedValue({ data: [] });
    relazioniAPI.create.mockRejectedValue({ response: { status: 422, data: { detail: "C'è già un amministratore condominio in carica" } } });
    getSoggettiAnagrafici.mockResolvedValue([{ id: 8, tipo_soggetto: 'PERSONA_GIURIDICA', ragione_sociale: 'Studio Bianchi' }]);
    renderIt();
    fireEvent.change(await screen.findByLabelText('Amministratore'), { target: { value: 'Bian' } });
    fireEvent.click(await screen.findByRole('button', { name: 'Studio Bianchi' }));
    fireEvent.change(screen.getByLabelText('In carica dal'), { target: { value: '2026-02-01' } });
    fireEvent.click(screen.getByRole('button', { name: 'Collega amministratore' }));
    expect(await screen.findByRole('alert')).toHaveTextContent('già un amministratore');
    expect(screen.queryByText(/Dati precedenti/)).not.toBeInTheDocument();
  });
});
