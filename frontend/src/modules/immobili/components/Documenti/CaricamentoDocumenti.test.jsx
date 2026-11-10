import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import CaricamentoDocumenti from './CaricamentoDocumenti';
import { caricamentoDocumentiAPI, unitaImmobiliariAPI } from '../../services/immobiliAPI';

vi.mock('../../services/immobiliAPI', () => ({
  caricamentoDocumentiAPI: { analizza: vi.fn(), stato: vi.fn(), rianalizza: vi.fn(), conferma: vi.fn() },
  unitaImmobiliariAPI: { getAll: vi.fn() },
}));
vi.mock('../../../../services/documentiAPI', () => ({
  documentiAPI: { getTipi: vi.fn(() => Promise.resolve({ data: [
    { codice: 'APE', nome: 'Attestato di prestazione energetica' },
    { codice: 'AGIBILITA', nome: 'Agibilità / abitabilità' },
  ] })) },
}));
vi.mock('../ImportVisura/ImportVisuraModal', () => ({
  default: ({ initialFiles, onClose }) => (
    <div>Import visura: {initialFiles[0].name}<button type="button" onClick={onClose}>Chiudi import</button></div>
  ),
}));

const UNITA = { id: 7, codice: 'TO-1', indirizzo: 'Via Po 1', citta: 'Torino' };
const PRONTO = {
  upload_token: 't'.repeat(32), nome_file: 'ape.pdf', esito: 'pronto', tipo_codice: 'APE', unita_id: 7,
  candidati: [], dati: { ep_gl_nren: 111.24, data_emissione: '2021-02-23' }, avvisi: [],
  differenze: [
    { campo: 'indirizzo', attuale: 'Via Po 1', nuovo: 'VIA PO n.3', selezionato: true },
    { campo: 'piano', attuale: '2', nuovo: '3', selezionato: true },
  ],
};

const file = (name) => new File(['x'], name, { type: 'application/pdf' });
const apri = async (nome) => {
  const b = await screen.findByRole('button', { name: nome });
  if (b.getAttribute('aria-expanded') !== 'true') fireEvent.click(b);
};
const trascina = (files) => fireEvent.change(screen.getByLabelText('File del documento'), { target: { files } });

beforeEach(() => {
  vi.clearAllMocks();
  unitaImmobiliariAPI.getAll.mockResolvedValue({ data: [UNITA] });
});
afterEach(() => vi.useRealTimers());

describe('CaricamentoDocumenti', () => {
  it('mostra una riga per file trascinato', async () => {
    caricamentoDocumentiAPI.analizza.mockImplementation((f) => Promise.resolve({ data: { ...PRONTO, nome_file: f.name } }));
    render(<CaricamentoDocumenti />);
    trascina([file('a.pdf'), file('b.pdf')]);
    expect(await screen.findByText('a.pdf')).toBeInTheDocument();
    expect(screen.getByText('b.pdf')).toBeInTheDocument();
  });

  it('esito pronto mostra immobile, dati e differenze', async () => {
    caricamentoDocumentiAPI.analizza.mockResolvedValue({ data: PRONTO });
    render(<CaricamentoDocumenti />);
    trascina([file('ape.pdf')]);
    await apri(/ape\.pdf/);
    expect(await screen.findByText('TO-1 · Via Po 1, Torino', { selector: 'dd' })).toBeInTheDocument();
    expect(screen.getByText(/111,24/)).toBeInTheDocument();
    expect(screen.getByLabelText(/Indirizzo: da Via Po 1 a VIA PO n\.3/)).toBeChecked();
  });

  it('scegli_tipo chiede il tipo e rianalizza', async () => {
    caricamentoDocumentiAPI.analizza.mockResolvedValue({ data: { ...PRONTO, esito: 'scegli_tipo', tipo_codice: null,
      unita_id: null, differenze: [], messaggio: 'Tipo di documento non riconosciuto: sceglilo' } });
    caricamentoDocumentiAPI.rianalizza.mockResolvedValue({ data: { ...PRONTO, tipo_codice: 'AGIBILITA', differenze: [] } });
    render(<CaricamentoDocumenti />);
    trascina([file('x.pdf')]);
    await apri(/x\.pdf/);
    fireEvent.change(await screen.findByLabelText('Tipo di documento'), { target: { value: 'AGIBILITA' } });
    await waitFor(() => expect(caricamentoDocumentiAPI.rianalizza).toHaveBeenCalledWith(
      { upload_token: PRONTO.upload_token, tipo_codice: 'AGIBILITA', unita_id: null }));
  });

  it('scartato mostra il messaggio e nessun pulsante conferma', async () => {
    caricamentoDocumentiAPI.analizza.mockResolvedValue({ data: { ...PRONTO, esito: 'scartato',
      messaggio: 'Ricevuta di registrazione del contratto: caricala dal contratto, nel modulo Affitti' } });
    render(<CaricamentoDocumenti />);
    trascina([file('rli.pdf')]);
    await apri(/rli\.pdf/);
    expect(await screen.findByText(/caricala dal contratto/)).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Conferma' })).toBeNull();
  });

  it('conferma invia solo le differenze selezionate', async () => {
    caricamentoDocumentiAPI.analizza.mockResolvedValue({ data: PRONTO });
    caricamentoDocumentiAPI.conferma.mockResolvedValue({ data: { documento_id: 1, unita_id: 7 } });
    const onCaricato = vi.fn();
    render(<CaricamentoDocumenti onCaricato={onCaricato} />);
    trascina([file('ape.pdf')]);
    await apri(/ape\.pdf/);
    fireEvent.click(await screen.findByLabelText(/Piano: da 2 a 3/));
    fireEvent.change(screen.getByLabelText('Classe energetica'), { target: { value: 'C' } });
    fireEvent.click(screen.getByRole('button', { name: 'Conferma' }));
    await waitFor(() => expect(caricamentoDocumentiAPI.conferma).toHaveBeenCalled());
    const body = caricamentoDocumentiAPI.conferma.mock.calls[0][0];
    expect(body.differenze.filter((d) => d.selezionato).map((d) => d.campo)).toEqual(['indirizzo']);
    expect(body.dati.classe).toBe('C');
    await waitFor(() => expect(onCaricato).toHaveBeenCalled());
  });

  it("visura apre l'import visure", async () => {
    caricamentoDocumentiAPI.analizza.mockResolvedValue({ data: { ...PRONTO, esito: 'visura', tipo_codice: 'VISURA_CATASTALE' } });
    render(<CaricamentoDocumenti />);
    trascina([file('visura.pdf')]);
    await apri(/visura\.pdf/);
    expect(await screen.findByText('Import visura: visura.pdf')).toBeInTheDocument();
  });

  it('in_lettura si aggiorna quando il lavoro finisce', async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    caricamentoDocumentiAPI.analizza.mockResolvedValue({ data: { ...PRONTO, esito: 'in_lettura', job_uuid: 'j' } });
    caricamentoDocumentiAPI.stato.mockResolvedValue({ data: PRONTO });
    render(<CaricamentoDocumenti />);
    trascina([file('scan.jpg')]);
    expect(await screen.findByText('In lettura')).toBeInTheDocument();
    await act(async () => { vi.advanceTimersByTime(10000); });
    await waitFor(() => expect(caricamentoDocumentiAPI.stato).toHaveBeenCalledWith(PRONTO.upload_token));
    expect(await screen.findByText('Letto')).toBeInTheDocument();
  });

  it('apre da sola la prima riga che richiede un\'azione', async () => {
    caricamentoDocumentiAPI.analizza.mockResolvedValue({ data: { ...PRONTO, esito: 'scegli_tipo', tipo_codice: null,
      unita_id: null, differenze: [] } });
    render(<CaricamentoDocumenti />);
    trascina([file('x.pdf')]);
    await waitFor(() => expect(screen.getByRole('button', { name: /x\.pdf/ })).toHaveAttribute('aria-expanded', 'true'));
  });

  it('il motivo dello scarto si legge nella riga chiusa', async () => {
    caricamentoDocumentiAPI.analizza.mockResolvedValue({ data: { ...PRONTO, esito: 'scartato',
      messaggio: 'Ricevuta di registrazione del contratto: caricala dal contratto, nel modulo Affitti' } });
    render(<CaricamentoDocumenti />);
    trascina([file('rli.pdf')]);
    expect(await screen.findByText(/caricala dal contratto/)).toBeInTheDocument();
  });

  it('la visura si chiude dal suo pannello', async () => {
    caricamentoDocumentiAPI.analizza.mockResolvedValue({ data: { ...PRONTO, esito: 'visura', tipo_codice: 'VISURA_CATASTALE' } });
    render(<CaricamentoDocumenti />);
    trascina([file('visura.pdf')]);
    await apri(/visura\.pdf/);
    fireEvent.click(await screen.findByRole('button', { name: 'Chiudi import' }));
    expect(screen.getByRole('button', { name: /visura\.pdf/ })).toHaveAttribute('aria-expanded', 'false');
  });

  it('dopo tre controlli falliti la lettura passa in errore', async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    caricamentoDocumentiAPI.analizza.mockResolvedValue({ data: { ...PRONTO, esito: 'in_lettura', job_uuid: 'j' } });
    caricamentoDocumentiAPI.stato.mockRejectedValue(new Error('rete'));
    render(<CaricamentoDocumenti />);
    trascina([file('scan.jpg')]);
    expect(await screen.findByText('In lettura')).toBeInTheDocument();
    for (let i = 0; i < 3; i += 1) {
      await act(async () => { vi.advanceTimersByTime(10000); });
    }
    expect(await screen.findByText('Errore')).toBeInTheDocument();
    expect(screen.getByText(/Impossibile verificare la lettura/)).toBeInTheDocument();
  });
});
