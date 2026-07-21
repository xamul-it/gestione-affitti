# Design System Frontend — Fondamenta + Pagina Vetrina

## Contesto

Il frontend (React + Vite) ha 91 file CSS indipendenti, uno per pagina/componente,
senza design token condivisi. Verifica quantitativa:

- 7 varianti diverse di "blu primario" in uso (`#007bff`, `#3498db`, `#0066cc`,
  `#1976d2`, `#2563eb`, `#667eea`, `#3b82f6`) per lo stesso ruolo semantico
- Icone miste: libreria `lucide-react` (via `iconRegistry.jsx`) + emoji dirette in
  20 file di componenti + chiavi manifest non mappate nel registro
  (`user-tie`, `building-columns`, `tag`, `puzzle`, più 4 emoji letterali)
- Nessun token CSS (custom properties), nessuna libreria di componenti UI condivisi
  (Button/Badge/Card reinventati per modulo)

Obiettivo: creare le fondamenta (token + componenti condivisi + fix icone) e una
pagina vetrina per validare le scelte visive, **prima** di toccare i moduli
esistenti. Il rollout sui moduli esistenti è esplicitamente fuori scope di
questo lavoro — verrà pianificato come fase separata dopo approvazione della
vetrina.

## Identità visiva (fonte: shop.ilz.it, sito Odoo + logo ILZ)

Estratta da CSS compilato Odoo (`--o-color-*`, `--primary`) e verificata
campionando i pixel del logo (`/web/image/website/1/logo/ILZ`):

- Rosso brand: `#DC110B` (CSS) / `#DC1914` (logo) — stesso colore, differenza da
  anti-aliasing
- Carboncino: `#4b4b4b` (CSS) / `#464646` (logo) — colore dominante del logotipo
- Nel logo il rosso è un **accento minoritario** (il pallino della "i"), non il
  colore di massa — il carboncino domina. Questo guida la scelta sotto.

## 1. Palette (token)

| Token | Valore | Uso |
|---|---|---|
| `--color-ink` | `#3D3D3D` (rifinito da `#464646` per contrasto testo) | Bottoni primari funzionali, testo enfatizzato, header |
| `--color-ink-hover` | `#262626` | Hover su ink |
| `--color-brand` | `#DC110B` | Stato attivo in nav, link, badge "novità", **una sola** CTA per pagina — mai su azioni generiche salva/conferma |
| `--color-brand-dark` | `#A5130F` | Hover su elementi brand |
| `--color-danger` | `#C2410C` (terracotta) | Elimina/errori — deliberatamente distinto dal rosso brand per non creare ambiguità |
| `--color-danger-dark` | `#9A3412` | Hover su danger |
| `--color-success` | `#28a745` | Conferme (invariato, già standard nel codebase) |
| `--color-warning` | `#ffc107` | Avvisi (invariato) |
| Scala neutri `--gray-100`…`--gray-900` | `#F8F9FA … #212529` | Testo, bordi, sfondi — stessa scala già presente nel CSS Odoo/Bootstrap, ripresa 1:1 |

Focus ring: sostituisce `#3498db` (incoerente, da "quick fix" precedente) con un
anello basato su `--color-brand` a opacità ridotta, contrasto verificato ≥ 3:1.

## 2. Tipografia

Font: **Plus Jakarta Sans** (Google Fonts, self-hosted via `@fontsource` o file
locali). Motivazione: il sito usa Poppins, font "da marketing" con x-height
basso e cifre non tabellari — inadatto a tabelle dense di importi/date che
l'app usa ovunque. Plus Jakarta Sans mantiene la stessa famiglia
geometrica/moderna (parentela visiva con Poppins) ma è disegnato per
interfacce: cifre tabellari, migliore leggibilità a 12-14px.

Fallback stack: `'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif`

Scala: h1 28px/h2 22px/h3 18px/h4 16px, body 15px, small 13px — pesi 400/500/600/700.

## 3. Spaziatura e forme

- Scala 4px: `4·8·12·16·24·32·48·64` (token `--space-1` … `--space-8`)
- Border radius bottoni/input/card: **8px** (`--radius-md`). Non il pill-shape
  10rem del sito sorgente: in un pannello dati denso con azioni affiancate il
  pill ovunque affollerebbe visivamente.
- Badge/pill di stato: pill-shape (`--radius-full`) — qui la convenzione
  pill è consolidata e riprende comunque lo spirito brand.
- Touch target minimo 44px (già presente in `index.css`, buona pratica
  esistente): **non si tocca**, resta come vincolo per bottoni/input.

## 4. Componenti condivisi

Nuovi, in `frontend/src/components/UI/` (cartella non ancora esistente):

- **`Button`**: props `variant` (`primary` | `brand` | `secondary` | `danger`
  | `ghost`), `size` (`sm` | `md` | `lg`), stati default/hover/disabled/loading
- **`Badge`**: props `variant` (`neutral` | `success` | `warning` | `danger` |
  `brand`), pill-shape — sostituisce gli N badge di stato duplicati nei moduli
  (`ScadenzaBadge`, `PoliceBadge`, `PlatformBadge`, ecc. — non toccati in
  questa fase, solo il nuovo primitivo viene creato)
- **`Card`**: contenitore standard (bg bianco, `--radius-md`, un solo token
  di ombra `--shadow-sm`)
- **`FormField`**: wrapper label + input/select/textarea + messaggio errore

Questi componenti sono nuovi e isolati: non sostituiscono nulla nei moduli
esistenti in questa fase (che continuano a usare i propri CSS). Vengono usati
solo nella pagina vetrina, a scopo di validazione.

## 5. Icone

Libreria unica: `lucide-react` (già in uso). Fix al registro
(`iconRegistry.jsx`):

| Chiave mancante/errata | Fix |
|---|---|
| `'user-tie'` | Aggiungere, mappata su icona `Contact2` |
| `'building-columns'` | Aggiungere, mappata su `Landmark` |
| `'tag'` | Aggiungere, mappata su `Tag` |
| `'puzzle'` | Aggiungere, mappata su `Puzzle` |
| `'👤'` in `anagrafica_italiana/manifest.js` | Sostituire con chiave esistente `'user'` |
| `'🏢'` in `anagrafica_italiana/manifest.js` | Sostituire con chiave esistente `'building'` |
| `'✉️'` in `gestione_pec/manifest.js` | Sostituire con chiave esistente `'envelope'` |
| `'⚙️'` in `gestione_pec/manifest.js` | Sostituire con chiave esistente `'cog'` |

Dimensioni standardizzate: 18px/stroke 1.7 inline, 20px nav, 24px header
(oggi non specificato esplicitamente, causa dimensioni incoerenti).

Le emoji usate come icone nei 20 file di componenti individuati **non vengono
toccate in questa fase** (fanno parte del rollout fase 2 sui moduli) — qui si
sistemano solo i manifest, che pilotano la navigazione/dashboard core.

## 6. Pagina vetrina

- File: `frontend/src/pages/Admin/StyleGuide.jsx` + CSS dedicato
- Rotta: `/admin/style-guide`, stesso pattern di accesso delle altre pagine
  `Admin/*Debug` esistenti (solo superuser, non in nav pubblica — link
  aggiunto solo nel menu Admin)
- Contenuto:
  - Swatch di tutti i colori-token con nome e hex
  - Scala tipografica (h1-h4, body, small)
  - Tutti i bottoni: variante × size × stato
  - Tutti i badge
  - Card di esempio
  - Form di esempio (con stato errore)
  - Tabella di esempio
  - Griglia di tutte le icone del registro (post-fix), nome sotto ciascuna

## Fuori scope (fase 2, futura, dopo approvazione vetrina)

- Migrazione dei ~90 CSS di pagine/moduli esistenti ai nuovi token
- Sostituzione dei badge/bottoni ad-hoc esistenti con i nuovi primitivi condivisi
- Rimozione delle emoji-icona nei 20 file componenti già individuati
- Fix del router `tasse` di `affitti_brevi` (disabilitato, tracciato separatamente)

## Test

- Nessuna logica di business: verifica visiva manuale della pagina vetrina
  nel browser (dev server) prima di considerare il lavoro completo
- Build frontend (`npm run build`) deve passare senza errori
