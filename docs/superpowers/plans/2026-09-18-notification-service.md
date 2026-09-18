# Servizio Notifiche Core — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a generic core notification service (email + in-app) that any module can call, wire it into the existing scadenzario (which tracks who to notify but never sends anything), and fix a pre-existing tenant-isolation gap discovered while researching this plan.

**Architecture:** New `Notifica` model/table (`core_notifiche`), tenant-scoped like `Scadenza`. New `NotificationService` in `app/core/platform_services/` (direct-import core service per the module-communication architecture decision — no REST needed). New daily APScheduler job that scans `Scadenza` rows and calls `NotificationService.notify()`. New `/api/v1/notifiche` routes and a `NotificationBell` frontend component.

**Tech Stack:** FastAPI, SQLAlchemy, Alembic (multi-schema), APScheduler (`BackgroundScheduler`), pytest, React.

**Spec:**
- `docs/superpowers/specs/2026-09-14-notification-service-design.md`
- `docs/superpowers/specs/2026-09-14-module-communication-architecture-design.md` (confirms this is a core service: direct import, no REST layer)

## Global Constraints

- `NotificationService` lives in `app/core/platform_services/` and is imported directly by any caller — never exposed as an internal REST hop (it's a core platform service, see the architecture spec §3.1).
- `Notifica` is a **tenant-scoped** table: it must be created via an Alembic migration with `target_schema = "tenant"`, and excluded from `create_core_tables()` in `app/main.py` (that function is only for tables meant to live once in `public`). This is the same fix being applied to the pre-existing `Scadenza`/`ScadenzaDestinatario`/`ScadenzaLog` tables, which were never actually migrated into tenant schemas (verified against the live DB: `core_scadenze` exists only in `public`, with 0 rows in every environment — no data migration needed, only structural).
- Email sending reuses the existing `NOTIFICHE_SMTP_*` settings in `app/core/config.py` (already present for `gestione_pec`). Do not add a second SMTP config block. Do not import anything from `gestione_pec` — core must never depend on a module (see architecture spec §3.1); duplicate the small SMTP-send helper instead.
- The scadenza reminder job notifies via **email only** (`canali=CanaleNotifica.EMAIL`), not in-app. Reason: `frontend/src/components/Platform/Scadenze/ScadenzaBadge.jsx` + `NotifichePanel.jsx` already show live, richer in-app visibility for scadenze (grouped by urgency, quick actions) by querying `/scadenze/my/scadenze` directly — creating an in-app `Notifica` row for the same event would just duplicate it in a second, separate bell. The generic in-app channel stays available in `NotificationService.notify()` for future modules that have no equivalent live view yet.
- Follow existing test conventions exactly: `db_session` (SQLite, function-scoped, see `tests/fixtures/database.py`) for unit tests, `auth_client`/`admin_client` (see `tests/fixtures/api_client.py`) for integration tests. No new fixtures needed.

---

### Task 1: Fix scadenzario tenant isolation + exclude tenant-only tables from `create_core_tables()`

**Files:**
- Modify: `backend/app/main.py:79-84` (`create_core_tables()`)
- Modify: `backend/alembic/env.py:56` (eager-import block — no functional change needed here, `Scadenza` family is already imported; this task only touches `create_core_tables`)
- Create: `backend/alembic/versions/2026091801_create_core_scadenze_tenant_tables.py`
- Test: `backend/tests/unit/test_core/test_main_create_core_tables.py`

**Interfaces:**
- Produces: `TENANT_ONLY_CORE_TABLES` (a `set[str]` constant in `app/main.py`) — Task 2 adds `"core_notifiche"` to this same set.

- [ ] **Step 1: Write the failing test**

Create `backend/tests/unit/test_core/test_main_create_core_tables.py`:

```python
"""
Verifies that tenant-only core tables (scadenzario, notifiche) are never
created in the public schema by create_core_tables() — they must only
exist per-tenant, via their dedicated Alembic migrations.
"""
from sqlalchemy import create_engine, MetaData
from sqlalchemy.pool import StaticPool

from app.core.database import Base
from app.main import TENANT_ONLY_CORE_TABLES, create_core_tables


def test_tenant_only_tables_excluded_from_public_creation():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    core_metadata = MetaData()
    for table in Base.metadata.tables.values():
        if table.name.startswith("core_") and table.name not in TENANT_ONLY_CORE_TABLES:
            table.to_metadata(core_metadata)
    core_metadata.create_all(bind=engine, checkfirst=True)

    created_names = set(core_metadata.tables.keys())
    assert "core_scadenze" not in created_names
    assert "core_scadenza_destinatari" not in created_names
    assert "core_scadenza_log" not in created_names
    assert "core_users" in created_names  # sanity: real public tables still included


def test_tenant_only_tables_constant_contains_scadenzario():
    assert "core_scadenze" in TENANT_ONLY_CORE_TABLES
    assert "core_scadenza_destinatari" in TENANT_ONLY_CORE_TABLES
    assert "core_scadenza_log" in TENANT_ONLY_CORE_TABLES
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && source venv/bin/activate && pytest tests/unit/test_core/test_main_create_core_tables.py -v`
Expected: FAIL — `ImportError: cannot import name 'TENANT_ONLY_CORE_TABLES' from 'app.main'`

- [ ] **Step 3: Add `TENANT_ONLY_CORE_TABLES` and filter it out in `create_core_tables()`**

In `backend/app/main.py`, replace:

```python
def create_core_tables():
    """
    Create only core tables (prefix core_) in public schema.
    Avoids creating module tables outside tenant install.
    """
    core_metadata = MetaData()
    for table in Base.metadata.tables.values():
        if table.name.startswith("core_"):
            table.to_metadata(core_metadata)
    core_metadata.create_all(bind=engine, checkfirst=True)
```

with:

```python
# Tables prefixed "core_" that are tenant-scoped business data (like any
# module's tables), NOT shared platform data. They must be created only
# inside each tenant schema via a dedicated Alembic migration
# (target_schema="tenant"), never here. create_core_tables() must never
# recreate them in `public` — that was the root cause of a tenant-isolation
# bug where core_scadenze ended up as a single table shared by every
# tenant (see docs/superpowers/plans/2026-09-18-notification-service.md).
TENANT_ONLY_CORE_TABLES = {
    "core_scadenze",
    "core_scadenza_destinatari",
    "core_scadenza_log",
    "core_notifiche",
}


def create_core_tables():
    """
    Create only shared-platform core tables (prefix core_) in public schema.
    Avoids creating module tables, and tenant-only core tables, outside
    tenant install/migration.
    """
    core_metadata = MetaData()
    for table in Base.metadata.tables.values():
        if table.name.startswith("core_") and table.name not in TENANT_ONLY_CORE_TABLES:
            table.to_metadata(core_metadata)
    core_metadata.create_all(bind=engine, checkfirst=True)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && source venv/bin/activate && pytest tests/unit/test_core/test_main_create_core_tables.py -v`
Expected: PASS

- [ ] **Step 5: Write the tenant migration for the scadenzario tables**

Create `backend/alembic/versions/2026091801_create_core_scadenze_tenant_tables.py`:

```python
"""Create core_scadenze/core_scadenza_destinatari/core_scadenza_log inside
every tenant schema.

These tables were previously only ever created in `public` (via
create_core_tables()'s unconditional Base.metadata.create_all()), meaning
every tenant shared a single, non-isolated scadenzario. Verified against
the live database: 0 rows in all three tables in every environment, so
this is a purely structural fix, no data migration needed.

Revision ID: 2026091801
Revises: 2026072301
Create Date: 2026-09-18
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "2026091801"
down_revision = "2026072301"
branch_labels = None
depends_on = None

target_schema = "tenant"


def upgrade() -> None:
    bind = op.get_bind()

    priorita_enum = postgresql.ENUM(
        "BASSA", "MEDIA", "ALTA", name="prioritascadenza", create_type=True
    )
    priorita_enum.create(bind, checkfirst=True)

    stato_enum = postgresql.ENUM(
        "ATTIVA", "SCADUTA", "COMPLETATA", "POSTICIPATA", "CANCELLATA",
        name="statoscadenza", create_type=True
    )
    stato_enum.create(bind, checkfirst=True)

    op.create_table(
        "core_scadenze",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("modulo", sa.String(length=100), nullable=True),
        sa.Column("entity_type", sa.String(length=100), nullable=True),
        sa.Column("entity_id", sa.Integer(), nullable=True),
        sa.Column("titolo", sa.String(length=200), nullable=False),
        sa.Column("descrizione", sa.Text(), nullable=True),
        sa.Column("data_scadenza", sa.Date(), nullable=False),
        sa.Column("priorita", priorita_enum, nullable=False),
        sa.Column("stato", stato_enum, nullable=False),
        # Unqualified "core_users.id" resolves via the tenant migration's
        # active search_path (tenant_schema, public) to public.core_users,
        # which is never replicated per-tenant. Same mechanism already
        # proven by every business module's tenant migration (e.g.
        # affitti_lungo) that references public domain tables.
        sa.ForeignKeyConstraint(["creato_da"], ["core_users.id"], ondelete="CASCADE"),
        sa.Column("creato_da", sa.Integer(), nullable=False),
        sa.Column("creato_il", sa.DateTime(), nullable=False),
        sa.Column("modificato_il", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["completato_da"], ["core_users.id"], ondelete="SET NULL"),
        sa.Column("completato_da", sa.Integer(), nullable=True),
        sa.Column("completato_il", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_core_scadenze_id", "core_scadenze", ["id"])
    op.create_index("ix_core_scadenze_data_scadenza", "core_scadenze", ["data_scadenza"])
    op.create_index("ix_core_scadenze_stato", "core_scadenze", ["stato"])
    op.create_index("idx_core_scadenze_creator", "core_scadenze", ["creato_da"])
    op.create_index("idx_core_scadenze_entity", "core_scadenze", ["modulo", "entity_type", "entity_id"])
    op.create_index("idx_core_scadenze_stato_data", "core_scadenze", ["stato", "data_scadenza"])

    op.create_table(
        "core_scadenza_destinatari",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.ForeignKeyConstraint(["scadenza_id"], ["core_scadenze.id"], ondelete="CASCADE"),
        sa.Column("scadenza_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["core_users.id"], ondelete="CASCADE"),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("notificato", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("notificato_il", sa.DateTime(), nullable=True),
        sa.UniqueConstraint("scadenza_id", "user_id", name="uq_scadenza_user"),
    )
    op.create_index("ix_core_scadenza_destinatari_id", "core_scadenza_destinatari", ["id"])
    op.create_index("idx_core_destinatari_scadenza", "core_scadenza_destinatari", ["scadenza_id"])
    op.create_index("idx_core_destinatari_user", "core_scadenza_destinatari", ["user_id"])
    op.create_index("idx_core_destinatari_notificato", "core_scadenza_destinatari", ["notificato"])

    op.create_table(
        "core_scadenza_log",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.ForeignKeyConstraint(["scadenza_id"], ["core_scadenze.id"], ondelete="CASCADE"),
        sa.Column("scadenza_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["core_users.id"], ondelete="SET NULL"),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("timestamp", sa.DateTime(), nullable=False),
        sa.Column("azione", sa.String(length=50), nullable=False),
        sa.Column("campo_modificato", sa.String(length=100), nullable=True),
        sa.Column("valore_precedente", sa.Text(), nullable=True),
        sa.Column("valore_nuovo", sa.Text(), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
    )
    op.create_index("ix_core_scadenza_log_id", "core_scadenza_log", ["id"])
    op.create_index("ix_core_scadenza_log_timestamp", "core_scadenza_log", ["timestamp"])
    op.create_index("idx_core_log_scadenza", "core_scadenza_log", ["scadenza_id"])
    op.create_index("idx_core_log_azione", "core_scadenza_log", ["azione"])


def downgrade() -> None:
    op.drop_table("core_scadenza_log")
    op.drop_table("core_scadenza_destinatari")
    op.drop_table("core_scadenze")
    bind = op.get_bind()
    postgresql.ENUM(name="statoscadenza").drop(bind, checkfirst=True)
    postgresql.ENUM(name="prioritascadenza").drop(bind, checkfirst=True)
```

- [ ] **Step 6: Apply the migration to every existing tenant schema**

Run: `cd backend && source venv/bin/activate && alembic -x schema=all upgrade head`
Expected: no errors; `2026091801` becomes head for `public` (no-op there, `upgrade()` always runs its DDL regardless of schema in this file — the tenant-only guard is `target_schema = "tenant"` at the top, which `env.py`'s `should_run_migration_for_schema` reads to skip this file entirely when migrating `public`)

Verify: `PGPASSWORD=affitti psql -h localhost -p 5433 -U affitti -d gestione_affitti -c "SELECT table_schema FROM information_schema.tables WHERE table_name='core_scadenze';"`
Expected: rows for `public`, `tenant_principale`, `tenant_produzione`, `tenant_qa_test`

- [ ] **Step 7: Restart the backend and confirm no duplicate/conflicting table errors**

Run: `cd backend && ./start.sh` (start, watch logs for `create_core_tables`-related errors, then stop with Ctrl+C)
Expected: starts cleanly; `create_core_tables()` no longer touches `core_scadenze`/`core_scadenza_destinatari`/`core_scadenza_log`

- [ ] **Step 8: Commit**

```bash
cd backend
git add app/main.py alembic/versions/2026091801_create_core_scadenze_tenant_tables.py tests/unit/test_core/test_main_create_core_tables.py
git commit -m "fix(scadenzario): isolate core_scadenze per tenant, stop sharing one public table"
```

---

### Task 2: `Notifica` model + tenant migration for `core_notifiche`

**Files:**
- Create: `backend/app/core/platform/models/notifica.py`
- Modify: `backend/app/core/platform/models/__init__.py`
- Modify: `backend/app/main.py` (import `Notifica` so it registers on `Base.metadata`)
- Modify: `backend/alembic/env.py` (same eager-import, needed for the migration subprocess)
- Create: `backend/alembic/versions/2026091802_create_core_notifiche_tenant_table.py`
- Test: `backend/tests/unit/test_core/test_notifica_model.py`

**Interfaces:**
- Consumes: `Base` from `app.core.database` (existing).
- Produces: `Notifica` (SQLAlchemy model, table `core_notifiche`), `CanaleNotifica` (`str, enum.Enum`: `IN_APP`, `EMAIL`, `ENTRAMBI`), `StatoEmailNotifica` (`str, enum.Enum`: `NON_RICHIESTA`, `PENDING`, `SENT`, `FAILED`) — Task 3's `NotificationService` and Task 4's schemas import these three names from `app.core.platform.models`.

- [ ] **Step 1: Write the failing test**

Create `backend/tests/unit/test_core/test_notifica_model.py`:

```python
from datetime import datetime

from app.core.platform.models import Notifica, CanaleNotifica, StatoEmailNotifica


def test_notifica_defaults(db_session):
    n = Notifica(
        user_id=1,
        tipo="test.evento",
        titolo="Titolo di prova",
        corpo="Corpo di prova",
    )
    db_session.add(n)
    db_session.commit()
    db_session.refresh(n)

    assert n.id is not None
    assert n.canali == CanaleNotifica.ENTRAMBI.value
    assert n.stato_email == StatoEmailNotifica.NON_RICHIESTA.value
    assert n.letta is False
    assert n.letta_il is None
    assert isinstance(n.creata_il, datetime)


def test_notifica_with_entity_link(db_session):
    n = Notifica(
        user_id=2,
        tipo="scadenza.reminder",
        titolo="Scadenza in avvicinamento",
        corpo="La scadenza X è in scadenza tra 3 giorni",
        entity_type="scadenza",
        entity_id=42,
        link_url="/scadenze/42",
        canali=CanaleNotifica.EMAIL.value,
    )
    db_session.add(n)
    db_session.commit()
    db_session.refresh(n)

    assert n.entity_type == "scadenza"
    assert n.entity_id == 42
    assert n.link_url == "/scadenze/42"
    assert n.canali == CanaleNotifica.EMAIL.value
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && source venv/bin/activate && pytest tests/unit/test_core/test_notifica_model.py -v`
Expected: FAIL — `ModuleNotFoundError` / `ImportError: cannot import name 'Notifica'`

- [ ] **Step 3: Create the model**

Create `backend/app/core/platform/models/notifica.py`:

```python
"""
Notifica Model - Generic Core Notification Service

Platform-level notification (email and/or in-app) for a single recipient.
Any module or core service creates these via
app.core.platform_services.NotificationService — never by instantiating
this class directly outside that service.

Tenant-scoped table (like Scadenza): created only inside each tenant
schema by backend/alembic/versions/2026091802_create_core_notifiche_tenant_table.py,
never by create_core_tables() (see app/main.py TENANT_ONLY_CORE_TABLES).
"""
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Index
from datetime import datetime
import enum

from app.core.database import Base


class CanaleNotifica(str, enum.Enum):
    """Which channel(s) a notification should be delivered through."""
    IN_APP = "IN_APP"
    EMAIL = "EMAIL"
    ENTRAMBI = "ENTRAMBI"


class StatoEmailNotifica(str, enum.Enum):
    """Delivery status of the email leg of a notification (in-app is always created)."""
    NON_RICHIESTA = "NON_RICHIESTA"
    PENDING = "PENDING"
    SENT = "SENT"
    FAILED = "FAILED"


class Notifica(Base):
    """
    A single notification for a single user.

    entity_type/entity_id/link_url are an optional, free-form pointer back
    to whatever triggered the notification (same polymorphic pattern as
    Scadenza) — used only to build a frontend deep-link, never joined on.
    """
    __tablename__ = "core_notifiche"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(
        Integer,
        ForeignKey("core_users.id", ondelete="CASCADE"),
        nullable=False,
        comment="Recipient user",
    )

    tipo = Column(String(100), nullable=False, comment="Free namespace, e.g. 'scadenza.reminder'")
    titolo = Column(String(255), nullable=False)
    corpo = Column(Text, nullable=False)

    entity_type = Column(String(50), nullable=True)
    entity_id = Column(Integer, nullable=True)
    link_url = Column(String(500), nullable=True)

    canali = Column(String(20), nullable=False, default=CanaleNotifica.ENTRAMBI.value)
    stato_email = Column(String(20), nullable=False, default=StatoEmailNotifica.NON_RICHIESTA.value)
    errore_email = Column(Text, nullable=True)

    letta = Column(Boolean, nullable=False, default=False)
    letta_il = Column(DateTime, nullable=True)

    creata_il = Column(DateTime, nullable=False, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_core_notifiche_user_letta", "user_id", "letta"),
        Index("idx_core_notifiche_tipo", "tipo"),
        {"extend_existing": True},
    )

    def __repr__(self):
        return f"<Notifica(id={self.id}, user_id={self.user_id}, tipo='{self.tipo}', letta={self.letta})>"
```

- [ ] **Step 4: Export from `platform/models/__init__.py`**

In `backend/app/core/platform/models/__init__.py`, add the import and `__all__` entries:

```python
from .notifica import Notifica, CanaleNotifica, StatoEmailNotifica
```

and in `__all__`:

```python
    'Notifica',
    'CanaleNotifica',
    'StatoEmailNotifica',
```

- [ ] **Step 5: Register the model on `Base.metadata` in `app/main.py` and `alembic/env.py`**

In `backend/app/main.py`, change:

```python
from app.core.platform.models import (
    MenuItem, Widget, UserDashboard,
    Scadenza, ScadenzaDestinatario, ScadenzaLog,
    DocumentJob, JobStatus
)
```

to:

```python
from app.core.platform.models import (
    MenuItem, Widget, UserDashboard,
    Scadenza, ScadenzaDestinatario, ScadenzaLog,
    DocumentJob, JobStatus,
    Notifica, CanaleNotifica, StatoEmailNotifica
)
```

In `backend/alembic/env.py`, change:

```python
from app.core.platform.models import (  # noqa: F401
    MenuItem, Widget, UserDashboard, Scadenza, ScadenzaDestinatario, ScadenzaLog, DocumentJob, JobStatus,
)
```

to:

```python
from app.core.platform.models import (  # noqa: F401
    MenuItem, Widget, UserDashboard, Scadenza, ScadenzaDestinatario, ScadenzaLog, DocumentJob, JobStatus,
    Notifica, CanaleNotifica, StatoEmailNotifica,
)
```

- [ ] **Step 6: Run test to verify it passes**

Run: `cd backend && source venv/bin/activate && pytest tests/unit/test_core/test_notifica_model.py -v`
Expected: PASS

- [ ] **Step 7: Write the tenant migration**

Create `backend/alembic/versions/2026091802_create_core_notifiche_tenant_table.py`:

```python
"""Create core_notifiche inside every tenant schema.

Revision ID: 2026091802
Revises: 2026091801
Create Date: 2026-09-18
"""
from alembic import op
import sqlalchemy as sa

revision = "2026091802"
down_revision = "2026091801"
branch_labels = None
depends_on = None

target_schema = "tenant"


def upgrade() -> None:
    op.create_table(
        "core_notifiche",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.ForeignKeyConstraint(["user_id"], ["core_users.id"], ondelete="CASCADE"),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("tipo", sa.String(length=100), nullable=False),
        sa.Column("titolo", sa.String(length=255), nullable=False),
        sa.Column("corpo", sa.Text(), nullable=False),
        sa.Column("entity_type", sa.String(length=50), nullable=True),
        sa.Column("entity_id", sa.Integer(), nullable=True),
        sa.Column("link_url", sa.String(length=500), nullable=True),
        sa.Column("canali", sa.String(length=20), nullable=False),
        sa.Column("stato_email", sa.String(length=20), nullable=False),
        sa.Column("errore_email", sa.Text(), nullable=True),
        sa.Column("letta", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("letta_il", sa.DateTime(), nullable=True),
        sa.Column("creata_il", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_core_notifiche_id", "core_notifiche", ["id"])
    op.create_index("idx_core_notifiche_user_letta", "core_notifiche", ["user_id", "letta"])
    op.create_index("idx_core_notifiche_tipo", "core_notifiche", ["tipo"])


def downgrade() -> None:
    op.drop_table("core_notifiche")
```

- [ ] **Step 8: Apply the migration**

Run: `cd backend && source venv/bin/activate && alembic -x schema=all upgrade head`
Expected: no errors

Verify: `PGPASSWORD=affitti psql -h localhost -p 5433 -U affitti -d gestione_affitti -c "SELECT table_schema FROM information_schema.tables WHERE table_name='core_notifiche';"`
Expected: rows for `tenant_principale`, `tenant_produzione`, `tenant_qa_test` — **not** `public`

- [ ] **Step 9: Commit**

```bash
cd backend
git add app/core/platform/models/notifica.py app/core/platform/models/__init__.py app/main.py alembic/env.py alembic/versions/2026091802_create_core_notifiche_tenant_table.py tests/unit/test_core/test_notifica_model.py
git commit -m "feat(notifiche): add Notifica model, tenant-scoped from the start"
```

---

### Task 3: `NotificationService`

**Files:**
- Create: `backend/app/core/platform_services/notification_service.py`
- Modify: `backend/app/core/platform_services/__init__.py`
- Modify: `backend/app/core/config.py` (comment tweak only — no new settings needed here, `NOTIFICHE_SMTP_*` already exists)
- Test: `backend/tests/unit/test_core/test_notification_service.py`

**Interfaces:**
- Consumes: `Notifica`, `CanaleNotifica`, `StatoEmailNotifica` from `app.core.platform.models` (Task 2); `settings.NOTIFICHE_SMTP_*` from `app.core.config`.
- Produces:
  - `NotificationService(db: Session)`
  - `.notify(user_ids: list[int], tipo: str, titolo: str, corpo: str, entity_type: str | None = None, entity_id: int | None = None, link_url: str | None = None, canali: CanaleNotifica = CanaleNotifica.ENTRAMBI) -> list[Notifica]`
  - `.list_for_user(user_id: int, solo_non_lette: bool = False, skip: int = 0, limit: int = 50) -> list[Notifica]`
  - `.segna_letta(notifica_id: int, user_id: int) -> Notifica | None`
  - `.segna_tutte_lette(user_id: int) -> int` (returns count updated)
  - `.badge_count(user_id: int) -> int`
  These four method names/signatures are consumed by Task 4's routes and Task 5's reminder job.

- [ ] **Step 1: Write the failing tests**

Create `backend/tests/unit/test_core/test_notification_service.py`:

```python
import smtplib
from unittest.mock import patch, MagicMock

import pytest

from app.core.platform.models import CanaleNotifica, StatoEmailNotifica
from app.core.platform_services.notification_service import NotificationService


@pytest.fixture
def service(db_session):
    return NotificationService(db_session)


def test_notify_creates_in_app_row_without_email_when_smtp_not_configured(service, test_user):
    with patch("app.core.config.settings.NOTIFICHE_SMTP_HOST", None):
        result = service.notify(
            user_ids=[test_user.id],
            tipo="test.evento",
            titolo="Titolo",
            corpo="Corpo",
            canali=CanaleNotifica.ENTRAMBI,
        )

    assert len(result) == 1
    notifica = result[0]
    assert notifica.user_id == test_user.id
    assert notifica.stato_email == StatoEmailNotifica.NON_RICHIESTA.value
    assert notifica.letta is False


def test_notify_email_only_channel_still_creates_row(service, test_user):
    with patch("app.core.config.settings.NOTIFICHE_SMTP_HOST", None):
        result = service.notify(
            user_ids=[test_user.id],
            tipo="scadenza.reminder",
            titolo="Titolo",
            corpo="Corpo",
            canali=CanaleNotifica.EMAIL,
        )

    assert len(result) == 1
    assert result[0].canali == CanaleNotifica.EMAIL.value


def test_notify_multiple_recipients(service, test_user, admin_user):
    with patch("app.core.config.settings.NOTIFICHE_SMTP_HOST", None):
        result = service.notify(
            user_ids=[test_user.id, admin_user.id],
            tipo="test.evento",
            titolo="Titolo",
            corpo="Corpo",
        )

    assert {n.user_id for n in result} == {test_user.id, admin_user.id}


def test_notify_sends_email_and_marks_sent_on_success(service, test_user):
    smtp_instance = MagicMock()
    with patch("app.core.config.settings.NOTIFICHE_SMTP_HOST", "smtp.example.com"), \
         patch("app.core.config.settings.NOTIFICHE_SMTP_TLS", "STARTTLS"), \
         patch("smtplib.SMTP") as mock_smtp:
        mock_smtp.return_value.__enter__.return_value = smtp_instance
        result = service.notify(
            user_ids=[test_user.id],
            tipo="test.evento",
            titolo="Titolo",
            corpo="Corpo",
            canali=CanaleNotifica.EMAIL,
        )

    assert result[0].stato_email == StatoEmailNotifica.SENT.value
    smtp_instance.sendmail.assert_called_once()


def test_notify_marks_failed_on_smtp_error_but_keeps_in_app_row(service, test_user):
    with patch("app.core.config.settings.NOTIFICHE_SMTP_HOST", "smtp.example.com"), \
         patch("app.core.config.settings.NOTIFICHE_SMTP_TLS", "STARTTLS"), \
         patch("smtplib.SMTP", side_effect=smtplib.SMTPException("boom")):
        result = service.notify(
            user_ids=[test_user.id],
            tipo="test.evento",
            titolo="Titolo",
            corpo="Corpo",
            canali=CanaleNotifica.EMAIL,
        )

    assert len(result) == 1
    assert result[0].stato_email == StatoEmailNotifica.FAILED.value
    assert result[0].errore_email is not None


def test_list_for_user_filters_by_owner(service, test_user, admin_user):
    with patch("app.core.config.settings.NOTIFICHE_SMTP_HOST", None):
        service.notify(user_ids=[test_user.id], tipo="a", titolo="A", corpo="A")
        service.notify(user_ids=[admin_user.id], tipo="b", titolo="B", corpo="B")

    mine = service.list_for_user(test_user.id)
    assert len(mine) == 1
    assert mine[0].user_id == test_user.id


def test_list_for_user_solo_non_lette(service, test_user):
    with patch("app.core.config.settings.NOTIFICHE_SMTP_HOST", None):
        notifiche = service.notify(user_ids=[test_user.id], tipo="a", titolo="A", corpo="A")
    service.segna_letta(notifiche[0].id, test_user.id)

    assert service.list_for_user(test_user.id, solo_non_lette=True) == []
    assert len(service.list_for_user(test_user.id, solo_non_lette=False)) == 1


def test_segna_letta_only_affects_owner(service, test_user, admin_user):
    with patch("app.core.config.settings.NOTIFICHE_SMTP_HOST", None):
        notifiche = service.notify(user_ids=[test_user.id], tipo="a", titolo="A", corpo="A")

    result = service.segna_letta(notifiche[0].id, admin_user.id)
    assert result is None  # not the owner, no-op

    result = service.segna_letta(notifiche[0].id, test_user.id)
    assert result.letta is True
    assert result.letta_il is not None


def test_segna_tutte_lette(service, test_user):
    with patch("app.core.config.settings.NOTIFICHE_SMTP_HOST", None):
        service.notify(user_ids=[test_user.id], tipo="a", titolo="A", corpo="A")
        service.notify(user_ids=[test_user.id], tipo="b", titolo="B", corpo="B")

    count = service.segna_tutte_lette(test_user.id)
    assert count == 2
    assert service.badge_count(test_user.id) == 0


def test_badge_count(service, test_user):
    with patch("app.core.config.settings.NOTIFICHE_SMTP_HOST", None):
        service.notify(user_ids=[test_user.id], tipo="a", titolo="A", corpo="A")
        notifiche = service.notify(user_ids=[test_user.id], tipo="b", titolo="B", corpo="B")
    service.segna_letta(notifiche[0].id, test_user.id)

    assert service.badge_count(test_user.id) == 1
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && source venv/bin/activate && pytest tests/unit/test_core/test_notification_service.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'app.core.platform_services.notification_service'`

- [ ] **Step 3: Implement `NotificationService`**

Create `backend/app/core/platform_services/notification_service.py`:

```python
"""
NotificationService - Generic Core Notification Service

Creates in-app notifications and, optionally, sends the corresponding
email via the application's own SMTP account (NOTIFICHE_SMTP_* settings —
shared with gestione_pec, not duplicated per module). Core platform
service: any module imports and calls this directly (see
docs/superpowers/specs/2026-09-14-module-communication-architecture-design.md
§3.1) — never re-implement email sending in a module.

Usage:
    from app.core.platform_services import NotificationService
    service = NotificationService(db)
    service.notify(user_ids=[5, 8], tipo="scadenza.reminder", titolo="...", corpo="...")
"""
from __future__ import annotations

import logging
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime
from typing import List, Optional

from sqlalchemy.orm import Session

from app.core.platform.models import Notifica, CanaleNotifica, StatoEmailNotifica

logger = logging.getLogger(__name__)


class NotificationService:
    def __init__(self, db: Session):
        self.db = db

    # =========================================================================
    # WRITE
    # =========================================================================

    def notify(
        self,
        user_ids: List[int],
        tipo: str,
        titolo: str,
        corpo: str,
        entity_type: Optional[str] = None,
        entity_id: Optional[int] = None,
        link_url: Optional[str] = None,
        canali: CanaleNotifica = CanaleNotifica.ENTRAMBI,
    ) -> List[Notifica]:
        """
        Create one Notifica per user_id. If canali includes EMAIL, attempts
        to send it immediately via the application SMTP account and updates
        stato_email accordingly. A failed email never raises and never
        removes the in-app notification — it only sets stato_email=FAILED.
        """
        created: List[Notifica] = []

        vuole_email = canali in (CanaleNotifica.EMAIL, CanaleNotifica.ENTRAMBI)

        for user_id in user_ids:
            notifica = Notifica(
                user_id=user_id,
                tipo=tipo,
                titolo=titolo,
                corpo=corpo,
                entity_type=entity_type,
                entity_id=entity_id,
                link_url=link_url,
                canali=canali.value,
                stato_email=StatoEmailNotifica.PENDING.value if vuole_email else StatoEmailNotifica.NON_RICHIESTA.value,
            )
            self.db.add(notifica)
            self.db.flush()
            created.append(notifica)

        if vuole_email:
            for notifica in created:
                self._send_email_for(notifica)

        self.db.commit()
        for notifica in created:
            self.db.refresh(notifica)
        return created

    def _send_email_for(self, notifica: Notifica) -> None:
        """Attempts email delivery for one Notifica; updates it in place, never raises."""
        from app.core.config import settings
        from sqlalchemy import text

        if not settings.NOTIFICHE_SMTP_HOST:
            notifica.stato_email = StatoEmailNotifica.NON_RICHIESTA.value
            return

        row = self.db.execute(
            text("SELECT email FROM public.core_users WHERE id = :id AND email IS NOT NULL"),
            {"id": notifica.user_id},
        ).fetchone()
        if not row:
            notifica.stato_email = StatoEmailNotifica.FAILED.value
            notifica.errore_email = "Utente senza email"
            return

        try:
            self._send_via_smtp(row[0], notifica.titolo, notifica.corpo)
            notifica.stato_email = StatoEmailNotifica.SENT.value
            notifica.errore_email = None
        except Exception as exc:
            logger.warning("[NotificationService] invio email fallito per notifica user_id=%s: %s", notifica.user_id, exc)
            notifica.stato_email = StatoEmailNotifica.FAILED.value
            notifica.errore_email = str(exc)[:2000]

    @staticmethod
    def _send_via_smtp(to_email: str, subject: str, body_text: str) -> None:
        from app.core.config import settings

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = settings.NOTIFICHE_SMTP_FROM_EMAIL or settings.NOTIFICHE_SMTP_USER
        msg["To"] = to_email
        msg.attach(MIMEText(body_text, "plain", "utf-8"))

        host = settings.NOTIFICHE_SMTP_HOST
        port = settings.NOTIFICHE_SMTP_PORT
        user = settings.NOTIFICHE_SMTP_USER
        password = settings.NOTIFICHE_SMTP_PASSWORD
        tls = (settings.NOTIFICHE_SMTP_TLS or "STARTTLS").upper()

        if tls == "SSL":
            ctx = ssl.create_default_context()
            with smtplib.SMTP_SSL(host, port, context=ctx, timeout=15) as smtp:
                if user and password:
                    smtp.login(user, password)
                smtp.sendmail(msg["From"], [to_email], msg.as_string())
        elif tls == "STARTTLS":
            with smtplib.SMTP(host, port, timeout=15) as smtp:
                smtp.ehlo()
                smtp.starttls(context=ssl.create_default_context())
                smtp.ehlo()
                if user and password:
                    smtp.login(user, password)
                smtp.sendmail(msg["From"], [to_email], msg.as_string())
        else:
            with smtplib.SMTP(host, port, timeout=15) as smtp:
                if user and password:
                    smtp.login(user, password)
                smtp.sendmail(msg["From"], [to_email], msg.as_string())

    # =========================================================================
    # READ
    # =========================================================================

    def list_for_user(
        self,
        user_id: int,
        solo_non_lette: bool = False,
        skip: int = 0,
        limit: int = 50,
    ) -> List[Notifica]:
        query = self.db.query(Notifica).filter(Notifica.user_id == user_id)
        if solo_non_lette:
            query = query.filter(Notifica.letta.is_(False))
        return (
            query.order_by(Notifica.creata_il.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def badge_count(self, user_id: int) -> int:
        return (
            self.db.query(Notifica)
            .filter(Notifica.user_id == user_id, Notifica.letta.is_(False))
            .count()
        )

    # =========================================================================
    # STATE
    # =========================================================================

    def segna_letta(self, notifica_id: int, user_id: int) -> Optional[Notifica]:
        notifica = (
            self.db.query(Notifica)
            .filter(Notifica.id == notifica_id, Notifica.user_id == user_id)
            .first()
        )
        if not notifica:
            return None
        notifica.letta = True
        notifica.letta_il = datetime.utcnow()
        self.db.commit()
        self.db.refresh(notifica)
        return notifica

    def segna_tutte_lette(self, user_id: int) -> int:
        notifiche = (
            self.db.query(Notifica)
            .filter(Notifica.user_id == user_id, Notifica.letta.is_(False))
            .all()
        )
        now = datetime.utcnow()
        for notifica in notifiche:
            notifica.letta = True
            notifica.letta_il = now
        self.db.commit()
        return len(notifiche)
```

- [ ] **Step 4: Export from `platform_services/__init__.py`**

In `backend/app/core/platform_services/__init__.py`, add:

```python
from .notification_service import NotificationService
```

and add `"NotificationService"` to `__all__`.

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd backend && source venv/bin/activate && pytest tests/unit/test_core/test_notification_service.py -v`
Expected: PASS (10 tests)

- [ ] **Step 6: Commit**

```bash
cd backend
git add app/core/platform_services/notification_service.py app/core/platform_services/__init__.py tests/unit/test_core/test_notification_service.py
git commit -m "feat(notifiche): add NotificationService (in-app + email)"
```

---

### Task 4: `/notifiche` routes + schemas + main.py wiring

**Files:**
- Create: `backend/app/core/schemas/notifica.py`
- Modify: `backend/app/core/schemas/__init__.py`
- Create: `backend/app/core/routes/notifiche.py`
- Modify: `backend/app/main.py` (import + `include_router`)
- Test: `backend/tests/integration/test_notifiche_routes.py`

**Interfaces:**
- Consumes: `NotificationService` (Task 3), `get_db`, `get_current_user`.
- Produces: `GET /api/v1/notifiche`, `POST /api/v1/notifiche/{id}/segna-letta`, `POST /api/v1/notifiche/segna-tutte-lette`, `GET /api/v1/notifiche/badge`.

- [ ] **Step 1: Write the failing integration tests**

Create `backend/tests/integration/test_notifiche_routes.py`:

```python
from unittest.mock import patch

from app.core.platform_services import NotificationService


def _create_notifica(db_session, user_id, titolo="Titolo"):
    with patch("app.core.config.settings.NOTIFICHE_SMTP_HOST", None):
        return NotificationService(db_session).notify(
            user_ids=[user_id], tipo="test.evento", titolo=titolo, corpo="Corpo"
        )[0]


def test_list_notifiche_returns_only_own(auth_client, admin_client, db_session, test_user, admin_user):
    _create_notifica(db_session, test_user.id, "Mia")
    _create_notifica(db_session, admin_user.id, "Non mia")

    response = auth_client.get("/api/v1/notifiche")
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["titolo"] == "Mia"


def test_list_notifiche_solo_non_lette(auth_client, db_session, test_user):
    n = _create_notifica(db_session, test_user.id)
    NotificationService(db_session).segna_letta(n.id, test_user.id)
    _create_notifica(db_session, test_user.id, "Seconda")

    response = auth_client.get("/api/v1/notifiche", params={"solo_non_lette": True})
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["titolo"] == "Seconda"


def test_segna_letta(auth_client, db_session, test_user):
    n = _create_notifica(db_session, test_user.id)

    response = auth_client.post(f"/api/v1/notifiche/{n.id}/segna-letta")
    assert response.status_code == 200
    assert response.json()["letta"] is True


def test_segna_letta_altrui_ritorna_404(auth_client, db_session, admin_user):
    n = _create_notifica(db_session, admin_user.id)

    response = auth_client.post(f"/api/v1/notifiche/{n.id}/segna-letta")
    assert response.status_code == 404


def test_segna_tutte_lette(auth_client, db_session, test_user):
    _create_notifica(db_session, test_user.id, "Uno")
    _create_notifica(db_session, test_user.id, "Due")

    response = auth_client.post("/api/v1/notifiche/segna-tutte-lette")
    assert response.status_code == 200
    assert response.json()["count"] == 2


def test_badge(auth_client, db_session, test_user):
    _create_notifica(db_session, test_user.id)

    response = auth_client.get("/api/v1/notifiche/badge")
    assert response.status_code == 200
    assert response.json()["count_non_lette"] == 1


def test_notifiche_require_auth(client):
    response = client.get("/api/v1/notifiche")
    assert response.status_code == 401
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && source venv/bin/activate && pytest tests/integration/test_notifiche_routes.py -v`
Expected: FAIL — 404 Not Found (route doesn't exist yet)

- [ ] **Step 3: Write schemas**

Create `backend/app/core/schemas/notifica.py`:

```python
"""Pydantic schemas for the generic Notifica (core notification service)."""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from enum import Enum


class CanaleNotifica(str, Enum):
    IN_APP = "IN_APP"
    EMAIL = "EMAIL"
    ENTRAMBI = "ENTRAMBI"


class StatoEmailNotifica(str, Enum):
    NON_RICHIESTA = "NON_RICHIESTA"
    PENDING = "PENDING"
    SENT = "SENT"
    FAILED = "FAILED"


class NotificaResponse(BaseModel):
    id: int
    tipo: str
    titolo: str
    corpo: str
    entity_type: Optional[str] = None
    entity_id: Optional[int] = None
    link_url: Optional[str] = None
    canali: str
    stato_email: str
    letta: bool
    letta_il: Optional[datetime] = None
    creata_il: datetime

    class Config:
        from_attributes = True


class NotificaBadgeResponse(BaseModel):
    count_non_lette: int


class SegnaTutteLetteResponse(BaseModel):
    count: int
```

In `backend/app/core/schemas/__init__.py`, add:

```python
from .notifica import (
    CanaleNotifica as CanaleNotificaSchema,
    StatoEmailNotifica as StatoEmailNotificaSchema,
    NotificaResponse,
    NotificaBadgeResponse,
    SegnaTutteLetteResponse,
)
```

and to `__all__`:

```python
    "NotificaResponse",
    "NotificaBadgeResponse",
    "SegnaTutteLetteResponse",
```

(`CanaleNotificaSchema`/`StatoEmailNotificaSchema` are imported under aliased names to avoid clashing with the existing `PrioritaScadenza`/`StatoScadenza` naming convention already re-exported from this module — they aren't needed elsewhere in this plan, so they don't need to be added to `__all__`.)

- [ ] **Step 4: Write the routes**

Create `backend/app/core/routes/notifiche.py`:

```python
"""
Notifiche API Routes - Generic Core Notification Service

Every endpoint operates only on the authenticated user's own notifications
— user_id always comes from the token, never from a query/path parameter.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.core.auth.dependencies import get_current_user
from app.core.auth.models import User
from app.core.platform_services import NotificationService
from app.core.schemas import NotificaResponse, NotificaBadgeResponse, SegnaTutteLetteResponse


router = APIRouter(prefix="/notifiche", tags=["Notifiche"])


@router.get("/", response_model=List[NotificaResponse])
def list_notifiche(
    solo_non_lette: bool = Query(False),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List the current user's notifications, most recent first."""
    service = NotificationService(db)
    return service.list_for_user(current_user.id, solo_non_lette=solo_non_lette, skip=skip, limit=limit)


@router.post("/{notifica_id}/segna-letta", response_model=NotificaResponse)
def segna_letta(
    notifica_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = NotificationService(db)
    notifica = service.segna_letta(notifica_id, current_user.id)
    if not notifica:
        raise HTTPException(status_code=404, detail="Notifica non trovata")
    return notifica


@router.post("/segna-tutte-lette", response_model=SegnaTutteLetteResponse)
def segna_tutte_lette(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = NotificationService(db)
    count = service.segna_tutte_lette(current_user.id)
    return SegnaTutteLetteResponse(count=count)


@router.get("/badge", response_model=NotificaBadgeResponse)
def badge(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = NotificationService(db)
    return NotificaBadgeResponse(count_non_lette=service.badge_count(current_user.id))
```

Note: `list_notifiche` is declared with path `"/"` (trailing slash, matching every other core route in this codebase, e.g. `scadenze.py`); FastAPI/Starlette's default `redirect_slashes=True` means `GET /api/v1/notifiche` (no trailing slash) also works.

- [ ] **Step 5: Wire the router in `main.py`**

In `backend/app/main.py`, add the import near the other platform routes:

```python
from app.core.routes.notifiche import router as notifiche_router
```

and the registration next to `scadenze_router`:

```python
app.include_router(scadenze_router, prefix=settings.API_V1_STR)
app.include_router(notifiche_router, prefix=settings.API_V1_STR)
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `cd backend && source venv/bin/activate && pytest tests/integration/test_notifiche_routes.py -v`
Expected: PASS (7 tests)

- [ ] **Step 7: Run the full backend test suite to check for regressions**

Run: `cd backend && ./run_tests.sh unit && ./run_tests.sh integration`
Expected: all passing (no regressions from Tasks 1-4)

- [ ] **Step 8: Commit**

```bash
cd backend
git add app/core/schemas/notifica.py app/core/schemas/__init__.py app/core/routes/notifiche.py app/main.py tests/integration/test_notifiche_routes.py
git commit -m "feat(notifiche): add /api/v1/notifiche routes"
```

---

### Task 5: Scadenza reminder job (closes the actual gap in the spec)

**Files:**
- Modify: `backend/app/core/platform_services/scadenza_service.py` (`update_overdue_status`)
- Modify: `backend/app/core/config.py` (add `REMINDER_GIORNI_PRIMA`)
- Create: `backend/app/core/platform_services/scadenza_reminder_job.py`
- Modify: `backend/app/main.py` (start the scheduler)
- Test: `backend/tests/unit/test_core/test_scadenza_service_overdue_reset.py`
- Test: `backend/tests/unit/test_core/test_scadenza_reminder_job.py`

**Interfaces:**
- Consumes: `ScadenzaService.update_overdue_status()` (existing, modified in this task), `NotificationService.notify()` (Task 3), `Tenant` model (`app.core.models.tenant`), `SessionLocal` (`app.core.database`).
- Produces: `run_reminder_check(tenant_schema: str) -> None`, `ReminderScheduler` class with `.start()` / `.stop()` / `._started` (mirrors `PecPollingScheduler`'s shape exactly, including the `_started` guard used at startup).

- [ ] **Step 1: Write the failing test for the anti-spam reset**

Create `backend/tests/unit/test_core/test_scadenza_service_overdue_reset.py`:

```python
from datetime import date, timedelta

from app.core.platform.models import Scadenza, ScadenzaDestinatario, StatoScadenza
from app.core.platform_services import ScadenzaService


def test_update_overdue_status_resets_notificato_flag(db_session, test_user):
    scadenza = Scadenza(
        titolo="Test",
        data_scadenza=date.today() - timedelta(days=1),
        stato=StatoScadenza.ATTIVA,
        creato_da=test_user.id,
    )
    db_session.add(scadenza)
    db_session.flush()

    destinatario = ScadenzaDestinatario(scadenza_id=scadenza.id, user_id=test_user.id, notificato=True)
    db_session.add(destinatario)
    db_session.commit()

    ScadenzaService(db_session).update_overdue_status()

    db_session.refresh(scadenza)
    db_session.refresh(destinatario)
    assert scadenza.stato == StatoScadenza.SCADUTA
    assert destinatario.notificato is False


def test_update_overdue_status_does_not_touch_already_scaduta(db_session, test_user):
    scadenza = Scadenza(
        titolo="Test",
        data_scadenza=date.today() - timedelta(days=5),
        stato=StatoScadenza.SCADUTA,
        creato_da=test_user.id,
    )
    db_session.add(scadenza)
    db_session.flush()
    destinatario = ScadenzaDestinatario(scadenza_id=scadenza.id, user_id=test_user.id, notificato=True)
    db_session.add(destinatario)
    db_session.commit()

    ScadenzaService(db_session).update_overdue_status()

    db_session.refresh(destinatario)
    assert destinatario.notificato is True  # untouched: was already SCADUTA before this call
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && source venv/bin/activate && pytest tests/unit/test_core/test_scadenza_service_overdue_reset.py -v`
Expected: FAIL on the first test — `notificato` stays `True` (current code never resets it)

- [ ] **Step 3: Update `update_overdue_status()`**

In `backend/app/core/platform_services/scadenza_service.py`, replace the `update_overdue_status` method body:

```python
    def update_overdue_status(self):
        """
        Update stato for all ATTIVA scadenze that are past due.
        Sets stato to SCADUTA automatically, and resets the notificato flag
        on every recipient so the reminder job (which only notifies once per
        "event") sends a fresh "scaduta" notification distinct from the
        earlier "in avvicinamento" one.

        Should be called periodically (e.g., daily cron job).
        """
        today = date.today()

        overdue = self.db.query(Scadenza).filter(
            Scadenza.stato == StatoScadenza.ATTIVA,
            Scadenza.data_scadenza < today
        ).all()

        for scadenza in overdue:
            scadenza.stato = StatoScadenza.SCADUTA
            scadenza.modificato_il = datetime.utcnow()

            for destinatario in scadenza.destinatari:
                destinatario.notificato = False
                destinatario.notificato_il = None

            # Log automatic state change
            log = ScadenzaLog.log_state_change(
                scadenza_id=scadenza.id,
                user_id=None,  # System action
                old_state=StatoScadenza.ATTIVA.value,
                new_state=StatoScadenza.SCADUTA.value,
                note="Aggiornamento automatico: scadenza superata"
            )
            self.db.add(log)

        if overdue:
            self.db.commit()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && source venv/bin/activate && pytest tests/unit/test_core/test_scadenza_service_overdue_reset.py -v`
Expected: PASS

- [ ] **Step 5: Add the `REMINDER_GIORNI_PRIMA` setting**

In `backend/app/core/config.py`, change the comment and add the new field right after the `NOTIFICHE_SMTP_*` block:

```python
    # Notifiche — SMTP applicativo (usato da gestione_pec e dal reminder scadenzario)
    # Se NOTIFICHE_SMTP_HOST è vuoto le notifiche email sono disabilitate.
    NOTIFICHE_SMTP_HOST: Optional[str] = None
    NOTIFICHE_SMTP_PORT: int = 587
    NOTIFICHE_SMTP_USER: Optional[str] = None
    NOTIFICHE_SMTP_PASSWORD: Optional[str] = None
    NOTIFICHE_SMTP_FROM_EMAIL: Optional[str] = None
    NOTIFICHE_SMTP_TLS: str = "STARTTLS"  # "SSL" | "STARTTLS" | "none"

    # Scadenzario — reminder automatico
    REMINDER_GIORNI_PRIMA: int = 3  # notifica quando data_scadenza è tra oggi e oggi+N
```

- [ ] **Step 6: Write the failing test for the reminder job**

Create `backend/tests/unit/test_core/test_scadenza_reminder_job.py`:

```python
from datetime import date, timedelta
from unittest.mock import patch

from app.core.platform.models import Scadenza, ScadenzaDestinatario, StatoScadenza
from app.core.platform_services.scadenza_reminder_job import _check_scadenze_in_avvicinamento


def _make_scadenza(db_session, user_id, giorni_da_oggi, notificato=False):
    scadenza = Scadenza(
        titolo=f"Scadenza tra {giorni_da_oggi}gg",
        data_scadenza=date.today() + timedelta(days=giorni_da_oggi),
        stato=StatoScadenza.ATTIVA,
        creato_da=user_id,
    )
    db_session.add(scadenza)
    db_session.flush()
    destinatario = ScadenzaDestinatario(scadenza_id=scadenza.id, user_id=user_id, notificato=notificato)
    db_session.add(destinatario)
    db_session.commit()
    return scadenza, destinatario


def test_notifies_scadenze_within_threshold(db_session, test_user):
    _make_scadenza(db_session, test_user.id, giorni_da_oggi=2)

    with patch("app.core.platform_services.scadenza_reminder_job.NotificationService") as MockService:
        _check_scadenze_in_avvicinamento(db_session, giorni_prima=3)

    MockService.return_value.notify.assert_called_once()


def test_does_not_notify_outside_threshold(db_session, test_user):
    _make_scadenza(db_session, test_user.id, giorni_da_oggi=10)

    with patch("app.core.platform_services.scadenza_reminder_job.NotificationService") as MockService:
        _check_scadenze_in_avvicinamento(db_session, giorni_prima=3)

    MockService.return_value.notify.assert_not_called()


def test_does_not_renotify_already_notified(db_session, test_user):
    _make_scadenza(db_session, test_user.id, giorni_da_oggi=1, notificato=True)

    with patch("app.core.platform_services.scadenza_reminder_job.NotificationService") as MockService:
        _check_scadenze_in_avvicinamento(db_session, giorni_prima=3)

    MockService.return_value.notify.assert_not_called()


def test_marks_recipients_notified_after_sending(db_session, test_user):
    scadenza, destinatario = _make_scadenza(db_session, test_user.id, giorni_da_oggi=1)

    with patch("app.core.platform_services.scadenza_reminder_job.NotificationService"):
        _check_scadenze_in_avvicinamento(db_session, giorni_prima=3)

    db_session.refresh(destinatario)
    assert destinatario.notificato is True
    assert destinatario.notificato_il is not None


def test_notifies_creator_when_no_explicit_recipients(db_session, test_user):
    scadenza = Scadenza(
        titolo="TODO senza destinatari",
        data_scadenza=date.today() + timedelta(days=1),
        stato=StatoScadenza.ATTIVA,
        creato_da=test_user.id,
    )
    db_session.add(scadenza)
    db_session.commit()

    with patch("app.core.platform_services.scadenza_reminder_job.NotificationService") as MockService:
        _check_scadenze_in_avvicinamento(db_session, giorni_prima=3)

    _, kwargs = MockService.return_value.notify.call_args
    assert test_user.id in kwargs["user_ids"]


def test_one_bad_scadenza_does_not_block_others(db_session, test_user):
    """A NotificationService failure on one scadenza must not stop the rest."""
    _make_scadenza(db_session, test_user.id, giorni_da_oggi=1)
    _make_scadenza(db_session, test_user.id, giorni_da_oggi=2)

    with patch("app.core.platform_services.scadenza_reminder_job.NotificationService") as MockService:
        MockService.return_value.notify.side_effect = [RuntimeError("boom"), None]
        _check_scadenze_in_avvicinamento(db_session, giorni_prima=3)

    assert MockService.return_value.notify.call_count == 2
```

- [ ] **Step 7: Run tests to verify they fail**

Run: `cd backend && source venv/bin/activate && pytest tests/unit/test_core/test_scadenza_reminder_job.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'app.core.platform_services.scadenza_reminder_job'`

- [ ] **Step 8: Implement the reminder job and scheduler**

Create `backend/app/core/platform_services/scadenza_reminder_job.py`:

```python
"""
Scadenza Reminder Job

Daily background check across every active tenant: notifies (email only,
see the plan's Global Constraints for why) the creator and recipients of
scadenze entering the "in avvicinamento" window, and re-notifies once when
a scadenza flips to SCADUTA (ScadenzaService.update_overdue_status()
resets the notificato flag for exactly that reason).

Pattern mirrors modules/gestione_pec/services/polling_scheduler.py:
tenant discovery via public.core_tenants, one SessionLocal() per tenant
with search_path set manually (no FastAPI request context here).
"""
from __future__ import annotations

import logging
import threading
from datetime import date, timedelta

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.core.platform.models import Scadenza, StatoScadenza, CanaleNotifica
from app.core.platform_services.scadenza_service import ScadenzaService
from app.core.platform_services.notification_service import NotificationService

logger = logging.getLogger(__name__)


def _check_scadenze_in_avvicinamento(db: Session, giorni_prima: int) -> None:
    """Notify (email) every ATTIVA scadenza due within [today, today+giorni_prima]
    whose recipients haven't been notified for this event yet. One failure
    is isolated to its own scadenza and never blocks the rest."""
    soglia = date.today() + timedelta(days=giorni_prima)

    scadenze = (
        db.query(Scadenza)
        .filter(
            Scadenza.stato == StatoScadenza.ATTIVA,
            Scadenza.data_scadenza >= date.today(),
            Scadenza.data_scadenza <= soglia,
        )
        .all()
    )

    for scadenza in scadenze:
        try:
            destinatari = [d for d in scadenza.destinatari if not d.notificato]
            user_ids = [d.user_id for d in destinatari]
            if not scadenza.destinatari and scadenza.creato_da not in user_ids:
                user_ids.append(scadenza.creato_da)
            if not user_ids:
                continue

            NotificationService(db).notify(
                user_ids=user_ids,
                tipo="scadenza.reminder",
                titolo=f"Scadenza in avvicinamento: {scadenza.titolo}",
                corpo=f"La scadenza \"{scadenza.titolo}\" è prevista per il {scadenza.data_scadenza.isoformat()}.",
                entity_type="scadenza",
                entity_id=scadenza.id,
                link_url=f"/scadenze/{scadenza.id}",
                canali=CanaleNotifica.EMAIL,
            )

            for destinatario in destinatari:
                destinatario.mark_notified()
            db.commit()
        except Exception as exc:
            logger.error(
                "[ReminderJob] errore notificando scadenza id=%s: %s",
                scadenza.id, exc, exc_info=True,
            )
            db.rollback()


def run_reminder_check(tenant_schema: str) -> None:
    """Entry point called once per active tenant by ReminderScheduler."""
    from app.core.config import settings

    db = SessionLocal()
    try:
        db.execute(text(f"SET search_path TO {tenant_schema}, public"))
        db.commit()

        ScadenzaService(db).update_overdue_status()
        _check_scadenze_in_avvicinamento(db, giorni_prima=settings.REMINDER_GIORNI_PRIMA)
    except Exception as exc:
        logger.error("[ReminderJob] %s: errore durante il check: %s", tenant_schema, exc, exc_info=True)
    finally:
        db.close()


def _run_for_all_tenants() -> None:
    db = SessionLocal()
    try:
        tenants = db.execute(
            text("SELECT schema_name FROM public.core_tenants WHERE active = true OR active IS NULL")
        ).fetchall()
    except Exception as exc:
        logger.warning("[ReminderScheduler] impossibile leggere i tenant: %s", exc)
        tenants = []
    finally:
        db.close()

    for row in tenants:
        run_reminder_check(row[0])


class ReminderScheduler:
    """Global daily job (07:00) that runs the reminder check for every active tenant."""

    def __init__(self) -> None:
        self.scheduler = BackgroundScheduler(
            job_defaults={"coalesce": True, "max_instances": 1, "misfire_grace_time": 3600}
        )
        self._started = False
        self._lock = threading.Lock()

    def start(self) -> None:
        with self._lock:
            if self._started:
                return
            self.scheduler.add_job(
                func=_run_for_all_tenants,
                trigger=CronTrigger(hour=7, minute=0),
                id="scadenza_reminder_job",
                name="Scadenza Reminder Check",
                replace_existing=True,
            )
            self.scheduler.start()
            self._started = True
            logger.info("[ReminderScheduler] avviato (giornaliero alle 07:00)")

    def stop(self) -> None:
        with self._lock:
            if not self._started:
                return
            self.scheduler.shutdown(wait=False)
            self._started = False


_reminder_scheduler: ReminderScheduler | None = None


def get_reminder_scheduler() -> ReminderScheduler:
    global _reminder_scheduler
    if _reminder_scheduler is None:
        _reminder_scheduler = ReminderScheduler()
    return _reminder_scheduler
```

- [ ] **Step 9: Run tests to verify they pass**

Run: `cd backend && source venv/bin/activate && pytest tests/unit/test_core/test_scadenza_reminder_job.py -v`
Expected: PASS (6 tests)

- [ ] **Step 10: Start the scheduler at app boot**

In `backend/app/main.py`, right after `create_core_tables()` is called (near the `# Crea le tabelle core nel database` comment), add:

```python
# Avvia lo scheduler del reminder scadenzario (core, non un modulo — gira
# sempre, indipendentemente da quali moduli business sono installati)
from app.core.platform_services.scadenza_reminder_job import get_reminder_scheduler
get_reminder_scheduler().start()
```

- [ ] **Step 11: Run the full backend test suite**

Run: `cd backend && ./run_tests.sh unit && ./run_tests.sh integration`
Expected: all passing, no regressions

- [ ] **Step 12: Commit**

```bash
cd backend
git add app/core/platform_services/scadenza_service.py app/core/config.py app/core/platform_services/scadenza_reminder_job.py app/main.py tests/unit/test_core/test_scadenza_service_overdue_reset.py tests/unit/test_core/test_scadenza_reminder_job.py
git commit -m "feat(notifiche): wire scadenzario reminder job into NotificationService"
```

---

### Task 6: Frontend `NotificationBell`

**Files:**
- Modify: `frontend/src/services/api.js`
- Create: `frontend/src/components/Notifications/hooks/useNotifiche.js`
- Create: `frontend/src/components/Notifications/NotificationBell.jsx`
- Create: `frontend/src/components/Notifications/NotificationBell.css`
- Modify: `frontend/src/components/Layout/TopBar.jsx`

**Interfaces:**
- Consumes: `notificheAPI` (new, this task), axios `api` instance already in `services/api.js`.
- Produces: `<NotificationBell />` React component, no props required (mirrors `<ScadenzaBadge autoLoad={true} onClick={...} />` usage shape).

- [ ] **Step 1: Add `notificheAPI` to `services/api.js`**

In `frontend/src/services/api.js`, add near `scadenzeAPI`:

```javascript
export const notificheAPI = {
  list: (params = {}) => api.get('/notifiche', { params }),
  segnaLetta: (id) => api.post(`/notifiche/${id}/segna-letta`),
  segnaTutteLette: () => api.post('/notifiche/segna-tutte-lette'),
  getBadge: () => api.get('/notifiche/badge'),
};
```

- [ ] **Step 2: Write `useNotifiche` hook**

Create `frontend/src/components/Notifications/hooks/useNotifiche.js`:

```javascript
/**
 * useNotifiche Hook - State management for generic core Notifiche.
 */
import { useState, useCallback } from 'react';
import { notificheAPI } from '../../../services/api';

export const useNotifiche = () => {
  const [notifiche, setNotifiche] = useState([]);
  const [badgeCount, setBadgeCount] = useState(0);
  const [loading, setLoading] = useState(false);

  const loadNotifiche = useCallback(async (soloNonLette = false) => {
    setLoading(true);
    try {
      const response = await notificheAPI.list({ solo_non_lette: soloNonLette });
      setNotifiche(response.data);
      return response.data;
    } finally {
      setLoading(false);
    }
  }, []);

  const loadBadge = useCallback(async () => {
    const response = await notificheAPI.getBadge();
    setBadgeCount(response.data.count_non_lette);
    return response.data.count_non_lette;
  }, []);

  const segnaLetta = useCallback(async (id) => {
    await notificheAPI.segnaLetta(id);
    setNotifiche((prev) => prev.map((n) => (n.id === id ? { ...n, letta: true } : n)));
    setBadgeCount((prev) => Math.max(0, prev - 1));
  }, []);

  const segnaTutteLette = useCallback(async () => {
    await notificheAPI.segnaTutteLette();
    setNotifiche((prev) => prev.map((n) => ({ ...n, letta: true })));
    setBadgeCount(0);
  }, []);

  return { notifiche, badgeCount, loading, loadNotifiche, loadBadge, segnaLetta, segnaTutteLette };
};
```

- [ ] **Step 3: Write `NotificationBell`**

Create `frontend/src/components/Notifications/NotificationBell.jsx`:

```javascript
/**
 * NotificationBell - generic core notification bell.
 *
 * Separate from ScadenzaBadge/NotifichePanel (which already show live
 * scadenze in-app): this bell surfaces generic Notifica rows created by
 * NotificationService.notify() from any module. The scadenza reminder
 * job itself sends email-only (see docs/superpowers/plans/2026-09-18-notification-service.md
 * Global Constraints), so this bell stays quiet for scadenze today and
 * lights up once other modules start calling notify() with in-app content.
 */
import { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useNotifiche } from './hooks/useNotifiche';
import { renderIcon } from '../Navigation/iconRegistry.jsx';
import './NotificationBell.css';

const NotificationBell = () => {
  const navigate = useNavigate();
  const { notifiche, badgeCount, loadNotifiche, loadBadge, segnaLetta, segnaTutteLette } = useNotifiche();
  const [open, setOpen] = useState(false);
  const containerRef = useRef(null);

  useEffect(() => {
    loadBadge();
    const interval = setInterval(loadBadge, 60 * 1000);
    return () => clearInterval(interval);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (open) loadNotifiche(false);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open]);

  useEffect(() => {
    const handleClickOutside = (e) => {
      if (containerRef.current && !containerRef.current.contains(e.target)) {
        setOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleItemClick = async (notifica) => {
    if (!notifica.letta) await segnaLetta(notifica.id);
    setOpen(false);
    if (notifica.link_url) navigate(notifica.link_url);
  };

  return (
    <div className="notification-bell" ref={containerRef}>
      <button className="notification-bell__trigger" onClick={() => setOpen((v) => !v)} title="Notifiche">
        {renderIcon('bell', { size: 16 })}
        {badgeCount > 0 && <span className="notification-bell__count">{badgeCount}</span>}
      </button>

      {open && (
        <div className="notification-bell__panel">
          <div className="notification-bell__header">
            <span>Notifiche</span>
            {notifiche.some((n) => !n.letta) && (
              <button className="notification-bell__mark-all" onClick={segnaTutteLette}>
                Segna tutte lette
              </button>
            )}
          </div>
          <div className="notification-bell__body">
            {notifiche.length === 0 && <div className="notification-bell__empty">Nessuna notifica</div>}
            {notifiche.map((n) => (
              <div
                key={n.id}
                className={`notification-bell__item ${n.letta ? '' : 'notification-bell__item--unread'}`}
                onClick={() => handleItemClick(n)}
              >
                <div className="notification-bell__item-title">{n.titolo}</div>
                <div className="notification-bell__item-body">{n.corpo}</div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default NotificationBell;
```

- [ ] **Step 4: Write minimal CSS**

Create `frontend/src/components/Notifications/NotificationBell.css`:

```css
.notification-bell {
  position: relative;
  display: inline-flex;
}

.notification-bell__trigger {
  position: relative;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: none;
  border: none;
  cursor: pointer;
  padding: 6px;
  color: inherit;
}

.notification-bell__count {
  position: absolute;
  top: 0;
  right: 0;
  background: #dc2626;
  color: #fff;
  border-radius: 999px;
  font-size: 10px;
  line-height: 1;
  padding: 2px 5px;
  min-width: 14px;
  text-align: center;
}

.notification-bell__panel {
  position: absolute;
  top: 100%;
  right: 0;
  width: 320px;
  max-height: 400px;
  overflow-y: auto;
  background: var(--color-surface, #fff);
  border: 1px solid var(--color-border, #e5e7eb);
  border-radius: 8px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
  z-index: 1000;
}

.notification-bell__header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 12px;
  border-bottom: 1px solid var(--color-border, #e5e7eb);
  font-weight: 600;
  font-size: 13px;
}

.notification-bell__mark-all {
  background: none;
  border: none;
  color: var(--color-primary, #2563eb);
  cursor: pointer;
  font-size: 12px;
  font-weight: 500;
}

.notification-bell__body {
  display: flex;
  flex-direction: column;
}

.notification-bell__empty {
  padding: 16px 12px;
  font-size: 13px;
  color: var(--color-text-muted, #6b7280);
  text-align: center;
}

.notification-bell__item {
  padding: 10px 12px;
  border-bottom: 1px solid var(--color-border, #f3f4f6);
  cursor: pointer;
}

.notification-bell__item:hover {
  background: var(--color-surface-hover, #f9fafb);
}

.notification-bell__item--unread {
  background: var(--color-surface-highlight, #eff6ff);
}

.notification-bell__item-title {
  font-size: 13px;
  font-weight: 600;
}

.notification-bell__item-body {
  font-size: 12px;
  color: var(--color-text-muted, #6b7280);
  margin-top: 2px;
}
```

- [ ] **Step 5: Mount it in `TopBar.jsx`**

In `frontend/src/components/Layout/TopBar.jsx`, add the import:

```javascript
import NotificationBell from '../Notifications/NotificationBell';
```

and mount it right next to the existing scadenze badge block:

```javascript
        {/* Scadenze Badge */}
        {isAuthenticated && (
          <div className="top-bar-scadenze">
            <ScadenzaBadge
              autoLoad={true}
              onClick={() => setNotificheOpen(!notificheOpen)}
            />
          </div>
        )}

        {isAuthenticated && (
          <div className="top-bar-notifications">
            <NotificationBell />
          </div>
        )}
```

- [ ] **Step 6: Manually verify in the browser**

Run: `cd frontend && npm run dev`, log in, open dev tools network tab, confirm `GET /api/v1/notifiche/badge` fires on load and every 60s, and that clicking the new bell icon (next to the existing scadenze badge) opens an empty "Nessuna notifica" panel (expected — nothing calls `notify()` with in-app content yet in this plan).

- [ ] **Step 7: Run frontend tests**

Run: `cd frontend && npm run test:run`
Expected: no regressions (no existing tests reference `TopBar`'s new import, per the current test file list)

- [ ] **Step 8: Commit**

```bash
cd frontend
git add src/services/api.js src/components/Notifications/ src/components/Layout/TopBar.jsx
git commit -m "feat(notifiche): add NotificationBell to TopBar"
```

---

## Post-plan verification

- [ ] Run `cd backend && ./run_tests.sh ci` (coverage + fail-under=80) and confirm the new files don't drag coverage down.
- [ ] Run `cd /home/htpc/test/gestione-affitti && ./run_all_tests.sh` for the combined backend+frontend suite.
- [ ] Restart the backend (`./start.sh`) once more and tail logs for `[ReminderScheduler]` startup confirmation and no errors from `create_core_tables()`.
