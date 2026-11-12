"""
Union of core relations (core_relazioni) and module-derived ones (providers
of immobili/affitti_lungo): app.core.platform_services.relazioni_query.
"""
from datetime import date
from decimal import Decimal

import pytest

from anagrafica_italiana.__manifest__ import manifest as anagrafica_manifest
from anagrafica_italiana.models import SoggettoAnagrafico
from anagrafica_italiana.models.soggetto_anagrafico import TipoSoggetto
from affitti_lungo.__manifest__ import manifest as affitti_manifest
from immobili import relations as immobili_relations
from immobili.__manifest__ import manifest as immobili_manifest
from immobili.models import (
    AssegnazioneConduttore, Condominio, Conduttore, DirittoImmobile, Proprietario, UnitaImmobiliare,
)
from immobili.models.diritti_immobile import TipoDiritto
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
    db = db_session
    rossi, verdi, neri = _soggetto(db, "Mario", "Rossi"), _soggetto(db, "Luca", "Verdi"), _soggetto(db, "Ada", "Neri")
    u1, u2 = _unita(db, unique_suffix, 1, "Via Roma 1"), _unita(db, unique_suffix, 2, "Via Po 2")
    p_rossi, p_verdi = Proprietario(soggetto_id=rossi.id), Proprietario(soggetto_id=verdi.id)
    db.add_all([p_rossi, p_verdi])
    db.flush()
    db.add_all([
        DirittoImmobile(bene_id=u1.id, proprietario_id=p_rossi.id,
                        tipo_diritto=TipoDiritto.COMPROPRIETARIO, quota_percentuale=Decimal("50.00"),
                        data_inizio=""),
        DirittoImmobile(bene_id=u2.id, proprietario_id=p_rossi.id,
                        tipo_diritto=TipoDiritto.PROPRIETARIO, quota_percentuale=Decimal("100.00"),
                        data_inizio="2015-03-01", data_fine="2020-01-01"),
    ])
    c_neri = Conduttore(soggetto_id=neri.id)
    db.add(c_neri)
    db.flush()
    db.add(AssegnazioneConduttore(bene_id=u1.id, conduttore_id=c_neri.id,
                                  data_inizio=date(2019, 1, 1), data_fine=date(2021, 12, 31)))
    cond = Condominio(codice=f"RQ-{unique_suffix}", nome="Condominio Aurora", indirizzo="Via Po 2", citta="Milano")
    db.add(cond)
    db.flush()
    RelazioneService(db, TENANT).crea(rossi.id, "amministratore_condominio", entity_type="CONDOMINIO",
                                      entity_id=cond.id, data_inizio=date(2026, 1, 1))
    db.flush()
    return dict(rossi=rossi, verdi=verdi, neri=neri, u1=u1, u2=u2, p_rossi=p_rossi, cond=cond)


def test_proprietario_righe_e_date(db_session, dati):
    righe = rq.elenca(db_session, TENANT, permessi={"*"}, soggetto_ids=[dati["rossi"].id], tipo="proprietario")
    by_entity = {r["entity_id"]: r for r in righe}
    assert set(by_entity) == {dati["u1"].id, dati["u2"].id}
    r1, r2 = by_entity[dati["u1"].id], by_entity[dati["u2"].id]
    assert r1["entity_type"] == "IMMOBILE"
    assert r1["descrizione"] == "Via Roma 1, Milano — Comproprietà 50%"
    assert r1["data_inizio"] is None and r1["corrente"] is True
    assert r1["record_id"] == dati["p_rossi"].id
    assert r2["data_fine"] == date(2020, 1, 1) and r2["corrente"] is False


def test_proprietario_senza_diritti(db_session, dati):
    [r] = rq.elenca(db_session, TENANT, permessi={"*"}, soggetto_ids=[dati["verdi"].id], tipo="proprietario")
    assert r["entity_id"] is None and r["corrente"] is True


def test_conduttore_cessato(db_session, dati):
    [r] = rq.elenca(db_session, TENANT, permessi={"*"}, soggetto_ids=[dati["neri"].id], tipo="conduttore")
    assert r["corrente"] is False
    assert rq.elenca(db_session, TENANT, permessi={"*"}, soggetto_ids=[dati["neri"].id],
                     tipo="conduttore", solo_correnti=True) == []


def test_core_insieme_ai_provider(db_session, dati):
    righe = rq.elenca(db_session, TENANT, permessi={"*"}, soggetto_ids=[dati["rossi"].id])
    amm = [r for r in righe if r["tipo"] == "amministratore_condominio"]
    assert len(amm) == 1
    assert amm[0]["descrizione"] == "Condominio Aurora"
    assert amm[0]["fonte"] == "CORE" and amm[0]["relazione_id"] is not None
    assert amm[0]["data_scadenza"] == date(2027, 1, 1)


def test_filtro_oggetto(db_session, dati):
    righe = rq.elenca(db_session, TENANT, permessi={"*"}, entity_type="CONDOMINIO", entity_id=dati["cond"].id)
    assert [r["soggetto_id"] for r in righe] == [dati["rossi"].id]


def test_relazioni_senza_permesso_non_si_vedono(db_session, dati):
    righe = rq.elenca(db_session, TENANT, permessi={"soggetto.view"}, soggetto_ids=[dati["rossi"].id])
    assert righe == []
    righe = rq.elenca(db_session, TENANT, permessi={"soggetto.view", "immobile.view"},
                      soggetto_ids=[dati["rossi"].id])
    assert {r["tipo"] for r in righe} == {"proprietario"}
    assert all(r["descrizione"] for r in righe if r["entity_id"])


def test_ruoli_per_soggetti_senza_permesso(db_session, dati):
    ruoli = rq.ruoli_per_soggetti(db_session, TENANT, [dati["rossi"].id, dati["neri"].id],
                                  permessi={"soggetto.view", "condominio.view"})
    assert [r["codice"] for r in ruoli[dati["rossi"].id]] == ["amministratore_condominio"]
    assert dati["neri"].id not in ruoli


def test_soggetti_con_ruolo_senza_permesso(db_session, dati):
    q = rq.soggetti_con_ruolo(db_session, TENANT, "proprietario", permessi={"soggetto.view"})
    assert list(db_session.execute(q)) == []


def test_provider_tabelle_assenti(db_session, dati, monkeypatch):
    assert immobili_relations.proprietari(db_session, "schema_inesistente") is None
    monkeypatch.setattr(immobili_relations, "proprietari", lambda db, schema: None)
    righe = rq.elenca(db_session, TENANT, permessi={"*"}, soggetto_ids=[dati["rossi"].id])
    assert {r["tipo"] for r in righe} == {"amministratore_condominio"}


def test_ruoli_per_soggetti(db_session, dati):
    ruoli = rq.ruoli_per_soggetti(db_session, TENANT, [dati["rossi"].id, dati["neri"].id], permessi={"*"})
    rossi = {r["codice"]: r["n"] for r in ruoli[dati["rossi"].id]}
    assert rossi == {"proprietario": 1, "amministratore_condominio": 1}
    assert ruoli[dati["neri"].id] == [{"codice": "conduttore", "nome": "Conduttore", "modulo": "immobili", "n": 0}]


def test_soggetti_con_ruolo(db_session, dati):
    ids = {r[0] for r in db_session.execute(rq.soggetti_con_ruolo(db_session, TENANT, "proprietario", permessi={"*"}))}
    assert {dati["rossi"].id, dati["verdi"].id} <= ids
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


def test_data_impossibile_non_rompe_la_query(db_session, dati):
    db_session.add(DirittoImmobile(bene_id=dati["u2"].id, proprietario_id=dati["p_rossi"].id,
                                   tipo_diritto=TipoDiritto.USUFRUTTUARIO, data_inizio="2024-02-30",
                                   data_fine="2024-13-01"))
    db_session.flush()
    righe = rq.elenca(db_session, TENANT, permessi={"*"}, soggetto_ids=[dati["rossi"].id], tipo="proprietario")
    usufrutto = [r for r in righe if "Usufrutto" in (r["descrizione"] or "")]
    assert len(usufrutto) == 1
    assert usufrutto[0]["data_inizio"] is None and usufrutto[0]["data_fine"] is None
