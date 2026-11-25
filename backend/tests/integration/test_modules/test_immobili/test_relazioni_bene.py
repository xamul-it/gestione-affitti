"""
Relations of a bene (rights, tenancies, assignments) on core_relazioni:
/beni/{id}/relazioni, the types declared by immobili by family and the
per-bene-type visibility on the generic /relazioni API.
Spec: docs/superpowers/plans/2026-11-25-beni-fase3-relazione-unica.md, Task 3.
"""
from fractions import Fraction

import pytest
from fastapi.testclient import TestClient

from anagrafica_italiana.models import SoggettoAnagrafico
from anagrafica_italiana.models.soggetto_anagrafico import TipoSoggetto
from app.core.auth.dependencies import get_current_active_user
from app.core.auth.models import Permission, Role, User
from app.core.database import get_db, get_tenant_schema
from app.core.models import RuoloDisponibile
from app.core.models.tenant import Tenant, TenantModule
from app.main import app
from immobili.__manifest__ import manifest
from immobili.models import CategoriaCatastale, Terreno, TerrenoPorzione, UnitaImmobiliare
from immobili.services.relazioni_bene import FAMIGLIE, somma_quote_aperte
from tests.integration.conftest import TEST_TENANT

pytestmark = pytest.mark.integration


def _user(*perms, superuser=False):
    return User(id=1, username="t", is_superuser=superuser, is_active=True,
                roles=[Role(name="r", permissions=[Permission(name=p) for p in perms])])


@pytest.fixture
def ctx(db_session, unique_suffix):
    s = unique_suffix
    cat = db_session.query(CategoriaCatastale.id).filter(CategoriaCatastale.codice == "A/3").scalar()
    unita = UnitaImmobiliare(codice=f"RB-U-{s}", tipo="Appartamento", indirizzo="Via A 1", citta="Forlì",
                             categoria_catastale_id=cat)
    terreno = Terreno(codice=f"RB-T-{s}", comune="Forlì", provincia="FC",
                      porzioni=[TerrenoPorzione(qualita="SEMINATIVO", superficie_mq=1000)])
    soggetti = [SoggettoAnagrafico(tipo_soggetto=TipoSoggetto.PERSONA_FISICA, nome=f"N{i}", cognome=f"C{i}-{s}")
                for i in range(3)]
    db_session.add_all([unita, terreno, *soggetti])
    db_session.flush()
    app.dependency_overrides[get_db] = lambda: db_session
    app.dependency_overrides[get_tenant_schema] = lambda: TEST_TENANT
    app.dependency_overrides[get_current_active_user] = lambda: _user(
        "immobile.view", "immobile.edit", "terreno.view", "terreno.edit", "soggetto.view", "soggetto.edit")
    try:
        with TestClient(app) as client:
            yield client, unita, terreno, soggetti, db_session
    finally:
        for dep in (get_db, get_tenant_schema, get_current_active_user):
            app.dependency_overrides.pop(dep, None)


def _as(*perms):
    app.dependency_overrides[get_current_active_user] = lambda: _user(*perms)


def _post(client, bene, soggetto, tipo, **extra):
    return client.post(f"/api/v1/beni/{bene.id}/relazioni", json={"soggetto_id": soggetto.id, "tipo": tipo, **extra})


def test_manifest_dichiara_famiglie(db_session):
    tipi = {t["codice"]: t for t in manifest["relation_types"] if t["codice"] != "amministratore_condominio"}
    assert len(tipi) == 17
    assert all(t["famiglia"] in FAMIGLIE and t["fonte"] == "CORE" and t["entity_types"] == ["IMMOBILE"]
               and t["permesso_oggetto"] == "immobile.view" for t in tipi.values())
    reali = [t for t in tipi.values() if t["famiglia"] == "diritti_reali"]
    assert len(reali) == 8 and all(t["ammette_quota"] and t["solo_beni"] for t in reali)
    assert not any(t.get("ammette_quota") or t.get("solo_beni") for t in tipi.values() if t["famiglia"] != "diritti_reali")
    # The catalog (synced from the manifest) has them too.
    nel_catalogo = {r.codice: r.famiglia for r in db_session.query(RuoloDisponibile).filter_by(modulo_id="immobili", attivo=True)}
    assert {c: nel_catalogo.get(c) for c in tipi} == {c: t["famiglia"] for c, t in tipi.items()}
    assert "proprietario" not in nel_catalogo


def test_crea_diritto_con_quota(ctx):
    client, unita, _, (a, *_), db = ctx
    res = _post(client, unita, a, "proprieta", quota="1/2")
    assert res.status_code == 201, res.text
    body = res.json()
    assert body["avvisi"] == []
    assert body["relazione"]["quota"] == "1/2" and body["relazione"]["soggetto_id"] == a.id
    assert somma_quote_aperte(db, unita.id, "proprieta") == Fraction(1, 2)


def test_tre_terzi_senza_avviso(ctx):
    client, unita, _, soggetti, db = ctx
    for s in soggetti:
        res = _post(client, unita, s, "proprieta", quota="1/3")
        assert res.status_code == 201 and res.json()["avvisi"] == []
    assert somma_quote_aperte(db, unita.id, "proprieta") == 1


def test_avviso_quote_oltre_intero(ctx):
    client, unita, _, (a, b, _), _ = ctx
    assert _post(client, unita, a, "proprieta", quota="2/3").json()["avvisi"] == []
    res = _post(client, unita, b, "proprieta", quota="1/2")
    assert res.status_code == 201
    assert res.json()["avvisi"] == ["Le quote di Proprietà sul bene superano l'intero (7/6)"]


def test_tipo_di_altro_modulo_rifiutato(ctx):
    client, unita, _, (a, *_), _ = ctx
    assert _post(client, unita, a, "amministratore_condominio").status_code == 422
    assert _post(client, unita, a, "inesistente").status_code == 422


def test_quota_su_tipo_senza_quota_e_malformata(ctx):
    client, unita, _, (a, *_), _ = ctx
    assert _post(client, unita, a, "conduttore", quota="1/2").status_code == 422
    assert _post(client, unita, a, "proprieta", quota="meta").status_code == 422


def test_comodatario_con_registrazione(ctx):
    client, unita, _, (a, b, _), _ = ctx
    dati = {"registrazione_data": "2026-01-10", "registrazione_ufficio": "TNX", "registrazione_numero": "123"}
    res = _post(client, unita, a, "comodatario", dati=dati)
    assert res.status_code == 201 and res.json()["relazione"]["dati"] == dati
    assert _post(client, unita, b, "comodatario", dati={**dati, "registrazione_data": "10/01/2026"}).status_code == 422


def test_relazioni_raggruppate_per_famiglia(ctx):
    client, unita, _, (a, b, c), _ = ctx
    _post(client, unita, a, "proprieta", quota="1/1")
    _post(client, unita, b, "conduttore")
    _post(client, unita, c, "manutentore")
    _post(client, unita, c, "conduttore", data_inizio="2020-01-01", data_fine="2020-12-31")
    body = client.get(f"/api/v1/beni/{unita.id}/relazioni").json()
    assert set(body) == set(FAMIGLIE)
    assert [r["tipo"] for r in body["diritti_reali"]] == ["proprieta"]
    assert [r["tipo"] for r in body["godimento"]] == ["conduttore", "conduttore"]
    assert [r["tipo"] for r in body["incarichi"]] == ["manutentore"]
    riga = body["diritti_reali"][0]
    assert riga["soggetto_nome"].startswith("C0-") and (riga["quota_numeratore"], riga["quota_denominatore"]) == (1, 1)
    correnti = client.get(f"/api/v1/beni/{unita.id}/relazioni?solo_correnti=true").json()
    assert [r["soggetto_id"] for r in correnti["godimento"]] == [b.id]


def test_anagrafica_con_relazioni_non_eliminabile(ctx):
    client, unita, _, (a, *_), _ = ctx
    _post(client, unita, a, "proprieta", quota="1/1")
    _as("soggetto.view", "soggetto.delete", "soggetto.edit")
    res = client.delete(f"/api/v1/anagrafica/soggetti-v2/{a.id}")
    assert res.status_code == 400, res.text


def test_modulo_disattivato_nasconde(ctx):
    client, unita, _, (a, *_), db = ctx
    _post(client, unita, a, "proprieta", quota="1/1")
    url = "/api/v1/relazioni/?famiglia=diritti_reali"
    assert len(client.get(url).json()) == 1
    tenant = db.query(Tenant).filter_by(schema_name=TEST_TENANT).one()
    modulo = db.query(TenantModule).filter_by(tenant_id=tenant.id, module_id="immobili").one()
    modulo.enabled = False
    db.flush()
    assert client.get(url).json() == []
    modulo.enabled = True
    db.flush()
    assert len(client.get(url).json()) == 1


@pytest.mark.parametrize("bene, vista, modifica", [("unita", "immobile.view", "immobile.edit"),
                                                  ("terreno", "terreno.view", "terreno.edit")])
def test_permessi_per_tipo_di_bene(ctx, bene, vista, modifica):
    client, unita, terreno, (a, *_), _ = ctx
    obj = unita if bene == "unita" else terreno
    url = f"/api/v1/beni/{obj.id}/relazioni"
    _as("soggetto.view")
    assert client.get(url).status_code == 403
    assert _post(client, obj, a, "proprieta", quota="1/2").status_code == 403
    _as(vista)
    assert client.get(url).status_code == 200
    assert _post(client, obj, a, "proprieta", quota="1/2").status_code == 403
    _as(vista, modifica)
    assert _post(client, obj, a, "proprieta", quota="1/2").status_code == 201


def test_relazioni_filtrate_per_tipo_di_bene(ctx):
    client, unita, terreno, (a, b, _), _ = ctx
    r_unita = _post(client, unita, a, "proprieta", quota="1/1").json()["relazione"]["id"]
    r_terreno = _post(client, terreno, b, "proprieta", quota="1/1").json()["relazione"]["id"]
    elenco = lambda: {r["relazione_id"] for r in client.get("/api/v1/relazioni/?entity_type=IMMOBILE").json()}

    _as("soggetto.view", "terreno.view")
    assert elenco() == {r_terreno}
    assert _post(client, unita, b, "usufrutto", quota="1/2").status_code == 403
    _as("soggetto.view", "immobile.view")
    assert elenco() == {r_unita}
    assert _post(client, terreno, a, "usufrutto", quota="1/2").status_code == 403


def test_scrittura_generica_per_tipo_di_bene(ctx):
    """On /relazioni the write permission follows the bene type too: terreno.edit for a land parcel."""
    client, unita, terreno, (a, b, _), _ = ctx
    r_terreno = _post(client, terreno, a, "proprieta", quota="1/2").json()["relazione"]["id"]
    # immobile.edit (the type's own permesso_oggetto) is not enough on a land parcel.
    _as("soggetto.view", "soggetto.edit", "immobile.view", "immobile.edit", "terreno.view")
    corpo = {"soggetto_id": b.id, "tipo": "proprieta", "entity_type": "IMMOBILE", "entity_id": terreno.id, "quota": "1/2"}
    assert client.post("/api/v1/relazioni/", json=corpo).status_code == 403
    assert client.put(f"/api/v1/relazioni/{r_terreno}", json={"note": "x"}).status_code == 403
    assert client.delete(f"/api/v1/relazioni/{r_terreno}").status_code == 403
    _as("soggetto.view", "soggetto.edit", "terreno.view", "terreno.edit")
    assert client.post("/api/v1/relazioni/", json=corpo).status_code == 201
    assert client.put(f"/api/v1/relazioni/{r_terreno}", json={"note": "x"}).status_code == 200
    assert client.delete(f"/api/v1/relazioni/{r_terreno}").status_code == 204
