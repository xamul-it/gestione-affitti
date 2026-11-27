import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import RaggruppamentiAlbero from './RaggruppamentiAlbero';
import { raggruppamentiAPI } from '../../services/immobiliAPI';

vi.mock('../../services/immobiliAPI', () => ({
  raggruppamentiAPI: { getAll: vi.fn(), create: vi.fn() },
}));

const albero = [
  { id: 1, tipo: 'COMPLESSO', nome: 'Complesso Forlì', attivo: true, beni: [], figli: [
    { id: 2, tipo: 'EDIFICIO', nome: 'Edificio A', attivo: true, figli: [],
      beni: [{ id: 9, codice: 'FO-001', tipo_bene: 'UNITA', descrizione: null }] },
  ] },
];

const renderAlbero = () => render(<MemoryRouter><RaggruppamentiAlbero /></MemoryRouter>);

describe('RaggruppamentiAlbero', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    raggruppamentiAPI.getAll.mockResolvedValue({ data: albero });
    raggruppamentiAPI.create.mockResolvedValue({ data: { id: 3 } });
  });

  it('shows nested rami with their beni', async () => {
    renderAlbero();
    expect(await screen.findByRole('link', { name: 'Complesso Forlì' })).toHaveAttribute('href', '/raggruppamenti/1');
    expect(screen.getByRole('link', { name: 'Edificio A' })).toHaveAttribute('href', '/raggruppamenti/2');
    expect(screen.getByRole('link', { name: /FO-001/ })).toHaveAttribute('href', '/beni/9');
    expect(screen.getByText('Edificio')).toBeInTheDocument();
    expect(raggruppamentiAPI.getAll).toHaveBeenCalledWith({ vista: 'albero', includi_archiviati: false });
  });

  it('reloads with the archived rami', async () => {
    renderAlbero();
    await screen.findByText('Complesso Forlì');
    fireEvent.click(screen.getByLabelText('Mostra archiviati'));
    await waitFor(() => expect(raggruppamentiAPI.getAll).toHaveBeenLastCalledWith({ vista: 'albero', includi_archiviati: true }));
  });

  it('creates a root ramo', async () => {
    renderAlbero();
    await screen.findByText('Complesso Forlì');
    fireEvent.click(screen.getByRole('button', { name: /nuovo raggruppamento/i }));
    fireEvent.change(screen.getByLabelText(/^Nome/), { target: { value: 'Fondo Bertinoro' } });
    fireEvent.change(screen.getByLabelText('Tipo'), { target: { value: 'FONDO' } });
    fireEvent.click(screen.getByRole('button', { name: 'Salva' }));
    await waitFor(() => expect(raggruppamentiAPI.create).toHaveBeenCalledWith({
      tipo: 'FONDO', nome: 'Fondo Bertinoro', descrizione: null, note: null, padre_id: null,
    }));
  });

  it('shows an empty state', async () => {
    raggruppamentiAPI.getAll.mockResolvedValue({ data: [] });
    renderAlbero();
    expect(await screen.findByText('Nessun raggruppamento')).toBeInTheDocument();
  });
});
