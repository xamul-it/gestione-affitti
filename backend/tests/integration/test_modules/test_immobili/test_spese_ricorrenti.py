"""
Integration tests for SpesaRicorrenteImmobile (recurring-expense tracking of immobili).

Calls route functions directly (db=pg_session, current_user=<real User>)
rather than through TestClient/HTTP/JWT — same established pattern as
tests/integration/test_notifiche_routes.py. Real PostgreSQL (pg_session),
not the SQLite db_session fixture, which is documented-broken for any
row-creating test in this repo.
"""
import pytest
from sqlalchemy import text

from app.core.auth.models import User
from app.core.auth.security import get_password_hash
from app.core.platform.models import Scadenza, StatoScadenza

from immobili.models import Bene
from immobili.models import (
    SpesaRicorrenteImmobile,
    UnitaImmobiliare,
)
from immobili.routes.spese_ricorrenti import (
    create_spesa_ricorrente,
    duplica_spesa_ricorrente,
    segna_pagato,
)
from immobili.schemas import (
    DuplicaSpesaRequest,
    SegnaPagatoRequest,
    SpesaRicorrenteCreate,
)

TENANT = "tenant_qa_test"


@pytest.fixture(autouse=True)
def override_get_db():
    """Shadow conftest.py's autouse override_get_db(db_session) for this module only — see test_notifica_model.py for rationale."""
    yield


@pytest.fixture
def pg_session(db_session):
    # Rolled-back transaction from tests/integration/conftest.py: commits in
    # the routes only release a savepoint, nothing reaches the dev DB.
    db_session.execute(text(f"SET search_path TO {TENANT}, public"))
    return db_session


@pytest.fixture
def test_user(pg_session):
    user = User(
        email="spese-ricorrenti-test@example.com",
        username="spese_ricorrenti_test",
        full_name="Spese Ricorrenti Test",
        hashed_password=get_password_hash("testpass123"),
        is_active=True,
        is_superuser=True,  # bypasses require_permission's permission check
    )
    pg_session.add(user)
    pg_session.commit()
    pg_session.refresh(user)
    try:
        yield user
    finally:
        pg_session.query(User).filter_by(id=user.id).delete()
        pg_session.commit()


@pytest.fixture
def unita(pg_session):
    u = UnitaImmobiliare(
        codice="TEST-SPRIC-001",
        tipo="Appartamento",
        indirizzo="Via Test 1",
        citta="Testville",
    )
    pg_session.add(u)
    pg_session.commit()
    try:
        yield u
    finally:
        pg_session.query(Bene).filter_by(id=u.id).delete()  # cascades to the unit
        pg_session.commit()


def _cleanup_spese(pg_session, spesa_ids, scadenza_ids):
    pg_session.rollback()
    ids = [i for i in spesa_ids if i]
    if ids:
        pg_session.query(SpesaRicorrenteImmobile).filter(SpesaRicorrenteImmobile.id.in_(ids)).delete(synchronize_session=False)
    sids = [i for i in scadenza_ids if i]
    if sids:
        pg_session.query(Scadenza).filter(Scadenza.id.in_(sids)).delete(synchronize_session=False)
    pg_session.commit()


def test_create_spesa_ricorrente_creates_linked_scadenza(pg_session, test_user, unita):
    spesa = None
    scadenza_id = None
    try:
        spesa = create_spesa_ricorrente(
            SpesaRicorrenteCreate(
                bene_id=unita.id,
                tipo_spesa="IMU",
                responsabile="PROPRIETARIO",
                periodo="2026",
                rata="ACCONTO",
                importo="450.00",
                data_scadenza="2026-06-16",
            ),
            db=pg_session,
            current_user=test_user,
        )
        scadenza_id = spesa.scadenza_id
        assert spesa.pagato is False
        assert scadenza_id is not None

        scadenza = pg_session.query(Scadenza).filter_by(id=scadenza_id).first()
        assert scadenza is not None
        assert scadenza.modulo == "immobili"
        assert scadenza.entity_type == "SPESA_RICORRENTE"
        assert scadenza.entity_id == spesa.id
        assert scadenza.stato == StatoScadenza.ATTIVA
        assert "IMU" in scadenza.titolo
    finally:
        _cleanup_spese(pg_session, [spesa.id if spesa else None], [scadenza_id])


def test_create_spesa_ricorrente_rejects_both_targets(pg_session, test_user, unita):
    with pytest.raises(Exception):
        SpesaRicorrenteCreate(
            bene_id=unita.id,
            condominio_id=1,
            tipo_spesa="TARI",
            responsabile="CONDUTTORE",
            periodo="2026",
            importo="100.00",
            data_scadenza="2026-06-16",
        )


def test_segna_pagato_completes_linked_scadenza(pg_session, test_user, unita):
    spesa = None
    scadenza_id = None
    try:
        spesa = create_spesa_ricorrente(
            SpesaRicorrenteCreate(
                bene_id=unita.id,
                tipo_spesa="TARI",
                responsabile="CONDUTTORE",
                periodo="2026",
                importo="120.50",
                data_scadenza="2026-04-30",
            ),
            db=pg_session,
            current_user=test_user,
        )
        scadenza_id = spesa.scadenza_id

        aggiornata = segna_pagato(
            spesa.id,
            SegnaPagatoRequest(data_pagamento="2026-04-20"),
            db=pg_session,
            current_user=test_user,
        )
        assert aggiornata.pagato is True
        assert str(aggiornata.data_pagamento) == "2026-04-20"

        scadenza = pg_session.query(Scadenza).filter_by(id=scadenza_id).first()
        assert scadenza.stato == StatoScadenza.COMPLETATA
    finally:
        _cleanup_spese(pg_session, [spesa.id if spesa else None], [scadenza_id])


def test_duplica_spesa_ricorrente_creates_new_period(pg_session, test_user, unita):
    originale = None
    duplicata = None
    scadenza_ids = []
    try:
        originale = create_spesa_ricorrente(
            SpesaRicorrenteCreate(
                bene_id=unita.id,
                tipo_spesa="IMU",
                responsabile="PROPRIETARIO",
                periodo="2026",
                rata="SALDO",
                importo="450.00",
                data_scadenza="2026-12-16",
            ),
            db=pg_session,
            current_user=test_user,
        )
        scadenza_ids.append(originale.scadenza_id)

        duplicata = duplica_spesa_ricorrente(
            originale.id,
            DuplicaSpesaRequest(periodo="2027", data_scadenza="2027-12-16"),
            db=pg_session,
            current_user=test_user,
        )
        scadenza_ids.append(duplicata.scadenza_id)

        assert duplicata.id != originale.id
        assert duplicata.periodo == "2027"
        assert duplicata.tipo_spesa == "IMU"
        assert duplicata.responsabile == "PROPRIETARIO"
        assert duplicata.rata == "SALDO"  # carried over, not specified in the request
        assert duplicata.importo == originale.importo  # carried over
        assert duplicata.pagato is False
        assert duplicata.scadenza_id != originale.scadenza_id
    finally:
        _cleanup_spese(
            pg_session,
            [originale.id if originale else None, duplicata.id if duplicata else None],
            scadenza_ids,
        )
