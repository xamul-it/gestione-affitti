"""
The unit's energy class is the class of its current APE (spec
2026-11-10-caricamento-unico-documenti-immobili): one source, the document;
the old column is neither written nor read.
"""
from datetime import date
from types import SimpleNamespace

import pytest

from app.core.platform.models import EntityType
from app.core.platform_services.documento_service import DocumentoService, FileInput
from immobili.models import UnitaImmobiliare
from immobili.routes.immobili import get_unita_immobiliare, get_unita_immobiliari, update_unita_immobiliare
from immobili.schemas import UnitaImmobiliareUpdate
from tests.integration.conftest import TEST_TENANT

pytestmark = pytest.mark.integration
USER = SimpleNamespace(id=1)


@pytest.fixture
def unita(db_session, unique_suffix, tmp_path, monkeypatch):
    from app.core.file_storage import file_storage
    monkeypatch.setattr(file_storage, "base_path", tmp_path)
    u = UnitaImmobiliare(codice=f"CE-{unique_suffix}", tipo="Appartamento", indirizzo="Via Po 1", citta="Torino",
                         classe_energetica="G")
    db_session.add(u)
    db_session.flush()
    return u


def _ape(db, unita, classe, emissione):
    DocumentoService(db, TEST_TENANT, 1).crea(
        entity_type=EntityType.IMMOBILE, entity_id=unita.id, tipo_codice="APE",
        files=[FileInput(f"%PDF {classe}".encode(), f"{classe}.pdf", "application/pdf")],
        data_riferimento=emissione, dati={"classe": classe})
    db.flush()


def test_classe_unita_viene_dall_ape_corrente(db_session, unita):
    _ape(db_session, unita, "D", date(2015, 1, 1))
    _ape(db_session, unita, "B", date(2022, 1, 1))
    assert get_unita_immobiliare(unita.id, db=db_session, current_user=USER).classe_energetica == "B"
    lista = {u.id: u for u in get_unita_immobiliari(db=db_session, current_user=USER, limit=10000)}
    assert lista[unita.id].classe_energetica == "B"


def test_unita_senza_ape_classe_vuota(db_session, unita):
    assert get_unita_immobiliare(unita.id, db=db_session, current_user=USER).classe_energetica is None


def test_scrittura_classe_ignorata(db_session, unita):
    update_unita_immobiliare(unita.id, UnitaImmobiliareUpdate(classe_energetica="A1", note="x"),
                             db=db_session, current_user=USER)
    db_session.refresh(unita)
    assert unita.classe_energetica == "G"
