import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import ProprietariList from './ProprietariList';
import ConduttoriList from '../Conduttori/ConduttoriList';
import { relazioniAPI } from '../../../../services/relazioniAPI';

vi.mock('../../../../services/relazioniAPI', () => ({ relazioniAPI: { list: vi.fn() } }));
vi.mock('../../../anagrafica_italiana/components/SoggettiAnagrafici/SoggettiTable', () => ({
  nomeSoggetto: (s) => `${s.nome} ${s.cognome}`,
}));
vi.mock('../../../anagrafica_italiana/services/anagraficaAPI', () => ({
  soggettiAnagraficiAPI: {},
  getSoggettiAnagrafici: vi.fn().mockResolvedValue([
    { id: 7, tipo_soggetto: 'PERSONA_FISICA', nome: 'Mario', cognome: 'Rossi' },
  ]),
}));

describe('ProprietariList', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    relazioniAPI.list.mockResolvedValue({ data: [
      { relazione_id: 1, soggetto_id: 7, tipo: 'usufrutto', tipo_nome: 'Usufrutto', entity_type: 'IMMOBILE', entity_id: 3,
        descrizione: 'Via Roma 1, Milano', quota: '1/2', data_inizio: '2020-01-01', data_fine: null, corrente: true },
    ] });
  });

  it('lists the diritti reali family with the right and the quota', async () => {
    render(<MemoryRouter><ProprietariList /></MemoryRouter>);
    expect(screen.getByRole('heading', { name: 'Titolari di diritti' })).toBeInTheDocument();
    expect(await screen.findByRole('link', { name: 'Mario Rossi' })).toHaveAttribute('href', '/anagrafiche/7');
    expect(screen.getByText('Usufrutto')).toBeInTheDocument();
    expect(screen.getByText('1/2')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Via Roma 1, Milano' })).toHaveAttribute('href', '/beni/3');
    expect(relazioniAPI.list).toHaveBeenCalledWith({ famiglia: 'diritti_reali', entity_type: 'IMMOBILE', solo_correnti: true });
  });
});

describe('ConduttoriList', () => {
  it('lists the godimento family without quota', async () => {
    relazioniAPI.list.mockResolvedValue({ data: [
      { relazione_id: 2, soggetto_id: 7, tipo: 'comodatario', tipo_nome: 'Comodatario', entity_type: 'IMMOBILE', entity_id: 3,
        descrizione: 'Via Roma 1, Milano', data_inizio: '2024-01-01', data_fine: null, corrente: true },
    ] });
    render(<MemoryRouter><ConduttoriList /></MemoryRouter>);
    expect(screen.getByRole('heading', { name: 'Godimento' })).toBeInTheDocument();
    expect(await screen.findByText('Comodatario')).toBeInTheDocument();
    expect(screen.queryByText('Quota')).not.toBeInTheDocument();
    expect(relazioniAPI.list).toHaveBeenCalledWith({ famiglia: 'godimento', entity_type: 'IMMOBILE', solo_correnti: true });
  });
});
