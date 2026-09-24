"""
Regression tests for DELETE /anagrafica/soggetti-v2/{id} when the soggetto
has an active role (Proprietario/Affittuario/Tecnico/Conduttore) linked
to it.

Before this fix, delete_soggetto_v2 had no guard and went straight to
db.delete()/commit(). SoggettoAnagrafico.proprietari (and .tecnici) have
no cascade/passive_deletes configured, and immo_proprietari has no real
FK constraint in the DB at all, so deleting a soggetto already registered
as a Proprietario crashed with a NotNullViolation instead of the intended
"can't delete, has active roles" 400 (the v1 soggetti.py router — not
mounted — already implements this exact guard; v2, the live route, never
had it).

Conduttore is included even though immo_conduttori DOES have a real
ON DELETE CASCADE (unlike Proprietario): the original fix omitted
Conduttore's role check entirely (SoggettoAnagrafico had no .conduttori
relationship at all), so deleting a soggetto registered as a Conduttore
silently cascaded away the Conduttore/AssegnazioneConduttore rows with no
warning — the opposite policy from every other role, found by independent
review.

Uses real PostgreSQL (pg_session), same pattern as test_public_api.py.
"""
import pytest
from fastapi import HTTPException
from sqlalchemy import text

from anagrafica_italiana.models import SoggettoAnagrafico, TipoSoggetto
from anagrafica_italiana.routes.soggetti_v2 import _has_role_records, delete_soggetto_v2

from immobili.models import Conduttore, Proprietario
from immobili.routes.proprietari import create_proprietario
from immobili.routes.conduttori import create_conduttore
from immobili.schemas import ConduttoreCreate, ProprietarioCreate

TENANT = "tenant_qa_test"


@pytest.fixture(autouse=True)
def override_get_db():
    """Shadow conftest.py's autouse override_get_db(db_session) for this module only — see test_notifica_model.py for rationale."""
    yield


@pytest.fixture
def pg_session():
    """
    Bound to a single, explicitly-checked-out Connection for the fixture's
    whole lifetime (rather than letting the Session pull from/return to the
    engine's pool per-transaction, as plain SessionLocal() does). A commit
    or rollback ends a *logical* transaction and releases the connection
    back to the pool; the next query can then land on a *different* pooled
    connection that never had this fixture's `SET search_path` applied,
    surfacing as a spurious "relation does not exist" on an otherwise
    correct query — this only needs one physical connection for the
    session's whole lifetime to avoid entirely.
    """
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
def soggetto(pg_session):
    s = SoggettoAnagrafico(
        tipo_soggetto=TipoSoggetto.PERSONA_FISICA,
        nome="Delete",
        cognome="Guard",
        codice_fiscale="DLTGRD80A01H501G",
    )
    pg_session.add(s)
    pg_session.commit()
    soggetto_id = s.id
    yield s
    # Capture the id before any rollback: rollback() releases the session's
    # connection back to the pool, and accessing an expired ORM attribute
    # afterward (e.g. s.id) can trigger a reload on a *different* pooled
    # connection that never had this test's `SET search_path` applied,
    # surfacing as a spurious "relation does not exist" error.
    pg_session.query(SoggettoAnagrafico).filter_by(id=soggetto_id).delete()
    pg_session.commit()


def test_delete_soggetto_blocked_when_registered_as_proprietario(pg_session, soggetto):
    proprietario = create_proprietario(ProprietarioCreate(soggetto_id=soggetto.id), db=pg_session)
    proprietario_id = proprietario.id
    try:
        with pytest.raises(HTTPException) as exc_info:
            delete_soggetto_v2(soggetto.id, db=pg_session, tenant_schema=TENANT)
        assert exc_info.value.status_code == 400

        # Blocked, not silently cascaded: both rows must still exist.
        assert pg_session.query(SoggettoAnagrafico).filter_by(id=soggetto.id).first() is not None
        assert pg_session.query(Proprietario).filter_by(id=proprietario_id).first() is not None
    finally:
        pg_session.query(Proprietario).filter_by(id=proprietario_id).delete()
        pg_session.commit()


def test_delete_soggetto_blocked_when_registered_as_conduttore(pg_session, soggetto):
    conduttore = create_conduttore(ConduttoreCreate(soggetto_id=soggetto.id), db=pg_session)
    conduttore_id = conduttore.id
    try:
        with pytest.raises(HTTPException) as exc_info:
            delete_soggetto_v2(soggetto.id, db=pg_session, tenant_schema=TENANT)
        assert exc_info.value.status_code == 400

        # Blocked, not silently cascaded via immo_conduttori's real ON DELETE CASCADE.
        assert pg_session.query(SoggettoAnagrafico).filter_by(id=soggetto.id).first() is not None
        assert pg_session.query(Conduttore).filter_by(id=conduttore_id).first() is not None
    finally:
        pg_session.query(Conduttore).filter_by(id=conduttore_id).delete()
        pg_session.commit()


def test_delete_soggetto_succeeds_without_roles(pg_session, soggetto):
    soggetto_id = soggetto.id

    delete_soggetto_v2(soggetto_id, db=pg_session, tenant_schema=TENANT)

    assert pg_session.query(SoggettoAnagrafico).filter_by(id=soggetto_id).first() is None


def test_has_role_records_missing_table_does_not_reset_search_path(pg_session, soggetto):
    """
    Regression test for the search_path-loss bug: the original fix checked
    role tables via try/except-and-rollback a ProgrammingError. get_db()
    issues `SET search_path` as the first statement of the session's
    transaction, so a mid-request rollback undoes that SET along with it,
    silently reverting the rest of the request to the wrong schema — on
    the ordinary, successful "no roles" path for any tenant missing one of
    these role modules, not just some rare error case.

    None of immo_proprietari/affittuari/tecnici/immo_conduttori exist in
    'public' (they're tenant-only tables), so passing tenant_schema=
    'public' exercises the "table doesn't exist" branch for all four
    without needing a second real tenant fixture.
    """
    result = _has_role_records(pg_session, soggetto, tenant_schema="public")
    assert result is False

    # If search_path had been reset (by a rollback undoing the session's
    # original `SET search_path TO tenant_qa_test, public`), this query
    # would now run against 'public' and find nothing, or error outright —
    # not find the tenant-scoped soggetto created by the fixture.
    assert pg_session.query(SoggettoAnagrafico).filter_by(id=soggetto.id).first() is not None
