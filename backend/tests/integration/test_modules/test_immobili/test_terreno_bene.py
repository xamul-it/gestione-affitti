"""
Terreno as joined subclass of Bene, with portions (phase 2a of
docs/superpowers/specs/2026-11-10-beni-catastali-design.md).
"""
from decimal import Decimal

from sqlalchemy import text

from immobili.models import Bene, Terreno, TerrenoPorzione


def _terreno(db, codice="TER-B-1"):
    t = Terreno(
        codice=codice, comune="Forlì", provincia="FC",
        porzioni=[
            TerrenoPorzione(porzione="AA", qualita="BOSCO CEDUO", classe="2", superficie_mq=363,
                            reddito_dominicale=Decimal("0.25"), reddito_agrario=Decimal("0.09")),
            TerrenoPorzione(porzione="AB", qualita="PASCOLO", classe="2", superficie_mq=63,
                            reddito_dominicale=Decimal("0.06"), reddito_agrario=Decimal("0.03")),
        ],
    )
    t.ricalcola_superficie()
    db.add(t)
    db.flush()
    return t


def test_terreno_crea_bene_terreno(db_session):
    t = _terreno(db_session)
    riga = db_session.execute(
        text("SELECT tipo_bene, comune FROM immo_beni WHERE id = :id"), {"id": t.id}
    ).one()
    assert riga.tipo_bene == "TERRENO"
    assert riga.comune == "Forlì"
    assert t.superficie_mq == 426
    assert t.reddito_dominicale_totale == Decimal("0.31")
    assert t.reddito_agrario_totale == Decimal("0.12")
    assert [p.porzione for p in t.porzioni] == ["AA", "AB"]
    db_session.expire_all()
    assert isinstance(db_session.get(Bene, t.id), Terreno)


def test_redditi_totali_none_se_nessuna_porzione_li_ha(db_session):
    t = Terreno(codice="TER-B-2", comune="Forlì", provincia="FC",
                porzioni=[TerrenoPorzione(qualita="ENTE URBANO", superficie_mq=120)])
    assert t.reddito_dominicale_totale is None
    assert t.reddito_agrario_totale is None


def test_sezione_catastale_e_sinonimo_di_sezione(db_session):
    t = Terreno(codice="TER-B-3", comune="Forlì", provincia="FC", sezione_catastale="A",
                porzioni=[TerrenoPorzione(qualita="SEMINATIVO", superficie_mq=10)])
    assert t.sezione == "A"


def test_cancellare_terreno_cancella_bene_porzioni_e_figli(db_session):
    from anagrafica_italiana.models import SoggettoAnagrafico, TipoSoggetto
    from immobili.models import AssegnazioneConduttore, Conduttore, DirittoImmobile, Proprietario

    t = _terreno(db_session, codice="TER-B-4")
    s = SoggettoAnagrafico(tipo_soggetto=TipoSoggetto.PERSONA_FISICA, nome="Terreno", cognome="Figli")
    db_session.add(s)
    db_session.flush()
    p = Proprietario(soggetto_id=s.id)
    c = Conduttore(soggetto_id=s.id)
    db_session.add_all([p, c])
    db_session.flush()
    db_session.add_all([
        DirittoImmobile(bene_id=t.id, proprietario_id=p.id, tipo_diritto="USUFRUTTUARIO"),
        AssegnazioneConduttore(bene_id=t.id, conduttore_id=c.id),
    ])
    db_session.flush()
    bene_id = t.id

    db_session.delete(t)
    db_session.flush()
    db_session.expire_all()

    for tabella in ("immo_beni", "immo_terreni"):
        assert db_session.execute(text(f"SELECT count(*) FROM {tabella} WHERE id = :id"), {"id": bene_id}).scalar() == 0
    assert db_session.execute(text(
        "SELECT count(*) FROM immo_terreni_porzioni WHERE terreno_id = :id"), {"id": bene_id}).scalar() == 0
    for tabella in ("immo_diritti_immobile", "immo_assegnazioni_conduttore"):
        assert db_session.execute(text(f"SELECT count(*) FROM {tabella} WHERE bene_id = :id"), {"id": bene_id}).scalar() == 0
