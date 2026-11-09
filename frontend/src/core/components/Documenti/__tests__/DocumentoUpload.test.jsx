import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import DocumentoUpload from '../DocumentoUpload';
import { documentiAPI } from '../../../../services/documentiAPI';
import { getDocumentForm } from '../../../documenti/documentForms';

vi.mock('../../../../services/documentiAPI', () => ({
  documentiAPI: { upload: vi.fn() },
}));
vi.mock('../../../documenti/documentForms', () => ({ getDocumentForm: vi.fn(() => null) }));

const tipi = [
  { id: 1, codice: 'POLIZZA_FABBRICATO', nome: 'Polizza assicurativa fabbricato', categoria: 'immobiliare',
    regime: 'SOSTITUTIVO', scadenza: { manuale: true }, form: null },
  { id: 2, codice: 'CONFORMITA_IMPIANTO', nome: 'Dichiarazione di conformità impianto', categoria: 'immobiliare',
    regime: 'SOSTITUTIVO', sottotipi: ['ELETTRICO', 'GAS'], scadenza: null, form: null },
  { id: 3, codice: 'APE', nome: 'Attestato di prestazione energetica', categoria: 'immobiliare',
    regime: 'SOSTITUTIVO', scadenza: { mesi: 120, da: 'data_riferimento' }, form: 'test.form' },
];

const pdf = (name) => new File(['%PDF'], name, { type: 'application/pdf' });

function setup(props = {}) {
  const onSaved = vi.fn();
  render(<DocumentoUpload entityType="IMMOBILE" entityId={5} tipi={tipi} onSaved={onSaved} onCancel={() => {}} {...props} />);
  return { onSaved };
}

describe('DocumentoUpload', () => {
  beforeEach(() => vi.clearAllMocks());

  it('requires the expiry date for a manual-scadenza type', async () => {
    setup();
    fireEvent.change(screen.getByLabelText('Tipologia'), { target: { value: 'POLIZZA_FABBRICATO' } });
    fireEvent.change(screen.getByLabelText(/file del documento/i), { target: { files: [pdf('p.pdf')] } });
    expect(screen.getByLabelText(/data di scadenza/i)).toBeRequired();
    fireEvent.click(screen.getByRole('button', { name: /^carica$/i }));
    expect(await screen.findByText(/indica la data di scadenza/i)).toBeInTheDocument();
    expect(documentiAPI.upload).not.toHaveBeenCalled();
  });

  it('uploads files, dates and sottotipo', async () => {
    documentiAPI.upload.mockResolvedValue({ data: { id: 9 } });
    const { onSaved } = setup();
    fireEvent.change(screen.getByLabelText('Tipologia'), { target: { value: 'CONFORMITA_IMPIANTO' } });
    fireEvent.change(screen.getByLabelText('Sottotipo'), { target: { value: 'GAS' } });
    fireEvent.change(screen.getByLabelText(/data del documento/i), { target: { value: '2023-05-02' } });
    fireEvent.change(screen.getByLabelText(/file del documento/i), { target: { files: [pdf('a.pdf'), pdf('b.pdf')] } });
    expect(screen.getByText('a.pdf')).toBeInTheDocument();
    expect(screen.getByText('b.pdf')).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: /^carica$/i }));
    await waitFor(() => expect(onSaved).toHaveBeenCalledWith({ id: 9 }));
    const fd = documentiAPI.upload.mock.calls[0][0];
    expect(fd.get('tipo_codice')).toBe('CONFORMITA_IMPIANTO');
    expect(fd.get('sottotipo')).toBe('GAS');
    expect(fd.get('data_riferimento')).toBe('2023-05-02');
    expect(fd.getAll('files')).toHaveLength(2);
    expect(fd.get('entity_type')).toBe('IMMOBILE');
  });

  it('renders the form registered by the module', async () => {
    getDocumentForm.mockReturnValue(({ tipo, initialFiles }) => (
      <p>Form {tipo.codice} con {initialFiles.length} file</p>
    ));
    setup();
    fireEvent.change(screen.getByLabelText(/file del documento/i), { target: { files: [pdf('ape.pdf')] } });
    fireEvent.change(screen.getByLabelText('Tipologia'), { target: { value: 'APE' } });
    expect(await screen.findByText('Form APE con 1 file')).toBeInTheDocument();
    expect(getDocumentForm).toHaveBeenCalledWith('test.form');
  });
});
