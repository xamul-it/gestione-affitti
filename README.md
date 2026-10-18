# Modstack Platform

Piattaforma web modulare a plugin. Il core è domain-agnostic; tutta la logica di business vive nei **moduli**, distribuiti come archivi ZIP installabili indipendentemente.

**Stack:** FastAPI + PostgreSQL (backend) · React + Vite (frontend)
**Multi-tenancy:** schema-based PostgreSQL (ogni tenant ha il proprio schema PG)

---

## Requisiti

| Componente | Versione minima |
|---|---|
| Python | 3.10+ |
| PostgreSQL | 13+ |
| Node.js | 18+ |

---

## Primo avvio (setup da zero)

### 1. Database

```sql
-- Eseguire come superuser PostgreSQL
CREATE DATABASE gestione_affitti;
CREATE USER affitti WITH PASSWORD 'affitti';
GRANT ALL PRIVILEGES ON DATABASE gestione_affitti TO affitti;
```

### 2. Backend

```bash
cd backend

python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# Modificare DATABASE_URL e SECRET_KEY nel file .env
```

`.env` minimale:

```env
DATABASE_URL=postgresql://affitti:affitti@localhost:5432/gestione_affitti
SECRET_KEY=cambia-questa-chiave-con-almeno-32-caratteri-casuali
```

```bash
# Avvio
./start.sh
```

> `start.sh` attiva il venv, pulisce variabili d'ambiente che confliggono con `.env`,
> e lancia uvicorn con `--reload`. Equivale a:
> `python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload`

Al primo avvio vengono creati automaticamente:
- Tabelle core nello schema `public`
- Utente admin (`admin / changeme123`) — **cambiare subito**

- API: `http://localhost:8000`
- Swagger UI: `http://localhost:8000/docs`

### 3. Frontend

```bash
cd frontend
npm install
npm run dev
```

Il file `frontend/.env` è già configurato per puntare al backend locale:

```env
VITE_API_BASE_URL=http://localhost:8000/api/v1
```

Per accesso da rete locale, cambiare l'IP:

```env
VITE_API_BASE_URL=http://192.168.x.x:8000/api/v1
```

- Frontend: `http://localhost:3000`

---

## Gestione moduli

### Avvio rapido (sviluppo)

In sviluppo i moduli in `backend/modules/` vengono caricati automaticamente all'avvio —
**non serve installare nulla** se si lavora nel repo principale con i moduli già presenti.

Per sviluppare un modulo in un **repo separato** (es. `modstack-anagrafica`) usare `module link`:

```bash
cd backend
source venv/bin/activate

# Punta alla root del repo del modulo (cerca backend/<nome>/ e frontend/<nome>/)
python manage.py module link /path/to/modstack-anagrafica

# Oppure punta direttamente alla dir del modulo backend (con __manifest__.py)
python manage.py module link /path/to/modstack-anagrafica/backend/anagrafica_italiana
```

`module link` crea symlink (equivalente di `pip install -e`):
- `backend/modules/<nome>/` → sorgente backend
- `frontend/src/modules/<nome>/` → sorgente frontend (se presente)
- Esegue le migrazioni del modulo
- Registra il modulo nel database (stato `linked`)

Riavviare il backend dopo il link. Il frontend (Vite HMR) non richiede riavvio.

### Installare un modulo da ZIP (produzione / staging)

```bash
cd backend
source venv/bin/activate

python manage.py module install /path/to/modulo_v20260101.zip
```

Lo script:
1. Valida il manifest e controlla le dipendenze
2. Estrae backend in `backend/modules/<nome>/`
3. Estrae frontend in `frontend/src/modules/<nome>/`
4. Esegue le migrazioni Alembic del modulo
5. Registra il modulo nel database

Riavviare il backend dopo l'installazione (o chiamare `POST /api/v1/modules/reload`).

### Rimuovere un modulo

```bash
# Sicuro (default): sposta i file in .removed_TIMESTAMP, dati DB intatti
python manage.py module remove nome_modulo

# Distruttivo: elimina anche le tabelle del tenant (chiede doppia conferma)
python manage.py module remove nome_modulo --drop-data
```

### Elenco e stato moduli

```bash
python manage.py module list
python manage.py module info nome_modulo
```

### Costruire lo ZIP per distribuzione

```bash
# Dalla root del repository
./build_module.sh nome_modulo      # → dist/nome_modulo_v<versione>.zip
./build_module.sh all              # tutti i moduli
```

---

## Moduli disponibili

| Modulo | Dipendenze | Descrizione |
|---|---|---|
| `anagrafica_italiana` | — | Soggetti anagrafici, documenti d'identità, comuni italiani |
| `immobili` | anagrafica_italiana | Unità immobiliari, condomini, proprietari, terreni |
| `affitti_lungo` | immobili, anagrafica_italiana | Contratti, affittuari, incassi, spese, tecnici |
| `affitti_brevi` | immobili, anagrafica_italiana | Prenotazioni, soggiorni, tasse di soggiorno, canali iCal |

---

## Struttura del progetto

```
gestione-affitti/
├── backend/
│   ├── app/
│   │   ├── core/           # Piattaforma: auth, module_system, database, middleware
│   │   └── main.py         # Entry point — auto-discovery moduli
│   ├── modules/            # Moduli installati (o linkati in sviluppo)
│   │   ├── anagrafica_italiana/
│   │   ├── immobili/
│   │   ├── affitti_lungo/
│   │   └── affitti_brevi/
│   ├── manage.py           # CLI lifecycle moduli (install / link / remove / list)
│   ├── start.sh            # Script di avvio sviluppo
│   ├── .env.example        # Template configurazione
│   └── requirements.txt
│
├── frontend/
│   └── src/
│       ├── modules/        # Moduli frontend (specchia backend/modules/)
│       ├── components/     # Componenti piattaforma condivisi
│       └── core/modules/   # Auto-discovery e registry frontend
│
├── build_module.sh         # Costruisce ZIP distribuibili
└── dist/                   # ZIP prodotti (gitignored)
```

---

## Multi-tenancy

Ogni tenant ha il proprio schema PostgreSQL (`tenant_<nome>`). Il tenant viene
risolto dal claim `tenant_schema` nel JWT; il middleware imposta il `search_path`
automaticamente su ogni request.

```bash
# Creare un tenant (API, autenticato come admin)
POST /api/v1/tenants/
{ "nome": "Mia Azienda", "schema_name": "tenant_miaazienda" }

# Installare un modulo per un tenant
POST /api/v1/tenants/{tenant_id}/modules/{module_id}/install
```

---

## Comandi di sviluppo

```bash
# Backend — tutti i test
cd backend && ./run_tests.sh

# Backend — test per modulo specifico
./run_tests.sh module anagrafica

# Backend — coverage HTML
./run_tests.sh coverage

# Frontend — test unitari (Vitest)
cd frontend && npm run test:run

# Suite completa backend + frontend
./run_all_tests.sh
```

---

## Migrazioni database

```bash
cd backend
source venv/bin/activate

# Schema public (tabelle core)
alembic upgrade head

# Tutti i tenant
alembic -x schema=all upgrade head

# Tenant specifico
alembic -x schema=tenant_test upgrade head

# Creare una nuova migrazione
alembic revision --autogenerate -m "descrizione"
# Nel file generato impostare: target_schema = "public" | "tenant" | "both"
```

> **Limite noto:** `alembic upgrade head` da solo (schema `public`, senza mai
> aver avviato l'app) **non basta a creare un database da zero**. Le tabelle
> core di base (`core_users`, `core_tenants`, `core_modules`, ecc.) non sono
> mai state create da nessuna migration — vengono create da
> `create_core_tables()` al primo avvio dell'app (`./start.sh`), come
> descritto in "Primo avvio" sopra. Le migration in questo repo presuppongono
> quella base già esistente e gestiscono solo l'evoluzione incrementale dello
> schema da lì in poi (`2025122702_legacy_anchor.py` è l'"ancora" per questo).
> Segui sempre l'ordine: **1. `./start.sh` almeno una volta, 2. poi le
> migration.** Un vero bootstrap "solo migration" (utile per pipeline
> CI/CD che separano il passo di migrazione dall'avvio dell'app) richiederebbe
> scrivere una migration iniziale che ricostruisca l'intero schema `public`
> di base — non ancora fatto, è un lavoro a sé.

---

## Credenziali di default

| Campo | Valore |
|---|---|
| Username | `admin` |
| Password | `changeme123` |
| Email | `admin@example.com` |

> **Cambiare la password al primo accesso.**
