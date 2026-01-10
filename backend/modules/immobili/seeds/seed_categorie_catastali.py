"""
Seed Categorie Catastali - Italian cadastral categories.

Seeds the categorie_catastali table with official Italian property classifications.
"""
from sqlalchemy.orm import Session
from ..models import CategoriaCatastale
import logging

logger = logging.getLogger(__name__)


# Official Italian cadastral categories
CATEGORIE_SEED_DATA = [
    # Gruppo A - Abitazioni (Residential)
    ("A/1", "Abitazioni di tipo signorile", "A",
     "Abitazioni signorili con caratteristiche costruttive, tecnologiche e di rifiniture di livello superiore", 1),
    ("A/2", "Abitazioni di tipo civile", "A",
     "Abitazioni di tipo civile con caratteristiche costruttive, tecnologiche e di rifiniture di livello ordinario", 2),
    ("A/3", "Abitazioni di tipo economico", "A",
     "Abitazioni di tipo economico con caratteristiche costruttive e rifiniture di modesto livello", 3),
    ("A/4", "Abitazioni di tipo popolare", "A",
     "Abitazioni di tipo popolare con caratteristiche costruttive e rifiniture di livello particolarmente modesto", 4),
    ("A/5", "Abitazioni di tipo ultra-popolare", "A",
     "Abitazioni di tipo ultra-popolare con caratteristiche costruttive e rifiniture di livello molto modesto", 5),
    ("A/6", "Abitazioni di tipo rurale", "A",
     "Abitazioni di tipo rurale", 6),
    ("A/7", "Abitazioni in villini", "A",
     "Abitazioni in villini - case mono o bifamiliari con giardino e/o corte", 7),
    ("A/8", "Abitazioni in ville", "A",
     "Abitazioni in ville - abitazioni signorili con parco e/o giardino", 8),
    ("A/9", "Castelli, palazzi di eminenti pregi artistici o storici", "A",
     "Castelli e palazzi di pregio artistico o storico", 9),
    ("A/10", "Uffici e studi privati", "A",
     "Uffici e studi privati", 10),
    ("A/11", "Abitazioni ed alloggi tipici dei luoghi", "A",
     "Abitazioni ed alloggi tipici dei luoghi (trulli, sassi, baite, rifugi, etc.)", 11),

    # Gruppo B - Collettività (Community buildings)
    ("B/1", "Collegi e convitti, educandati, ricoveri, orfanotrofi, ospizi, conventi, seminari, caserme", "B",
     "Collegi, convitti, ospizi, conventi, seminari, caserme", 12),
    ("B/2", "Case di cura ed ospedali", "B",
     "Case di cura ed ospedali (senza fine di lucro)", 13),
    ("B/3", "Prigioni e riformatori", "B",
     "Prigioni e riformatori", 14),
    ("B/4", "Uffici pubblici", "B",
     "Uffici pubblici", 15),
    ("B/5", "Scuole e laboratori scientifici", "B",
     "Scuole, laboratori scientifici pubblici", 16),
    ("B/6", "Biblioteche, pinacoteche, musei, gallerie, accademie", "B",
     "Biblioteche, musei, gallerie, accademie", 17),
    ("B/7", "Cappelle ed oratori non destinati all'esercizio pubblico del culto", "B",
     "Cappelle ed oratori non aperti al pubblico", 18),
    ("B/8", "Magazzini sotterranei per depositi di derrate", "B",
     "Magazzini sotterranei per depositi di derrate", 19),

    # Gruppo C - Commerciale/Pertinenze (Commercial/Accessory)
    ("C/1", "Negozi e botteghe", "C",
     "Negozi e botteghe", 20),
    ("C/2", "Magazzini e locali di deposito", "C",
     "Magazzini e locali di deposito", 21),
    ("C/3", "Laboratori per arti e mestieri", "C",
     "Laboratori per arti e mestieri", 22),
    ("C/4", "Fabbricati e locali per esercizi sportivi", "C",
     "Fabbricati e locali per esercizi sportivi (senza fine di lucro)", 23),
    ("C/5", "Stabilimenti balneari e di acque curative", "C",
     "Stabilimenti balneari e di acque curative (senza fine di lucro)", 24),
    ("C/6", "Stalle, scuderie, rimesse, autorimesse", "C",
     "Stalle, scuderie, rimesse, autorimesse (senza fine di lucro)", 25),
    ("C/7", "Tettoie chiuse o aperte", "C",
     "Tettoie chiuse o aperte", 26),

    # Gruppo D - Immobili a destinazione speciale (Special purpose)
    ("D/1", "Opifici", "D",
     "Opifici - stabilimenti industriali", 27),
    ("D/2", "Alberghi e pensioni", "D",
     "Alberghi e pensioni (con fine di lucro)", 28),
    ("D/3", "Teatri, cinematografi, sale per concerti e spettacoli", "D",
     "Teatri, cinematografi, sale per concerti e spettacoli", 29),
    ("D/4", "Case di cura ed ospedali", "D",
     "Case di cura ed ospedali (con fine di lucro)", 30),
    ("D/5", "Istituti di credito, cambio e assicurazione", "D",
     "Istituti di credito, cambio e assicurazione (banche, assicurazioni)", 31),
    ("D/6", "Fabbricati e locali per esercizi sportivi", "D",
     "Fabbricati e locali per esercizi sportivi (con fine di lucro)", 32),
    ("D/7", "Fabbricati costruiti per le speciali esigenze di attività industriale", "D",
     "Fabbricati per attività industriali", 33),
    ("D/8", "Fabbricati costruiti per speciali esigenze di attività commerciale", "D",
     "Fabbricati per attività commerciali (centri commerciali, outlet)", 34),
    ("D/9", "Edifici galleggianti o sospesi", "D",
     "Edifici galleggianti o sospesi", 35),
    ("D/10", "Fabbricati per funzioni produttive connesse alle attività agricole", "D",
     "Fabbricati agricoli produttivi", 36),

    # Gruppo E - Immobili a destinazione particolare (Special categories)
    ("E/1", "Stazioni per servizi di trasporto, terrestri, marittimi ed aerei", "E",
     "Stazioni per servizi di trasporto", 37),
    ("E/2", "Ponti comunali e provinciali soggetti a pedaggio", "E",
     "Ponti soggetti a pedaggio", 38),
    ("E/3", "Costruzioni e fabbricati per speciali esigenze pubbliche", "E",
     "Costruzioni per speciali esigenze pubbliche", 39),
    ("E/4", "Recinti chiusi per speciali esigenze pubbliche", "E",
     "Recinti chiusi per speciali esigenze pubbliche", 40),
    ("E/5", "Fabbricati costituenti fortificazioni e loro dipendenze", "E",
     "Fortificazioni e dipendenze", 41),
    ("E/6", "Fari, semafori, torri per rendere l'uso pubblico l'orologio comunale", "E",
     "Fari, semafori, torri pubbliche", 42),
    ("E/7", "Fabbricati destinati all'esercizio pubblico dei culti", "E",
     "Chiese e luoghi di culto pubblici", 43),
    ("E/8", "Fabbricati e costruzioni nei cimiteri", "E",
     "Fabbricati e costruzioni cimiteriali", 44),
    ("E/9", "Edifici a destinazione particolare non compresi nelle categorie precedenti", "E",
     "Edifici a destinazione particolare (non classificati altrove)", 45),
]


def seed_categorie_catastali(db: Session) -> int:
    """
    Seed categorie catastali table.

    Args:
        db: Database session

    Returns:
        Number of categories seeded
    """
    # Check if already seeded
    existing_count = db.query(CategoriaCatastale).count()
    if existing_count > 0:
        logger.info(f"Categorie catastali already seeded ({existing_count} records)")
        return 0

    logger.info("Seeding categorie catastali...")
    seeded_count = 0

    for codice, nome, gruppo, descrizione, ordinamento in CATEGORIE_SEED_DATA:
        try:
            categoria = CategoriaCatastale(
                codice=codice,
                nome=nome,
                gruppo=gruppo,
                descrizione=descrizione,
                ordinamento=ordinamento,
                attiva=True
            )
            db.add(categoria)
            seeded_count += 1
        except Exception as e:
            logger.error(f"Error seeding categoria {codice}: {e}")

    db.commit()
    logger.info(f"Successfully seeded {seeded_count} categorie catastali")
    return seeded_count
