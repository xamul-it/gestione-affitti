import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor, within } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import CollegamentiSection from './CollegamentiSection';
import { beniAPI } from '../../services/immobiliAPI';

vi.mock('../../services/immobiliAPI', () => ({
  beniAPI: {
    getCollegamenti: vi.fn(), eliminaCollegamento: vi.fn(), aggiornaCollegamento: vi.fn(),
    creaCollegamento: vi.fn(), getAll: vi.fn(),
  },
}));

const abitazione = { id: 5, tipo_bene: 'UNITA', categoria_catastale: { codice: 'A/3' } };
const risposta = {
  collegamenti: [
    { id: 3, tipo: 'PERTINENZA', questo_e: 'PRINCIPALE', etichetta: 'Pertinenze', aperto: true,
      altro_bene: { id: 9, codice: 'BOX-1', descrizione: 'Box auto', tipo_bene: 'UNITA' },
      data_inizio: '2020-01-01', data_fine: null, note: null },
    { id: 4, tipo: 'FABBRICATO_SU_PARTICELLA', questo_e: 'COLLEGATO', etichetta: 'Costruito sulla particella', aperto: true,
      altro_bene: { id: 12, codice: 'TER-1', descrizione: null, indirizzo: null, tipo_bene: 'TERRENO' },
      data_inizio: null, data_fine: null, note: null },
  ],
  avvisi: ["Più pertinenze di categoria C/6: per l'IMU dell'abitazione principale ne conta una per categoria (L. 160/2019, c. 741)"],
};

const renderSezione = () => render(<MemoryRouter><CollegamentiSection beneId={5} bene={abitazione} /></MemoryRouter>);

describe('CollegamentiSection', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    beniAPI.getCollegamenti.mockResolvedValue({ data: risposta });
    beniAPI.eliminaCollegamento.mockResolvedValue({});
  });

  it('mostra gruppi, link e avvisi', async () => {
    renderSezione();
    expect(await screen.findByText('Pertinenze')).toBeInTheDocument();
    expect(screen.getByText('Costruito sulla particella')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /BOX-1/ })).toHaveAttribute('href', '/beni/9');
    expect(screen.getByRole('link', { name: 'TER-1' })).toHaveAttribute('href', '/beni/12');
    expect(screen.getByRole('status')).toHaveTextContent('Più pertinenze di categoria C/6');
  });

  it('elimina dopo la conferma e ricarica', async () => {
    renderSezione();
    fireEvent.click(await screen.findByRole('button', { name: 'Elimina il collegamento con BOX-1' }));
    const dialog = screen.getByRole('dialog');
    fireEvent.click(within(dialog).getByRole('button', { name: 'Elimina' }));
    await waitFor(() => expect(beniAPI.eliminaCollegamento).toHaveBeenCalledWith(5, 3));
    await waitFor(() => expect(beniAPI.getCollegamenti).toHaveBeenCalledTimes(2));
  });

  it('chiude con la data di fine', async () => {
    beniAPI.aggiornaCollegamento.mockResolvedValue({});
    renderSezione();
    fireEvent.click(await screen.findByRole('button', { name: 'Chiudi il collegamento con BOX-1' }));
    fireEvent.change(screen.getByLabelText('Fino al'), { target: { value: '2026-03-31' } });
    fireEvent.click(screen.getByRole('button', { name: 'Conferma' }));
    await waitFor(() => expect(beniAPI.aggiornaCollegamento).toHaveBeenCalledWith(5, 3, { data_fine: '2026-03-31' }));
  });

  it('mostra storico chiede anche i chiusi', async () => {
    renderSezione();
    fireEvent.click(await screen.findByLabelText('Mostra storico'));
    await waitFor(() => expect(beniAPI.getCollegamenti).toHaveBeenLastCalledWith(5, true));
  });

  it('stato vuoto', async () => {
    beniAPI.getCollegamenti.mockResolvedValue({ data: { collegamenti: [], avvisi: [] } });
    renderSezione();
    expect(await screen.findByText('Nessun bene collegato')).toBeInTheDocument();
    expect(screen.queryByRole('status')).not.toBeInTheDocument();
  });

  it('nuovo collegamento: scegli, cerca, salva; errore del server', async () => {
    beniAPI.getCollegamenti.mockResolvedValue({ data: { collegamenti: [], avvisi: [] } });
    beniAPI.getAll.mockResolvedValue({ data: [{ id: 9, codice: 'BOX-1', descrizione: 'Box', tipo_bene: 'UNITA' }] });
    beniAPI.creaCollegamento.mockRejectedValueOnce({ response: { status: 400, data: { detail: "'BOX-1' è già pertinenza di 'APP-B'" } } });
    renderSezione();
    fireEvent.click(await screen.findByRole('button', { name: /Collega/ }));
    fireEvent.click(screen.getByLabelText('Aggiungi pertinenza'));
    fireEvent.change(screen.getByLabelText(/Cerca il bene/), { target: { value: 'BOX' } });
    fireEvent.click(await screen.findByRole('button', { name: /BOX-1/ }));
    expect(beniAPI.getAll).toHaveBeenCalledWith({ q: 'BOX', tipo_bene: 'UNITA' });
    fireEvent.click(screen.getByRole('button', { name: 'Salva' }));
    expect(await screen.findByRole('alert')).toHaveTextContent("già pertinenza di 'APP-B'");
    expect(beniAPI.creaCollegamento).toHaveBeenCalledWith(5, {
      altro_bene_id: 9, tipo: 'PERTINENZA', questo_e: 'PRINCIPALE', data_inizio: null, note: null,
    });
  });

  it('errore di caricamento: niente stato vuoto', async () => {
    beniAPI.getCollegamenti.mockRejectedValue({ response: { status: 500, data: { detail: 'Errore' } } });
    renderSezione();
    expect(await screen.findByRole('alert')).toBeInTheDocument();
    expect(screen.queryByText('Nessun bene collegato')).not.toBeInTheDocument();
  });

  it('ricerca senza risultati e salva senza bene scelto', async () => {
    beniAPI.getCollegamenti.mockResolvedValue({ data: { collegamenti: [], avvisi: [] } });
    beniAPI.getAll.mockResolvedValue({ data: [] });
    renderSezione();
    fireEvent.click(await screen.findByRole('button', { name: /Collega/ }));
    fireEvent.change(screen.getByLabelText(/Cerca il bene/), { target: { value: 'ZZZ' } });
    expect(await screen.findByText('Nessun bene trovato')).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'Salva' }));
    expect(screen.getByText('Scegli il bene da collegare')).toBeInTheDocument();
    expect(screen.getByLabelText(/Cerca il bene/)).toHaveFocus();
    expect(beniAPI.creaCollegamento).not.toHaveBeenCalled();
  });
});
