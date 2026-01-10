"""
Servizio di registrazione dinamica dei ruoli per la piattaforma.

Permette ai moduli di registrare i propri ruoli senza modificare il core.
"""
import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.core.models import RuoloDisponibile, SoggettoRuolo

logger = logging.getLogger(__name__)


class RoleRegistry:
    """
    Registry per la gestione dinamica dei ruoli nella piattaforma.

    Ogni modulo può registrare i propri ruoli durante l'inizializzazione.
    Il core non conosce i ruoli specifici, ma fornisce solo il meccanismo.
    """

    @staticmethod
    def register_roles(
        db: Session,
        modulo_id: str,
        roles: List[Dict[str, Any]],
        overwrite: bool = False
    ) -> Dict[str, Any]:
        """
        Registra i ruoli di un modulo.

        Args:
            db: Database session
            modulo_id: ID del modulo che registra i ruoli
            roles: Lista di dizionari con i dati dei ruoli:
                {
                    "codice": "proprietario",
                    "nome_display": "Proprietario",
                    "descrizione": "Proprietario di immobili",
                    "tabella_specializzazione": "proprietari"
                }
            overwrite: Se True, aggiorna i ruoli esistenti

        Returns:
            Dizionario con statistiche della registrazione
        """
        created = 0
        updated = 0
        skipped = 0
        errors = []

        for role_data in roles:
            try:
                codice = role_data.get("codice")
                if not codice:
                    errors.append("Ruolo senza codice")
                    continue

                # Cerca ruolo esistente
                existing = db.query(RuoloDisponibile).filter(
                    RuoloDisponibile.codice == codice,
                    RuoloDisponibile.modulo_id == modulo_id
                ).first()

                if existing:
                    if overwrite:
                        # Aggiorna ruolo esistente
                        for key, value in role_data.items():
                            if key != "codice" and key != "modulo_id":
                                setattr(existing, key, value)
                        updated += 1
                        logger.info(f"Ruolo '{codice}' del modulo '{modulo_id}' aggiornato")
                    else:
                        skipped += 1
                        logger.debug(f"Ruolo '{codice}' del modulo '{modulo_id}' già esistente")
                else:
                    # Crea nuovo ruolo
                    role = RuoloDisponibile(
                        codice=codice,
                        modulo_id=modulo_id,
                        nome_display=role_data.get("nome_display", codice),
                        descrizione=role_data.get("descrizione"),
                        tabella_specializzazione=role_data.get("tabella_specializzazione"),
                        metadata_json=role_data.get("metadata_json"),
                        attivo=role_data.get("attivo", True)
                    )
                    db.add(role)
                    created += 1
                    logger.info(f"Ruolo '{codice}' del modulo '{modulo_id}' creato")

            except IntegrityError as e:
                db.rollback()
                error_msg = f"Errore integrità per ruolo '{role_data.get('codice')}': {str(e)}"
                errors.append(error_msg)
                logger.error(error_msg)
            except Exception as e:
                db.rollback()
                error_msg = f"Errore registrando ruolo '{role_data.get('codice')}': {str(e)}"
                errors.append(error_msg)
                logger.error(error_msg)

        # Commit finale
        try:
            db.commit()
        except Exception as e:
            db.rollback()
            errors.append(f"Errore nel commit finale: {str(e)}")
            logger.error(f"Errore nel commit dei ruoli: {str(e)}")

        result = {
            "modulo_id": modulo_id,
            "created": created,
            "updated": updated,
            "skipped": skipped,
            "total_roles": len(roles),
            "errors": errors
        }

        logger.info(
            f"Registrazione ruoli modulo '{modulo_id}': "
            f"{created} creati, {updated} aggiornati, {skipped} saltati, "
            f"{len(errors)} errori"
        )

        return result

    @staticmethod
    def unregister_module_roles(db: Session, modulo_id: str) -> int:
        """
        Rimuove tutti i ruoli di un modulo.

        ATTENZIONE: Rimuove anche tutte le assegnazioni di quei ruoli ai soggetti.

        Args:
            db: Database session
            modulo_id: ID del modulo

        Returns:
            Numero di ruoli rimossi
        """
        roles = db.query(RuoloDisponibile).filter(
            RuoloDisponibile.modulo_id == modulo_id
        ).all()

        count = len(roles)

        for role in roles:
            db.delete(role)

        db.commit()

        logger.info(f"Rimossi {count} ruoli del modulo '{modulo_id}'")

        return count

    @staticmethod
    def get_module_roles(db: Session, modulo_id: str) -> List[RuoloDisponibile]:
        """
        Ottiene tutti i ruoli registrati da un modulo.

        Args:
            db: Database session
            modulo_id: ID del modulo

        Returns:
            Lista di ruoli disponibili
        """
        return db.query(RuoloDisponibile).filter(
            RuoloDisponibile.modulo_id == modulo_id
        ).all()

    @staticmethod
    def get_all_roles(db: Session, attivo_only: bool = True) -> List[RuoloDisponibile]:
        """
        Ottiene tutti i ruoli disponibili nella piattaforma.

        Args:
            db: Database session
            attivo_only: Se True, restituisce solo i ruoli attivi

        Returns:
            Lista di tutti i ruoli disponibili
        """
        query = db.query(RuoloDisponibile)

        if attivo_only:
            query = query.filter(RuoloDisponibile.attivo == True)

        return query.all()

    @staticmethod
    def assign_role_to_subject(
        db: Session,
        soggetto_id: int,
        ruolo_codice: str,
        modulo_id: str,
        record_specializzazione_id: Optional[int] = None,
        note: Optional[str] = None
    ) -> SoggettoRuolo:
        """
        Assegna un ruolo a un soggetto.

        Args:
            db: Database session
            soggetto_id: ID del soggetto anagrafico
            ruolo_codice: Codice del ruolo
            modulo_id: ID del modulo che ha il ruolo
            record_specializzazione_id: ID del record nella tabella di specializzazione
            note: Note sull'assegnazione

        Returns:
            L'assegnazione creata

        Raises:
            ValueError: Se il ruolo non esiste
        """
        # Trova il ruolo
        ruolo = db.query(RuoloDisponibile).filter(
            RuoloDisponibile.codice == ruolo_codice,
            RuoloDisponibile.modulo_id == modulo_id
        ).first()

        if not ruolo:
            raise ValueError(
                f"Ruolo '{ruolo_codice}' del modulo '{modulo_id}' non trovato"
            )

        # Verifica se già assegnato
        existing = db.query(SoggettoRuolo).filter(
            SoggettoRuolo.soggetto_id == soggetto_id,
            SoggettoRuolo.ruolo_id == ruolo.id,
            SoggettoRuolo.record_specializzazione_id == record_specializzazione_id
        ).first()

        if existing:
            # Riattiva se era disattivato
            if not existing.attivo:
                existing.attivo = True
                db.commit()
            return existing

        # Crea nuova assegnazione
        assegnazione = SoggettoRuolo(
            soggetto_id=soggetto_id,
            ruolo_id=ruolo.id,
            record_specializzazione_id=record_specializzazione_id,
            note=note,
            attivo=True
        )

        db.add(assegnazione)
        db.commit()
        db.refresh(assegnazione)

        logger.info(
            f"Ruolo '{ruolo_codice}' assegnato al soggetto {soggetto_id}"
        )

        return assegnazione

    @staticmethod
    def remove_role_from_subject(
        db: Session,
        soggetto_id: int,
        ruolo_codice: str,
        modulo_id: str,
        soft_delete: bool = True
    ) -> bool:
        """
        Rimuove un ruolo da un soggetto.

        Args:
            db: Database session
            soggetto_id: ID del soggetto
            ruolo_codice: Codice del ruolo
            modulo_id: ID del modulo
            soft_delete: Se True, disattiva invece di eliminare

        Returns:
            True se rimosso, False se non trovato
        """
        # Trova il ruolo
        ruolo = db.query(RuoloDisponibile).filter(
            RuoloDisponibile.codice == ruolo_codice,
            RuoloDisponibile.modulo_id == modulo_id
        ).first()

        if not ruolo:
            return False

        # Trova l'assegnazione
        assegnazione = db.query(SoggettoRuolo).filter(
            SoggettoRuolo.soggetto_id == soggetto_id,
            SoggettoRuolo.ruolo_id == ruolo.id
        ).first()

        if not assegnazione:
            return False

        if soft_delete:
            assegnazione.attivo = False
        else:
            db.delete(assegnazione)

        db.commit()

        logger.info(
            f"Ruolo '{ruolo_codice}' rimosso dal soggetto {soggetto_id} "
            f"(soft_delete={soft_delete})"
        )

        return True
