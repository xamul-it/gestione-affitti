"""
Regression tests for delete_unita_immobiliare/delete_condominio when the
parent has existing children.

Before this fix, several one-to-many relationships on UnitaImmobiliare and
Condominio had no cascade/passive_deletes configuration, so deleting a
parent with existing children raised either a NotNullViolation (children
whose FK is non-nullable, and whose table has no real DB-level FK
constraint to fall back on: DirittoImmobile, CertificatoEnergetico) or a
CHECK-constraint violation (SpesaRicorrenteImmobile, whose exactly-one-of
unita/condominio constraint is violated the moment SQLAlchemy tries to
null out one side in Python instead of trusting the real ON DELETE
CASCADE constraint on that table).

Calls route functions directly (db=pg_session), same established pattern
as test_proprietari.py / test_conduttori_spese_ricorrenti.py.
"""
import pytest
from sqlalchemy import text

from anagrafica_italiana.models import SoggettoAnagrafico, TipoSoggetto

from immobili.models import (
    AssegnazioneConduttore,
    CertificatoEnergetico,
    Condominio,
    Conduttore,
    DirittoImmobile,
    Proprietario,
    SpesaRicorrenteImmobile,
    UnitaImmobiliare,
)
from immobili.routes.immobili import delete_unita_immobiliare
from immobili.routes.condomini import delete_condominio
from immobili.routes.diritti_immobile import create_diritto
from immobili.routes.assegnazioni_conduttore import create_assegnazione
from immobili.routes.spese_ricorrenti import create_spesa_ricorrente
from immobili.routes.proprietari import create_proprietario
from immobili.routes.conduttori import create_conduttore
from immobili.schemas import (
    AssegnazioneConduttoreCreate,
    ConduttoreCreate,
    DirittoImmobileCreate,
    ProprietarioCreate,
    SpesaRicorrenteCreate,
)

TENANT = "tenant_qa_test"


@pytest.fixture(autouse=True)
def override_get_db():
    """Shadow conftest.py's autouse override_get_db(db_session) for this module only — see test_notifica_model.py for rationale."""
    yield


@pytest.fixture
def pg_session():
    from app.core.database import SessionLocal
    session = SessionLocal()
    try:
        session.execute(text(f"SET search_path TO {TENANT}, public"))
        session.commit()
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture
def unita(pg_session):
    u = UnitaImmobiliare(
        codice="TEST-CASCADE-001",
        tipo="Appartamento",
        indirizzo="Via Cascade 1",
        citta="Testville",
    )
    pg_session.add(u)
    pg_session.commit()
    yield u
    pg_session.rollback()
    pg_session.query(UnitaImmobiliare).filter_by(codice="TEST-CASCADE-001").delete()
    pg_session.commit()


@pytest.fixture
def condominio(pg_session):
    c = Condominio(codice="TEST-CASCADE-COND", indirizzo="Via Cascade 2", citta="Testville")
    pg_session.add(c)
    pg_session.commit()
    yield c
    pg_session.rollback()
    pg_session.query(Condominio).filter_by(codice="TEST-CASCADE-COND").delete()
    pg_session.commit()


@pytest.fixture
def soggetto_proprietario(pg_session):
    s = SoggettoAnagrafico(
        tipo_soggetto=TipoSoggetto.PERSONA_FISICA,
        nome="Cascade",
        cognome="Owner",
        codice_fiscale="CSCOWN80A01H501C",
    )
    pg_session.add(s)
    pg_session.commit()
    yield s
    pg_session.rollback()
    pg_session.query(SoggettoAnagrafico).filter_by(id=s.id).delete()
    pg_session.commit()


@pytest.fixture
def soggetto_conduttore(pg_session):
    s = SoggettoAnagrafico(
        tipo_soggetto=TipoSoggetto.PERSONA_FISICA,
        nome="Cascade",
        cognome="Tenant",
        codice_fiscale="CSCTNT80A01H501D",
    )
    pg_session.add(s)
    pg_session.commit()
    yield s
    pg_session.rollback()
    pg_session.query(SoggettoAnagrafico).filter_by(id=s.id).delete()
    pg_session.commit()


def test_delete_unita_immobiliare_cascades_diritto(pg_session, unita, soggetto_proprietario):
    proprietario = create_proprietario(ProprietarioCreate(soggetto_id=soggetto_proprietario.id), db=pg_session)
    try:
        diritto = create_diritto(
            DirittoImmobileCreate(
                unita_immobiliare_id=unita.id,
                proprietario_id=proprietario.id,
                tipo_diritto="PROPRIETARIO",
                quota_percentuale=100,
            ),
            db=pg_session,
        )
        diritto_id = diritto.id
        unita_id = unita.id

        delete_unita_immobiliare(unita_id, db=pg_session)

        assert pg_session.query(UnitaImmobiliare).filter_by(id=unita_id).first() is None
        assert pg_session.query(DirittoImmobile).filter_by(id=diritto_id).first() is None
    finally:
        pg_session.rollback()
        pg_session.query(Proprietario).filter_by(id=proprietario.id).delete()
        pg_session.commit()


def test_delete_unita_immobiliare_cascades_certificato_energetico(pg_session, unita):
    cert = CertificatoEnergetico(
        unita_immobiliare_id=unita.id,
        tecnico_id=1,
        classe_energetica="A4",
        data_emissione="2026-01-01",
        data_scadenza="2036-01-01",
    )
    pg_session.add(cert)
    pg_session.commit()
    cert_id = cert.id
    unita_id = unita.id

    delete_unita_immobiliare(unita_id, db=pg_session)

    assert pg_session.query(UnitaImmobiliare).filter_by(id=unita_id).first() is None
    assert pg_session.query(CertificatoEnergetico).filter_by(id=cert_id).first() is None


def test_delete_unita_immobiliare_cascades_assegnazione_conduttore(pg_session, unita, soggetto_conduttore):
    conduttore = create_conduttore(ConduttoreCreate(soggetto_id=soggetto_conduttore.id), db=pg_session)
    try:
        assegnazione = create_assegnazione(
            AssegnazioneConduttoreCreate(unita_immobiliare_id=unita.id, conduttore_id=conduttore.id),
            db=pg_session,
        )
        assegnazione_id = assegnazione.id
        unita_id = unita.id

        delete_unita_immobiliare(unita_id, db=pg_session)

        assert pg_session.query(UnitaImmobiliare).filter_by(id=unita_id).first() is None
        assert pg_session.query(AssegnazioneConduttore).filter_by(id=assegnazione_id).first() is None
    finally:
        pg_session.rollback()
        pg_session.query(Conduttore).filter_by(id=conduttore.id).delete()
        pg_session.commit()


def test_delete_unita_immobiliare_cascades_spesa_ricorrente(pg_session, unita, test_user=None):
    from app.core.auth.models import User
    from app.core.auth.security import get_password_hash

    user = User(
        email="cascade-test@example.com",
        username="cascade_test_user",
        full_name="Cascade Test",
        hashed_password=get_password_hash("testpass123"),
        is_active=True,
        is_superuser=True,
    )
    pg_session.add(user)
    pg_session.commit()
    pg_session.refresh(user)
    try:
        spesa = create_spesa_ricorrente(
            SpesaRicorrenteCreate(
                unita_immobiliare_id=unita.id,
                tipo_spesa="IMU",
                responsabile="PROPRIETARIO",
                periodo="2026",
                importo="450.00",
                data_scadenza="2026-06-16",
            ),
            db=pg_session,
            current_user=user,
        )
        spesa_id = spesa.id
        unita_id = unita.id

        delete_unita_immobiliare(unita_id, db=pg_session)

        assert pg_session.query(UnitaImmobiliare).filter_by(id=unita_id).first() is None
        assert pg_session.query(SpesaRicorrenteImmobile).filter_by(id=spesa_id).first() is None
    finally:
        pg_session.rollback()
        pg_session.query(User).filter_by(id=user.id).delete()
        pg_session.commit()


def test_delete_condominio_cascades_spesa_ricorrente(pg_session, condominio):
    from app.core.auth.models import User
    from app.core.auth.security import get_password_hash

    user = User(
        email="cascade-test-condo@example.com",
        username="cascade_test_condo_user",
        full_name="Cascade Test Condo",
        hashed_password=get_password_hash("testpass123"),
        is_active=True,
        is_superuser=True,
    )
    pg_session.add(user)
    pg_session.commit()
    pg_session.refresh(user)
    try:
        spesa = create_spesa_ricorrente(
            SpesaRicorrenteCreate(
                condominio_id=condominio.id,
                tipo_spesa="MANUTENZIONE_ORDINARIA",
                responsabile="CONDUTTORE",
                periodo="2026",
                importo="120.00",
                data_scadenza="2026-06-16",
            ),
            db=pg_session,
            current_user=user,
        )
        spesa_id = spesa.id
        condominio_id = condominio.id

        delete_condominio(condominio_id, db=pg_session)

        assert pg_session.query(Condominio).filter_by(id=condominio_id).first() is None
        assert pg_session.query(SpesaRicorrenteImmobile).filter_by(id=spesa_id).first() is None
    finally:
        pg_session.rollback()
        pg_session.query(User).filter_by(id=user.id).delete()
        pg_session.commit()
