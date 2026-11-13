import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import PorzioniEditor from './PorzioniEditor';

const una = [{ porzione: 'AA', qualita: 'SEMINATIVO', classe: '2', superficie_mq: 100,
  reddito_dominicale: '', reddito_agrario: '', deduzioni: '' }];

describe('PorzioniEditor', () => {
  it('adds a row', () => {
    const onChange = vi.fn();
    render(<PorzioniEditor value={una} onChange={onChange} />);
    fireEvent.click(screen.getByRole('button', { name: /aggiungi porzione/i }));
    expect(onChange).toHaveBeenCalledTimes(1);
    expect(onChange.mock.calls[0][0]).toHaveLength(2);
  });

  it('does not remove the last row', () => {
    render(<PorzioniEditor value={una} onChange={vi.fn()} />);
    expect(screen.getByRole('button', { name: /togli porzione 1/i })).toBeDisabled();
  });

  it('removes a row when there are more', () => {
    const onChange = vi.fn();
    render(<PorzioniEditor value={[...una, { ...una[0], porzione: 'AB' }]} onChange={onChange} />);
    fireEvent.click(screen.getByRole('button', { name: /togli porzione 1/i }));
    expect(onChange.mock.calls[0][0].map((p) => p.porzione)).toEqual(['AB']);
  });

  it('passes the surface as a number', () => {
    const onChange = vi.fn();
    render(<PorzioniEditor value={una} onChange={onChange} />);
    fireEvent.change(screen.getByLabelText(/superficie m² porzione 1/i), { target: { value: '363' } });
    expect(onChange.mock.calls[0][0][0].superficie_mq).toBe(363);
  });

  it('shows the total surface in ha, are and centiare', () => {
    render(<PorzioniEditor value={[{ ...una[0], superficie_mq: 363 }, { ...una[0], superficie_mq: 63 }]} onChange={vi.fn()} />);
    expect(screen.getByText(/4 a 26 ca/)).toBeInTheDocument();
  });
});
