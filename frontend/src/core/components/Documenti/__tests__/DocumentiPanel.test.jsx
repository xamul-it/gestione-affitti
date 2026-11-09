import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor, within } from '@testing-library/react';
import DocumentiPanel from '../DocumentiPanel';
import { documentiAPI } from '../../../../services/documentiAPI';

vi.mock('../../../../services/documentiAPI', () => ({
  documentiAPI: {
    getTipi: vi.fn(), list: vi.fn(), upload: vi.fn(), remove: vi.fn(),
    download: vi.fn(), view: vi.fn(),
  },
}));

const tipi = [
  { id: 1, codice: 'APE', nome: 'Attestato di prestazione energetica', categoria: 'immobiliare',
    regime: 'SOSTITUTIVO', scadenza: { mesi: 120, da: 'data_riferimento' }, promemoria_giorni: [90, 30], form: null },
  { id: 2, codice: 'TITOLO_EDILIZIO', nome: 'Titolo edilizio', categoria: 'immobiliare',
    regime: 'CUMULATIVO', scadenza: null, form: null },
];

const iso = (d) => d.toISOString().slice(0, 10);
const daysFromNow = (n) => { const d = new Date(); d.setDate(d.getDate() + n); return iso(d); };

const doc = (over) => ({
  id: 1, entity_type: 'IMMOBILE', entity_id: 5, tipo_codice: 'APE', tipo_nome: 'Attestato di prestazione energetica',
  regime: 'SOSTITUTIVO', stato: 'CORRENTE', data_riferimento: '2024-03-15', data_scadenza_effettiva: '2034-03-15',
  sottotipo: null, files: [{ id: 10, nome_file: 'ape.pdf', mime_type: 'application/pdf' }], nome_file: 'ape.pdf',
  ...over,
});

describe('DocumentiPanel', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    documentiAPI.getTipi.mockResolvedValue({ data: tipi });
  });

  it('shows the document in force and hides the history until asked', async () => {
    documentiAPI.list.mockResolvedValue({ data: [
      doc({ id: 2 }),
      doc({ id: 1, stato: 'SOSTITUITO', data_riferimento: '2014-03-15', nome_file: 'vecchio.pdf' }),
    ] });
    render(<DocumentiPanel entityType="IMMOBILE" entityId={5} />);
    expect(await screen.findByText('Attestato di prestazione energetica')).toBeInTheDocument();
    expect(screen.queryByText('15/03/2014')).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: /storico \(1\)/i }));
    expect(screen.getByText('15/03/2014')).toBeInTheDocument();
    expect(documentiAPI.list).toHaveBeenCalledWith({ entity_type: 'IMMOBILE', entity_id: 5, includi_sostituiti: true });
  });

  it('marks expired and expiring documents', async () => {
    documentiAPI.list.mockResolvedValue({ data: [
      doc({ id: 1, data_scadenza_effettiva: daysFromNow(-1) }),
      doc({ id: 2, entity_id: 5, tipo_codice: 'TITOLO_EDILIZIO', tipo_nome: 'Titolo edilizio', regime: 'CUMULATIVO',
            data_scadenza_effettiva: null }),
    ] });
    render(<DocumentiPanel entityType="IMMOBILE" entityId={5} />);
    expect(await screen.findByText('Scaduto')).toBeInTheDocument();
  });

  it('marks a document expiring within the reminder window', async () => {
    documentiAPI.list.mockResolvedValue({ data: [doc({ data_scadenza_effettiva: daysFromNow(20) })] });
    render(<DocumentiPanel entityType="IMMOBILE" entityId={5} />);
    expect(await screen.findByText('In scadenza')).toBeInTheDocument();
  });

  it('shows the empty state', async () => {
    documentiAPI.list.mockResolvedValue({ data: [] });
    render(<DocumentiPanel entityType="IMMOBILE" entityId={5} />);
    expect(await screen.findByText('Nessun documento')).toBeInTheDocument();
  });

  it('opens the upload form', async () => {
    documentiAPI.list.mockResolvedValue({ data: [] });
    render(<DocumentiPanel entityType="IMMOBILE" entityId={5} />);
    fireEvent.click(await screen.findByRole('button', { name: /carica documento/i }));
    expect(screen.getByRole('dialog')).toBeInTheDocument();
    expect(within(screen.getByRole('dialog')).getByLabelText('Tipologia')).toBeInTheDocument();
  });
});
