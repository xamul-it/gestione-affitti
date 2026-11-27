"""
Rules and warnings of links between beni (services/collegamenti_beni.py),
phase 2b of docs/superpowers/specs/2026-11-10-beni-catastali-design.md.
"""
from datetime import date
from types import SimpleNamespace

import pytest
from sqlalchemy import text

from anagrafica_italiana.models import SoggettoAnagrafico, TipoSoggetto
from immobili.models import (
    CategoriaCatastale, CollegamentoBeni,
    Terreno, TerrenoPorzione, UnitaImmobiliare,
)
from immobili.services.collegamenti_beni import (
    CollegamentoNonValido, TIPI_COLLEGAMENTO, aggiorna_collegamento,
    avvisi_collegamenti, crea_collegamento,
)
from immobili.services.elimina_bene import elimina_bene
from immobili.services.relazioni_bene import crea_relazione_bene
from tests.integration.conftest import TEST_TENANT

pytestmark = pytest.mark.integration

OGGI = date(2026, 11, 25)


def _unita(db, codice, categoria=None):
    cat_id = None
    if categoria:
        cat_id = db.query(CategoriaCatastale.id).filter(CategoriaCatastale.codice == categoria).scalar()
        assert cat_id, categoria
    u = UnitaImmobiliare(codice=codice, tipo="Appartamento", indirizzo="Via A 1", citta="Forlì",
                         categoria_catastale_id=cat_id)
    db.add(u)
    db.flush()
    return u


def _terreno(db, codice):
    t = Terreno(codice=codice, comune="Forlì", provincia="FC",
                porzioni=[TerrenoPorzione(qualita="SEMINATIVO", superficie_mq=100)])
    db.add(t)
    db.flush()
    return t


def _proprietario(db, cognome):
    s = SoggettoAnagrafico(tipo_soggetto=TipoSoggetto.PERSONA_FISICA, nome="Test", cognome=cognome)
    db.add(s)
    db.flush()
    return s


def _diritto(db, bene, soggetto, tipo="proprieta"):
    crea_relazione_bene(db, TEST_TENANT, None, bene.id, soggetto.id, tipo, quota="1/1")
    db.flush()


@pytest.fixture
def beni(db_session):
    db = db_session
    return SimpleNamespace(
        app_a=_unita(db, "APP-A", "A/3"),
        app_b=_unita(db, "APP-B", "A/3"),
        box=_unita(db, "BOX-1", "C/6"),
        box2=_unita(db, "BOX-2", "C/6"),
        cantina=_unita(db, "CANT-1", "C/2"),
        ufficio=_unita(db, "UFF-1", "A/10"),
        senza=_unita(db, "SENZA-CAT"),
        terreno=_terreno(db, "TER-1"),
        terreno2=_terreno(db, "TER-2"),
        fabbricato=_unita(db, "FABB-1", "A/3"),
    )


def test_tipi_ed_etichette():
    assert TIPI_COLLEGAMENTO["PERTINENZA"]["etichetta_principale"] == "Pertinenze"
    assert TIPI_COLLEGAMENTO["PERTINENZA"]["etichetta_collegato"] == "Pertinenza di"
    assert TIPI_COLLEGAMENTO["FABBRICATO_SU_PARTICELLA"]["etichetta_collegato"] == "Costruito sulla particella"
    # A farm is a FONDO raggruppamento since phase 4a.
    assert set(TIPI_COLLEGAMENTO) == {"PERTINENZA", "FABBRICATO_SU_PARTICELLA"}


def test_pertinenza_valida(db_session, beni):
    c = crea_collegamento(db_session, beni.app_a.id, beni.box.id, "PERTINENZA", None, None)
    assert c.id and c.aperto is True


@pytest.mark.parametrize("principale,collegato,messaggio", [
    ("ufficio", "box", "Una pertinenza si collega a un'abitazione (categoria A, tranne A/10)"),
    ("box", "app_a", "Una pertinenza si collega a un'abitazione (categoria A, tranne A/10)"),
    ("app_a", "terreno", "Pertinenza: serve un'unità di categoria C/2, C/6 o C/7"),
    ("app_a", "senza", "Pertinenza: serve un'unità di categoria C/2, C/6 o C/7"),
    ("senza", "box", "Una pertinenza si collega a un'abitazione (categoria A, tranne A/10)"),
])
def test_pertinenza_regole(db_session, beni, principale, collegato, messaggio):
    with pytest.raises(CollegamentoNonValido) as e:
        crea_collegamento(db_session, getattr(beni, principale).id, getattr(beni, collegato).id,
                          "PERTINENZA", None, None)
    assert str(e.value) == messaggio


def test_se_stesso_tipo_sconosciuto_e_doppione(db_session, beni):
    with pytest.raises(CollegamentoNonValido, match="Un bene non si collega a sé stesso"):
        crea_collegamento(db_session, beni.app_a.id, beni.app_a.id, "PERTINENZA", None, None)
    with pytest.raises(CollegamentoNonValido, match="Tipo di collegamento sconosciuto: BOH"):
        crea_collegamento(db_session, beni.app_a.id, beni.box.id, "BOH", None, None)
    crea_collegamento(db_session, beni.terreno.id, beni.fabbricato.id, "FABBRICATO_SU_PARTICELLA", None, None)
    with pytest.raises(CollegamentoNonValido, match="Collegamento già presente"):
        crea_collegamento(db_session, beni.terreno.id, beni.fabbricato.id, "FABBRICATO_SU_PARTICELLA", None, None)


def test_pertinenza_gia_di_altra_abitazione(db_session, beni):
    crea_collegamento(db_session, beni.app_a.id, beni.box.id, "PERTINENZA", None, None)
    with pytest.raises(CollegamentoNonValido) as e:
        crea_collegamento(db_session, beni.app_b.id, beni.box.id, "PERTINENZA", None, None)
    assert str(e.value) == "'BOX-1' è già pertinenza di 'APP-A'"


def test_riapertura_dopo_chiusura(db_session, beni):
    c = crea_collegamento(db_session, beni.app_a.id, beni.box.id, "PERTINENZA", date(2020, 1, 1), None)
    aggiorna_collegamento(db_session, c, date(2020, 1, 1), date(2025, 12, 31), "venduto")
    assert c.aperto is False
    nuovo = crea_collegamento(db_session, beni.app_a.id, beni.box.id, "PERTINENZA", None, None)
    righe = db_session.query(CollegamentoBeni).filter(CollegamentoBeni.bene_collegato_id == beni.box.id).all()
    assert len(righe) == 2 and [r.aperto for r in righe].count(True) == 1
    # Reopening the old one while the new one is open: same checks as creating.
    with pytest.raises(CollegamentoNonValido, match="Collegamento già presente"):
        aggiorna_collegamento(db_session, c, date(2020, 1, 1), None, None)
    assert nuovo.aperto


def test_riapertura_pertinenza_ora_di_altra_abitazione(db_session, beni):
    c = crea_collegamento(db_session, beni.app_a.id, beni.box.id, "PERTINENZA", None, None)
    aggiorna_collegamento(db_session, c, None, date(2025, 12, 31), None)
    crea_collegamento(db_session, beni.app_b.id, beni.box.id, "PERTINENZA", None, None)
    with pytest.raises(CollegamentoNonValido, match="'BOX-1' è già pertinenza di 'APP-B'"):
        aggiorna_collegamento(db_session, c, None, None, None)


def test_data_fine_prima_di_inizio(db_session, beni):
    c = crea_collegamento(db_session, beni.app_a.id, beni.box.id, "PERTINENZA", date(2025, 1, 1), None)
    with pytest.raises(CollegamentoNonValido, match="La data di fine precede quella di inizio"):
        aggiorna_collegamento(db_session, c, date(2025, 1, 1), date(2024, 1, 1), None)


def test_fabbricato_e_fondo_regole(db_session, beni):
    crea_collegamento(db_session, beni.terreno.id, beni.fabbricato.id, "FABBRICATO_SU_PARTICELLA", None, None)
    with pytest.raises(CollegamentoNonValido) as e:
        crea_collegamento(db_session, beni.fabbricato.id, beni.terreno.id, "FABBRICATO_SU_PARTICELLA", None, None)
    assert str(e.value) == "Fabbricato su particella: il principale è un terreno, il collegato un'unità"
    with pytest.raises(CollegamentoNonValido) as e:
        crea_collegamento(db_session, beni.terreno.id, beni.terreno2.id, "PARTE_DI_FONDO", None, None)
    assert str(e.value) == "Tipo di collegamento sconosciuto: PARTE_DI_FONDO"


AVVISO_C6 = ("Più pertinenze di categoria C/6: per l'IMU dell'abitazione principale "
             "ne conta una per categoria (L. 160/2019, c. 741)")


def test_avviso_due_pertinenze_stessa_categoria(db_session, beni):
    crea_collegamento(db_session, beni.app_a.id, beni.box.id, "PERTINENZA", None, None)
    crea_collegamento(db_session, beni.app_a.id, beni.cantina.id, "PERTINENZA", None, None)
    assert avvisi_collegamenti(db_session, beni.app_a.id, OGGI) == []
    crea_collegamento(db_session, beni.app_a.id, beni.box2.id, "PERTINENZA", None, None)
    assert AVVISO_C6 in avvisi_collegamenti(db_session, beni.app_a.id, OGGI)
    assert AVVISO_C6 in avvisi_collegamenti(db_session, beni.box.id, OGGI)
    assert AVVISO_C6 not in avvisi_collegamenti(db_session, beni.cantina.id, OGGI)


def test_avviso_titolari_diversi(db_session, beni):
    p1, p2 = _proprietario(db_session, "Uno"), _proprietario(db_session, "Due")
    _diritto(db_session, beni.app_a, p1)
    _diritto(db_session, beni.box, p2)
    _diritto(db_session, beni.cantina, p1)
    crea_collegamento(db_session, beni.app_a.id, beni.box.id, "PERTINENZA", None, None)
    crea_collegamento(db_session, beni.app_a.id, beni.cantina.id, "PERTINENZA", None, None)
    avviso = "Titolari di 'BOX-1' diversi da quelli dell'abitazione"
    assert avvisi_collegamenti(db_session, beni.app_a.id, OGGI) == [avviso]
    assert avvisi_collegamenti(db_session, beni.box.id, OGGI) == [avviso]
    assert avvisi_collegamenti(db_session, beni.cantina.id, OGGI) == []


def test_cancellare_bene_toglie_collegamenti(db_session, beni):
    crea_collegamento(db_session, beni.app_a.id, beni.box.id, "PERTINENZA", None, None)
    crea_collegamento(db_session, beni.terreno.id, beni.box.id, "FABBRICATO_SU_PARTICELLA", None, None)
    box_id = beni.box.id
    elimina_bene(db_session, beni.box, None)
    assert db_session.execute(text(
        "SELECT count(*) FROM immo_beni_collegamenti WHERE bene_id = :b OR bene_collegato_id = :b"
    ), {"b": box_id}).scalar() == 0
    assert db_session.get(UnitaImmobiliare, beni.app_a.id) is not None
    assert db_session.get(Terreno, beni.terreno.id) is not None
