"""
Documents attached to a core relation (entity_type RELAZIONE): upload, listing,
type validation and removal together with the relation.
"""
import io
from datetime import date

import pytest
from fastapi import HTTPException, UploadFile

from app.core.file_storage import file_storage
from app.core.platform.models import Documento, EntityType
from app.core.platform_services.document_type_sync import sync_document_types
from app.core.platform_services.relation_type_sync import sync_relation_types
from app.core.platform_services.relazione_service import RelazioneService
from app.core.routes.documenti import get_documenti, upload_documento
from anagrafica_italiana.__manifest__ import manifest as anagrafica_manifest
from anagrafica_italiana.models import SoggettoAnagrafico
from anagrafica_italiana.models.soggetto_anagrafico import TipoSoggetto
from immobili.__manifest__ import manifest as immobili_manifest
from immobili.models import Condominio

pytestmark = pytest.mark.integration

from tests.integration.conftest import TEST_TENANT as TENANT


@pytest.fixture(autouse=True)
def setup(db_session, tmp_path, monkeypatch):
    monkeypatch.setattr(file_storage, "base_path", tmp_path)
    sync_document_types(db_session, {"immobili": immobili_manifest, "anagrafica_italiana": anagrafica_manifest})
    sync_relation_types(db_session, {"immobili": immobili_manifest, "anagrafica_italiana": anagrafica_manifest})


@pytest.fixture
def relazione(db_session, unique_suffix):
    soggetto = SoggettoAnagrafico(tipo_soggetto=TipoSoggetto.PERSONA_FISICA, nome="Mario", cognome="Rossi")
    condominio = Condominio(codice=f"COND-{unique_suffix}", nome="Aurora", indirizzo="Via Po 1", citta="Torino")
    db_session.add_all([soggetto, condominio])
    db_session.flush()
    return RelazioneService(db_session, TENANT).crea(
        soggetto.id, "amministratore_condominio", entity_type="CONDOMINIO", entity_id=condominio.id, data_inizio=date(2026, 1, 15),
    )


def _file():
    return UploadFile(file=io.BytesIO(b"%PDF-1.4 x"), filename="a.pdf", headers={"content-type": "application/pdf"})


async def _upload(db, relazione_id, tipo_codice):
    return await upload_documento(
        files=[_file()], file=None, entity_type=EntityType.RELAZIONE, entity_id=relazione_id,
        tipo_codice=tipo_codice, tipo_documento=None, data_riferimento=None, sottotipo=None,
        data_scadenza=None, dati=None, descrizione=None, note=None,
        db=db, tenant_schema=TENANT, current_user=None,
    )


@pytest.mark.asyncio
@pytest.mark.parametrize("tipo", ["ATTO_PROVENIENZA", "CONTRATTO_AFFITTO_AGRARIO", "CONTRATTO_COMODATO",
                                  "DELEGA_TERZO_RESPONSABILE"])
async def test_upload_su_relazione(db_session, relazione, tipo):
    out = await _upload(db_session, relazione.id, tipo)
    assert out.tipo_codice == tipo
    assert out.entity_type == "RELAZIONE"
    elenco = get_documenti(entity_type=EntityType.RELAZIONE, entity_id=relazione.id, db=db_session, current_user=None)
    assert [d.id for d in elenco] == [out.id]


@pytest.mark.asyncio
async def test_tipologia_non_ammessa_su_relazione(db_session, relazione):
    # The upload route maps service ValueErrors to 422, like every other rejected type.
    with pytest.raises(HTTPException) as exc:
        await _upload(db_session, relazione.id, "VISURA_CATASTALE")
    assert exc.value.status_code in (400, 422)
    assert "non si applica" in exc.value.detail


@pytest.mark.asyncio
async def test_elimina_relazione_toglie_documenti(db_session, relazione):
    out = await _upload(db_session, relazione.id, "CONTRATTO_COMODATO")
    RelazioneService(db_session, TENANT).elimina(relazione.id)
    assert db_session.query(Documento).filter(Documento.id == out.id).count() == 0
    assert db_session.query(Documento).filter(
        Documento.entity_type == EntityType.RELAZIONE, Documento.entity_id == relazione.id).count() == 0
