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

const BUTTON_VARIANTS = ['primary', 'brand', 'secondary', 'danger', 'ghost'];
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
