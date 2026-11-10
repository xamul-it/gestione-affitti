"""
Core role relations (fonte CORE) between a soggetto and an object of a module,
stored in the tenant table core_relazioni (spec
docs/superpowers/specs/2026-11-10-relazioni-ruoli-soggetti-design.md).

- The relation type (catalog public.core_ruoli_disponibili) decides the
  scadenza: none, manual, or computed ({"mesi": n, "da": "data_inizio"}).
- An open relation with a scadenza owns an ATTIVA core Scadenza on its
  object; closing it (data_fine) completes it, deleting it cancels it.
- Flushes, never commits: the caller owns the transaction.
"""
from datetime import date
from typing import Optional

from dateutil.relativedelta import relativedelta
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.models import RuoloDisponibile
from app.core.platform.models import Relazione, StatoScadenza
from app.core.platform_services.relazioni_moduli import verifica_modulo_attivo
from app.core.platform_services.scadenze_collegate import apri_o_aggiorna, chiudi, utente_sistema

# Tables holding the objects a relation can point to.
TABELLE_OGGETTI = {
    "CONDOMINIO": "immo_condomini",
    "IMMOBILE": "immo_unita_immobiliari",
    "SOGGETTO_ANAGRAFICO": "anag_soggetti_anagrafici",
}

_CAMPI_MODIFICABILI = ("sottotipo", "data_inizio", "data_fine", "data_scadenza", "note", "dati")


def e_corrente(data_fine: Optional[date], oggi: Optional[date] = None) -> bool:
    return data_fine is None or data_fine >= (oggi or date.today())


class RelazioneService:
    def __init__(self, db: Session, tenant_schema: str, user_id: Optional[int] = None):
        self.db = db
        self.tenant_schema = tenant_schema
        self._user_id = user_id

    def _user(self) -> int:
        if self._user_id is None:
            self._user_id = utente_sistema(self.db)
        return self._user_id

    # ------------------------------------------------------------ catalogo

    def tipo(self, codice: str) -> RuoloDisponibile:
        tipo = (self.db.query(RuoloDisponibile)
                .filter(RuoloDisponibile.codice == codice, RuoloDisponibile.attivo.is_(True))
                .order_by(RuoloDisponibile.id).first())
        if tipo is None:
            raise LookupError(f"Tipo di relazione '{codice}' inesistente o non attivo")
        return tipo

    def _get(self, relazione_id: int) -> Relazione:
        rel = self.db.get(Relazione, relazione_id)
        if rel is None:
            raise LookupError(f"Relazione {relazione_id} inesistente")
        return rel

    # ----------------------------------------------------------- controlli

    def _soggetto(self, soggetto_id: int):
        row = self.db.execute(text(
            "SELECT id, tipo_soggetto, nome, cognome, ragione_sociale FROM anag_soggetti_anagrafici WHERE id = :id"
        ), {"id": soggetto_id}).first()
        if row is None:
            raise LookupError(f"Anagrafica {soggetto_id} inesistente")
        return row

    @staticmethod
    def _nome(row) -> str:
        if row.ragione_sociale and not (row.nome or row.cognome):
            return row.ragione_sociale
        return " ".join(p for p in (row.cognome, row.nome) if p) or row.ragione_sociale or f"Anagrafica {row.id}"

    def _verifica_oggetto(self, tipo: RuoloDisponibile, entity_type: Optional[str], entity_id: Optional[int]) -> None:
        if tipo.entity_types:
            if entity_type not in tipo.entity_types or entity_id is None:
                raise ValueError(
                    f"Il tipo '{tipo.nome_display}' non si applica a {entity_type or 'nessun oggetto'}"
                )
        elif entity_type is not None:
            raise ValueError(f"Il tipo '{tipo.nome_display}' non si applica a un oggetto")
        if entity_type is None:
            return
        tabella = TABELLE_OGGETTI.get(entity_type)
        if tabella is None:
            raise ValueError(f"Oggetto {entity_type} non supportato")
        if self.db.execute(text(f"SELECT 1 FROM {tabella} WHERE id = :id"), {"id": entity_id}).first() is None:
            raise LookupError(f"{entity_type} {entity_id} inesistente")

    def _verifica_regole_tipo(self, tipo: RuoloDisponibile, soggetto, entity_id: Optional[int]) -> None:
        if tipo.codice == "ruolo_azienda":
            azienda = self._soggetto(entity_id)
            if azienda.id == soggetto.id:
                raise ValueError("Una persona non può avere un ruolo in se stessa")
            if soggetto.tipo_soggetto != "PERSONA_FISICA":
                raise ValueError("Il ruolo in azienda si assegna a una persona fisica")
            if azienda.tipo_soggetto != "PERSONA_GIURIDICA":
                raise ValueError("Il ruolo in azienda richiede una persona giuridica come azienda")

    def _aperte(self, tipo: RuoloDisponibile, entity_type, entity_id, escludi_id=None):
        q = self.db.query(Relazione).filter(
            Relazione.ruolo_id == tipo.id,
            (Relazione.data_fine.is_(None)) | (Relazione.data_fine >= date.today()),
        )
        q = q.filter(Relazione.entity_type == entity_type) if entity_type else q.filter(Relazione.entity_type.is_(None))
        q = q.filter(Relazione.entity_id == entity_id) if entity_id is not None else q.filter(Relazione.entity_id.is_(None))
        if escludi_id is not None:
            q = q.filter(Relazione.id != escludi_id)
        return q

    def _verifica_duplicati(self, tipo, rel: Relazione) -> None:
        if not e_corrente(rel.data_fine):
            return
        aperte = self._aperte(tipo, rel.entity_type, rel.entity_id, escludi_id=rel.id)
        if tipo.unico_per_oggetto and aperte.first() is not None:
            raise ValueError(
                f"C'è già un {tipo.nome_display.lower()} in carica: chiudi l'incarico precedente prima di registrarne uno nuovo"
            )
        stesso = aperte.filter(Relazione.soggetto_id == rel.soggetto_id)
        stesso = stesso.filter(Relazione.sottotipo == rel.sottotipo) if rel.sottotipo else stesso.filter(Relazione.sottotipo.is_(None))
        if rel.sottotipo:
            duplicato = stesso.first() is not None
        else:
            # Without a sottotipo, a free-text role (dati["ruolo"]) tells relations apart.
            testo = (rel.dati or {}).get("ruolo")
            duplicato = any((r.dati or {}).get("ruolo") == testo for r in stesso.all())
        if duplicato:
            raise ValueError(f"Esiste già una relazione '{tipo.nome_display}' aperta per questa anagrafica e questo oggetto")

    # ------------------------------------------------------------ scadenza

    @staticmethod
    def _scadenza(tipo: RuoloDisponibile, data_inizio: Optional[date], data_scadenza: Optional[date]) -> Optional[date]:
        regola = tipo.scadenza
        if not regola:
            return None
        if regola.get("manuale"):
            return data_scadenza
        if data_inizio is None:
            raise ValueError(f"La data di inizio è obbligatoria per {tipo.nome_display}: la scadenza si calcola da lì")
        return data_inizio + relativedelta(months=regola["mesi"])

    def _sync_scadenza(self, tipo: RuoloDisponibile, rel: Relazione) -> None:
        if not e_corrente(rel.data_fine):
            chiudi(self.db, rel.scadenza_id, StatoScadenza.COMPLETATA, f"Relazione {rel.id} chiusa", self._user())
            return
        if rel.data_scadenza is None:
            chiudi(self.db, rel.scadenza_id, StatoScadenza.CANCELLATA, f"Relazione {rel.id} senza scadenza", self._user())
            rel.scadenza_id = None
            return
        soggetto = self._soggetto(rel.soggetto_id)
        rel.scadenza_id = apri_o_aggiorna(
            self.db, scadenza_id=rel.scadenza_id, modulo=tipo.modulo_id,
            entity_type=rel.entity_type or "SOGGETTO_ANAGRAFICO",
            entity_id=rel.entity_id if rel.entity_type else rel.soggetto_id,
            titolo=f"{tipo.nome_display} — {self._nome(soggetto)}",
            descrizione=f"Relazione n. {rel.id}", data=rel.data_scadenza, user_id=self._user(),
            nota_creazione=f"Creata dalla relazione {rel.id}",
        )

    # ---------------------------------------------------------- operazioni

    def crea(self, soggetto_id: int, tipo_codice: str, *, entity_type: Optional[str] = None,
             entity_id: Optional[int] = None, sottotipo: Optional[str] = None,
             data_inizio: Optional[date] = None, data_fine: Optional[date] = None,
             data_scadenza: Optional[date] = None, note: Optional[str] = None,
             dati: Optional[dict] = None) -> Relazione:
        tipo = self.tipo(tipo_codice)
        verifica_modulo_attivo(self.db, self.tenant_schema, tipo)
        if tipo.fonte != "CORE":
            raise ValueError(f"Il tipo '{tipo.nome_display}' è gestito dal modulo {tipo.modulo_id}")
        soggetto = self._soggetto(soggetto_id)
        self._verifica_oggetto(tipo, entity_type, entity_id)
        self._verifica_regole_tipo(tipo, soggetto, entity_id)
        if data_inizio and data_fine and data_fine < data_inizio:
            raise ValueError("La data di fine precede quella di inizio")
        rel = Relazione(
            soggetto_id=soggetto_id, ruolo_id=tipo.id, entity_type=entity_type, entity_id=entity_id,
            sottotipo=sottotipo, data_inizio=data_inizio, data_fine=data_fine,
            data_scadenza=self._scadenza(tipo, data_inizio, data_scadenza), note=note, dati=dati,
            creato_da=self._user_id,
        )
        self._verifica_duplicati(tipo, rel)
        self.db.add(rel)
        self.db.flush()
        self._sync_scadenza(tipo, rel)
        self.db.flush()
        return rel

    def aggiorna(self, relazione_id: int, **campi) -> Relazione:
        rel = self._get(relazione_id)
        tipo = self.db.get(RuoloDisponibile, rel.ruolo_id)
        verifica_modulo_attivo(self.db, self.tenant_schema, tipo)
        sconosciuti = set(campi) - set(_CAMPI_MODIFICABILI)
        if sconosciuti:
            raise ValueError(f"Campi non modificabili: {', '.join(sorted(sconosciuti))}")
        for nome, valore in campi.items():
            setattr(rel, nome, valore)
        if rel.data_inizio and rel.data_fine and rel.data_fine < rel.data_inizio:
            raise ValueError("La data di fine precede quella di inizio")
        if tipo.scadenza and not tipo.scadenza.get("manuale") and ("data_inizio" in campi or "data_scadenza" in campi):
            rel.data_scadenza = self._scadenza(tipo, rel.data_inizio, None)
        elif not tipo.scadenza:
            rel.data_scadenza = None
        self._verifica_duplicati(tipo, rel)
        self._sync_scadenza(tipo, rel)
        self.db.flush()
        return rel

    def rinnova(self, relazione_id: int) -> Relazione:
        rel = self._get(relazione_id)
        tipo = self.db.get(RuoloDisponibile, rel.ruolo_id)
        verifica_modulo_attivo(self.db, self.tenant_schema, tipo)
        if not tipo.scadenza or tipo.scadenza.get("manuale") or rel.data_scadenza is None:
            raise ValueError(f"Il tipo '{tipo.nome_display}' non ha una scadenza da rinnovare")
        if not e_corrente(rel.data_fine):
            raise ValueError("La relazione è chiusa: non si può rinnovare")
        rel.data_scadenza = rel.data_scadenza + relativedelta(months=tipo.scadenza["mesi"])
        self._sync_scadenza(tipo, rel)
        self.db.flush()
        return rel

    def elimina_per_oggetto(self, entity_type: str, entity_id: int) -> int:
        """Remove every core relation pointing to an object being deleted; cancels their scadenze."""
        rels = self.db.query(Relazione).filter(
            Relazione.entity_type == entity_type, Relazione.entity_id == entity_id
        ).all()
        for rel in rels:
            self.elimina(rel.id)
        return len(rels)

    def conta_per_soggetto(self, soggetto_id: int) -> int:
        """Core relations of an anagrafica, as soggetto or as object (e.g. the company of a role)."""
        return self.db.query(Relazione).filter(
            (Relazione.soggetto_id == soggetto_id)
            | ((Relazione.entity_type == "SOGGETTO_ANAGRAFICO") & (Relazione.entity_id == soggetto_id))
        ).count()

    def elimina(self, relazione_id: int) -> None:
        rel = self._get(relazione_id)
        chiudi(self.db, rel.scadenza_id, StatoScadenza.CANCELLATA, f"Relazione {rel.id} eliminata", self._user())
        self.db.delete(rel)
        self.db.flush()
