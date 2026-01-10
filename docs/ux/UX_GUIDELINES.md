# UX/UI Guidelines for Gestione Affitti
**Version:** 1.0
**Last Updated:** 2025-12-25

---

## Table of Contents
1. [Core Principles](#core-principles)
2. [Component Usage Guidelines](#component-usage-guidelines)
3. [Do's and Don'ts](#dos-and-donts)
4. [Common Patterns](#common-patterns)
5. [Accessibility Checklist](#accessibility-checklist)
6. [Mobile Best Practices](#mobile-best-practices)
7. [Performance Guidelines](#performance-guidelines)

---

## Core Principles

### 1. Minimize Friction
Every click, every confirmation, every extra step is friction. Design flows that allow users to accomplish tasks with minimal interactions.

**Good:**
- Inline editing for simple field changes
- One confirmation dialog for destructive actions
- Smart defaults that reduce decisions

**Bad:**
- Multiple confirmation dialogs
- Modal → Form → Confirmation → Modal loop
- Forcing users through wizards for simple tasks

### 2. Provide Clear Feedback
Users should always know what's happening. Use visual feedback for every action.

**Required feedback:**
- Loading states (spinners, skeleton screens)
- Success confirmations (toast notifications)
- Error messages (clear, actionable)
- Progress indicators (for multi-step operations)

### 3. Optimize for Common Tasks
Identify the 20% of actions users perform 80% of the time. Make these fast and easy.

**Examples:**
- Quick search with keyboard shortcut (Ctrl+F)
- Bulk operations for repetitive tasks
- Recently used items for quick access
- Keyboard shortcuts for power users

### 4. Mobile-First Thinking
Design for mobile, enhance for desktop. Not the reverse.

**Key considerations:**
- Touch targets minimum 44x44px
- Thumb-friendly button placement
- Avoid hover-only interactions
- Test on real devices

### 5. Progressive Disclosure
Don't overwhelm users. Show what's needed, hide what's not.

**Techniques:**
- Collapsible sections
- Tabs for grouped content
- "Show more" links
- Conditional fields (show only when relevant)

---

## Component Usage Guidelines

### DataTable Component

#### When to Use
- Displaying lists of entities (users, properties, contracts)
- Data that needs sorting, filtering, pagination
- Bulk operations on multiple items

#### Configuration Best Practices

```javascript
// GOOD: Clear, scannable table
const config = {
  columns: [
    { field: 'nome', label: 'Nome', sortable: true },
    { field: 'email', label: 'Email' },
    { field: 'telefono', label: 'Telefono' },
  ],
  rowActions: [
    { id: 'view', label: 'Dettagli', to: '/users/:id' },
    { id: 'edit', action: 'edit' },
    { id: 'delete', action: 'delete' },
  ],
};

// BAD: Too many columns, unreadable
const config = {
  columns: [
    { field: 'id', label: 'ID' }, // Not useful for users
    { field: 'nome', label: 'Nome' },
    { field: 'cognome', label: 'Cognome' },
    { field: 'email', label: 'Email' },
    { field: 'telefono', label: 'Telefono' },
    { field: 'cellulare', label: 'Cellulare' },
    { field: 'indirizzo', label: 'Indirizzo' }, // Too detailed
    { field: 'created_at', label: 'Creato il' }, // Rarely needed
    { field: 'updated_at', label: 'Aggiornato il' }, // Rarely needed
  ],
};
```

#### Search Configuration
```javascript
// GOOD: Descriptive placeholder
searchPlaceholder: 'Cerca per nome, email, codice fiscale...'

// BAD: Generic placeholder
searchPlaceholder: 'Cerca...'
```

#### Empty States
```javascript
// GOOD: Helpful, actionable
emptyTitle: 'Nessun affittuario trovato'
emptyMessage: 'Non ci sono affittuari registrati. Clicca su "Nuovo Affittuario" per iniziare.'

// BAD: Cryptic, unhelpful
emptyTitle: 'Nessun dato'
emptyMessage: 'La tabella e vuota.'
```

---

### FormBuilder Component

#### Form Structure
Organize forms into logical sections with clear progression.

```javascript
// GOOD: Grouped by topic, logical flow
const formConfig = {
  sections: [
    {
      title: 'Dati Personali',
      columns: 2,
      fields: [
        { name: 'nome', label: 'Nome', required: true },
        { name: 'cognome', label: 'Cognome', required: true },
        { name: 'codice_fiscale', label: 'Codice Fiscale', colSpan: 2 },
      ],
    },
    {
      title: 'Contatti',
      columns: 2,
      fields: [
        { name: 'email', type: 'email' },
        { name: 'telefono', type: 'tel' },
      ],
    },
  ],
};

// BAD: All fields in one section, no structure
const formConfig = {
  sections: [
    {
      fields: [
        { name: 'nome' },
        { name: 'cognome' },
        { name: 'email' },
        { name: 'telefono' },
        { name: 'indirizzo' },
        { name: 'note' },
      ],
    },
  ],
};
```

#### Field Labels and Placeholders

```javascript
// GOOD: Clear label, helpful placeholder
{
  name: 'codice_fiscale',
  label: 'Codice Fiscale',
  placeholder: 'RSSMRA80A01H501X',
  helpText: '16 caratteri alfanumerici',
}

// BAD: Vague label, no guidance
{
  name: 'cf',
  label: 'CF',
  placeholder: 'Inserisci...',
}
```

#### Validation

```javascript
// GOOD: Clear, actionable error messages
validation: {
  required: true,
  pattern: /^[A-Z]{6}\d{2}[A-Z]\d{2}[A-Z]\d{3}[A-Z]$/i,
  message: 'Codice fiscale non valido. Deve essere 16 caratteri (es: RSSMRA80A01H501X)',
}

// BAD: Generic, unhelpful
validation: {
  required: true,
  pattern: /^[A-Z]{6}\d{2}[A-Z]\d{2}[A-Z]\d{3}[A-Z]$/i,
  message: 'Campo non valido',
}
```

---

### FormModal Component

#### Size Selection

```javascript
// Use appropriate modal sizes:

// Small: Single field, simple confirmation
<FormModal size="small" title="Cambia Password">

// Medium: Standard forms (3-10 fields)
<FormModal size="medium" title="Modifica Affittuario">

// Large: Complex forms, multiple sections
<FormModal size="large" title="Nuovo Contratto">

// Fullscreen: Rich content, file uploads, embedded components
<FormModal size="fullscreen" title="Editor Documento">
```

#### User Experience

```javascript
// GOOD: Success feedback visible before close
const handleSuccess = () => {
  setShowSuccessMessage(true);
  setTimeout(() => onClose(), 1000); // User sees success
};

// BAD: Modal closes immediately
const handleSuccess = () => {
  onClose(); // Too fast, no feedback
};
```

---

### Toast Notifications

#### When to Use Toasts

**Do use toasts for:**
- Operation success confirmations
- Non-critical errors
- Background task updates
- Undo actions

**Don't use toasts for:**
- Critical errors (use modal)
- Information that requires action (use modal)
- Long messages (use modal or inline)

#### Toast Messages

```javascript
// GOOD: Clear, concise, specific
toast.success('Affittuario salvato con successo');
toast.error('Errore durante il salvataggio. Riprova tra qualche minuto.');

// BAD: Vague, technical
toast.success('Operazione completata');
toast.error('Errore 500');
```

#### Undo Actions

```javascript
// GOOD: Provide undo for reversible actions
toast.success('Elemento eliminato', {
  action: {
    label: 'Annulla',
    onClick: () => restoreItem(item),
  },
});

// Without undo, use confirmation dialog instead
```

---

## Do's and Don'ts

### Interactions

#### ✅ Do
- Use single confirmation for delete operations
- Provide undo for reversible actions
- Debounce search inputs (300ms)
- Show loading indicators immediately
- Use optimistic updates when possible
- Provide keyboard shortcuts for common actions

#### ❌ Don't
- Use `window.confirm()` or `window.alert()`
- Mix confirmation styles (dialog for single, alert for bulk)
- Trigger API calls on every keystroke
- Hide loading states (users think it's broken)
- Use modals for simple operations (edit one field)
- Force mouse interaction for everything

### Visual Design

#### ✅ Do
- Use consistent color palette
- Ensure WCAG AA contrast (4.5:1 minimum)
- Provide clear visual hierarchy (primary vs secondary actions)
- Use spacing consistently (multiples of 0.25rem)
- Test with color blindness simulator

#### ❌ Don't
- Use color as the only indicator (also use icons/text)
- Make all buttons look the same
- Use low-contrast text (gray on gray)
- Randomly space elements
- Forget focus indicators

### Forms

#### ✅ Do
- Group related fields
- Use appropriate input types (email, tel, date)
- Show validation errors after submit attempt
- Clear errors immediately when user fixes them
- Provide helpful placeholders
- Mark required fields clearly
- Auto-focus first field in modal forms

#### ❌ Don't
- Create single giant form section
- Use text inputs for everything
- Show errors before user finishes typing
- Keep errors visible after field is fixed
- Use placeholders as labels
- Mark everything as required
- Make users hunt for the first field

### Data Tables

#### ✅ Do
- Show most important columns first
- Use sortable columns for key fields
- Provide meaningful empty states
- Show row count and pagination info
- Enable keyboard navigation
- Make row actions obvious
- Use consistent action order (View, Edit, Delete)

#### ❌ Don't
- Show more than 7-8 columns
- Hide sort indicators
- Just say "No data"
- Hide pagination on large datasets
- Require mouse for everything
- Hide actions in dropdown menus
- Randomly order actions

---

## Common Patterns

### Pattern: Search and Filter

```javascript
// GOOD: Debounced search with loading indicator
const [searchInput, setSearchInput] = useState('');
const debouncedSearch = useDebounce(searchInput, 300);

useEffect(() => {
  fetchResults(debouncedSearch);
}, [debouncedSearch]);

// Show loading while debouncing
{searchInput !== debouncedSearch && <LoadingSpinner />}
```

### Pattern: Optimistic Updates

```javascript
// GOOD: Update UI immediately, rollback on error
const handleToggle = async (item) => {
  const previousState = item.active;

  // Optimistic update
  setItem({ ...item, active: !item.active });

  try {
    await api.update(item.id, { active: !item.active });
    toast.success('Stato aggiornato');
  } catch (err) {
    // Rollback on error
    setItem({ ...item, active: previousState });
    toast.error('Errore durante l\'aggiornamento');
  }
};
```

### Pattern: Bulk Operations

```javascript
// GOOD: Clear selection, bulk actions, progress
const [selectedIds, setSelectedIds] = useState(new Set());

const handleBulkDelete = async () => {
  setDeleting(true);
  let deleted = 0;

  for (const id of selectedIds) {
    try {
      await api.delete(id);
      deleted++;
    } catch (err) {
      console.error(`Failed to delete ${id}`);
    }
  }

  toast.success(`${deleted} elementi eliminati`);
  setSelectedIds(new Set());
  setDeleting(false);
  refresh();
};
```

### Pattern: Progressive Form Validation

```javascript
// GOOD: Validate after first submit attempt
const [hasSubmitted, setHasSubmitted] = useState(false);

const handleSubmit = async (values) => {
  setHasSubmitted(true);

  if (!isValid(values)) {
    return; // Show errors now
  }

  await saveData(values);
};

// Show errors only after submit attempt
const showError = (field) => {
  return hasSubmitted && errors[field];
};
```

### Pattern: Keyboard Shortcuts

```javascript
// GOOD: Non-intrusive shortcuts with visual hints
useKeyboardShortcut('ctrl+n', handleNew, { when: !modalOpen });
useKeyboardShortcut('ctrl+f', focusSearch);
useKeyboardShortcut('escape', closeModal, { when: modalOpen });

// Show hints in UI
<button title="Nuovo (Ctrl+N)">+ Nuovo</button>
```

---

## Accessibility Checklist

### Keyboard Navigation
- [ ] All interactive elements are keyboard accessible
- [ ] Tab order is logical and follows visual layout
- [ ] Focus indicators are clearly visible
- [ ] Escape key closes modals and dropdowns
- [ ] Enter key submits forms and activates buttons
- [ ] Arrow keys navigate within components (tables, lists)

### Screen Readers
- [ ] All images have alt text
- [ ] Form inputs have associated labels
- [ ] Buttons have descriptive text (not just icons)
- [ ] Error messages are announced (aria-live)
- [ ] Loading states are announced
- [ ] Table headers use `<th>` elements
- [ ] Modal dialogs have `role="dialog"` and `aria-modal="true"`

### Color and Contrast
- [ ] Text contrast meets WCAG AA (4.5:1)
- [ ] Large text contrast meets WCAG AA (3:1)
- [ ] Interactive elements have sufficient contrast
- [ ] Color is not the only way to convey information
- [ ] Links are distinguishable from regular text

### Touch and Motor
- [ ] Touch targets are minimum 44x44px
- [ ] Buttons have adequate spacing (prevent mis-taps)
- [ ] No hover-only interactions
- [ ] No time-limited interactions (or provide way to extend)
- [ ] Actions can be undone or confirmed

### Testing
- [ ] Test with keyboard only (unplug mouse)
- [ ] Test with screen reader (NVDA, JAWS, VoiceOver)
- [ ] Test with zoom at 200%
- [ ] Test with high contrast mode
- [ ] Test on mobile devices

---

## Mobile Best Practices

### Touch Targets

```css
/* GOOD: Touch-friendly sizes */
.button {
  min-width: 44px;
  min-height: 44px;
  padding: 0.75rem 1rem;
}

/* BAD: Too small for fingers */
.button {
  padding: 0.25rem 0.5rem;
}
```

### Layout

```css
/* GOOD: Responsive, mobile-first */
.container {
  padding: 1rem;
}

@media (min-width: 768px) {
  .container {
    padding: 2rem;
  }
}

/* BAD: Desktop-first, mobile as afterthought */
.container {
  padding: 3rem;
}

@media (max-width: 768px) {
  .container {
    padding: 0.5rem; /* Cramped */
  }
}
```

### Tables on Mobile

```javascript
// GOOD: Hide less important columns on mobile
const columns = [
  { field: 'nome', label: 'Nome', hideOn: [] }, // Always show
  { field: 'email', label: 'Email', hideOn: ['mobile'] },
  { field: 'telefono', label: 'Telefono', hideOn: [] },
  { field: 'created_at', label: 'Creato', hideOn: ['mobile', 'tablet'] },
];

// Or use card layout on mobile
@media (max-width: 640px) {
  .table {
    display: block;
  }

  .table-row {
    display: block;
    margin-bottom: 1rem;
    padding: 1rem;
    border: 1px solid #e5e7eb;
    border-radius: 0.5rem;
  }
}
```

### Forms on Mobile

```css
/* GOOD: Full-width inputs on mobile */
@media (max-width: 640px) {
  .form-grid {
    grid-template-columns: 1fr !important;
  }

  .form-field {
    grid-column: span 1 !important;
  }
}

/* GOOD: Larger text for readability */
@media (max-width: 640px) {
  input, select, textarea {
    font-size: 16px; /* Prevents iOS zoom on focus */
  }
}
```

---

## Performance Guidelines

### Search and Filtering

```javascript
// ALWAYS debounce user input
const debouncedValue = useDebounce(searchTerm, 300);

// NEVER trigger on every keystroke
onChange={(e) => fetchResults(e.target.value)} // BAD
```

### API Calls

```javascript
// GOOD: Cancel previous requests
const abortController = new AbortController();

useEffect(() => {
  const controller = new AbortController();

  fetchData({ signal: controller.signal });

  return () => controller.abort();
}, [searchTerm]);

// GOOD: Cache repeated requests
const cache = new Map();
const cachedFetch = (url) => {
  if (cache.has(url)) return cache.get(url);
  const promise = fetch(url);
  cache.set(url, promise);
  return promise;
};
```

### Rendering

```javascript
// GOOD: Memoize expensive computations
const filteredItems = useMemo(() => {
  return items.filter(item => item.name.includes(search));
}, [items, search]);

// GOOD: Use virtualization for long lists
import { FixedSizeList } from 'react-window';

<FixedSizeList
  height={600}
  itemCount={items.length}
  itemSize={50}
>
  {({ index, style }) => (
    <div style={style}>{items[index].name}</div>
  )}
</FixedSizeList>
```

### Perceived Performance

```javascript
// GOOD: Show skeleton screens during loading
{loading ? (
  <SkeletonTable rows={5} />
) : (
  <DataTable data={data} />
)}

// GOOD: Optimistic updates
const handleSave = async (data) => {
  // Update UI immediately
  updateCache(data);

  try {
    await api.save(data);
  } catch (err) {
    // Rollback on error
    revertCache();
    showError();
  }
};

// BAD: Just show spinner
{loading && <Spinner />}
```

---

## Quick Reference

### Color Palette

```css
/* Primary (Blue) */
--color-primary-50: #eff6ff;
--color-primary-500: #3b82f6;
--color-primary-600: #2563eb;

/* Success (Green) */
--color-success-500: #10b981;
--color-success-600: #059669;

/* Error (Red) */
--color-error-500: #ef4444;
--color-error-600: #dc2626;

/* Warning (Orange) */
--color-warning-500: #f59e0b;
--color-warning-600: #d97706;

/* Gray */
--color-gray-50: #f9fafb;
--color-gray-100: #f3f4f6;
--color-gray-200: #e5e7eb;
--color-gray-300: #d1d5db;
--color-gray-400: #9ca3af;
--color-gray-500: #6b7280;
--color-gray-600: #4b5563;
--color-gray-700: #374151;
--color-gray-800: #1f2937;
--color-gray-900: #111827;
```

### Spacing Scale

```css
/* Base unit: 0.25rem = 4px */
--space-1: 0.25rem;  /* 4px */
--space-2: 0.5rem;   /* 8px */
--space-3: 0.75rem;  /* 12px */
--space-4: 1rem;     /* 16px */
--space-5: 1.25rem;  /* 20px */
--space-6: 1.5rem;   /* 24px */
--space-8: 2rem;     /* 32px */
--space-10: 2.5rem;  /* 40px */
--space-12: 3rem;    /* 48px */
--space-16: 4rem;    /* 64px */
```

### Typography

```css
/* Font sizes */
--text-xs: 0.75rem;    /* 12px */
--text-sm: 0.875rem;   /* 14px */
--text-base: 1rem;     /* 16px */
--text-lg: 1.125rem;   /* 18px */
--text-xl: 1.25rem;    /* 20px */
--text-2xl: 1.5rem;    /* 24px */

/* Font weights */
--font-normal: 400;
--font-medium: 500;
--font-semibold: 600;
--font-bold: 700;
```

---

## Resources

- **WCAG Guidelines:** https://www.w3.org/WAI/WCAG21/quickref/
- **WebAIM Contrast Checker:** https://webaim.org/resources/contrastchecker/
- **iOS Human Interface Guidelines:** https://developer.apple.com/design/human-interface-guidelines/
- **Material Design:** https://material.io/design
- **Nielsen Norman Group:** https://www.nngroup.com/articles/
- **Laws of UX:** https://lawsofux.com/

---

## Version History

- **1.0** (2025-12-25): Initial version after core components review
