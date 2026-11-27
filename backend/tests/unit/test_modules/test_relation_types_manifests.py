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
    assert set(_types("immobili")) == {
        "proprieta", "nuda_proprieta", "usufrutto", "uso", "abitazione", "superficie", "enfiteusi",
        "diritto_reale_altro", "conduttore", "affittuario_agrario", "comodatario", "godimento_altro",
        "manutentore", "terzo_responsabile_impianto", "responsabile_impianto", "tecnico_incaricato",
        "incarico_altro", "amministratore_condominio",
    }
    assert set(_types("affitti_lungo")) == {"affittuario", "tecnico"}
    assert set(_types("anagrafica_italiana")) == {"ruolo_azienda"}


def test_amministratore_condominio():
    t = _types("immobili")["amministratore_condominio"]
    assert t["scadenza"] == {"mesi": 12, "da": "data_inizio"}
    assert t["unico_per_oggetto"] is True
    assert t["entity_types"] == ["CONDOMINIO"]
    assert t.get("fonte", "CORE") == "CORE"
    assert t["permesso_oggetto"] == "condominio.view"


FAMIGLIE_BENI = {
    "diritti_reali": {"proprieta", "nuda_proprieta", "usufrutto", "uso", "abitazione", "superficie",
                      "enfiteusi", "diritto_reale_altro"},
    "godimento": {"conduttore", "affittuario_agrario", "comodatario", "godimento_altro"},
    "incarichi": {"manutentore", "terzo_responsabile_impianto", "responsabile_impianto",
                  "tecnico_incaricato", "incarico_altro"},
}


def test_tipi_dei_beni_per_famiglia():
    tipi = _types("immobili")
    for famiglia, codici in FAMIGLIE_BENI.items():
        for codice in codici:
            t = tipi[codice]
            assert t["famiglia"] == famiglia
            assert t["fonte"] == "CORE" and "provider" not in t
            # Rights only on beni; tenancies and assignments also on a raggruppamento (phase 4a).
            atteso = ["IMMOBILE"] if famiglia == "diritti_reali" else ["IMMOBILE", "RAGGRUPPAMENTO"]
            assert t["entity_types"] == atteso
            assert t["permesso_oggetto"] == "immobile.view"
            assert t.get("ammette_quota", False) is (famiglia == "diritti_reali")
            assert t.get("solo_beni", False) is (famiglia == "diritti_reali")


def test_hook_permessi_dei_beni():
    assert immobili_manifest["object_permissions"] == {
        "IMMOBILE": "immobili.services.relazioni_bene:permessi_vista",
        "RAGGRUPPAMENTO": "immobili.services.relazioni_bene:permessi_vista_raggruppamenti"}


def test_ruolo_azienda():
    t = _types("anagrafica_italiana")["ruolo_azienda"]
    assert t["entity_types"] == ["SOGGETTO_ANAGRAFICO"]
    assert t["sottotipi_fonte"] == "anag_ruoli_azienda_tipi"


def test_legacy_role_lists_removed():
    assert "ruoli_disponibili" not in anagrafica_manifest
    assert "ruoli_disponibili" not in affitti_manifest
    assert "register_roles" not in (affitti_manifest.get("endpoints") or {})
