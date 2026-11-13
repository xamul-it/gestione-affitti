import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, within } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import RelazioniSection from './RelazioniSection';
import { relazioniAPI } from '../../../services/relazioniAPI';

vi.mock('../../../services/relazioniAPI', () => ({ relazioniAPI: { list: vi.fn() } }));

const rel = (over) => ({
  soggetto_id: 3, tipo: 'proprietario', tipo_nome: 'Proprietario', modulo: 'immobili', fonte: 'MODULO',
  entity_type: 'IMMOBILE', entity_id: 12, descrizione: 'Via Roma 1, Milano — Proprietà 100%',
  data_inizio: '2015-03-01', data_fine: null, data_scadenza: null, corrente: true, ...over,
});

describe('RelazioniSection', () => {
  beforeEach(() => vi.clearAllMocks());

  it('groups relations by type with links to the objects', async () => {
    relazioniAPI.list.mockResolvedValue({ data: [
      rel(),
      rel({ tipo: 'amministratore_condominio', tipo_nome: 'Amministratore condominio', fonte: 'CORE',
            entity_type: 'CONDOMINIO', entity_id: 4, descrizione: 'Condominio Aurora',
            data_inizio: '2026-01-15', data_scadenza: '2027-01-15' }),
    ] });
    render(<MemoryRouter><RelazioniSection soggettoId={3} /></MemoryRouter>);
    expect(await screen.findByRole('heading', { name: 'Proprietario' })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /Via Roma 1/ })).toHaveAttribute('href', '/beni/12');
    expect(screen.getByRole('link', { name: 'Condominio Aurora' })).toHaveAttribute('href', '/condomini');
    expect(screen.getByText('15/01/2027')).toBeInTheDocument();
    expect(relazioniAPI.list).toHaveBeenCalledWith({ soggetto_id: 3 });
  });

  it('marks ended relations and hidden objects', async () => {
    relazioniAPI.list.mockResolvedValue({ data: [
      rel({ data_fine: '2020-01-01', corrente: false }),
      rel({ descrizione: null, entity_id: null }),
    ] });
    render(<MemoryRouter><RelazioniSection soggettoId={3} /></MemoryRouter>);
    const rows = await screen.findAllByRole('row');
    expect(within(rows[1]).getByText('Cessata')).toBeInTheDocument();
    expect(within(rows[2]).getAllByRole('cell')[0]).toHaveTextContent(/^—$/);
    expect(within(rows[2]).getByText('In corso')).toBeInTheDocument();
  });

  it('explains the empty state', async () => {
    relazioniAPI.list.mockResolvedValue({ data: [] });
    render(<MemoryRouter><RelazioniSection soggettoId={3} /></MemoryRouter>);
    expect(await screen.findByText(/Nessuna relazione: questa anagrafica non è ancora proprietaria/)).toBeInTheDocument();
  });
});
