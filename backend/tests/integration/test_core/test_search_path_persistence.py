"""
A session must keep its tenant search_path across commits.

After commit() the Session hands its connection back to the pool and the
next statement checks one out again - with the default FIFO QueuePool,
often a different one, still carrying whatever search_path its previous
user (another request, a scheduler) left on it. Every query after a
commit in a request (refresh, follow-up reads, a second write) then ran in
that other tenant's schema.

The test parks a connection set to tenant_principale in the pool before
the commit, which makes that exact hand-over deterministic.
"""
import pytest
from sqlalchemy import text

from app.core.database import SessionLocal, engine, get_db


@pytest.fixture(autouse=True)
def override_get_db():
    # Shadows conftest's autouse SQLite override: these tests need the
    # real engine and its pool.
    yield


def _search_path(db):
    return db.execute(text("SHOW search_path")).scalar()


def _park_connection_on(schema):
    conn = engine.connect()
    conn.execute(text(f"SET search_path TO {schema}, public"))
    conn.commit()
    return conn


def test_get_db_search_path_survives_commit():
    gen = get_db(tenant_schema="tenant_qa_test")
    db = next(gen)
    try:
        other = _park_connection_on("tenant_principale")
        other.close()
        db.commit()
        assert _search_path(db) == "tenant_qa_test, public"
    finally:
        gen.close()


def test_manual_set_survives_commit():
    db = SessionLocal()
    try:
        db.execute(text("SET search_path TO tenant_qa_test, public"))
        other = _park_connection_on("tenant_principale")
        other.close()
        db.commit()
        assert _search_path(db) == "tenant_qa_test, public"
    finally:
        db.close()


def test_manual_set_via_connection_survives_rollback():
    db = SessionLocal()
    try:
        db.connection().execute(text("SET search_path TO tenant_qa_test, public"))
        other = _park_connection_on("tenant_principale")
        other.close()
        db.rollback()
        assert _search_path(db) == "tenant_qa_test, public"
    finally:
        db.close()


def test_session_without_search_path_does_not_inherit_a_tenant():
    other = _park_connection_on("tenant_principale")
    other.close()
    db = SessionLocal()
    try:
        assert _search_path(db) == "public"
    finally:
        db.close()


def test_raw_connection_set_does_not_leak_into_a_session():
    db = SessionLocal()
    try:
        db.execute(text("SET search_path TO tenant_qa_test, public"))
        db.commit()
        # A plain engine connection reusing the same pooled DBAPI
        # connection must not rewrite the session's remembered path.
        _park_connection_on("tenant_principale").close()
        assert _search_path(db) == "tenant_qa_test, public"
    finally:
        db.close()


def test_session_bound_to_configured_connection_keeps_its_search_path():
    # Session(bind=connection) always reuses that one connection, so the
    # search_path the caller set on it must be left alone.
    from sqlalchemy.orm import Session

    connection = engine.connect()
    connection.execute(text("SET search_path TO tenant_qa_test, public"))
    connection.commit()
    db = Session(bind=connection)
    try:
        assert _search_path(db) == "tenant_qa_test, public"
        db.commit()
        assert _search_path(db) == "tenant_qa_test, public"
    finally:
        db.close()
        connection.close()
