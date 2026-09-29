# Motore Scadenze Compliance — Affitti Brevi (Sub-progetto A) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Collegare il modulo `affitti_brevi` al motore scadenze core della piattaforma (`Scadenza`/`ScadenzaService`), eliminando due generazioni di codice morto per le comunicazioni obbligatorie, e validare il pattern end-to-end su due trigger per-`Soggiorno` senza integrazioni esterne (comunicazione Polizia, promemoria pagamento tassa di soggiorno).

**Architecture:** Un nuovo `ComplianceScadenzeService` crea righe `Comunicazione` + `Scadenza` core collegate quando un `Soggiorno` si avvicina al check-in; un job APScheduler orario (stesso pattern bound-`Connection` multi-tenant di `sync_scheduler.py`) le genera automaticamente; una nuova route permette il completamento manuale; il frontend espone un link di risoluzione dal pannello notifiche verso una pagina di dettaglio dedicata.

**Tech Stack:** FastAPI, SQLAlchemy, Alembic (migrazioni multi-schema), APScheduler, React, Vitest (se applicabile).

**Spec:** `docs/superpowers/specs/2026-09-28-affitti-brevi-motore-scadenze-compliance-design.md`

## Global Constraints

- Ogni `Comunicazione`/`Scadenza` generata deve essere **idempotente**: una seconda esecuzione sullo stesso `Soggiorno`+tipo non deve duplicare nulla.
- Ogni funzione multi-tenant (scheduler) usa il pattern bound-`Connection` (mai `SessionLocal()` nudo attraverso un commit) — vedi `sync_scheduler.py`/`scadenza_reminder_job.py` come riferimento.
- Le scadenze generate da job devono avere `destinatari_ids` = tutti i `User` con `is_superuser=True, is_active=True` del tenant corrente (altrimenti sono invisibili a tutti in `NotifichePanel`/`GET /scadenze/`, che filtrano per creatore-o-destinatario).
- Nessuna integrazione esterna (Alloggiati Web, messaggistica, pagamenti) in questo sotto-progetto: il completamento delle `Comunicazione` è sempre manuale via endpoint.
- Le route di `affitti_brevi` non usano `require_permission`/`get_current_user` da nessuna parte del modulo oggi (verificato via grep): la nuova route segue lo stesso stile (solo `Depends(get_db)`), per coerenza — non è un'omissione, è lo stile già in uso nel modulo.
- Codice morto pre-refactor da eliminare, non da recuperare: `scadenza_generator.py`, `comunicazione_polizia_service.py`, `routes/tasse.py`, il modello `AttivitaSchedulata`/`Log`, e il cluster frontend `components/Scadenze/*` + l'export `scadenzeAPI` in `affittiBreviAPI.js` (tutti riferiscono modelli/endpoint che non esistono più).
- `routes/tasse.py` NON viene ricostruito qui — resta commentato/assente, è compito del sotto-progetto B.

---

### Task 1: Rimuovere il codice morto lato backend

**Files:**
- Delete: `backend/modules/affitti_brevi/services/scadenza_generator.py`
- Delete: `backend/modules/affitti_brevi/services/comunicazione_polizia_service.py`
- Delete: `backend/modules/affitti_brevi/routes/tasse.py`
- Modify: `backend/modules/affitti_brevi/routes/__init__.py`

**Interfaces:**
- Nessuna — nessun file esistente importa questi tre moduli con successo (verificato via grep: sono raggiungibili solo da se stessi/tra loro), quindi la rimozione non rompe nulla di funzionante.

- [ ] **Step 1: Verificare che nessun altro file importi i tre moduli da eliminare**

Esegui:
```bash
cd backend
grep -rn "scadenza_generator\|comunicazione_polizia_service\|routes\.tasse\|routes import tasse\|from \.routes import.*tasse" modules/affitti_brevi --include=*.py | grep -v __pycache__
```
Atteso: solo i riferimenti interni ai tre file stessi (es. `tasse.py` che importa da `comunicazione_polizia_service` — non rilevante, lo cancelliamo comunque) e il commento in `routes/__init__.py`. Nessun altro modulo attivo li importa.

- [ ] **Step 2: Eliminare i tre file**

```bash
rm backend/modules/affitti_brevi/services/scadenza_generator.py
rm backend/modules/affitti_brevi/services/comunicazione_polizia_service.py
rm backend/modules/affitti_brevi/routes/tasse.py
```

- [ ] **Step 3: Aggiornare `routes/__init__.py`**

Sostituisci il contenuto con:

```python
"""
Affitti Brevi Routes

API endpoints for short-term rental management:
- Canali: Booking platform configuration
- Calendari: Property-channel link management
- CalendarioUnificato: Unified calendar view
- Prenotazioni: Booking management
- Soggiorni: Stay operations (check-in, check-out, guests)
- Sync: iCal synchronization
"""
from . import (
    canali,
    calendari,
    calendario_unificato,
    prenotazioni,
    soggiorni,
    sync,
)

# NOTE: router "tasse" ancora assente — la ricostruzione del calcolo/
# dichiarazione tassa di soggiorno contro i modelli attuali (TassaSoggiorno)
# è compito del sotto-progetto B (vedi docs/superpowers/specs/
# 2026-09-28-affitti-brevi-motore-scadenze-compliance-design.md).
#
# NOTE: router "comunicazioni" arriva con il Task 7 di questo piano — non è
# ancora aggiunto qui per evitare un ImportError in ogni verifica intermedia
# (import app.main, test suite) dei Task 2-6, che girano prima che quel
# modulo esista.

__all__ = [
    "canali",
    "calendari",
    "calendario_unificato",
    "prenotazioni",
    "soggiorni",
    "sync",
]
```

(Il router `comunicazioni` viene aggiunto qui solo al Task 7, quando il modulo esiste — vedi la NOTE nel file sopra. Questo mantiene il modulo importabile ad ogni task intermedio.)

- [ ] **Step 4: Commit**

```bash
git add backend/modules/affitti_brevi/services/scadenza_generator.py \
        backend/modules/affitti_brevi/services/comunicazione_polizia_service.py \
        backend/modules/affitti_brevi/routes/tasse.py \
        backend/modules/affitti_brevi/routes/__init__.py
git commit -m "chore(affitti_brevi): remove dead pre-refactor compliance code"
```

---

### Task 2: Migrazione schema — drop `AttivitaSchedulata`, aggiungi `Comunicazione.scadenza_id`

**Files:**
- Delete: `backend/modules/affitti_brevi/models/attivita_schedulata.py`
- Modify: `backend/modules/affitti_brevi/models/__init__.py`
- Modify: `backend/modules/affitti_brevi/models/comunicazione.py`
- Modify: `backend/modules/affitti_brevi/migrations/versions/2025021701_create_affitti_brevi_tables.py`
- Create: `backend/modules/affitti_brevi/migrations/versions/2025021702_compliance_scadenze_engine.py`

**Interfaces:**
- Produce: `Comunicazione.scadenza_id: Optional[int]` — usato da `ComplianceScadenzeService` (Task 4/5) per collegare la `Comunicazione` alla `Scadenza` core.

- [ ] **Step 1: Rimuovere `AttivitaSchedulata` dal modello**

```bash
rm backend/modules/affitti_brevi/models/attivita_schedulata.py
```

In `backend/modules/affitti_brevi/models/__init__.py`, rimuovi il blocco:
```python
# Scheduled activities
from .attivita_schedulata import (
    AttivitaSchedulata,
    AttivitaSchedulataLog,
    TipoAttivita,
    StatoAttivita,
    Periodicita
)
```
e dal docstring del file rimuovi la riga `- AttivitaSchedulata: Scheduled tasks`. Rimuovi anche dalla lista `__all__`:
```python
    # Attività
    "AttivitaSchedulata",
    "AttivitaSchedulataLog",
    "TipoAttivita",
    "StatoAttivita",
    "Periodicita",
```

- [ ] **Step 2: Rimuovere l'import di `attivita_schedulata` dalla migrazione originale**

In `backend/modules/affitti_brevi/migrations/versions/2025021701_create_affitti_brevi_tables.py`, rimuovi la riga:
```python
    "affitti_brevi.models.attivita_schedulata",
```
dalla lista `for module_name in [...]`. (Questa migrazione costruisce `Base.metadata` dinamicamente da tutti i moduli `ab_*` importati: senza questa riga, un tenant **nuovo** non creerà più le tabelle `ab_attivita_schedulate*`. Per i tenant **esistenti** che le hanno già, serve il drop esplicito nella nuova migrazione, step successivo.)

- [ ] **Step 3: Aggiungere `scadenza_id` a `Comunicazione`**

In `backend/modules/affitti_brevi/models/comunicazione.py`, aggiungi dopo il campo `soggiorno_id` (circa riga 66):

```python
    # Collegamento alla scadenza core (cross-schema: core_scadenze vive in
    # public, ab_comunicazioni nello schema tenant — nessun vincolo FK
    # reale possibile, stesso motivo per cui Scadenza.entity_id è un
    # intero libero verso le tabelle di modulo).
    scadenza_id = Column(
        Integer,
        nullable=True,
        index=True,
        comment="FK logica a core_scadenze.id"
    )
```

- [ ] **Step 4: Scrivere la migrazione**

Crea `backend/modules/affitti_brevi/migrations/versions/2025021702_compliance_scadenze_engine.py`:

```python
"""compliance scadenze engine

Drop the never-executed AttivitaSchedulata/Log tables (superseded by the
compliance scheduler's per-tenant APScheduler job) and add
Comunicazione.scadenza_id (link to the core Scadenza this Comunicazione
was generated for).

Revision ID: 2025021702
Revises: 2025021701
Create Date: 2026-09-29 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '2025021702'
down_revision = '2025021701'
branch_labels = None
depends_on = None

# Target schema: tenant schemas only
target_schema = "tenant"


def upgrade():
    op.drop_table('ab_attivita_schedulate_log')
    op.drop_table('ab_attivita_schedulate')

    op.add_column(
        'ab_comunicazioni',
        sa.Column('scadenza_id', sa.Integer(), nullable=True,
                  comment='FK logica a core_scadenze.id')
    )
    op.create_index('ix_ab_comunicazioni_scadenza_id', 'ab_comunicazioni', ['scadenza_id'])


def downgrade():
    op.drop_index('ix_ab_comunicazioni_scadenza_id', table_name='ab_comunicazioni')
    op.drop_column('ab_comunicazioni', 'scadenza_id')

    op.create_table(
        'ab_attivita_schedulate',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('tipo', sa.String(50), nullable=False),
        sa.Column('nome', sa.String(200), nullable=False),
        sa.Column('descrizione', sa.Text(), nullable=True),
        sa.Column('unita_immobiliare_id', sa.Integer(),
                  sa.ForeignKey('immo_unita_immobiliari.id', ondelete='SET NULL'), nullable=True),
        sa.Column('canale_id', sa.Integer(),
                  sa.ForeignKey('ab_canali.id', ondelete='SET NULL'), nullable=True),
        sa.Column('periodicita', sa.String(30), nullable=False, server_default='SINGOLA'),
        sa.Column('ora_esecuzione', sa.String(5), nullable=True, server_default='06:00'),
        sa.Column('giorno_settimana', sa.Integer(), nullable=True),
        sa.Column('giorno_mese', sa.Integer(), nullable=True),
        sa.Column('prossima_esecuzione', sa.DateTime(timezone=True), nullable=True),
        sa.Column('ultima_esecuzione', sa.DateTime(timezone=True), nullable=True),
        sa.Column('stato', sa.String(30), nullable=False, server_default='PIANIFICATA'),
        sa.Column('attiva', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('esito_ultima_esecuzione', sa.Text(), nullable=True),
        sa.Column('errore_ultima_esecuzione', sa.Text(), nullable=True),
        sa.Column('esecuzioni_totali', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('esecuzioni_successo', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('esecuzioni_fallite', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('precondizioni', sa.Text(), nullable=True),
        sa.Column('output_tipo', sa.String(50), nullable=True),
        sa.Column('output_destinatari', sa.Text(), nullable=True),
        sa.Column('notifica_completamento', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('notifica_errore', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('notifica_scadenza', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('note', sa.Text(), nullable=True),
        sa.Column('creato_da', sa.String(100), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('ix_ab_attivita_prossima_esec', 'ab_attivita_schedulate',
                     ['prossima_esecuzione', 'attiva'])
    op.create_index('ix_ab_attivita_tipo_stato', 'ab_attivita_schedulate', ['tipo', 'stato'])

    op.create_table(
        'ab_attivita_schedulate_log',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('attivita_id', sa.Integer(),
                  sa.ForeignKey('ab_attivita_schedulate.id', ondelete='CASCADE'), nullable=False),
        sa.Column('data_esecuzione', sa.DateTime(timezone=True), nullable=False),
        sa.Column('data_completamento', sa.DateTime(timezone=True), nullable=True),
        sa.Column('durata_secondi', sa.Integer(), nullable=True),
        sa.Column('stato', sa.String(30), nullable=False),
        sa.Column('esito', sa.Text(), nullable=True),
        sa.Column('errore', sa.Text(), nullable=True),
        sa.Column('elementi_processati', sa.Integer(), server_default='0'),
        sa.Column('elementi_successo', sa.Integer(), server_default='0'),
        sa.Column('elementi_errore', sa.Integer(), server_default='0'),
        sa.Column('elementi_saltati', sa.Integer(), server_default='0'),
        sa.Column('eseguito_da', sa.String(100), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
```

- [ ] **Step 5: Applicare la migrazione su tutti i tenant**

```bash
cd backend
source venv/bin/activate
alembic -x schema=all upgrade head
```

Verifica:
```bash
psql "$DATABASE_URL" -c "\dt tenant_qa_test.ab_attivita_schedulate*"
```
Atteso: `Did not find any relation`. E:
```bash
psql "$DATABASE_URL" -c "\d tenant_qa_test.ab_comunicazioni" | grep scadenza_id
```
Atteso: la colonna `scadenza_id` presente.

- [ ] **Step 6: Verificare che l'app importi ancora correttamente**

```bash
cd backend
python -c "import app.main"
```
Atteso: nessun `ImportError`/`ModuleNotFoundError` (conferma che nessun altro file importa ancora `attivita_schedulata`).

- [ ] **Step 7: Commit**

```bash
git add backend/modules/affitti_brevi/models/attivita_schedulata.py \
        backend/modules/affitti_brevi/models/__init__.py \
        backend/modules/affitti_brevi/models/comunicazione.py \
        backend/modules/affitti_brevi/migrations/versions/2025021701_create_affitti_brevi_tables.py \
        backend/modules/affitti_brevi/migrations/versions/2025021702_compliance_scadenze_engine.py
git commit -m "feat(affitti_brevi): drop dead AttivitaSchedulata engine, link Comunicazione to core Scadenza"
```

---

### Task 3: Estrarre l'helper multi-tenant condiviso

**Files:**
- Create: `backend/modules/affitti_brevi/services/tenant_scan.py`
- Modify: `backend/modules/affitti_brevi/services/sync_scheduler.py`

**Interfaces:**
- Produce: `get_active_tenant_schemas(modulo: str) -> list[str]` — usata da `sync_scheduler.py` (Task esistente, refactor) e da `compliance_scheduler.py` (Task 6).

- [ ] **Step 1: Creare `tenant_scan.py`**

```python
"""
Tenant Scan Helper

Elenca gli schema dei tenant attivi con un dato modulo abilitato.
Estratto da sync_scheduler.py: sia lo scheduler di sync iCal sia il
compliance_scheduler (docs/superpowers/specs/2026-09-28-affitti-brevi-motore-
scadenze-compliance-design.md) hanno bisogno della stessa identica
iterazione multi-tenant.
"""
from typing import List
import logging

from sqlalchemy import text

from app.core.database import SessionLocal

logger = logging.getLogger(__name__)


def get_active_tenant_schemas(modulo: str) -> List[str]:
    """Schemi dei tenant attivi che hanno `modulo` abilitato."""
    from app.core.services.tenant_service import TenantService

    db = SessionLocal()
    try:
        db.connection().execute(text("SET search_path TO public"))
        rows = db.execute(
            text("SELECT id, schema_name FROM public.core_tenants WHERE active = true OR active IS NULL")
        ).fetchall()
        schemas = []
        for tenant_id, schema_name in rows:
            try:
                if modulo in TenantService.get_enabled_modules(tenant_id, db):
                    schemas.append(schema_name)
            except Exception as e:
                logger.warning("Could not check enabled modules for tenant %s: %s", schema_name, e)
        return schemas
    except Exception as e:
        logger.warning("Could not list tenants for '%s' scan: %s", modulo, e)
        return []
    finally:
        db.close()
```

- [ ] **Step 2: Aggiornare `sync_scheduler.py` per usare l'helper condiviso**

In `backend/modules/affitti_brevi/services/sync_scheduler.py`:
1. Aggiungi l'import in cima al file: `from .tenant_scan import get_active_tenant_schemas`
2. Rimuovi l'intera funzione `_get_active_tenant_schemas()` (righe 71-93 del file attuale).
3. In `SyncScheduler.sync_job()`, sostituisci:
   ```python
   for tenant_schema in _get_active_tenant_schemas():
   ```
   con:
   ```python
   for tenant_schema in get_active_tenant_schemas("affitti_brevi"):
   ```

- [ ] **Step 3: Rieseguire la suite di test esistente per affitti_brevi**

```bash
cd backend
./run_tests.sh module affitti_brevi
```
Atteso: tutti i test già esistenti (inclusi quelli di `test_ical_sync.py`) passano ancora — il refactor non cambia il comportamento, solo la posizione del codice.

- [ ] **Step 4: Commit**

```bash
git add backend/modules/affitti_brevi/services/tenant_scan.py \
        backend/modules/affitti_brevi/services/sync_scheduler.py
git commit -m "refactor(affitti_brevi): extract shared multi-tenant scan helper"
```

---

### Task 4: `ComplianceScadenzeService` — generazione scadenze Polizia e tassa

**Files:**
- Create: `backend/modules/affitti_brevi/services/compliance_scadenze_service.py`
- Test: `backend/tests/integration/test_modules/test_affitti_brevi/test_compliance_scadenze_service.py`

**Interfaces:**
- Produce: `ComplianceScadenzeService(db).genera_scadenza_polizia(soggiorno: Soggiorno) -> Optional[Comunicazione]`
- Produce: `ComplianceScadenzeService(db).genera_scadenza_tassa(soggiorno: Soggiorno) -> Optional[Comunicazione]`
- Consuma: `ScadenzaService` (`app.core.platform_services`), `ScadenzaCreate`/`PrioritaScadenza` (`app.core.schemas`), `get_system_user_id` (`app.core.auth.init_data`), `User` (`app.core.auth.models`).

- [ ] **Step 1: Scrivere il test che fallisce**

Crea `backend/tests/integration/test_modules/test_affitti_brevi/test_compliance_scadenze_service.py`:

```python
"""
Test per ComplianceScadenzeService — motore scadenze compliance
(docs/superpowers/specs/2026-09-28-affitti-brevi-motore-scadenze-compliance-design.md).

Usa pg_session bound a singola Connection (pattern stabilito in questa
sessione, vedi test_ical_sync.py per il razionale).
"""
from datetime import date, timedelta

import pytest
from sqlalchemy import text

from affitti_brevi.models import Comunicazione, TipoComunicazione, Prenotazione, Soggiorno
from affitti_brevi.services.compliance_scadenze_service import ComplianceScadenzeService
from app.core.platform_services import ScadenzaService
from immobili.models import UnitaImmobiliare

TENANT = "tenant_qa_test"


@pytest.fixture(autouse=True)
def override_get_db():
    """Shadow conftest.py's autouse override_get_db(db_session) for this module only — see test_notifica_model.py for rationale."""
    yield


@pytest.fixture
def pg_session():
    from app.core.database import engine
    from sqlalchemy.orm import Session as SASession

    connection = engine.connect()
    connection.execute(text(f"SET search_path TO {TENANT}, public"))
    connection.commit()
    session = SASession(bind=connection)
    try:
        yield session
    finally:
        session.close()
        connection.close()


@pytest.fixture
def soggiorno(pg_session):
    unita = UnitaImmobiliare(
        codice="TEST-COMPL-001",
        tipo="Appartamento",
        indirizzo="Via Test 1",
        citta="Testville",
    )
    pg_session.add(unita)
    pg_session.flush()

    checkin = date.today() + timedelta(hours=6)
    prenotazione = Prenotazione(
        unita_immobiliare_id=unita.id,
        codice_prenotazione="TEST-COMPL-PREN-001",
        data_checkin=date.today(),
        data_checkout=date.today() + timedelta(days=3),
    )
    pg_session.add(prenotazione)
    pg_session.flush()

    s = Soggiorno(
        prenotazione_id=prenotazione.id,
        unita_immobiliare_id=unita.id,
        data_checkin=date.today(),
        data_checkout=date.today() + timedelta(days=3),
    )
    pg_session.add(s)
    pg_session.commit()

    yield s

    pg_session.query(Comunicazione).filter_by(soggiorno_id=s.id).delete()
    pg_session.query(Soggiorno).filter_by(id=s.id).delete()
    pg_session.query(Prenotazione).filter_by(id=prenotazione.id).delete()
    pg_session.query(UnitaImmobiliare).filter_by(id=unita.id).delete()
    pg_session.commit()


def test_genera_scadenza_polizia_crea_comunicazione_e_scadenza(pg_session, soggiorno):
    service = ComplianceScadenzeService(pg_session)

    comunicazione = service.genera_scadenza_polizia(soggiorno)

    assert comunicazione is not None
    assert comunicazione.tipo == TipoComunicazione.POLIZIA.value
    assert comunicazione.scadenza_id is not None

    scadenza = ScadenzaService(pg_session).get_scadenza(comunicazione.scadenza_id)
    assert scadenza is not None
    assert scadenza.modulo == "affitti_brevi"
    assert scadenza.entity_type == "comunicazione"
    assert scadenza.entity_id == comunicazione.id
    # 24h dal check-in
    assert scadenza.data_scadenza == soggiorno.data_checkin + timedelta(days=1)


def test_genera_scadenza_polizia_idempotente(pg_session, soggiorno):
    service = ComplianceScadenzeService(pg_session)

    primo = service.genera_scadenza_polizia(soggiorno)
    secondo = service.genera_scadenza_polizia(soggiorno)

    assert primo is not None
    assert secondo is None  # no-op, già esisteva

    count = pg_session.query(Comunicazione).filter_by(
        soggiorno_id=soggiorno.id, tipo=TipoComunicazione.POLIZIA.value
    ).count()
    assert count == 1


def test_genera_scadenza_tassa_crea_comunicazione_con_data_checkin(pg_session, soggiorno):
    service = ComplianceScadenzeService(pg_session)

    comunicazione = service.genera_scadenza_tassa(soggiorno)

    assert comunicazione is not None
    assert comunicazione.tipo == TipoComunicazione.TASSA_DICHIARAZIONE.value

    scadenza = ScadenzaService(pg_session).get_scadenza(comunicazione.scadenza_id)
    assert scadenza.data_scadenza == soggiorno.data_checkin
```

- [ ] **Step 2: Eseguire il test e verificare che fallisca**

```bash
cd backend
pytest tests/integration/test_modules/test_affitti_brevi/test_compliance_scadenze_service.py -v
```
Atteso: `ModuleNotFoundError: No module named 'affitti_brevi.services.compliance_scadenze_service'`.

- [ ] **Step 3: Implementare `ComplianceScadenzeService`**

Crea `backend/modules/affitti_brevi/services/compliance_scadenze_service.py`:

```python
"""
Compliance Scadenze Service

Collega affitti_brevi al motore scadenze core della piattaforma
(app.core.platform_services.scadenza_service.ScadenzaService) per le
comunicazioni obbligatorie legate a un Soggiorno: comunicazione Polizia
(24h dal check-in) e promemoria pagamento tassa di soggiorno (giorno del
check-in). Vedi docs/superpowers/specs/2026-09-28-affitti-brevi-motore-
scadenze-compliance-design.md.

Non invia nulla a nessun portale esterno: il completamento è sempre
manuale in questa fase (vedi completa_comunicazione).
"""
from datetime import datetime, timedelta, timezone
from typing import List, Optional

from sqlalchemy.orm import Session

from affitti_brevi.models import (
    Comunicazione,
    TipoComunicazione,
    StatoComunicazione,
    MetodoInvio,
    Soggiorno,
)
from app.core.auth.init_data import get_system_user_id
from app.core.auth.models import User
from app.core.platform_services import ScadenzaService
from app.core.schemas import ScadenzaCreate, PrioritaScadenza


def _get_admin_destinatari_ids(db: Session) -> List[int]:
    """
    Id di tutti i superuser attivi del tenant corrente.

    Non esiste ancora un concetto di "responsabile struttura" nel sistema
    (vedi spec, sezione decisioni di scope): per questo sotto-progetto le
    scadenze compliance notificano tutti gli admin del tenant.
    """
    return [
        row[0] for row in
        db.query(User.id).filter(User.is_superuser == True, User.is_active == True).all()
    ]


class ComplianceScadenzeService:
    def __init__(self, db: Session):
        self.db = db

    def genera_scadenza_polizia(self, soggiorno: Soggiorno) -> Optional[Comunicazione]:
        """Genera la Comunicazione+Scadenza per la comunicazione Polizia
        (24h dal check-in). Idempotente: None se già esiste."""
        esistente = self.db.query(Comunicazione).filter(
            Comunicazione.soggiorno_id == soggiorno.id,
            Comunicazione.tipo == TipoComunicazione.POLIZIA.value,
        ).first()
        if esistente:
            return None

        checkin_start = datetime.combine(soggiorno.data_checkin, datetime.min.time()).replace(tzinfo=timezone.utc)
        scadenza_dt = checkin_start + timedelta(hours=24)

        comunicazione = Comunicazione(
            soggiorno_id=soggiorno.id,
            unita_immobiliare_id=soggiorno.unita_immobiliare_id,
            tipo=TipoComunicazione.POLIZIA.value,
            stato=StatoComunicazione.DA_PREPARARE.value,
            data_scadenza=scadenza_dt,
        )
        self.db.add(comunicazione)
        self.db.flush()

        scadenza = ScadenzaService(self.db).create_scadenza(
            ScadenzaCreate(
                modulo="affitti_brevi",
                entity_type="comunicazione",
                entity_id=comunicazione.id,
                titolo=f"Comunicazione Polizia — Soggiorno #{soggiorno.id}",
                descrizione=(
                    f"Comunicare i dati di {soggiorno.numero_ospiti_previsti} ospiti entro 24h "
                    f"dal check-in del {soggiorno.data_checkin.isoformat()}."
                ),
                data_scadenza=scadenza_dt.date(),
                priorita=PrioritaScadenza.ALTA,
                destinatari_ids=_get_admin_destinatari_ids(self.db),
            ),
            user_id=get_system_user_id(self.db),
        )
        comunicazione.scadenza_id = scadenza.id
        self.db.commit()
        self.db.refresh(comunicazione)
        return comunicazione

    def genera_scadenza_tassa(self, soggiorno: Soggiorno) -> Optional[Comunicazione]:
        """Genera la Comunicazione+Scadenza promemoria pagamento tassa di
        soggiorno (giorno del check-in). Idempotente: None se già esiste."""
        esistente = self.db.query(Comunicazione).filter(
            Comunicazione.soggiorno_id == soggiorno.id,
            Comunicazione.tipo == TipoComunicazione.TASSA_DICHIARAZIONE.value,
        ).first()
        if esistente:
            return None

        checkin_start = datetime.combine(soggiorno.data_checkin, datetime.min.time()).replace(tzinfo=timezone.utc)

        importo = None
        if soggiorno.tassa_soggiorno is not None:
            importo = soggiorno.tassa_soggiorno.importo_effettivo

        descrizione = f"Richiedi il pagamento della tassa di soggiorno per il soggiorno #{soggiorno.id}."
        descrizione += f" Importo calcolato: € {importo:.2f}." if importo is not None else " Importo da calcolare."

        comunicazione = Comunicazione(
            soggiorno_id=soggiorno.id,
            unita_immobiliare_id=soggiorno.unita_immobiliare_id,
            tipo=TipoComunicazione.TASSA_DICHIARAZIONE.value,
            stato=StatoComunicazione.DA_PREPARARE.value,
            data_scadenza=checkin_start,
        )
        self.db.add(comunicazione)
        self.db.flush()

        scadenza = ScadenzaService(self.db).create_scadenza(
            ScadenzaCreate(
                modulo="affitti_brevi",
                entity_type="comunicazione",
                entity_id=comunicazione.id,
                titolo=f"Richiedi pagamento tassa di soggiorno — Soggiorno #{soggiorno.id}",
                descrizione=descrizione,
                data_scadenza=soggiorno.data_checkin,
                priorita=PrioritaScadenza.MEDIA,
                destinatari_ids=_get_admin_destinatari_ids(self.db),
            ),
            user_id=get_system_user_id(self.db),
        )
        comunicazione.scadenza_id = scadenza.id
        self.db.commit()
        self.db.refresh(comunicazione)
        return comunicazione
```

- [ ] **Step 4: Eseguire il test e verificare che passi**

```bash
cd backend
pytest tests/integration/test_modules/test_affitti_brevi/test_compliance_scadenze_service.py -v
```
Atteso: 3 test PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/modules/affitti_brevi/services/compliance_scadenze_service.py \
        backend/tests/integration/test_modules/test_affitti_brevi/test_compliance_scadenze_service.py
git commit -m "feat(affitti_brevi): add ComplianceScadenzeService for police/tax deadline generation"
```

---

### Task 5: `ComplianceScadenzeService.completa_comunicazione`

**Files:**
- Modify: `backend/modules/affitti_brevi/services/compliance_scadenze_service.py`
- Modify: `backend/tests/integration/test_modules/test_affitti_brevi/test_compliance_scadenze_service.py`

**Interfaces:**
- Produce: `ComplianceScadenzeService(db).completa_comunicazione(comunicazione_id: int, note: Optional[str] = None) -> Comunicazione`
- Consuma: `Comunicazione.mark_inviata` (già esistente sul modello), `ScadenzaService.completa_scadenza` (già esistente).

- [ ] **Step 1: Aggiungere il test che fallisce**

Aggiungi in fondo a `test_compliance_scadenze_service.py`:

```python
def test_completa_comunicazione_marca_invio_e_completa_scadenza(pg_session, soggiorno):
    service = ComplianceScadenzeService(pg_session)
    comunicazione = service.genera_scadenza_polizia(soggiorno)

    aggiornata = service.completa_comunicazione(comunicazione.id, note="Inviata a mano")

    assert aggiornata.stato == "INVIATA"

    from app.core.platform.models import StatoScadenza
    scadenza = ScadenzaService(pg_session).get_scadenza(aggiornata.scadenza_id)
    assert scadenza.stato == StatoScadenza.COMPLETATA


def test_completa_comunicazione_id_inesistente_solleva_valueerror(pg_session):
    service = ComplianceScadenzeService(pg_session)
    with pytest.raises(ValueError):
        service.completa_comunicazione(999999)
```

- [ ] **Step 2: Eseguire e verificare che falliscano**

```bash
cd backend
pytest tests/integration/test_modules/test_affitti_brevi/test_compliance_scadenze_service.py -v -k completa_comunicazione
```
Atteso: `AttributeError: 'ComplianceScadenzeService' object has no attribute 'completa_comunicazione'`.

- [ ] **Step 3: Implementare il metodo**

In `backend/modules/affitti_brevi/services/compliance_scadenze_service.py`, aggiungi alla classe `ComplianceScadenzeService`:

```python
    def completa_comunicazione(self, comunicazione_id: int, note: Optional[str] = None) -> Comunicazione:
        """Marca la Comunicazione come inviata (manualmente) e completa la
        Scadenza core collegata, se presente."""
        comunicazione = self.db.query(Comunicazione).filter(
            Comunicazione.id == comunicazione_id
        ).first()
        if not comunicazione:
            raise ValueError(f"Comunicazione {comunicazione_id} non trovata")

        comunicazione.mark_inviata(MetodoInvio.MANUALE)
        self.db.commit()
        self.db.refresh(comunicazione)

        if comunicazione.scadenza_id:
            ScadenzaService(self.db).completa_scadenza(
                comunicazione.scadenza_id,
                user_id=get_system_user_id(self.db),
                note=note or "Completata da affitti_brevi",
            )

        return comunicazione
```

- [ ] **Step 4: Eseguire tutti i test del file e verificare che passino**

```bash
cd backend
pytest tests/integration/test_modules/test_affitti_brevi/test_compliance_scadenze_service.py -v
```
Atteso: 5 test PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/modules/affitti_brevi/services/compliance_scadenze_service.py \
        backend/tests/integration/test_modules/test_affitti_brevi/test_compliance_scadenze_service.py
git commit -m "feat(affitti_brevi): add manual completion for compliance Comunicazione"
```

---

### Task 6: Scheduler orario e wiring in `register_module`

**Files:**
- Create: `backend/modules/affitti_brevi/services/compliance_scheduler.py`
- Modify: `backend/modules/affitti_brevi/__init__.py`
- Test: `backend/tests/unit/test_modules/test_affitti_brevi/test_compliance_scheduler.py`
- Test: `backend/tests/integration/test_modules/test_affitti_brevi/test_compliance_scan_tenant.py`

**Interfaces:**
- Produce: `get_compliance_scheduler(interval_hours: int = 1) -> ComplianceScheduler`, con `.start()`/`.stop()`/`.is_running`, stessa shape di `get_scheduler()` in `sync_scheduler.py`.
- Consuma: `get_active_tenant_schemas` (Task 3), `ComplianceScadenzeService` (Task 4/5).

- [ ] **Step 1: Scrivere il test che fallisce**

Crea `backend/tests/unit/test_modules/test_affitti_brevi/test_compliance_scheduler.py`:

```python
"""
Test unitari per ComplianceScheduler — verificano solo che lo start/stop
non blocchi e non sollevi eccezioni (l'esecuzione multi-tenant reale è
testata in test_compliance_scadenze_service.py). Nessuna chiamata di rete/DB
reale qui: get_active_tenant_schemas è mockata.
"""
from unittest.mock import patch

from affitti_brevi.services.compliance_scheduler import ComplianceScheduler


def test_start_non_blocca_e_marca_is_running():
    scheduler = ComplianceScheduler(interval_hours=1)
    with patch("affitti_brevi.services.compliance_scheduler.get_active_tenant_schemas", return_value=[]):
        scheduler.start()
        try:
            assert scheduler.is_running is True
        finally:
            scheduler.stop()
    assert scheduler.is_running is False


def test_start_due_volte_non_solleva():
    scheduler = ComplianceScheduler(interval_hours=1)
    with patch("affitti_brevi.services.compliance_scheduler.get_active_tenant_schemas", return_value=[]):
        scheduler.start()
        try:
            scheduler.start()  # no-op, solo un warning loggato
            assert scheduler.is_running is True
        finally:
            scheduler.stop()
```

- [ ] **Step 2: Eseguire e verificare che falliscano**

```bash
cd backend
pytest tests/unit/test_modules/test_affitti_brevi/test_compliance_scheduler.py -v
```
Atteso: `ModuleNotFoundError: No module named 'affitti_brevi.services.compliance_scheduler'`.

- [ ] **Step 3: Implementare `compliance_scheduler.py`**

```python
"""
Compliance Scheduler Service

Scheduler in background (APScheduler) che ogni ora scandisce i Soggiorno
con check-in nelle prossime 48 ore, per ogni tenant con affitti_brevi
abilitato, e genera le scadenze di compliance (Polizia, tassa di
soggiorno) tramite ComplianceScadenzeService. Vedi docs/superpowers/specs/
2026-09-28-affitti-brevi-motore-scadenze-compliance-design.md.

Stesso pattern bound-Connection di sync_scheduler.py: un Session legato
all'engine restituisce la connessione al pool a ogni commit, e la query
successiva potrebbe capitare su una connessione diversa che non ha più
il search_path impostato.
"""
from datetime import date, timedelta
import logging

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.database import engine
from .tenant_scan import get_active_tenant_schemas
from .compliance_scadenze_service import ComplianceScadenzeService

logger = logging.getLogger(__name__)


def _scan_tenant(tenant_schema: str) -> dict:
    """Genera le scadenze di compliance dovute per un tenant."""
    if not tenant_schema.replace('_', '').replace('-', '').isalnum():
        logger.error("Invalid tenant schema, skipping compliance scan: %s", tenant_schema)
        return {'soggiorni_esaminati': 0, 'comunicazioni_create': 0, 'errori': 1}

    connection = engine.connect()
    try:
        connection.execute(text(f"SET search_path TO {tenant_schema}, public"))
        connection.commit()

        db = Session(bind=connection)
        try:
            from affitti_brevi.models import Soggiorno

            oggi = date.today()
            limite = oggi + timedelta(days=2)
            soggiorni = db.query(Soggiorno).filter(
                Soggiorno.valido == True,
                Soggiorno.data_checkin >= oggi,
                Soggiorno.data_checkin <= limite,
            ).all()

            service = ComplianceScadenzeService(db)
            create = 0
            errori = 0
            for soggiorno in soggiorni:
                try:
                    if service.genera_scadenza_polizia(soggiorno) is not None:
                        create += 1
                    if service.genera_scadenza_tassa(soggiorno) is not None:
                        create += 1
                except Exception as exc:
                    errori += 1
                    logger.error(
                        "Compliance scan failed for soggiorno %s (tenant %s): %s",
                        soggiorno.id, tenant_schema, exc, exc_info=True,
                    )
            return {
                'soggiorni_esaminati': len(soggiorni),
                'comunicazioni_create': create,
                'errori': errori,
            }
        finally:
            db.close()
    except Exception as exc:
        logger.error("Compliance scan failed for tenant %s: %s", tenant_schema, exc, exc_info=True)
        return {'soggiorni_esaminati': 0, 'comunicazioni_create': 0, 'errori': 1}
    finally:
        connection.close()


class ComplianceScheduler:
    """Scheduler in background per la generazione delle scadenze di compliance."""

    def __init__(self, interval_hours: int = 1):
        self.scheduler = BackgroundScheduler()
        self.interval_hours = interval_hours
        self.is_running = False

    def scan_job(self):
        logger.info("Starting scheduled compliance scan job")
        totals = {'soggiorni_esaminati': 0, 'comunicazioni_create': 0, 'errori': 0}
        for tenant_schema in get_active_tenant_schemas("affitti_brevi"):
            stats = _scan_tenant(tenant_schema)
            for key in totals:
                totals[key] += stats.get(key, 0)
        logger.info(
            "Compliance scan completed: %s soggiorni esaminati, %s comunicazioni create, %s errori",
            totals['soggiorni_esaminati'], totals['comunicazioni_create'], totals['errori'],
        )

    def start(self):
        if self.is_running:
            logger.warning("Compliance scheduler already running")
            return
        try:
            self.scheduler.add_job(
                func=self.scan_job,
                trigger=IntervalTrigger(hours=self.interval_hours),
                id='compliance_scan_job',
                name='Compliance Scadenze Scan',
                replace_existing=True,
                max_instances=1,
                coalesce=True,
            )
            self.scheduler.start()
            self.is_running = True
            logger.info(f"Compliance scheduler started (interval: {self.interval_hours} hours)")

            # Stesso motivo di sync_scheduler.py: job iniziale schedulato come
            # one-off sul thread di background, non eseguito sincrono qui —
            # questo metodo è chiamato da register_module(app), che gira a
            # import-time di app.main (anche per la test suite).
            self.scheduler.add_job(
                func=self.scan_job,
                id='compliance_scan_job_initial',
                name='Compliance Scadenze Scan (initial)',
                replace_existing=True,
            )
        except Exception as exc:
            logger.error(f"Failed to start compliance scheduler: {exc}", exc_info=True)
            raise

    def stop(self):
        if not self.is_running:
            logger.warning("Compliance scheduler not running")
            return
        self.scheduler.shutdown(wait=True)
        self.is_running = False
        logger.info("Compliance scheduler stopped")


_scheduler_instance = None


def get_compliance_scheduler(interval_hours: int = 1) -> ComplianceScheduler:
    global _scheduler_instance
    if _scheduler_instance is None:
        _scheduler_instance = ComplianceScheduler(interval_hours)
    return _scheduler_instance
```

- [ ] **Step 4: Eseguire e verificare che passino**

```bash
cd backend
pytest tests/unit/test_modules/test_affitti_brevi/test_compliance_scheduler.py -v
```
Atteso: 2 test PASS.

- [ ] **Step 4bis: Test di integrazione per `_scan_tenant` (filtro `valido`)**

Il filtro "un `Soggiorno` con `valido=False` (prenotazione in conflitto) non genera scadenze" — requisito esplicito della spec, §5 — vive nella query di `_scan_tenant`, non nel servizio (`ComplianceScadenzeService` non conosce `valido`, riceve solo il `Soggiorno` che il chiamante gli passa). Va quindi testato qui, con dati reali, non mockando `get_active_tenant_schemas`.

Crea `backend/tests/integration/test_modules/test_affitti_brevi/test_compliance_scan_tenant.py`:

```python
"""
Test di integrazione per compliance_scheduler._scan_tenant — verifica il
filtro valido=True/data_checkin sulla query, che ComplianceScadenzeService
da solo non applica (riceve solo il Soggiorno che il chiamante gli passa).
"""
from datetime import date, timedelta

import pytest
from sqlalchemy import text

from affitti_brevi.models import Comunicazione, Prenotazione, Soggiorno
from affitti_brevi.services.compliance_scheduler import _scan_tenant
from immobili.models import UnitaImmobiliare

TENANT = "tenant_qa_test"


@pytest.fixture
def pg_session():
    from app.core.database import engine
    from sqlalchemy.orm import Session as SASession

    connection = engine.connect()
    connection.execute(text(f"SET search_path TO {TENANT}, public"))
    connection.commit()
    session = SASession(bind=connection)
    try:
        yield session
    finally:
        session.close()
        connection.close()


def _crea_soggiorno(pg_session, codice, valido=True):
    unita = UnitaImmobiliare(codice=codice, tipo="Appartamento", indirizzo="Via Test 1", citta="Testville")
    pg_session.add(unita)
    pg_session.flush()

    prenotazione = Prenotazione(
        unita_immobiliare_id=unita.id,
        codice_prenotazione=f"{codice}-PREN",
        data_checkin=date.today(),
        data_checkout=date.today() + timedelta(days=2),
    )
    pg_session.add(prenotazione)
    pg_session.flush()

    soggiorno = Soggiorno(
        prenotazione_id=prenotazione.id,
        unita_immobiliare_id=unita.id,
        data_checkin=date.today(),
        data_checkout=date.today() + timedelta(days=2),
        valido=valido,
    )
    pg_session.add(soggiorno)
    pg_session.commit()
    return unita, prenotazione, soggiorno


def test_scan_tenant_ignora_soggiorni_non_validi(pg_session):
    unita_ok, pren_ok, soggiorno_ok = _crea_soggiorno(pg_session, "TEST-SCAN-OK")
    unita_ko, pren_ko, soggiorno_ko = _crea_soggiorno(pg_session, "TEST-SCAN-KO", valido=False)

    try:
        stats = _scan_tenant(TENANT)

        assert stats["errori"] == 0
        comunicazioni_ok = pg_session.query(Comunicazione).filter_by(soggiorno_id=soggiorno_ok.id).count()
        comunicazioni_ko = pg_session.query(Comunicazione).filter_by(soggiorno_id=soggiorno_ko.id).count()

        assert comunicazioni_ok == 2  # Polizia + tassa
        assert comunicazioni_ko == 0
    finally:
        for unita, prenotazione, soggiorno in [(unita_ok, pren_ok, soggiorno_ok), (unita_ko, pren_ko, soggiorno_ko)]:
            pg_session.query(Comunicazione).filter_by(soggiorno_id=soggiorno.id).delete()
            pg_session.query(Soggiorno).filter_by(id=soggiorno.id).delete()
            pg_session.query(Prenotazione).filter_by(id=prenotazione.id).delete()
            pg_session.query(UnitaImmobiliare).filter_by(id=unita.id).delete()
        pg_session.commit()
```

Esegui e verifica che passi (dopo aver implementato `_scan_tenant` allo Step 3):
```bash
cd backend
pytest tests/integration/test_modules/test_affitti_brevi/test_compliance_scan_tenant.py -v
```

- [ ] **Step 5: Avviare lo scheduler da `register_module`**

In `backend/modules/affitti_brevi/__init__.py`, dopo il blocco che avvia `SyncScheduler` (fine della funzione `register_module`), aggiungi:

```python
    # Avvia lo scheduler di generazione scadenze compliance (Polizia, tassa
    # di soggiorno). Stesso motivo/pattern del blocco sopra.
    try:
        from .services.compliance_scheduler import get_compliance_scheduler
        compliance_scheduler = get_compliance_scheduler()
        if not compliance_scheduler.is_running:
            compliance_scheduler.start()
            print("[Affitti Brevi] Scheduler scadenze compliance avviato")
    except Exception as exc:
        logger.error("[Affitti Brevi] Impossibile avviare lo scheduler scadenze compliance: %s", exc, exc_info=True)
```

- [ ] **Step 6: Verificare l'avvio reale, non bloccante**

```bash
cd backend
time python -c "import app.main"
```
Atteso: completa in pochi secondi (nessun blocco sincrono), nessuna eccezione. Poi:
```bash
grep -c "Scheduler scadenze compliance avviato" <(python -c "import app.main" 2>&1)
```
Atteso: `1`.

- [ ] **Step 7: Commit**

```bash
git add backend/modules/affitti_brevi/services/compliance_scheduler.py \
        backend/modules/affitti_brevi/__init__.py \
        backend/tests/unit/test_modules/test_affitti_brevi/test_compliance_scheduler.py \
        backend/tests/integration/test_modules/test_affitti_brevi/test_compliance_scan_tenant.py
git commit -m "feat(affitti_brevi): start hourly compliance deadline scan scheduler"
```

---

### Task 7: Route e schema `Comunicazioni`

**Files:**
- Create: `backend/modules/affitti_brevi/schemas/comunicazione.py`
- Modify: `backend/modules/affitti_brevi/schemas/__init__.py`
- Create: `backend/modules/affitti_brevi/routes/comunicazioni.py`
- Modify: `backend/modules/affitti_brevi/routes/__init__.py`
- Modify: `backend/modules/affitti_brevi/__init__.py` (`register_module`)
- Test: `backend/tests/integration/test_modules/test_affitti_brevi/test_comunicazioni_routes.py`

**Interfaces:**
- Produce: `GET /api/v1/affitti-brevi/comunicazioni/{id}`, `POST /api/v1/affitti-brevi/comunicazioni/{id}/segna-completata`
- Consuma: `ComplianceScadenzeService.completa_comunicazione` (Task 5).

- [ ] **Step 1: Scrivere il test che fallisce**

Crea `backend/tests/integration/test_modules/test_affitti_brevi/test_comunicazioni_routes.py`:

```python
"""
Test di integrazione per le route /comunicazioni — vedi
test_compliance_scadenze_service.py per i test della logica di dominio
sottostante; qui si verifica solo il livello HTTP/route.
"""
from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from affitti_brevi.models import Comunicazione, Prenotazione, Soggiorno
from affitti_brevi.services.compliance_scadenze_service import ComplianceScadenzeService
from affitti_brevi.routes.comunicazioni import router as comunicazioni_router
from immobili.models import UnitaImmobiliare
from app.core.database import get_db
from fastapi import FastAPI

TENANT = "tenant_qa_test"


@pytest.fixture
def pg_session():
    from app.core.database import engine
    from sqlalchemy.orm import Session as SASession

    connection = engine.connect()
    connection.execute(text(f"SET search_path TO {TENANT}, public"))
    connection.commit()
    session = SASession(bind=connection)
    try:
        yield session
    finally:
        session.close()
        connection.close()


@pytest.fixture
def client(pg_session):
    app = FastAPI()
    app.include_router(comunicazioni_router, prefix="/api/v1/affitti-brevi")
    app.dependency_overrides[get_db] = lambda: pg_session
    return TestClient(app)


@pytest.fixture
def comunicazione(pg_session):
    unita = UnitaImmobiliare(codice="TEST-ROUTE-001", tipo="Appartamento", indirizzo="Via Test 1", citta="Testville")
    pg_session.add(unita)
    pg_session.flush()

    prenotazione = Prenotazione(
        unita_immobiliare_id=unita.id,
        codice_prenotazione="TEST-ROUTE-PREN-001",
        data_checkin=date.today(),
        data_checkout=date.today() + timedelta(days=2),
    )
    pg_session.add(prenotazione)
    pg_session.flush()

    soggiorno = Soggiorno(
        prenotazione_id=prenotazione.id,
        unita_immobiliare_id=unita.id,
        data_checkin=date.today(),
        data_checkout=date.today() + timedelta(days=2),
    )
    pg_session.add(soggiorno)
    pg_session.commit()

    c = ComplianceScadenzeService(pg_session).genera_scadenza_polizia(soggiorno)

    yield c

    pg_session.query(Comunicazione).filter_by(soggiorno_id=soggiorno.id).delete()
    pg_session.query(Soggiorno).filter_by(id=soggiorno.id).delete()
    pg_session.query(Prenotazione).filter_by(id=prenotazione.id).delete()
    pg_session.query(UnitaImmobiliare).filter_by(id=unita.id).delete()
    pg_session.commit()


def test_get_comunicazione(client, comunicazione):
    response = client.get(f"/api/v1/affitti-brevi/comunicazioni/{comunicazione.id}")
    assert response.status_code == 200
    assert response.json()["tipo"] == "POLIZIA"


def test_get_comunicazione_404(client):
    response = client.get("/api/v1/affitti-brevi/comunicazioni/999999")
    assert response.status_code == 404


def test_segna_completata(client, comunicazione):
    response = client.post(
        f"/api/v1/affitti-brevi/comunicazioni/{comunicazione.id}/segna-completata",
        json={"note": "Inviato a mano allo sportello"},
    )
    assert response.status_code == 200
    assert response.json()["stato"] == "INVIATA"
```

- [ ] **Step 2: Eseguire e verificare che falliscano**

```bash
cd backend
pytest tests/integration/test_modules/test_affitti_brevi/test_comunicazioni_routes.py -v
```
Atteso: `ModuleNotFoundError: No module named 'affitti_brevi.routes.comunicazioni'`.

- [ ] **Step 3: Creare lo schema**

Crea `backend/modules/affitti_brevi/schemas/comunicazione.py`:

```python
"""
Comunicazione Schemas
"""
from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime


class ComunicazioneResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    soggiorno_id: Optional[int] = None
    unita_immobiliare_id: Optional[int] = None
    tipo: str
    stato: str
    data_scadenza: datetime
    data_invio: Optional[datetime] = None
    scadenza_id: Optional[int] = None
    note: Optional[str] = None


class SegnaCompletataRequest(BaseModel):
    note: Optional[str] = None
```

In `backend/modules/affitti_brevi/schemas/__init__.py`, aggiungi:

```python
# Comunicazioni (Compliance communications)
from .comunicazione import (
    ComunicazioneResponse,
    SegnaCompletataRequest,
)
```

e aggiungi alla lista `__all__`:
```python
    # Comunicazioni
    "ComunicazioneResponse",
    "SegnaCompletataRequest",
```

- [ ] **Step 4: Creare la route**

Crea `backend/modules/affitti_brevi/routes/comunicazioni.py`:

```python
"""
Comunicazioni Routes

API per il dettaglio e il completamento manuale delle comunicazioni di
compliance (Polizia, tassa di soggiorno) generate da
ComplianceScadenzeService. L'invio automatico reale (Alloggiati Web) è
compito del sotto-progetto C — qui il completamento è sempre manuale.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from ..models import Comunicazione
from ..schemas.comunicazione import ComunicazioneResponse, SegnaCompletataRequest
from ..services.compliance_scadenze_service import ComplianceScadenzeService

router = APIRouter(prefix="/comunicazioni", tags=["Comunicazioni"])


@router.get("/{comunicazione_id}", response_model=ComunicazioneResponse)
def get_comunicazione(comunicazione_id: int, db: Session = Depends(get_db)):
    """Dettaglio di una comunicazione di compliance."""
    comunicazione = db.query(Comunicazione).filter(Comunicazione.id == comunicazione_id).first()
    if not comunicazione:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Comunicazione con ID {comunicazione_id} non trovata"
        )
    return comunicazione


@router.post("/{comunicazione_id}/segna-completata", response_model=ComunicazioneResponse)
def segna_completata(
    comunicazione_id: int,
    payload: SegnaCompletataRequest,
    db: Session = Depends(get_db)
):
    """Marca la comunicazione come inviata manualmente e completa la
    scadenza core collegata."""
    service = ComplianceScadenzeService(db)
    try:
        return service.completa_comunicazione(comunicazione_id, note=payload.note)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
```

- [ ] **Step 5: Registrare la route in `register_module`**

In `backend/modules/affitti_brevi/__init__.py`, nella funzione `register_module`:
1. Aggiungi `comunicazioni` alla tupla di import:
```python
    from .routes import (
        canali,
        calendari,
        calendario_unificato,
        prenotazioni,
        soggiorni,
        sync,
        comunicazioni,
    )
```
2. Aggiungi la registrazione:
```python
    app.include_router(comunicazioni.router, prefix=prefix, tags=tags)
```
3. Aggiorna la stampa di log:
```python
    print("[Affitti Brevi] Routes: canali, calendari, calendario-unificato, prenotazioni, soggiorni, sync, comunicazioni")
```

- [ ] **Step 5bis: Aggiungere `comunicazioni` a `routes/__init__.py`**

Il modulo esiste ora: in `backend/modules/affitti_brevi/routes/__init__.py`, aggiungi `comunicazioni` alla tupla `from . import (...)` e alla lista `__all__` (il Task 1 li aveva deliberatamente omessi per non rompere l'import del pacchetto prima che questo task creasse il file — vedi la NOTE lasciata in quel file). Il risultato finale:

```python
from . import (
    canali,
    calendari,
    calendario_unificato,
    prenotazioni,
    soggiorni,
    sync,
    comunicazioni,
)

# NOTE: router "tasse" ancora assente — la ricostruzione del calcolo/
# dichiarazione tassa di soggiorno contro i modelli attuali (TassaSoggiorno)
# è compito del sotto-progetto B (vedi docs/superpowers/specs/
# 2026-09-28-affitti-brevi-motore-scadenze-compliance-design.md).

__all__ = [
    "canali",
    "calendari",
    "calendario_unificato",
    "prenotazioni",
    "soggiorni",
    "sync",
    "comunicazioni",
]
```

- [ ] **Step 6: Eseguire e verificare che passino**

```bash
cd backend
pytest tests/integration/test_modules/test_affitti_brevi/test_comunicazioni_routes.py -v
```
Atteso: 3 test PASS.

- [ ] **Step 7: Rieseguire l'intera suite del modulo**

```bash
cd backend
./run_tests.sh module affitti_brevi
```
Atteso: tutti i test passano (compresi quelli dei task precedenti e quelli pre-esistenti).

- [ ] **Step 8: Commit**

```bash
git add backend/modules/affitti_brevi/schemas/comunicazione.py \
        backend/modules/affitti_brevi/schemas/__init__.py \
        backend/modules/affitti_brevi/routes/comunicazioni.py \
        backend/modules/affitti_brevi/routes/__init__.py \
        backend/modules/affitti_brevi/__init__.py \
        backend/tests/integration/test_modules/test_affitti_brevi/test_comunicazioni_routes.py
git commit -m "feat(affitti_brevi): expose Comunicazione detail and manual completion routes"
```

---

### Task 8: Frontend — rimuovere il cluster dead Scadenze/scadenzeAPI

**Files:**
- Delete: `frontend/src/modules/affitti_brevi/components/Scadenze/` (intera directory: `ComunicazioniPoliziaList.jsx`, `ScadenzaDetail.jsx`, `ScadenzaBadge.jsx`, `ScadenzaBadge.css`, `ScadenzeList.jsx`, `Scadenze.css`, `index.js`)
- Modify: `frontend/src/modules/affitti_brevi/index.js`
- Modify: `frontend/src/modules/affitti_brevi/services/affittiBreviAPI.js`

**Interfaces:**
- Nessuna prodotta: questo task rimuove codice che chiama endpoint (`/affitti-brevi/scadenze/*`, `/affitti-brevi/scadenze/comunicazioni-polizia/*`) mai esistiti sul backend attuale (verificato via grep sui router registrati).

- [ ] **Step 1: Verificare che nessun altro file (oltre a quelli in rimozione) importi il cluster**

```bash
cd frontend/src
grep -rln "components/Scadenze\|scadenzeAPI" modules/affitti_brevi --include=*.jsx --include=*.js
```
Atteso: solo `modules/affitti_brevi/components/Dashboard/ScadenzeWidget.jsx` (sarà riscritto al Task 9), `modules/affitti_brevi/index.js` e `modules/affitti_brevi/services/affittiBreviAPI.js` (questo task), oltre ai file della cartella stessa in rimozione.

- [ ] **Step 2: Eliminare la directory**

```bash
rm -rf frontend/src/modules/affitti_brevi/components/Scadenze
```

- [ ] **Step 3: Aggiornare `index.js`**

In `frontend/src/modules/affitti_brevi/index.js`, rimuovi la riga:
```javascript
// Scadenze e Comunicazioni Polizia (Phase 5)
export { ScadenzeList, ScadenzaDetail, ScadenzaBadge, ComunicazioniPoliziaList } from './components/Scadenze';
```

- [ ] **Step 4: Rimuovere `scadenzeAPI` da `affittiBreviAPI.js`**

In `frontend/src/modules/affitti_brevi/services/affittiBreviAPI.js`, rimuovi l'intero blocco (dal commento `// Scadenze API` fino alla chiusura dell'oggetto, righe 102-140 del file attuale):
```javascript
// Scadenze API
export const scadenzeAPI = {
  ...
};
```
E nell'export di default in fondo al file, rimuovi la riga `scadenzeAPI,`:
```javascript
export default {
  calendariAPI,
  prenotazioniAPI,
  ospitiAPI,
  tasseAPI,
};
```

- [ ] **Step 5: Verificare che il build frontend non si rompa**

```bash
cd frontend
npm run build
```
Atteso: build completata senza errori (nessun import rotto — verrà rotto temporaneamente da `ScadenzeWidget.jsx`, sistemato al Task 9: se il build fallisce qui per quel file, è atteso e verrà risolto subito dopo).

- [ ] **Step 6: Commit**

```bash
git add frontend/src/modules/affitti_brevi/index.js \
        frontend/src/modules/affitti_brevi/services/affittiBreviAPI.js
git add -u frontend/src/modules/affitti_brevi/components/Scadenze
git commit -m "chore(affitti_brevi): remove dead pre-refactor Scadenze frontend cluster"
```

---

### Task 9: Frontend — ricostruire `ScadenzeWidget.jsx` sul core `scadenzeAPI`

**Files:**
- Modify: `frontend/src/modules/affitti_brevi/components/Dashboard/ScadenzeWidget.jsx`

**Interfaces:**
- Consuma: `scadenzeAPI.list({ modulo })` da `frontend/src/services/api.js` (client core, NON quello locale del modulo appena rimosso).

- [ ] **Step 1: Riscrivere il widget**

Sostituisci il contenuto di `frontend/src/modules/affitti_brevi/components/Dashboard/ScadenzeWidget.jsx`:

```jsx
import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { scadenzeAPI } from '../../../../services/api';
import './ScadenzeWidget.css';

/**
 * ScadenzeWidget - Dashboard widget for upcoming affitti_brevi deadlines
 *
 * Legge le scadenze reali dal motore core (core_scadenze, filtrate per
 * modulo=affitti_brevi) — vedi docs/superpowers/specs/2026-09-28-affitti-
 * brevi-motore-scadenze-compliance-design.md. Sostituisce la versione
 * precedente, che chiamava endpoint /affitti-brevi/scadenze/* mai esistiti.
 */
function ScadenzeWidget() {
  const [scadenze, setScadenze] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadScadenze();
  }, []);

  const loadScadenze = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await scadenzeAPI.list({ modulo: 'affitti_brevi', limit: 100 });
      setScadenze(response.data);
    } catch (err) {
      console.error('Error loading scadenze:', err);
      setError('Errore nel caricamento delle scadenze');
    } finally {
      setLoading(false);
    }
  };

  const attive = scadenze.filter((s) => s.stato !== 'COMPLETATA' && s.stato !== 'CANCELLATA');
  const scadute = attive.filter((s) => s.is_scaduta);
  const inScadenza = attive.filter((s) => !s.is_scaduta);
  const completate = scadenze.filter((s) => s.stato === 'COMPLETATA');

  const upcoming = [...scadute, ...inScadenza]
    .sort((a, b) => new Date(a.data_scadenza) - new Date(b.data_scadenza))
    .slice(0, 5);

  const formatDate = (dateString) => new Date(dateString).toLocaleDateString('it-IT');

  if (loading) {
    return (
      <div className="scadenze-widget">
        <div className="widget-loading">Caricamento...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="scadenze-widget">
        <div className="widget-error">{error}</div>
      </div>
    );
  }

  return (
    <div className="scadenze-widget">
      <div className="widget-header">
        <h3>⏰ Scadenze Affitti Brevi</h3>
      </div>

      <div className="stats-summary">
        <div className="stat-item stat-danger">
          <div className="stat-value">{scadute.length}</div>
          <div className="stat-label">Scadute</div>
        </div>
        <div className="stat-item stat-warning">
          <div className="stat-value">{inScadenza.length}</div>
          <div className="stat-label">In Scadenza</div>
        </div>
        <div className="stat-item stat-success">
          <div className="stat-value">{completate.length}</div>
          <div className="stat-label">Completate</div>
        </div>
      </div>

      <div className="scadenze-list">
        <h4>Prossime Scadenze</h4>
        {upcoming.length === 0 ? (
          <div className="no-scadenze">
            <p>Nessuna scadenza urgente</p>
          </div>
        ) : (
          <ul>
            {upcoming.map((scadenza) => (
              <li key={scadenza.id} className="scadenza-item">
                <div className="scadenza-header">
                  <span className={`badge ${scadenza.is_scaduta ? 'badge-danger' : 'badge-warning'}`}>
                    {scadenza.is_scaduta ? 'Scaduta' : 'In Scadenza'}
                  </span>
                </div>
                <div className="scadenza-title">{scadenza.titolo}</div>
                <div className="scadenza-date">{formatDate(scadenza.data_scadenza)}</div>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}

export default ScadenzeWidget;
```

(Rimosso il link "Vedi tutto"/"Gestisci Scadenze" verso `/affitti-brevi/scadenze`: quella pagina non esiste — il pannello notifiche core, già montato in `TopBar`, resta il punto d'accesso principale a queste scadenze.)

- [ ] **Step 2: Verificare manualmente**

```bash
cd frontend
npm run build
npm run preview -- --port 3000
```
Apri il browser sulla dashboard del tenant `tenant_qa_test`, verifica che il widget "Scadenze Affitti Brevi" carichi senza errori (mostrerà 0 scadenze finché il Task 6 non ha generato dati reali, oppure i dati creati dai test se non ripuliti — comportamento atteso).

- [ ] **Step 3: Commit**

```bash
git add frontend/src/modules/affitti_brevi/components/Dashboard/ScadenzeWidget.jsx
git commit -m "fix(affitti_brevi): rebuild dashboard ScadenzeWidget against the core Scadenza API"
```

---

### Task 10: Frontend — pagina `ComunicazioneDetail` e route

**Files:**
- Create: `frontend/src/modules/affitti_brevi/components/Comunicazioni/ComunicazioneDetail.jsx`
- Create: `frontend/src/modules/affitti_brevi/components/Comunicazioni/ComunicazioneDetail.css`
- Modify: `frontend/src/modules/affitti_brevi/services/affittiBreviAPI.js`
- Modify: `frontend/src/modules/affitti_brevi/index.js`
- Modify: `frontend/src/modules/affitti_brevi/manifest.js`

**Interfaces:**
- Produce: route `/affitti-brevi/comunicazioni/:id` → componente `ComunicazioneDetail`.
- Consuma: `GET /api/v1/affitti-brevi/comunicazioni/{id}`, `POST /api/v1/affitti-brevi/comunicazioni/{id}/segna-completata` (Task 7).

- [ ] **Step 1: Aggiungere `comunicazioniAPI` a `affittiBreviAPI.js`**

Aggiungi in `frontend/src/modules/affitti_brevi/services/affittiBreviAPI.js`, dopo il blocco `ospitiAPI`:

```javascript
// Comunicazioni Compliance API (Polizia, tassa di soggiorno)
export const comunicazioniAPI = {
  getById: (id) => api.get(`/comunicazioni/${id}`),
  segnaCompletata: (id, note = null) => api.post(`/comunicazioni/${id}/segna-completata`, { note }),
};
```

E aggiungi `comunicazioniAPI,` all'export di default.

- [ ] **Step 2: Creare il componente**

Crea `frontend/src/modules/affitti_brevi/components/Comunicazioni/ComunicazioneDetail.jsx`:

```jsx
import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { comunicazioniAPI } from '../../services/affittiBreviAPI';
import './ComunicazioneDetail.css';

const TIPO_LABELS = {
  POLIZIA: 'Comunicazione Polizia',
  ISTAT: 'Report ISTAT',
  TASSA_DICHIARAZIONE: 'Tassa di Soggiorno',
  ALTRO: 'Altro',
};

function ComunicazioneDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [comunicazione, setComunicazione] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [note, setNote] = useState('');
  const [completing, setCompleting] = useState(false);

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  const load = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await comunicazioniAPI.getById(id);
      setComunicazione(response.data);
    } catch (err) {
      setError('Comunicazione non trovata o errore di caricamento');
    } finally {
      setLoading(false);
    }
  };

  const handleCompleta = async () => {
    if (!window.confirm('Segnare questa comunicazione come completata?')) return;
    try {
      setCompleting(true);
      await comunicazioniAPI.segnaCompletata(id, note || null);
      await load();
    } catch (err) {
      alert('Errore nel completamento della comunicazione');
    } finally {
      setCompleting(false);
    }
  };

  if (loading) return <div className="comunicazione-detail">Caricamento...</div>;
  if (error) return <div className="comunicazione-detail error">{error}</div>;
  if (!comunicazione) return null;

  const completata = comunicazione.stato !== 'DA_PREPARARE' && comunicazione.stato !== 'PRONTA'
    && comunicazione.stato !== 'ERRORE';

  return (
    <div className="comunicazione-detail">
      <button className="btn btn-secondary" onClick={() => navigate(-1)}>&larr; Indietro</button>

      <h2>{TIPO_LABELS[comunicazione.tipo] || comunicazione.tipo}</h2>

      <div className="detail-grid">
        <div className="detail-row">
          <span className="detail-label">Stato:</span>
          <span className={`badge badge-${completata ? 'success' : 'warning'}`}>{comunicazione.stato}</span>
        </div>
        <div className="detail-row">
          <span className="detail-label">Scadenza:</span>
          <span>{new Date(comunicazione.data_scadenza).toLocaleString('it-IT')}</span>
        </div>
        {comunicazione.data_invio && (
          <div className="detail-row">
            <span className="detail-label">Inviata il:</span>
            <span>{new Date(comunicazione.data_invio).toLocaleString('it-IT')}</span>
          </div>
        )}
      </div>

      {!completata && (
        <div className="completion-section">
          <h4>Completa manualmente</h4>
          <textarea
            value={note}
            onChange={(e) => setNote(e.target.value)}
            placeholder="Note (opzionale)"
            rows={3}
          />
          <button className="btn btn-success" disabled={completing} onClick={handleCompleta}>
            {completing ? 'Completamento...' : '✓ Segna come completata'}
          </button>
        </div>
      )}
    </div>
  );
}

export default ComunicazioneDetail;
```

Crea `frontend/src/modules/affitti_brevi/components/Comunicazioni/ComunicazioneDetail.css`:

```css
.comunicazione-detail {
  max-width: 640px;
  margin: 0 auto;
  padding: 24px;
}

.comunicazione-detail.error {
  color: #b91c1c;
}

.detail-grid {
  margin-top: 16px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.detail-row {
  display: flex;
  gap: 8px;
  align-items: center;
}

.detail-label {
  font-weight: 600;
  min-width: 120px;
}

.completion-section {
  margin-top: 24px;
  padding-top: 16px;
  border-top: 1px solid #e5e7eb;
}

.completion-section textarea {
  width: 100%;
  margin: 8px 0;
}
```

- [ ] **Step 3: Esportare il componente da `index.js`**

In `frontend/src/modules/affitti_brevi/index.js`, aggiungi:

```javascript
// Comunicazioni Compliance
export { default as ComunicazioneDetail } from './components/Comunicazioni/ComunicazioneDetail';
```

- [ ] **Step 4: Aggiungere la route in `manifest.js`**

In `frontend/src/modules/affitti_brevi/manifest.js`, nell'array `routes`, aggiungi (route con parametro, non in menu — si accede solo dal link di risoluzione della scadenza, non c'è una entry in `menuItems`):

```javascript
    {
      path: '/affitti-brevi/comunicazioni/:id',
      component: 'ComunicazioneDetail',
      label: 'Comunicazione',
      hideFromMenu: true,
    },
```

- [ ] **Step 5: Verificare manualmente**

```bash
cd frontend
npm run build
npm run preview -- --port 3000
```
Naviga manualmente a `/affitti-brevi/comunicazioni/<id di una comunicazione reale creata dai test>` e verifica che la pagina carichi, mostri stato/scadenza, e che il pulsante "Segna come completata" funzioni (ricarica lo stato ad `INVIATA`).

- [ ] **Step 6: Commit**

```bash
git add frontend/src/modules/affitti_brevi/components/Comunicazioni \
        frontend/src/modules/affitti_brevi/services/affittiBreviAPI.js \
        frontend/src/modules/affitti_brevi/index.js \
        frontend/src/modules/affitti_brevi/manifest.js
git commit -m "feat(affitti_brevi): add Comunicazione detail page with manual completion"
```

---

### Task 11: Frontend — collegare `ScadenzaResolve.jsx`

**Files:**
- Modify: `frontend/src/pages/ScadenzaResolve.jsx`

**Interfaces:**
- Consuma: nessuna nuova — collega un `modulo`/`entity_type` già usati da `ComplianceScadenzeService` (Task 4) alla route creata al Task 10.

- [ ] **Step 1: Aggiungere il case in `buildTarget`**

In `frontend/src/pages/ScadenzaResolve.jsx`, nella funzione `buildTarget`, dopo il case esistente per `anagrafica_italiana`/`SOGGETTO_ANAGRAFICO`:

```javascript
  if (normalizedModule === 'affitti_brevi' && normalizedType === 'COMUNICAZIONE') {
    return `/affitti-brevi/comunicazioni/${entityId}`;
  }
```

- [ ] **Step 2: Verificare manualmente end-to-end**

```bash
cd frontend
npm run build
npm run preview -- --port 3000
```
1. Assicurati che il job compliance (Task 6) o i test abbiano generato almeno una `Comunicazione`/`Scadenza` reale per `tenant_qa_test`.
2. Fai login, apri il pannello notifiche (icona campanella in `TopBar`).
3. Verifica che la scadenza "Comunicazione Polizia — Soggiorno #..." appaia nel gruppo corretto (Oggi/Domani/Questa Settimana).
4. Clicca il pulsante "Apri" (icona link) sulla notifica.
5. Verifica che la navigazione arrivi a `/affitti-brevi/comunicazioni/<id>` (non alla pagina di fallback "Nessuna pagina di completamento configurata").
6. Clicca "Segna come completata", verifica che la comunicazione passi a `INVIATA`.
7. Riapri il pannello notifiche, verifica che la scadenza sia sparita dalla lista (perché `COMPLETATA`).

- [ ] **Step 3: Commit**

```bash
git add frontend/src/pages/ScadenzaResolve.jsx
git commit -m "feat(affitti_brevi): wire notification resolve link to Comunicazione detail page"
```

---

## Verifica finale

- [ ] `cd backend && ./run_tests.sh module affitti_brevi` — tutti i test passano.
- [ ] `cd backend && ./run_tests.sh` (suite completa) — nessuna regressione in altri moduli.
- [ ] `cd frontend && npm run build` — build pulita.
- [ ] Verifica manuale end-to-end del Task 11 (notifica → risoluzione → completamento → sparizione) ripetuta una volta a mente fresca.
- [ ] Nessun riferimento residuo a `scadenza_generator`, `comunicazione_polizia_service`, `ScadenzaAffittiBrevi`, `AttivitaSchedulata`, `components/Scadenze` nel repo:
  ```bash
  grep -rn "scadenza_generator\|comunicazione_polizia_service\|ScadenzaAffittiBrevi\|AttivitaSchedulata\|components/Scadenze" backend/modules/affitti_brevi frontend/src/modules/affitti_brevi --include=*.py --include=*.jsx --include=*.js | grep -v __pycache__
  ```
  Atteso: nessun risultato.
