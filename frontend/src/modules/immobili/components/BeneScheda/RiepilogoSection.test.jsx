import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import RiepilogoSection from './RiepilogoSection';
import { beniAPI } from '../../services/immobiliAPI';

vi.mock('../../services/immobiliAPI', () => ({ beniAPI: { getRiepilogo: vi.fn() } }));

const soggetto = (nome, ruolo, quota) => ({ soggetto_id: nome.length, nome, ruolo, quota });
const riepilogo = {
  data: '2026-11-25',
  voci: [
    { codice: 'RENDITA', etichetta: 'Reddito dominicale', norma: 'TUIR artt. 26, 27',
      soggetti: [soggetto('Ugo Usufrutto', 'USUFRUTTUARIO', '100')] },
    { codice: 'SPESE_ORDINARIE', etichetta: 'Spese ordinarie', norma: 'c.c. art. 1004',
      soggetti: [soggetto('Carlo', 'CONDUTTORE', null), soggetto('Dario', 'CONDUTTORE', null)] },
    { codice: 'SPESE_STRAORDINARIE', etichetta: 'Spese straordinarie', norma: 'c.c. art. 1005',
      soggetti: [soggetto('Nino Nudo', 'NUDA_PROPRIETA', '100')] },
    { codice: 'IMU', etichetta: 'IMU', norma: 'L. 160/2019, c. 743', soggetti: [] },
  ],
  avvisi: ['Nessun titolare registrato alla data'],
};

describe('RiepilogoSection', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    beniAPI.getRiepilogo.mockResolvedValue({ data: riepilogo });
  });

  it('mostra voci, soggetti, quote e avvisi', async () => {
    render(<RiepilogoSection beneId={5} />);
    const riga = (await screen.findByText('Spese straordinarie')).closest('tr');
    expect(riga).toHaveTextContent('Nino Nudo');
    expect(riga).toHaveTextContent('100%');
    expect(screen.getByText('Carlo').closest('tr')).toHaveTextContent('—');
    expect(screen.getByText('IMU').closest('tr')).toHaveTextContent('—');
    expect(screen.getByRole('status')).toHaveTextContent('Nessun titolare');
    expect(screen.getByText('Indica a chi spetta ciascuna voce, non calcola importi.')).toBeInTheDocument();
  });

  it('cambio data ricarica', async () => {
    render(<RiepilogoSection beneId={5} />);
    await screen.findByText('Spese straordinarie');
    fireEvent.change(screen.getByLabelText('Alla data'), { target: { value: '2025-01-01' } });
    await waitFor(() => expect(beniAPI.getRiepilogo).toHaveBeenLastCalledWith(5, '2025-01-01'));
  });

  it('403: la sezione non c’è', async () => {
    beniAPI.getRiepilogo.mockRejectedValue({ response: { status: 403 } });
    const { container } = render(<RiepilogoSection beneId={5} />);
    await waitFor(() => expect(container).toBeEmptyDOMElement());
  });
});
