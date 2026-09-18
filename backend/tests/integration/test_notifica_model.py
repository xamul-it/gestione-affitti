import pytest
from datetime import datetime

from app.core.database import SessionLocal
from app.core.platform.models import Notifica, CanaleNotifica, StatoEmailNotifica
from sqlalchemy import text


@pytest.fixture
def pg_session():
    """
    Use the real PostgreSQL database configured in .env
    instead of SQLite in-memory for this test module.

    Sets search_path to tenant_principale where core_notifiche exists.
    """
    db = SessionLocal()

    # Set search_path to tenant_principale to access tenant-scoped tables
    try:
        db.execute(text("SET search_path TO tenant_principale, public"))
        db.commit()
    except Exception:
        pass

    yield db
    db.close()


def test_notifica_defaults(pg_session):
    n = Notifica(
        user_id=1,
        tipo="test.evento",
        titolo="Titolo di prova",
        corpo="Corpo di prova",
    )
    pg_session.add(n)
    pg_session.commit()
    pg_session.refresh(n)

    assert n.id is not None
    assert n.canali == CanaleNotifica.ENTRAMBI.value
    assert n.stato_email == StatoEmailNotifica.NON_RICHIESTA.value
    assert n.letta is False
    assert n.letta_il is None
    assert isinstance(n.creata_il, datetime)


def test_notifica_with_entity_link(pg_session):
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
    pg_session.add(n)
    pg_session.commit()
    pg_session.refresh(n)

    assert n.entity_type == "scadenza"
    assert n.entity_id == 42
    assert n.link_url == "/scadenze/42"
    assert n.canali == CanaleNotifica.EMAIL.value
