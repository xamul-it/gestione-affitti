"""
Seed script per popolare il database con 100 soggetti anagrafici italiani.
Genera persone fisiche e giuridiche con Codice Fiscale e Partita IVA validi.

Eseguire con:
    cd backend
    source venv/bin/activate
    python modules/anagrafica_italiana/seeds/seed_soggetti_anagrafici.py
"""
import sys
import os
import random
import string
from datetime import date, timedelta
from typing import List, Dict, Tuple

# Add backend directory to path for imports
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)
modules_dir = os.path.join(backend_dir, 'modules')
if modules_dir not in sys.path:
    sys.path.insert(0, modules_dir)

from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from anagrafica_italiana.models.soggetto_anagrafico import SoggettoAnagrafico, TipoSoggetto


# =============================================================================
# DATI ITALIANI REALISTICI
# =============================================================================

NOMI_MASCHILI = [
    "Marco", "Alessandro", "Giuseppe", "Francesco", "Andrea", "Luca",
    "Giovanni", "Paolo", "Stefano", "Antonio", "Roberto", "Matteo",
    "Davide", "Michele", "Lorenzo", "Fabio", "Simone", "Massimo",
    "Riccardo", "Daniele", "Claudio", "Alberto", "Pietro", "Emanuele",
    "Nicola", "Federico", "Vincenzo", "Salvatore", "Carlo", "Sergio"
]

NOMI_FEMMINILI = [
    "Maria", "Anna", "Giulia", "Francesca", "Sara", "Elena",
    "Chiara", "Laura", "Valentina", "Martina", "Alessandra", "Federica",
    "Silvia", "Paola", "Roberta", "Monica", "Simona", "Claudia",
    "Elisa", "Cristina", "Barbara", "Ilaria", "Michela", "Angela",
    "Daniela", "Giovanna", "Teresa", "Rosa", "Lucia", "Patrizia"
]

COGNOMI = [
    "Rossi", "Russo", "Ferrari", "Esposito", "Bianchi", "Romano",
    "Colombo", "Ricci", "Marino", "Greco", "Bruno", "Gallo",
    "Conti", "De Luca", "Mancini", "Costa", "Giordano", "Rizzo",
    "Lombardi", "Moretti", "Barbieri", "Fontana", "Santoro", "Mariani",
    "Rinaldi", "Caruso", "Ferrara", "Galli", "Martini", "Leone",
    "Longo", "Gentile", "Martinelli", "Vitale", "Lombardo", "Serra",
    "Coppola", "De Santis", "D'Angelo", "Marchetti", "Parisi", "Villa",
    "Conte", "Ferraro", "Ferri", "Fabbri", "Bianco", "Marini"
]

# Comuni italiani con codice catastale
COMUNI = [
    {"nome": "Roma", "codice": "H501", "provincia": "RM", "cap": "00100"},
    {"nome": "Milano", "codice": "F205", "provincia": "MI", "cap": "20100"},
    {"nome": "Napoli", "codice": "F839", "provincia": "NA", "cap": "80100"},
    {"nome": "Torino", "codice": "L219", "provincia": "TO", "cap": "10100"},
    {"nome": "Palermo", "codice": "G273", "provincia": "PA", "cap": "90100"},
    {"nome": "Genova", "codice": "D969", "provincia": "GE", "cap": "16100"},
    {"nome": "Bologna", "codice": "A944", "provincia": "BO", "cap": "40100"},
    {"nome": "Firenze", "codice": "D612", "provincia": "FI", "cap": "50100"},
    {"nome": "Bari", "codice": "A662", "provincia": "BA", "cap": "70100"},
    {"nome": "Catania", "codice": "C351", "provincia": "CT", "cap": "95100"},
    {"nome": "Venezia", "codice": "L736", "provincia": "VE", "cap": "30100"},
    {"nome": "Verona", "codice": "L781", "provincia": "VR", "cap": "37100"},
    {"nome": "Messina", "codice": "F158", "provincia": "ME", "cap": "98100"},
    {"nome": "Padova", "codice": "G224", "provincia": "PD", "cap": "35100"},
    {"nome": "Trieste", "codice": "L424", "provincia": "TS", "cap": "34100"},
    {"nome": "Brescia", "codice": "B157", "provincia": "BS", "cap": "25100"},
    {"nome": "Taranto", "codice": "L049", "provincia": "TA", "cap": "74100"},
    {"nome": "Prato", "codice": "G999", "provincia": "PO", "cap": "59100"},
    {"nome": "Reggio Calabria", "codice": "H224", "provincia": "RC", "cap": "89100"},
    {"nome": "Modena", "codice": "F257", "provincia": "MO", "cap": "41100"},
    {"nome": "Reggio Emilia", "codice": "H223", "provincia": "RE", "cap": "42100"},
    {"nome": "Perugia", "codice": "G478", "provincia": "PG", "cap": "06100"},
    {"nome": "Livorno", "codice": "E625", "provincia": "LI", "cap": "57100"},
    {"nome": "Ravenna", "codice": "H199", "provincia": "RA", "cap": "48100"},
    {"nome": "Cagliari", "codice": "B354", "provincia": "CA", "cap": "09100"},
    {"nome": "Foggia", "codice": "D643", "provincia": "FG", "cap": "71100"},
    {"nome": "Rimini", "codice": "H294", "provincia": "RN", "cap": "47900"},
    {"nome": "Salerno", "codice": "H703", "provincia": "SA", "cap": "84100"},
    {"nome": "Ferrara", "codice": "D548", "provincia": "FE", "cap": "44100"},
    {"nome": "Sassari", "codice": "I452", "provincia": "SS", "cap": "07100"},
]

VIE = [
    "Via Roma", "Via Garibaldi", "Via Mazzini", "Via Dante", "Via Verdi",
    "Corso Italia", "Corso Vittorio Emanuele", "Via XX Settembre", "Via Cavour",
    "Via Nazionale", "Via della Repubblica", "Viale Europa", "Via San Giovanni",
    "Via Marconi", "Via Gramsci", "Via Kennedy", "Via della Libertà",
    "Via dei Mille", "Piazza del Duomo", "Via Matteotti", "Via Colombo",
    "Via Leonardo da Vinci", "Via Michelangelo", "Via Raffaello", "Via Tiziano"
]

TIPI_SOCIETA = [
    "S.r.l.", "S.p.A.", "S.a.s.", "S.n.c.", "S.r.l.s."
]

SETTORI = [
    "Costruzioni", "Immobiliare", "Consulenza", "Servizi", "Commercio",
    "Edilizia", "Manutenzioni", "Energia", "Logistica", "Informatica",
    "Alimentare", "Trasporti", "Arredamento", "Tessile", "Meccanica"
]

PREFISSI_AZIENDA = [
    "Alfa", "Beta", "Delta", "Gamma", "Omega", "Nova", "Prima", "Euro",
    "Italia", "Nord", "Sud", "Centro", "Global", "Tech", "Green", "Smart"
]

SUFFISSI_AZIENDA = [
    "Group", "Service", "Solutions", "Holding", "System", "Project",
    "Invest", "Management", "Partner", "Team", "Works", "Lab"
]


# =============================================================================
# ALGORITMI CODICE FISCALE E PARTITA IVA
# =============================================================================

# Tabella conversione mesi per CF
MESI_CF = {
    1: 'A', 2: 'B', 3: 'C', 4: 'D', 5: 'E', 6: 'H',
    7: 'L', 8: 'M', 9: 'P', 10: 'R', 11: 'S', 12: 'T'
}

# Tabelle per carattere di controllo CF
DISPARI = {
    '0': 1, '1': 0, '2': 5, '3': 7, '4': 9, '5': 13, '6': 15, '7': 17, '8': 19, '9': 21,
    'A': 1, 'B': 0, 'C': 5, 'D': 7, 'E': 9, 'F': 13, 'G': 15, 'H': 17, 'I': 19, 'J': 21,
    'K': 2, 'L': 4, 'M': 18, 'N': 20, 'O': 11, 'P': 3, 'Q': 6, 'R': 8, 'S': 12, 'T': 14,
    'U': 16, 'V': 10, 'W': 22, 'X': 25, 'Y': 24, 'Z': 23
}

PARI = {
    '0': 0, '1': 1, '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9,
    'A': 0, 'B': 1, 'C': 2, 'D': 3, 'E': 4, 'F': 5, 'G': 6, 'H': 7, 'I': 8, 'J': 9,
    'K': 10, 'L': 11, 'M': 12, 'N': 13, 'O': 14, 'P': 15, 'Q': 16, 'R': 17, 'S': 18, 'T': 19,
    'U': 20, 'V': 21, 'W': 22, 'X': 23, 'Y': 24, 'Z': 25
}

CONTROLLO = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'


def estrai_consonanti(s: str) -> str:
    """Estrae le consonanti da una stringa"""
    return ''.join(c for c in s.upper() if c.isalpha() and c not in 'AEIOU')


def estrai_vocali(s: str) -> str:
    """Estrae le vocali da una stringa"""
    return ''.join(c for c in s.upper() if c.isalpha() and c in 'AEIOU')


def codice_cognome(cognome: str) -> str:
    """Calcola i 3 caratteri del cognome per il CF"""
    cognome = cognome.replace(" ", "").replace("'", "")
    cons = estrai_consonanti(cognome)
    voc = estrai_vocali(cognome)
    codice = (cons + voc + 'XXX')[:3]
    return codice.upper()


def codice_nome(nome: str) -> str:
    """Calcola i 3 caratteri del nome per il CF"""
    nome = nome.replace(" ", "").replace("'", "")
    cons = estrai_consonanti(nome)
    voc = estrai_vocali(nome)
    # Per il nome: se ci sono 4+ consonanti, prendi 1a, 3a e 4a
    if len(cons) >= 4:
        codice = cons[0] + cons[2] + cons[3]
    else:
        codice = (cons + voc + 'XXX')[:3]
    return codice.upper()


def codice_data_sesso(data_nascita: date, sesso: str) -> str:
    """Calcola i caratteri di data e sesso per il CF"""
    anno = str(data_nascita.year)[-2:]
    mese = MESI_CF[data_nascita.month]
    giorno = data_nascita.day
    if sesso == 'F':
        giorno += 40
    return f"{anno}{mese}{giorno:02d}"


def calcola_check_digit_cf(cf_parziale: str) -> str:
    """Calcola il carattere di controllo del CF"""
    totale = 0
    for i, char in enumerate(cf_parziale):
        if (i + 1) % 2 == 0:  # posizione pari (1-indexed)
            totale += PARI[char]
        else:  # posizione dispari
            totale += DISPARI[char]
    return CONTROLLO[totale % 26]


def genera_codice_fiscale(cognome: str, nome: str, data_nascita: date,
                          sesso: str, codice_comune: str) -> str:
    """Genera un Codice Fiscale italiano valido"""
    cf = (
        codice_cognome(cognome) +
        codice_nome(nome) +
        codice_data_sesso(data_nascita, sesso) +
        codice_comune.upper()
    )
    cf += calcola_check_digit_cf(cf)
    return cf


def calcola_check_digit_piva(piva_parziale: str) -> str:
    """Calcola il carattere di controllo della Partita IVA (algoritmo Luhn)"""
    totale = 0
    for i, digit in enumerate(piva_parziale):
        n = int(digit)
        if i % 2 == 0:  # posizione dispari (0-indexed)
            totale += n
        else:  # posizione pari
            doubled = n * 2
            totale += doubled if doubled < 10 else doubled - 9
    check = (10 - (totale % 10)) % 10
    return str(check)


def genera_partita_iva() -> str:
    """Genera una Partita IVA italiana valida (11 cifre)"""
    # Prime 7 cifre: numero progressivo
    numeri = ''.join(random.choices('0123456789', k=7))
    # 3 cifre: codice ufficio provinciale (001-100 per uffici provinciali)
    ufficio = f"{random.randint(1, 100):03d}"
    piva_parziale = numeri + ufficio
    check = calcola_check_digit_piva(piva_parziale)
    return piva_parziale + check


def genera_telefono() -> str:
    """Genera un numero di telefono fisso italiano"""
    prefissi = ['02', '06', '011', '051', '055', '081', '091', '041', '010', '080']
    return f"{random.choice(prefissi)} {random.randint(1000000, 9999999)}"


def genera_cellulare() -> str:
    """Genera un numero di cellulare italiano"""
    prefissi = ['320', '333', '347', '349', '366', '377', '388', '389', '392', '393']
    return f"{random.choice(prefissi)} {random.randint(1000000, 9999999)}"


def genera_email(nome: str, cognome: str, dominio: str = None) -> str:
    """Genera un indirizzo email"""
    if dominio is None:
        domini = ['gmail.com', 'libero.it', 'yahoo.it', 'outlook.it', 'hotmail.it', 'virgilio.it']
        dominio = random.choice(domini)
    nome_clean = nome.lower().replace(' ', '').replace("'", "")
    cognome_clean = cognome.lower().replace(' ', '').replace("'", "")
    formati = [
        f"{nome_clean}.{cognome_clean}@{dominio}",
        f"{nome_clean[0]}.{cognome_clean}@{dominio}",
        f"{cognome_clean}.{nome_clean}@{dominio}",
        f"{nome_clean}{cognome_clean}@{dominio}",
    ]
    return random.choice(formati)


def genera_pec(ragione_sociale: str = None, cognome: str = None) -> str:
    """Genera un indirizzo PEC"""
    domini_pec = ['pec.it', 'legalmail.it', 'postecert.it', 'arubapec.it']
    if ragione_sociale:
        base = ragione_sociale.lower().replace(' ', '').replace('.', '').replace("'", "")[:20]
    else:
        base = cognome.lower().replace(' ', '').replace("'", "")
    return f"{base}@{random.choice(domini_pec)}"


def genera_indirizzo(comune: dict) -> Tuple[str, str, str, str]:
    """Genera un indirizzo italiano completo"""
    via = random.choice(VIE)
    civico = random.randint(1, 200)
    indirizzo = f"{via}, {civico}"
    return indirizzo, comune['nome'], comune['cap'], comune['provincia']


def genera_ragione_sociale() -> str:
    """Genera una ragione sociale per persona giuridica"""
    tipo = random.choice(TIPI_SOCIETA)
    formati = [
        f"{random.choice(PREFISSI_AZIENDA)} {random.choice(SETTORI)} {tipo}",
        f"{random.choice(COGNOMI)} {random.choice(SETTORI)} {tipo}",
        f"{random.choice(PREFISSI_AZIENDA)} {random.choice(SUFFISSI_AZIENDA)} {tipo}",
        f"{random.choice(COGNOMI)} & {random.choice(COGNOMI)} {tipo}",
        f"Immobiliare {random.choice(COGNOMI)} {tipo}",
        f"{random.choice(SETTORI)} {random.choice(COGNOMI)} {tipo}",
    ]
    return random.choice(formati)


# =============================================================================
# GENERATORI DI SOGGETTI
# =============================================================================

def genera_persona_fisica(indice: int) -> Dict:
    """Genera i dati per una persona fisica"""
    sesso = random.choice(['M', 'F'])
    nome = random.choice(NOMI_MASCHILI if sesso == 'M' else NOMI_FEMMINILI)
    cognome = random.choice(COGNOMI)

    # Data di nascita tra 25 e 75 anni fa
    oggi = date.today()
    anni = random.randint(25, 75)
    giorni = random.randint(0, 365)
    data_nascita = date(oggi.year - anni, 1, 1) + timedelta(days=giorni)

    # Comune di nascita
    comune_nascita = random.choice(COMUNI)

    # Comune di residenza (può essere diverso)
    comune_residenza = random.choice(COMUNI)

    # Genera CF
    codice_fiscale = genera_codice_fiscale(
        cognome, nome, data_nascita, sesso, comune_nascita['codice']
    )

    # Indirizzo
    indirizzo, citta, cap, provincia = genera_indirizzo(comune_residenza)

    # 30% delle persone fisiche ha anche P.IVA (liberi professionisti)
    partita_iva = genera_partita_iva() if random.random() < 0.3 else None

    return {
        "tipo_soggetto": "PERSONA_FISICA",
        "codice_fiscale": codice_fiscale,
        "partita_iva": partita_iva,
        "nome": nome,
        "cognome": cognome,
        "data_nascita": data_nascita.isoformat(),
        "luogo_nascita": comune_nascita['nome'],
        "ragione_sociale": None,
        "email": genera_email(nome, cognome),
        "telefono": genera_telefono() if random.random() > 0.3 else None,
        "cellulare": genera_cellulare(),
        "pec": genera_pec(cognome=cognome) if partita_iva else None,
        "indirizzo": indirizzo,
        "citta": citta,
        "cap": cap,
        "provincia": provincia,
        "note": None,
        "attivo": True
    }


def genera_persona_giuridica(indice: int) -> Dict:
    """Genera i dati per una persona giuridica"""
    ragione_sociale = genera_ragione_sociale()
    comune = random.choice(COMUNI)
    indirizzo, citta, cap, provincia = genera_indirizzo(comune)

    # Dominio aziendale per email
    nome_azienda = ragione_sociale.split()[0].lower()
    dominio = f"{nome_azienda}.it"

    return {
        "tipo_soggetto": "PERSONA_GIURIDICA",
        "codice_fiscale": None,  # Le aziende usano P.IVA
        "partita_iva": genera_partita_iva(),
        "nome": None,
        "cognome": None,
        "data_nascita": None,
        "luogo_nascita": None,
        "ragione_sociale": ragione_sociale,
        "email": f"info@{dominio}",
        "telefono": genera_telefono(),
        "cellulare": None,
        "pec": genera_pec(ragione_sociale=ragione_sociale),
        "indirizzo": indirizzo,
        "citta": citta,
        "cap": cap,
        "provincia": provincia,
        "note": None,
        "attivo": True
    }


# =============================================================================
# FUNZIONE PRINCIPALE DI SEED
# =============================================================================

def seed_soggetti_anagrafici(
    n_persone_fisiche: int = 70,
    n_persone_giuridiche: int = 30,
    db: Session = None
) -> List[Dict]:
    """
    Popola il database con soggetti anagrafici.

    Args:
        n_persone_fisiche: Numero di persone fisiche da creare (default 70)
        n_persone_giuridiche: Numero di persone giuridiche da creare (default 30)
        db: Sessione database (opzionale, ne crea una nuova se non fornita)

    Returns:
        Lista dei soggetti creati con i loro dati
    """
    close_db = False
    if db is None:
        db = SessionLocal()
        close_db = True

    soggetti_creati = []
    errori = []

    try:
        print(f"\n{'='*60}")
        print("SEED SOGGETTI ANAGRAFICI")
        print(f"{'='*60}")
        print(f"Persone fisiche da creare: {n_persone_fisiche}")
        print(f"Persone giuridiche da creare: {n_persone_giuridiche}")
        print(f"{'='*60}\n")

        # Genera persone fisiche
        print("Creazione persone fisiche...")
        for i in range(n_persone_fisiche):
            try:
                dati = genera_persona_fisica(i)

                # Verifica unicità CF
                existing = db.query(SoggettoAnagrafico).filter(
                    SoggettoAnagrafico.codice_fiscale == dati['codice_fiscale']
                ).first()
                if existing:
                    # Rigenera con nuovo CF
                    for _ in range(5):
                        dati = genera_persona_fisica(i)
                        existing = db.query(SoggettoAnagrafico).filter(
                            SoggettoAnagrafico.codice_fiscale == dati['codice_fiscale']
                        ).first()
                        if not existing:
                            break
                    if existing:
                        print(f"  [SKIP] CF duplicato dopo 5 tentativi")
                        continue

                # Verifica unicità P.IVA
                if dati['partita_iva']:
                    existing = db.query(SoggettoAnagrafico).filter(
                        SoggettoAnagrafico.partita_iva == dati['partita_iva']
                    ).first()
                    if existing:
                        dati['partita_iva'] = None  # Rimuovi P.IVA duplicata

                # Crea oggetto
                soggetto = SoggettoAnagrafico(
                    tipo_soggetto=TipoSoggetto.PERSONA_FISICA,
                    codice_fiscale=dati['codice_fiscale'],
                    partita_iva=dati['partita_iva'],
                    nome=dati['nome'],
                    cognome=dati['cognome'],
                    data_nascita=date.fromisoformat(dati['data_nascita']) if dati['data_nascita'] else None,
                    luogo_nascita=dati['luogo_nascita'],
                    email=dati['email'],
                    telefono=dati['telefono'],
                    cellulare=dati['cellulare'],
                    pec=dati['pec'],
                    indirizzo=dati['indirizzo'],
                    citta=dati['citta'],
                    cap=dati['cap'],
                    provincia=dati['provincia'],
                    attivo=True
                )
                db.add(soggetto)
                db.flush()  # Per ottenere l'ID

                dati['id'] = soggetto.id
                soggetti_creati.append(dati)

                if (i + 1) % 10 == 0:
                    print(f"  Creati {i + 1}/{n_persone_fisiche} persone fisiche")

            except Exception as e:
                errori.append(f"Persona fisica {i}: {str(e)}")

        # Genera persone giuridiche
        print("\nCreazione persone giuridiche...")
        for i in range(n_persone_giuridiche):
            try:
                dati = genera_persona_giuridica(i)

                # Verifica unicità P.IVA
                existing = db.query(SoggettoAnagrafico).filter(
                    SoggettoAnagrafico.partita_iva == dati['partita_iva']
                ).first()
                if existing:
                    # Rigenera con nuova P.IVA
                    for _ in range(5):
                        dati = genera_persona_giuridica(i)
                        existing = db.query(SoggettoAnagrafico).filter(
                            SoggettoAnagrafico.partita_iva == dati['partita_iva']
                        ).first()
                        if not existing:
                            break
                    if existing:
                        print(f"  [SKIP] P.IVA duplicata dopo 5 tentativi")
                        continue

                # Crea oggetto
                soggetto = SoggettoAnagrafico(
                    tipo_soggetto=TipoSoggetto.PERSONA_GIURIDICA,
                    partita_iva=dati['partita_iva'],
                    ragione_sociale=dati['ragione_sociale'],
                    email=dati['email'],
                    telefono=dati['telefono'],
                    pec=dati['pec'],
                    indirizzo=dati['indirizzo'],
                    citta=dati['citta'],
                    cap=dati['cap'],
                    provincia=dati['provincia'],
                    attivo=True
                )
                db.add(soggetto)
                db.flush()

                dati['id'] = soggetto.id
                soggetti_creati.append(dati)

                if (i + 1) % 10 == 0:
                    print(f"  Creati {i + 1}/{n_persone_giuridiche} persone giuridiche")

            except Exception as e:
                errori.append(f"Persona giuridica {i}: {str(e)}")

        # Commit finale
        db.commit()

        print(f"\n{'='*60}")
        print("RISULTATO SEED")
        print(f"{'='*60}")
        print(f"Soggetti creati con successo: {len(soggetti_creati)}")
        print(f"  - Persone fisiche: {len([s for s in soggetti_creati if s['tipo_soggetto'] == 'PERSONA_FISICA'])}")
        print(f"  - Persone giuridiche: {len([s for s in soggetti_creati if s['tipo_soggetto'] == 'PERSONA_GIURIDICA'])}")
        if errori:
            print(f"Errori: {len(errori)}")
            for err in errori[:5]:
                print(f"  - {err}")
        print(f"{'='*60}\n")

        return soggetti_creati

    except Exception as e:
        db.rollback()
        print(f"ERRORE CRITICO: {str(e)}")
        raise

    finally:
        if close_db:
            db.close()


def genera_report_markdown(soggetti: List[Dict], output_path: str = None) -> str:
    """
    Genera un report in formato Markdown con i dati inseriti.

    Args:
        soggetti: Lista dei soggetti creati
        output_path: Percorso del file di output (opzionale)

    Returns:
        Contenuto del report in Markdown
    """
    persone_fisiche = [s for s in soggetti if s['tipo_soggetto'] == 'PERSONA_FISICA']
    persone_giuridiche = [s for s in soggetti if s['tipo_soggetto'] == 'PERSONA_GIURIDICA']

    md = []
    md.append("# Report Seed Soggetti Anagrafici")
    md.append("")
    md.append(f"**Data generazione:** {date.today().isoformat()}")
    md.append("")
    md.append("## Riepilogo")
    md.append("")
    md.append(f"| Tipo | Quantita |")
    md.append(f"|------|----------|")
    md.append(f"| Persone Fisiche | {len(persone_fisiche)} |")
    md.append(f"| Persone Giuridiche | {len(persone_giuridiche)} |")
    md.append(f"| **Totale** | **{len(soggetti)}** |")
    md.append("")

    # Statistiche per provincia
    province = {}
    for s in soggetti:
        prov = s.get('provincia', 'N/D')
        province[prov] = province.get(prov, 0) + 1

    md.append("## Distribuzione per Provincia")
    md.append("")
    md.append("| Provincia | Soggetti |")
    md.append("|-----------|----------|")
    for prov, count in sorted(province.items(), key=lambda x: -x[1]):
        md.append(f"| {prov} | {count} |")
    md.append("")

    # Persone Fisiche
    md.append("## Persone Fisiche")
    md.append("")
    md.append("| ID | Nome | Cognome | Codice Fiscale | P.IVA | Citta | Provincia |")
    md.append("|----|------|---------|----------------|-------|-------|-----------|")
    for pf in persone_fisiche:
        piva = pf.get('partita_iva') or '-'
        md.append(f"| {pf.get('id', '-')} | {pf['nome']} | {pf['cognome']} | {pf['codice_fiscale']} | {piva} | {pf['citta']} | {pf['provincia']} |")
    md.append("")

    # Persone Giuridiche
    md.append("## Persone Giuridiche")
    md.append("")
    md.append("| ID | Ragione Sociale | Partita IVA | Email | Citta | Provincia |")
    md.append("|----|-----------------|-------------|-------|-------|-----------|")
    for pg in persone_giuridiche:
        md.append(f"| {pg.get('id', '-')} | {pg['ragione_sociale']} | {pg['partita_iva']} | {pg['email']} | {pg['citta']} | {pg['provincia']} |")
    md.append("")

    # Dettaglio completo
    md.append("## Dettaglio Completo - Persone Fisiche")
    md.append("")
    for i, pf in enumerate(persone_fisiche, 1):
        md.append(f"### {i}. {pf['nome']} {pf['cognome']}")
        md.append("")
        md.append(f"- **ID:** {pf.get('id', '-')}")
        md.append(f"- **Codice Fiscale:** `{pf['codice_fiscale']}`")
        if pf.get('partita_iva'):
            md.append(f"- **Partita IVA:** `{pf['partita_iva']}`")
        md.append(f"- **Data di Nascita:** {pf['data_nascita']}")
        md.append(f"- **Luogo di Nascita:** {pf['luogo_nascita']}")
        md.append(f"- **Indirizzo:** {pf['indirizzo']}")
        md.append(f"- **Citta:** {pf['citta']} ({pf['cap']}) {pf['provincia']}")
        md.append(f"- **Email:** {pf['email']}")
        if pf.get('telefono'):
            md.append(f"- **Telefono:** {pf['telefono']}")
        md.append(f"- **Cellulare:** {pf['cellulare']}")
        if pf.get('pec'):
            md.append(f"- **PEC:** {pf['pec']}")
        md.append("")

    md.append("## Dettaglio Completo - Persone Giuridiche")
    md.append("")
    for i, pg in enumerate(persone_giuridiche, 1):
        md.append(f"### {i}. {pg['ragione_sociale']}")
        md.append("")
        md.append(f"- **ID:** {pg.get('id', '-')}")
        md.append(f"- **Partita IVA:** `{pg['partita_iva']}`")
        md.append(f"- **Indirizzo:** {pg['indirizzo']}")
        md.append(f"- **Citta:** {pg['citta']} ({pg['cap']}) {pg['provincia']}")
        md.append(f"- **Email:** {pg['email']}")
        if pg.get('telefono'):
            md.append(f"- **Telefono:** {pg['telefono']}")
        md.append(f"- **PEC:** {pg['pec']}")
        md.append("")

    content = '\n'.join(md)

    if output_path:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Report salvato in: {output_path}")

    return content


# =============================================================================
# ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Seed soggetti anagrafici')
    parser.add_argument('--pf', type=int, default=70, help='Numero persone fisiche (default: 70)')
    parser.add_argument('--pg', type=int, default=30, help='Numero persone giuridiche (default: 30)')
    parser.add_argument('--report', type=str, default=None, help='Path per il report MD')

    args = parser.parse_args()

    # Esegui seed
    soggetti = seed_soggetti_anagrafici(
        n_persone_fisiche=args.pf,
        n_persone_giuridiche=args.pg
    )

    # Genera report
    report_path = args.report or os.path.join(
        os.path.dirname(__file__),
        '../../../../docs/reports/seed_soggetti_report.md'
    )

    # Crea directory se non esiste
    os.makedirs(os.path.dirname(report_path), exist_ok=True)

    genera_report_markdown(soggetti, report_path)
