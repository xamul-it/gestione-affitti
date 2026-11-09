"""
Parser for "Visura attuale per soggetto" (analitica) and its single-unit
sibling "Visura attuale per immobile" (same layout, but the unit header has
no "n.N" line and intestati come under "Intestazione attuale dell'immobile -
totale intestati: K").

Two-column layout: the right column ("Causali di aggiornamento ed
annotazioni") is dropped by keeping, for each line, only the text before
the first gap of 3+ spaces, and only when the line starts near the left
margin (right-column-only lines start far to the right).

Each unit is a block "Immobile di catasto fabbricati - n.N"; intestati come
in "Intestazione attuale degli immobili dal n. A al n. B" (or
"dell'immobile n. N") and apply to that range of units.
"""
import re
from typing import Dict, List, Optional

from .models import FabbricatoParsed, FormatoVisura, IntestatoParsed, VisuraFormatError, VisuraParsed
from .text import (
    build_intestato,
    normalize_categoria,
    parse_it_date,
    parse_it_decimal,
    split_indirizzo,
    split_lines,
)

_LEFT_MARGIN = 20

_UNIT_HDR = re.compile(r"^Immobile di catasto (fabbricati|terreni)\b")
_UNIT_N = re.compile(r"^n\.\s*(\d+)$")
_COMUNE = re.compile(r"^Comune di (.+?) \((\w{4})\)(?: \((\w{2})\))?")
# Long comune names push "(C310) (GR)" to the next line.
_COMUNE_NOME = re.compile(r"^Comune di (.+?)$")
_COMUNE_CODICE = re.compile(r"^\((\w{4})\)(?: \((\w{2})\))?$")
_IDENT = re.compile(
    r"^(?:Sezione Urbana (?P<sez>\S+) )?Foglio (?P<foglio>\S+) Particella (?P<particella>\S+)"
    r"(?: Subalterno (?P<sub>\S+))?"
)
_RENDITA = re.compile(r"^Rendita: Euro ([\d.]+,\d{2})")
_ZONA = re.compile(r"Zona censuaria (\w+)")
_MICRO = re.compile(r"Micro ?zona (\w+)", re.IGNORECASE)
_CLASSAMENTO = re.compile(
    r"^Categoria (?P<cat>[A-F]/\d{1,2})\w?\)?(?:, Classe (?P<classe>\w+))?"
    r"(?:, Consistenza (?P<cons>\d+(?:,\d+)?) (?P<unit>vani|m2|m²|mq))?"
)
_TOT = re.compile(r"^Totale: (\d+(?:,\d+)?) m")
_ESCL = re.compile(r"^Totale escluse aree scoperte\s*\w?\)?: (\d+(?:,\d+)?) m")
_INTEST_RANGE = re.compile(r"^Intestazione attuale degli immobili dal n\. (\d+) al n\. (\d+)")
_INTEST_ONE = re.compile(r"^Intestazione attuale dell'immobile n\. (\d+)")
_INTEST_SINGLE = re.compile(r"^Intestazione attuale dell.immobile - totale intestati")
_ENTRY = re.compile(r"^(\d+)\.\s+(\S.*)$")
_CF = re.compile(r"^\(CF ([A-Z0-9]{11,16})\)")
_NATO = re.compile(r"^nat[oa] a (.+?) il (\d{2}/\d{2}/\d{4})")
_DIRITTO = re.compile(r"^Diritto di:\s*(.*)$")
_END_INTEST = re.compile(r"^(Totale Parziale|Totale generale|Immobile di catasto|Catasto Fabbricati|Visura telematica)")


def _left(line: str) -> str:
    stripped = line.lstrip()
    if not stripped or len(line) - len(stripped) > _LEFT_MARGIN:
        return ""
    left = re.split(r"\s{3,}", stripped, maxsplit=1)[0].strip()
    # Some visure bullet the identificativi line: "• Foglio 483 Particella 65 ..."
    return re.sub(r"^[•·\-*]\s+", "", left)


def _clean_diritto(text: str) -> str:
    text = re.sub(r"\s*\(deriva dall'atto.*$", "", text)
    text = re.sub(r"\s+per\s+(?=\d+\s*/\s*\d+)", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _finish_entry(entry: Optional[dict], out: List[IntestatoParsed]) -> None:
    if not entry or not entry.get("diritto"):
        return
    out.append(build_intestato(
        entry["nominativo"],
        entry.get("cf"),
        entry.get("data_nascita"),
        entry.get("luogo"),
        _clean_diritto(" ".join(entry["diritto"])),
    ))


def parse_analitica(text: str, per_immobile: bool = False) -> VisuraParsed:
    numero_m = re.search(r"Numero Pratica:\s*(\S+)", text)
    data_m = re.search(r"Data:\s*(\d{2}/\d{2}/\d{4})", text)
    if not numero_m or not data_m:
        raise VisuraFormatError("Visura analitica non riconosciuta: numero o data mancanti")
    cf_m = re.search(r"\(CF:\s*([A-Z0-9]{11,16})\)", text)

    lines = [_left(l) for l in split_lines(text)]

    units: Dict[int, dict] = {}
    intestati_ranges: List[tuple] = []  # (from, to, [IntestatoParsed])
    terreni_count = 0
    warnings: List[str] = []

    current: Optional[dict] = None
    mode = None  # "unit" | "indirizzo" | "intest"
    intest_list: Optional[List[IntestatoParsed]] = None
    entry: Optional[dict] = None
    in_diritto = False
    expect_unit_n = None

    for line in lines:
        if not line:
            in_diritto = False
            continue

        hdr = _UNIT_HDR.match(line)
        if hdr:
            if mode == "intest":
                _finish_entry(entry, intest_list)
                entry = None
            if per_immobile and hdr.group(1) == "fabbricati" and not units:
                current = {"n": 1}
                units[1] = current
                mode = "unit"
                continue
            expect_unit_n = hdr.group(1)
            mode = None
            continue
        if expect_unit_n:
            n_m = _UNIT_N.match(line)
            if n_m:
                if expect_unit_n == "terreni":
                    terreni_count += 1
                    current = None
                else:
                    current = {"n": int(n_m.group(1))}
                    units[current["n"]] = current
                mode = "unit"
                expect_unit_n = None
                continue

        r = _INTEST_RANGE.match(line)
        o = _INTEST_ONE.match(line)
        single = per_immobile and _INTEST_SINGLE.match(line)
        if r or o or single:
            if r:
                start, end = int(r.group(1)), int(r.group(2))
            elif o:
                start = end = int(o.group(1))
            else:
                start = end = 1
            intest_list = []
            intestati_ranges.append((start, end, intest_list))
            mode = "intest"
            entry = None
            in_diritto = False
            current = None
            continue

        if mode == "intest":
            if _END_INTEST.match(line):
                _finish_entry(entry, intest_list)
                entry = None
                mode = None
                continue
            e = _ENTRY.match(line)
            if e:
                _finish_entry(entry, intest_list)
                entry = {"nominativo": e.group(2), "diritto": []}
                in_diritto = False
                continue
            if entry is None:
                continue
            m = _CF.match(line)
            if m:
                entry["cf"] = m.group(1)
                continue
            m = _NATO.match(line)
            if m:
                entry["luogo"] = re.sub(r"\s*\([A-Z]{2}\)\s*$", "", m.group(1)).strip()
                entry["data_nascita"] = parse_it_date(m.group(2))
                continue
            m = _DIRITTO.match(line)
            if m:
                entry["diritto"] = [m.group(1)]
                in_diritto = True
                continue
            if in_diritto:
                entry["diritto"].append(line)
            continue

        if current is None:
            continue

        if mode == "indirizzo":
            current["indirizzo"], current["piano"] = split_indirizzo(line)
            mode = "unit"
            continue
        if line == "Indirizzo":
            mode = "indirizzo"
            continue
        # The catasto terreni counterpart repeats Comune/Foglio/Particella
        # without subalterno: never take identificativi from it.
        if line.startswith("Particelle corrispondenti al catasto terreni"):
            mode = "terreni_corr"
            continue
        if mode == "terreni_corr":
            if _COMUNE_NOME.match(line) or _COMUNE_CODICE.match(line) or _IDENT.match(line):
                continue
            mode = "unit"
        if current.pop("codice_a_capo", False):
            m = _COMUNE_CODICE.match(line)
            if m:
                current["codice"], current["provincia"] = m.group(1), m.group(2)
                continue
        m = _COMUNE.match(line)
        if m and "comune" not in current:
            current["comune"], current["codice"], current["provincia"] = m.group(1), m.group(2), m.group(3)
            continue
        m = _COMUNE_NOME.match(line)
        if m and "comune" not in current:
            current["comune"], current["codice_a_capo"] = m.group(1).strip(), True
            continue
        m = _IDENT.match(line)
        if m and "foglio" not in current:
            current.update(sez=m.group("sez"), foglio=m.group("foglio"),
                           particella=m.group("particella"), sub=m.group("sub"))
            continue
        m = _RENDITA.match(line)
        if m:
            current["rendita"] = parse_it_decimal(m.group(1))
            continue
        m = _ZONA.search(line)
        if m:
            current["zona"] = m.group(1)
            mm = _MICRO.search(line)
            if mm:
                current["micro"] = mm.group(1)
            continue
        m = _CLASSAMENTO.match(line)
        if m:
            current["categoria"] = normalize_categoria(m.group("cat"))
            current["classe"] = m.group("classe")
            if m.group("cons"):
                is_vani = m.group("unit") == "vani"
                current["consistenza"] = f"{m.group('cons')} {'vani' if is_vani else 'm2'}"
                if is_vani:
                    current["vani"] = parse_it_decimal(m.group("cons"))
            continue
        m = _ESCL.match(line)
        if m:
            current["escluse"] = parse_it_decimal(m.group(1))
            continue
        m = _TOT.match(line)
        if m and "totale" not in current:
            current["totale"] = parse_it_decimal(m.group(1))
            continue

    if mode == "intest":
        _finish_entry(entry, intest_list)

    fabbricati: List[FabbricatoParsed] = []
    for n in sorted(units):
        u = units[n]
        if "foglio" not in u or "categoria" not in u:
            warnings.append(f"Immobile n.{n} non interpretabile: dati identificativi o classamento mancanti")
            continue
        intestati: List[IntestatoParsed] = []
        for start, end, lst in intestati_ranges:
            if start <= n <= end:
                intestati = list(lst)
        if not intestati:
            warnings.append(f"Nessun intestato trovato per l'immobile n.{n}")
        fabbricati.append(FabbricatoParsed(
            comune=u.get("comune", ""),
            codice_catastale_comune=u.get("codice", ""),
            provincia=u.get("provincia"),
            sezione_urbana=u.get("sez"),
            foglio=u["foglio"],
            particella=u["particella"],
            subalterno=u.get("sub"),
            zona_censuaria=u.get("zona"),
            micro_zona=u.get("micro"),
            categoria=u["categoria"],
            classe=u.get("classe"),
            consistenza=u.get("consistenza"),
            vani=u.get("vani"),
            superficie_totale=u.get("totale"),
            superficie_escluse_aree=u.get("escluse"),
            rendita=u.get("rendita"),
            indirizzo=u.get("indirizzo"),
            piano=u.get("piano"),
            intestati=intestati,
        ))

    return VisuraParsed(
        formato=FormatoVisura.ANALITICA,
        numero=numero_m.group(1),
        data=parse_it_date(data_m.group(1)),
        soggetto_cf=cf_m.group(1) if cf_m else None,
        fabbricati=fabbricati,
        terreni_count=terreni_count,
        warnings=warnings,
    )
