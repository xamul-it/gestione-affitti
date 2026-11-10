"""
Manifest relation_types -> public.core_ruoli_disponibili sync
(app.core.platform_services.relation_type_sync), inside the rolled-back
transaction of the integration db_session.
"""
import pytest

from app.core.models import RuoloDisponibile
from app.core.platform_services.relation_type_registry import RelationTypeDefinition
from app.core.platform_services.relation_type_sync import sync_relation_types

pytestmark = pytest.mark.integration


def _manifests(s):
    return {
        f"mod_a_{s}": {"relation_types": [
            {"codice": f"amm_{s}", "nome": "Amministratore", "entity_types": ["CONDOMINIO"],
             "scadenza": {"mesi": 12, "da": "data_inizio"}, "unico_per_oggetto": True},
        ]},
        f"mod_b_{s}": {"relation_types": [
            {"codice": f"prop_{s}", "nome": "Proprietario", "entity_types": ["IMMOBILE"],
             "fonte": "MODULO", "provider": "x.y:z"},
        ]},
    }


def _get(db, codice, modulo):
    return db.query(RuoloDisponibile).filter_by(codice=codice, modulo_id=modulo).one()


def test_create_and_idempotent(db_session, unique_suffix):
    s = unique_suffix
    report = sync_relation_types(db_session, _manifests(s))
    assert set(report.creati) == {f"amm_{s}", f"prop_{s}"}
    amm = _get(db_session, f"amm_{s}", f"mod_a_{s}")
    assert amm.nome_display == "Amministratore"
    assert amm.fonte == "CORE"
    assert amm.scadenza == {"mesi": 12, "da": "data_inizio"}
    assert amm.unico_per_oggetto is True
    assert amm.entity_types == ["CONDOMINIO"]
    prop = _get(db_session, f"prop_{s}", f"mod_b_{s}")
    assert (prop.fonte, prop.provider) == ("MODULO", "x.y:z")
    again = sync_relation_types(db_session, _manifests(s))
    assert again.creati == [] and again.aggiornati == []


def test_update_and_reactivate(db_session, unique_suffix):
    s = unique_suffix
    sync_relation_types(db_session, _manifests(s))
    m = _manifests(s)
    m[f"mod_a_{s}"]["relation_types"][0]["nome"] = "Amministratore condominio"
    _get(db_session, f"amm_{s}", f"mod_a_{s}").attivo = False
    db_session.flush()
    report = sync_relation_types(db_session, m)
    assert report.aggiornati == [f"amm_{s}"]
    row = _get(db_session, f"amm_{s}", f"mod_a_{s}")
    assert (row.nome_display, row.attivo) == ("Amministratore condominio", True)


def test_complete_deactivates_orphans_and_duplicates(db_session, unique_suffix):
    s = unique_suffix
    sync_relation_types(db_session, _manifests(s))
    dup = RuoloDisponibile(codice=f"prop_{s}", modulo_id=f"old_{s}", nome_display="Doppio", attivo=True)
    orphan = RuoloDisponibile(codice=f"orf_{s}", modulo_id=f"old_{s}", nome_display="Orfano", attivo=True)
    pec = RuoloDisponibile(codice=f"pec_{s}", modulo_id="gestione_pec", nome_display="PEC", attivo=True)
    db_session.add_all([dup, orphan, pec])
    db_session.flush()

    sync_relation_types(db_session, _manifests(s))
    assert dup.attivo and orphan.attivo  # partial sync: other modules untouched

    report = sync_relation_types(db_session, _manifests(s), complete=True)
    assert dup.attivo is False and orphan.attivo is False
    assert pec.attivo is True  # modules using endpoints.register_roles keep their rows
    assert f"prop_{s}" in report.disattivati


def test_partial_deactivates_own_undeclared(db_session, unique_suffix):
    s = unique_suffix
    sync_relation_types(db_session, _manifests(s))
    m = _manifests(s)
    m[f"mod_b_{s}"]["relation_types"] = []
    report = sync_relation_types(db_session, m)
    assert _get(db_session, f"prop_{s}", f"mod_b_{s}").attivo is False
    assert f"prop_{s}" in report.disattivati


def test_invalid_entry_reported(db_session, unique_suffix):
    s = unique_suffix
    m = _manifests(s)
    m[f"mod_b_{s}"]["relation_types"].append({"codice": f"bad_{s}", "nome": "x", "fonte": "X"})
    report = sync_relation_types(db_session, m)
    assert any(f"bad_{s}" in e for e in report.errori)
    assert db_session.query(RuoloDisponibile).filter_by(codice=f"bad_{s}").count() == 0


@pytest.mark.parametrize("bad", [
    {"fonte": "X"},
    {"entity_types": ["NO"]},
    {"fonte": "MODULO"},
    {"scadenza": {"mesi": 12, "da": "data_riferimento"}},
    {"fonte": "MODULO", "provider": "a:b", "scadenza": {"manuale": True}},
])
def test_invalid_definition_rejected(bad):
    with pytest.raises(ValueError):
        RelationTypeDefinition(codice="x", nome="X", modulo="m", **bad)
