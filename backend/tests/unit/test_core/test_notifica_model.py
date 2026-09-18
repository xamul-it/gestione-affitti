import pytest
from datetime import datetime

from app.core.platform.models import Notifica, CanaleNotifica, StatoEmailNotifica


@pytest.fixture(autouse=True)
def override_get_db():
    """
    Shadow conftest.py's autouse `override_get_db(db_session)` fixture for
    this module only. That global fixture unconditionally builds
    `db_session`/`db_engine` (SQLite), which runs an unfiltered
    `Base.metadata.create_all()` — this fails because `Tenant` declares
    `__table_args__ = {'schema': 'public'}`, which SQLite's dialect
    rejects. This test doesn't need the FastAPI app or its dependency
    override at all — it constructs a Notifica directly against the
    db_session fixture below — so shadowing this fixture with a no-op
    avoids that unrelated pre-existing problem (same pattern already
    used in tests/unit/test_core/test_main_create_core_tables.py and
    tests/integration/test_tenant_module_routes.py).
    """
    yield


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
