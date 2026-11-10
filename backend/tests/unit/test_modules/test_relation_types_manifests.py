"""
Relation types declared by the module manifests (spec
docs/superpowers/specs/2026-11-10-relazioni-ruoli-soggetti-design.md).
"""
import pytest

from affitti_lungo.__manifest__ import manifest as affitti_manifest
from anagrafica_italiana.__manifest__ import manifest as anagrafica_manifest
from immobili.__manifest__ import manifest as immobili_manifest
from app.core.platform_services.relation_type_registry import RelationTypeDefinition

MANIFESTS = {
    "immobili": immobili_manifest,
    "affitti_lungo": affitti_manifest,
    "anagrafica_italiana": anagrafica_manifest,
}


def _types(name):
    return {t["codice"]: t for t in MANIFESTS[name]["relation_types"]}


@pytest.mark.parametrize("module_name", list(MANIFESTS))
def test_relation_types_validate(module_name):
    for entry in MANIFESTS[module_name]["relation_types"]:
        RelationTypeDefinition(modulo=module_name, **entry)


def test_expected_codes():
    assert set(_types("immobili")) == {"proprietario", "conduttore", "amministratore_condominio"}
    assert set(_types("affitti_lungo")) == {"affittuario", "tecnico"}
    assert set(_types("anagrafica_italiana")) == {"ruolo_azienda"}


def test_amministratore_condominio():
    t = _types("immobili")["amministratore_condominio"]
    assert t["scadenza"] == {"mesi": 12, "da": "data_inizio"}
    assert t["unico_per_oggetto"] is True
    assert t["entity_types"] == ["CONDOMINIO"]
    assert t.get("fonte", "CORE") == "CORE"
    assert t["permesso_oggetto"] == "condominio.view"


def test_module_sourced_roles():
    for codice in ("proprietario", "conduttore"):
        t = _types("immobili")[codice]
        assert t["fonte"] == "MODULO"
        assert t["entity_types"] == ["IMMOBILE"]
        assert t["permesso_oggetto"] == "immobile.view"
    assert _types("immobili")["proprietario"]["provider"] == "immobili.relations:proprietari"
    assert _types("immobili")["conduttore"]["provider"] == "immobili.relations:conduttori"


def test_ruolo_azienda():
    t = _types("anagrafica_italiana")["ruolo_azienda"]
    assert t["entity_types"] == ["SOGGETTO_ANAGRAFICO"]
    assert t["sottotipi_fonte"] == "anag_ruoli_azienda_tipi"


def test_legacy_role_lists_removed():
    assert "ruoli_disponibili" not in anagrafica_manifest
    assert "ruoli_disponibili" not in affitti_manifest
    assert "register_roles" not in (affitti_manifest.get("endpoints") or {})
