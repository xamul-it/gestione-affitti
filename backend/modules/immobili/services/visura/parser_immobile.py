"""
Parser for the tabular "Visura per immobile" (older layout, one or a few
units of the same particella).

Layout (pdftotext -layout):
  Dati della richiesta   Comune di MILANO ( Codice: F205)
  ...
  N.   DATI IDENTIFICATIVI            DATI DI CLASSAMENTO ...
       Sezione  Foglio  Particella  Sub  Zona  Micro  Categoria ...
       Urbana                            Cens. Zona
  1             481     60          21   2            A/3  4  6 vani  Totale: 143 m²  Euro 821,17 ...
                                                                      Totale escluse aree
                                                                      scoperte**: 142 m²
  Indirizzo     VIALE UMBRIA n. 49 piano: 5-S1-7 interno: 23;
  INTESTATO
  N.   DATI ANAGRAFICI   CODICE FISCALE   DIRITTI E ONERI REALI
  1    COGNOME Nome nato a X il dd/mm/yyyy   CF*   (1) Proprieta` per 1/1 ...

Every intestato applies to every unit of the visura. Identificativi are
assigned to columns using the header line positions, as in the sintetica
parser.
"""
import re
from typing import Dict, List, Optional

from .models import FabbricatoParsed, FormatoVisura, VisuraFormatError, VisuraParsed
from .parser_sintetica import (
    _CATEGORIA,
    _CLASSAMENTO,
    _ESCL_SUP,
    _RENDITA,
    _ROW_START,
    _TOT_SUP,
    _assign_identificativi,
    _parse_intestato_line,
    _word_pos,
)
from .text import normalize_categoria, parse_it_date, parse_it_decimal, split_lines

_COMUNE = re.compile(r"Comune di (.+?)\s*\(\s*Codice:\s*(\w+)\s*\)")
_HEADER = re.compile(r"^\s+Sezione\s+Foglio\s+Particella\b")
_INDIRIZZO = re.compile(r"^\s*Indirizzo\s{2,}(?P<ind>\S.*?)\s*$")
_PIANO = re.compile(r"\s+piano:\s*(?P<piano>[^;]+?)\s*(?=;|\s+interno:|$)", re.IGNORECASE)
_INTERNO = re.compile(r"\s+interno:\s*(?P<interno>[^;]+?)\s*(?=;|$)", re.IGNORECASE)
_INTESTATO = re.compile(r"^\s*INTESTAT[OI]\b")
_END_INTEST = re.compile(r"^\s*(DATI DERIVANTI DA|Mappali|Unità immobiliari n\.|Visura telematica)")


def _header_columns(line: str) -> Dict[str, int]:
    cols = {
        "sezione": _word_pos(line, "Sezione"),
        "foglio": _word_pos(line, "Foglio"),
        "numero": _word_pos(line, "Particella"),
        "sub": _word_pos(line, "Sub"),
        "zona": _word_pos(line, "Zona"),
        "micro": _word_pos(line, "Micro"),
    }
    return {k: v for k, v in cols.items() if v is not None}


def _split_indirizzo(raw: str):
    """'VIALE UMBRIA n. 49 piano: 5-S1-7 interno: 23;' -> ('VIALE UMBRIA n. 49 interno 23', '5-S1-7')."""
    piano = interno = None
    m = _PIANO.search(raw)
    if m:
        piano = m.group("piano").strip()
    m = _INTERNO.search(raw)
    if m:
        interno = m.group("interno").strip()
    base = re.split(r"\s+(?:piano|interno|scala):", raw, maxsplit=1, flags=re.IGNORECASE)[0]
    base = re.sub(r"\s+", " ", base).strip().rstrip(";").strip()
    if interno:
        base = f"{base} interno {interno}"
    return base, piano


def parse_immobile(text: str) -> VisuraParsed:
    lines = split_lines(text)

    numero_m = re.search(r"Visura n\.:\s*(\S+)", text)
    data_m = re.search(r"Data:\s*(\d{2}/\d{2}/\d{4})", text)
    if not numero_m or not data_m:
        raise VisuraFormatError("Visura per immobile non riconosciuta: numero o data mancanti")
    comune_m = _COMUNE.search(text)
    if not comune_m:
        raise VisuraFormatError("Visura per immobile non riconosciuta: comune mancante")
    comune, codice = comune_m.group(1).strip(), comune_m.group(2)

    warnings: List[str] = []
    units: List[dict] = []
    intestati = []
    cols: Optional[Dict[str, int]] = None
    mode = None  # "table" | "intest"

    for i, line in enumerate(lines):
        if _HEADER.match(line):
            cols = _header_columns(line)
            mode = "table"
            continue
        if _INTESTATO.match(line):
            mode = "intest"
            continue
        if mode == "intest":
            if _END_INTEST.match(line):
                mode = None
                continue
            intestato = _parse_intestato_line(line)
            if intestato is not None:
                intestati.append(intestato)
            continue
        m = _INDIRIZZO.match(line)
        if m and units:
            units[-1]["indirizzo"], units[-1]["piano"] = _split_indirizzo(m.group("ind"))
            continue
        if mode != "table" or cols is None or not _ROW_START.match(line):
            continue
        cat_m = _CATEGORIA.search(line)
        if not cat_m:
            continue
        ident = _assign_identificativi(line[: cat_m.start() + 1], cols)
        if "foglio" not in ident or "numero" not in ident:
            warnings.append(f"Riga non interpretabile nella visura: {line.strip()[:80]}")
            continue
        cls = _CLASSAMENTO.search(line, cat_m.start())
        following = "\n".join(lines[i: i + 4])
        tot_m = _TOT_SUP.search(line)
        escl_m = _ESCL_SUP.search(following)
        rendita_m = _RENDITA.search(line)
        cons = cls.group("cons") if cls else None
        unit = cls.group("unit") if cls else None
        consistenza = vani = None
        if cons:
            if unit == "vani":
                consistenza, vani = f"{cons} vani", parse_it_decimal(cons)
            else:
                consistenza = f"{cons} m2"
        units.append({
            "ident": ident,
            "categoria": normalize_categoria(cat_m.group(1)),
            "classe": cls.group("classe") if cls else None,
            "consistenza": consistenza,
            "vani": vani,
            "totale": parse_it_decimal(tot_m.group(1)) if tot_m else None,
            "escluse": parse_it_decimal(escl_m.group(1)) if escl_m else None,
            "rendita": parse_it_decimal(rendita_m.group(1)) if rendita_m else None,
            "indirizzo": None,
            "piano": None,
        })

    if not units:
        raise VisuraFormatError("Visura per immobile: nessuna unità immobiliare trovata")
    if not intestati:
        warnings.append("Nessun intestato trovato nella visura")

    fabbricati = [
        FabbricatoParsed(
            comune=comune,
            codice_catastale_comune=codice,
            provincia=None,
            sezione_urbana=u["ident"].get("sezione"),
            foglio=u["ident"]["foglio"],
            particella=u["ident"]["numero"],
            subalterno=u["ident"].get("sub"),
            zona_censuaria=u["ident"].get("zona"),
            micro_zona=u["ident"].get("micro"),
            categoria=u["categoria"],
            classe=u["classe"],
            consistenza=u["consistenza"],
            vani=u["vani"],
            superficie_totale=u["totale"],
            superficie_escluse_aree=u["escluse"],
            rendita=u["rendita"],
            indirizzo=u["indirizzo"],
            piano=u["piano"],
            intestati=list(intestati),
        )
        for u in units
    ]

    return VisuraParsed(
        formato=FormatoVisura.SINTETICA,
        numero=numero_m.group(1),
        data=parse_it_date(data_m.group(1)),
        soggetto_cf=None,
        fabbricati=fabbricati,
        terreni_count=0,
        warnings=warnings,
    )
