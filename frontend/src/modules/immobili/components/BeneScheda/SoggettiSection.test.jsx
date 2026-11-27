import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor, within } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import SoggettiSection from './SoggettiSection';
import { beniAPI } from '../../services/immobiliAPI';
import { relazioniAPI } from '../../../../services/relazioniAPI';
import { subscribeToToasts } from '../../../../core/hooks/useToast';

vi.mock('../../services/immobiliAPI', () => ({
  beniAPI: { getRelazioni: vi.fn(), createRelazione: vi.fn() },
}));
vi.mock('../../../../services/relazioniAPI', () => ({
  relazioniAPI: { getTipi: vi.fn(), update: vi.fn(), remove: vi.fn() },
}));
vi.mock('../../../../core/components/Documenti/DocumentiPanel', () => ({
  default: ({ entityType, entityId }) => <div>Pannello documenti {entityType} {entityId}</div>,
}));
vi.mock('../../../anagrafica_italiana/components/SoggettiAnagrafici/SoggettoPicker', () => ({
  default: ({ label, value, onSelect }) => (
    <div>
      <span>{label}: {value ? 'scelto' : 'nessuno'}</span>
      <button type="button" onClick={() => onSelect({ id: 7, tipo_soggetto: 'PERSONA_FISICA', nome: 'Mario', cognome: 'Rossi' })}>
        Scegli anagrafica
      </button>
    </div>
  ),
}));

const risposta = {
  diritti_reali: [
    { id: 1, tipo: 'proprieta', tipo_nome: 'Proprietà', soggetto_id: 7, soggetto_nome: 'Mario Rossi',
      quota_numeratore: 1, quota_denominatore: 2, quota: '1/2', data_inizio: '2020-01-01', data_fine: null, note: null, dati: null },
  ],
  godimento: [
    { id: 2, tipo: 'conduttore', tipo_nome: 'Conduttore', soggetto_id: 8, soggetto_nome: 'Anna Bianchi',
      quota_numeratore: null, quota_denominatore: null, quota: null, data_inizio: '2024-01-01', data_fine: null, note: null, dati: null },
  ],
  incarichi: [],
};

const tipi = {
  diritti_reali: [{ codice: 'proprieta', nome: 'Proprietà', famiglia: 'diritti_reali', ammette_quota: true }],
  godimento: [
    { codice: 'conduttore', nome: 'Conduttore', famiglia: 'godimento', ammette_quota: false },
    { codice: 'comodatario', nome: 'Comodatario', famiglia: 'godimento', ammette_quota: false },
  ],
  incarichi: [{ codice: 'gestore', nome: 'Gestore', famiglia: 'incarichi', ammette_quota: false }],
};

const renderSezione = (props = {}) => render(
  <MemoryRouter><SoggettiSection beneId={5} onChange={vi.fn()} {...props} /></MemoryRouter>,
);
const blocco = (nome) => screen.getByRole('region', { name: nome });

describe('SoggettiSection', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    beniAPI.getRelazioni.mockResolvedValue({ data: risposta });
    beniAPI.createRelazione.mockResolvedValue({ data: { relazione: risposta.godimento[0], avvisi: [] } });
    relazioniAPI.getTipi.mockImplementation((_et, famiglia) => Promise.resolve({ data: tipi[famiglia] }));
  });

  it('renders the three blocks in order, loading only current relations', async () => {
    renderSezione();
    expect(await screen.findByText('Mario Rossi')).toBeInTheDocument();
    const titoli = screen.getAllByRole('heading', { level: 4 }).map((h) => h.textContent);
    expect(titoli).toEqual(['Diritti reali', 'Godimento', 'Incarichi']);
    expect(screen.getByRole('link', { name: 'Mario Rossi' })).toHaveAttribute('href', '/anagrafiche/7');
    expect(within(blocco('Incarichi')).getByText('Nessun incarico')).toBeInTheDocument();
    expect(beniAPI.getRelazioni).toHaveBeenCalledWith(5, { soloCorrenti: true });
  });

  it('shows the quota only in the diritti reali block', async () => {
    renderSezione();
    await screen.findByText('Mario Rossi');
    expect(within(blocco('Diritti reali')).getByText('1/2')).toBeInTheDocument();
    expect(within(blocco('Godimento')).queryByText('Quota')).not.toBeInTheDocument();
  });

  it('reloads with soloCorrenti=false when showing closed relations', async () => {
    renderSezione();
    await screen.findByText('Mario Rossi');
    fireEvent.click(screen.getByLabelText('Mostra chiuse'));
    await waitFor(() => expect(beniAPI.getRelazioni).toHaveBeenLastCalledWith(5, { soloCorrenti: false }));
  });

  it('conduttore form has no quota, comodatario shows the registration fields', async () => {
    renderSezione();
    await screen.findByText('Mario Rossi');
    fireEvent.click(within(blocco('Godimento')).getByRole('button', { name: /Aggiungi/ }));
    const dialog = await screen.findByRole('dialog');
    await within(dialog).findByLabelText('Tipo');
    expect(within(dialog).queryByLabelText(/Quota/)).not.toBeInTheDocument();
    expect(within(dialog).queryByLabelText('Data di registrazione')).not.toBeInTheDocument();
    fireEvent.change(within(dialog).getByLabelText('Tipo'), { target: { value: 'comodatario' } });
    expect(within(dialog).getByLabelText('Data di registrazione')).toBeInTheDocument();
    expect(within(dialog).getByLabelText('Ufficio di registrazione')).toBeInTheDocument();
    expect(within(dialog).getByLabelText('Numero di registrazione')).toBeInTheDocument();
  });

  it('diritti reali form validates the quota like the backend', async () => {
    renderSezione();
    await screen.findByText('Mario Rossi');
    fireEvent.click(within(blocco('Diritti reali')).getByRole('button', { name: /Aggiungi/ }));
    const dialog = await screen.findByRole('dialog');
    fireEvent.click(within(dialog).getByText('Scegli anagrafica'));
    fireEvent.change(await within(dialog).findByLabelText(/Quota/), { target: { value: '3/2' } });
    fireEvent.click(within(dialog).getByRole('button', { name: 'Salva' }));
    expect(await within(dialog).findByText(/quota non valida/i)).toBeInTheDocument();
    expect(beniAPI.createRelazione).not.toHaveBeenCalled();
    fireEvent.change(within(dialog).getByLabelText(/Quota/), { target: { value: '1 / 2' } });
    fireEvent.click(within(dialog).getByRole('button', { name: 'Salva' }));
    await waitFor(() => expect(beniAPI.createRelazione).toHaveBeenCalledWith(5, expect.objectContaining({
      soggetto_id: 7, tipo: 'proprieta', quota: '1/2',
    })));
  });

  it('shows the warnings of the response as toasts', async () => {
    beniAPI.createRelazione.mockResolvedValue({ data: {
      relazione: risposta.godimento[0], avvisi: ['Quote oltre il 100%'],
    } });
    const messaggi = [];
    const stop = subscribeToToasts((t) => { messaggi.push(t); });
    renderSezione();
    await screen.findByText('Mario Rossi');
    fireEvent.click(within(blocco('Godimento')).getByRole('button', { name: /Aggiungi/ }));
    const dialog = await screen.findByRole('dialog');
    fireEvent.click(within(dialog).getByText('Scegli anagrafica'));
    fireEvent.click(within(dialog).getByRole('button', { name: 'Salva' }));
    await waitFor(() => expect(messaggi.some((t) => t.type === 'warning' && /Quote oltre il 100%/.test(t.message))).toBe(true));
    stop();
  });

  it('closes a relation with an end date and deletes after confirmation', async () => {
    relazioniAPI.update.mockResolvedValue({});
    relazioniAPI.remove.mockResolvedValue({});
    const onChange = vi.fn();
    renderSezione({ onChange });
    fireEvent.click(await screen.findByRole('button', { name: 'Chiudi la relazione di Anna Bianchi' }));
    fireEvent.change(screen.getByLabelText('Fino al'), { target: { value: '2026-03-31' } });
    fireEvent.click(screen.getByRole('button', { name: 'Conferma' }));
    await waitFor(() => expect(relazioniAPI.update).toHaveBeenCalledWith(2, { data_fine: '2026-03-31' }));
    await waitFor(() => expect(onChange).toHaveBeenCalled());

    fireEvent.click(await screen.findByRole('button', { name: 'Elimina la relazione di Mario Rossi' }));
    fireEvent.click(within(screen.getByRole('dialog')).getByRole('button', { name: 'Elimina' }));
    await waitFor(() => expect(relazioniAPI.remove).toHaveBeenCalledWith(1));
  });

  it('opens the documents of a relation', async () => {
    renderSezione();
    fireEvent.click(await screen.findByRole('button', { name: 'Documenti della relazione di Mario Rossi' }));
    expect(await screen.findByText('Pannello documenti RELAZIONE 1')).toBeInTheDocument();
  });
});

describe('SoggettiSection - edit', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    relazioniAPI.getTipi.mockImplementation((_et, famiglia) => Promise.resolve({ data: tipi[famiglia] }));
  });

  it('keeps quota on edit of a diritto reale', async () => {
    beniAPI.getRelazioni.mockResolvedValue({ data: risposta });
    relazioniAPI.update.mockResolvedValue({});
    renderSezione();
    fireEvent.click(await screen.findByRole('button', { name: 'Modifica la relazione di Mario Rossi' }));
    const dialog = await screen.findByRole('dialog');
    await waitFor(() => expect(within(dialog).getByLabelText(/Quota/)).toHaveValue('1/2'));
    fireEvent.click(within(dialog).getByRole('button', { name: 'Salva' }));
    await waitFor(() => expect(relazioniAPI.update).toHaveBeenCalledWith(1, expect.objectContaining({ quota: '1/2' })));
  });

  it('keeps other dati keys and registration data of a comodatario', async () => {
    const comodato = { id: 3, tipo: 'comodatario', tipo_nome: 'Comodatario', soggetto_id: 8, soggetto_nome: 'Anna Bianchi',
      quota: null, data_inizio: '2024-01-01', data_fine: null, note: null,
      dati: { registrazione_ufficio: 'Milano', altro: 'x' } };
    beniAPI.getRelazioni.mockResolvedValue({ data: { ...risposta, godimento: [comodato] } });
    relazioniAPI.update.mockResolvedValue({});
    renderSezione();
    fireEvent.click(await screen.findByRole('button', { name: 'Modifica la relazione di Anna Bianchi' }));
    const dialog = await screen.findByRole('dialog');
    fireEvent.change(within(dialog).getByLabelText('Numero di registrazione'), { target: { value: '55' } });
    fireEvent.click(within(dialog).getByRole('button', { name: 'Salva' }));
    await waitFor(() => expect(relazioniAPI.update).toHaveBeenCalledWith(3, expect.objectContaining({
      dati: { registrazione_ufficio: 'Milano', altro: 'x', registrazione_numero: '55' },
    })));
  });

  it('shows a 422 error in the form and rejects an end before the start', async () => {
    beniAPI.getRelazioni.mockResolvedValue({ data: risposta });
    beniAPI.createRelazione.mockRejectedValue({ response: { status: 422, data: { detail: 'Esiste già un conduttore' } } });
    renderSezione();
    await screen.findByText('Mario Rossi');
    fireEvent.click(within(blocco('Godimento')).getByRole('button', { name: /Aggiungi/ }));
    const dialog = await screen.findByRole('dialog');
    fireEvent.click(within(dialog).getByText('Scegli anagrafica'));
    fireEvent.change(within(dialog).getByLabelText('Dal'), { target: { value: '2024-05-01' } });
    fireEvent.change(within(dialog).getByLabelText('Fino al'), { target: { value: '2024-04-01' } });
    fireEvent.click(within(dialog).getByRole('button', { name: 'Salva' }));
    expect(await within(dialog).findByText(/data di fine non può precedere/)).toBeInTheDocument();
    expect(beniAPI.createRelazione).not.toHaveBeenCalled();
    fireEvent.change(within(dialog).getByLabelText('Fino al'), { target: { value: '' } });
    fireEvent.click(within(dialog).getByRole('button', { name: 'Salva' }));
    expect(await within(dialog).findByText(/Esiste già un conduttore/)).toBeInTheDocument();
  });

  it('shows inherited relations read-only, with the ramo they come from', async () => {
    beniAPI.getRelazioni.mockResolvedValue({ data: { ...risposta, incarichi: [
      { id: 3, tipo: 'manutentore', tipo_nome: 'Manutentore', soggetto_id: 9, soggetto_nome: 'Caldaie Srl',
        quota: null, data_inizio: null, data_fine: null, note: null, dati: null,
        provenienza: { raggruppamento_id: 2, nome: 'Edificio A', tipo: 'EDIFICIO' } },
    ] } });
    renderSezione();
    const incarichi = await screen.findByRole('region', { name: 'Incarichi' });
    expect(await within(incarichi).findByText('Caldaie Srl')).toBeInTheDocument();
    expect(within(incarichi).getByRole('link', { name: 'dal raggruppamento Edificio A' })).toHaveAttribute('href', '/raggruppamenti/2');
    expect(within(incarichi).queryByRole('button', { name: /Caldaie Srl/ })).not.toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Chiudi la relazione di Anna Bianchi' })).toBeInTheDocument();
  });

  it('works on a ramo with its own loader and only some families', async () => {
    const caricaRelazioni = vi.fn().mockResolvedValue({ data: risposta });
    renderSezione({ caricaRelazioni, famiglie: ['godimento', 'incarichi'] });
    expect(await screen.findByText('Anna Bianchi')).toBeInTheDocument();
    expect(caricaRelazioni).toHaveBeenCalledWith({ soloCorrenti: true });
    expect(beniAPI.getRelazioni).not.toHaveBeenCalled();
    expect(screen.queryByRole('region', { name: 'Diritti reali' })).not.toBeInTheDocument();
  });
});
