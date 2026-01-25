import csv
import io
import logging
import re
import unicodedata
import zipfile
from typing import Dict, List

import requests
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..models import ComuneItalia

logger = logging.getLogger(__name__)

COMUNI_SOURCE_URL = "https://lab.comuni-italiani.it/files/listacomuni.zip"


def _normalize_nome(value: str) -> str:
    if not value:
        return ""
    normalized = unicodedata.normalize("NFKD", value)
    normalized = "".join(ch for ch in normalized if not unicodedata.combining(ch))
    normalized = re.sub(r"[^a-zA-Z0-9 ]", " ", normalized)
    normalized = re.sub(r"\s+", " ", normalized).strip().lower()
    return normalized


def _decode_bytes(raw: bytes) -> str:
    for encoding in ("utf-8-sig", "utf-8", "latin-1"):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    return raw.decode("latin-1", errors="replace")


def _load_comuni_from_source() -> List[Dict[str, str]]:
    response = requests.get(COMUNI_SOURCE_URL, timeout=60)
    response.raise_for_status()

    with zipfile.ZipFile(io.BytesIO(response.content)) as zf:
        txt_name = next((name for name in zf.namelist() if name.lower().endswith(".txt")), None)
        if not txt_name:
            raise ValueError("File comuni non trovato nello zip")
        raw = zf.read(txt_name)

    content = _decode_bytes(raw)
    reader = csv.reader(io.StringIO(content), delimiter=";")
    headers = next(reader, [])
    header_map = {h.strip().lower(): idx for idx, h in enumerate(headers)}

    def idx(*names: str) -> int:
        for name in names:
            key = name.strip().lower()
            if key in header_map:
                return header_map[key]
        return -1

    idx_istat = idx("istat", "codice istat")
    idx_nome = idx("comune", "nome comune")
    idx_provincia = idx("provincia", "sigla provincia")
    idx_regione = idx("regione", "sigla regione")
    idx_cap = idx("cap")
    idx_catastale = idx("codfisco", "codice catastale (codice fisco)", "codice catastale")

    comuni = []
    for row in reader:
        if not row or idx_istat < 0:
            continue
        codice_istat = row[idx_istat].strip()
        if not codice_istat:
            continue
        nome = row[idx_nome].strip() if idx_nome >= 0 and idx_nome < len(row) else ""
        provincia = row[idx_provincia].strip() if idx_provincia >= 0 and idx_provincia < len(row) else None
        regione = row[idx_regione].strip() if idx_regione >= 0 and idx_regione < len(row) else None
        cap = row[idx_cap].strip() if idx_cap >= 0 and idx_cap < len(row) else None
        cod_cat = row[idx_catastale].strip() if idx_catastale >= 0 and idx_catastale < len(row) else None
        comuni.append({
            "codice_istat": codice_istat,
            "nome": nome,
            "nome_normalized": _normalize_nome(nome),
            "provincia_sigla": provincia.upper() if provincia else None,
            "regione": regione.upper() if regione else None,
            "cap": cap,
            "codice_catastale": cod_cat or None,
        })

    return comuni


def sync_comuni_italia(public_db: Session) -> Dict[str, int]:
    public_db.execute(text("ALTER TABLE public.anag_comuni_italia ADD COLUMN IF NOT EXISTS attivo BOOLEAN DEFAULT TRUE"))

    comuni_source = _load_comuni_from_source()
    existing = public_db.query(ComuneItalia).all()
    existing_by_istat = {c.codice_istat: c for c in existing}

    created = 0
    updated = 0
    reactivated = 0
    seen = set()

    for row in comuni_source:
        codice_istat = row["codice_istat"]
        seen.add(codice_istat)
        comune = existing_by_istat.get(codice_istat)
        if comune:
            if row["nome"]:
                comune.nome = row["nome"]
                comune.nome_normalized = row["nome_normalized"]
            if row["provincia_sigla"]:
                comune.provincia_sigla = row["provincia_sigla"]
            if row["cap"]:
                comune.cap = row["cap"]
            if row["codice_catastale"]:
                comune.codice_catastale = row["codice_catastale"]
            if row["regione"] and not comune.regione:
                comune.regione = row["regione"]
            if comune.attivo is False:
                comune.attivo = True
                reactivated += 1
            updated += 1
        else:
            public_db.add(ComuneItalia(
                nome=row["nome"] or codice_istat,
                nome_normalized=row["nome_normalized"] or _normalize_nome(codice_istat),
                codice_istat=codice_istat,
                codice_catastale=row["codice_catastale"],
                cap=row["cap"],
                provincia_sigla=row["provincia_sigla"] or "--",
                provincia_nome=None,
                regione=row["regione"],
                latitudine=None,
                longitudine=None,
                attivo=True,
            ))
            created += 1

    deactivated = 0
    for comune in existing:
        if comune.codice_istat not in seen and comune.attivo is not False:
            comune.attivo = False
            deactivated += 1

    public_db.commit()

    return {
        "source_rows": len(comuni_source),
        "created": created,
        "updated": updated,
        "reactivated": reactivated,
        "deactivated": deactivated,
        "total": len(existing_by_istat) + created,
    }
