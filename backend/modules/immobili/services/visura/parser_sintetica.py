"""
Parser for "Visura attuale sintetica per soggetto".

Layout (pdftotext -layout): numbered blocks
  "N. Immobili siti nel Comune di X (Codice A944) Catasto dei Fabbricati"
each with a table whose rows span several lines (address above the numeric
row, superficie split around it), followed by
  "Intestazione degli immobili indicati al n.N"
listing the intestati that apply to every unit of block N. Columns are
located from the table header of the same page, since widths change per
page.
"""
import re
from typing import Dict, List, Optional

from .models import FabbricatoParsed, FormatoVisura, VisuraFormatError, VisuraParsed
from .text import (
    build_intestato,
    normalize_categoria,
    parse_it_date,
    parse_it_decimal,
    split_indirizzo,
    split_lines,
)

_BLOCK = re.compile(
    r"^\s*(\d+)\.\s+Immobili siti nel Comune di (.+?) \(Codice (\w+)\)\s+Catasto dei (Fabbricati|Terreni)"
)
_HEADER1 = re.compile(r"^\s*N\.\s+Sez\b")
_INTEST = re.compile(r"Intestazione degli immobili indicati al n\.\s*(\d+)")
_ROW_START = re.compile(r"^\s{0,4}(\d+)\s{2,}\S")
_CATEGORIA = re.compile(r"\s([A-F]/\d{1,2})\s")
_CLASSAMENTO = re.compile(
    r"(?P<cat>[A-F]/\d{1,2})\s+(?:(?P<classe>[0-9A-Z]{1,2})\s+)?"
    r"(?:(?P<cons>\d+(?:,\d+)?)\s*(?P<unit>vani|m²|m2|mq))?"
)
_RENDITA = re.compile(r"Euro\s+([\d.]+,\d{2})")
_STREET = re.compile(
    r"^(VIA|VIALE|V\.LE|PIAZZA|P\.ZA|PIAZZALE|CORSO|C\.SO|LARGO|VICOLO|VICOLETTO|STRADA|STRADELLO|"
    r"LOCALITA'?|LOC\.|FRAZIONE|CONTRADA|BORGO|SALITA|VIALETTO|RIVA|FONDAMENTA|CALLE|LUNGOMARE|"
    r"LUNGOTEVERE|PASSAGGIO|GALLERIA|TRAVERSA|PIAZZETTA|RUGA|RIONE)\s"
)
_TOT_SUP = re.compile(r"Totale:\s*(\d+(?:,\d+)?)\s*m")
_ESCL_SUP = re.compile(r"scoperte\*+:\s*(\d+(?:,\d+)?)\s*m")
_NATO = re.compile(r"^(?P<nome>.*?)\s+nat[oa]\s+a\s+(?P<luogo>.+?)\s+il\s+(?P<data>\d{2}/\d{2}/\d{4})")
_CF = re.compile(r"\b([A-Z0-9]{16}|\d{11})\*?(?=\s|$)")
_DIRITTO = re.compile(r"\(\d+\)\s+(.+?)\s*$")


def _word_pos(line: str, word: str) -> Optional[int]:
    m = re.search(rf"\b{re.escape(word)}\b", line)
    return m.start() if m else None


def _header_columns(lines: List[str], idx: int) -> Dict[str, int]:
    l1, l2 = lines[idx], lines[idx + 1] if idx + 1 < len(lines) else ""
    cols = {
        "sezione": _word_pos(l1, "Sez"),
        "foglio": _word_pos(l2, "Foglio"),
        "numero": _word_pos(l2, "Numero"),
        "sub": _word_pos(l2, "Sub"),
        "zona": _word_pos(l1, "Zona"),
        "micro": _word_pos(l1, "Micro"),
    }
    cols = {k: v for k, v in cols.items() if v is not None}
    cols["_indirizzo"] = _word_pos(l1, "Indirizzo") or 140
    return cols


def _assign_identificativi(prefix: str, cols: Dict[str, int]) -> Dict[str, str]:
    out: Dict[str, str] = {}
    data_cols = sorted((v, k) for k, v in cols.items() if not k.startswith("_"))
    tokens = list(re.finditer(r"\S+", prefix))[1:]  # skip row number
    for tok in tokens:
        candidates = [(pos, name) for pos, name in data_cols if pos <= tok.end() - 1]
        if not candidates:
            continue
        name = candidates[-1][1]
        out.setdefault(name, tok.group())
    return out


def _find_indirizzo(lines, row, lower, ind_col):
    # The address column is left of its "Indirizzo" header word (the header
    # is centred), so take the last 2+-space separated chunk of the line
    # when it starts in the right-hand area of the table.
    for j in range(row - 1, max(lower, row - 5) - 1, -1):
        chunks = list(re.finditer(r"\S+(?: \S+)*", lines[j]))
        if not chunks or chunks[-1].start() < ind_col - 30:
            continue
        seg = chunks[-1].group()
        if _STREET.match(seg) or re.search(r"\sPiano\s", seg):
            return split_indirizzo(seg)
    return None, None


def _parse_intestato_line(line: str):
    m = _DIRITTO.search(line)
    if not m:
        return None
    diritto = m.group(1)
    before = line[: m.start()]
    row = _ROW_START.match(before)
    if not row:
        return None
    anag = before[row.end() - 1:]
    cf = None
    cf_m = None
    for cand in _CF.finditer(anag):
        cf_m = cand
    if cf_m:
        cf = cf_m.group(1)
        anag = anag[: cf_m.start()]
    anag = anag.strip()
    data_nascita = luogo = None
    nato = _NATO.match(anag)
    if nato:
        anag = nato.group("nome")
        luogo = re.sub(r"\s*\([A-Z]{2}\)\s*$", "", nato.group("luogo")).strip()
        data_nascita = parse_it_date(nato.group("data"))
    return build_intestato(anag, cf, data_nascita, luogo, diritto)


def parse_sintetica(text: str) -> VisuraParsed:
    lines = split_lines(text)

    numero_m = re.search(r"Visura n\.:\s*(\S+)", text)
    data_m = re.search(r"Data:\s*(\d{2}/\d{2}/\d{4})", text)
    if not numero_m or not data_m:
        raise VisuraFormatError("Visura sintetica non riconosciuta: numero o data mancanti")
    cf_m = re.search(r"\(CF:\s*([A-Z0-9]{11,16})\)", text)

    blocks: Dict[str, dict] = {}
    fabbricati_by_block: Dict[str, List[FabbricatoParsed]] = {}
    terreni_count = 0
    warnings: List[str] = []

    current_block: Optional[dict] = None
    cols: Optional[Dict[str, int]] = None
    mode = None  # "table" | "intest"
    intest_block: Optional[str] = None
    row_indices: List[int] = []
    pending_rows: List[tuple] = []  # (line index, block)

    for i, line in enumerate(lines):
        bm = _BLOCK.match(line)
        if bm:
            current_block = {
                "n": bm.group(1),
                "comune": bm.group(2).strip(),
                "codice": bm.group(3),
                "terreni": bm.group(4) == "Terreni",
            }
            blocks[current_block["n"]] = current_block
            mode = None
            continue
        if _HEADER1.match(line):
            cols = _header_columns(lines, i)
            mode = "table"
            continue
        im = _INTEST.search(line)
        if im:
            mode = "intest"
            intest_block = im.group(1)
            continue
        if line.startswith("DATI DERIVANTI DA"):
            mode = None
            continue

        if mode == "table" and current_block is not None:
            if not _ROW_START.match(line):
                continue
            if current_block["terreni"]:
                terreni_count += 1
                continue
            if _CATEGORIA.search(line):
                row_indices.append(i)
                pending_rows.append((i, current_block, dict(cols)))
        elif mode == "intest" and intest_block is not None:
            intestato = _parse_intestato_line(line)
            if intestato is not None:
                blocks.setdefault(intest_block, {}).setdefault("intestati", []).append(intestato)

    for k, (i, block, row_cols) in enumerate(pending_rows):
        line = lines[i]
        prev_row = row_indices[k - 1] if k > 0 else -1
        next_row = row_indices[k + 1] if k + 1 < len(row_indices) else len(lines)
        cat_m = _CATEGORIA.search(line)
        ident = _assign_identificativi(line[: cat_m.start() + 1], row_cols)
        if "foglio" not in ident or "numero" not in ident:
            warnings.append(f"Riga non interpretabile nella visura: {line.strip()[:80]}")
            continue
        cls = _CLASSAMENTO.search(line, cat_m.start())
        ind_col = row_cols["_indirizzo"]
        indirizzo, piano = _find_indirizzo(lines, i, prev_row + 1, ind_col)

        window = [
            lines[j][: max(0, ind_col - 4)]
            for j in range(max(prev_row + 1, i - 2), min(next_row, i + 3))
        ]
        window_text = "\n".join(window)
        tot_m = _TOT_SUP.search(window_text)
        escl_m = _ESCL_SUP.search(window_text)
        rendita_m = _RENDITA.search(line)

        cons = cls.group("cons") if cls else None
        unit = cls.group("unit") if cls else None
        consistenza = None
        vani = None
        if cons:
            if unit == "vani":
                consistenza = f"{cons} vani"
                vani = parse_it_decimal(cons)
            else:
                consistenza = f"{cons} m2"

        fabbricati_by_block.setdefault(block["n"], []).append(FabbricatoParsed(
            comune=block["comune"],
            codice_catastale_comune=block["codice"],
            provincia=None,
            sezione_urbana=ident.get("sezione"),
            foglio=ident["foglio"],
            particella=ident["numero"],
            subalterno=ident.get("sub"),
            zona_censuaria=ident.get("zona"),
            micro_zona=ident.get("micro"),
            categoria=normalize_categoria(cat_m.group(1)),
            classe=cls.group("classe") if cls else None,
            consistenza=consistenza,
            vani=vani,
            superficie_totale=parse_it_decimal(tot_m.group(1)) if tot_m else None,
            superficie_escluse_aree=parse_it_decimal(escl_m.group(1)) if escl_m else None,
            rendita=parse_it_decimal(rendita_m.group(1)) if rendita_m else None,
            indirizzo=indirizzo,
            piano=piano,
        ))

    fabbricati: List[FabbricatoParsed] = []
    for n, units in fabbricati_by_block.items():
        intestati = blocks.get(n, {}).get("intestati", [])
        if not intestati:
            warnings.append(f"Nessun intestato trovato per il gruppo di immobili n.{n}")
        for unit in units:
            unit.intestati = list(intestati)
            fabbricati.append(unit)

    return VisuraParsed(
        formato=FormatoVisura.SINTETICA,
        numero=numero_m.group(1),
        data=parse_it_date(data_m.group(1)),
        soggetto_cf=cf_m.group(1) if cf_m else None,
        fabbricati=fabbricati,
        terreni_count=terreni_count,
        warnings=warnings,
    )
