"""
DocumentoService - typed documents with history and linked scadenze.

Spec: docs/superpowers/specs/2026-11-09-tipologie-documentali-moduli-design.md

- The document type (public.core_tipi_documento, synced from the module
  manifests) decides the rules: which entities it applies to, SOSTITUTIVO
  (one document in force per entity + type + sottotipo, the others kept as
  history) or CUMULATIVO, and the scadenza (none, manual, or N months from
  data_riferimento).
- A CORRENTE document with a scadenza owns an ATTIVA core Scadenza; it is
  completed when the document is superseded and cancelled when deleted.
- Files are never overwritten.

The service flushes but never commits: the caller owns the transaction.
"""
import io
import logging
from dataclasses import dataclass
from datetime import date, datetime
from typing import List, Optional

from dateutil.relativedelta import relativedelta
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.file_storage import file_storage
from app.core.platform.models import (
    Documento,
    DocumentoFile,
    EntityType,
    PrioritaScadenza,
    Scadenza,
    StatoScadenza,
    TipoDocumento,
)
from app.core.platform.models.documento import TipoDocumentoEnum
from app.core.platform.models.scadenza_log import ScadenzaLog
from app.core.platform.models.tipo_documento_override import TipoDocumentoOverride
from app.core.platform_services.document_type_sync import apply_override

logger = logging.getLogger(__name__)

CORRENTE = "CORRENTE"
SOSTITUITO = "SOSTITUITO"


@dataclass
class FileInput:
    content: bytes
    filename: str
    mime_type: Optional[str] = None


def _parse_date(value) -> Optional[date]:
    if isinstance(value, date):
        return value
    if isinstance(value, str) and value:
        try:
            return date.fromisoformat(value[:10])
        except ValueError:
            return None
    return None


def _legacy_enum(codice: str) -> TipoDocumentoEnum:
    """Value for the deprecated NOT NULL tipo_documento column."""
    try:
        return TipoDocumentoEnum(codice)
    except ValueError:
        return TipoDocumentoEnum.ALTRO


class DocumentoService:
    def __init__(self, db: Session, tenant_schema: str, user_id: Optional[int]):
        self.db = db
        self.tenant_schema = tenant_schema
        self._user_id = user_id

    # ------------------------------------------------------------------ types

    def _overrides(self) -> dict:
        if self.db.execute(text("SELECT to_regclass('core_tipi_documento_overrides')")).scalar() is None:
            return {}
        return {o.tipo_documento_id: o for o in self.db.query(TipoDocumentoOverride).all()}

    def tipi_per_entita(self, entity_type: EntityType) -> List[dict]:
        overrides = self._overrides()
        result = []
        for tipo in self.db.query(TipoDocumento).order_by(TipoDocumento.nome).all():
            if tipo.entity_types is not None and entity_type.value not in tipo.entity_types:
                continue
            merged = apply_override(tipo, overrides.get(tipo.id))
            if merged is not None and merged["attivo"]:
                result.append(merged)
        return result

    def _tipo(self, codice: str, entity_type: EntityType) -> TipoDocumento:
        tipo = self.db.query(TipoDocumento).filter(TipoDocumento.codice == codice).first()
        merged = apply_override(tipo, self._overrides().get(tipo.id)) if tipo else None
        if tipo is None or merged is None or not merged["attivo"]:
            raise ValueError(f"Tipologia documento '{codice}' inesistente o non attiva")
        if tipo.entity_types is not None and entity_type.value not in tipo.entity_types:
            raise ValueError(f"La tipologia '{tipo.nome}' non si applica a {entity_type.value}")
        return tipo

    # -------------------------------------------------------------- scadenze

    @staticmethod
    def _scadenza_calcolata(tipo: TipoDocumento, data_riferimento: date, data_scadenza: Optional[date]):
        regola = tipo.scadenza
        if not regola:
            return data_scadenza
        if regola.get("manuale"):
            if data_scadenza is None:
                raise ValueError(f"Scadenza obbligatoria per {tipo.nome}")
            return data_scadenza
        return data_riferimento + relativedelta(months=regola["mesi"])

    def scadenza_effettiva(self, documento: Documento) -> Optional[date]:
        scadenza = documento.data_scadenza
        decaduto = _parse_date((documento.dati or {}).get("decaduto_il"))
        if decaduto and (scadenza is None or decaduto < scadenza):
            return decaduto
        return scadenza

    def _user(self) -> int:
        if self._user_id is None:
            # System operations (migrations, sync): attribute to the first superuser.
            self._user_id = self.db.execute(text(
                "SELECT id FROM public.core_users ORDER BY is_superuser DESC, id LIMIT 1"
            )).scalar()
        return self._user_id

    def _sync_scadenza(self, documento: Documento, tipo: TipoDocumento) -> None:
        effettiva = self.scadenza_effettiva(documento)
        if documento.stato != CORRENTE or effettiva is None:
            return
        scadenza = self.db.get(Scadenza, documento.scadenza_id) if documento.scadenza_id else None
        if scadenza is not None and scadenza.stato in (StatoScadenza.ATTIVA, StatoScadenza.SCADUTA):
            if scadenza.data_scadenza != effettiva:
                scadenza.data_scadenza = effettiva
                scadenza.modificato_il = datetime.utcnow()
            return
        scadenza = Scadenza(
            modulo=tipo.modulo,
            entity_type=documento.entity_type.value,
            entity_id=documento.entity_id,
            titolo=f"{tipo.nome} in scadenza",
            descrizione=f"Documento n. {documento.id}",
            data_scadenza=effettiva,
            priorita=PrioritaScadenza.ALTA,
            stato=StatoScadenza.ATTIVA,
            creato_da=self._user(),
        )
        self.db.add(scadenza)
        self.db.flush()
        self.db.add(ScadenzaLog.log_creation(scadenza_id=scadenza.id, user_id=self._user(),
                                             note=f"Creata dal documento {documento.id}"))
        documento.scadenza_id = scadenza.id

    def _chiudi_scadenza(self, documento: Documento, stato: StatoScadenza, note: str) -> None:
        if not documento.scadenza_id:
            return
        scadenza = self.db.get(Scadenza, documento.scadenza_id)
        if scadenza is None or scadenza.stato not in (StatoScadenza.ATTIVA, StatoScadenza.SCADUTA):
            return
        scadenza.stato = stato
        scadenza.modificato_il = datetime.utcnow()
        if stato == StatoScadenza.COMPLETATA:
            scadenza.completato_da = self._user()
            scadenza.completato_il = datetime.utcnow()
            self.db.add(ScadenzaLog.log_completion(scadenza_id=scadenza.id, user_id=self._user(), note=note))
        else:
            self.db.add(ScadenzaLog.log_cancellation(scadenza_id=scadenza.id, user_id=self._user(), note=note))

    # --------------------------------------------------------------- history

    def _gruppo(self, documento: Documento):
        q = self.db.query(Documento).filter(
            Documento.entity_type == documento.entity_type,
            Documento.entity_id == documento.entity_id,
            Documento.tipo_documento_id == documento.tipo_documento_id,
        )
        if documento.sottotipo is None:
            return q.filter(Documento.sottotipo.is_(None))
        return q.filter(Documento.sottotipo == documento.sottotipo)

    def _applica_storico(self, documento: Documento, tipo: TipoDocumento) -> None:
        if tipo.regime != "SOSTITUTIVO":
            return
        corrente = self._gruppo(documento).filter(
            Documento.stato == CORRENTE, Documento.id != documento.id
        ).order_by(Documento.data_riferimento.desc(), Documento.id.desc()).first()
        if corrente is None:
            return
        if (corrente.data_riferimento or date.min) > documento.data_riferimento:
            documento.stato = SOSTITUITO
            documento.sostituito_da_id = corrente.id
            return
        corrente.stato = SOSTITUITO
        corrente.sostituito_da_id = documento.id
        self._chiudi_scadenza(corrente, StatoScadenza.COMPLETATA, f"Sostituito da documento {documento.id}")

    def storico(self, documento_id: int) -> List[Documento]:
        documento = self.db.get(Documento, documento_id)
        if documento is None:
            return []
        return self._gruppo(documento).order_by(
            Documento.data_riferimento.desc().nullslast(), Documento.id.desc()
        ).all()

    # ------------------------------------------------------------ operations

    def crea(
        self,
        *,
        entity_type: EntityType,
        entity_id: int,
        tipo_codice: str,
        files: List[FileInput],
        data_riferimento: Optional[date] = None,
        sottotipo: Optional[str] = None,
        data_scadenza: Optional[date] = None,
        dati: Optional[dict] = None,
        descrizione: Optional[str] = None,
        note: Optional[str] = None,
        metadata_parsato: Optional[dict] = None,
    ) -> Documento:
        tipo = self._tipo(tipo_codice, entity_type)
        if sottotipo is not None and tipo.sottotipi is not None and sottotipo not in tipo.sottotipi:
            raise ValueError(f"Sottotipo '{sottotipo}' non previsto per {tipo.nome}")
        if not files:
            raise ValueError("Nessun file caricato")
        data_riferimento = data_riferimento or date.today()
        if dati is not None:
            # Empty optional dates from forms mean "not set".
            dati = {k: v for k, v in dati.items() if not (k == "decaduto_il" and not v)}
        scadenza = self._scadenza_calcolata(tipo, data_riferimento, data_scadenza)

        saved: List[str] = []
        try:
            for f in files:
                saved.append(file_storage.save_file(
                    io.BytesIO(f.content), entity_type.value, entity_id, f.filename,
                    tenant_schema=self.tenant_schema,
                ))
            first = files[0]
            documento = Documento(
                entity_type=entity_type,
                entity_id=entity_id,
                tipo_documento_id=tipo.id,
                tipo_documento=_legacy_enum(tipo.codice),
                descrizione=descrizione,
                note=note,
                data_riferimento=data_riferimento,
                data_scadenza=scadenza,
                stato=CORRENTE,
                sottotipo=sottotipo,
                dati=dati,
                metadata_parsato=metadata_parsato,
                nome_file=first.filename,
                file_path=saved[0],
                mime_type=first.mime_type,
                dimensione=len(first.content),
            )
            for ordine, (f, path) in enumerate(zip(files, saved), start=1):
                documento.files.append(DocumentoFile(
                    file_path=path, nome_file=f.filename, mime_type=f.mime_type,
                    dimensione=len(f.content), ordine=ordine,
                    tipo_pagina="unico" if len(files) == 1 else f"pagina_{ordine}",
                ))
            self.db.add(documento)
            self.db.flush()
            self._applica_storico(documento, tipo)
            self._sync_scadenza(documento, tipo)
            self.db.flush()
            return documento
        except Exception:
            for path in saved:
                try:
                    file_storage.delete_file(path, tenant_schema=self.tenant_schema)
                except Exception:
                    logger.warning("File non rimosso dopo errore: %s", path)
            raise

    def elimina(self, documento_id: int) -> List[str]:
        """Delete the document (history and scadenza rules applied). Returns the file paths
        to remove with elimina_file() AFTER the caller commits: a rollback must not lose files."""
        documento = self.db.get(Documento, documento_id)
        if documento is None:
            raise ValueError(f"Documento {documento_id} non trovato")
        tipo = self.db.get(TipoDocumento, documento.tipo_documento_id) if documento.tipo_documento_id else None
        era_corrente = documento.stato == CORRENTE
        self._chiudi_scadenza(documento, StatoScadenza.CANCELLATA, f"Documento {documento.id} eliminato")
        paths = [f.file_path for f in documento.files] or ([documento.file_path] if documento.file_path else [])
        gruppo = self._gruppo(documento)
        self.db.delete(documento)
        self.db.flush()

        if tipo is not None and tipo.regime == "SOSTITUTIVO" and era_corrente:
            rimasti = gruppo.order_by(Documento.data_riferimento.desc().nullslast(), Documento.id.desc()).all()
            if rimasti:
                nuovo = rimasti[0]
                nuovo.stato = CORRENTE
                nuovo.sostituito_da_id = None
                for d in rimasti[1:]:
                    d.stato = SOSTITUITO
                    d.sostituito_da_id = nuovo.id
                self._sync_scadenza(nuovo, tipo)
                self.db.flush()

        return sorted(set(paths))

    def elimina_file(self, paths: List[str]) -> None:
        for path in paths:
            try:
                file_storage.delete_file(path, tenant_schema=self.tenant_schema)
            except Exception:
                logger.warning("File non rimosso: %s", path)

    # ------------------------------------------------------------ alignment

    def _tipo_by_codice(self, codice: str) -> Optional[TipoDocumento]:
        return self.db.query(TipoDocumento).filter(TipoDocumento.codice == codice).first()

    def allinea_storico(self, tipo_codice: str) -> int:
        """For a SOSTITUTIVO type, leave one CORRENTE document per group (the most recent).
        Fixes documents created before the history rules existed. Returns how many were superseded."""
        tipo = self._tipo_by_codice(tipo_codice)
        if tipo is None or tipo.regime != "SOSTITUTIVO":
            return 0
        correnti = self.db.query(Documento).filter(
            Documento.tipo_documento_id == tipo.id, Documento.stato == CORRENTE
        ).order_by(Documento.data_riferimento.desc().nullslast(), Documento.id.desc()).all()
        vincitori = {}
        changed = 0
        for d in correnti:
            key = (d.entity_type, d.entity_id, d.sottotipo)
            if key not in vincitori:
                vincitori[key] = d
                continue
            d.stato = SOSTITUITO
            d.sostituito_da_id = vincitori[key].id
            self._chiudi_scadenza(d, StatoScadenza.COMPLETATA, f"Sostituito da documento {vincitori[key].id}")
            changed += 1
        self.db.flush()
        return changed

    def allinea_scadenze(self, tipo_codice: str) -> int:
        """Create the missing open scadenza of every CORRENTE document of the type. Returns how many."""
        tipo = self._tipo_by_codice(tipo_codice)
        if tipo is None or not tipo.scadenza:
            return 0
        created = 0
        for d in self.db.query(Documento).filter(
            Documento.tipo_documento_id == tipo.id, Documento.stato == CORRENTE, Documento.scadenza_id.is_(None)
        ).all():
            self._sync_scadenza(d, tipo)
            created += int(d.scadenza_id is not None)
        self.db.flush()
        return created
