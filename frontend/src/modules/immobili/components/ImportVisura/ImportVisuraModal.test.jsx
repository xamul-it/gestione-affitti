import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import ImportVisuraModal from './ImportVisuraModal';
import { visuraImportAPI } from '../../services/immobiliAPI';

vi.mock('../../services/immobiliAPI', () => ({
  visuraImportAPI: { preview: vi.fn(), apply: vi.fn() },
}));

const proposta = {
  upload_token: 'a'.repeat(32),
  formato: 'SINTETICA',
  numero_visura: 'T234664/2025',
  data_visura: '2025-12-16',
  avvisi: [],
  soggetti: [
    {
      key: 's0', azione: 'crea', soggetto_id: null, persona_giuridica: false,
      nominativo: 'ZANDERIGHI Luigi', cognome: 'ZANDERIGHI', nome: 'Luigi',
      codice_fiscale: 'ZNDLMT73E17F205F', campi_da_completare: [], selezionato: true,
    },
  ],
  unita: [
    {
      key: 'u0', azione: 'crea', unita_id: null, foglio: '99', particella: '666', subalterno: '30',
      tipo: null, indirizzo: 'VIA EMILIA PONENTE n. 1', citta: 'Bologna', provincia: 'BO',
      piano: 'T', categoria: 'D/1', rendita_catastale: 100, note_catastali: '', modifiche: [],
      diritti: [{ soggetto_key: 's0', nominativo: 'ZANDERIGHI Luigi', tipo_diritto: 'PROPRIETARIO', quota_percentuale: 100, note: "Proprieta' 1/1", azione: 'crea', selezionato: true }],
      avvisi: [], selezionato: true,
    },
    {
      key: 'u1', azione: 'invariato', unita_id: 7, foglio: '99', particella: '666', subalterno: '19',
      tipo: 'Appartamento', indirizzo: 'VIA EMILIA PONENTE n. 354', citta: 'Bologna', provincia: 'BO',
      piano: 'S1', categoria: 'A/3', rendita_catastale: 1316.97, note_catastali: '', modifiche: [],
      diritti: [], avvisi: [], selezionato: true,
    },
  ],
};

async function uploadAndAnalyze() {
  const file = new File(['%PDF'], 'visura.pdf', { type: 'application/pdf' });
  fireEvent.change(screen.getByLabelText(/file pdf/i), { target: { files: [file] } });
  fireEvent.click(screen.getByRole('button', { name: /analizza/i }));
}

describe('ImportVisuraModal', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders upload step with Visura catastale option', () => {
    render(<ImportVisuraModal onClose={() => {}} onImported={() => {}} />);
    expect(screen.getByRole('option', { name: 'Visura catastale' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /analizza/i })).toBeDisabled();
  });

  it('shows sections after preview', async () => {
    visuraImportAPI.preview.mockResolvedValue({ data: proposta });
    render(<ImportVisuraModal onClose={() => {}} onImported={() => {}} />);
    await uploadAndAnalyze();
    expect(await screen.findByText('Anagrafiche da aggiungere')).toBeInTheDocument();
    expect(screen.getByText('Immobili da aggiungere')).toBeInTheDocument();
    expect(screen.getByText(/Già presenti/)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /^importa$/i })).toBeDisabled();
  });

  it('enables import when tipo filled and sends deselections', async () => {
    visuraImportAPI.preview.mockResolvedValue({ data: proposta });
    visuraImportAPI.apply.mockResolvedValue({
      data: { soggetti_creati: 0, soggetti_aggiornati: 0, unita_create: [1], unita_aggiornate: [], diritti_creati: 0, documenti_allegati: 1 },
    });
    render(<ImportVisuraModal onClose={() => {}} onImported={() => {}} />);
    await uploadAndAnalyze();
    fireEvent.change(await screen.findByLabelText(/tipo immobile foglio 99 particella 666 sub 30/i), {
      target: { value: 'Appartamento' },
    });
    fireEvent.click(screen.getByLabelText(/seleziona ZANDERIGHI Luigi/i));
    const importa = screen.getByRole('button', { name: /^importa$/i });
    expect(importa).toBeEnabled();
    fireEvent.click(importa);
    await waitFor(() => expect(visuraImportAPI.apply).toHaveBeenCalled());
    const [token, sent] = visuraImportAPI.apply.mock.calls[0];
    expect(token).toBe('a'.repeat(32));
    expect(sent.unita[0].tipo).toBe('Appartamento');
    expect(sent.soggetti[0].selezionato).toBe(false);
    expect(await screen.findByText(/Import completato/i)).toBeInTheDocument();
  });

  it('shows backend error detail', async () => {
    visuraImportAPI.preview.mockRejectedValue({
      response: { data: { detail: 'Formato non supportato: carica una visura catastale sintetica o analitica' } },
    });
    render(<ImportVisuraModal onClose={() => {}} onImported={() => {}} />);
    await uploadAndAnalyze();
    expect(await screen.findByText(/Formato non supportato/)).toBeInTheDocument();
  });

  it('processes several files as a queue: next preview only after import', async () => {
    visuraImportAPI.preview.mockResolvedValue({ data: proposta });
    visuraImportAPI.apply.mockResolvedValue({
      data: { soggetti_creati: 1, soggetti_aggiornati: 0, unita_create: [1], unita_aggiornate: [], diritti_creati: 1, documenti_allegati: 1 },
    });
    render(<ImportVisuraModal onClose={() => {}} onImported={() => {}} />);
    const a = new File(['%PDF'], 'a.pdf', { type: 'application/pdf' });
    const b = new File(['%PDF-b'], 'b.pdf', { type: 'application/pdf' });
    fireEvent.change(screen.getByLabelText(/file pdf/i), { target: { files: [a, b] } });
    fireEvent.click(screen.getByRole('button', { name: /analizza 2 file/i }));

    expect(await screen.findByText('Visura 1 di 2')).toBeInTheDocument();
    expect(visuraImportAPI.preview).toHaveBeenCalledTimes(1);
    expect(visuraImportAPI.preview.mock.calls[0][0].name).toBe('a.pdf');

    fireEvent.change(screen.getByLabelText(/tipo immobile foglio 99 particella 666 sub 30/i), {
      target: { value: 'Box' },
    });
    fireEvent.click(screen.getByRole('button', { name: /^importa$/i }));

    expect(await screen.findByText('Visura 2 di 2')).toBeInTheDocument();
    expect(visuraImportAPI.preview).toHaveBeenCalledTimes(2);
    expect(visuraImportAPI.preview.mock.calls[1][0].name).toBe('b.pdf');
    expect(visuraImportAPI.apply).toHaveBeenCalledTimes(1);
  });

  it('skips a visura and reports per-file outcome', async () => {
    visuraImportAPI.preview.mockResolvedValue({ data: proposta });
    const onImported = vi.fn();
    render(<ImportVisuraModal onClose={() => {}} onImported={onImported} />);
    await uploadAndAnalyze();
    fireEvent.click(await screen.findByRole('button', { name: /salta/i }));
    expect(await screen.findByText('Nessuna visura importata')).toBeInTheDocument();
    expect(screen.getByText('Saltata')).toBeInTheDocument();
    expect(visuraImportAPI.apply).not.toHaveBeenCalled();
    fireEvent.click(screen.getAllByRole('button', { name: /chiudi/i }).at(-1));
    expect(onImported).not.toHaveBeenCalled();
  });

  it('accepts dropped files and flags non-PDF files without analysing them', async () => {
    visuraImportAPI.preview.mockResolvedValue({ data: proposta });
    render(<ImportVisuraModal onClose={() => {}} onImported={() => {}} />);
    const pdf = new File(['%PDF'], 'visura.pdf', { type: 'application/pdf' });
    const txt = new File(['x'], 'note.txt', { type: 'text/plain' });
    fireEvent.drop(screen.getByText(/trascina qui/i).closest('.visura-dropzone'), {
      dataTransfer: { files: [pdf, txt] },
    });
    expect(screen.getByText('visura.pdf')).toBeInTheDocument();
    expect(screen.getByText('Non è un file PDF')).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: /^analizza$/i }));
    expect(await screen.findByText('Visura 1 di 2')).toBeInTheDocument();
    expect(visuraImportAPI.preview).toHaveBeenCalledTimes(1);
  });

  it('asks for confirmation before closing mid-review', async () => {
    visuraImportAPI.preview.mockResolvedValue({ data: proposta });
    const onClose = vi.fn();
    render(<ImportVisuraModal onClose={onClose} onImported={() => {}} />);
    await uploadAndAnalyze();
    await screen.findByText('Anagrafiche da aggiungere');
    fireEvent.click(screen.getAllByRole('button', { name: /chiudi/i })[0]);
    expect(screen.getByText("Interrompere l'importazione?")).toBeInTheDocument();
    expect(onClose).not.toHaveBeenCalled();
    fireEvent.click(screen.getByRole('button', { name: /interrompi/i }));
    expect(onClose).toHaveBeenCalled();
  });
});

describe('ImportVisuraModal with initial files', () => {
  it('puts the files received from the document upload in the queue', () => {
    const file = new File(['%PDF'], 'stefi.pdf', { type: 'application/pdf' });
    render(<ImportVisuraModal onClose={() => {}} onImported={() => {}} initialFiles={[file]} embedded />);
    expect(screen.getByText('stefi.pdf')).toBeInTheDocument();
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
  });
});
