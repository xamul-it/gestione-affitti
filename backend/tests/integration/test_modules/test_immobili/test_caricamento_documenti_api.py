"""
Single upload point for immobili documents (spec
2026-11-10-caricamento-unico-documenti-immobili): POST /analizza reads a file
and proposes type, unit, data and differences; POST /conferma saves only what
the user confirmed.

Test files are b"%PDF" + invented text; the PDF text extraction is replaced by
a decode so no real document is needed.
"""
from datetime import date

import pytest
from fastapi.testclient import TestClient

from app.core.auth.dependencies import get_current_active_user
from app.core.auth.models import User
from app.core.database import get_db, get_tenant_schema
from app.core.file_storage import file_storage
from app.core.platform.models import Documento, EntityType
from app.core.platform_services.documento_service import DocumentoService, FileInput
from app.main import app
from immobili.models import UnitaImmobiliare, VariazioneCatastale
from immobili.services.lettura_documenti import caricamento
from immobili.services.visura import VisuraFormatError
from tests.integration.conftest import TEST_TENANT
from tests.unit.test_modules.test_immobili_lettura.fixtures import (
    APE_CON_CLASSE, APE_ER, RLI12, TESTO_QUALSIASI, VISURA_IMMOBILE,
)

pytestmark = pytest.mark.integration

BASE = "/api/v1/unita-immobiliari/caricamento-documenti"
ADMIN = dict(id=1, username="admin-test", is_superuser=True, is_active=True, roles=[])


def _pdf(testo: str) -> bytes:
    return b"%PDF-1.4\n" + testo.encode()


def _fake_pdf_to_text(content: bytes) -> str:
    if not content.startswith(b"%PDF"):
        raise VisuraFormatError("Il file caricato non è un PDF valido")
    return content[len(b"%PDF-1.4\n"):].decode()


@pytest.fixture
def client(db_session, tmp_path, monkeypatch):
    monkeypatch.setattr(file_storage, "base_path", tmp_path)
    monkeypatch.setattr(caricamento, "pdf_to_text", _fake_pdf_to_text)
    utente = {"user": User(**ADMIN)}
    app.dependency_overrides[get_db] = lambda: db_session
    app.dependency_overrides[get_tenant_schema] = lambda: TEST_TENANT
    app.dependency_overrides[get_current_active_user] = lambda: utente["user"]
    try:
        with TestClient(app) as c:
            c.utente = utente
            yield c
    finally:
        for dep in (get_db, get_tenant_schema, get_current_active_user):
            app.dependency_overrides.pop(dep, None)


@pytest.fixture
def unita(db_session, unique_suffix):
    u = UnitaImmobiliare(codice=f"CU-{unique_suffix}", tipo="Appartamento", indirizzo="Via Po 1", citta="Torino",
                         foglio="12", particella="345", subalterno="6", piano="2")
    db_session.add(u)
    db_session.flush()
    return u


def _analizza(client, testo, nome="doc.pdf"):
    res = client.post(f"{BASE}/analizza", files={"file": (nome, _pdf(testo), "application/pdf")})
    assert res.status_code == 200, res.text
    return res.json()


def test_ape_pronto_con_unita_e_dati(client, unita):
    a = _analizza(client, APE_ER)
    assert a["esito"] == "pronto" and a["tipo_codice"] == "APE" and a["unita_id"] == unita.id
    assert a["dati"]["ep_gl_nren"] == 111.24 and a["dati"]["data_emissione"] == "2021-02-23"
    assert [d["campo"] for d in a["differenze"]] == ["indirizzo"]
    assert a["upload_token"]


def test_testo_sconosciuto_chiede_il_tipo(client):
    a = _analizza(client, TESTO_QUALSIASI)
    assert a["esito"] == "scegli_tipo" and a["upload_token"]


def test_rianalizza_con_tipo_scelto(client, unita):
    a = _analizza(client, TESTO_QUALSIASI)
    res = client.post(f"{BASE}/rianalizza", json={"upload_token": a["upload_token"], "tipo_codice": "AGIBILITA",
                                                  "unita_id": unita.id})
    assert res.status_code == 200, res.text
    assert res.json()["esito"] == "pronto" and res.json()["unita_id"] == unita.id


def test_rli_scartato(client):
    a = _analizza(client, RLI12)
    assert a["esito"] == "scartato"
    assert a["messaggio"] == "Ricevuta di registrazione del contratto: caricala dal contratto, nel modulo Affitti"


def test_visura_rimanda_all_import(client):
    assert _analizza(client, VISURA_IMMOBILE)["esito"] == "visura"


def test_visura_senza_permesso_import(client):
    client.utente["user"] = _utente_con({"documenti.write", "immobile.edit"})
    a = _analizza(client, VISURA_IMMOBILE)
    assert a["esito"] == "scartato" and a["messaggio"] == "Serve il permesso di import visure"


def test_unita_non_trovata_chiede_immobile(client):
    a = _analizza(client, APE_ER)
    assert a["esito"] == "scegli_immobile" and a["unita_id"] is None


def test_duplicato_gia_presente(client, unita, db_session):
    DocumentoService(db_session, TEST_TENANT, 1).crea(
        entity_type=EntityType.IMMOBILE, entity_id=unita.id, tipo_codice="APE",
        files=[FileInput(_pdf(APE_ER), "ape.pdf", "application/pdf")], data_riferimento=date(2021, 2, 23),
        dati={"classe": "C"})
    db_session.flush()
    assert _analizza(client, APE_ER)["esito"] == "gia_presente"


def _conferma(client, a, **extra):
    body = {"upload_token": a["upload_token"], "tipo_codice": a["tipo_codice"], "unita_id": a["unita_id"],
            "dati": {}, "differenze": a["differenze"], **extra}
    return client.post(f"{BASE}/conferma", json=body)


def test_conferma_salva_ape_e_aggiorna_campi_selezionati(client, unita, db_session):
    a = _analizza(client, APE_ER.replace("Piano - Interno: 2°", "Piano - Interno: 3°"))
    differenze = [{**d, "selezionato": d["campo"] == "indirizzo"} for d in a["differenze"]]
    assert {d["campo"] for d in differenze} == {"indirizzo", "piano"}
    res = _conferma(client, a, dati={"classe": "C"}, differenze=differenze)
    assert res.status_code == 200, res.text
    db_session.refresh(unita)
    assert unita.indirizzo == "VIA PO n.3" and unita.piano == "2"
    doc = db_session.get(Documento, res.json()["documento_id"])
    assert doc.dati["classe"] == "C" and doc.dati["ep_gl_nren"] == 111.24 and doc.stato == "CORRENTE"
    assert doc.data_riferimento == date(2021, 2, 23)
    var = db_session.query(VariazioneCatastale).filter_by(unita_immobiliare_id=unita.id).all()
    assert [(v.campo, v.origine, v.documento_id) for v in var] == [("indirizzo", "DOCUMENTO", doc.id)]


def test_conferma_ape_piu_vecchio_va_in_storico(client, unita, db_session):
    DocumentoService(db_session, TEST_TENANT, 1).crea(
        entity_type=EntityType.IMMOBILE, entity_id=unita.id, tipo_codice="APE",
        files=[FileInput(b"%PDF-1.4\nrecente", "recente.pdf", "application/pdf")],
        data_riferimento=date(2024, 1, 1), dati={"classe": "B"})
    db_session.flush()
    a = _analizza(client, APE_CON_CLASSE)
    assert "APE più vecchio di quello in vigore: verrà archiviato come storico" in a["avvisi"]
    res = _conferma(client, a)
    assert res.status_code == 200, res.text
    assert db_session.get(Documento, res.json()["documento_id"]).stato == "SOSTITUITO"


def test_conferma_ape_senza_classe_422(client, unita, db_session):
    a = _analizza(client, APE_ER)
    res = _conferma(client, a)
    assert res.status_code == 422 and res.json()["detail"] == "Indica la classe energetica (A4…G)"
    assert db_session.query(Documento).filter_by(entity_type=EntityType.IMMOBILE, entity_id=unita.id).count() == 0


def test_conferma_token_scaduto_404(client, unita):
    res = client.post(f"{BASE}/conferma", json={"upload_token": "0" * 32, "tipo_codice": "APE",
                                                "unita_id": unita.id, "dati": {"classe": "C"}})
    assert res.status_code == 404
    assert res.json()["detail"] == "Caricamento scaduto o non trovato, ricarica il documento"


def _utente_con(permessi):
    u = User(id=2, username="limitato", is_superuser=False, is_active=True, roles=[])
    u.get_permissions = lambda: set(permessi)
    return u


def test_senza_permesso_403(client):
    client.utente["user"] = _utente_con(set())
    res = client.post(f"{BASE}/analizza", files={"file": ("x.pdf", _pdf(APE_ER), "application/pdf")})
    assert res.status_code == 403
