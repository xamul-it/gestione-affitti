import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import ApeForm from './ApeForm';
import { documentiAPI } from '../../../../services/documentiAPI';
import { tecniciAPI } from '../../../../services/api';

vi.mock('../../../../services/documentiAPI', () => ({ documentiAPI: { upload: vi.fn() } }));
vi.mock('../../../../services/api', () => ({ tecniciAPI: { getAll: vi.fn() } }));

const tipo = { codice: 'APE', nome: 'Attestato di prestazione energetica', scadenza: { mesi: 120, da: 'data_riferimento' } };
const pdf = new File(['%PDF'], 'ape.pdf', { type: 'application/pdf' });

function setup(files = [pdf]) {
  const onSaved = vi.fn();
  render(<ApeForm entityType="IMMOBILE" entityId={5} tipo={tipo} initialFiles={files} onSaved={onSaved} onCancel={() => {}} />);
  return { onSaved };
}

describe('ApeForm', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    tecniciAPI.getAll.mockResolvedValue({ data: [{ id: 3, nome: 'Anna', cognome: 'Rossi' }] });
  });

  it('requires classe and data di emissione', async () => {
    setup();
    fireEvent.click(screen.getByRole('button', { name: /^salva$/i }));
    expect(await screen.findByText(/indica la classe energetica/i)).toBeInTheDocument();
    expect(documentiAPI.upload).not.toHaveBeenCalled();
  });

  it('shows the expiry computed from the emission date', () => {
    setup();
    fireEvent.change(screen.getByLabelText(/data di emissione/i), { target: { value: '2024-03-15' } });
    expect(screen.getByText('Scade il 15/03/2034')).toBeInTheDocument();
  });

  it('posts the APE data', async () => {
    documentiAPI.upload.mockResolvedValue({ data: { id: 11 } });
    const { onSaved } = setup();
    await screen.findByRole('option', { name: 'Anna Rossi' });
    fireEvent.change(screen.getByLabelText(/classe energetica/i), { target: { value: 'C' } });
    fireEvent.change(screen.getByLabelText(/epgl,nren/i), { target: { value: '88,5' } });
    fireEvent.change(screen.getByLabelText(/codice identificativo/i), { target: { value: 'APE-123' } });
    fireEvent.change(screen.getByLabelText(/certificatore/i), { target: { value: '3' } });
    fireEvent.change(screen.getByLabelText(/data di emissione/i), { target: { value: '2024-03-15' } });
    fireEvent.click(screen.getByRole('button', { name: /^salva$/i }));
    await waitFor(() => expect(onSaved).toHaveBeenCalledWith({ id: 11 }));
    const fd = documentiAPI.upload.mock.calls[0][0];
    expect(fd.get('tipo_codice')).toBe('APE');
    expect(fd.get('data_riferimento')).toBe('2024-03-15');
    expect(JSON.parse(fd.get('dati'))).toEqual({
      classe: 'C', ep_gl_nren: 88.5, codice_identificativo: 'APE-123', tecnico_id: 3, decaduto_il: null,
    });
    expect(fd.getAll('files')).toHaveLength(1);
  });

  it('requires the PDF of the certificate', async () => {
    setup([]);
    fireEvent.change(screen.getByLabelText(/classe energetica/i), { target: { value: 'C' } });
    fireEvent.change(screen.getByLabelText(/data di emissione/i), { target: { value: '2024-03-15' } });
    fireEvent.click(screen.getByRole('button', { name: /^salva$/i }));
    expect(await screen.findByText(/aggiungi il file dell'ape/i)).toBeInTheDocument();
  });
});
