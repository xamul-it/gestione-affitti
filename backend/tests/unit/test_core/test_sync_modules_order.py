"""scripts/sync_modules.py: catalogs are synced before the module migrations."""
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "scripts"))
import sync_modules  # noqa: E402

pytestmark = pytest.mark.unit


class _Result(list):
    def all(self):
        return list(self)


class _Conn:
    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def execute(self, stmt, params=None):
        sql = str(stmt)
        if "FROM public.core_modules" in sql:
            return _Result([("modx", "/tmp/modx", "active")])
        if "FROM public.core_tenants" in sql:
            return _Result([("tenant_x", 1)])
        if "core_tenant_modules" in sql:
            return _Result([])
        return _Result([("tenant_x", "alembic_version_mx")])

    def begin(self):
        return self


class _Engine(_Conn):
    def connect(self):
        return _Conn()


class _Session:
    def __init__(self, *a, **k):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def execute(self, *a, **k):
        pass

    def commit(self):
        pass

    def rollback(self):
        pass


def test_sync_tipi_prima_delle_migrazioni(monkeypatch):
    calls = []
    manifest = {"migrations_path": "m", "module_short_code": "mx", "schema_target": "tenant"}
    report = SimpleNamespace(creati=[], aggiornati=[], disattivati=[], errori=[])
    monkeypatch.setattr(sync_modules, "create_engine", lambda *a, **k: _Engine())
    monkeypatch.setattr(sync_modules, "Session", _Session, raising=False)
    monkeypatch.setattr("sqlalchemy.orm.Session", _Session)
    monkeypatch.setattr(sync_modules.Path, "exists", lambda self: True)
    monkeypatch.setattr(sync_modules, "load_manifest", lambda name: manifest)
    monkeypatch.setattr(sync_modules, "load_all_models", lambda order: None)
    monkeypatch.setattr(sync_modules, "run_module_alembic",
                        lambda *a, **k: calls.append("run_module_alembic") or True)
    monkeypatch.setattr(sync_modules, "sync_document_types",
                        lambda *a, **k: calls.append("sync_document_types") or report)
    monkeypatch.setattr(sync_modules, "sync_relation_types",
                        lambda *a, **k: calls.append("sync_relation_types") or report)
    monkeypatch.setattr(sys, "argv", ["sync_modules.py"])
    monkeypatch.setattr(sync_modules, "call_seed", lambda *a, **k: None)

    sync_modules.main()

    assert "run_module_alembic" in calls
    first_migration = calls.index("run_module_alembic")
    assert calls.index("sync_document_types") < first_migration
    assert calls.index("sync_relation_types") < first_migration
