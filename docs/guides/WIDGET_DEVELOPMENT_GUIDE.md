# Widget Development Guide

## Guida Completa allo Sviluppo di Widget Modulari

Questa guida spiega come creare e registrare widget personalizzati per i moduli della piattaforma, rispettando l'architettura modulare e i principi di separazione.

---

## 📐 Architettura del Sistema Widget

### Principi Fondamentali

1. **Platform = Domain Agnostic**
   - La piattaforma NON conosce i moduli specifici
   - I widget sono caricati dinamicamente via registry
   - Nessun import statico di moduli nella piattaforma

2. **Module Self-Registration**
   - Ogni modulo dichiara i suoi widget
   - La registrazione avviene al caricamento del modulo
   - Lazy loading automatico dei componenti

3. **Dependency Direction**
   ```
   Modulo → Platform ✅ (corretto)
   Platform → Modulo ❌ (violazione)
   ```

### Componenti Chiave

```
frontend/src/
├── core/
│   └── widgets/                        # ⚙️ PLATFORM CORE
│       ├── WidgetComponentRegistry.js  # Registry dinamico
│       ├── LazyWidgetLoader.jsx        # Lazy loader
│       └── index.js                    # Exports
│
└── modules/
    └── {nome_modulo}/                  # 📦 BUSINESS MODULE
        ├── components/
        │   └── Dashboard/              # 📊 Widget components
        │       ├── MyWidget.jsx
        │       ├── MyWidget.css
        │       └── ...
        ├── index.js                    # ⚡ Registrazione widget
        └── manifest.js                 # 📋 Metadata modulo
```

---

## 🚀 Quick Start: Creare un Nuovo Widget

### Step 1: Creare il Widget Component

**File:** `frontend/src/modules/{modulo}/components/Dashboard/MyWidget.jsx`

```jsx
import React, { useState, useEffect } from 'react'
import { getMyData } from '../../services/myAPI'
import './MyWidget.css'

/**
 * MyWidget - Descrizione del widget
 *
 * Mostra [cosa fa il widget] e permette [interazioni possibili]
 */
function MyWidget() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    loadData()
  }, [])

  async function loadData() {
    try {
      setLoading(true)
      setError(null)

      const result = await getMyData()
      setData(result)
    } catch (err) {
      console.error('Error loading data:', err)
      setError('Errore nel caricamento dei dati')
    } finally {
      setLoading(false)
    }
  }

  // Loading state
  if (loading) {
    return (
      <div className="my-widget">
        <div className="widget-loading">Caricamento...</div>
      </div>
    )
  }

  // Error state
  if (error) {
    return (
      <div className="my-widget">
        <div className="widget-error">{error}</div>
      </div>
    )
  }

  // Success - render data
  return (
    <div className="my-widget">
      <div className="widget-header">
        <h3>📊 Titolo Widget</h3>
      </div>

      <div className="widget-content">
        {/* Il tuo contenuto qui */}
        <p>Dati: {JSON.stringify(data)}</p>
      </div>

      <div className="widget-footer">
        <button onClick={loadData}>
          <i className="fas fa-sync-alt"></i> Aggiorna
        </button>
      </div>
    </div>
  )
}

export default MyWidget
```

### Step 2: Creare gli Stili del Widget

**File:** `frontend/src/modules/{modulo}/components/Dashboard/MyWidget.css`

```css
.my-widget {
  background: white;
  border-radius: 8px;
  padding: 1rem;
  height: 100%;
  display: flex;
  flex-direction: column;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.my-widget .widget-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
  padding-bottom: 0.5rem;
  border-bottom: 1px solid #e0e0e0;
}

.my-widget .widget-header h3 {
  margin: 0;
  font-size: 1.1rem;
  font-weight: 600;
  color: #333;
}

.my-widget .widget-content {
  flex: 1;
  overflow-y: auto;
}

.my-widget .widget-footer {
  margin-top: 1rem;
  padding-top: 0.5rem;
  border-top: 1px solid #e0e0e0;
}

.my-widget .widget-loading {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 150px;
  color: #666;
}

.my-widget .widget-error {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 150px;
  color: #d32f2f;
  background: #ffebee;
  border-radius: 4px;
  padding: 1rem;
}
```

### Step 3: Registrare il Widget nel Modulo

**File:** `frontend/src/modules/{modulo}/index.js`

```javascript
import { widgetRegistry } from '../../core/widgets'

// ⚡ Registra widget nel registry della piattaforma
widgetRegistry.registerWidget(
  'MyWidget',                                        // Nome componente
  'nome_modulo',                                     // ID modulo
  () => import('./components/Dashboard/MyWidget')   // Lazy loader
)

// ... resto exports del modulo
export { default as MyWidget } from './components/Dashboard/MyWidget'
```

### Step 4: Dichiarare il Widget nel Backend

**File:** `backend/modules/{modulo}/__init__.py`

```python
# Widget da registrare con la platform
WIDGETS = [
    {
        "id": "nome_modulo.my_widget",              # ID univoco (modulo.nome)
        "title": "Il Mio Widget",                   # Titolo visualizzato
        "component": "MyWidget",                    # Nome componente (deve corrispondere)
        "description": "Descrizione del widget",    # Descrizione
        "default_width": 6,                         # Larghezza default (1-12)
        "default_height": 4,                        # Altezza default (1-12)
        "category": "stats",                        # Categoria (stats, charts, alerts, etc.)
        "module_id": "nome_modulo",                 # ID modulo
        "required_permission": "mia_entita.view"    # Permesso richiesto
    },
    # ... altri widget
]
```

### Step 5: Dichiarare il Widget nel Manifest Backend

**File:** `backend/modules/{modulo}/__manifest__.py`

```python
manifest = {
    "name": "Nome Modulo",
    "technical_name": "nome_modulo",
    # ... altre proprietà

    # Dashboard widgets
    "widgets": [
        {
            "id": "nome_modulo.my_widget",
            "title": "Il Mio Widget",
            "component": "MyWidget",
            "default_width": 6,
            "default_height": 4,
            "category": "stats",
            "required_permission": "mia_entita.view",
            "description": "Descrizione del widget",
        },
    ],
}
```

### Step 6: Registrare i Widget nel Database

Esegui lo script di registrazione:

```bash
cd backend
python register_widgets_manual.py
```

Oppure riavvia il backend per auto-registrazione durante startup.

---

## 📋 Convenzioni e Best Practices

### Naming Conventions

1. **Widget Component File:**
   - Nome: `{Entità}{Scopo}Widget.jsx`
   - Esempi: `ImmobiliStatsWidget.jsx`, `ContrattiScadenzaWidget.jsx`

2. **Widget Component Name:**
   - Stesso nome del file senza estensione
   - Esempio: `ImmobiliStatsWidget`

3. **Widget ID:**
   - Pattern: `{module_id}.{widget_name}`
   - Usa snake_case per widget_name
   - Esempi: `immobili.stats`, `affitti_lungo.contratti_scadenza`

4. **CSS Class:**
   - Nome: `{entità}-{scopo}-widget`
   - Esempi: `immobili-stats-widget`, `contratti-scadenza-widget`

### Struttura Widget Component

Ogni widget DEVE avere:

```jsx
function MyWidget() {
  // 1. State management
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  // 2. Data loading
  useEffect(() => {
    loadData()
  }, [])

  // 3. Loading state
  if (loading) return <LoadingState />

  // 4. Error state
  if (error) return <ErrorState error={error} />

  // 5. Success state - render data
  return <SuccessState data={data} />
}
```

### Dimensioni Widget

Grid system: 12 colonne × N righe

**Larghezza (width):**
- `3` = 25% (piccolo)
- `6` = 50% (medio)
- `12` = 100% (largo)

**Altezza (height):**
- `3` = piccolo
- `4` = medio
- `6` = alto

**Esempi:**
- **Stat card**: 3×3 (piccola card con numero)
- **Chart**: 6×4 (grafico medio)
- **Table**: 12×6 (tabella grande)

### Categorie Widget

Usa categorie coerenti:

- `stats` - Statistiche e numeri
- `charts` - Grafici e visualizzazioni
- `alerts` - Avvisi e notifiche
- `lists` - Liste e tabelle
- `actions` - Pulsanti e azioni rapide

---

## 🎨 Esempi Pratici

### Esempio 1: Widget Statistiche Semplice

```jsx
function StatsWidget() {
  const [stats, setStats] = useState({ count: 0, total: 0 })
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function load() {
      const data = await fetchStats()
      setStats(data)
      setLoading(false)
    }
    load()
  }, [])

  if (loading) return <div>Caricamento...</div>

  return (
    <div className="stats-widget">
      <div className="stat-card">
        <div className="stat-value">{stats.count}</div>
        <div className="stat-label">Totale</div>
      </div>
      <div className="stat-card">
        <div className="stat-value">€{stats.total}</div>
        <div className="stat-label">Valore</div>
      </div>
    </div>
  )
}
```

### Esempio 2: Widget Lista con Link

```jsx
function RecentItemsWidget() {
  const [items, setItems] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function load() {
      const data = await fetchRecentItems({ limit: 5 })
      setItems(data)
      setLoading(false)
    }
    load()
  }, [])

  if (loading) return <div>Caricamento...</div>

  return (
    <div className="recent-items-widget">
      <div className="widget-header">
        <h3>📋 Ultimi Elementi</h3>
        <Link to="/items">Vedi tutti</Link>
      </div>

      <ul className="items-list">
        {items.map(item => (
          <li key={item.id}>
            <Link to={`/items/${item.id}`}>
              <strong>{item.title}</strong>
              <small>{item.date}</small>
            </Link>
          </li>
        ))}
      </ul>
    </div>
  )
}
```

### Esempio 3: Widget Grafico

```jsx
import { LineChart, Line, XAxis, YAxis, Tooltip } from 'recharts'

function ChartWidget() {
  const [data, setData] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function load() {
      const chartData = await fetchChartData()
      setData(chartData)
      setLoading(false)
    }
    load()
  }, [])

  if (loading) return <div>Caricamento...</div>

  return (
    <div className="chart-widget">
      <div className="widget-header">
        <h3>📈 Andamento Mensile</h3>
      </div>

      <div className="chart-container">
        <LineChart width={500} height={300} data={data}>
          <XAxis dataKey="month" />
          <YAxis />
          <Tooltip />
          <Line type="monotone" dataKey="value" stroke="#8884d8" />
        </LineChart>
      </div>
    </div>
  )
}
```

---

## 🔧 Testing e Debugging

### Debug Widget Registry

In development mode, il registry è accessibile nella console:

```javascript
// Controlla widget registrati
window.__widgetRegistry.getRegisteredWidgets()
// Output: ['ImmobiliStatsWidget', 'StatsSoggettiWidget', ...]

// Verifica se widget è registrato
window.__widgetRegistry.hasWidget('MyWidget')

// Ottieni info su un widget
window.__widgetRegistry.getWidgetInfo('MyWidget')
// Output: { moduleId: 'nome_modulo', loaded: false }

// Statistiche
window.__widgetRegistry.getStats()
// Output: { registered: 5, loaded: 2, modules: Set(['immobili', ...]) }
```

### Console Logs

Il registry logga automaticamente:

```
[WidgetRegistry] ✅ Registered widget: MyWidget (module: nome_modulo)
[WidgetRegistry] Loading widget: MyWidget...
[WidgetRegistry] ✅ Loaded widget: MyWidget
```

### Errori Comuni

**1. "Widget component not registered"**
- **Causa:** Widget non registrato in `index.js`
- **Soluzione:** Aggiungi `widgetRegistry.registerWidget(...)`

**2. "Component export not found"**
- **Causa:** Export non corrisponde al nome
- **Soluzione:** Usa `export default` o esporta con nome corretto

**3. Widget non appare nella lista**
- **Causa:** ID widget non inizia con module_id
- **Soluzione:** Usa pattern `{module_id}.{widget_name}`

**4. Widget non si carica**
- **Causa:** Path import errato
- **Soluzione:** Verifica path in `() => import('./components/Dashboard/MyWidget')`

---

## 📦 Checklist Completa

Prima di considerare il widget completo:

### Frontend
- [ ] Creato componente widget in `components/Dashboard/`
- [ ] Creato file CSS per il widget
- [ ] Implementati stati: loading, error, success
- [ ] Registrato widget in `index.js` del modulo
- [ ] Esportato widget da `index.js`
- [ ] Testato caricamento lazy
- [ ] Verificato responsive design

### Backend
- [ ] Dichiarato widget in `__init__.py`
- [ ] Dichiarato widget in `__manifest__.py`
- [ ] ID widget segue pattern `{module_id}.{widget_name}`
- [ ] Nome componente corrisponde al frontend
- [ ] Permessi configurati correttamente
- [ ] Eseguito script di registrazione

### Testing
- [ ] Widget appare nella lista disponibili
- [ ] Widget si aggiunge alla dashboard
- [ ] Dati caricano correttamente
- [ ] Loading state funziona
- [ ] Error handling funziona
- [ ] Widget si rimuove correttamente
- [ ] Layout responsive su mobile
- [ ] Console senza errori

---

## 🔄 Workflow Sviluppo

```bash
# 1. Crea widget component
touch frontend/src/modules/{modulo}/components/Dashboard/MyWidget.jsx
touch frontend/src/modules/{modulo}/components/Dashboard/MyWidget.css

# 2. Implementa logica widget (vedi esempi sopra)

# 3. Registra in modulo
# Edita: frontend/src/modules/{modulo}/index.js

# 4. Dichiara nel backend
# Edita: backend/modules/{modulo}/__init__.py
# Edita: backend/modules/{modulo}/__manifest__.py

# 5. Registra nel database
cd backend
python register_widgets_manual.py

# 6. Test nel browser
# - Ricarica frontend (Ctrl+Shift+R)
# - Vai su /modules/{modulo}/dashboard
# - Clicca "+ Widget"
# - Verifica che appaia nella lista
# - Aggiungi e verifica funzionamento
```

---

## 📚 Riferimenti

### File da Consultare

**Frontend:**
- `frontend/src/core/widgets/WidgetComponentRegistry.js` - Registry implementation
- `frontend/src/core/widgets/LazyWidgetLoader.jsx` - Lazy loader
- `frontend/src/components/Platform/ModuleDashboard.jsx` - Dashboard container

**Backend:**
- `backend/app/core/platform_services/routes/dashboard.py` - Dashboard API
- `backend/register_widgets_manual.py` - Script registrazione manuale

**Esempi Esistenti:**
- `frontend/src/modules/immobili/components/Dashboard/ImmobiliStatsWidget.jsx`
- `frontend/src/modules/anagrafica_italiana/components/Dashboard/StatsSoggettiWidget.jsx`

### Documentazione Correlata

- `CLAUDE.md` - Architettura generale del progetto
- `BACKEND_DOMAIN_REFACTORING_COMPLETED.md` - Architettura modulare backend

---

## ❓ FAQ

**Q: Posso usare librerie esterne nel widget?**
A: Sì, installa con `npm install` e importa normalmente.

**Q: Come condividere codice tra widget dello stesso modulo?**
A: Crea componenti condivisi in `components/Dashboard/shared/`

**Q: Posso passare props ai widget?**
A: Sì, ma non è standard. Considera se il widget è veramente generico.

**Q: Come gestire aggiornamenti real-time?**
A: Usa WebSocket, polling con setInterval, o React Query.

**Q: Widget può usare servizi di altri moduli?**
A: Sì, se c'è dipendenza dichiarata. Importa direttamente l'API.

---

## 🎯 Prossimi Passi

Dopo aver creato il tuo widget:

1. Considera aggiungere **interazioni** (filtri, ordinamento)
2. Implementa **caching** per performance
3. Aggiungi **tests** (Jest + React Testing Library)
4. Documenta **casi d'uso** specifici
5. Raccogli **feedback utenti** per miglioramenti

---

**Versione:** 1.0
**Ultima modifica:** 2025-12-07
**Autore:** Team Gestione Affitti
