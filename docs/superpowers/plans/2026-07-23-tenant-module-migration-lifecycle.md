# Tenant Module Migration Lifecycle Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix Alembic's core-schema reliability, add per-tenant module version tracking so a mismatch between a tenant's installed tables and the module's current version can be detected, gate the tenant module-management page on that mismatch (disable or force-update), and let "carica dati di esempio" be re-triggered on an already-installed module.

**Architecture:** A new column `installed_version` on `core_tenant_modules` records which module version a tenant's tables are aligned to. `TenantModuleService` sets it on install/sync and `get_tenant_modules()` compares it against the module's current `core_modules.version` to compute a `needs_update` flag returned to the frontend. Two new endpoints expose the existing (already non-destructive) `sync_module_tables_for_tenant` as "force update" and the existing module-install entry point as a standalone "reseed" action. `TenantModules.jsx` renders a restricted action set (disable / force-update only) when `needs_update` is true, and adds a reseed button independent of install state.

**Tech Stack:** FastAPI, SQLAlchemy, Alembic (multi-schema `env.py`), React + Vite, pytest (integration, real Postgres via `db_session` fixture).

## Global Constraints

- Reference analysis doc: `docs/multi-tenancy/MODULE_MIGRATION_LIFECYCLE.md` — every requirement below traces back to it.
- Scope decision (explicit, not in the analysis doc): the "module doesn't start until resolved" rule is enforced as a **UI-level gate on the tenant module-management page only** in this plan — restricting that page's available actions to disable/force-update when `needs_update` is true. It does **not** add backend request-blocking middleware across every module route for mismatched tenants; that is a larger, separate change if wanted later.
- Do NOT touch `Base.metadata.create_all()` usage or attempt to remove it — explicitly out of scope (see conversation: retroactive migration backfill risk).
- Do NOT modify any of the 4 pre-existing December-2025 multi-tenancy docs — only `MODULE_MIGRATION_LIFECYCLE.md` (already written) is current.
- `sync_module_tables_for_tenant` (`backend/app/core/services/tenant_module_service.py:757`) is additive-only (`ADD COLUMN`/`CREATE INDEX IF NOT EXISTS`, never `DROP`) — do not change that non-destructive behavior.
- **Critical:** the existing `db_session` fixture (`backend/tests/fixtures/database.py:20-47`) runs against an **in-memory SQLite** database, not Postgres. `sync_module_tables_for_tenant`/`get_tenant_modules` use raw Postgres-only SQL (`pg_attribute`, `pg_indexes`, `format_type`) that does not exist on SQLite. Do NOT use `db_session`, `client`, or `admin_client` for the new tests in this plan — they are all wired (via the autouse `override_get_db` fixture in `backend/tests/conftest.py:57-70`) to the SQLite session. Instead, construct a real Postgres session directly with `from app.core.database import SessionLocal` (the same sessionmaker the running app uses, bound to `settings.DATABASE_URL`) in each new test file. This is a pre-existing gap in the test infrastructure (no fixture for real-Postgres integration tests exists yet) — out of scope to fix generally; each new test file here works around it locally.
- Do not use `tests/fixtures/tenant.py`'s `test_tenant`/`another_tenant` fixtures — they import `Tenant` from the wrong module (`app.core.auth.models` instead of `app.core.models.tenant`) and use field names (`name`, `is_active`) that don't exist on the current model; this is pre-existing test debt, out of scope to fix here.
- Every test that creates a throwaway Postgres schema must drop it in a `finally`/fixture teardown, regardless of test outcome.

---

### Task 1: Fix stale table reference blocking `alembic -x schema=all`

**Files:**
- Modify: `backend/alembic/versions/2026011501_add_modules_registered.py`

**Interfaces:**
- Consumes: nothing from later tasks.
- Produces: nothing consumed by later tasks (this task is a standalone correctness fix, verified by running Alembic directly, not by other code).

**Context:** `backend/app/core/module_system/models.py:18` declares `Module.__tablename__ = "core_modules"`. The migration below still references the pre-rename name `modules`, which doesn't exist — this doesn't currently error because `Base.metadata.create_all()` already created the columns on `public.core_modules` at some point, masking the fact that replaying this migration from scratch (e.g. against a brand-new empty tenant schema, or a fresh database) fails.

- [ ] **Step 1: Fix the migration**

In `backend/alembic/versions/2026011501_add_modules_registered.py`, find:
```python
def upgrade() -> None:
    op.add_column(
        "modules",
        sa.Column("registered", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )
    op.add_column(
        "modules",
        sa.Column("registered_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("modules", "registered_at")
    op.drop_column("modules", "registered")
```
Replace with:
```python
def upgrade() -> None:
    op.add_column(
        "core_modules",
        sa.Column("registered", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )
    op.add_column(
        "core_modules",
        sa.Column("registered_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("core_modules", "registered_at")
    op.drop_column("core_modules", "registered")
```

- [ ] **Step 2: Verify `schema=all` now completes without error**

Run:
```bash
cd backend && source venv/bin/activate
alembic -x schema=all upgrade head
```
Expected: output ends with `Completed migration for schema: tenant_produzione` (or whichever schemas are registered) and no `ProgrammingError`/`UndefinedTable` traceback. This exercises all 3 currently-registered tenants (`tenant_principale`, `tenant_qa_test`, `tenant_produzione`) plus `public` — all 6 migrations declare `target_schema = "public"`, so for tenant schemas every DDL call is gated to a no-op; only `public` should show real `ALTER`/`CREATE` activity (and only if columns are actually missing there — expect no-ops everywhere since `create_all()` already created everything).

- [ ] **Step 3: Commit**

```bash
cd /home/htpc/test/gestione-affitti
git add backend/alembic/versions/2026011501_add_modules_registered.py
git commit -m "fix(alembic): correct stale 'modules' table reference to 'core_modules'"
```

---

### Task 2: `installed_version` column + backfill migration

**Files:**
- Create: `backend/alembic/versions/2026072301_add_tenant_module_installed_version.py`
- Modify: `backend/app/core/models/tenant.py:62-84` (`TenantModule` class)

**Interfaces:**
- Produces: `TenantModule.installed_version: Optional[str]` (SQLAlchemy column, nullable `String(20)`) — consumed by Task 3's service changes and Task 4's schema/route changes.

- [ ] **Step 1: Write the migration**

Create `backend/alembic/versions/2026072301_add_tenant_module_installed_version.py`:

```python
"""Add installed_version to core_tenant_modules for update-drift tracking.

Revision ID: 2026072301
Revises: 2026013101
Create Date: 2026-07-23 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "2026072301"
down_revision = "2026013101"
branch_labels = None
depends_on = None

target_schema = "public"


def upgrade() -> None:
    op.add_column(
        "core_tenant_modules",
        sa.Column("installed_version", sa.String(20), nullable=True),
    )
    # Backfill: this column didn't exist before, so there is no real drift
    # yet for modules already installed on a tenant — treat them as aligned
    # with the module's current version as of this migration.
    op.execute("""
        UPDATE core_tenant_modules tm
        SET installed_version = m.version
        FROM core_modules m
        WHERE m.technical_name = tm.module_id
    """)


def downgrade() -> None:
    op.drop_column("core_tenant_modules", "installed_version")
```

- [ ] **Step 2: Add the column to the SQLAlchemy model**

In `backend/app/core/models/tenant.py`, find:
```python
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("public.core_tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    module_id = Column(String(50), nullable=False, index=True)  # e.g., "immobili", "affitti_lungo"
    enabled = Column(Boolean, default=True, nullable=False, index=True)
    installed_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    disabled_at = Column(DateTime, nullable=True)
    config = deferred(Column(JSONB, nullable=True))
```
Replace with:
```python
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("public.core_tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    module_id = Column(String(50), nullable=False, index=True)  # e.g., "immobili", "affitti_lungo"
    enabled = Column(Boolean, default=True, nullable=False, index=True)
    installed_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    disabled_at = Column(DateTime, nullable=True)
    installed_version = Column(String(20), nullable=True)
    config = deferred(Column(JSONB, nullable=True))
```

- [ ] **Step 3: Run the migration and verify**

Run:
```bash
cd backend && source venv/bin/activate
alembic upgrade head
```
Expected: no errors; revision `2026072301` becomes current head.

Verify the backfill with a direct query:
```bash
PGPASSWORD=affitti psql -h localhost -p 5433 -U affitti -d gestione_affitti -c \
  "SELECT tenant_id, module_id, installed_version FROM public.core_tenant_modules ORDER BY tenant_id, module_id;"
```
Expected: every existing row (tenant 1 and tenant 3, 6 modules each, per the current registered state) has a non-null `installed_version` matching that module's current version in `core_modules`.

- [ ] **Step 4: Commit**

```bash
cd /home/htpc/test/gestione-affitti
git add backend/alembic/versions/2026072301_add_tenant_module_installed_version.py backend/app/core/models/tenant.py
git commit -m "feat(tenant-modules): add installed_version column with backfill migration"
```

---

### Task 3: Service layer — set, bump, and compare `installed_version`

**Files:**
- Modify: `backend/app/core/services/tenant_module_service.py`
- Test: `backend/tests/integration/test_tenant_module_version.py`

**Interfaces:**
- Consumes: `TenantModule.installed_version` (Task 2).
- Produces:
  - `TenantModuleService._register_module(tenant_id: int, module_id: str, db: Session, version: Optional[str] = None) -> TenantModule` (signature change: new optional `version` param, sets `installed_version` when provided)
  - `TenantModuleService.reseed_test_data_for_tenant(tenant_id: int, module_id: str, db: Session) -> bool` (new method)
  - `get_tenant_modules()` return dicts now include `"installed_version": <str|None>` and `"needs_update": <bool>` keys — consumed by Task 4's schema and Task 5's frontend.

- [ ] **Step 1: Write the failing tests**

Create `backend/tests/integration/test_tenant_module_version.py`:

```python
"""
Integration tests for per-tenant module version tracking.

Uses a real Postgres session (the same SessionLocal the running app uses,
bound to settings.DATABASE_URL) rather than the SQLite-backed db_session
fixture — sync_module_tables_for_tenant/get_tenant_modules run raw
Postgres-only SQL (pg_attribute, pg_indexes) that does not exist on
SQLite. A throwaway tenant schema is created and dropped per test,
regardless of outcome.
"""
import pytest
from sqlalchemy import text

from app.core.database import SessionLocal
from app.core.models.tenant import Tenant, TenantModule
from app.core.module_system.models import Module
from app.core.services.tenant_module_service import TenantModuleService

TEST_SCHEMA = "tenant_pytest_version_check"


@pytest.fixture
def pg_session():
    """A real session against the actual dev Postgres database."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture
def throwaway_tenant(pg_session):
    """A real tenant row pointing at a throwaway schema name. The schema
    itself is never physically CREATEd — sufficient for version-tracking
    logic, which reads/writes core_tenant_modules and core_modules only."""
    tenant = Tenant(
        schema_name=TEST_SCHEMA,
        nome_display="Pytest Version Check",
        active=True,
    )
    pg_session.add(tenant)
    pg_session.commit()
    pg_session.refresh(tenant)
    try:
        yield tenant
    finally:
        pg_session.query(TenantModule).filter_by(tenant_id=tenant.id).delete()
        pg_session.query(Tenant).filter_by(id=tenant.id).delete()
        pg_session.commit()


@pytest.mark.tenant
def test_register_module_sets_installed_version(pg_session, throwaway_tenant):
    module = pg_session.query(Module).filter_by(technical_name="esempio_componenti").first()
    assert module is not None, "esempio_componenti must be registered for this test to run"

    TenantModuleService._register_module(throwaway_tenant.id, "esempio_componenti", pg_session, version=module.version)

    tm = pg_session.query(TenantModule).filter_by(
        tenant_id=throwaway_tenant.id, module_id="esempio_componenti"
    ).first()
    assert tm is not None
    assert tm.installed_version == module.version


@pytest.mark.tenant
def test_needs_update_false_when_versions_match(pg_session, throwaway_tenant):
    module = pg_session.query(Module).filter_by(technical_name="esempio_componenti").first()
    TenantModuleService._register_module(throwaway_tenant.id, "esempio_componenti", pg_session, version=module.version)

    modules_payload = TenantModuleService.get_tenant_modules(throwaway_tenant.id, pg_session)
    entry = next(m for m in modules_payload if m["module_id"] == "esempio_componenti")
    assert entry["installed_version"] == module.version
    assert entry["needs_update"] is False


@pytest.mark.tenant
def test_needs_update_true_when_versions_differ(pg_session, throwaway_tenant):
    module = pg_session.query(Module).filter_by(technical_name="esempio_componenti").first()
    TenantModuleService._register_module(throwaway_tenant.id, "esempio_componenti", pg_session, version="0000000000")

    modules_payload = TenantModuleService.get_tenant_modules(throwaway_tenant.id, pg_session)
    entry = next(m for m in modules_payload if m["module_id"] == "esempio_componenti")
    assert entry["installed_version"] == "0000000000"
    assert entry["needs_update"] is True


@pytest.mark.tenant
def test_needs_update_false_when_installed_version_unknown(pg_session, throwaway_tenant):
    """A row with installed_version still NULL (shouldn't happen after the
    Task 2 backfill, but defensively) must not be treated as needing an
    update — there's nothing to compare against."""
    module = pg_session.query(Module).filter_by(technical_name="esempio_componenti").first()
    TenantModuleService._register_module(throwaway_tenant.id, "esempio_componenti", pg_session, version=None)

    modules_payload = TenantModuleService.get_tenant_modules(throwaway_tenant.id, pg_session)
    entry = next(m for m in modules_payload if m["module_id"] == "esempio_componenti")
    assert entry["installed_version"] is None
    assert entry["needs_update"] is False
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `cd backend && source venv/bin/activate && pytest tests/integration/test_tenant_module_version.py -v -m tenant`
Expected: FAIL — `_register_module()` doesn't accept a `version` keyword argument yet (`TypeError`), and `needs_update`/`installed_version` keys don't exist in the payload dicts.

- [ ] **Step 3: Update `_register_module` to accept and store version**

In `backend/app/core/services/tenant_module_service.py`, find (around line 732):
```python
    def _register_module(tenant_id: int, module_id: str, db: Session) -> TenantModule:
        """Register or re-enable a module for a tenant."""
        existing = db.query(TenantModule).filter_by(
            tenant_id=tenant_id,
            module_id=module_id
        ).first()

        if existing:
            existing.enabled = True
            existing.disabled_at = None
        else:
            tenant_module = TenantModule(
                tenant_id=tenant_id,
                module_id=module_id,
                enabled=True
            )
            if TenantModuleService._config_column_exists(db):
                tenant_module.config = {}
            db.add(tenant_module)
            existing = tenant_module

        db.commit()
        return existing
```
Replace with:
```python
    def _register_module(tenant_id: int, module_id: str, db: Session, version: Optional[str] = None) -> TenantModule:
        """Register or re-enable a module for a tenant."""
        existing = db.query(TenantModule).filter_by(
            tenant_id=tenant_id,
            module_id=module_id
        ).first()

        if existing:
            existing.enabled = True
            existing.disabled_at = None
        else:
            tenant_module = TenantModule(
                tenant_id=tenant_id,
                module_id=module_id,
                enabled=True
            )
            if TenantModuleService._config_column_exists(db):
                tenant_module.config = {}
            db.add(tenant_module)
            existing = tenant_module

        if version is not None:
            existing.installed_version = version

        db.commit()
        return existing
```

- [ ] **Step 4: Pass the module's current version at every `_register_module` call site**

In `backend/app/core/services/tenant_module_service.py`, find (around line 579, inside `install_module_for_tenant`, after table verification):
```python
        # 4. Register module as installed
        TenantModuleService._register_module(tenant_id, module_id, db)

        return results
```
Replace with:
```python
        # 4. Register module as installed
        TenantModuleService._register_module(tenant_id, module_id, db, version=module_record.version)

        return results
```

Find (around line 798, at the end of `sync_module_tables_for_tenant`):
```python
        # Register module
        TenantModuleService._register_module(tenant_id, module_id, db)
```
Replace with:
```python
        # Register module (bumps installed_version to the module's current version)
        TenantModuleService._register_module(tenant_id, module_id, db, version=module_record.version)
```

- [ ] **Step 5: Add `reseed_test_data_for_tenant`**

In `backend/app/core/services/tenant_module_service.py`, add this new method immediately after `sync_module_tables_for_tenant` (after the closing of the method that ends at line 799 in its original form — place it before `_sync_table_columns`):

```python
    @staticmethod
    def reseed_test_data_for_tenant(tenant_id: int, module_id: str, db: Session) -> bool:
        """
        Re-run a module's install entry point with seed_test_data=True for a
        tenant where the module is already installed. Does not touch table
        structure — only re-invokes whatever seeding logic the module's
        install() function runs when seed_test_data is True.
        """
        tenant = db.query(Tenant).get(tenant_id)
        if not tenant:
            raise ValueError(f"Tenant {tenant_id} not found")

        module_record = db.query(Module).filter(Module.technical_name == module_id).first()
        if not module_record:
            raise ValueError(f"Unknown module: {module_id}")

        return TenantModuleService._run_module_install(
            module_record,
            tenant_id,
            tenant.schema_name,
            db,
            seed_test_data=True,
        )
```

- [ ] **Step 6: Add `installed_version`/`needs_update` to `get_tenant_modules`**

In `backend/app/core/services/tenant_module_service.py`, find (around line 1129, inside the `for module_id in all_module_ids:` loop of `get_tenant_modules`):
```python
            modules_payload.append({
                "module_id": module_id,
                "name": (module_record.name if module_record else module_id.replace('_', ' ').title()),
                "version": module_record.version if module_record else None,
                "description": (module_record.description or (manifest or {}).get("description", "")) if module_record else "",
                "author": (manifest or {}).get("author") if module_record else None,
                "icon": (module_record.icon or (manifest or {}).get("icon")) if module_record else None,
                "category": (module_record.category or (manifest or {}).get("category") or "other") if module_record else "other",
                "dependencies": (manifest or {}).get("dependencies", []) if module_record else [],
                "enabled": effective_enabled,
                "needs_install": needs_install,
                "installed_at": module_map[module_id].installed_at.isoformat() if module_id in module_map else None,
                "tenant_tables": tenant_tables,
                "table_count": len(tenant_tables),
                "config": module_map[module_id].config if has_config and module_id in module_map else {}
            })
```
Replace with:
```python
            installed_version = module_map[module_id].installed_version if module_id in module_map else None
            current_version = module_record.version if module_record else None
            needs_update = bool(
                installed_version is not None
                and current_version is not None
                and installed_version != current_version
            )

            modules_payload.append({
                "module_id": module_id,
                "name": (module_record.name if module_record else module_id.replace('_', ' ').title()),
                "version": current_version,
                "description": (module_record.description or (manifest or {}).get("description", "")) if module_record else "",
                "author": (manifest or {}).get("author") if module_record else None,
                "icon": (module_record.icon or (manifest or {}).get("icon")) if module_record else None,
                "category": (module_record.category or (manifest or {}).get("category") or "other") if module_record else "other",
                "dependencies": (manifest or {}).get("dependencies", []) if module_record else [],
                "enabled": effective_enabled,
                "needs_install": needs_install,
                "installed_at": module_map[module_id].installed_at.isoformat() if module_id in module_map else None,
                "installed_version": installed_version,
                "needs_update": needs_update,
                "tenant_tables": tenant_tables,
                "table_count": len(tenant_tables),
                "config": module_map[module_id].config if has_config and module_id in module_map else {}
            })
```

- [ ] **Step 7: Run the tests to verify they pass**

Run: `cd backend && source venv/bin/activate && pytest tests/integration/test_tenant_module_version.py -v -m tenant`
Expected: PASS (all 4 tests).

- [ ] **Step 8: Commit**

```bash
cd /home/htpc/test/gestione-affitti
git add backend/app/core/services/tenant_module_service.py backend/tests/integration/test_tenant_module_version.py
git commit -m "feat(tenant-modules): track installed_version, compute needs_update, add reseed method"
```

---

### Task 4: API — force-update and reseed endpoints, schema fields

**Files:**
- Modify: `backend/app/core/schemas/tenant.py:81-96` (`TenantModuleResponse`)
- Modify: `backend/app/core/routes/tenants.py`
- Test: `backend/tests/integration/test_tenant_module_routes.py`

**Interfaces:**
- Consumes: `TenantModuleService.get_tenant_modules()` (now returns `installed_version`/`needs_update`), `TenantModuleService.sync_module_tables_for_tenant()` (Task 3, unchanged signature, now bumps version), `TenantModuleService.reseed_test_data_for_tenant()` (Task 3).
- Produces: `POST /tenants/{tenant_id}/modules/{module_id}/force-update`, `POST /tenants/{tenant_id}/modules/{module_id}/reseed` — consumed by Task 5's frontend.

**Note on testing approach:** the app's `client`/`admin_client` TestClient fixtures are wired (via `backend/tests/conftest.py`'s autouse `override_get_db`) to the SQLite `db_session`, which cannot run the Postgres-only SQL inside the services these routes call (see Task 3's note). Route logic here is a thin pass-through to already-tested service methods, so this task verifies the two routes are wired correctly with a direct Python-level test of the route functions (bypassing HTTP/TestClient) plus a manual curl check against the real running dev server for the actual HTTP contract.

- [ ] **Step 1: Write the failing test**

Create `backend/tests/integration/test_tenant_module_routes.py`:

```python
"""
Tests that the force-update and reseed route functions are wired to the
correct service methods and return the expected response shape. Calls the
route functions directly (not via TestClient/HTTP) against a real Postgres
session, for the same reason test_tenant_module_version.py does — the
underlying service calls raw Postgres-only SQL that SQLite can't run.
"""
import pytest

from app.core.database import SessionLocal
from app.core.models.tenant import Tenant, TenantModule
from app.core.auth.models import User
from app.core.module_system.models import Module
from app.core.services.tenant_module_service import TenantModuleService
from app.core.routes.tenants import force_update_module, reseed_module_test_data

TEST_SCHEMA = "tenant_pytest_route_check"


@pytest.fixture
def pg_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture
def throwaway_tenant(pg_session):
    tenant = Tenant(
        schema_name=TEST_SCHEMA,
        nome_display="Pytest Route Check",
        active=True,
    )
    pg_session.add(tenant)
    pg_session.commit()
    pg_session.refresh(tenant)
    try:
        yield tenant
    finally:
        pg_session.query(TenantModule).filter_by(tenant_id=tenant.id).delete()
        pg_session.query(Tenant).filter_by(id=tenant.id).delete()
        pg_session.commit()


@pytest.fixture
def superuser(pg_session):
    """Reuse the existing admin superuser (id=1) already present in the dev DB."""
    user = pg_session.query(User).filter_by(is_superuser=True).first()
    assert user is not None, "a superuser must exist in the dev DB for this test"
    return user


@pytest.mark.tenant
def test_force_update_route_bumps_installed_version(pg_session, throwaway_tenant, superuser):
    module = pg_session.query(Module).filter_by(technical_name="esempio_componenti").first()
    TenantModuleService._register_module(throwaway_tenant.id, "esempio_componenti", pg_session, version="0000000000")

    result = force_update_module(throwaway_tenant.id, "esempio_componenti", current_user=superuser, db=pg_session)
    assert result["status"] == "updated"

    pg_session.expire_all()
    tm = pg_session.query(TenantModule).filter_by(
        tenant_id=throwaway_tenant.id, module_id="esempio_componenti"
    ).first()
    assert tm.installed_version == module.version


@pytest.mark.tenant
def test_reseed_route_returns_success(pg_session, throwaway_tenant, superuser):
    module = pg_session.query(Module).filter_by(technical_name="esempio_componenti").first()
    TenantModuleService._register_module(throwaway_tenant.id, "esempio_componenti", pg_session, version=module.version)

    result = reseed_module_test_data(throwaway_tenant.id, "esempio_componenti", current_user=superuser, db=pg_session)
    assert result["status"] == "reseeded"
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `cd backend && source venv/bin/activate && pytest tests/integration/test_tenant_module_routes.py -v -m tenant`
Expected: FAIL — `force_update_module`/`reseed_module_test_data` don't exist yet in `app.core.routes.tenants` (`ImportError`).

- [ ] **Step 3: Add the two new fields to `TenantModuleResponse`**

In `backend/app/core/schemas/tenant.py`, find:
```python
class TenantModuleResponse(BaseModel):
    """Schema for tenant module status."""
    module_id: str
    name: str
    version: Optional[str] = None
    description: Optional[str] = None
    author: Optional[str] = None
    icon: Optional[str] = None
    category: Optional[str] = None
    dependencies: List[str] = Field(default_factory=list)
    enabled: bool
    needs_install: bool = False
    installed_at: Optional[str]  # ISO format string
    tenant_tables: List[str] = Field(default_factory=list)
    table_count: int
    config: Optional[Dict[str, Any]] = None
```
Replace with:
```python
class TenantModuleResponse(BaseModel):
    """Schema for tenant module status."""
    module_id: str
    name: str
    version: Optional[str] = None
    description: Optional[str] = None
    author: Optional[str] = None
    icon: Optional[str] = None
    category: Optional[str] = None
    dependencies: List[str] = Field(default_factory=list)
    enabled: bool
    needs_install: bool = False
    installed_at: Optional[str]  # ISO format string
    installed_version: Optional[str] = None
    needs_update: bool = False
    tenant_tables: List[str] = Field(default_factory=list)
    table_count: int
    config: Optional[Dict[str, Any]] = None
```

- [ ] **Step 4: Add the two new routes**

In `backend/app/core/routes/tenants.py`, find the existing `disable_module` route (around line 389-409) and add the two new routes immediately after it:
```python
@router.post("/{tenant_id}/modules/{module_id}/disable")
def disable_module(
    tenant_id: int,
    module_id: str,
    drop_tables: bool = False,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Disable module (keep data) - PLATFORM ADMIN ONLY.
    """
    ensure_tenant_admin_access(tenant_id, current_user, db)
    drop_result = TenantModuleService.disable_module_for_tenant(
        tenant_id, module_id, db, drop_tables=drop_tables
    )
    return {
        "status": "disabled",
        "module_id": module_id,
        "tables_dropped": drop_result.get("dropped", []),
        "tables_failed": drop_result.get("failed", []),
    }


@router.post("/{tenant_id}/modules/{module_id}/force-update")
def force_update_module(
    tenant_id: int,
    module_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Force-sync a tenant's module tables to match the module's current
    version - PLATFORM ADMIN ONLY. Non-destructive: only adds missing
    columns/indexes, never drops data.
    """
    ensure_tenant_admin_access(tenant_id, current_user, db)
    try:
        TenantModuleService.sync_module_tables_for_tenant(tenant_id, module_id, db)
        return {"status": "updated", "module_id": module_id}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Update failed: {str(e)}")


@router.post("/{tenant_id}/modules/{module_id}/reseed")
def reseed_module_test_data(
    tenant_id: int,
    module_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Re-run a module's sample-data seeding for a tenant where it is already
    installed - PLATFORM ADMIN ONLY.
    """
    ensure_tenant_admin_access(tenant_id, current_user, db)
    try:
        success = TenantModuleService.reseed_test_data_for_tenant(tenant_id, module_id, db)
        if not success:
            raise HTTPException(status_code=500, detail="Reseed failed. Check server logs.")
        return {"status": "reseeded", "module_id": module_id}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
```

- [ ] **Step 5: Run the test to verify it passes**

Run: `cd backend && source venv/bin/activate && pytest tests/integration/test_tenant_module_routes.py -v -m tenant`
Expected: PASS (both tests).

- [ ] **Step 6: Manual HTTP contract check against the running dev server**

With the backend dev server running (`./start.sh` in `backend/`, or already running), get an admin token and exercise both routes for real over HTTP:

```bash
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"changeme123"}' | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

# Replace 1 with a real tenant_id that has esempio_componenti enabled
curl -s -X POST http://localhost:8000/api/v1/tenants/1/modules/esempio_componenti/force-update \
  -H "Authorization: Bearer $TOKEN" -w "\nHTTP %{http_code}\n"

curl -s -X POST http://localhost:8000/api/v1/tenants/1/modules/esempio_componenti/reseed \
  -H "Authorization: Bearer $TOKEN" -w "\nHTTP %{http_code}\n"
```
Expected: both return HTTP 200 with `{"status": "updated", ...}` / `{"status": "reseeded", ...}`.

- [ ] **Step 7: Commit**

```bash
cd /home/htpc/test/gestione-affitti
git add backend/app/core/schemas/tenant.py backend/app/core/routes/tenants.py backend/tests/integration/test_tenant_module_routes.py
git commit -m "feat(tenant-modules): add force-update and reseed API endpoints"
```

---

### Task 5: Frontend — update gate and standalone reseed action

**Files:**
- Modify: `frontend/src/pages/Tenant/TenantModules.jsx`
- Modify: `frontend/src/pages/Tenant/TenantModules.css`

**Interfaces:**
- Consumes: `module.needs_update` and `module.installed_version` (Task 3/4, present on every object in the array returned by `GET /tenants/{id}/modules`), `POST /tenants/{id}/modules/{module_id}/force-update`, `POST /tenants/{id}/modules/{module_id}/reseed` (Task 4).

- [ ] **Step 1: Add the two new API calls**

In `frontend/src/pages/Tenant/TenantModules.jsx`, find:
```jsx
  const openConfigEditor = (module) => {
```
Insert immediately before it:
```jsx
  const forceUpdateModule = async (moduleId) => {
    if (!currentTenant) return;
    try {
      const token = localStorage.getItem('access_token');
      await axios.post(
        `${API_BASE_URL}/tenants/${currentTenant.id}/modules/${moduleId}/force-update`,
        {},
        { headers: { Authorization: `Bearer ${token}` } }
      );
      await loadTenantModules(currentTenant.id);
      await loadMenu();
    } catch (err) {
      alert(`Errore aggiornamento: ${err.response?.data?.detail || 'Operazione fallita'}`);
    }
  };

  const reseedModule = async (moduleId) => {
    if (!currentTenant) return;
    try {
      const token = localStorage.getItem('access_token');
      await axios.post(
        `${API_BASE_URL}/tenants/${currentTenant.id}/modules/${moduleId}/reseed`,
        {},
        { headers: { Authorization: `Bearer ${token}` } }
      );
      alert('Dati di esempio caricati.');
    } catch (err) {
      alert(`Errore caricamento dati di esempio: ${err.response?.data?.detail || 'Operazione fallita'}`);
    }
  };

```

- [ ] **Step 2: Show a version-mismatch badge**

In `frontend/src/pages/Tenant/TenantModules.jsx`, find:
```jsx
                        <div className="tenant-module-status">
                          <span className={`status-badge ${module.enabled ? 'active' : 'inactive'}`}>
                            {module.enabled ? 'Attivo' : 'Disattivo'}
                          </span>
                        </div>
```
Replace with:
```jsx
                        <div className="tenant-module-status">
                          <span className={`status-badge ${module.enabled ? 'active' : 'inactive'}`}>
                            {module.enabled ? 'Attivo' : 'Disattivo'}
                          </span>
                          {module.needs_update && (
                            <span className="status-badge needs-update">
                              Aggiornamento richiesto
                            </span>
                          )}
                        </div>
```

- [ ] **Step 3: Gate the action row when `needs_update` is true**

In `frontend/src/pages/Tenant/TenantModules.jsx`, find the whole `<div className="tenant-module-actions">` block:
```jsx
                        <div className="tenant-module-actions">
                          {!module.enabled && (
                            <label className="tenant-module-testdata-toggle">
                              <input
                                type="checkbox"
                                checked={!!seedTestDataByModule[module.module_id]}
                                onChange={(event) =>
                                  setSeedTestDataByModule((prev) => ({
                                    ...prev,
                                    [module.module_id]: event.target.checked,
                                  }))
                                }
                              />
                              Carica dati di test
                            </label>
                          )}
                          {module.enabled && (
                            <label className="tenant-module-drop-toggle">
                              <input
                                type="checkbox"
                                checked={!!dropTablesByModule[module.module_id]}
                                onChange={(event) =>
                                  setDropTablesByModule((prev) => ({
                                    ...prev,
                                    [module.module_id]: event.target.checked,
                                  }))
                                }
                              />
                              Cancella tabelle tenant
                            </label>
                          )}
                          <button
                            className={`btn btn-sm ${module.enabled ? 'btn-outline' : 'btn-primary'}`}
                            onClick={() => toggleTenantModule(
                              module.module_id,
                              module.enabled,
                              !!dropTablesByModule[module.module_id],
                              !!seedTestDataByModule[module.module_id]
                            )}
                          >
                            {module.enabled ? 'Disabilita' : 'Abilita'}
                          </button>
                          <button
                            className="btn btn-sm btn-secondary"
                            onClick={() => openConfigEditor(module)}
                          >
                            Config
                          </button>
                        </div>
```
Replace with:
```jsx
                        <div className="tenant-module-actions">
                          {module.needs_update ? (
                            <>
                              <p className="tenant-module-update-notice">
                                Le tabelle di questo tenant non sono allineate alla versione
                                corrente del modulo ({module.installed_version} → {module.version}).
                                Disabilita il modulo oppure forza l'aggiornamento delle tabelle.
                              </p>
                              <button
                                className="btn btn-sm btn-outline"
                                onClick={() => toggleTenantModule(module.module_id, true, false, false)}
                              >
                                Disabilita
                              </button>
                              <button
                                className="btn btn-sm btn-primary"
                                onClick={() => forceUpdateModule(module.module_id)}
                              >
                                Forza aggiornamento
                              </button>
                            </>
                          ) : (
                            <>
                              {!module.enabled && (
                                <label className="tenant-module-testdata-toggle">
                                  <input
                                    type="checkbox"
                                    checked={!!seedTestDataByModule[module.module_id]}
                                    onChange={(event) =>
                                      setSeedTestDataByModule((prev) => ({
                                        ...prev,
                                        [module.module_id]: event.target.checked,
                                      }))
                                    }
                                  />
                                  Carica dati di test
                                </label>
                              )}
                              {module.enabled && (
                                <label className="tenant-module-drop-toggle">
                                  <input
                                    type="checkbox"
                                    checked={!!dropTablesByModule[module.module_id]}
                                    onChange={(event) =>
                                      setDropTablesByModule((prev) => ({
                                        ...prev,
                                        [module.module_id]: event.target.checked,
                                      }))
                                    }
                                  />
                                  Cancella tabelle tenant
                                </label>
                              )}
                              <button
                                className={`btn btn-sm ${module.enabled ? 'btn-outline' : 'btn-primary'}`}
                                onClick={() => toggleTenantModule(
                                  module.module_id,
                                  module.enabled,
                                  !!dropTablesByModule[module.module_id],
                                  !!seedTestDataByModule[module.module_id]
                                )}
                              >
                                {module.enabled ? 'Disabilita' : 'Abilita'}
                              </button>
                              <button
                                className="btn btn-sm btn-secondary"
                                onClick={() => openConfigEditor(module)}
                              >
                                Config
                              </button>
                              {module.enabled && (
                                <button
                                  className="btn btn-sm btn-secondary"
                                  onClick={() => reseedModule(module.module_id)}
                                >
                                  Carica dati di esempio
                                </button>
                              )}
                            </>
                          )}
                        </div>
```

- [ ] **Step 4: Add CSS for the new badge and notice**

In `frontend/src/pages/Tenant/TenantModules.css`, find:
```css
.status-badge.inactive {
```
and add immediately before that rule (i.e. after whatever rule precedes it — insert as a new rule block anywhere in the `.status-badge` group):
```css
.status-badge.needs-update {
  background-color: #fff3cd;
  color: #856404;
  margin-left: 6px;
}

.tenant-module-update-notice {
  font-size: 13px;
  color: #856404;
  background-color: #fff3cd;
  padding: 8px 10px;
  border-radius: 4px;
  margin: 0 0 8px 0;
  width: 100%;
}
```

- [ ] **Step 5: Manual verification**

With the frontend dev server running (`npm run dev` in `frontend/`), and the backend running with Task 1-4 applied:

1. Find the module's real current version (the source of truth for the revert in step 5):
   ```bash
   grep "version" backend/modules/esempio_componenti/__manifest__.py
   ```
   Note the value (e.g. `'2026010101'`) — call it `REAL_VERSION` below.
2. Temporarily bump the module's version in the core registry to simulate drift:
   ```bash
   PGPASSWORD=affitti psql -h localhost -p 5433 -U affitti -d gestione_affitti -c \
     "UPDATE public.core_modules SET version = '9999999999' WHERE technical_name = 'esempio_componenti';"
   ```
3. Open `/tenant/modules` (or wherever `TenantModules` is routed) for a tenant that has `esempio_componenti` enabled (e.g. tenant Principale). Expected: the card shows the "Aggiornamento richiesto" badge, the notice text, and only the Disabilita/Forza aggiornamento buttons.
4. Click "Forza aggiornamento". Expected: request succeeds, page reloads modules, badge disappears, normal actions (Config, Carica dati di esempio) reappear.
5. Restore the module's real version (force-update just wrote `installed_version = '9999999999'` on the tenant row too, so both need resetting to `REAL_VERSION` from step 1):
   ```bash
   PGPASSWORD=affitti psql -h localhost -p 5433 -U affitti -d gestione_affitti -c \
     "UPDATE public.core_modules SET version = 'REAL_VERSION' WHERE technical_name = 'esempio_componenti';
      UPDATE public.core_tenant_modules SET installed_version = 'REAL_VERSION' WHERE module_id = 'esempio_componenti';"
   ```
   (substitute the actual value noted in step 1 for `REAL_VERSION`)
6. Click "Carica dati di esempio" on an already-enabled module. Expected: no error, alert confirms data loaded.

- [ ] **Step 6: Commit**

```bash
cd /home/htpc/test/gestione-affitti
git add frontend/src/pages/Tenant/TenantModules.jsx frontend/src/pages/Tenant/TenantModules.css
git commit -m "feat(tenant-modules): add version-mismatch gate and standalone reseed action"
```

---

### Task 6: Full verification pass

**Files:** none created/modified — verification only.

- [ ] **Step 1: Run the new and existing backend integration tests**

Run: `cd backend && source venv/bin/activate && pytest tests/integration/test_tenant_module_version.py tests/integration/test_tenant_module_routes.py -v -m tenant`
Expected: all pass (4 + 2 = 6 tests).

- [ ] **Step 2: Run the full backend suite to check for regressions**

Run: `cd backend && source venv/bin/activate && ./run_tests.sh` (or `pytest` directly if the script requires flags not relevant here)
Expected: no new failures introduced by this plan's changes (pre-existing unrelated failures, if any, are out of scope — note them, don't fix them here).

- [ ] **Step 3: Run `alembic -x schema=all upgrade head` one more time from a clean state**

Run:
```bash
cd backend && source venv/bin/activate
alembic -x schema=all upgrade head
```
Expected: completes cleanly for `public`, `tenant_principale`, `tenant_qa_test`, `tenant_produzione` — no errors. This is the concrete proof that Task 1's fix plus Task 2's new migration both replay correctly end-to-end.

- [ ] **Step 4: Frontend build check**

Run: `cd frontend && npm run build`
Expected: succeeds with no errors.

- [ ] **Step 5: Report completion**

Summarize to the user: all 6 tasks done, test counts, and remind them that backend request-level enforcement (blocking a mismatched module's actual routes, not just the management page) was explicitly scoped out — flagged as a possible future follow-up, not done here.
