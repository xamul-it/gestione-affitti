"""
Land API with portions (phase 2a of
docs/superpowers/specs/2026-11-10-beni-catastali-design.md).
Routes are called directly, as in test_bene_model.py.
"""
from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from pydantic import ValidationError
from sqlalchemy import text

from immobili.routes.immobili import create_unita_immobiliare, update_unita_immobiliare
from immobili.routes.terreni import create_terreno, delete_terreno, get_terreno, update_terreno
from immobili.schemas import UnitaImmobiliareCreate, UnitaImmobiliareUpdate
from immobili.schemas.terreno import TerrenoCreate, TerrenoPorzioneIn, TerrenoUpdate

pytestmark = pytest.mark.integration

UTENTE = SimpleNamespace(id=1)


def _porzioni():
    return [
        TerrenoPorzioneIn(porzione="AA", qualita="BOSCO CEDUO", classe="2", superficie_mq=363,
                          reddito_dominicale="0.25", reddito_agrario="0.09"),
        TerrenoPorzioneIn(porzione="AB", qualita="PASCOLO", classe="2", superficie_mq=63,
                          reddito_dominicale="0.06", reddito_agrario="0.03", deduzioni="D12"),
    ]


def _crea(db, codice="TAPI-1", **campi):
    dati = {"codice": codice, "comune": "Forlì", "provincia": "FC", "porzioni": _porzioni(), **campi}
    return create_terreno(TerrenoCreate(**dati), db=db, current_user=UTENTE)


def test_crea_terreno_con_porzioni(db_session):
    t = _crea(db_session, foglio="40", particella="154", sezione_catastale="A", edificabile=True)
    assert t.tipo_bene == "TERRENO"
    assert t.superficie_mq == 426
    assert len(t.porzioni) == 2
    assert t.porzioni[1].deduzioni == "D12"
    assert str(t.reddito_dominicale_totale) == "0.31"
    assert t.sezione_catastale == "A"
    assert t.edificabile is True and t.esente_imu_montano is False
    assert db_session.execute(text("SELECT sezione FROM immo_beni WHERE id = :id"), {"id": t.id}).scalar() == "A"


def test_crea_terreno_senza_porzioni_422():
    with pytest.raises(ValidationError):
        TerrenoCreate(codice="TAPI-0", comune="Forlì", provincia="FC", porzioni=[])
    with pytest.raises(ValidationError):
        TerrenoCreate(codice="TAPI-0", comune="Forlì", provincia="FC")


def test_porzione_superficie_negativa_422():
    with pytest.raises(ValidationError):
        TerrenoPorzioneIn(qualita="SEMINATIVO", superficie_mq=-1)


def test_update_sostituisce_porzioni(db_session):
    t = _crea(db_session, codice="TAPI-2")
    r = update_terreno(t.id, TerrenoUpdate(porzioni=[TerrenoPorzioneIn(qualita="SEMINATIVO", superficie_mq=1000)]),
                       db=db_session, current_user=UTENTE)
    assert r.superficie_mq == 1000
    assert [p.qualita for p in r.porzioni] == ["SEMINATIVO"]
    assert db_session.execute(text(
        "SELECT count(*) FROM immo_terreni_porzioni WHERE terreno_id = :id"), {"id": t.id}).scalar() == 1


def test_update_senza_porzioni_le_lascia(db_session):
    t = _crea(db_session, codice="TAPI-3")
    r = update_terreno(t.id, TerrenoUpdate(nome="Campo", attivo=False), db=db_session, current_user=UTENTE)
    assert r.nome == "Campo" and r.attivo is False
    assert len(r.porzioni) == 2 and r.superficie_mq == 426


def test_update_porzioni_vuote_422():
    with pytest.raises(ValidationError):
        TerrenoUpdate(porzioni=[])


def test_codice_gia_usato_da_unita_400(db_session):
    create_unita_immobiliare(UnitaImmobiliareCreate(codice="X-1", tipo="Box", indirizzo="Via B 2", citta="Forlì"),
                             db=db_session, current_user=UTENTE)
    with pytest.raises(HTTPException) as e:
        _crea(db_session, codice="X-1")
    assert e.value.status_code == 400
    assert "già usato da un altro bene" in e.value.detail

    _crea(db_session, codice="X-2")
    with pytest.raises(HTTPException) as e:
        create_unita_immobiliare(UnitaImmobiliareCreate(codice="X-2", tipo="Box", indirizzo="Via B 2", citta="Forlì"),
                                 db=db_session, current_user=UTENTE)
    assert e.value.status_code == 400
    assert "già usato da un altro bene" in e.value.detail


def test_codice_duplicato_in_update_400(db_session):
    u = create_unita_immobiliare(UnitaImmobiliareCreate(codice="X-3", tipo="Box", indirizzo="Via B 2", citta="Forlì"),
                                 db=db_session, current_user=UTENTE)
    t = _crea(db_session, codice="X-4")
    with pytest.raises(HTTPException) as e:
        update_terreno(t.id, TerrenoUpdate(codice="X-3"), db=db_session, current_user=UTENTE)
    assert e.value.status_code == 400 and "già usato da un altro bene" in e.value.detail
    with pytest.raises(HTTPException) as e:
        update_unita_immobiliare(u.id, UnitaImmobiliareUpdate(codice="X-4"), db=db_session, current_user=UTENTE)
    assert e.value.status_code == 400 and "già usato da un altro bene" in e.value.detail
    # Saving a parcel with its own code is fine.
    assert update_terreno(t.id, TerrenoUpdate(codice="X-4"), db=db_session, current_user=UTENTE).codice == "X-4"


def test_delete_terreno_cancella(db_session):
    t = _crea(db_session, codice="TAPI-5")
    assert delete_terreno(t.id, db=db_session, current_user=UTENTE) is None
    with pytest.raises(HTTPException) as e:
        get_terreno(t.id, db=db_session, current_user=UTENTE)
    assert e.value.status_code == 404
    assert db_session.execute(text("SELECT count(*) FROM immo_beni WHERE id = :id"), {"id": t.id}).scalar() == 0


def test_etichetta_terreno_senza_indirizzo(db_session):
    from app.core.platform_services.entity_label_registry import entity_label_registry
    import immobili  # noqa: F401  (registers the IMMOBILE resolver)

    t = _crea(db_session, codice="T-9")
    assert entity_label_registry.labels(db_session, "IMMOBILE", [t.id]) == {t.id: "T-9 · Forlì"}


def test_descrizione_relazione_terreno_senza_indirizzo(db_session):
    from anagrafica_italiana.models import SoggettoAnagrafico, TipoSoggetto
    from immobili.models import DirittoImmobile, Proprietario
    from immobili.relations import proprietari

    t = _crea(db_session, codice="T-10")
    s = SoggettoAnagrafico(tipo_soggetto=TipoSoggetto.PERSONA_FISICA, nome="Rel", cognome="Terreno")
    db_session.add(s)
    db_session.flush()
    p = Proprietario(soggetto_id=s.id)
    db_session.add(p)
    db_session.flush()
    db_session.add(DirittoImmobile(bene_id=t.id, proprietario_id=p.id, tipo_diritto="USUFRUTTUARIO"))
    db_session.flush()
    sel = proprietari(db_session, "tenant_qa_test").subquery()
    descrizione = db_session.execute(
        __import__("sqlalchemy").select(sel.c.descrizione).where(sel.c.entity_id == t.id)).scalar()
    assert descrizione.startswith("T-10 · Forlì — ")


def test_tipologie_documentali_del_terreno():
    from immobili.__manifest__ import manifest

    tipi = {t["codice"]: t for t in manifest["document_types"]}
    assert tipi["ESTRATTO_MAPPA"]["regime"] == "SOSTITUTIVO"
    assert tipi["CDU"]["scadenza"] == {"mesi": 12, "da": "data_riferimento"}
    assert tipi["CDU"]["promemoria_giorni"] == [30]
    assert tipi["CONTRATTO_AFFITTO_AGRARIO"]["regime"] == "CUMULATIVO"
    assert "TIPO_MAPPALE" in tipi["VARIAZIONE_CATASTALE"]["sottotipi"]


def test_modifica_dati_catastali_terreno_registra_variazioni(db_session):
    from immobili.routes.beni import get_variazioni_catastali

    t = _crea(db_session, codice="TAPI-VAR", foglio="40", particella="154")
    update_terreno(t.id, TerrenoUpdate(
        particella="155", nome="Campo",
        porzioni=[TerrenoPorzioneIn(qualita="SEMINATIVO", superficie_mq=1000)],
    ), db=db_session, current_user=UTENTE)
    superuser = SimpleNamespace(id=1, is_superuser=True, get_permissions=lambda: set())
    righe = get_variazioni_catastali(t.id, db=db_session, current_user=superuser)
    assert {(r.campo, r.valore_precedente, r.valore_nuovo, r.origine) for r in righe} == {
        ("particella", "154", "155", "MANUALE"),
        ("superficie_mq", "426.0", "1000.0", "MANUALE"),
    }
