import { describe, it, expect } from 'vitest';
import { render } from '@testing-library/react';
import { renderIcon, ICONS } from './iconRegistry';

describe('iconRegistry', () => {
  it('resolves previously-missing manifest keys to real icons', () => {
    expect(ICONS['user-tie']).toBeDefined();
    expect(ICONS['building-columns']).toBeDefined();
    expect(ICONS['tag']).toBeDefined();
    expect(ICONS['puzzle']).toBeDefined();
  });

  it('renderIcon returns an svg (not the text fallback) for the new keys', () => {
    const { container } = render(<div>{renderIcon('user-tie')}</div>);
    expect(container.querySelector('svg')).not.toBeNull();
    expect(container.querySelector('.nav-emoji-icon')).toBeNull();
  });

  it('still falls back to raw text for a genuinely unknown key', () => {
    const { container } = render(<div>{renderIcon('totally-unknown-key')}</div>);
    expect(container.querySelector('.nav-emoji-icon')).not.toBeNull();
  });
});
