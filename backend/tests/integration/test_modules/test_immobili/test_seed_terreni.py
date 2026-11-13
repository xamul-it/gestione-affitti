"""Demo land parcels of the tenant seed follow the bene + portions layout."""
from sqlalchemy import text

from immobili.seeds.seed_tenant import seed_terreni_demo


def test_seed_terreni_crea_beni_con_porzioni(db_session):
    db_session.execute(text("DELETE FROM immo_beni WHERE tipo_bene = 'TERRENO'"))
    assert seed_terreni_demo(db_session, tipologia_id=None) == 2
    righe = db_session.execute(text(
        "SELECT b.codice, t.superficie_mq, count(p.id) AS porzioni FROM immo_beni b "
        "JOIN immo_terreni t ON t.id = b.id JOIN immo_terreni_porzioni p ON p.terreno_id = t.id "
        "GROUP BY b.codice, t.superficie_mq ORDER BY b.codice")).all()
    assert [(r.codice, r.superficie_mq, r.porzioni) for r in righe] == [("TER-001", 1500, 1), ("TER-002", 800, 1)]
    assert seed_terreni_demo(db_session, tipologia_id=None) == 0
