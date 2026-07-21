import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import Card from './Card';

describe('Card', () => {
  it('renders children inside a ds-card container', () => {
    render(<Card>Contenuto</Card>);
    expect(screen.getByText('Contenuto')).toHaveClass('ds-card');
  });

  it('merges an extra className with the base class', () => {
    render(<Card className="extra">X</Card>);
    expect(screen.getByText('X')).toHaveClass('ds-card', 'extra');
  });
});
