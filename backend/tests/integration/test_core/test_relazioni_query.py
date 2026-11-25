"""
Union of core relations (core_relazioni) and module-derived ones (providers
of immobili/affitti_lungo): app.core.platform_services.relazioni_query.
"""
from datetime import date, datetime

import pytest

from anagrafica_italiana.__manifest__ import manifest as anagrafica_manifest
from anagrafica_italiana.models import SoggettoAnagrafico
from anagrafica_italiana.models.soggetto_anagrafico import TipoSoggetto
from affitti_lungo.__manifest__ import manifest as affitti_manifest
from affitti_lungo import relations as affitti_relations
from affitti_lungo.models.affittuari import Affittuario
from affitti_lungo.models.tecnici import SpecializzazioneTecnico, Tecnico
from immobili.__manifest__ import manifest as immobili_manifest
from immobili.models import Condominio, UnitaImmobiliare
from immobili.services.relazioni_bene import crea_relazione_bene
from app.core.platform_services import relazioni_query as rq
from app.core.platform_services.relation_type_sync import sync_relation_types
from app.core.platform_services.relazione_service import RelazioneService

pytestmark = pytest.mark.integration

from tests.integration.conftest import TEST_TENANT as TENANT


@pytest.fixture(autouse=True)
def catalogo(db_session):
    sync_relation_types(db_session, {
        "immobili": immobili_manifest, "affitti_lungo": affitti_manifest,
        "anagrafica_italiana": anagrafica_manifest,
    })


def _soggetto(db, nome, cognome):
    s = SoggettoAnagrafico(tipo_soggetto=TipoSoggetto.PERSONA_FISICA, nome=nome, cognome=cognome)
    db.add(s)
    db.flush()
    return s


def _unita(db, suffix, n, indirizzo):
    u = UnitaImmobiliare(codice=f"RQ-{suffix}-{n}", tipo="Appartamento", indirizzo=indirizzo, citta="Milano")
    db.add(u)
    db.flush()
    return u


@pytest.fixture
def dati(db_session, unique_suffix):
    """Core relations on beni (type families of immobili) plus module-derived ones (affitti_lungo providers)."""
    db = db_session
    rossi, verdi, neri = _soggetto(db, "Mario", "Rossi"), _soggetto(db, "Luca", "Verdi"), _soggetto(db, "Ada", "Neri")
    u1, u2 = _unita(db, unique_suffix, 1, "Via Roma 1"), _unita(db, unique_suffix, 2, "Via Po 2")
    r1, _ = crea_relazione_bene(db, TENANT, None, u1.id, rossi.id, "proprieta", quota="1/2")
    r2, _ = crea_relazione_bene(db, TENANT, None, u2.id, rossi.id, "proprieta", quota="1/1",
                                data_inizio=date(2015, 3, 1), data_fine=date(2020, 1, 1))
    crea_relazione_bene(db, TENANT, None, u1.id, neri.id, "conduttore",
                        data_inizio=date(2019, 1, 1), data_fine=date(2021, 12, 31))
    # Module-derived: Verdi is a tenant (affittuario) without object; Neri a deactivated technician.
    a_verdi = Affittuario(soggetto_id=verdi.id)
    t_neri = Tecnico(soggetto_id=neri.id, specializzazione=SpecializzazioneTecnico.GEOMETRA, attivo=False,
                    updated_at=datetime(2020, 6, 1))
    db.add_all([a_verdi, t_neri])
    cond = Condominio(codice=f"RQ-{unique_suffix}", nome="Condominio Aurora", indirizzo="Via Po 2", citta="Milano")
    db.add(cond)
    db.flush()
    RelazioneService(db, TENANT).crea(rossi.id, "amministratore_condominio", entity_type="CONDOMINIO",
                                      entity_id=cond.id, data_inizio=date(2026, 1, 1))
    db.flush()
    return dict(rossi=rossi, verdi=verdi, neri=neri, u1=u1, u2=u2, r1=r1, r2=r2, cond=cond,
                a_verdi=a_verdi, t_neri=t_neri)


def test_diritto_righe_e_date(db_session, dati):
    righe = rq.elenca(db_session, TENANT, permessi={"*"}, soggetto_ids=[dati["rossi"].id], tipo="proprieta")
    by_entity = {r["entity_id"]: r for r in righe}
    assert set(by_entity) == {dati["u1"].id, dati["u2"].id}
    r1, r2 = by_entity[dati["u1"].id], by_entity[dati["u2"].id]
    assert r1["entity_type"] == "IMMOBILE" and r1["fonte"] == "CORE"
    assert r1["quota"] == "1/2"
    assert "Via Roma 1" in r1["descrizione"]
    assert r1["data_inizio"] is None and r1["corrente"] is True
    assert r1["relazione_id"] == dati["r1"].id
    assert r2["data_fine"] == date(2020, 1, 1) and r2["corrente"] is False


def test_modulo_senza_oggetto(db_session, dati):
    [r] = rq.elenca(db_session, TENANT, permessi={"*"}, soggetto_ids=[dati["verdi"].id], tipo="affittuario")
    assert r["fonte"] == "MODULO" and r["entity_id"] is None and r["corrente"] is True
    assert r["record_id"] == dati["a_verdi"].id


def test_modulo_cessato(db_session, dati):
    [r] = rq.elenca(db_session, TENANT, permessi={"*"}, soggetto_ids=[dati["neri"].id], tipo="tecnico")
    assert r["corrente"] is False
    assert rq.elenca(db_session, TENANT, permessi={"*"}, soggetto_ids=[dati["neri"].id],
                     tipo="tecnico", solo_correnti=True) == []


def test_core_insieme_ai_provider(db_session, dati):
    righe = rq.elenca(db_session, TENANT, permessi={"*"}, soggetto_ids=[dati["rossi"].id])
    amm = [r for r in righe if r["tipo"] == "amministratore_condominio"]
    assert len(amm) == 1
    assert amm[0]["descrizione"] == "Condominio Aurora"
    assert amm[0]["fonte"] == "CORE" and amm[0]["relazione_id"] is not None
    assert amm[0]["data_scadenza"] == date(2027, 1, 1)
    righe = rq.elenca(db_session, TENANT, permessi={"*"}, soggetto_ids=[dati["verdi"].id])
    assert {r["fonte"] for r in righe} == {"MODULO"}


def test_filtro_oggetto(db_session, dati):
    righe = rq.elenca(db_session, TENANT, permessi={"*"}, entity_type="CONDOMINIO", entity_id=dati["cond"].id)
    assert [r["soggetto_id"] for r in righe] == [dati["rossi"].id]


def test_relazioni_senza_permesso_non_si_vedono(db_session, dati):
    righe = rq.elenca(db_session, TENANT, permessi={"soggetto.view"}, soggetto_ids=[dati["rossi"].id])
    assert righe == []
    righe = rq.elenca(db_session, TENANT, permessi={"soggetto.view", "immobile.view"},
                      soggetto_ids=[dati["rossi"].id])
    assert {r["tipo"] for r in righe} == {"proprieta"}
    assert all(r["descrizione"] for r in righe if r["entity_id"])


def test_ruoli_per_soggetti_senza_permesso(db_session, dati):
    ruoli = rq.ruoli_per_soggetti(db_session, TENANT, [dati["rossi"].id, dati["neri"].id],
                                  permessi={"soggetto.view", "condominio.view"})
    assert [r["codice"] for r in ruoli[dati["rossi"].id]] == ["amministratore_condominio"]
    # Neri's tenancy on a bene needs immobile.view; the module-derived technician has no object permission.
    assert [r["codice"] for r in ruoli[dati["neri"].id]] == ["tecnico"]


def test_soggetti_con_ruolo_senza_permesso(db_session, dati):
    q = rq.soggetti_con_ruolo(db_session, TENANT, "proprieta", permessi={"soggetto.view"})
    assert list(db_session.execute(q)) == []


def test_provider_tabelle_assenti(db_session, dati, monkeypatch):
    assert affitti_relations.affittuari(db_session, "schema_inesistente") is None
    monkeypatch.setattr(affitti_relations, "affittuari", lambda db, schema: None)
    righe = rq.elenca(db_session, TENANT, permessi={"*"}, soggetto_ids=[dati["verdi"].id], tipo="affittuario")
    assert righe == []


def test_ruoli_per_soggetti(db_session, dati):
    ruoli = rq.ruoli_per_soggetti(db_session, TENANT, [dati["rossi"].id, dati["neri"].id], permessi={"*"})
    rossi = {r["codice"]: r["n"] for r in ruoli[dati["rossi"].id]}
    assert rossi == {"proprieta": 1, "amministratore_condominio": 1}
    neri = {r["codice"]: r["n"] for r in ruoli[dati["neri"].id]}
    assert neri == {"conduttore": 0, "tecnico": 0}


def test_soggetti_con_ruolo(db_session, dati):
    ids = {r[0] for r in db_session.execute(rq.soggetti_con_ruolo(db_session, TENANT, "proprieta", permessi={"*"}))}
    assert dati["rossi"].id in ids
    ids = {r[0] for r in db_session.execute(rq.soggetti_con_ruolo(db_session, TENANT, "conduttore", permessi={"*"}))}
    assert dati["neri"].id not in ids
    ids = {r[0] for r in db_session.execute(
        rq.soggetti_con_ruolo(db_session, TENANT, "conduttore", solo_correnti=False, permessi={"*"}))}
    assert dati["neri"].id in ids


def test_filtro_oggetto_senza_permesso_non_rivela_nulla(db_session, dati):
    righe = rq.elenca(db_session, TENANT, permessi={"soggetto.view"},
                      entity_type="IMMOBILE", entity_id=dati["u1"].id)
    assert righe == []
    righe = rq.elenca(db_session, TENANT, permessi={"soggetto.view", "immobile.view"},
                      entity_type="IMMOBILE", entity_id=dati["u1"].id)
    assert dati["rossi"].id in {r["soggetto_id"] for r in righe}
