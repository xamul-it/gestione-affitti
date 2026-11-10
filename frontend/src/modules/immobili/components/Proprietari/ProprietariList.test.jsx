import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import ProprietariList from './ProprietariList';
import ConduttoriList from '../Conduttori/ConduttoriList';
import { proprietariAPI, conduttoriAPI } from '../../services/immobiliAPI';
import { relazioniAPI } from '../../../../services/relazioniAPI';

const row = { id: 7, tipo_soggetto: 'PERSONA_FISICA', nome: 'Mario', cognome: 'Rossi' };

vi.mock('../../../anagrafica_italiana/components/SoggettiAnagrafici/SoggettiTable', () => ({
  default: ({ ruolo, title, extraColumns, rowActions }) => (
    <div>
      <h1>{title}</h1>
      <span>ruolo={ruolo}</span>
      {extraColumns.map((c) => <div key={c.field}>{c.label}: {c.render(undefined, row)}</div>)}
      {rowActions.filter((a) => a.onClick).map((a) => (
        <button key={a.id} type="button" onClick={() => a.onClick(row)}>{a.label}</button>
      ))}
    </div>
  ),
  nomeSoggetto: (s) => `${s.nome} ${s.cognome}`,
  linkSoggetto: (s) => `/anagrafiche/persone-fisiche/${s.id}`,
}));
vi.mock('../../services/immobiliAPI', async (importOriginal) => ({
  ...(await importOriginal()),
  proprietariAPI: { getAll: vi.fn(), delete: vi.fn() },
  conduttoriAPI: { getAll: vi.fn(), delete: vi.fn() },
}));
vi.mock('../../../../services/relazioniAPI', () => ({ relazioniAPI: { list: vi.fn() } }));
vi.mock('./ProprietarioForm', () => ({ default: () => <div role="dialog">Form proprietario</div> }));
vi.mock('../Conduttori/ConduttoreForm', () => ({ default: () => <div role="dialog">Form conduttore</div> }));

describe('ProprietariList', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    proprietariAPI.getAll.mockResolvedValue({ data: [{ id: 42, soggetto_id: 7, note_proprietario: 'Erede' }] });
    proprietariAPI.delete.mockResolvedValue({});
    relazioniAPI.list.mockResolvedValue({ data: [
      { soggetto_id: 7, tipo: 'proprietario', descrizione: 'Via Roma 1, Milano — Comproprietà 50%', corrente: true },
      { soggetto_id: 7, tipo: 'proprietario', descrizione: 'Via Po 2, Milano — Proprietà 100%', corrente: false },
    ] });
  });

  it('prefilters owners and shows their properties and notes', async () => {
    render(<MemoryRouter><ProprietariList /></MemoryRouter>);
    expect(screen.getByText('ruolo=proprietario')).toBeInTheDocument();
    expect(await screen.findByText(/Via Roma 1, Milano — Comproprietà 50%/)).toBeInTheDocument();
    expect(screen.getByText(/Via Po 2.*\(cessato\)/)).toBeInTheDocument();
    expect(screen.getByText(/Erede/)).toBeInTheDocument();
    expect(relazioniAPI.list).toHaveBeenCalledWith({ tipo: 'proprietario' });
  });

  it('removes the owner record, never the anagrafica', async () => {
    render(<MemoryRouter><ProprietariList /></MemoryRouter>);
    await screen.findByText(/Erede/);
    fireEvent.click(screen.getByRole('button', { name: 'Togli dai proprietari' }));
    expect(screen.getByText(/Togliere Mario Rossi dai proprietari\?/)).toBeInTheDocument();
    expect(screen.getByText(/L'anagrafica resta\./)).toBeInTheDocument();
    fireEvent.click(screen.getAllByRole('button', { name: 'Togli dai proprietari' }).at(-1));
    await waitFor(() => expect(proprietariAPI.delete).toHaveBeenCalledWith(42));
  });

  it('edits the owner notes in the owner form', async () => {
    render(<MemoryRouter><ProprietariList /></MemoryRouter>);
    await screen.findByText(/Erede/);
    fireEvent.click(screen.getByRole('button', { name: 'Modifica note' }));
    expect(screen.getByRole('dialog')).toHaveTextContent('Form proprietario');
  });
});

describe('ConduttoriList', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    conduttoriAPI.getAll.mockResolvedValue({ data: [{ id: 9, soggetto_id: 7, note: '' }] });
    conduttoriAPI.delete.mockResolvedValue({});
    relazioniAPI.list.mockResolvedValue({ data: [
      { soggetto_id: 7, tipo: 'conduttore', descrizione: 'Via Roma 1, Milano', corrente: true },
    ] });
  });

  it('prefilters occupants and removes the occupant record', async () => {
    render(<MemoryRouter><ConduttoriList /></MemoryRouter>);
    expect(screen.getByText('ruolo=conduttore')).toBeInTheDocument();
    expect(await screen.findByText('Via Roma 1, Milano')).toBeInTheDocument();
    expect(screen.getByText(/Unità occupate:/)).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'Togli dai conduttori' }));
    expect(screen.getByText(/Verranno rimosse anche le sue assegnazioni\./)).toBeInTheDocument();
    fireEvent.click(screen.getAllByRole('button', { name: 'Togli dai conduttori' }).at(-1));
    await waitFor(() => expect(conduttoriAPI.delete).toHaveBeenCalledWith(9));
  });
});
