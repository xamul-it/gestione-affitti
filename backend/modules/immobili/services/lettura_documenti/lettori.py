"""
Readers of the immobili document types: how each type is recognised in the
text and which fields are read. Declared once here and applied both by the
backend (native-text PDFs) and by the external OCR service (scans).

Order matters: the first recognised spec wins. Specs with `scarto` belong to
other modules and are only recognised to be refused with a message.
"""
from datetime import datetime
from typing import List, Optional

from ..visura.text import strip_zeros
from .motore import RisultatoTipo, SpecTipo, applica

MSG_RLI = "Ricevuta di registrazione del contratto: caricala dal contratto, nel modulo Affitti"

CLASSI_ENERGETICHE = ("A4", "A3", "A2", "A1", "B", "C", "D", "E", "F", "G")

# APE: cadastral table "Cod. Comune / Sezione / Foglio / Particella / Subalterno"
# with the values on the next line (layout of the regional APE forms).
_TAB = r"Cod\.\s*Comune\s+Sezione\s+Foglio\s+Particella\s+Subalterno[^\n]*\n\s*"
_DATA = r"(?P<v>\d{2}/\d{2}/\d{4})"

LETTORI: List[SpecTipo] = [
    SpecTipo(
        codice="RLI12",
        riconosci=[r"RLI12|REGISTRAZIONE\s+CONTRATTI\s+DI\s+LOCAZIONE"],
        scarto=MSG_RLI,
    ),
    SpecTipo(
        codice="VISURA_CATASTALE",
        riconosci=[r"Visura\s+(?:attuale\s+)?(?:sintetica\s+)?per\s+(?:soggetto|immobile)"],
    ),
    SpecTipo(
        codice="APE",
        riconosci=[r"PRESTAZIONE\s+ENERGETICA", r"EP\s*gl,?\s*nren"],
        campi={
            "codice_comune": _TAB + r"(?P<v>[A-Z]\d{3})\b",
            "foglio": _TAB + r"[A-Z]\d{3}\s+\S+\s+(?P<v>\d+)",
            "particella": _TAB + r"[A-Z]\d{3}\s+\S+\s+\d+\s+(?P<v>\d+)",
            "subalterno": _TAB + r"[A-Z]\d{3}\s+\S+\s+\d+\s+\d+\s+(?P<v>\d+)",
            "comune": r"Comune:\s*(?P<v>[^\n]+?)\s*\n",
            "indirizzo": r"Indirizzo:\s*(?P<v>[^\n]+?)\s*\n",
            "piano": r"Piano\s*-\s*Interno:\s*(?P<v>[^\s°-]+)",
            "classe": r"Classe\s+energetica\s*:?\s*(?-i:(?P<v>A[1-4]|[B-G]))\b",
            # The value sits among the class thresholds ("100<=Eptot<134"…).
            "ep_gl_nren": r"EP\s*gl,?\s*nren(?:\s|\d+\s*<=?\s*Eptot\s*[<>]=?\s*\d+|Eptot\s*[<>]=?\s*\d+)*"
                          r"(?P<v>\d{1,4},\d{1,2})",
            "rilasciato_il": r"RILASCIATO\s+IL\s+" + _DATA,
            "valido_fino_al": r"VALIDO\s+FINO\s+AL\s+" + _DATA,
        },
    ),
    SpecTipo(
        codice="PLANIMETRIA_CATASTALE",
        riconosci=[r"Planimetria", r"Catasto\s+dei\s+Fabbricati|Identificativi\s+Catastali"],
        campi={
            "comune": r"Comune\s+di\s+(?P<v>[^\n(]+?)\s*(?:\(|\n)",
            "foglio": r"Foglio\s*:?\s*(?P<v>\d+)",
            "particella": r"Particella\s*:?\s*(?P<v>\d+)",
            "subalterno": r"Subalterno\s*:?\s*(?P<v>\d+)",
        },
    ),
]


def spec_per_codice(codice: str) -> Optional[SpecTipo]:
    return next((s for s in LETTORI if s.codice == codice), None)


def riconosci_tipo(testo: str) -> Optional[RisultatoTipo]:
    for spec in LETTORI:
        r = applica(spec, testo)
        if r.riconosciuto:
            return r
    return None


def _data_iso(value: str) -> Optional[str]:
    try:
        return datetime.strptime(value, "%d/%m/%Y").date().isoformat()
    except ValueError:
        return None


def normalizza(codice: str, campi: dict) -> dict:
    """Read strings -> typed values. Unparseable values are dropped, not guessed."""
    dati = {}
    for chiave in ("foglio", "particella", "subalterno"):
        if campi.get(chiave):
            dati[chiave] = strip_zeros(campi[chiave])
    if campi.get("codice_comune"):
        dati["codice_comune"] = campi["codice_comune"].upper()
    if campi.get("comune"):
        dati["comune"] = campi["comune"].upper()
    for chiave in ("indirizzo", "piano"):
        if campi.get(chiave):
            dati[chiave] = campi[chiave]
    if codice == "APE":
        classe = (campi.get("classe") or "").upper()
        if classe in CLASSI_ENERGETICHE:
            dati["classe"] = classe
        if campi.get("ep_gl_nren"):
            try:
                dati["ep_gl_nren"] = float(campi["ep_gl_nren"].replace(".", "").replace(",", "."))
            except ValueError:
                pass
        for src, dst in (("rilasciato_il", "data_emissione"), ("valido_fino_al", "valido_fino_al")):
            iso = _data_iso(campi.get(src) or "")
            if iso:
                dati[dst] = iso
    return dati
