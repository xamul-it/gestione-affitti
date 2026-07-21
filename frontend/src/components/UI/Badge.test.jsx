import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import Badge from './Badge';

describe('Badge', () => {
  it('renders children with the default neutral class', () => {
    render(<Badge>In attesa</Badge>);
    expect(screen.getByText('In attesa')).toHaveClass('ds-badge', 'ds-badge--neutral');
  });

  it('applies the requested variant class', () => {
    render(<Badge variant="danger">Scaduto</Badge>);
    expect(screen.getByText('Scaduto')).toHaveClass('ds-badge--danger');
  });
});
