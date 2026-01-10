# Gestione Affitti

Sistema modulare per la gestione delle proprietà immobiliari in affitto.

## Descrizione

Gestione Affitti è un'applicazione web completa per la gestione di proprietà immobiliari date in affitto. L'applicazione è progettata con un'architettura modulare che permette di aggiungere facilmente nuove funzionalità.

### Modulo Affitti a Lungo Termine

Il modulo principale attualmente implementato include:

- **Censimento Immobili**: Gestione completa degli immobili con tutti i dettagli catastali e caratteristiche
- **Censimento Affittuari**: Anagrafica completa degli affittuari con dati personali e di contatto
- **Contratti di Affitto**: Gestione dei contratti con scadenze, canoni e registrazioni
- **Spese**: Registrazione di tutte le spese per unità immobiliare con categorie e tracking pagamenti
- **Incassi**: Tracciamento degli incassi mensili collegati ai contratti

### Moduli Futuri

L'architettura modulare permette di aggiungere facilmente:
- Modulo Tasse
- Modulo Affitti Brevi
- Modulo Alert/Notifiche
- Modulo Ristrutturazione

## Stack Tecnologico

### Backend
- **Framework**: FastAPI (Python)
- **Database**: PostgreSQL
- **ORM**: SQLAlchemy
- **Validazione**: Pydantic

### Frontend
- **Framework**: React 18
- **Build Tool**: Vite
- **Routing**: React Router v6
- **HTTP Client**: Axios

## Requisiti di Sistema

- Python 3.8 o superiore
- Node.js 18 o superiore
- PostgreSQL 12 o superiore
- npm o yarn

## Installazione

### 1. Clonare il Repository

```bash
cd gestione-affitti
```

### 2. Setup Database

Creare un database PostgreSQL:

```sql
CREATE DATABASE gestione_affitti;
CREATE USER your_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE gestione_affitti TO your_user;
```

### 3. Setup Backend

```bash
cd backend

# Creare ambiente virtuale
python -m venv venv

# Attivare ambiente virtuale
# Su Linux/Mac:
source venv/bin/activate
# Su Windows:
venv\Scripts\activate

# Installare dipendenze
pip install -r requirements.txt

# Configurare variabili d'ambiente
cp .env.example .env
# Modificare .env con le proprie credenziali del database
```

Modificare il file `.env` con le proprie configurazioni:

```env
DATABASE_URL=postgresql://your_user:your_password@localhost:5432/gestione_affitti
SECRET_KEY=your-secret-key-min-32-chars
```

### 4. Setup Frontend

```bash
cd frontend

# Installare dipendenze
npm install
```

## Avvio dell'Applicazione

### Avvio Backend

```bash
cd backend
source venv/bin/activate  # Su Linux/Mac
# oppure venv\Scripts\activate su Windows

# Avviare il server
python app/main.py
```

Il backend sarà disponibile su: `http://localhost:8000`

Documentazione API interattiva: `http://localhost:8000/docs`

### Avvio Frontend

```bash
cd frontend
npm run dev
```

Il frontend sarà disponibile su: `http://localhost:3000`

## Struttura del Progetto

```
gestione-affitti/
├── backend/
│   ├── app/
│   │   ├── core/              # Configurazioni core
│   │   │   ├── config.py
│   │   │   └── database.py
│   │   ├── modules/           # Moduli dell'applicazione
│   │   │   └── affitti_lungo/
│   │   │       ├── models/    # Modelli SQLAlchemy
│   │   │       ├── schemas/   # Schemi Pydantic
│   │   │       └── routes/    # Endpoints API
│   │   └── main.py           # Entry point
│   ├── requirements.txt
│   └── .env.example
│
└── frontend/
    ├── src/
    │   ├── components/        # Componenti React
    │   │   ├── Immobili/
    │   │   ├── Affittuari/
    │   │   ├── Contratti/
    │   │   ├── Spese/
    │   │   ├── Incassi/
    │   │   └── Layout/
    │   ├── pages/            # Pagine
    │   ├── services/         # Servizi API
    │   ├── App.jsx
    │   └── main.jsx
    ├── package.json
    └── vite.config.js
```

## API Endpoints

### Immobili
- `GET /api/v1/immobili/` - Lista immobili
- `GET /api/v1/immobili/{id}` - Dettaglio immobile
- `POST /api/v1/immobili/` - Crea immobile
- `PUT /api/v1/immobili/{id}` - Aggiorna immobile
- `DELETE /api/v1/immobili/{id}` - Elimina immobile

### Affittuari
- `GET /api/v1/affittuari/` - Lista affittuari
- `GET /api/v1/affittuari/{id}` - Dettaglio affittuario
- `POST /api/v1/affittuari/` - Crea affittuario
- `PUT /api/v1/affittuari/{id}` - Aggiorna affittuario
- `DELETE /api/v1/affittuari/{id}` - Elimina affittuario

### Contratti
- `GET /api/v1/contratti/` - Lista contratti
- `GET /api/v1/contratti/{id}` - Dettaglio contratto
- `GET /api/v1/contratti/immobile/{immobile_id}` - Contratti per immobile
- `GET /api/v1/contratti/affittuario/{affittuario_id}` - Contratti per affittuario
- `POST /api/v1/contratti/` - Crea contratto
- `PUT /api/v1/contratti/{id}` - Aggiorna contratto
- `DELETE /api/v1/contratti/{id}` - Elimina contratto

### Spese
- `GET /api/v1/spese/` - Lista spese
- `GET /api/v1/spese/{id}` - Dettaglio spesa
- `GET /api/v1/spese/immobile/{immobile_id}` - Spese per immobile
- `POST /api/v1/spese/` - Crea spesa
- `PUT /api/v1/spese/{id}` - Aggiorna spesa
- `DELETE /api/v1/spese/{id}` - Elimina spesa

### Incassi
- `GET /api/v1/incassi/` - Lista incassi
- `GET /api/v1/incassi/{id}` - Dettaglio incasso
- `GET /api/v1/incassi/contratto/{contratto_id}` - Incassi per contratto
- `POST /api/v1/incassi/` - Crea incasso
- `PUT /api/v1/incassi/{id}` - Aggiorna incasso
- `DELETE /api/v1/incassi/{id}` - Elimina incasso

## Sviluppo di Nuovi Moduli

Per aggiungere un nuovo modulo:

1. Creare la struttura del modulo in `backend/app/modules/nome_modulo/`
2. Implementare modelli, schemi e routes
3. Registrare i router in `main.py`
4. Creare i componenti React in `frontend/src/components/NomeModulo/`
5. Aggiungere le routes in `App.jsx`

## Build per Produzione

### Backend

```bash
cd backend
pip install gunicorn
gunicorn -w 4 -k uvicorn.workers.UvicornWorker app.main:app
```

### Frontend

```bash
cd frontend
npm run build
```

I file statici saranno generati nella cartella `dist/` e possono essere serviti da un web server come Nginx o Apache.

## Licenza

Questo progetto è distribuito sotto licenza MIT.

## Supporto

Per problemi o domande, aprire una issue su GitHub o contattare il team di sviluppo.

## Contributi

I contributi sono benvenuti! Per favore:
1. Fork del repository
2. Creare un branch per la feature (`git checkout -b feature/AmazingFeature`)
3. Commit delle modifiche (`git commit -m 'Add some AmazingFeature'`)
4. Push al branch (`git push origin feature/AmazingFeature`)
5. Aprire una Pull Request

## Autori

- Team di Sviluppo Gestione Affitti

## Changelog

### v1.0.0 (2024)
- Release iniziale con modulo Affitti a Lungo Termine
- Gestione completa di immobili, affittuari, contratti, spese e incassi
- Interfaccia web responsive con React
- API REST completa con FastAPI
