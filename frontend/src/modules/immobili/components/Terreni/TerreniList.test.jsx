import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import TerreniList from './TerreniList';
import { terreniAPI } from '../../services/immobiliAPI';
import { subscribeToToasts } from '../../../../core/hooks/useToast';

let config = null;
vi.mock('../../../../core/components', () => ({
  DataTable: (props) => { config = props.config; return <div>tabella</div>; },
}));
vi.mock('../../services/immobiliAPI', () => ({ terreniAPI: { update: vi.fn() } }));

const azione = (id) => config.rowActions.find((a) => a.id === id);

describe('TerreniList', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    render(<MemoryRouter><TerreniList /></MemoryRouter>);
  });

  it('disattiva e ripristina senza il colore delle azioni pericolose', async () => {
    const toggle = azione('toggle');
    expect(toggle.variant({ attivo: true })).toBe('secondary');
    terreniAPI.update.mockResolvedValue({ data: {} });
    const table = { refresh: vi.fn() };
    await toggle.onClick({ id: 4, attivo: true }, table);
    expect(terreniAPI.update).toHaveBeenCalledWith(4, { attivo: false });
    expect(table.refresh).toHaveBeenCalled();
    expect(azione('delete').variant).toBe('danger');
  });

  it("mostra un errore se l'aggiornamento fallisce", async () => {
    const messaggi = [];
    const stop = subscribeToToasts((toasts) => { messaggi.push(...[].concat(toasts)); });
    terreniAPI.update.mockRejectedValue({ response: { status: 500, data: { detail: 'guasto' } } });
    await azione('toggle').onClick({ id: 4, attivo: true }, { refresh: vi.fn() });
    if (typeof stop === 'function') stop();
    expect(messaggi.some((t) => t.type === 'error')).toBe(true);
  });
});
