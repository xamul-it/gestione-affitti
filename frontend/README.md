# Gestione Affitti - Frontend

Applicazione React per la gestione di affitti immobiliari. Fa parte del progetto Gestione Affitti, un sistema modulare con backend FastAPI e frontend React.

## Tecnologie

- **React 18** - UI framework
- **Vite** - Build tool e dev server
- **React Router 6** - Routing
- **Axios** - HTTP client
- **Bootstrap 5** - Styling
- **React Bootstrap** - Componenti UI
- **FontAwesome** - Icone

## Prerequisiti

- Node.js 18+ (consigliato LTS)
- npm 9+
- Backend API in esecuzione (vedi `../backend/README.md`)

## Installazione

```bash
cd gestione-affitti/frontend

# Installa le dipendenze
npm install
```

## Configurazione

### File `.env`

Crea o modifica il file `.env` nella cartella `frontend/`:

```env
# URL base dell'API backend
# Usa l'IP del server se accedi da altri dispositivi sulla rete locale
VITE_API_BASE_URL=http://192.168.1.2:8000/api/v1

# Per sviluppo locale (stesso PC)
# VITE_API_BASE_URL=http://localhost:8000/api/v1
```

**Importante:** Quando accedi al frontend da un dispositivo remoto (es. tablet, altro PC), devi usare l'IP del server nel `VITE_API_BASE_URL`, non `localhost`.

### Configurazione Vite

Il file `vite.config.js` è già configurato per:
- Porta di sviluppo: **3000**
- Accesso da rete locale: abilitato (`host: true`)
- Proxy API: configurato per `/api/v1`

## Avvio

### Sviluppo

```bash
# Avvia il server di sviluppo con hot-reload
npm run dev
```

Il frontend sarà disponibile su:
- Locale: http://localhost:3000
- Rete: http://[IP-SERVER]:3000 (es. http://192.168.1.2:3000)

### Produzione

```bash
# Build per produzione
npm run build

# Preview della build
npm run preview
```

I file di build saranno nella cartella `dist/`.

## Struttura del Progetto

```
frontend/
├── src/
│   ├── modules/                 # Moduli business (self-contained)
│   │   ├── anagrafica_italiana/ # Anagrafica italiana
│   │   ├── immobili/            # Gestione immobili
│   │   └── affitti_lungo/       # Affitti a lungo termine
│   │
│   ├── components/              # Componenti condivisi
│   │   ├── Layout/              # Navigazione e layout
│   │   ├── Platform/            # Menu dinamico, sistema moduli
│   │   ├── Auth/                # Autenticazione
│   │   └── Search/              # Ricerca globale
│   │
│   ├── core/                    # Infrastruttura platform
│   │   └── modules/             # Sistema moduli dinamico
│   │
│   ├── contexts/                # React contexts
│   │   ├── AuthContext.jsx      # Autenticazione
│   │   └── TenantContext.jsx    # Multi-tenancy
│   │
│   ├── services/                # API services
│   │   └── api.js               # Client API centralizzato
│   │
│   ├── pages/                   # Pagine route-level
│   ├── App.jsx                  # Router configuration
│   └── main.jsx                 # Entry point
│
├── public/                      # Asset statici
├── .env                         # Configurazione ambiente
├── vite.config.js               # Configurazione Vite
└── package.json                 # Dipendenze npm
```

## Architettura Modulare

Il frontend segue un'architettura **modulare** che rispecchia il backend:

### Moduli Business

Ogni modulo in `src/modules/` è auto-contenuto:
- `components/` - Componenti React del modulo
- `services/` - API calls specifiche del modulo
- `manifest.js` - Metadata (routes, menu, permissions)
- `index.js` - Exports pubblici

### Auto-Discovery

I moduli sono scoperti automaticamente via `import.meta.glob`:
```javascript
const modules = import.meta.glob('/src/modules/*/manifest.js')
```

## Convenzioni di Codice

### Import

```javascript
// Preferire import da moduli
import { UnitaImmobiliariList } from './modules/immobili'
import { affittiAPI } from './modules/affitti_lungo'

// API centralizzata per backward compatibility
import { unitaImmobiliariAPI } from './services/api'
```

### API Calls

```javascript
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1'
```

## Multi-Tenancy

Il frontend supporta multi-tenancy:

1. **Login** - Utente si autentica
2. **Selezione Tenant** - Lista tenant disponibili
3. **Switch Tenant** - Nuovo token JWT con `tenant_schema`
4. **Operazioni** - Tutte le API usano il tenant selezionato

Gestito tramite `TenantContext.jsx`.

## Troubleshooting

### Errore CORS

**Problema:** `Cross-Origin Request Blocked`

**Soluzioni:**
1. Verifica che il backend sia in esecuzione su porta 8000
2. Controlla che `VITE_API_BASE_URL` punti all'IP corretto
3. Il backend accetta automaticamente richieste da `192.168.x.x`

### API non raggiungibile

**Problema:** Network Error nelle chiamate API

**Soluzioni:**
1. Controlla che il backend sia attivo: `curl http://localhost:8000/docs`
2. Se accedi da remoto, usa l'IP del server (non localhost)
3. Verifica firewall: porta 8000 deve essere aperta

### Hot-reload non funziona

**Soluzioni:**
1. Riavvia il server dev: `npm run dev`
2. Cancella cache: `rm -rf node_modules/.vite`
3. Reinstalla dipendenze: `rm -rf node_modules && npm install`

## Script NPM

| Comando | Descrizione |
|---------|-------------|
| `npm run dev` | Server sviluppo con hot-reload |
| `npm run build` | Build produzione |
| `npm run preview` | Preview build produzione |
| `npm run lint` | Esegui ESLint |

## Link Utili

- [Documentazione Progetto](../docs/)
- [Backend README](../backend/README.md)
- [Guida Widget Dashboard](../docs/guides/WIDGET_DEVELOPMENT_GUIDE.md)
