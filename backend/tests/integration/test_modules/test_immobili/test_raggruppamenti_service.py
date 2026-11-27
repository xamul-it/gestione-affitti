"""
Tree of raggruppamenti (services/raggruppamenti.py): create, move with the
cycle check, archive, delete with the children moving up.
Plan: docs/superpowers/plans/2026-11-25-beni-fase4a-raggruppamenti.md, Task 2.
"""
from datetime import date, timedelta

import pytest
from sqlalchemy import text

from anagrafica_italiana.models import SoggettoAnagrafico
from anagrafica_italiana.models.soggetto_anagrafico import TipoSoggetto
from immobili.models import Raggruppamento, UnitaImmobiliare
from immobili.services.raggruppamenti import (
    TIPI_RAGGRUPPAMENTO, RamoNonCancellabile, antenati, aggiorna_raggruppamento, cancella_raggruppamento,
    crea_raggruppamento, discendenti_ids, sposta_bene, sposta_raggruppamento,
)

pytestmark = pytest.mark.integration

CICLO = "Un raggruppamento non può stare dentro se stesso o un suo sottoraggruppamento"


@pytest.fixture
def albero(db_session, unique_suffix):
    """Complesso C › Edificio E › Altro A, plus a unit U."""
    c = crea_raggruppamento(db_session, "COMPLESSO", f"C-{unique_suffix}")
    e = crea_raggruppamento(db_session, "EDIFICIO", f"E-{unique_suffix}", padre_id=c.id)
    a = crea_raggruppamento(db_session, "ALTRO", f"A-{unique_suffix}", padre_id=e.id)
    u = UnitaImmobiliare(codice=f"RG-U-{unique_suffix}", tipo="Appartamento", indirizzo="Via A 1", citta="Forlì")
    db_session.add(u)
    db_session.flush()
    return db_session, c, e, a, u


def test_tipi():
    assert TIPI_RAGGRUPPAMENTO == {"COMPLESSO": "Complesso", "EDIFICIO": "Edificio", "FONDO": "Fondo", "ALTRO": "Altro"}


def test_crea_con_padre(albero):
    db, c, e, _, _ = albero
    assert e.padre_id == c.id and e.attivo is True


def test_tipo_non_valido(db_session):
    with pytest.raises(ValueError):
        crea_raggruppamento(db_session, "CONDOMINIO", "x")


def test_nome_vuoto(db_session):
    with pytest.raises(ValueError):
        crea_raggruppamento(db_session, "EDIFICIO", "  ")


def test_padre_inesistente(db_session):
    with pytest.raises(LookupError):
        crea_raggruppamento(db_session, "EDIFICIO", "x", padre_id=-1)


def test_antenati_dalla_radice(albero):
    db, c, e, a, _ = albero
    assert [r.id for r in antenati(db, a.id)] == [c.id, e.id, a.id]
    assert discendenti_ids(db, c.id) == {c.id, e.id, a.id}


def test_sposta_sotto_se_stesso(albero):
    db, c, _, _, _ = albero
    with pytest.raises(ValueError, match=CICLO):
        sposta_raggruppamento(db, c, c.id)
    assert c.padre_id is None


def test_sposta_sotto_discendente(albero):
    db, c, e, a, _ = albero
    with pytest.raises(ValueError, match=CICLO):
        sposta_raggruppamento(db, c, a.id)
    db.refresh(c)
    assert c.padre_id is None and e.padre_id == c.id


def test_sposta_alla_radice(albero):
    db, _, e, a, _ = albero
    sposta_raggruppamento(db, a, None)
    assert a.padre_id is None
    sposta_raggruppamento(db, a, e.id)
    assert a.padre_id == e.id


def test_sposta_bene(albero):
    db, _, e, _, u = albero
    sposta_bene(db, u, e.id)
    assert u.raggruppamento_id == e.id
    sposta_bene(db, u, None)
    assert u.raggruppamento_id is None


def test_dentro_ramo_archiviato(albero):
    db, c, e, a, u = albero
    aggiorna_raggruppamento(db, e, attivo=False)
    with pytest.raises(ValueError, match="Il raggruppamento è archiviato"):
        crea_raggruppamento(db, "ALTRO", "x", padre_id=e.id)
    with pytest.raises(ValueError, match="Il raggruppamento è archiviato"):
        sposta_bene(db, u, e.id)
    altro = crea_raggruppamento(db, "ALTRO", "y")
    with pytest.raises(ValueError, match="Il raggruppamento è archiviato"):
        sposta_raggruppamento(db, altro, e.id)


def test_archivia_e_riattiva(albero):
    db, c, e, a, u = albero
    sposta_bene(db, u, e.id)
    aggiorna_raggruppamento(db, e, attivo=False)
    assert e.attivo is False and a.padre_id == e.id and u.raggruppamento_id == e.id
    aggiorna_raggruppamento(db, e, attivo=True)
    assert e.attivo is True


def test_aggiorna_tipo_non_valido(albero):
    db, _, e, _, _ = albero
    with pytest.raises(ValueError):
        aggiorna_raggruppamento(db, e, tipo="X")


def test_cancella_figli_salgono(albero):
    db, c, e, a, u = albero
    sposta_bene(db, u, e.id)
    assert cancella_raggruppamento(db, e) == {"rami_saliti": 1, "beni_saliti": 1}
    db.refresh(a)
    db.refresh(u)
    assert a.padre_id == c.id and u.raggruppamento_id == c.id
    assert db.get(Raggruppamento, e.id) is None
    cancella_raggruppamento(db, c)
    db.refresh(a)
    db.refresh(u)
    assert a.padre_id is None and u.raggruppamento_id is None


def _soggetto(db, s):
    sog = SoggettoAnagrafico(tipo_soggetto=TipoSoggetto.PERSONA_FISICA, nome="N", cognome=f"C-{s}")
    db.add(sog)
    db.flush()
    return sog


def test_cancella_con_relazione_chiusa(albero, unique_suffix):
    db, _, e, _, _ = albero
    ruolo = db.execute(text("SELECT id FROM public.core_ruoli_disponibili WHERE codice = 'manutentore'")).scalar()
    db.execute(text(
        "INSERT INTO core_relazioni (soggetto_id, ruolo_id, entity_type, entity_id, data_fine) "
        "VALUES (:s, :r, 'RAGGRUPPAMENTO', :e, :f)"),
        {"s": _soggetto(db, unique_suffix).id, "r": ruolo, "e": e.id, "f": date.today() - timedelta(days=1)})
    with pytest.raises(RamoNonCancellabile):
        cancella_raggruppamento(db, e)
    assert db.get(Raggruppamento, e.id) is not None


def test_cancella_con_documento(albero):
    db, _, e, _, _ = albero
    db.execute(text(
        "INSERT INTO core_documenti (entity_type, entity_id, tipo_documento) "
        "VALUES ('RAGGRUPPAMENTO', :e, 'DOCUMENTO_GENERICO')"), {"e": e.id})
    with pytest.raises(RamoNonCancellabile):
        cancella_raggruppamento(db, e)
