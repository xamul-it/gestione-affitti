"""
Raggruppamenti API, relations on a ramo and their inheritance on the beni.
Plan: docs/superpowers/plans/2026-11-25-beni-fase4a-raggruppamenti.md, Task 3.
"""
from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient

from anagrafica_italiana.models import SoggettoAnagrafico
from anagrafica_italiana.models.soggetto_anagrafico import TipoSoggetto
from app.core.auth.dependencies import get_current_active_user
from app.core.auth.models import Permission, Role, User
from app.core.database import get_db, get_tenant_schema
from app.core.platform_services import object_permissions
from app.main import app
from immobili.models import Terreno, TerrenoPorzione, UnitaImmobiliare
from immobili.services.raggruppamenti import crea_raggruppamento, sposta_bene
from immobili.services.relazioni_bene import relazioni_effettive
from tests.integration.conftest import TEST_TENANT

pytestmark = pytest.mark.integration

TUTTI = ("immobile.view", "immobile.edit", "terreno.view", "terreno.edit", "soggetto.view", "soggetto.edit")


def _user(*perms):
    return User(id=1, username="t", is_superuser=False, is_active=True,
                roles=[Role(name="r", permissions=[Permission(name=p) for p in perms])])


def _as(*perms):
    app.dependency_overrides[get_current_active_user] = lambda: _user(*perms)


@pytest.fixture
def ctx(db_session, unique_suffix):
    """Complesso C › Edificio E; unit U and land parcel T in E; three soggetti."""
    s = unique_suffix
    c = crea_raggruppamento(db_session, "COMPLESSO", f"Complesso {s}")
    e = crea_raggruppamento(db_session, "EDIFICIO", f"Edificio A {s}", padre_id=c.id)
    u = UnitaImmobiliare(codice=f"RA-U-{s}", tipo="Appartamento", indirizzo="Via A 1", citta="Forlì")
    t = Terreno(codice=f"RA-T-{s}", comune="Forlì", provincia="FC",
                porzioni=[TerrenoPorzione(qualita="SEMINATIVO", superficie_mq=1000)])
    soggetti = [SoggettoAnagrafico(tipo_soggetto=TipoSoggetto.PERSONA_FISICA, nome=f"N{i}", cognome=f"C{i}-{s}")
                for i in range(3)]
    db_session.add_all([u, t, *soggetti])
    db_session.flush()
    sposta_bene(db_session, u, e.id)
    sposta_bene(db_session, t, e.id)
    app.dependency_overrides[get_db] = lambda: db_session
    app.dependency_overrides[get_tenant_schema] = lambda: TEST_TENANT
    _as(*TUTTI)
    try:
        with TestClient(app) as client:
            yield client, db_session, c, e, u, t, soggetti
    finally:
        for dep in (get_db, get_tenant_schema, get_current_active_user):
            app.dependency_overrides.pop(dep, None)


def _rel_ramo(client, ramo, soggetto, tipo, **extra):
    return client.post(f"/api/v1/raggruppamenti/{ramo.id}/relazioni",
                       json={"soggetto_id": soggetto.id, "tipo": tipo, **extra})


def _rel_bene(client, bene, soggetto, tipo, **extra):
    return client.post(f"/api/v1/beni/{bene.id}/relazioni", json={"soggetto_id": soggetto.id, "tipo": tipo, **extra})


# --- inheritance ---------------------------------------------------------------

def test_conduttore_su_ramo_ereditato(ctx):
    client, _, _, e, u, _, (a, b, _) = ctx
    assert _rel_ramo(client, e, a, "conduttore").status_code == 201
    assert _rel_bene(client, u, b, "comodatario").status_code == 201
    godimento = client.get(f"/api/v1/beni/{u.id}/relazioni").json()["godimento"]
    per_tipo = {r["tipo"]: r for r in godimento}
    assert per_tipo["conduttore"]["provenienza"] == {"raggruppamento_id": e.id, "nome": e.nome, "tipo": "EDIFICIO"}
    assert per_tipo["comodatario"]["provenienza"] is None


def test_eredita_due_livelli(ctx):
    client, _, c, _, u, _, (a, *_) = ctx
    _rel_ramo(client, c, a, "manutentore")
    incarichi = client.get(f"/api/v1/beni/{u.id}/relazioni").json()["incarichi"]
    assert [(r["tipo"], r["provenienza"]["raggruppamento_id"]) for r in incarichi] == [("manutentore", c.id)]


def test_stesso_tipo_bene_e_ramo(ctx):
    client, _, _, e, u, _, (a, b, _) = ctx
    _rel_ramo(client, e, a, "manutentore")
    _rel_bene(client, u, b, "manutentore")
    incarichi = client.get(f"/api/v1/beni/{u.id}/relazioni").json()["incarichi"]
    assert sorted((r["provenienza"] or {}).get("raggruppamento_id", 0) for r in incarichi) == [0, e.id]


def test_effettive_alla_data(ctx):
    client, db, _, e, u, _, (a, *_) = ctx
    ieri = date.today() - timedelta(days=1)
    _rel_ramo(client, e, a, "manutentore", data_inizio=str(ieri - timedelta(days=60)), data_fine=str(ieri))
    assert relazioni_effettive(db, u.id, date.today()) == []
    passato = relazioni_effettive(db, u.id, ieri - timedelta(days=30))
    assert [(x.tipo.codice, x.provenienza.id) for x in passato] == [("manutentore", e.id)]
    assert len(relazioni_effettive(db, u.id)) == 1


def test_diritto_reale_su_ramo_rifiutato(ctx):
    client, db, _, e, _, _, (a, *_) = ctx
    assert _rel_ramo(client, e, a, "proprieta", quota="1/1").status_code == 422
    corpo = {"soggetto_id": a.id, "tipo": "proprieta", "entity_type": "RAGGRUPPAMENTO", "entity_id": e.id,
             "quota": "1/1"}
    assert client.post("/api/v1/relazioni/", json=corpo).status_code == 422
    assert client.get(f"/api/v1/raggruppamenti/{e.id}/relazioni").json()["diritti_reali"] == []


def test_relazioni_del_ramo_solo_proprie(ctx):
    client, _, c, e, _, _, (a, b, _) = ctx
    _rel_ramo(client, c, a, "manutentore")
    _rel_ramo(client, e, b, "conduttore")
    body = client.get(f"/api/v1/raggruppamenti/{e.id}/relazioni").json()
    assert [r["soggetto_id"] for r in body["godimento"]] == [b.id] and body["incarichi"] == []


# --- tree API ------------------------------------------------------------------

def test_crea_e_dettaglio(ctx):
    client, _, c, e, u, t, _ = ctx
    res = client.post("/api/v1/raggruppamenti/", json={"tipo": "ALTRO", "nome": "Cantine", "padre_id": e.id})
    assert res.status_code == 201, res.text
    nuovo = res.json()["id"]
    det = client.get(f"/api/v1/raggruppamenti/{e.id}").json()
    assert [p["id"] for p in det["percorso"]] == [c.id, e.id]
    assert [f["id"] for f in det["figli"]] == [nuovo]
    assert {b["id"] for b in det["beni"]} == {u.id, t.id}
    assert client.post("/api/v1/raggruppamenti/", json={"tipo": "X", "nome": "y"}).status_code == 422


def test_lista_albero_e_piatta(ctx):
    client, _, c, e, u, _, _ = ctx
    albero = client.get("/api/v1/raggruppamenti/?vista=albero").json()
    radice = next(r for r in albero if r["id"] == c.id)
    assert [f["id"] for f in radice["figli"]] == [e.id]
    assert u.id in {b["id"] for b in radice["figli"][0]["beni"]}
    piatta = {r["id"]: r for r in client.get("/api/v1/raggruppamenti/?vista=piatta").json()}
    assert piatta[e.id]["percorso"] == f"{c.nome} › {e.nome}"


def test_archiviati_nascosti(ctx):
    client, _, _, e, _, _, _ = ctx
    assert client.put(f"/api/v1/raggruppamenti/{e.id}", json={"attivo": False}).status_code == 200
    assert e.id not in {r["id"] for r in client.get("/api/v1/raggruppamenti/?vista=piatta").json()}
    con = client.get("/api/v1/raggruppamenti/?vista=piatta&includi_archiviati=true").json()
    assert e.id in {r["id"] for r in con}


def test_sposta_ciclo(ctx):
    client, _, c, e, _, _, _ = ctx
    res = client.post(f"/api/v1/raggruppamenti/{c.id}/sposta", json={"padre_id": e.id})
    assert res.status_code == 422
    assert client.post(f"/api/v1/raggruppamenti/{e.id}/sposta", json={"padre_id": None}).json()["padre_id"] is None


def test_delete_ramo_con_relazioni(ctx):
    client, _, _, e, _, _, (a, *_) = ctx
    _rel_ramo(client, e, a, "manutentore")
    res = client.delete(f"/api/v1/raggruppamenti/{e.id}")
    assert res.status_code == 409
    assert res.json()["detail"] == "Il raggruppamento ha relazioni o documenti: archivialo"


def test_delete_ramo_vuoto(ctx):
    client, db, c, e, u, _, _ = ctx
    assert client.delete(f"/api/v1/raggruppamenti/{e.id}").status_code == 204
    db.refresh(u)
    assert u.raggruppamento_id == c.id


def test_percorso_bene_e_patch(ctx):
    client, _, c, e, u, _, _ = ctx
    bene = client.get(f"/api/v1/beni/{u.id}").json()
    assert bene["raggruppamento_id"] == e.id and [p["id"] for p in bene["percorso"]] == [c.id, e.id]
    res = client.patch(f"/api/v1/beni/{u.id}/raggruppamento", json={"raggruppamento_id": None})
    assert res.status_code == 200 and res.json()["raggruppamento_id"] is None and res.json()["percorso"] == []
    res = client.patch(f"/api/v1/beni/{u.id}/raggruppamento", json={"raggruppamento_id": c.id})
    assert res.json()["raggruppamento_id"] == c.id


# --- permissions -----------------------------------------------------------------

def test_solo_terreni(ctx):
    client, _, _, e, u, t, (a, *_) = ctx
    _rel_ramo(client, e, a, "manutentore")
    _as("terreno.view", "soggetto.view")
    det = client.get(f"/api/v1/raggruppamenti/{e.id}")
    assert det.status_code == 200 and {b["id"] for b in det.json()["beni"]} == {t.id}
    assert [r["tipo"] for r in client.get(f"/api/v1/beni/{t.id}/relazioni").json()["incarichi"]] == ["manutentore"]
    _as("terreno.view", "terreno.edit", "soggetto.view")
    assert client.patch(f"/api/v1/beni/{u.id}/raggruppamento", json={"raggruppamento_id": None}).status_code in (403, 404)


def test_permessi_ramo(ctx):
    client, _, _, e, _, _, _ = ctx
    _as("soggetto.view")
    assert client.get(f"/api/v1/raggruppamenti/{e.id}").status_code == 403
    _as("terreno.view")
    assert client.put(f"/api/v1/raggruppamenti/{e.id}", json={"nome": "x"}).status_code == 403
    _as("terreno.view", "terreno.edit")
    assert client.put(f"/api/v1/raggruppamenti/{e.id}", json={"nome": "Nuovo nome"}).status_code == 200
    _as("immobile.view")
    assert client.get(f"/api/v1/raggruppamenti/{e.id}/relazioni").status_code == 403


def test_hook_ramo_piu_righe(ctx):
    _, db, _, e, _, _, _ = ctx
    for vista in ("immobile.view", "terreno.view"):
        assert object_permissions.oggetto_visibile(
            db, TEST_TENANT, {vista}, entity_type="RAGGRUPPAMENTO", entity_id=e.id, permesso_oggetto=None)
    assert object_permissions.permessi_modifica(
        db, TEST_TENANT, entity_type="RAGGRUPPAMENTO", entity_id=e.id) == {"immobile.edit", "terreno.edit"}


def test_anagrafica_con_relazione_su_ramo_non_eliminabile(ctx):
    client, _, _, e, _, _, (a, *_) = ctx
    _rel_ramo(client, e, a, "manutentore")
    _as("soggetto.view", "soggetto.delete", "soggetto.edit")
    assert client.delete(f"/api/v1/anagrafica/soggetti-v2/{a.id}").status_code == 400


# --- writes that change what the beni inherit need the edit permission of every bene type below --------

SOLO_TERRENI = ("terreno.view", "terreno.edit", "soggetto.view", "soggetto.edit")


def test_relazione_su_ramo_misto_richiede_tutti_i_tipi(ctx):
    client, _, c, e, _, _, (a, *_) = ctx
    _as(*SOLO_TERRENI)
    assert _rel_ramo(client, e, a, "manutentore").status_code == 403
    # Through the generic API too.
    corpo = {"soggetto_id": a.id, "tipo": "manutentore", "entity_type": "RAGGRUPPAMENTO", "entity_id": c.id}
    assert client.post("/api/v1/relazioni/", json=corpo).status_code == 403


def test_relazione_su_ramo_di_soli_terreni(ctx, db_session):
    client, db, _, _, _, t, (a, *_) = ctx
    fondo = crea_raggruppamento(db, "FONDO", "Fondo solo terreni")
    sposta_bene(db, t, fondo.id)
    _as(*SOLO_TERRENI)
    assert _rel_ramo(client, fondo, a, "affittuario_agrario").status_code == 201
    corpo = {"soggetto_id": a.id, "tipo": "manutentore", "entity_type": "RAGGRUPPAMENTO", "entity_id": fondo.id}
    assert client.post("/api/v1/relazioni/", json=corpo).status_code == 201


def test_modifica_relazione_del_ramo_misto(ctx):
    client, _, _, e, _, _, (a, *_) = ctx
    rid = _rel_ramo(client, e, a, "manutentore").json()["relazione"]["id"]
    _as(*SOLO_TERRENI)
    assert client.put(f"/api/v1/relazioni/{rid}", json={"note": "x"}).status_code == 403


def test_sposta_e_cancella_ramo_misto(ctx):
    client, _, c, e, _, _, _ = ctx
    _as(*SOLO_TERRENI)
    assert client.post(f"/api/v1/raggruppamenti/{e.id}/sposta", json={"padre_id": None}).status_code == 403
    assert client.delete(f"/api/v1/raggruppamenti/{c.id}").status_code == 403
    # Renaming or archiving does not change what the beni inherit: either edit permission is enough.
    assert client.put(f"/api/v1/raggruppamenti/{e.id}", json={"nome": "Rinominato"}).status_code == 200


def test_permessi_modifica_richiesti_hook(ctx):
    _, db, c, e, _, _, _ = ctx
    assert object_permissions.permessi_modifica_richiesti(
        db, TEST_TENANT, entity_type="RAGGRUPPAMENTO", entity_id=c.id) == {"immobile.edit", "terreno.edit"}
    vuoto = crea_raggruppamento(db, "ALTRO", "Vuoto")
    assert object_permissions.permessi_modifica_richiesti(
        db, TEST_TENANT, entity_type="RAGGRUPPAMENTO", entity_id=vuoto.id) == set()
    assert object_permissions.permessi_modifica_richiesti(
        db, TEST_TENANT, entity_type="IMMOBILE", entity_id=1) is None


def test_descrizione_del_ramo_nelle_relazioni_dell_anagrafica(ctx):
    """The cross-module relation list (soggetto page) names the ramo."""
    client, _, _, e, _, _, (a, *_) = ctx
    _rel_ramo(client, e, a, "manutentore")
    righe = [r for r in client.get(f"/api/v1/relazioni/?soggetto_id={a.id}").json()
             if r["entity_type"] == "RAGGRUPPAMENTO"]
    assert [r["descrizione"] for r in righe] == [e.nome]
