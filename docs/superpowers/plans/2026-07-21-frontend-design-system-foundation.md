# Frontend Design System Foundation — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the shared foundation (CSS design tokens, font, fixed icon registry, four shared UI primitives) and a `/admin/style-guide` showcase page, so the visual language can be validated before any existing module is touched.

**Architecture:** A new `src/styles/tokens.css` defines CSS custom properties (color/spacing/radius/typography) imported once from `index.css`. Four new presentational components live in `src/components/UI/` (`Button`, `Badge`, `Card`, `FormField`), each with its own scoped CSS class prefixed `ds-` (design-system) so they never collide with the ~90 existing per-module stylesheets. A new `StyleGuide` page under `src/pages/Admin/` renders every token and component for visual review, reachable only via `/admin/style-guide` (superuser-only route, no nav link — same pattern as the existing `Admin/*Debug` pages).

**Tech Stack:** React 18, Vite 5, `lucide-react` (icons), Vitest + Testing Library (existing test setup), `@fontsource/plus-jakarta-sans` (new dependency, self-hosted font — no external CDN call).

## Global Constraints

- Spec: `docs/superpowers/specs/2026-07-21-frontend-design-system-design.md` — every requirement below traces back to it.
- No value above 32px (`--space-6`) in any new component CSS (hard ceiling from the spec).
- Touch target minimum stays 44px on `Button` (`min-height: 44px`) — only horizontal padding is tightened, never the minimum height.
- Icon library stays `lucide-react` exclusively; no new icon dependency.
- Do NOT touch any of the ~90 existing module/page CSS files, existing badge components (`ScadenzaBadge`, `PoliceBadge`, `PlatformBadge`, etc.), or the `affitti_brevi` `tasse` router — all explicitly out of scope per the spec.
- Every new component file gets a colocated `.test.jsx` using the existing Vitest + Testing Library setup (see `src/pages/Dashboard.test.jsx` for the project's conventions: `describe/it/expect` from `vitest`, `render/screen` from `@testing-library/react`).

---

### Task 1: Design tokens, font, and focus-ring fix

**Files:**
- Create: `frontend/src/styles/tokens.css`
- Modify: `frontend/src/index.css` (add `@import` at top; replace focus-ring color)
- Modify: `frontend/src/main.jsx` (add font imports)
- Modify: `frontend/package.json` (add `@fontsource/plus-jakarta-sans` dependency)

**Interfaces:**
- Produces (consumed by every later task): CSS custom properties `--color-ink`, `--color-ink-hover`, `--color-brand`, `--color-brand-dark`, `--color-danger`, `--color-danger-dark`, `--color-success`, `--color-warning`, `--color-focus-ring`, `--gray-100`…`--gray-900`, `--font-family-base`, `--font-size-h1`…`--font-size-h4`, `--font-size-body`, `--font-size-small`, `--space-1`…`--space-6`, `--radius-md`, `--radius-full`, `--shadow-sm`. These exact names are used verbatim in Tasks 2-6.

- [ ] **Step 1: Install the font package**

Run: `cd frontend && npm install @fontsource/plus-jakarta-sans`
Expected: `package.json` gains `"@fontsource/plus-jakarta-sans": "^5.3.0"` (or later patch) under `dependencies`.

- [ ] **Step 2: Create the token stylesheet**

Create `frontend/src/styles/tokens.css`:

```css
/*
 * Design tokens — single source of truth for color, spacing, radius and
 * typography across the platform. Values sourced from shop.ilz.it (Odoo
 * site CSS + logo pixel sampling) — see
 * docs/superpowers/specs/2026-07-21-frontend-design-system-design.md
 */
:root {
  /* Brand + functional colors */
  --color-ink: #3D3D3D;
  --color-ink-hover: #262626;
  --color-brand: #DC110B;
  --color-brand-dark: #A5130F;
  --color-danger: #C2410C;
  --color-danger-dark: #9A3412;
  --color-success: #28a745;
  --color-warning: #ffc107;
  --color-focus-ring: rgba(220, 17, 11, 0.35);

  /* Neutral scale (same values already used across the Bootstrap-derived CSS) */
  --gray-100: #F8F9FA;
  --gray-200: #E9ECEF;
  --gray-300: #DEE2E6;
  --gray-400: #CED4DA;
  --gray-500: #ADB5BD;
  --gray-600: #6C757D;
  --gray-700: #495057;
  --gray-800: #343A40;
  --gray-900: #212529;

  /* Typography */
  --font-family-base: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  --font-size-h1: 28px;
  --font-size-h2: 22px;
  --font-size-h3: 18px;
  --font-size-h4: 16px;
  --font-size-body: 15px;
  --font-size-small: 13px;

  /* Spacing — hard ceiling at --space-6 (32px), see spec section 3 */
  --space-1: 4px;
  --space-2: 8px;
  --space-3: 12px;
  --space-4: 16px;
  --space-5: 24px;
  --space-6: 32px;

  /* Shape */
  --radius-md: 8px;
  --radius-full: 9999px;
  --shadow-sm: 0 2px 4px rgba(0, 0, 0, 0.1);
}
```

- [ ] **Step 3: Import tokens and fix the focus ring in `index.css`**

Add as the very first line of `frontend/src/index.css`:

```css
@import './styles/tokens.css';
```

Then in the same file, replace the three existing focus-ring rules (currently hardcoded to `#3498db`):

Find:
```css
*:focus {
  outline: 3px solid #3498db;
  outline-offset: 2px;
}
```
Replace with:
```css
*:focus {
  outline: 3px solid var(--color-brand);
  outline-offset: 2px;
}
```

Find:
```css
*:focus-visible {
  outline: 3px solid #3498db;
  outline-offset: 2px;
}
```
Replace with:
```css
*:focus-visible {
  outline: 3px solid var(--color-brand);
  outline-offset: 2px;
}
```

Find:
```css
button:focus-visible, .btn:focus-visible {
  outline: 3px solid #3498db;
  outline-offset: 2px;
  box-shadow: 0 0 0 3px rgba(52, 152, 219, 0.2);
}
```
Replace with:
```css
button:focus-visible, .btn:focus-visible {
  outline: 3px solid var(--color-brand);
  outline-offset: 2px;
  box-shadow: 0 0 0 3px var(--color-focus-ring);
}
```

- [ ] **Step 4: Load the font in `main.jsx`**

In `frontend/src/main.jsx`, add these imports before `import './index.css'`:

```jsx
import '@fontsource/plus-jakarta-sans/400.css'
import '@fontsource/plus-jakarta-sans/500.css'
import '@fontsource/plus-jakarta-sans/600.css'
import '@fontsource/plus-jakarta-sans/700.css'
```

- [ ] **Step 5: Verify the app still builds and boots**

Run: `cd frontend && npm run build`
Expected: build succeeds with no errors (tokens.css and font imports resolve).

- [ ] **Step 6: Commit**

```bash
cd /home/htpc/test/gestione-affitti
git add frontend/package.json frontend/package-lock.json frontend/src/styles/tokens.css frontend/src/index.css frontend/src/main.jsx
git commit -m "feat(design-system): add CSS design tokens, self-hosted font, brand focus ring"
```

---

### Task 2: Icon registry fixes

**Files:**
- Modify: `frontend/src/components/Navigation/iconRegistry.jsx`
- Modify: `frontend/src/modules/anagrafica_italiana/manifest.js`
- Modify: `frontend/src/modules/gestione_pec/manifest.js`
- Test: `frontend/src/components/Navigation/iconRegistry.test.jsx` (new)

**Interfaces:**
- Consumes: nothing from Task 1.
- Produces: `ICONS` map in `iconRegistry.jsx` gains keys `'user-tie'`, `'building-columns'`, `'tag'`, `'puzzle'`. `renderIcon(iconName, options)` (unchanged signature) now resolves these keys instead of falling through to the emoji/text fallback. Consumed by `NavigationItem.jsx` and all 26 other existing call sites — no signature change, so no other file needs edits.

- [ ] **Step 1: Write the failing test**

Create `frontend/src/components/Navigation/iconRegistry.test.jsx`:

```jsx
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
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `cd frontend && npx vitest run src/components/Navigation/iconRegistry.test.jsx`
Expected: FAIL — `ICONS['user-tie']` is `undefined`.

- [ ] **Step 3: Add the missing icons to the registry**

In `frontend/src/components/Navigation/iconRegistry.jsx`, add to the `lucide-react` import block (alphabetical order, matching existing style):

Find:
```jsx
import {
  BadgeCheck,
  Bell,
  Briefcase,
  Building,
  Building2,
  Calendar,
```
Replace with:
```jsx
import {
  BadgeCheck,
  Bell,
  Briefcase,
  Building,
  Building2,
  Calendar,
  Contact2,
  Landmark,
  Puzzle,
  Tag,
```

(Note: `Contact2`, `Landmark`, `Puzzle`, `Tag` are inserted here for alphabetical grouping with the rest of the import block — actual placement inside the import list does not affect behavior, only readability.)

Find:
```jsx
  'money-bill-wave': CircleDollarSign,
  cog: Settings,
};
```
Replace with:
```jsx
  'money-bill-wave': CircleDollarSign,
  cog: Settings,
  'user-tie': Contact2,
  'building-columns': Landmark,
  tag: Tag,
  puzzle: Puzzle,
};
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `cd frontend && npx vitest run src/components/Navigation/iconRegistry.test.jsx`
Expected: PASS (all 3 tests).

- [ ] **Step 5: Fix the emoji-as-icon manifest entries**

In `frontend/src/modules/anagrafica_italiana/manifest.js`:

Find:
```js
      id: 'anagrafica.persone_fisiche',
      label: 'Persone Fisiche',
      path: '/anagrafiche/persone-fisiche',
      icon: '👤',
```
Replace with:
```js
      id: 'anagrafica.persone_fisiche',
      label: 'Persone Fisiche',
      path: '/anagrafiche/persone-fisiche',
      icon: 'user',
```

Find:
```js
      id: 'anagrafica.persone_giuridiche',
      label: 'Persone Giuridiche',
      path: '/anagrafiche/persone-giuridiche',
      icon: '🏢',
```
Replace with:
```js
      id: 'anagrafica.persone_giuridiche',
      label: 'Persone Giuridiche',
      path: '/anagrafiche/persone-giuridiche',
      icon: 'building',
```

In `frontend/src/modules/gestione_pec/manifest.js`:

Find:
```js
      id: 'pec.inbox',
      label: 'Caselle PEC',
      path: '/pec',
      icon: '✉️',
```
Replace with:
```js
      id: 'pec.inbox',
      label: 'Caselle PEC',
      path: '/pec',
      icon: 'envelope',
```

Find:
```js
      id: 'pec.admin',
      label: 'Configura PEC',
      path: '/pec/admin',
      icon: '⚙️',
```
Replace with:
```js
      id: 'pec.admin',
      label: 'Configura PEC',
      path: '/pec/admin',
      icon: 'cog',
```

- [ ] **Step 6: Commit**

```bash
cd /home/htpc/test/gestione-affitti
git add frontend/src/components/Navigation/iconRegistry.jsx frontend/src/components/Navigation/iconRegistry.test.jsx frontend/src/modules/anagrafica_italiana/manifest.js frontend/src/modules/gestione_pec/manifest.js
git commit -m "fix(icons): add missing manifest icon keys, replace raw emoji with registry keys"
```

---

### Task 3: `Button` component

**Files:**
- Create: `frontend/src/components/UI/Button.jsx`
- Create: `frontend/src/components/UI/Button.css`
- Test: `frontend/src/components/UI/Button.test.jsx`

**Interfaces:**
- Consumes: tokens from Task 1 (`--color-ink`, `--color-ink-hover`, `--color-brand`, `--color-brand-dark`, `--color-danger`, `--color-danger-dark`, `--gray-100`, `--gray-400`, `--space-1`…`--space-5`, `--radius-md`, `--font-family-base`, `--font-size-small`, `--font-size-body`, `--font-size-h4`).
- Produces: `export default function Button({ variant, size, disabled, loading, children, className, ...rest })`. `variant` ∈ `'primary' | 'brand' | 'secondary' | 'danger'` (default `'primary'`). `size` ∈ `'sm' | 'md' | 'lg'` (default `'md'`). Renders a native `<button>` with class `ds-btn ds-btn--{variant} ds-btn--{size}`. Consumed by Task 7 (StyleGuide page).

- [ ] **Step 1: Write the failing test**

Create `frontend/src/components/UI/Button.test.jsx`:

```jsx
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
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `cd frontend && npx vitest run src/components/UI/Button.test.jsx`
Expected: FAIL — cannot resolve `./Button` (file does not exist yet).

- [ ] **Step 3: Implement the component**

Create `frontend/src/components/UI/Button.css`:

```css
.ds-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-2);
  min-height: 44px;
  border: none;
  border-radius: var(--radius-md);
  font-family: var(--font-family-base);
  font-weight: 600;
  cursor: pointer;
  transition: background-color 0.15s ease;
}

.ds-btn:disabled {
  cursor: not-allowed;
  opacity: 0.6;
}

.ds-btn--sm {
  padding: var(--space-1) var(--space-3);
  font-size: var(--font-size-small);
}

.ds-btn--md {
  padding: var(--space-2) var(--space-4);
  font-size: var(--font-size-body);
}

.ds-btn--lg {
  padding: var(--space-3) var(--space-5);
  font-size: var(--font-size-h4);
}

.ds-btn--primary {
  background-color: var(--color-ink);
  color: #fff;
}
.ds-btn--primary:hover:not(:disabled) {
  background-color: var(--color-ink-hover);
}

.ds-btn--brand {
  background-color: var(--color-brand);
  color: #fff;
}
.ds-btn--brand:hover:not(:disabled) {
  background-color: var(--color-brand-dark);
}

.ds-btn--secondary {
  background-color: transparent;
  color: var(--color-ink);
  border: 1px solid var(--gray-400);
}
.ds-btn--secondary:hover:not(:disabled) {
  background-color: var(--gray-100);
}

.ds-btn--danger {
  background-color: var(--color-danger);
  color: #fff;
}
.ds-btn--danger:hover:not(:disabled) {
  background-color: var(--color-danger-dark);
}

.ds-btn__spinner {
  width: 14px;
  height: 14px;
  border: 2px solid rgba(255, 255, 255, 0.4);
  border-top-color: #fff;
  border-radius: 50%;
  animation: ds-btn-spin 0.6s linear infinite;
}

@keyframes ds-btn-spin {
  to {
    transform: rotate(360deg);
  }
}
```

Create `frontend/src/components/UI/Button.jsx`:

```jsx
import './Button.css';

export default function Button({
  variant = 'primary',
  size = 'md',
  disabled = false,
  loading = false,
  children,
  className = '',
  ...rest
}) {
  const classes = ['ds-btn', `ds-btn--${variant}`, `ds-btn--${size}`, className]
    .filter(Boolean)
    .join(' ');

  return (
    <button className={classes} disabled={disabled || loading} {...rest}>
      {loading ? <span className="ds-btn__spinner" aria-hidden="true" /> : null}
      {children}
    </button>
  );
}
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `cd frontend && npx vitest run src/components/UI/Button.test.jsx`
Expected: PASS (all 3 tests).

- [ ] **Step 5: Commit**

```bash
cd /home/htpc/test/gestione-affitti
git add frontend/src/components/UI/Button.jsx frontend/src/components/UI/Button.css frontend/src/components/UI/Button.test.jsx
git commit -m "feat(design-system): add shared Button component"
```

---

### Task 4: `Badge` component

**Files:**
- Create: `frontend/src/components/UI/Badge.jsx`
- Create: `frontend/src/components/UI/Badge.css`
- Test: `frontend/src/components/UI/Badge.test.jsx`

**Interfaces:**
- Consumes: tokens from Task 1 (`--gray-200`, `--gray-800`, `--color-danger-dark`, `--color-brand-dark`, `--space-1`, `--space-3`, `--radius-full`, `--font-family-base`, `--font-size-small`).
- Produces: `export default function Badge({ variant, children, className })`. `variant` ∈ `'neutral' | 'success' | 'warning' | 'danger' | 'brand'` (default `'neutral'`). Renders `<span class="ds-badge ds-badge--{variant}">`. Consumed by Task 7.

- [ ] **Step 1: Write the failing test**

Create `frontend/src/components/UI/Badge.test.jsx`:

```jsx
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
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `cd frontend && npx vitest run src/components/UI/Badge.test.jsx`
Expected: FAIL — cannot resolve `./Badge`.

- [ ] **Step 3: Implement the component**

Create `frontend/src/components/UI/Badge.css`:

```css
.ds-badge {
  display: inline-flex;
  align-items: center;
  gap: var(--space-1);
  padding: var(--space-1) var(--space-3);
  border-radius: var(--radius-full);
  font-family: var(--font-family-base);
  font-size: var(--font-size-small);
  font-weight: 600;
  line-height: 1.4;
}

.ds-badge--neutral {
  background-color: var(--gray-200);
  color: var(--gray-800);
}

.ds-badge--success {
  background-color: #d4edda;
  color: #155724;
}

.ds-badge--warning {
  background-color: #fff3cd;
  color: #856404;
}

.ds-badge--danger {
  background-color: #fde3d8;
  color: var(--color-danger-dark);
}

.ds-badge--brand {
  background-color: #fbdad8;
  color: var(--color-brand-dark);
}
```

Create `frontend/src/components/UI/Badge.jsx`:

```jsx
import './Badge.css';

export default function Badge({ variant = 'neutral', children, className = '' }) {
  const classes = ['ds-badge', `ds-badge--${variant}`, className].filter(Boolean).join(' ');
  return <span className={classes}>{children}</span>;
}
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `cd frontend && npx vitest run src/components/UI/Badge.test.jsx`
Expected: PASS (both tests).

- [ ] **Step 5: Commit**

```bash
cd /home/htpc/test/gestione-affitti
git add frontend/src/components/UI/Badge.jsx frontend/src/components/UI/Badge.css frontend/src/components/UI/Badge.test.jsx
git commit -m "feat(design-system): add shared Badge component"
```

---

### Task 5: `Card` component

**Files:**
- Create: `frontend/src/components/UI/Card.jsx`
- Create: `frontend/src/components/UI/Card.css`
- Test: `frontend/src/components/UI/Card.test.jsx`

**Interfaces:**
- Consumes: tokens from Task 1 (`--radius-md`, `--shadow-sm`, `--space-4`).
- Produces: `export default function Card({ children, className, ...rest })`. Renders `<div class="ds-card">`. Consumed by Task 7.

- [ ] **Step 1: Write the failing test**

Create `frontend/src/components/UI/Card.test.jsx`:

```jsx
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
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `cd frontend && npx vitest run src/components/UI/Card.test.jsx`
Expected: FAIL — cannot resolve `./Card`.

- [ ] **Step 3: Implement the component**

Create `frontend/src/components/UI/Card.css`:

```css
.ds-card {
  background-color: #fff;
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-sm);
  padding: var(--space-4);
}
```

Create `frontend/src/components/UI/Card.jsx`:

```jsx
import './Card.css';

export default function Card({ children, className = '', ...rest }) {
  const classes = ['ds-card', className].filter(Boolean).join(' ');
  return (
    <div className={classes} {...rest}>
      {children}
    </div>
  );
}
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `cd frontend && npx vitest run src/components/UI/Card.test.jsx`
Expected: PASS (both tests).

- [ ] **Step 5: Commit**

```bash
cd /home/htpc/test/gestione-affitti
git add frontend/src/components/UI/Card.jsx frontend/src/components/UI/Card.css frontend/src/components/UI/Card.test.jsx
git commit -m "feat(design-system): add shared Card component"
```

---

### Task 6: `FormField` component + `UI` barrel export

**Files:**
- Create: `frontend/src/components/UI/FormField.jsx`
- Create: `frontend/src/components/UI/FormField.css`
- Create: `frontend/src/components/UI/index.js`
- Test: `frontend/src/components/UI/FormField.test.jsx`

**Interfaces:**
- Consumes: tokens from Task 1 (`--space-1`, `--space-3`, `--font-family-base`, `--font-size-small`, `--color-ink`, `--color-danger-dark`); `Button`, `Badge`, `Card` from Tasks 3-5 (re-exported only).
- Produces: `export default function FormField({ label, htmlFor, error, children })`. Renders a `<label htmlFor={htmlFor}>` above `children`, and a `<p role="alert">{error}</p>` below when `error` is truthy. `frontend/src/components/UI/index.js` re-exports `Button`, `Badge`, `Card`, `FormField` — this is the single import path Task 7 uses (`import { Button, Badge, Card, FormField } from '../../components/UI'`).

- [ ] **Step 1: Write the failing test**

Create `frontend/src/components/UI/FormField.test.jsx`:

```jsx
import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import FormField from './FormField';

describe('FormField', () => {
  it('wires the label to its input via htmlFor/id', () => {
    render(
      <FormField label="Email" htmlFor="email">
        <input id="email" />
      </FormField>
    );
    expect(screen.getByLabelText('Email')).toBeInTheDocument();
  });

  it('renders an error message with role alert when provided', () => {
    render(
      <FormField label="Email" htmlFor="email" error="Campo obbligatorio">
        <input id="email" />
      </FormField>
    );
    expect(screen.getByRole('alert')).toHaveTextContent('Campo obbligatorio');
  });

  it('renders no alert when there is no error', () => {
    render(
      <FormField label="Email" htmlFor="email">
        <input id="email" />
      </FormField>
    );
    expect(screen.queryByRole('alert')).toBeNull();
  });
});
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `cd frontend && npx vitest run src/components/UI/FormField.test.jsx`
Expected: FAIL — cannot resolve `./FormField`.

- [ ] **Step 3: Implement the component**

Create `frontend/src/components/UI/FormField.css`:

```css
.ds-field {
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
  margin-bottom: var(--space-3);
}

.ds-field__label {
  font-family: var(--font-family-base);
  font-size: var(--font-size-small);
  font-weight: 600;
  color: var(--color-ink);
}

.ds-field__error {
  font-size: var(--font-size-small);
  color: var(--color-danger-dark);
  margin: 0;
}
```

Create `frontend/src/components/UI/FormField.jsx`:

```jsx
import './FormField.css';

export default function FormField({ label, htmlFor, error, children }) {
  return (
    <div className="ds-field">
      {label ? (
        <label className="ds-field__label" htmlFor={htmlFor}>
          {label}
        </label>
      ) : null}
      {children}
      {error ? (
        <p className="ds-field__error" role="alert">
          {error}
        </p>
      ) : null}
    </div>
  );
}
```

Create `frontend/src/components/UI/index.js`:

```js
export { default as Button } from './Button';
export { default as Badge } from './Badge';
export { default as Card } from './Card';
export { default as FormField } from './FormField';
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `cd frontend && npx vitest run src/components/UI/FormField.test.jsx`
Expected: PASS (all 3 tests).

- [ ] **Step 5: Commit**

```bash
cd /home/htpc/test/gestione-affitti
git add frontend/src/components/UI/FormField.jsx frontend/src/components/UI/FormField.css frontend/src/components/UI/index.js frontend/src/components/UI/FormField.test.jsx
git commit -m "feat(design-system): add shared FormField component and UI barrel export"
```

---

### Task 7: Style Guide showcase page

**Files:**
- Create: `frontend/src/pages/Admin/StyleGuide.jsx`
- Create: `frontend/src/pages/Admin/StyleGuide.css`
- Modify: `frontend/src/App.jsx` (add import + route)

**Interfaces:**
- Consumes: `Button, Badge, Card, FormField` from `../../components/UI` (Task 6); `ICONS` from `../../components/Navigation/iconRegistry` (Task 2); all tokens from Task 1.
- Produces: route `/admin/style-guide`, gated by `<ProtectedRoute requiredRole="Admin">` — same pattern as the existing `/admin/roles-debug` route at `App.jsx:183`.

- [ ] **Step 1: Create the page component**

Create `frontend/src/pages/Admin/StyleGuide.jsx`:

```jsx
import { renderIcon, ICONS } from '../../components/Navigation/iconRegistry';
import { Button, Badge, Card, FormField } from '../../components/UI';
import './StyleGuide.css';

const COLOR_SWATCHES = [
  { name: '--color-ink', value: '#3D3D3D' },
  { name: '--color-ink-hover', value: '#262626' },
  { name: '--color-brand', value: '#DC110B' },
  { name: '--color-brand-dark', value: '#A5130F' },
  { name: '--color-danger', value: '#C2410C' },
  { name: '--color-danger-dark', value: '#9A3412' },
  { name: '--color-success', value: '#28a745' },
  { name: '--color-warning', value: '#ffc107' },
  { name: '--gray-100', value: '#F8F9FA' },
  { name: '--gray-300', value: '#DEE2E6' },
  { name: '--gray-500', value: '#ADB5BD' },
  { name: '--gray-700', value: '#495057' },
  { name: '--gray-900', value: '#212529' },
];

const SPACING_STEPS = [
  { name: '--space-1', value: 4 },
  { name: '--space-2', value: 8 },
  { name: '--space-3', value: 12 },
  { name: '--space-4', value: 16 },
  { name: '--space-5', value: 24 },
  { name: '--space-6', value: 32 },
];

const BUTTON_VARIANTS = ['primary', 'brand', 'secondary', 'danger'];
const BUTTON_SIZES = ['sm', 'md', 'lg'];
const BADGE_VARIANTS = ['neutral', 'success', 'warning', 'danger', 'brand'];

export default function StyleGuide() {
  return (
    <div className="style-guide">
      <h1>Style Guide</h1>
      <p className="style-guide__intro">
        Fondamenta del design system: token, componenti condivisi e icone.
        Vedi <code>docs/superpowers/specs/2026-07-21-frontend-design-system-design.md</code>.
      </p>

      <section>
        <h2>Colori</h2>
        <div className="style-guide__swatches">
          {COLOR_SWATCHES.map((c) => (
            <div key={c.name} className="style-guide__swatch">
              <span className="style-guide__swatch-color" style={{ backgroundColor: c.value }} />
              <span className="style-guide__swatch-name">{c.name}</span>
              <span className="style-guide__swatch-hex">{c.value}</span>
            </div>
          ))}
        </div>
      </section>

      <section>
        <h2>Tipografia</h2>
        <h1 style={{ fontSize: 'var(--font-size-h1)' }}>Titolo H1</h1>
        <h2 style={{ fontSize: 'var(--font-size-h2)' }}>Titolo H2</h2>
        <h3 style={{ fontSize: 'var(--font-size-h3)' }}>Titolo H3</h3>
        <h4 style={{ fontSize: 'var(--font-size-h4)' }}>Titolo H4</h4>
        <p style={{ fontSize: 'var(--font-size-body)' }}>Testo body — 15px.</p>
        <p style={{ fontSize: 'var(--font-size-small)' }}>Testo small — 13px.</p>
      </section>

      <section>
        <h2>Spaziatura</h2>
        <div className="style-guide__spacing">
          {SPACING_STEPS.map((s) => (
            <div key={s.name} className="style-guide__spacing-row">
              <span className="style-guide__spacing-name">
                {s.name} ({s.value}px)
              </span>
              <span
                className="style-guide__spacing-block"
                style={{ width: `${s.value}px`, height: `${s.value}px` }}
              />
            </div>
          ))}
        </div>
      </section>

      <section>
        <h2>Bottoni</h2>
        {BUTTON_VARIANTS.map((variant) => (
          <div key={variant} className="style-guide__row">
            {BUTTON_SIZES.map((size) => (
              <Button key={size} variant={variant} size={size}>
                {variant} {size}
              </Button>
            ))}
            <Button variant={variant} disabled>
              disabled
            </Button>
            <Button variant={variant} loading>
              loading
            </Button>
          </div>
        ))}
      </section>

      <section>
        <h2>Badge</h2>
        <div className="style-guide__row">
          {BADGE_VARIANTS.map((variant) => (
            <Badge key={variant} variant={variant}>
              {variant}
            </Badge>
          ))}
        </div>
      </section>

      <section>
        <h2>Card</h2>
        <Card>Contenuto di esempio dentro una Card.</Card>
      </section>

      <section>
        <h2>Form</h2>
        <Card>
          <FormField label="Nome" htmlFor="sg-nome">
            <input id="sg-nome" placeholder="Mario Rossi" />
          </FormField>
          <FormField label="Email" htmlFor="sg-email" error="Campo obbligatorio">
            <input id="sg-email" placeholder="mario@esempio.it" />
          </FormField>
        </Card>
      </section>

      <section>
        <h2>Tabella</h2>
        <table>
          <thead>
            <tr>
              <th>Nome</th>
              <th>Stato</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td>Esempio 1</td>
              <td>
                <Badge variant="success">attivo</Badge>
              </td>
            </tr>
            <tr>
              <td>Esempio 2</td>
              <td>
                <Badge variant="danger">scaduto</Badge>
              </td>
            </tr>
          </tbody>
        </table>
      </section>

      <section>
        <h2>Icone ({Object.keys(ICONS).length})</h2>
        <div className="style-guide__icons">
          {Object.keys(ICONS).sort().map((key) => (
            <div key={key} className="style-guide__icon">
              {renderIcon(key, { size: 20 })}
              <span>{key}</span>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
```

- [ ] **Step 2: Create the page stylesheet**

Create `frontend/src/pages/Admin/StyleGuide.css`:

```css
.style-guide {
  padding: var(--space-5);
  font-family: var(--font-family-base);
  max-width: 960px;
}

.style-guide__intro {
  color: var(--gray-700);
  margin-bottom: var(--space-5);
}

.style-guide section {
  margin-bottom: var(--space-6);
}

.style-guide__swatches {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
  gap: var(--space-3);
}

.style-guide__swatch {
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
}

.style-guide__swatch-color {
  display: block;
  width: 100%;
  height: 48px;
  border-radius: var(--radius-md);
  border: 1px solid var(--gray-300);
}

.style-guide__swatch-name {
  font-size: var(--font-size-small);
  font-weight: 600;
}

.style-guide__swatch-hex {
  font-size: var(--font-size-small);
  color: var(--gray-600);
}

.style-guide__spacing-row {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  margin-bottom: var(--space-2);
}

.style-guide__spacing-name {
  width: 160px;
  font-size: var(--font-size-small);
}

.style-guide__spacing-block {
  display: block;
  background-color: var(--color-brand);
  border-radius: 2px;
}

.style-guide__row {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--space-3);
  margin-bottom: var(--space-3);
}

.style-guide__icons {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
  gap: var(--space-3);
}

.style-guide__icon {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-1);
  padding: var(--space-2);
  border-radius: var(--radius-md);
  border: 1px solid var(--gray-200);
  font-size: var(--font-size-small);
  text-align: center;
}
```

- [ ] **Step 3: Wire the route in `App.jsx`**

In `frontend/src/App.jsx`, find the Admin page imports block:

```jsx
import CoreCleanup from './pages/Admin/CoreCleanup';
```

Add immediately after it:

```jsx
import StyleGuide from './pages/Admin/StyleGuide';
```

Then find the existing debug route:

```jsx
                <Route path="/admin/core-cleanup" element={<ProtectedRoute requiredRole="Admin"><CoreCleanup /></ProtectedRoute>} />
```

Add immediately after it:

```jsx
                <Route path="/admin/style-guide" element={<ProtectedRoute requiredRole="Admin"><StyleGuide /></ProtectedRoute>} />
```

- [ ] **Step 4: Manual visual verification**

Run: `cd frontend && npm run dev` (if not already running), then open `http://localhost:3000/admin/style-guide` in a browser logged in as an Admin user.
Expected: page renders all sections without console errors; colors/spacing/buttons/badges/icons visible and legible.

- [ ] **Step 5: Commit**

```bash
cd /home/htpc/test/gestione-affitti
git add frontend/src/pages/Admin/StyleGuide.jsx frontend/src/pages/Admin/StyleGuide.css frontend/src/App.jsx
git commit -m "feat(design-system): add /admin/style-guide showcase page"
```

---

### Task 8: Full verification pass

**Files:** none created/modified — verification only.

**Interfaces:** none.

- [ ] **Step 1: Run the full frontend test suite**

Run: `cd frontend && npm run test:run`
Expected: all tests pass, including the 11 new tests added in Tasks 2-6 (3 icon registry + 3 Button + 2 Badge + 2 Card + 3 FormField).

- [ ] **Step 2: Run the production build**

Run: `cd frontend && npm run build`
Expected: build succeeds with no errors or new warnings related to `tokens.css`, the font package, or the new `UI` components.

- [ ] **Step 3: Manual smoke test of the running app**

With `npm run dev` running, open `http://localhost:3000`, log in, and check:
- No visual regression on existing pages (focus ring is now red instead of blue — expected change, not a bug)
- `/admin/style-guide` loads and matches what was reviewed in Task 7 Step 4
- The `anagrafica_italiana` and `gestione_pec` nav menu items that previously showed emoji now show proper vector icons

- [ ] **Step 4: Report completion**

Summarize to the user: what was built, the two verification commands that passed, and the URL to review (`/admin/style-guide`). Remind them that the ~90-file rollout across existing modules is a separate follow-up, to be planned once they approve what they see on the style guide page.
