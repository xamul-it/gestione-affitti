import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import DocumentiImmobiliPage from './DocumentiImmobiliPage';
import { documentiAPI } from '../../../../services/documentiAPI';

vi.mock('../../../../services/documentiAPI', () => ({
  documentiAPI: { getTipi: vi.fn(), list: vi.fn(), download: vi.fn(), view: vi.fn() },
}));

const tipi = [
  { codice: 'APE', nome: 'Attestato di prestazione energetica', categoria: 'immobiliare', promemoria_giorni: [90, 30] },
  { codice: 'VISURA_CATASTALE', nome: 'Visura catastale', categoria: 'immobiliare' },
];

function renderAt(url) {
  return render(<MemoryRouter initialEntries={[url]}><DocumentiImmobiliPage /></MemoryRouter>);
}

describe('DocumentiImmobiliPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    documentiAPI.getTipi.mockResolvedValue({ data: tipi });
    documentiAPI.list.mockResolvedValue({ data: [
      { id: 4, entity_type: 'IMMOBILE', entity_id: 2, entity_label: 'MI-0002 · VIA ARCHIMEDE n. 73A, Milano',
        tipo_codice: 'APE', tipo_nome: 'Attestato di prestazione energetica', stato: 'CORRENTE',
        data_riferimento: '2024-03-15', data_scadenza_effettiva: '2034-03-15', files: [] },
    ] });
  });

  it('reads the type filter from the URL', async () => {
    renderAt('/immobili/documenti?tipo=APE');
    await waitFor(() => expect(documentiAPI.list).toHaveBeenCalledWith(
      expect.objectContaining({ entity_type: 'IMMOBILE', modulo: 'immobili', tipo_codice: 'APE', includi_sostituiti: false }),
    ));
    const link = await screen.findByRole('link', { name: /MI-0002/ });
    expect(link).toHaveAttribute('href', '/unita-immobiliari/2');
  });

  it('shows superseded documents on request', async () => {
    renderAt('/immobili/documenti');
    await screen.findByRole('link', { name: /MI-0002/ });
    fireEvent.click(screen.getByLabelText(/mostra anche i sostituiti/i));
    await waitFor(() => expect(documentiAPI.list).toHaveBeenLastCalledWith(
      expect.objectContaining({ includi_sostituiti: true }),
    ));
  });

  it('filters by expiry', async () => {
    renderAt('/immobili/documenti');
    await screen.findByRole('link', { name: /MI-0002/ });
    fireEvent.change(screen.getByLabelText('Scadenza'), { target: { value: '90' } });
    await waitFor(() => expect(documentiAPI.list).toHaveBeenLastCalledWith(
      expect.objectContaining({ scadenza_entro_giorni: 90 }),
    ));
  });
});
