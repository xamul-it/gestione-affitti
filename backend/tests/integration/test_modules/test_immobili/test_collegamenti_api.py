"""
/beni/{id}/collegamenti and the pertinenza flag in the unit list, phase 2b
of docs/superpowers/specs/2026-11-10-beni-catastali-design.md.
"""
from datetime import date
from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from immobili.models import CategoriaCatastale, Terreno, TerrenoPorzione, UnitaImmobiliare
from immobili.routes.beni import (
    create_collegamento, delete_collegamento, get_collegamenti, update_collegamento,
)
from immobili.routes.immobili import get_unita_immobiliari
from immobili.schemas.collegamento_beni import CollegamentoCreate, CollegamentoUpdate

pytestmark = pytest.mark.integration

UTENTE = SimpleNamespace(id=1, is_superuser=True, get_permissions=lambda: set())


def _utente(*permessi):
    return SimpleNamespace(id=2, is_superuser=False, get_permissions=lambda: set(permessi))


def _unita(db, codice, categoria):
    cat_id = db.query(CategoriaCatastale.id).filter(CategoriaCatastale.codice == categoria).scalar()
    u = UnitaImmobiliare(codice=codice, tipo="Appartamento", indirizzo="Via A 1", citta="Forlì",
                         categoria_catastale_id=cat_id)
    db.add(u)
    db.flush()
    return u


@pytest.fixture
def beni(db_session):
    db = db_session
    t = Terreno(codice="CAPI-T", comune="Forlì", provincia="FC",
                porzioni=[TerrenoPorzione(qualita="ENTE URBANO", superficie_mq=100)])
    db.add(t)
    db.flush()
    return SimpleNamespace(
        app_a=_unita(db, "APP-A", "A/3"), app_b=_unita(db, "APP-B", "A/3"),
        box=_unita(db, "BOX-1", "C/6"), altra=_unita(db, "ALTRA-1", "A/2"),
        fabbricato=_unita(db, "CAPI-F", "A/3"), terreno=t,
    )


def _crea(db, bene_id, altro_id, tipo="PERTINENZA", questo_e="PRINCIPALE", utente=UTENTE, **extra):
    return create_collegamento(
        bene_id, CollegamentoCreate(altro_bene_id=altro_id, tipo=tipo, questo_e=questo_e, **extra),
        db=db, current_user=utente,
    )


def _elenco(db, bene_id, storico=False, utente=UTENTE):
    return get_collegamenti(bene_id, storico=storico, db=db, current_user=utente)


def _errore(fn):
    with pytest.raises(HTTPException) as e:
        fn()
    return e.value


def test_crea_e_elenca_pertinenza(db_session, beni):
    c = _crea(db_session, beni.app_a.id, beni.box.id)
    assert c.questo_e == "PRINCIPALE" and c.aperto and c.altro_bene.codice == "BOX-1"
    dall_abitazione = _elenco(db_session, beni.app_a.id).collegamenti
    assert [(x.questo_e, x.etichetta) for x in dall_abitazione] == [("PRINCIPALE", "Pertinenze")]
    dal_box = _elenco(db_session, beni.box.id).collegamenti
    assert [(x.questo_e, x.etichetta, x.altro_bene.codice) for x in dal_box] == [
        ("COLLEGATO", "Pertinenza di", "APP-A")]


def test_crea_dal_lato_collegato(db_session, beni):
    c = _crea(db_session, beni.box.id, beni.app_a.id, questo_e="COLLEGATO")
    assert c.questo_e == "COLLEGATO" and c.etichetta == "Pertinenza di"
    assert _elenco(db_session, beni.app_a.id).collegamenti[0].altro_bene.codice == "BOX-1"


def test_pertinenza_doppia_400_non_500(db_session, beni):
    _crea(db_session, beni.app_a.id, beni.box.id)
    e = _errore(lambda: _crea(db_session, beni.app_b.id, beni.box.id))
    assert e.status_code == 400 and e.detail == "'BOX-1' è già pertinenza di 'APP-A'"


def test_tipo_sconosciuto_400(db_session, beni):
    e = _errore(lambda: _crea(db_session, beni.app_a.id, beni.box.id, tipo="BOH"))
    assert e.status_code == 400 and e.detail == "Tipo di collegamento sconosciuto: BOH"


def test_chiudi_e_riapri(db_session, beni):
    c = _crea(db_session, beni.app_a.id, beni.box.id)
    chiuso = update_collegamento(beni.app_a.id, c.id, CollegamentoUpdate(data_fine=date(2026, 1, 31)),
                                 db=db_session, current_user=UTENTE)
    assert chiuso.aperto is False and chiuso.data_fine == date(2026, 1, 31)
    assert _elenco(db_session, beni.app_a.id).collegamenti == []
    assert len(_elenco(db_session, beni.app_a.id, storico=True).collegamenti) == 1
    _crea(db_session, beni.app_a.id, beni.box.id)
    storico = _elenco(db_session, beni.app_a.id, storico=True).collegamenti
    assert [x.aperto for x in storico] == [True, False]


def test_put_tiene_i_campi_non_inviati(db_session, beni):
    c = _crea(db_session, beni.app_a.id, beni.box.id, data_inizio=date(2020, 1, 1), note="rogito")
    r = update_collegamento(beni.app_a.id, c.id, CollegamentoUpdate(note="nuova"),
                            db=db_session, current_user=UTENTE)
    assert r.data_inizio == date(2020, 1, 1) and r.note == "nuova"


def test_data_fine_prima_di_inizio(db_session, beni):
    with pytest.raises(ValidationError):
        CollegamentoUpdate(data_inizio=date(2026, 1, 1), data_fine=date(2025, 1, 1))
    c = _crea(db_session, beni.app_a.id, beni.box.id, data_inizio=date(2026, 1, 1))
    e = _errore(lambda: update_collegamento(beni.app_a.id, c.id, CollegamentoUpdate(data_fine=date(2025, 1, 1)),
                                            db=db_session, current_user=UTENTE))
    assert e.status_code == 400 and e.detail == "La data di fine precede quella di inizio"


def test_altro_bene_invisibile_nascosto(db_session, beni):
    _crea(db_session, beni.terreno.id, beni.fabbricato.id, tipo="FABBRICATO_SU_PARTICELLA")
    solo_unita = _utente("immobile.view", "immobile.edit")
    risposta = _elenco(db_session, beni.fabbricato.id, utente=solo_unita)
    assert risposta.collegamenti == []
    e = _errore(lambda: _crea(db_session, beni.altra.id, beni.terreno.id, tipo="FABBRICATO_SU_PARTICELLA",
                              questo_e="COLLEGATO", utente=solo_unita))
    assert e.status_code == 404 and e.detail == "Bene non trovato"


def test_scrittura_senza_edit_403(db_session, beni):
    e = _errore(lambda: _crea(db_session, beni.app_a.id, beni.box.id, utente=_utente("immobile.view")))
    assert e.status_code == 403
    e = _errore(lambda: _elenco(db_session, beni.app_a.id, utente=_utente()))
    assert e.status_code == 403


def test_collegamento_di_altro_bene_404(db_session, beni):
    c = _crea(db_session, beni.app_a.id, beni.box.id)
    e = _errore(lambda: update_collegamento(beni.altra.id, c.id, CollegamentoUpdate(note="x"),
                                            db=db_session, current_user=UTENTE))
    assert e.status_code == 404 and e.detail == "Collegamento non trovato"
    e = _errore(lambda: delete_collegamento(beni.altra.id, c.id, db=db_session, current_user=UTENTE))
    assert e.status_code == 404
    delete_collegamento(beni.box.id, c.id, db=db_session, current_user=UTENTE)
    assert _elenco(db_session, beni.app_a.id, storico=True).collegamenti == []


def test_lista_unita_ruolo_pertinenza(db_session, beni):
    _crea(db_session, beni.app_a.id, beni.box.id)
    lista = get_unita_immobiliari(skip=0, limit=10000, db=db_session, current_user=UTENTE)
    ruoli = {u.codice: u.ruolo_pertinenza for u in lista}
    assert ruoli["APP-A"] == "CON_PERTINENZE"
    assert ruoli["BOX-1"] == "PERTINENZA"
    assert ruoli["ALTRA-1"] is None
