"""
Backfill of the history columns added to core_documenti by core migration
2026110902: legacy documents (only the TipoDocumentoEnum column, no
tipo_documento_id, no data_riferimento) must keep being listed after the
migration, under their mapped document type.
"""
import importlib.util
from datetime import date
from pathlib import Path

import pytest
from sqlalchemy import text

pytestmark = pytest.mark.integration

_MIGRATION = Path(__file__).resolve().parents[3] / "alembic" / "versions" / "2026110902_documenti_storico.py"


def _load_migration():
    spec = importlib.util.spec_from_file_location("mig_2026110902", _MIGRATION)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _insert_legacy(db, tipo_enum: str, metadata: str | None) -> int:
    return db.execute(text("""
        INSERT INTO core_documenti (entity_type, entity_id, tipo_documento, metadata_parsato,
                                    data_riferimento, tipo_documento_id, created_at)
        VALUES ('IMMOBILE', 999001, :tipo, CAST(:meta AS json), NULL, NULL, '2023-02-01 10:00+00')
        RETURNING id
    """), {"tipo": tipo_enum, "meta": metadata}).scalar_one()


def test_backfill_legacy_documents(db_session):
    migration = _load_migration()
    visura_id = _insert_legacy(db_session, "VISURA_CATASTALE", '{"data_visura": "2024-05-10"}')
    foto_id = _insert_legacy(db_session, "FOTO", None)

    migration.backfill(db_session.connection())

    rows = {
        r.id: r for r in db_session.execute(text("""
            SELECT d.id, d.stato, d.data_riferimento, d.tipo_documento_id, t.codice
            FROM core_documenti d LEFT JOIN public.core_tipi_documento t ON t.id = d.tipo_documento_id
            WHERE d.id IN (:a, :b)
        """), {"a": visura_id, "b": foto_id})
    }
    visura, foto = rows[visura_id], rows[foto_id]
    assert visura.stato == "CORRENTE"
    assert visura.data_riferimento == date(2024, 5, 10)
    assert visura.codice == "VISURA_CATASTALE"
    assert foto.stato == "CORRENTE"
    assert foto.tipo_documento_id is None
    assert foto.data_riferimento == date(2023, 2, 1)
