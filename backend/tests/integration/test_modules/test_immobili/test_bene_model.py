"""
Bene (immo_beni) with UnitaImmobiliare as joined subclass sharing its id
(phase 1 of docs/superpowers/specs/2026-11-10-beni-catastali-design.md).
"""
from types import SimpleNamespace

from sqlalchemy import text

from immobili.models import Bene, UnitaImmobiliare
from immobili.routes.immobili import create_unita_immobiliare
from immobili.schemas import UnitaImmobiliareCreate


def _unita(db, codice="BENE-T-1", citta="Forlì"):
    u = UnitaImmobiliare(codice=codice, tipo="Appartamento", indirizzo="Via A 1", citta=citta)
    db.add(u)
    db.flush()
    return u


def test_unita_crea_bene_con_lo_stesso_id(db_session):
    u = _unita(db_session)
    riga = db_session.execute(
        text("SELECT tipo_bene, comune, codice FROM immo_beni WHERE id = :id"), {"id": u.id}
    ).one()
    assert riga.tipo_bene == "UNITA"
    assert riga.comune == "Forlì"
    assert riga.codice == "BENE-T-1"
    assert db_session.get(Bene, u.id) is u


def test_filtro_per_citta(db_session):
    _unita(db_session, codice="BENE-T-2", citta="Cittàprova")
    assert db_session.query(UnitaImmobiliare).filter(UnitaImmobiliare.citta == "Cittàprova").count() == 1


def test_api_unita_risponde_con_citta(db_session):
    utente = SimpleNamespace(id=1)
    risposta = create_unita_immobiliare(
        UnitaImmobiliareCreate(codice="BENE-T-3", tipo="Box", indirizzo="Via B 2", citta="Forlì"),
        db=db_session, current_user=utente,
    )
    assert risposta.citta == "Forlì"
    assert risposta.indirizzo == "Via B 2"
    assert db_session.execute(
        text("SELECT tipo_bene FROM immo_beni WHERE id = :id"), {"id": risposta.id}
    ).scalar() == "UNITA"


def test_cancellare_unita_cancella_bene_e_figli(db_session):
    from anagrafica_italiana.models import SoggettoAnagrafico, TipoSoggetto
    from immobili.models import (
        AssegnazioneConduttore, Conduttore, DirittoImmobile, Proprietario,
        SpesaRicorrenteImmobile, ResponsabileSpesa,
    )
    from datetime import date

    u = _unita(db_session, codice="BENE-T-4")
    s = SoggettoAnagrafico(tipo_soggetto=TipoSoggetto.PERSONA_FISICA, nome="Bene", cognome="Figli")
    db_session.add(s)
    db_session.flush()
    p = Proprietario(soggetto_id=s.id)
    c = Conduttore(soggetto_id=s.id)
    db_session.add_all([p, c])
    db_session.flush()
    db_session.add_all([
        DirittoImmobile(bene_id=u.id, proprietario_id=p.id, tipo_diritto="PROPRIETARIO"),
        AssegnazioneConduttore(bene_id=u.id, conduttore_id=c.id),
        SpesaRicorrenteImmobile(
            bene_id=u.id, tipo_spesa="IMU", responsabile=ResponsabileSpesa.PROPRIETARIO,
            periodo="2026", importo=10, data_scadenza=date(2026, 6, 16),
        ),
    ])
    db_session.flush()
    bene_id = u.id

    db_session.delete(u)
    db_session.flush()
    db_session.expire_all()

    for tabella in ("immo_beni", "immo_unita_immobiliari"):
        assert db_session.execute(text(f"SELECT count(*) FROM {tabella} WHERE id = :id"), {"id": bene_id}).scalar() == 0
    for tabella in ("immo_diritti_immobile", "immo_assegnazioni_conduttore", "immo_spese_ricorrenti"):
        assert db_session.execute(text(f"SELECT count(*) FROM {tabella} WHERE bene_id = :id"), {"id": bene_id}).scalar() == 0


def test_etichetta_immobile_dal_bene(db_session):
    from app.core.platform_services.entity_label_registry import entity_label_registry
    import immobili  # noqa: F401  (registers the IMMOBILE resolver)

    u = _unita(db_session, codice="BENE-T-5", citta="Forlì")
    assert entity_label_registry.labels(db_session, "IMMOBILE", [u.id]) == {u.id: "BENE-T-5 · Via A 1, Forlì"}
