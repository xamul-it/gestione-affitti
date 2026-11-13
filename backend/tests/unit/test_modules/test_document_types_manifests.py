"""
The document types declared by the anagrafica_italiana and immobili
manifests are valid and keep the codes already stored in the database
(documents reference the rows; the old seed's codes must not change).
"""
import pytest

from anagrafica_italiana.__manifest__ import manifest as anagrafica_manifest
from immobili.__manifest__ import manifest as immobili_manifest
from app.core.platform_services.document_type_registry import DocumentTypeDefinition

# Codes created by the former anagrafica seed (seeds/seed_tipi_documento.py).
OLD_SEED_CODES = {
    "CARTA_IDENTITA", "PASSAPORTO", "PATENTE", "CODICE_FISCALE", "PARTITA_IVA",
    "VISURA_CAMERALE", "CERTIFICATO_CCIAA", "ATTO_COSTITUTIVO", "STATUTO", "DURC",
    "CERTIFICATO_REGISTRO_IMPRESE", "BILANCIO", "CERTIFICATO_PROFESSIONALE",
    "ISCRIZIONE_ALBO", "CONTRATTO", "DOCUMENTO_GENERICO",
}

IMMOBILI_CODES = {
    "VISURA_CATASTALE", "PLANIMETRIA_CATASTALE", "VARIAZIONE_CATASTALE", "APE",
    "ATTO_PROVENIENZA", "CONFORMITA_IMPIANTO", "LIBRETTO_IMPIANTO", "AGIBILITA",
    "TITOLO_EDILIZIO", "POLIZZA_FABBRICATO", "ALTRO_IMMOBILE",
    "ESTRATTO_MAPPA", "CDU", "CONTRATTO_AFFITTO_AGRARIO",
}


def _codes(manifest):
    return [t["codice"] for t in manifest["document_types"]]


@pytest.mark.parametrize("module_name,manifest", [
    ("anagrafica_italiana", anagrafica_manifest),
    ("immobili", immobili_manifest),
])
def test_manifests_validate(module_name, manifest):
    codes = _codes(manifest)
    assert len(codes) == len(set(codes))
    for entry in manifest["document_types"]:
        fields = {k: v for k, v in entry.items() if k != "codice"}
        DocumentTypeDefinition(codice=entry["codice"], modulo_origine=module_name, **fields)


def test_existing_db_codes_preserved():
    assert OLD_SEED_CODES <= set(_codes(anagrafica_manifest))
    assert "PATENTE_GUIDA" not in _codes(anagrafica_manifest)


def test_visura_owned_by_immobili():
    assert "VISURA_CATASTALE" in _codes(immobili_manifest)
    assert "VISURA_CATASTALE" not in _codes(anagrafica_manifest)


def test_immobili_types():
    types = {t["codice"]: t for t in immobili_manifest["document_types"]}
    assert set(types) == IMMOBILI_CODES
    assert all(t["entity_types"] == ["IMMOBILE"] for t in types.values())
    assert types["APE"]["regime"] == "SOSTITUTIVO"
    assert types["APE"]["scadenza"] == {"mesi": 120, "da": "data_riferimento"}
    assert types["APE"]["form"] == "immobili.ape"
    assert types["VISURA_CATASTALE"]["form"] == "immobili.visura"
    assert types["CONFORMITA_IMPIANTO"]["sottotipi"] == ["ELETTRICO", "GAS", "TERMICO", "IDRICO"]
    assert types["POLIZZA_FABBRICATO"]["scadenza"] == {"manuale": True}
    assert types["VARIAZIONE_CATASTALE"]["regime"] == "CUMULATIVO"


def test_anagrafica_identity_documents_supersede():
    types = {t["codice"]: t for t in anagrafica_manifest["document_types"]}
    for codice in ("CARTA_IDENTITA", "PASSAPORTO", "PATENTE"):
        assert types[codice]["regime"] == "SOSTITUTIVO"
        assert types[codice]["scadenza"] == {"manuale": True}
        assert types[codice]["entity_types"] == ["SOGGETTO_ANAGRAFICO"]
