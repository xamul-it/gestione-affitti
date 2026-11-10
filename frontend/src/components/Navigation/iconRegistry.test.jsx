import { describe, it, expect } from 'vitest';
import { render } from '@testing-library/react';
import fs from 'node:fs';
import path from 'node:path';
import { renderIcon, ICONS } from './iconRegistry';

const ICON_NAME = /^[a-z][a-z0-9-]*$/;

/** Icon names declared by the frontend manifests and the backend module manifests. */
function declaredIconNames() {
  const names = new Set();
  const collect = (text) => {
    for (const m of text.matchAll(/["']?icon["']?\s*:\s*["']([^"']+)["']/g)) {
      if (ICON_NAME.test(m[1])) names.add(m[1]);
    }
  };
  const frontendModules = path.resolve(__dirname, '../../modules');
  for (const dir of fs.readdirSync(frontendModules)) {
    const file = path.join(frontendModules, dir, 'manifest.js');
    if (fs.existsSync(file)) collect(fs.readFileSync(file, 'utf8'));
  }
  const backendModules = path.resolve(__dirname, '../../../../backend/modules');
  if (fs.existsSync(backendModules)) {
    for (const dir of fs.readdirSync(backendModules)) {
      const file = path.join(backendModules, dir, '__manifest__.py');
      if (fs.existsSync(file)) collect(fs.readFileSync(file, 'utf8'));
    }
  }
  return [...names];
}

describe('iconRegistry', () => {
  it('resolves previously-missing manifest keys to real icons', () => {
    expect(ICONS['user-tie']).toBeDefined();
    expect(ICONS['building-columns']).toBeDefined();
    expect(ICONS['tag']).toBeDefined();
    expect(ICONS['puzzle']).toBeDefined();
    expect(ICONS['user-check']).toBeDefined();
    expect(ICONS['file-signature']).toBeDefined();
  });

  it('registers every icon declared by a module manifest', () => {
    const names = declaredIconNames();
    expect(names.length).toBeGreaterThan(10);
    expect(names.filter((n) => !ICONS[n])).toEqual([]);
  });

  it('renderIcon returns an svg (not the text fallback) for the new keys', () => {
    const { container } = render(<div>{renderIcon('user-tie')}</div>);
    expect(container.querySelector('svg')).not.toBeNull();
    expect(container.querySelector('.nav-emoji-icon')).toBeNull();
  });

  it('renders a generic icon, never the raw name, for an unknown icon name', () => {
    const { container } = render(<div>{renderIcon('totally-unknown-key')}</div>);
    expect(container.querySelector('svg')).not.toBeNull();
    expect(container.textContent).not.toContain('totally-unknown-key');
  });

  it('still shows an emoji passed as icon as text', () => {
    const { container } = render(<div>{renderIcon('📊')}</div>);
    expect(container.querySelector('.nav-emoji-icon')?.textContent).toBe('📊');
  });
});
