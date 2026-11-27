import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import RaggruppamentoScheda from './RaggruppamentoScheda';
import { raggruppamentiAPI } from '../../services/immobiliAPI';

vi.mock('../../services/immobiliAPI', () => ({
  raggruppamentiAPI: {
    getById: vi.fn(), getAll: vi.fn(), update: vi.fn(), sposta: vi.fn(), delete: vi.fn(),
    getRelazioni: vi.fn(), createRelazione: vi.fn(), create: vi.fn(),
  },
}));
vi.mock('../BeneScheda/SoggettiSection', () => ({
  default: ({ famiglie }) => <div>Soggetti del ramo {famiglie.join(',')}</div>,
}));

const dettaglio = {
  id: 2, tipo: 'EDIFICIO', nome: 'Edificio A', attivo: true, descrizione: null, note: null, padre_id: 1,
  percorso: [{ id: 1, nome: 'Complesso Forlì', tipo: 'COMPLESSO' }, { id: 2, nome: 'Edificio A', tipo: 'EDIFICIO' }],
  figli: [{ id: 3, tipo: 'ALTRO', nome: 'Cantine', attivo: true }],
  beni: [{ id: 9, codice: 'FO-001', tipo_bene: 'UNITA', descrizione: null },
    { id: 10, codice: 'FO-002', tipo_bene: 'UNITA', descrizione: null }],
};
const albero = [{ id: 1, nome: 'Complesso Forlì', figli: [
  { id: 2, nome: 'Edificio A', figli: [{ id: 3, nome: 'Cantine', figli: [] }] },
  { id: 4, nome: 'Edificio B', figli: [] },
] }];

const renderScheda = () => render(
  <MemoryRouter initialEntries={['/raggruppamenti/2']}>
    <Routes>
      <Route path="/raggruppamenti/:id" element={<RaggruppamentoScheda />} />
      <Route path="/raggruppamenti" element={<div>Albero</div>} />
    </Routes>
  </MemoryRouter>,
);

describe('RaggruppamentoScheda', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    raggruppamentiAPI.getById.mockResolvedValue({ data: dettaglio });
    raggruppamentiAPI.getAll.mockResolvedValue({ data: albero });
    raggruppamentiAPI.update.mockResolvedValue({ data: { ...dettaglio, attivo: false } });
    raggruppamentiAPI.sposta.mockResolvedValue({ data: dettaglio });
    raggruppamentiAPI.delete.mockResolvedValue({});
  });

  it('shows path, children, beni and the ramo relations without rights in rem', async () => {
    renderScheda();
    expect(await screen.findByRole('heading', { name: 'Edificio A', level: 2 })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Complesso Forlì' })).toHaveAttribute('href', '/raggruppamenti/1');
    expect(screen.getByRole('link', { name: 'Cantine' })).toHaveAttribute('href', '/raggruppamenti/3');
    expect(screen.getByRole('link', { name: /FO-002/ })).toHaveAttribute('href', '/beni/10');
    expect(screen.getByText('Soggetti del ramo godimento,incarichi')).toBeInTheDocument();
  });

  it('archives the ramo', async () => {
    renderScheda();
    await screen.findByRole('heading', { name: 'Edificio A', level: 2 });
    fireEvent.click(screen.getByRole('button', { name: 'Archivia' }));
    await waitFor(() => expect(raggruppamentiAPI.update).toHaveBeenCalledWith(2, { attivo: false }));
  });

  it('moves the ramo, without itself and its sub-rami among the choices', async () => {
    renderScheda();
    await screen.findByRole('heading', { name: 'Edificio A', level: 2 });
    fireEvent.click(screen.getByRole('button', { name: 'Sposta' }));
    const scelta = await screen.findByLabelText('Nuovo ramo superiore');
    const opzioni = Array.from(scelta.querySelectorAll('option')).map((o) => o.textContent);
    expect(opzioni).toEqual(['Nessuno (in cima)', 'Complesso Forlì', 'Complesso Forlì › Edificio B']);
    fireEvent.change(scelta, { target: { value: '4' } });
    fireEvent.click(screen.getByRole('button', { name: 'Conferma spostamento' }));
    await waitFor(() => expect(raggruppamentiAPI.sposta).toHaveBeenCalledWith(2, 4));
  });

  it('asks before deleting and says what moves up', async () => {
    renderScheda();
    await screen.findByRole('heading', { name: 'Edificio A', level: 2 });
    fireEvent.click(screen.getByRole('button', { name: 'Elimina' }));
    expect(screen.getByText(/1 sotto-ramo e 2 beni salgono in Complesso Forlì/)).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'Elimina definitivamente' }));
    await waitFor(() => expect(raggruppamentiAPI.delete).toHaveBeenCalledWith(2));
    expect(await screen.findByText('Albero')).toBeInTheDocument();
  });

  it('shows the server message when the ramo cannot be deleted', async () => {
    raggruppamentiAPI.delete.mockRejectedValue({
      response: { status: 409, data: { detail: 'Il ramo ha relazioni o documenti: archivialo' } },
    });
    renderScheda();
    await screen.findByRole('heading', { name: 'Edificio A', level: 2 });
    fireEvent.click(screen.getByRole('button', { name: 'Elimina' }));
    fireEvent.click(screen.getByRole('button', { name: 'Elimina definitivamente' }));
    expect(await screen.findByRole('alert')).toHaveTextContent('Il ramo ha relazioni o documenti: archivialo');
  });
});
