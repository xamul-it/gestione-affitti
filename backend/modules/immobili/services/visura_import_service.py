"""
Import of unità immobiliari, anagrafiche and diritti from a parsed catasto
visura.

build_proposal() diffs a VisuraParsed against the tenant DB and returns an
editable proposal; nothing is written. The proposal is organised per "tipo
di bene" (only fabbricati today) so terreni can be added as a new section.

Matching rules (spec docs/superpowers/specs/2026-10-30-import-visure-catastali-design.md):
- soggetto: by codice fiscale; without CF, PERSONA_GIURIDICA by
  case-insensitive ragione_sociale
- unità: by città + foglio + particella + subalterno (leading zeros ignored)
- diritto: same unità + same soggetto's Proprietario + same tipo_diritto
"""
import io
import logging
import re
import unicodedata
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Dict, List, Optional, Tuple

from sqlalchemy import func
from sqlalchemy.orm import Session

from anagrafica_italiana.models import ComuneItalia, SoggettoAnagrafico, TipoSoggetto
from app.core.file_storage import file_storage
from app.core.platform.models import Documento, EntityType, TipoDocumento, TipoDocumentoEnum

from ..models import (
    CategoriaCatastale,
    DirittoImmobile,
    Proprietario,
    TipoImmobileCategoriaMap,
    UnitaImmobiliare,
)
from ..schemas.visura_import import (
    CampoModifica,
    DirittoProposta,
    SoggettoProposta,
    UnitaProposta,
    VisuraProposta,
)
from .codice_generator_service import CodiceGeneratorService
from .visura.models import FabbricatoParsed, IntestatoParsed, VisuraParsed
from .visura.text import strip_zeros

logger = logging.getLogger(__name__)

NOTE_BLOCK_RE = re.compile(r"--- Dati catastali \(da visura [^\n]*\) ---\n.*?--- fine dati catastali ---", re.S)

DEFAULT_TIPO_BY_CATEGORIA = {
    "A/10": "Ufficio",
    "C/1": "Negozio",
    "C/2": "Magazzino",
    "C/6": "Box",
    "C/7": "Posto auto",
}
APPARTAMENTO_CATEGORIE = {f"A/{n}" for n in (1, 2, 3, 4, 5, 6, 7, 8, 9, 11)}

SOGGETTO_CAMPI_COMPLETABILI = ("cognome", "nome", "data_nascita", "luogo_nascita")


def normalize_nome(value: Optional[str]) -> str:
    if not value:
        return ""
    value = unicodedata.normalize("NFKD", value)
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    value = re.sub(r"[^a-zA-Z0-9 ]", " ", value)
    return re.sub(r"\s+", " ", value).strip().lower()


def note_block(f: FabbricatoParsed, numero: str, data_visura) -> str:
    righe = [f"--- Dati catastali (da visura {numero} del {data_visura.strftime('%d/%m/%Y')}) ---"]
    classamento = [f"Categoria {f.categoria}"]
    if f.classe:
        classamento.append(f"Classe {f.classe}")
    if f.consistenza:
        classamento.append(f"Consistenza {f.consistenza}")
    righe.append(", ".join(classamento))
    zona = []
    if f.zona_censuaria:
        zona.append(f"Zona censuaria {f.zona_censuaria}")
    if f.micro_zona:
        zona.append(f"Micro zona {f.micro_zona}")
    if f.sezione_urbana:
        zona.append(f"Sezione urbana {f.sezione_urbana}")
    if zona:
        righe.append(", ".join(zona))
    righe.append("--- fine dati catastali ---")
    return "\n".join(righe)


def extract_note_block(note: Optional[str]) -> Optional[str]:
    if not note:
        return None
    m = NOTE_BLOCK_RE.search(note)
    return m.group(0) if m else None


def _block_body(block: Optional[str]) -> Optional[str]:
    """Block content without its header line, so a newer visura with the
    same data does not count as a change."""
    if not block:
        return None
    return block.split("\n", 1)[1] if "\n" in block else ""


def replace_note_block(note: Optional[str], block: str) -> str:
    if note and NOTE_BLOCK_RE.search(note):
        return NOTE_BLOCK_RE.sub(lambda _: block, note, count=1)
    if note and note.strip():
        return f"{note.rstrip()}\n\n{block}"
    return block


def _unit_key(citta: Optional[str], foglio, particella, sub) -> Tuple:
    return (normalize_nome(citta), strip_zeros(foglio), strip_zeros(particella), strip_zeros(sub))


def _resolve_comune(db: Session, f: FabbricatoParsed) -> Optional[ComuneItalia]:
    if f.codice_catastale_comune:
        c = db.query(ComuneItalia).filter(ComuneItalia.codice_catastale == f.codice_catastale_comune).first()
        if c:
            return c
    candidates = db.query(ComuneItalia).filter(ComuneItalia.nome_normalized == normalize_nome(f.comune)).all()
    if f.provincia:
        same_prov = [c for c in candidates if c.provincia_sigla == f.provincia]
        candidates = same_prov or candidates
    return candidates[0] if len(candidates) == 1 else None


def _default_tipo(db: Session, categoria: str, categoria_id: Optional[int]) -> Optional[str]:
    if categoria_id is not None:
        mapping = (
            db.query(TipoImmobileCategoriaMap)
            .filter(
                TipoImmobileCategoriaMap.categoria_catastale_id == categoria_id,
                TipoImmobileCategoriaMap.is_user_defined.is_(True),
            )
            .order_by(TipoImmobileCategoriaMap.confidence_score.desc())
            .first()
        )
        if mapping:
            return mapping.tipo_immobile.capitalize()
    if categoria in APPARTAMENTO_CATEGORIE:
        return "Appartamento"
    return DEFAULT_TIPO_BY_CATEGORIA.get(categoria)


def _soggetto_display(s: SoggettoAnagrafico) -> str:
    if s.ragione_sociale:
        return s.ragione_sociale
    return " ".join(p for p in (s.cognome, s.nome) if p) or f"Soggetto {s.id}"


def _intestato_key(i: IntestatoParsed) -> str:
    return i.codice_fiscale or f"nome:{normalize_nome(i.nominativo)}"


def _match_soggetto(db: Session, i: IntestatoParsed) -> Optional[SoggettoAnagrafico]:
    if i.codice_fiscale:
        return db.query(SoggettoAnagrafico).filter(SoggettoAnagrafico.codice_fiscale == i.codice_fiscale).first()
    return (
        db.query(SoggettoAnagrafico)
        .filter(
            SoggettoAnagrafico.tipo_soggetto == TipoSoggetto.PERSONA_GIURIDICA,
            func.lower(SoggettoAnagrafico.ragione_sociale) == i.nominativo.lower(),
        )
        .first()
    )


def _build_soggetti(db: Session, visura: VisuraParsed) -> Tuple[List[SoggettoProposta], Dict[str, SoggettoProposta]]:
    proposte: List[SoggettoProposta] = []
    by_key: Dict[str, SoggettoProposta] = {}
    for f in visura.fabbricati:
        for i in f.intestati:
            k = _intestato_key(i)
            if k in by_key:
                continue
            existing = _match_soggetto(db, i)
            campi: List[str] = []
            if existing is None:
                azione = "crea"
            else:
                if not i.persona_giuridica:
                    campi = [c for c in SOGGETTO_CAMPI_COMPLETABILI
                             if getattr(existing, c) in (None, "") and getattr(i, c) not in (None, "")]
                azione = "aggiorna" if campi else "invariato"
            p = SoggettoProposta(
                key=f"s{len(proposte)}",
                azione=azione,
                soggetto_id=existing.id if existing else None,
                persona_giuridica=i.persona_giuridica,
                nominativo=i.nominativo,
                cognome=i.cognome,
                nome=i.nome,
                ragione_sociale=i.ragione_sociale,
                codice_fiscale=i.codice_fiscale,
                data_nascita=i.data_nascita,
                luogo_nascita=i.luogo_nascita,
                campi_da_completare=campi,
            )
            proposte.append(p)
            by_key[k] = p
    return proposte, by_key


def _existing_units(db: Session) -> Dict[Tuple, UnitaImmobiliare]:
    units = db.query(UnitaImmobiliare).filter(
        UnitaImmobiliare.foglio.isnot(None), UnitaImmobiliare.particella.isnot(None)
    ).all()
    return {_unit_key(u.citta, u.foglio, u.particella, u.subalterno): u for u in units}


def _float(value) -> Optional[float]:
    return float(value) if value is not None else None


def _diritti_esistenti(db: Session, unita_id: int) -> List[Tuple[DirittoImmobile, int]]:
    """(diritto, soggetto_id) pairs for a unit."""
    return (
        db.query(DirittoImmobile, Proprietario.soggetto_id)
        .join(Proprietario, DirittoImmobile.proprietario_id == Proprietario.id)
        .filter(DirittoImmobile.unita_immobiliare_id == unita_id)
        .all()
    )


def build_proposal(db: Session, visura: VisuraParsed) -> VisuraProposta:
    soggetti, soggetti_by_key = _build_soggetti(db, visura)
    existing_units = _existing_units(db)
    categorie = {c.codice: c.id for c in db.query(CategoriaCatastale).all()}
    avvisi_globali = list(visura.warnings)
    if visura.terreni_count:
        avvisi_globali.append(f"{visura.terreni_count} terreni trovati nella visura: non importati")

    unita: List[UnitaProposta] = []
    for f in visura.fabbricati:
        avvisi: List[str] = []
        comune = _resolve_comune(db, f)
        if comune:
            citta, provincia = comune.nome, comune.provincia_sigla
            cap = re.split(r"[,\-\s]+", comune.cap.strip())[0] if comune.cap else None
        else:
            citta, provincia, cap = f.comune.title(), f.provincia, None
            avvisi.append(f"Comune {f.comune} ({f.codice_catastale_comune}) non trovato nell'anagrafica comuni")

        categoria_id = categorie.get(f.categoria)
        superficie = f.superficie_escluse_aree if f.superficie_escluse_aree is not None else f.superficie_totale
        locali = int(f.vani) if f.vani is not None and f.vani == f.vani.to_integral_value() else None
        block = note_block(f, visura.numero, visura.data)

        existing = existing_units.get(_unit_key(citta, f.foglio, f.particella, f.subalterno))
        if existing is None and comune is None:
            existing = existing_units.get(_unit_key(f.comune, f.foglio, f.particella, f.subalterno))

        nuovi = {
            "categoria_catastale_id": categoria_id,
            "rendita_catastale": _float(f.rendita),
            "superficie_mq": _float(superficie),
            "indirizzo": f.indirizzo,
            "piano": f.piano,
        }
        modifiche: List[CampoModifica] = []
        if existing is not None:
            for campo, nuovo in nuovi.items():
                attuale = getattr(existing, campo)
                if nuovo is not None and attuale != nuovo:
                    modifiche.append(CampoModifica(campo=campo, attuale=attuale, nuovo=nuovo))
            attuale_block = extract_note_block(existing.note)
            if _block_body(attuale_block) != _block_body(block):
                modifiche.append(CampoModifica(campo="note_catastali", attuale=attuale_block, nuovo=block))

        diritti: List[DirittoProposta] = []
        esistenti = _diritti_esistenti(db, existing.id) if existing is not None else []
        visti = set()
        for i in f.intestati:
            sp = soggetti_by_key[_intestato_key(i)]
            visti.add((sp.soggetto_id, i.tipo_diritto))
            azione = "crea"
            if sp.soggetto_id is not None:
                for d, soggetto_id in esistenti:
                    if soggetto_id == sp.soggetto_id and d.tipo_diritto == i.tipo_diritto:
                        azione = "invariato"
                        quota_sistema = _float(d.quota_percentuale)
                        quota_visura = _float(i.quota_percentuale)
                        if quota_visura is not None and quota_sistema != quota_visura:
                            avvisi.append(
                                f"Quota diversa per {i.nominativo}: sistema "
                                f"{quota_sistema if quota_sistema is not None else '-'}%, visura {quota_visura}%"
                            )
                        break
            diritti.append(DirittoProposta(
                soggetto_key=sp.key,
                nominativo=i.nominativo,
                tipo_diritto=i.tipo_diritto,
                quota_percentuale=_float(i.quota_percentuale),
                note=i.diritto_testo,
                azione=azione,
            ))
        for d, soggetto_id in esistenti:
            if (soggetto_id, d.tipo_diritto) not in visti:
                s = db.get(SoggettoAnagrafico, soggetto_id)
                nome = _soggetto_display(s) if s else f"soggetto {soggetto_id}"
                avvisi.append(f"Diritto {d.tipo_diritto.value} di {nome} presente a sistema ma non in visura")

        if existing is None:
            azione = "crea"
        elif modifiche or any(d.azione == "crea" for d in diritti):
            azione = "aggiorna"
        else:
            azione = "invariato"

        unita.append(UnitaProposta(
            key=f"u{len(unita)}",
            azione=azione,
            unita_id=existing.id if existing is not None else None,
            foglio=f.foglio,
            particella=f.particella,
            subalterno=f.subalterno,
            sezione_urbana=f.sezione_urbana,
            tipo=existing.tipo if existing is not None else _default_tipo(db, f.categoria, categoria_id),
            indirizzo=f.indirizzo or (existing.indirizzo if existing is not None else ""),
            citta=existing.citta if existing is not None else citta,
            provincia=provincia,
            cap=cap,
            piano=f.piano,
            superficie_mq=_float(superficie),
            locali=locali,
            rendita_catastale=_float(f.rendita),
            categoria_catastale_id=categoria_id,
            categoria=f.categoria,
            note_catastali=block,
            modifiche=modifiche,
            diritti=diritti,
            avvisi=avvisi,
        ))

    return VisuraProposta(
        formato=visura.formato,
        numero_visura=visura.numero,
        data_visura=visura.data,
        soggetti=soggetti,
        unita=unita,
        avvisi=avvisi_globali,
    )


# --- apply ------------------------------------------------------------------

UPDATABLE_FIELDS = {"categoria_catastale_id", "rendita_catastale", "superficie_mq", "indirizzo", "piano"}


class VisuraImportError(ValueError):
    """The confirmed proposal cannot be applied; message is shown to the user."""


@dataclass
class ImportResult:
    soggetti_creati: int = 0
    soggetti_aggiornati: int = 0
    unita_create: List[int] = field(default_factory=list)
    unita_aggiornate: List[int] = field(default_factory=list)
    diritti_creati: int = 0
    documenti_allegati: int = 0


def _label(u: UnitaProposta) -> str:
    return f"foglio {u.foglio} particella {u.particella} sub {u.subalterno or '-'}"


def _validate(db: Session, proposta: VisuraProposta) -> Dict[str, UnitaImmobiliare]:
    """Check everything before writing anything; returns existing units by key."""
    for s in proposta.soggetti:
        if s.azione != "crea" and (s.soggetto_id is None or db.get(SoggettoAnagrafico, s.soggetto_id) is None):
            raise VisuraImportError(f"Anagrafica {s.nominativo} non più presente: ricarica la visura")
    existing: Dict[str, UnitaImmobiliare] = {}
    for u in proposta.unita:
        if not u.selezionato:
            continue
        if u.azione == "crea":
            missing = [c for c in ("tipo", "indirizzo", "citta") if not (getattr(u, c) or "").strip()]
            if missing:
                raise VisuraImportError(f"{', '.join(missing).capitalize()} mancante per l'unità {_label(u)}")
            continue
        unit = db.get(UnitaImmobiliare, u.unita_id) if u.unita_id else None
        if unit is None or _unit_key("", unit.foglio, unit.particella, unit.subalterno)[1:] != \
                _unit_key("", u.foglio, u.particella, u.subalterno)[1:]:
            raise VisuraImportError(f"Unità {_label(u)} non più corrispondente: ricarica la visura")
        existing[u.key] = unit
    return existing


def _create_soggetto(s: SoggettoProposta) -> SoggettoAnagrafico:
    if s.persona_giuridica:
        piva = s.codice_fiscale if s.codice_fiscale and s.codice_fiscale.isdigit() else None
        return SoggettoAnagrafico(
            tipo_soggetto=TipoSoggetto.PERSONA_GIURIDICA,
            ragione_sociale=s.ragione_sociale or s.nominativo,
            codice_fiscale=s.codice_fiscale,
            partita_iva=piva,
        )
    return SoggettoAnagrafico(
        tipo_soggetto=TipoSoggetto.PERSONA_FISICA,
        cognome=s.cognome,
        nome=s.nome,
        codice_fiscale=s.codice_fiscale,
        data_nascita=s.data_nascita,
        luogo_nascita=s.luogo_nascita,
    )


def _proprietario_for(db: Session, soggetto_id: int, cache: Dict[int, Proprietario]) -> Proprietario:
    if soggetto_id not in cache:
        p = db.query(Proprietario).filter(Proprietario.soggetto_id == soggetto_id).order_by(Proprietario.id).first()
        if p is None:
            p = Proprietario(soggetto_id=soggetto_id)
            db.add(p)
            db.flush()
        cache[soggetto_id] = p
    return cache[soggetto_id]


def _has_visura(db: Session, unit_id: int, numero: str) -> bool:
    docs = db.query(Documento).filter(
        Documento.entity_type == EntityType.IMMOBILE, Documento.entity_id == unit_id
    ).all()
    return any((d.metadata_parsato or {}).get("numero_visura") == numero for d in docs)


def apply_proposal(
    db: Session,
    proposta: VisuraProposta,
    pdf_bytes: bytes,
    filename: str,
    tenant_schema: str,
) -> ImportResult:
    existing_units = _validate(db, proposta)
    result = ImportResult()
    saved_files: List[str] = []
    try:
        soggetto_ids: Dict[str, int] = {}
        for s in proposta.soggetti:
            if s.azione == "crea":
                if not s.selezionato:
                    continue
                nuovo = _create_soggetto(s)
                db.add(nuovo)
                db.flush()
                soggetto_ids[s.key] = nuovo.id
                result.soggetti_creati += 1
                continue
            soggetto_ids[s.key] = s.soggetto_id
            if s.azione == "aggiorna" and s.selezionato:
                target = db.get(SoggettoAnagrafico, s.soggetto_id)
                changed = False
                for campo in s.campi_da_completare:
                    if campo in SOGGETTO_CAMPI_COMPLETABILI and getattr(target, campo) in (None, ""):
                        setattr(target, campo, getattr(s, campo))
                        changed = True
                result.soggetti_aggiornati += int(changed)

        generator = CodiceGeneratorService(db)
        proprietari: Dict[int, Proprietario] = {}
        tipo_visura = db.query(TipoDocumento).filter(TipoDocumento.codice == "VISURA_CATASTALE").first()

        for u in proposta.unita:
            if not u.selezionato:
                continue
            if u.azione == "crea":
                unit = UnitaImmobiliare(
                    codice=generator.generate_codice(u.provincia, UnitaImmobiliare),
                    codice_auto_generated=True,
                    tipo=u.tipo.strip(),
                    indirizzo=u.indirizzo.strip(),
                    citta=u.citta.strip(),
                    cap=u.cap,
                    provincia=u.provincia,
                    piano=u.piano,
                    superficie_mq=u.superficie_mq,
                    locali=u.locali,
                    rendita_catastale=u.rendita_catastale,
                    foglio=u.foglio,
                    particella=u.particella,
                    subalterno=u.subalterno,
                    categoria_catastale_id=u.categoria_catastale_id,
                    note=u.note_catastali,
                )
                db.add(unit)
                db.flush()
                result.unita_create.append(unit.id)
            else:
                unit = existing_units[u.key]
                changed = False
                for m in u.modifiche:
                    if not m.selezionato:
                        continue
                    if m.campo in UPDATABLE_FIELDS:
                        setattr(unit, m.campo, m.nuovo)
                        changed = True
                    elif m.campo == "note_catastali":
                        unit.note = replace_note_block(unit.note, u.note_catastali)
                        changed = True
                if changed:
                    result.unita_aggiornate.append(unit.id)
            esistenti = {(sid, d.tipo_diritto) for d, sid in _diritti_esistenti(db, unit.id)}

            diritti_aggiunti = 0
            for d in u.diritti:
                soggetto_id = soggetto_ids.get(d.soggetto_key)
                if not d.selezionato or d.azione != "crea" or soggetto_id is None:
                    continue
                if (soggetto_id, d.tipo_diritto) in esistenti:
                    continue
                proprietario = _proprietario_for(db, soggetto_id, proprietari)
                db.add(DirittoImmobile(
                    unita_immobiliare_id=unit.id,
                    proprietario_id=proprietario.id,
                    tipo_diritto=d.tipo_diritto,
                    quota_percentuale=Decimal(str(d.quota_percentuale)) if d.quota_percentuale is not None else None,
                    note=d.note[:500],
                ))
                esistenti.add((soggetto_id, d.tipo_diritto))
                diritti_aggiunti += 1
            result.diritti_creati += diritti_aggiunti
            if diritti_aggiunti and u.azione != "crea" and unit.id not in result.unita_aggiornate:
                result.unita_aggiornate.append(unit.id)

            if _has_visura(db, unit.id, proposta.numero_visura):
                continue
            path = file_storage.save_file(
                io.BytesIO(pdf_bytes), EntityType.IMMOBILE.value, unit.id, filename, tenant_schema=tenant_schema
            )
            saved_files.append(path)
            db.add(Documento(
                entity_type=EntityType.IMMOBILE,
                entity_id=unit.id,
                tipo_documento=TipoDocumentoEnum.VISURA_CATASTALE,
                tipo_documento_id=tipo_visura.id if tipo_visura else None,
                nome_file=filename,
                file_path=path,
                mime_type="application/pdf",
                dimensione=len(pdf_bytes),
                descrizione=(
                    f"Visura catastale {proposta.formato.value.lower()} n. {proposta.numero_visura} "
                    f"del {proposta.data_visura.strftime('%d/%m/%Y')}"
                ),
                metadata_parsato={
                    "numero_visura": proposta.numero_visura,
                    "data_visura": proposta.data_visura.isoformat(),
                    "formato": proposta.formato.value,
                },
            ))
            db.flush()
            result.documenti_allegati += 1

        db.commit()
    except Exception:
        db.rollback()
        for path in saved_files:
            file_storage.delete_file(path, tenant_schema)
        logger.exception("Import visura %s fallito: rollback eseguito", proposta.numero_visura)
        raise
    return result
