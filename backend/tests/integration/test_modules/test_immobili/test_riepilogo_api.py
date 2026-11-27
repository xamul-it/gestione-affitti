"""GET /beni/{id}/riepilogo ("chi paga cosa"), phase 2b of the beni spec."""
from datetime import date
from decimal import Decimal
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from anagrafica_italiana.models import SoggettoAnagrafico, TipoSoggetto
from immobili.models import Terreno, TerrenoPorzione, UnitaImmobiliare
from immobili.routes.beni import get_riepilogo
from immobili.services.relazioni_bene import crea_relazione_bene
from tests.integration.conftest import TEST_TENANT

pytestmark = pytest.mark.integration

UTENTE = SimpleNamespace(id=1, is_superuser=True, get_permissions=lambda: set())


def _utente(*permessi):
    return SimpleNamespace(id=2, is_superuser=False, get_permissions=lambda: set(permessi))


def _soggetto(db, cognome):
    s = SoggettoAnagrafico(tipo_soggetto=TipoSoggetto.PERSONA_FISICA, nome="Riep", cognome=cognome)
    db.add(s)
    db.flush()
    return s


@pytest.fixture
def terreno_forli(db_session):
    db = db_session
    t = Terreno(codice="RIEP-T", comune="Forlì", provincia="FC",
                porzioni=[TerrenoPorzione(qualita="SEMINATIVO", superficie_mq=1000)])
    db.add(t)
    db.flush()
    for cognome, tipo in (("Nudo", "nuda_proprieta"), ("Usufrutto", "usufrutto")):
        crea_relazione_bene(db, TEST_TENANT, None, t.id, _soggetto(db, cognome).id, tipo, quota="1/1")
    # An agricultural tenant: the agrarian income follows whoever farms the land.
    crea_relazione_bene(db, TEST_TENANT, None, t.id, _soggetto(db, "Conduttore").id, "affittuario_agrario",
                        data_inizio=date(2020, 1, 1))
    db.flush()
    return t


def _chi(risposta, codice):
    voce = next(v for v in risposta.voci if v.codice == codice)
    return [s.nome for s in voce.soggetti]


def test_riepilogo_api_data_default_oggi(db_session, terreno_forli):
    r = get_riepilogo(terreno_forli.id, data=None, db=db_session, current_user=UTENTE)
    assert r.data == date.today()
    assert _chi(r, "RENDITA") == ["Riep Usufrutto"]
    assert _chi(r, "REDDITO_AGRARIO") == ["Riep Conduttore"]
    assert _chi(r, "SPESE_STRAORDINARIE") == ["Riep Nudo"]
    assert r.voci[0].soggetti[0].quota == Decimal(100)
    prima = get_riepilogo(terreno_forli.id, data=date(2019, 6, 1), db=db_session, current_user=UTENTE)
    assert _chi(prima, "SPESE_ORDINARIE") == ["Riep Usufrutto"]


def test_riepilogo_richiede_vista_del_bene_e_soggetto_view(db_session, terreno_forli):
    """Names of the anagrafiche: like the relations of the bene, the bene view alone is not enough."""
    with pytest.raises(HTTPException) as e:
        get_riepilogo(terreno_forli.id, data=None, db=db_session, current_user=_utente("terreno.view"))
    assert e.value.status_code == 403
    r = get_riepilogo(terreno_forli.id, data=None, db=db_session,
                      current_user=_utente("terreno.view", "soggetto.view"))
    assert r.voci


def test_riepilogo_terreno_con_solo_immobile_view_404(db_session, terreno_forli):
    with pytest.raises(HTTPException) as e:
        get_riepilogo(terreno_forli.id, data=None, db=db_session, current_user=_utente("immobile.view", "soggetto.view"))
    assert e.value.status_code == 404


def test_riepilogo_unita_senza_diritti(db_session):
    u = UnitaImmobiliare(codice="RIEP-U", tipo="Appartamento", indirizzo="Via A 1", citta="Forlì")
    db_session.add(u)
    db_session.flush()
    r = get_riepilogo(u.id, data=None, db=db_session, current_user=UTENTE)
    assert r.voci[0].etichetta == "Rendita catastale"
    assert r.avvisi == ["Nessun titolare registrato alla data"]


def test_riepilogo_terreno_locato_avviso_e_quote_esatte(db_session):
    t = Terreno(codice="RIEP-T2", comune="Forlì", provincia="FC",
                porzioni=[TerrenoPorzione(qualita="SEMINATIVO", superficie_mq=500)])
    db_session.add(t)
    db_session.flush()
    for i in range(3):
        crea_relazione_bene(db_session, TEST_TENANT, None, t.id, _soggetto(db_session, f"Terzo{i}").id,
                            "proprieta", quota="1/3")
    crea_relazione_bene(db_session, TEST_TENANT, None, t.id, _soggetto(db_session, "Locatario").id, "conduttore")
    r = get_riepilogo(t.id, data=None, db=db_session, current_user=UTENTE)
    assert _chi(r, "REDDITO_AGRARIO") == ["Riep Terzo0", "Riep Terzo1", "Riep Terzo2"]
    assert _chi(r, "SPESE_ORDINARIE") == ["Riep Locatario"]
    assert any(a.startswith("Terreno locato:") for a in r.avvisi)
    assert r.voci[0].soggetti[0].quota == Decimal("33.33")


# --- relations inherited from the raggruppamenti (phase 4a) ----------------------------

from immobili.services.raggruppamenti import aggiorna_raggruppamento, crea_raggruppamento, sposta_bene  # noqa: E402
from immobili.services.relazioni_bene import crea_relazione_raggruppamento  # noqa: E402


@pytest.fixture
def unita_in_edificio(db_session):
    db = db_session
    edificio = crea_raggruppamento(db, "EDIFICIO", "Edificio riepilogo")
    u = UnitaImmobiliare(codice="RIEP-UE", tipo="Appartamento", indirizzo="Via B 1", citta="Forlì")
    db.add(u)
    db.flush()
    sposta_bene(db, u, edificio.id)
    crea_relazione_bene(db, TEST_TENANT, None, u.id, _soggetto(db, "Proprietario").id, "proprieta", quota="1/1")
    crea_relazione_raggruppamento(db, TEST_TENANT, None, edificio.id, _soggetto(db, "Inquilino").id, "conduttore")
    crea_relazione_raggruppamento(db, TEST_TENANT, None, edificio.id, _soggetto(db, "Caldaista").id, "manutentore")
    db.flush()
    return u, edificio


def test_conduttore_del_ramo_paga_ordinarie(db_session, unita_in_edificio):
    u, _ = unita_in_edificio
    r = get_riepilogo(u.id, data=None, db=db_session, current_user=UTENTE)
    assert _chi(r, "SPESE_ORDINARIE") == ["Riep Inquilino"]
    assert _chi(r, "IMU") == ["Riep Proprietario"]


def test_ramo_archiviato_eredita(db_session, unita_in_edificio):
    u, edificio = unita_in_edificio
    aggiorna_raggruppamento(db_session, edificio, attivo=False)
    r = get_riepilogo(u.id, data=None, db=db_session, current_user=UTENTE)
    assert _chi(r, "SPESE_ORDINARIE") == ["Riep Inquilino"]


def test_incarico_del_ramo_ignorato(db_session, unita_in_edificio):
    u, _ = unita_in_edificio
    r = get_riepilogo(u.id, data=None, db=db_session, current_user=UTENTE)
    assert all("Riep Caldaista" not in [s.nome for s in v.soggetti] for v in r.voci)


def test_affittuario_agrario_del_fondo(db_session):
    db = db_session
    fondo = crea_raggruppamento(db, "FONDO", "Fondo riepilogo")
    t = Terreno(codice="RIEP-TF", comune="Forlì", provincia="FC",
                porzioni=[TerrenoPorzione(qualita="SEMINATIVO", superficie_mq=1000)])
    db.add(t)
    db.flush()
    sposta_bene(db, t, fondo.id)
    crea_relazione_bene(db, TEST_TENANT, None, t.id, _soggetto(db, "Titolare").id, "proprieta", quota="1/1")
    crea_relazione_raggruppamento(db, TEST_TENANT, None, fondo.id, _soggetto(db, "Agricoltore").id,
                                  "affittuario_agrario")
    db.flush()
    r = get_riepilogo(t.id, data=None, db=db, current_user=UTENTE)
    assert _chi(r, "REDDITO_AGRARIO") == ["Riep Agricoltore"]
    assert _chi(r, "RENDITA") == ["Riep Titolare"]
