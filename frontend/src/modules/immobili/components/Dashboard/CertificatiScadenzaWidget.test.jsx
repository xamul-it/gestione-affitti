import { describe, it, expect, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import CertificatiScadenzaWidget from './CertificatiScadenzaWidget';
import { documentiAPI } from '../../../../services/documentiAPI';

vi.mock('../../../../services/documentiAPI', () => ({ documentiAPI: { list: vi.fn() } }));

const inDays = (n) => { const d = new Date(); d.setDate(d.getDate() + n); return d.toISOString().slice(0, 10); };

describe('CertificatiScadenzaWidget', () => {
  it('lists an APE expiring in 20 days as urgent, from the APE documents', async () => {
    documentiAPI.list.mockResolvedValue({ data: [
      { id: 7, entity_id: 2, entity_label: 'MI-0002 · VIA ARCHIMEDE n. 73A, Milano', dati: { classe: 'C' },
        data_scadenza_effettiva: inDays(20) },
    ] });
    const { container } = render(<MemoryRouter><CertificatiScadenzaWidget /></MemoryRouter>);
    expect(await screen.findByText('MI-0002 · VIA ARCHIMEDE n. 73A, Milano')).toBeInTheDocument();
    expect(screen.getByText('APE classe C')).toBeInTheDocument();
    expect(container.querySelector('.certificato-item.urgente')).not.toBeNull();
    await waitFor(() => expect(documentiAPI.list).toHaveBeenCalledWith(
      expect.objectContaining({ entity_type: 'IMMOBILE', tipo_codice: 'APE', scadenza_entro_giorni: 90 }),
    ));
    expect(screen.getAllByRole('link')[0]).toHaveAttribute('href', '/immobili/documenti?tipo=APE');
  });
});
