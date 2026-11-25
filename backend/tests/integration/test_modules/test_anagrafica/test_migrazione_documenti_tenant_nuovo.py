"""
A new tenant gets the document tables under their core_* names with the
current columns: anagrafica_italiana creates them as anag_* after the core
chain already ran its rename (2026092102) and history columns (2026110902).
Found by scripts/tenant_prova.py nuovo.
"""
import importlib.util
from pathlib import Path

import pytest
from sqlalchemy import text

pytestmark = pytest.mark.integration

MIGRAZIONE = (Path(__file__).resolve().parents[4] / "modules" / "anagrafica_italiana" / "migrations"
              / "versions" / "2026112501_documenti_core_tenant_nuovo.py")
SCHEMA = "tenant_pytest_documenti_nuovo"


class _Op:
    def __init__(self, conn):
        self.conn = conn

    def execute(self, sql):
        return self.conn.execute(sql)

    def get_bind(self):
        return self.conn


def _carica():
    spec = importlib.util.spec_from_file_location("migr_doc_nuovo", MIGRAZIONE)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


def _tabelle(conn):
    return {r[0] for r in conn.execute(text(
        "SELECT table_name FROM information_schema.tables WHERE table_schema = :s"), {"s": SCHEMA})}


def test_tabelle_anag_diventano_core_con_le_colonne_attuali(db_session):
    conn = db_session.connection()
    conn.execute(text(f"CREATE SCHEMA {SCHEMA}"))
    conn.execute(text(f"SET search_path TO {SCHEMA}, public"))
    conn.execute(text("CREATE TABLE core_scadenze (id SERIAL PRIMARY KEY)"))
    conn.execute(text(
        "CREATE TABLE anag_documenti (id SERIAL PRIMARY KEY, tipo_documento VARCHAR(50), "
        "tipo_documento_id INTEGER, metadata_parsato JSON, created_at TIMESTAMPTZ DEFAULT now())"))
    conn.execute(text("CREATE TABLE anag_documenti_files (id SERIAL PRIMARY KEY)"))
    conn.execute(text("CREATE TABLE anag_tipi_documento_overrides (id SERIAL PRIMARY KEY)"))
    conn.execute(text("CREATE TABLE anag_stati_documento_overrides (id SERIAL PRIMARY KEY)"))
    conn.execute(text("INSERT INTO anag_documenti (tipo_documento) VALUES ('ALTRO')"))

    modulo = _carica()
    modulo.op = _Op(conn)
    modulo.upgrade()
    modulo.upgrade()  # idempotent

    tabelle = _tabelle(conn)
    assert {"core_documenti", "core_documenti_files", "core_tipi_documento_overrides",
            "core_stati_documento_overrides"} <= tabelle
    assert not {t for t in tabelle if t.startswith("anag_documenti")}
    riga = conn.execute(text("SELECT stato, data_riferimento FROM core_documenti")).one()
    assert riga.stato == "CORRENTE" and riga.data_riferimento is not None


def test_tenant_esistente_invariato(db_session):
    """tenant_qa_test already has core_*: nothing renamed or lost."""
    prima = db_session.execute(text("SELECT count(*) FROM core_documenti")).scalar()
    modulo = _carica()
    modulo.op = _Op(db_session.connection())
    modulo.upgrade()
    assert db_session.execute(text("SELECT count(*) FROM core_documenti")).scalar() == prima
