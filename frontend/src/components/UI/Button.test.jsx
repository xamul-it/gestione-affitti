import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import Button from './Button';

describe('Button', () => {
  it('renders children with default primary/md classes', () => {
    render(<Button>Salva</Button>);
    const btn = screen.getByRole('button', { name: 'Salva' });
    expect(btn).toHaveClass('ds-btn', 'ds-btn--primary', 'ds-btn--md');
  });

  it('applies the requested variant and size classes', () => {
    render(<Button variant="danger" size="lg">Elimina</Button>);
    const btn = screen.getByRole('button', { name: 'Elimina' });
    expect(btn).toHaveClass('ds-btn--danger', 'ds-btn--lg');
  });

  it('disables the button while loading and does not fire onClick', async () => {
    const onClick = vi.fn();
    render(<Button loading onClick={onClick}>Salva</Button>);
    const btn = screen.getByRole('button');
    expect(btn).toBeDisabled();
    await userEvent.click(btn);
    expect(onClick).not.toHaveBeenCalled();
  });
});
