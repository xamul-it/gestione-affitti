"""
Energy certificates (immo_certificati_energetici) -> core APE documents,
plus the history/scadenze alignment run by scripts/sync_modules.py through
the immobili post_sync hook. Idempotent, never deletes.
"""
from datetime import date

import pytest
from sqlalchemy import text

from app.core.file_storage import file_storage
from app.core.platform.models import Documento, EntityType, Scadenza
from app.core.platform_services.document_type_sync import sync_document_types
from app.core.platform_services.documento_service import DocumentoService
from immobili import post_sync
from immobili.__manifest__ import manifest as immobili_manifest
from immobili.models import UnitaImmobiliare
from immobili.services.migrazione_ape import migra_ape

pytestmark = pytest.mark.integration

TENANT = "tenant_qa_test"


@pytest.fixture
def units(db_session, tmp_path, monkeypatch):
    monkeypatch.setattr(file_storage, "base_path", tmp_path)
    sync_document_types(db_session, {"immobili": immobili_manifest})
    db_session.execute(text("DELETE FROM immo_certificati_energetici"))
    result = []
    for i in range(2):
        u = UnitaImmobiliare(codice=f"TEST-APE-{i}", tipo="Appartamento", indirizzo="VIA X", citta="Milano")
        db_session.add(u)
        result.append(u)
    db_session.flush()
    (tmp_path / TENANT).mkdir(exist_ok=True)
    (tmp_path / TENANT / "ape1.pdf").write_bytes(b"%PDF-1.4 ape")
    return result


def _cert(db, unit_id, classe, emissione, scadenza, file_path=None):
    return db.execute(text("""
        INSERT INTO immo_certificati_energetici
            (unita_immobiliare_id, tecnico_id, classe_energetica, indice_prestazione_energetica,
             data_emissione, data_scadenza, numero_protocollo, file_path, note)
        VALUES (:u, 7, :c, 123.4, :e, :s, :p, :f, 'nota')
        RETURNING id
    """), {"u": unit_id, "c": classe, "e": emissione, "s": scadenza, "p": f"P-{classe}", "f": file_path}).scalar()


def _ape_docs(db, unit_id):
    return db.query(Documento).filter(
        Documento.entity_type == EntityType.IMMOBILE, Documento.entity_id == unit_id
    ).order_by(Documento.data_riferimento).all()


def test_migra_ape_counts(db_session, units):
    a, b = units
    _cert(db_session, a.id, "G", date(2012, 5, 1), date(2022, 5, 1))
    cid = _cert(db_session, a.id, "C", date(2023, 5, 1), date(2033, 5, 1), f"{TENANT}/ape1.pdf")
    _cert(db_session, b.id, "B", date(2020, 1, 10), date(2030, 1, 10))

    report = migra_ape(db_session, TENANT)
    assert report == {"letti": 3, "creati": 3, "saltati": 0, "senza_file": 2}

    old, new = _ape_docs(db_session, a.id)
    assert (old.stato, new.stato) == ("SOSTITUITO", "CORRENTE")
    assert old.sostituito_da_id == new.id
    assert new.dati == {"classe": "C", "ep_gl_nren": 123.4, "codice_identificativo": "P-C",
                        "tecnico_id": 7, "certificato_id": cid}
    assert new.data_riferimento == date(2023, 5, 1) and new.data_scadenza == date(2033, 5, 1)
    assert new.note == "nota"
    assert [f.file_path for f in new.files] == [f"{TENANT}/ape1.pdf"]
    assert new.tipo.codice == "APE"
    assert db_session.get(Scadenza, new.scadenza_id).data_scadenza == date(2033, 5, 1)
    assert old.scadenza_id is None


def test_migra_ape_idempotent(db_session, units):
    _cert(db_session, units[0].id, "B", date(2020, 1, 10), date(2030, 1, 10))
    migra_ape(db_session, TENANT)
    again = migra_ape(db_session, TENANT)
    assert again["creati"] == 0 and again["saltati"] == 1
    assert len(_ape_docs(db_session, units[0].id)) == 1


def test_migra_ape_without_rows(db_session, units):
    assert migra_ape(db_session, TENANT) == {"letti": 0, "creati": 0, "saltati": 0, "senza_file": 0}


def test_allinea_storico_fixes_two_current(db_session, units):
    service = DocumentoService(db_session, TENANT, None)
    a = units[0]
    for d in (date(2021, 1, 1), date(2024, 4, 4)):
        db_session.add(Documento(entity_type=EntityType.IMMOBILE, entity_id=a.id, tipo_documento="VISURA_CATASTALE",
                                 tipo_documento_id=service._tipo("VISURA_CATASTALE", EntityType.IMMOBILE).id,
                                 data_riferimento=d, stato="CORRENTE"))
    db_session.flush()
    assert service.allinea_storico("VISURA_CATASTALE") == 1
    old, new = _ape_docs(db_session, a.id)
    assert (old.stato, new.stato) == ("SOSTITUITO", "CORRENTE")
    assert service.allinea_storico("VISURA_CATASTALE") == 0


def test_allinea_scadenze_idempotent(db_session, units):
    service = DocumentoService(db_session, TENANT, None)
    db_session.add(Documento(entity_type=EntityType.IMMOBILE, entity_id=units[0].id, tipo_documento="ALTRO",
                             tipo_documento_id=service._tipo("POLIZZA_FABBRICATO", EntityType.IMMOBILE).id,
                             data_riferimento=date(2025, 1, 1), data_scadenza=date(2026, 1, 1), stato="CORRENTE"))
    db_session.flush()
    assert service.allinea_scadenze("POLIZZA_FABBRICATO") == 1
    assert service.allinea_scadenze("POLIZZA_FABBRICATO") == 0


def test_post_sync_runs_everything(db_session, units):
    _cert(db_session, units[0].id, "B", date(2020, 1, 10), date(2030, 1, 10))
    report = post_sync(db_session, TENANT)
    assert report["ape"]["creati"] == 1
    assert len(_ape_docs(db_session, units[0].id)) == 1
