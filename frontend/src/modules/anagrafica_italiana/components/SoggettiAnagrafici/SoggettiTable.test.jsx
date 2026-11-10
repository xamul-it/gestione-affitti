import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';

const { get } = vi.hoisted(() => ({ get: vi.fn() }));
vi.mock('axios', () => {
  const client = { get, post: vi.fn(), put: vi.fn(), delete: vi.fn(), interceptors: { request: { use: vi.fn() }, response: { use: vi.fn() } } };
  return { default: { create: () => client, isCancel: () => false }, create: () => client, isCancel: () => false };
});

import SoggettiTable from './SoggettiTable';

const soggetti = [
  {
    id: 1, tipo_soggetto: 'PERSONA_FISICA', nome: 'Mario', cognome: 'Rossi', attivo: true,
    ruoli: [
      { codice: 'proprietario', nome: 'Proprietario', modulo: 'immobili', n: 1 },
      { codice: 'amministratore_condominio', nome: 'Amministratore condominio', modulo: 'immobili', n: 1 },
      { codice: 'conduttore', nome: 'Conduttore', modulo: 'immobili', n: 0 },
    ],
  },
];

function lastParams() {
  const calls = get.mock.calls.filter(([url]) => url === '/anagrafica/soggetti-v2/');
  return calls[calls.length - 1][1].params;
}

describe('SoggettiTable', () => {
  beforeEach(() => {
    get.mockReset();
    get.mockImplementation((url) => Promise.resolve({
      data: url === '/relazioni/tipi' ? [{ codice: 'proprietario', nome: 'Proprietario' }] : soggetti,
    }));
  });

  it('prefilters by role and shows role badges', async () => {
    render(<MemoryRouter><SoggettiTable title="Proprietari" ruolo="proprietario" /></MemoryRouter>);
    expect(await screen.findByText('Amministratore condominio')).toBeInTheDocument();
    expect(lastParams()).toMatchObject({ ruolo: 'proprietario' });
    expect(screen.getByText('Proprietario')).toBeInTheDocument();
    expect(screen.getByText('Conduttore')).toHaveClass('soggetti-ruolo--cessato');
    expect(screen.getByRole('link', { name: /Mario Rossi/ })).toHaveAttribute('href', '/anagrafiche/persone-fisiche/1');
  });

  it('renders extra columns', async () => {
    const extraColumns = [{ field: 'immobili', label: 'Immobili', render: () => 'Via Roma 1' }];
    render(<MemoryRouter><SoggettiTable ruolo="proprietario" extraColumns={extraColumns} /></MemoryRouter>);
    expect(await screen.findByText('Via Roma 1')).toBeInTheDocument();
    expect(screen.getByRole('columnheader', { name: /Immobili/ })).toBeInTheDocument();
  });

  it('includes ended relations when asked', async () => {
    render(<MemoryRouter><SoggettiTable ruolo="conduttore" /></MemoryRouter>);
    await screen.findByText('Mario Rossi');
    fireEvent.click(screen.getByLabelText('Anche cessati'));
    await waitFor(() => expect(lastParams()).toMatchObject({ ruolo: 'conduttore', ruolo_anche_cessati: true }));
  });

  it('offers a role filter on the full list', async () => {
    render(<MemoryRouter><SoggettiTable title="Anagrafiche" showFiltroRuolo /></MemoryRouter>);
    const select = await screen.findByLabelText('Ruolo');
    await screen.findByRole('option', { name: 'Proprietario' });
    fireEvent.change(select, { target: { value: 'proprietario' } });
    await waitFor(() => expect(lastParams()).toMatchObject({ ruolo: 'proprietario' }));
  });
});
