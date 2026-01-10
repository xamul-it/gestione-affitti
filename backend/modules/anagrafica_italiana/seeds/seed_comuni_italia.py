"""
Seed Comuni Italia - Italian municipalities minimal dataset.

Seeds the comuni_italia table with top 50 Italian cities for CAP lookup.
For production, replace with complete ISTAT dataset (~8,000 municipalities).
"""
from sqlalchemy.orm import Session
from ..models import ComuneItalia
import logging
import unicodedata

logger = logging.getLogger(__name__)


def normalize_for_db(text: str) -> str:
    """Normalize text for database (lowercase, no accents)."""
    text = text.lower().strip()
    # Remove accents
    text = ''.join(
        c for c in unicodedata.normalize('NFD', text)
        if unicodedata.category(c) != 'Mn'
    )
    return text


# Top 50+ Italian cities with CAP and province data
# Format: (nome, codice_istat, cap, provincia_sigla, provincia_nome, regione)
COMUNI_SEED_DATA = [
    # Lombardia
    ("Milano", "015146", "20100", "MI", "Milano", "Lombardia"),
    ("Bergamo", "016024", "24100", "BG", "Bergamo", "Lombardia"),
    ("Brescia", "017029", "25100", "BS", "Brescia", "Lombardia"),
    ("Como", "013075", "22100", "CO", "Como", "Lombardia"),
    ("Cremona", "019036", "26100", "CR", "Cremona", "Lombardia"),
    ("Lecco", "097042", "23900", "LC", "Lecco", "Lombardia"),
    ("Lodi", "098030", "26900", "LO", "Lodi", "Lombardia"),
    ("Mantova", "020030", "46100", "MN", "Mantova", "Lombardia"),
    ("Monza", "108033", "20900", "MB", "Monza e della Brianza", "Lombardia"),
    ("Pavia", "018110", "27100", "PV", "Pavia", "Lombardia"),
    ("Sondrio", "014061", "23100", "SO", "Sondrio", "Lombardia"),
    ("Varese", "012133", "21100", "VA", "Varese", "Lombardia"),

    # Emilia-Romagna
    ("Bologna", "037006", "40100", "BO", "Bologna", "Emilia-Romagna"),
    ("Ferrara", "038008", "44100", "FE", "Ferrara", "Emilia-Romagna"),
    ("Forlì", "040012", "47121", "FC", "Forlì-Cesena", "Emilia-Romagna"),
    ("Cesena", "040007", "47521", "FC", "Forlì-Cesena", "Emilia-Romagna"),
    ("Modena", "036023", "41121", "MO", "Modena", "Emilia-Romagna"),
    ("Parma", "034027", "43121", "PR", "Parma", "Emilia-Romagna"),
    ("Piacenza", "033032", "29121", "PC", "Piacenza", "Emilia-Romagna"),
    ("Ravenna", "039014", "48121", "RA", "Ravenna", "Emilia-Romagna"),
    ("Reggio Emilia", "035033", "42121", "RE", "Reggio Emilia", "Emilia-Romagna"),
    ("Rimini", "099014", "47921", "RN", "Rimini", "Emilia-Romagna"),

    # Piemonte
    ("Torino", "001272", "10100", "TO", "Torino", "Piemonte"),
    ("Alessandria", "006003", "15100", "AL", "Alessandria", "Piemonte"),
    ("Asti", "005005", "14100", "AT", "Asti", "Piemonte"),
    ("Biella", "096004", "13900", "BI", "Biella", "Piemonte"),
    ("Cuneo", "004078", "12100", "CN", "Cuneo", "Piemonte"),
    ("Novara", "003106", "28100", "NO", "Novara", "Piemonte"),
    ("Verbania", "103072", "28900", "VB", "Verbano-Cusio-Ossola", "Piemonte"),
    ("Vercelli", "002158", "13100", "VC", "Vercelli", "Piemonte"),

    # Veneto
    ("Venezia", "027042", "30100", "VE", "Venezia", "Veneto"),
    ("Verona", "023091", "37100", "VR", "Verona", "Veneto"),
    ("Padova", "028060", "35100", "PD", "Padova", "Veneto"),
    ("Vicenza", "024116", "36100", "VI", "Vicenza", "Veneto"),
    ("Treviso", "026086", "31100", "TV", "Treviso", "Veneto"),
    ("Rovigo", "029050", "45100", "RO", "Rovigo", "Veneto"),
    ("Belluno", "025003", "32100", "BL", "Belluno", "Veneto"),

    # Lazio
    ("Roma", "058091", "00100", "RM", "Roma", "Lazio"),
    ("Frosinone", "060036", "03100", "FR", "Frosinone", "Lazio"),
    ("Latina", "059011", "04100", "LT", "Latina", "Lazio"),
    ("Rieti", "057059", "02100", "RI", "Rieti", "Lazio"),
    ("Viterbo", "056059", "01100", "VT", "Viterbo", "Lazio"),

    # Campania
    ("Napoli", "063049", "80100", "NA", "Napoli", "Campania"),
    ("Salerno", "065116", "84100", "SA", "Salerno", "Campania"),
    ("Avellino", "064008", "83100", "AV", "Avellino", "Campania"),
    ("Benevento", "062008", "82100", "BN", "Benevento", "Campania"),
    ("Caserta", "061022", "81100", "CE", "Caserta", "Campania"),

    # Toscana
    ("Firenze", "048017", "50100", "FI", "Firenze", "Toscana"),
    ("Pisa", "050026", "56100", "PI", "Pisa", "Toscana"),
    ("Livorno", "049009", "57100", "LI", "Livorno", "Toscana"),
    ("Arezzo", "051002", "52100", "AR", "Arezzo", "Toscana"),
    ("Siena", "052032", "53100", "SI", "Siena", "Toscana"),
    ("Grosseto", "053011", "58100", "GR", "Grosseto", "Toscana"),
    ("Lucca", "046017", "55100", "LU", "Lucca", "Toscana"),
    ("Pistoia", "047014", "51100", "PT", "Pistoia", "Toscana"),
    ("Prato", "100005", "59100", "PO", "Prato", "Toscana"),
    ("Massa", "045010", "54100", "MS", "Massa-Carrara", "Toscana"),

    # Puglia
    ("Bari", "072006", "70100", "BA", "Bari", "Puglia"),
    ("Lecce", "075035", "73100", "LE", "Lecce", "Puglia"),
    ("Taranto", "073027", "74100", "TA", "Taranto", "Puglia"),
    ("Foggia", "071024", "71100", "FG", "Foggia", "Puglia"),
    ("Brindisi", "074001", "72100", "BR", "Brindisi", "Puglia"),
    ("Barletta", "110001", "76121", "BT", "Barletta-Andria-Trani", "Puglia"),

    # Sicilia
    ("Palermo", "082053", "90100", "PA", "Palermo", "Sicilia"),
    ("Catania", "087015", "95100", "CT", "Catania", "Sicilia"),
    ("Messina", "083048", "98100", "ME", "Messina", "Sicilia"),
    ("Siracusa", "089017", "96100", "SR", "Siracusa", "Sicilia"),
    ("Ragusa", "088009", "97100", "RG", "Ragusa", "Sicilia"),
    ("Trapani", "081021", "91100", "TP", "Trapani", "Sicilia"),
    ("Agrigento", "084001", "92100", "AG", "Agrigento", "Sicilia"),
    ("Caltanissetta", "085003", "93100", "CL", "Caltanissetta", "Sicilia"),
    ("Enna", "086006", "94100", "EN", "Enna", "Sicilia"),

    # Liguria
    ("Genova", "010025", "16100", "GE", "Genova", "Liguria"),
    ("La Spezia", "011015", "19100", "SP", "La Spezia", "Liguria"),
    ("Savona", "009055", "17100", "SV", "Savona", "Liguria"),
    ("Imperia", "008031", "18100", "IM", "Imperia", "Liguria"),

    # Other major cities
    ("Trieste", "032006", "34100", "TS", "Trieste", "Friuli-Venezia Giulia"),
    ("Udine", "030129", "33100", "UD", "Udine", "Friuli-Venezia Giulia"),
    ("Ancona", "042002", "60100", "AN", "Ancona", "Marche"),
    ("Perugia", "054039", "06100", "PG", "Perugia", "Umbria"),
    ("Cagliari", "092009", "09100", "CA", "Cagliari", "Sardegna"),
    ("Bolzano", "021008", "39100", "BZ", "Bolzano/Bozen", "Trentino-Alto Adige"),
    ("Trento", "022205", "38100", "TN", "Trento", "Trentino-Alto Adige"),
    ("Aosta", "007003", "11100", "AO", "Aosta", "Valle d'Aosta"),
]


def seed_comuni_italia_minimal(db: Session) -> int:
    """
    Seed comuni italia table with minimal dataset (top cities).

    This provides basic CAP lookup functionality for the most common Italian cities.
    For production use, replace with complete ISTAT dataset.

    Args:
        db: Database session

    Returns:
        Number of comuni seeded
    """
    # Check if already seeded
    existing_count = db.query(ComuneItalia).count()
    if existing_count > 0:
        logger.info(f"Comuni Italia already seeded ({existing_count} records)")
        return 0

    logger.info("Seeding comuni Italia (minimal dataset)...")
    seeded_count = 0

    for nome, codice_istat, cap, provincia_sigla, provincia_nome, regione in COMUNI_SEED_DATA:
        try:
            comune = ComuneItalia(
                nome=nome,
                nome_normalized=normalize_for_db(nome),
                codice_istat=codice_istat,
                cap=cap,
                provincia_sigla=provincia_sigla,
                provincia_nome=provincia_nome,
                regione=regione
            )
            db.add(comune)
            seeded_count += 1
        except Exception as e:
            logger.error(f"Error seeding comune {nome}: {e}")

    db.commit()
    logger.info(f"Successfully seeded {seeded_count} comuni Italia")
    return seeded_count
