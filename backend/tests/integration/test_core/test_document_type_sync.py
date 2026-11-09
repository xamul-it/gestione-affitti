"""
Manifest document_types -> public.core_tipi_documento sync
(app.core.platform_services.document_type_sync). Runs on the real dev DB
inside the rolled-back transaction of the integration db_session.
"""
import pytest
from sqlalchemy import text

from app.core.platform.models import TipoDocumento
from app.core.platform.models.tipo_documento_override import TipoDocumentoOverride
from app.core.platform_services.document_type_registry import DocumentTypeDefinition
from app.core.platform_services.document_type_sync import apply_override, sync_document_types

pytestmark = pytest.mark.integration


def _manifests(suffix):
    return {
        "mod_a": {"document_types": [
            {"codice": f"T_APE_{suffix}", "nome": "APE test", "categoria": "immobiliare",
             "entity_types": ["IMMOBILE"], "regime": "SOSTITUTIVO",
             "scadenza": {"mesi": 120, "da": "data_riferimento"}, "form": "mod_a.ape"},
        ]},
        "mod_b": {"document_types": [
            {"codice": f"T_POL_{suffix}", "nome": "Polizza test", "entity_types": ["IMMOBILE"],
             "regime": "SOSTITUTIVO", "scadenza": {"manuale": True}},
        ]},
    }


def _get(db, codice):
    return db.query(TipoDocumento).filter(TipoDocumento.codice == codice).one()


def test_sync_creates_and_updates(db_session, unique_suffix):
    report = sync_document_types(db_session, _manifests(unique_suffix))
    assert set(report.creati) == {f"T_APE_{unique_suffix}", f"T_POL_{unique_suffix}"}

    ape = _get(db_session, f"T_APE_{unique_suffix}")
    assert ape.modulo == "mod_a"
    assert ape.regime == "SOSTITUTIVO"
    assert ape.scadenza == {"mesi": 120, "da": "data_riferimento"}
    assert ape.richiede_scadenza is True
    assert ape.form == "mod_a.ape"
    assert ape.entity_types == ["IMMOBILE"]

    again = sync_document_types(db_session, _manifests(unique_suffix))
    assert again.creati == [] and again.aggiornati == []


def test_sync_updates_changed_fields(db_session, unique_suffix):
    sync_document_types(db_session, _manifests(unique_suffix))
    manifests = _manifests(unique_suffix)
    manifests["mod_a"]["document_types"][0]["nome"] = "APE rinominato"
    report = sync_document_types(db_session, manifests)
    assert report.aggiornati == [f"T_APE_{unique_suffix}"]
    assert _get(db_session, f"T_APE_{unique_suffix}").nome == "APE rinominato"


def test_sync_deactivates_missing(db_session, unique_suffix):
    sync_document_types(db_session, _manifests(unique_suffix))
    manifests = _manifests(unique_suffix)
    manifests["mod_b"]["document_types"] = []
    report = sync_document_types(db_session, manifests)
    assert f"T_POL_{unique_suffix}" in report.disattivati
    pol = _get(db_session, f"T_POL_{unique_suffix}")
    assert pol.attivo is False


def test_partial_sync_leaves_other_modules_alone(db_session, unique_suffix):
    sync_document_types(db_session, _manifests(unique_suffix))
    orphan = TipoDocumento(codice=f"T_OLD_{unique_suffix}", nome="Legacy", attivo=True)
    db_session.add(orphan)
    db_session.flush()

    only_a = {"mod_a": _manifests(unique_suffix)["mod_a"]}
    sync_document_types(db_session, only_a)
    assert _get(db_session, f"T_POL_{unique_suffix}").attivo is True
    assert _get(db_session, f"T_OLD_{unique_suffix}").attivo is True

    sync_document_types(db_session, _manifests(unique_suffix), complete=True)
    assert _get(db_session, f"T_OLD_{unique_suffix}").attivo is False


def test_reactivates_type_back_in_manifest(db_session, unique_suffix):
    sync_document_types(db_session, _manifests(unique_suffix))
    _get(db_session, f"T_APE_{unique_suffix}").attivo = False
    db_session.flush()
    sync_document_types(db_session, _manifests(unique_suffix))
    assert _get(db_session, f"T_APE_{unique_suffix}").attivo is True


def test_sync_keeps_tenant_override(db_session, unique_suffix):
    sync_document_types(db_session, _manifests(unique_suffix))
    ape = _get(db_session, f"T_APE_{unique_suffix}")
    override = TipoDocumentoOverride(tipo_documento_id=ape.id, nome="Mio nome", richiede_scadenza=False)
    db_session.add(override)
    db_session.flush()

    sync_document_types(db_session, _manifests(unique_suffix))
    merged = apply_override(_get(db_session, f"T_APE_{unique_suffix}"), override)
    assert merged["nome"] == "Mio nome"
    assert merged["richiede_scadenza"] is False
    assert merged["regime"] == "SOSTITUTIVO"
    assert merged["modulo"] == "mod_a"


def test_apply_override_deleted_hides_type(db_session, unique_suffix):
    sync_document_types(db_session, _manifests(unique_suffix))
    ape = _get(db_session, f"T_APE_{unique_suffix}")
    assert apply_override(ape, TipoDocumentoOverride(tipo_documento_id=ape.id, is_deleted=True)) is None
    assert apply_override(ape, None)["codice"] == f"T_APE_{unique_suffix}"


def test_duplicate_codice_across_modules(db_session, unique_suffix):
    manifests = _manifests(unique_suffix)
    manifests["mod_b"]["document_types"].append(
        {"codice": f"T_APE_{unique_suffix}", "nome": "Doppione", "regime": "CUMULATIVO"}
    )
    report = sync_document_types(db_session, manifests)
    assert _get(db_session, f"T_APE_{unique_suffix}").modulo == "mod_a"
    assert any("mod_a" in e and "mod_b" in e for e in report.errori)


@pytest.mark.parametrize("bad", [
    {"regime": "BOH"},
    {"entity_types": ["NON_ESISTE"]},
    {"scadenza": {"mesi": 0, "da": "data_riferimento"}},
    {"scadenza": {"giorni": 10}},
])
def test_invalid_definition_rejected(bad):
    with pytest.raises(ValueError):
        DocumentTypeDefinition(codice="X", nome="X", categoria="c", modulo_origine="m", **bad)


def test_invalid_entry_reported_not_synced(db_session, unique_suffix):
    manifests = _manifests(unique_suffix)
    manifests["mod_b"]["document_types"].append({"codice": f"T_BAD_{unique_suffix}", "nome": "x", "regime": "BOH"})
    report = sync_document_types(db_session, manifests)
    assert any(f"T_BAD_{unique_suffix}" in e for e in report.errori)
    assert db_session.execute(
        text("SELECT count(*) FROM public.core_tipi_documento WHERE codice = :c"), {"c": f"T_BAD_{unique_suffix}"}
    ).scalar() == 0
