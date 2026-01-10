# Gestione Affitti - Backend

API backend FastAPI per la gestione di affitti immobiliari. Fa parte del progetto Gestione Affitti, un sistema modulare con backend FastAPI e frontend React.

## Tecnologie

- **FastAPI** - Web framework asincrono
- **SQLAlchemy** - ORM
- **PostgreSQL** - Database
- **Alembic** - Migrazioni database
- **Pydantic** - Validazione dati
- **JWT** - Autenticazione

## Prerequisiti

- Python 3.10+
- PostgreSQL 14+
- pip (gestore pacchetti Python)

## Installazione

```bash
cd gestione-affitti/backend

# Crea ambiente virtuale
python -m venv venv

# Attiva ambiente virtuale
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# Installa dipendenze
pip install -r requirements.txt
```

## Configurazione

### File `.env`

Crea il file `.env` nella cartella `backend/`:

```env
# Database PostgreSQL
DATABASE_URL=postgresql://user:password@localhost:5432/gestione_affitti

# Chiave segreta per JWT (genera una stringa random)
SECRET_KEY=your-super-secret-key-change-in-production

# CORS - origini permesse (opzionale, auto-detect per rete locale)
BACKEND_CORS_ORIGINS=http://localhost:3000,http://192.168.1.2:3000
```

### Database

Crea il database PostgreSQL:

```sql
CREATE DATABASE gestione_affitti;
```

Le tabelle vengono create automaticamente all'avvio.

## Avvio

### Sviluppo

```bash
# Attiva ambiente virtuale (se non già attivo)
source venv/bin/activate

# Avvia con auto-reload
python app/main.py

# Oppure con uvicorn direttamente
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Script di Avvio

```bash
chmod +x start.sh
./start.sh
```

### Produzione

```bash
gunicorn -w 4 -k uvicorn.workers.UvicornWorker app.main:app --bind 0.0.0.0:8000
```

## Endpoint

Il backend espone:

- **API:** http://localhost:8000/api/v1/
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

## Struttura del Progetto

```
backend/
├── app/
│   ├── core/                    # Platform core (domain-agnostic)
│   │   ├── config.py           # Settings
│   │   ├── database.py         # SQLAlchemy setup
│   │   ├── auth/               # Autenticazione
│   │   ├── module_system/      # Loader moduli dinamico
│   │   └── platform_services/  # Menu, dashboard, widgets
│   │
│   └── main.py                 # Entry point
│
├── modules/                     # Moduli business (pluggable)
│   ├── anagrafica_italiana/    # Anagrafica persone/aziende
│   ├── immobili/               # Gestione immobili
│   └── affitti_lungo/          # Contratti e affitti
│
├── alembic/                    # Migrazioni database
├── storage/                    # File uploads
├── requirements.txt            # Dipendenze Python
└── .env                        # Configurazione ambiente
```

## Architettura Modulare

Il backend è una **piattaforma domain-agnostic** con moduli business pluggable.

### Core

Il core (`app/core/`) contiene solo servizi platform:
- Autenticazione e autorizzazione
- Sistema di caricamento moduli
- Servizi piattaforma (menu, dashboard)
- Setup database

### Moduli

Ogni modulo in `modules/` è auto-contenuto:

```
modules/nome_modulo/
├── __manifest__.py    # Metadata e dipendenze
├── __init__.py        # Registration
├── models/            # SQLAlchemy models
├── schemas/           # Pydantic schemas
├── routes/            # FastAPI routers
└── services/          # Business logic
```

## Migrazioni Database

```bash
# Stato attuale
alembic current

# Nuova migrazione
alembic revision --autogenerate -m "descrizione"

# Applica migrazioni
alembic upgrade head

# Rollback
alembic downgrade -1
```

## Multi-Tenancy

Il backend supporta multi-tenancy basato su schema PostgreSQL:

```bash
# Login
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -d '{"username":"admin","password":"changeme123"}'

# Switch tenant
curl -X POST "http://localhost:8000/api/v1/tenants/switch" \
  -H "Authorization: Bearer <token>" \
  -d '{"tenant_id": 1}'
```

## API Conventions

| Metodo | Endpoint | Descrizione |
|--------|----------|-------------|
| GET | `/api/v1/entity/` | Lista (con paginazione) |
| GET | `/api/v1/entity/{id}` | Dettaglio singolo |
| POST | `/api/v1/entity/` | Crea nuovo |
| PUT | `/api/v1/entity/{id}` | Aggiorna |
| DELETE | `/api/v1/entity/{id}` | Elimina |

## Troubleshooting

### Database connection refused

```bash
# Verifica PostgreSQL
sudo systemctl status postgresql

# Test connessione
psql -h localhost -U user -d gestione_affitti
```

### Port already in use

```bash
# Trova processo sulla porta 8000
lsof -i :8000

# Termina processi Python
pkill -f "python.*app.main"
```

## Link Utili

- [Documentazione Progetto](../docs/)
- [Frontend README](../frontend/README.md)
- [API Swagger](http://localhost:8000/docs)
