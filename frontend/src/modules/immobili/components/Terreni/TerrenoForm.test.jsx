import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import TerrenoForm from './TerrenoForm';
import { terreniAPI, tipologieTerrenoAPI } from '../../services/immobiliAPI';

vi.mock('../../services/immobiliAPI', () => ({
  terreniAPI: { create: vi.fn(), update: vi.fn() },
  tipologieTerrenoAPI: { getAll: vi.fn() },
}));

describe('TerrenoForm', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    tipologieTerrenoAPI.getAll.mockResolvedValue({ data: [{ id: 3, codice: 'AGR', nome: 'Agricolo' }] });
    terreniAPI.create.mockResolvedValue({ data: { id: 1 } });
    terreniAPI.update.mockResolvedValue({ data: { id: 9 } });
  });

  it('creates a parcel with its portions and without the old single fields', async () => {
    render(<TerrenoForm onClose={vi.fn()} />);
    fireEvent.change(screen.getByLabelText(/^codice/i), { target: { value: 'T-1' } });
    fireEvent.change(screen.getByLabelText(/^comune/i), { target: { value: 'Forlì' } });
    fireEvent.change(screen.getByLabelText(/^provincia/i), { target: { value: 'FC' } });
    fireEvent.change(screen.getByLabelText(/qualità porzione 1/i), { target: { value: 'SEMINATIVO' } });
    fireEvent.change(screen.getByLabelText(/superficie m² porzione 1/i), { target: { value: '536' } });
    fireEvent.click(screen.getByLabelText(/edificabile/i));
    await waitFor(() => expect(screen.getByRole('option', { name: 'Agricolo' })).toBeInTheDocument());
    fireEvent.change(screen.getByLabelText(/^tipologia/i), { target: { value: '3' } });
    fireEvent.click(screen.getByRole('button', { name: 'Salva' }));

    await waitFor(() => expect(terreniAPI.create).toHaveBeenCalled());
    const dati = terreniAPI.create.mock.calls[0][0];
    expect(dati).toMatchObject({ codice: 'T-1', comune: 'Forlì', provincia: 'FC', edificabile: true, tipologia_id: 3 });
    expect(dati.porzioni).toEqual([expect.objectContaining({ qualita: 'SEMINATIVO', superficie_mq: 536, reddito_dominicale: null })]);
    for (const vecchio of ['superficie', 'unita_misura_superficie', 'qualita_coltura', 'classe_catastale', 'reddito_dominicale', 'tipologia']) {
      expect(dati).not.toHaveProperty(vecchio);
    }
  });

  it('edits an existing parcel keeping its portions', async () => {
    const terreno = {
      id: 9, codice: 'T-9', comune: 'Forlì', provincia: 'FC', nome: null, tipologia_id: null,
      edificabile: false, esente_imu_montano: true, servitu: null, attivo: true,
      porzioni: [{ id: 1, porzione: 'AA', qualita: 'PASCOLO', classe: '2', superficie_mq: 63,
        reddito_dominicale: '0.06', reddito_agrario: '0.03', deduzioni: null }],
      superficie_mq: 63, tipo_bene: 'TERRENO', created_at: 'x',
    };
    render(<TerrenoForm terreno={terreno} onClose={vi.fn()} />);
    fireEvent.click(screen.getByRole('button', { name: 'Salva' }));
    await waitFor(() => expect(terreniAPI.update).toHaveBeenCalled());
    const [id, dati] = terreniAPI.update.mock.calls[0];
    expect(id).toBe(9);
    expect(dati.esente_imu_montano).toBe(true);
    expect(dati.porzioni).toEqual([{ porzione: 'AA', qualita: 'PASCOLO', classe: '2', superficie_mq: 63,
      reddito_dominicale: '0.06', reddito_agrario: '0.03', deduzioni: null }]);
    for (const extra of ['id', 'tipo_bene', 'created_at', 'superficie_mq', 'tipologia']) {
      expect(dati).not.toHaveProperty(extra);
    }
  });
});
