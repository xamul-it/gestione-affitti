"""
Text extraction and shared parsing helpers for catasto visure.

Visure from the Agenzia delle Entrate are native-text PDFs: poppler's
`pdftotext -layout` (already installed for pdf2image) keeps the column
layout, which both parsers rely on.
"""
import re
import subprocess
from datetime import date, datetime
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional, Tuple

from immobili.models.diritti_immobile import TipoDiritto

from .models import FormatoVisura, IntestatoParsed, VisuraFormatError

UNSUPPORTED_MSG = "Formato non supportato: carica una visura catastale sintetica o analitica"

_CF_PF = re.compile(r"^[A-Z]{6}[0-9LMNPQRSTUV]{2}[A-Z][0-9LMNPQRSTUV]{2}[A-Z][0-9LMNPQRSTUV]{3}[A-Z]$")
_CF_PG = re.compile(r"^\d{11}$")
_QUOTA = re.compile(r"(\d+)\s*/\s*(\d+)")


def pdf_to_text(pdf_bytes: bytes) -> str:
    if not pdf_bytes.startswith(b"%PDF"):
        raise VisuraFormatError("Il file caricato non è un PDF valido")
    try:
        result = subprocess.run(
            ["pdftotext", "-layout", "-enc", "UTF-8", "-", "-"],
            input=pdf_bytes,
            capture_output=True,
            timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise VisuraFormatError("Impossibile leggere il PDF") from exc
    text = result.stdout.decode("utf-8", errors="replace")
    if result.returncode != 0 or not text.strip():
        raise VisuraFormatError("Impossibile leggere il PDF: nessun testo trovato (scansioni non supportate)")
    return text


def detect_formato(text: str) -> FormatoVisura:
    if "Visura attuale sintetica per soggetto" in text:
        return FormatoVisura.SINTETICA
    if "Visura attuale per soggetto" in text:
        return FormatoVisura.ANALITICA
    raise VisuraFormatError(UNSUPPORTED_MSG)


def split_lines(text: str) -> list:
    return [line.replace("\f", "") for line in text.split("\n")]


def parse_it_decimal(value: str) -> Decimal:
    """'1.316,97' -> Decimal('1316.97'); '4,5' -> Decimal('4.5')."""
    return Decimal(value.replace(".", "").replace(",", "."))


def parse_it_date(value: str) -> date:
    return datetime.strptime(value, "%d/%m/%Y").date()


def normalize_categoria(raw: str) -> str:
    """'A/3a)' -> 'A/3'; 'C/2' -> 'C/2'."""
    m = re.match(r"([A-F])\s*/\s*(\d{1,2})", raw.strip())
    return f"{m.group(1)}/{m.group(2)}" if m else raw.strip()


def strip_zeros(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    stripped = value.strip().lstrip("0")
    return stripped or ("0" if value.strip() else None)


def parse_diritto(testo: str) -> Tuple[TipoDiritto, Optional[Decimal]]:
    quota = None
    m = _QUOTA.search(testo)
    if m and int(m.group(2)):
        quota = (Decimal(m.group(1)) / Decimal(m.group(2)) * 100).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )

    t = testo.lower().replace("à", "a'").strip()
    t = re.sub(r"^diritto di\s+", "", t)
    if t.startswith("nuda propr"):
        tipo = TipoDiritto.NUDA_PROPRIETA
    elif "superficiari" in t or t.startswith("superficie"):
        tipo = TipoDiritto.SUPERFICIE
    elif t.startswith("propr"):
        tipo = TipoDiritto.PROPRIETARIO if quota is None or quota >= 100 else TipoDiritto.COMPROPRIETARIO
    elif t.startswith("usufrutt"):
        tipo = TipoDiritto.USUFRUTTUARIO
    elif re.match(r"uso\b", t):
        tipo = TipoDiritto.USO
    elif t.startswith("abitazion"):
        tipo = TipoDiritto.ABITAZIONE
    elif t.startswith("enfiteus"):
        tipo = TipoDiritto.ENFITEUSI
    else:
        tipo = TipoDiritto.ALTRO
    return tipo, quota


def build_intestato(
    nominativo: str,
    codice_fiscale: Optional[str],
    data_nascita: Optional[date],
    luogo_nascita: Optional[str],
    diritto_testo: str,
) -> IntestatoParsed:
    nominativo = re.sub(r"\s+", " ", nominativo).strip()
    cf = (codice_fiscale or "").replace("*", "").strip().upper() or None
    persona_giuridica = cf is None or bool(_CF_PG.match(cf))
    cognome = nome = ragione_sociale = None
    if persona_giuridica:
        ragione_sociale = nominativo
    else:
        words = nominativo.split(" ")
        idx = 0
        while idx < len(words) and words[idx] == words[idx].upper() and re.search(r"[A-Z]", words[idx]):
            idx += 1
        if 0 < idx < len(words):
            cognome, nome = " ".join(words[:idx]), " ".join(words[idx:])
        else:
            cognome = nominativo
    diritto_testo = re.sub(r"\s+", " ", diritto_testo).strip()
    tipo, quota = parse_diritto(diritto_testo)
    return IntestatoParsed(
        nominativo=nominativo,
        cognome=cognome,
        nome=nome,
        ragione_sociale=ragione_sociale,
        codice_fiscale=cf,
        persona_giuridica=persona_giuridica,
        data_nascita=data_nascita if not persona_giuridica else None,
        luogo_nascita=luogo_nascita if not persona_giuridica else None,
        diritto_testo=diritto_testo,
        tipo_diritto=tipo,
        quota_percentuale=quota,
    )


ADDRESS_PIANO = re.compile(r"^(?P<ind>.+?)\s+Piano\s+(?P<piano>\S.*?)\s*$")


def split_indirizzo(raw: str) -> Tuple[str, Optional[str]]:
    raw = re.sub(r"\s+", " ", raw).strip()
    m = ADDRESS_PIANO.match(raw)
    if m:
        return m.group("ind"), m.group("piano")
    return raw, None
