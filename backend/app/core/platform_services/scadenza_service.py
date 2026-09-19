"""
ScadenzaService - Business logic for universal deadline/reminder system.

Handles CRUD operations, state transitions, audit logging, and notifications
for the Scadenza model.

Usage:
    from app.core.platform_services import ScadenzaService
    from app.core.database import get_db

    service = ScadenzaService(db)
    scadenza = service.create_scadenza(data, user_id)
    badge = service.get_badge_info(user_id)
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from datetime import date, datetime, timedelta

from app.core.platform.models import (
    Scadenza,
    ScadenzaDestinatario,
    ScadenzaLog,
    StatoScadenza,
    PrioritaScadenza
)
from app.core.schemas import (
    ScadenzaCreate,
    ScadenzaTODOCreate,
    ScadenzaUpdate,
    ScadenzaListFilters,
    ScadenzaBadgeResponse
)


class ScadenzaService:
    """
    Business logic service for Scadenza management.

    Provides:
        - CRUD operations with audit logging
        - State management (ATTIVA → COMPLETATA, POSTICIPATA, etc.)
        - Multi-recipient support
        - Filtering and search
        - Badge/statistics for UI
        - Automatic state updates (ATTIVA → SCADUTA)
    """

    def __init__(self, db: Session):
        """Initialize service with database session."""
        self.db = db

    # =============================================================================
    # CRUD OPERATIONS
    # =============================================================================

    def create_scadenza(
        self,
        data: ScadenzaCreate,
        user_id: int
    ) -> Scadenza:
        """
        Create a new scadenza with audit logging.

        Args:
            data: Scadenza creation data
            user_id: ID of user creating the scadenza

        Returns:
            Created Scadenza instance
        """
        # Create scadenza
        scadenza = Scadenza(
            modulo=data.modulo,
            entity_type=data.entity_type,
            entity_id=data.entity_id,
            titolo=data.titolo,
            descrizione=data.descrizione,
            data_scadenza=data.data_scadenza,
            priorita=data.priorita,
            stato=StatoScadenza.ATTIVA,
            creato_da=user_id
        )

        self.db.add(scadenza)
        self.db.flush()  # Get ID

        # Add recipients if specified
        if data.destinatari_ids:
            for dest_user_id in data.destinatari_ids:
                destinatario = ScadenzaDestinatario(
                    scadenza_id=scadenza.id,
                    user_id=dest_user_id
                )
                self.db.add(destinatario)

        # Log creation
        log = ScadenzaLog.log_creation(
            scadenza_id=scadenza.id,
            user_id=user_id,
            note=f"Scadenza creata: {scadenza.titolo}"
        )
        self.db.add(log)

        self.db.commit()
        self.db.refresh(scadenza)
        return scadenza

    def create_todo(
        self,
        data: ScadenzaTODOCreate,
        user_id: int
    ) -> Scadenza:
        """
        Create a standalone TODO (entity-less scadenza).

        Args:
            data: TODO creation data
            user_id: ID of user creating the TODO

        Returns:
            Created Scadenza instance
        """
        # Convert to ScadenzaCreate with NULL entity fields
        full_data = ScadenzaCreate(
            modulo=None,
            entity_type=None,
            entity_id=None,
            titolo=data.titolo,
            descrizione=data.descrizione,
            data_scadenza=data.data_scadenza,
            priorita=data.priorita,
            destinatari_ids=data.destinatari_ids or []
        )

        return self.create_scadenza(full_data, user_id)

    def get_scadenza(self, scadenza_id: int) -> Optional[Scadenza]:
        """
        Get scadenza by ID with relationships loaded.

        Args:
            scadenza_id: Scadenza ID

        Returns:
            Scadenza instance or None
        """
        return self.db.query(Scadenza).filter(
            Scadenza.id == scadenza_id
        ).first()

    def list_scadenze(
        self,
        filters: Optional[ScadenzaListFilters] = None,
        user_id: Optional[int] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Scadenza]:
        """
        List scadenze with filters.

        Args:
            filters: Filter criteria
            user_id: If provided, only return scadenze visible to this user
            skip: Pagination offset
            limit: Max results

        Returns:
            List of Scadenza instances
        """
        query = self.db.query(Scadenza)

        # Apply filters
        if filters:
            if filters.modulo:
                query = query.filter(Scadenza.modulo == filters.modulo)
            if filters.entity_type:
                query = query.filter(Scadenza.entity_type == filters.entity_type)
            if filters.entity_id:
                query = query.filter(Scadenza.entity_id == filters.entity_id)
            if filters.stato:
                query = query.filter(Scadenza.stato == filters.stato)
            if filters.priorita:
                query = query.filter(Scadenza.priorita == filters.priorita)
            if filters.creato_da:
                query = query.filter(Scadenza.creato_da == filters.creato_da)
            if filters.solo_todo:
                query = query.filter(
                    Scadenza.modulo.is_(None),
                    Scadenza.entity_type.is_(None),
                    Scadenza.entity_id.is_(None)
                )
            if filters.solo_scadute:
                query = query.filter(
                    Scadenza.stato == StatoScadenza.ATTIVA,
                    Scadenza.data_scadenza < date.today()
                )
            if filters.data_da:
                query = query.filter(Scadenza.data_scadenza >= filters.data_da)
            if filters.data_a:
                query = query.filter(Scadenza.data_scadenza <= filters.data_a)

        # Filter by user visibility (creator or recipient)
        if user_id:
            query = query.filter(
                or_(
                    Scadenza.creato_da == user_id,
                    Scadenza.destinatari.any(ScadenzaDestinatario.user_id == user_id)
                )
            )

        # Order by priority (ALTA first) and date
        query = query.order_by(
            Scadenza.priorita.desc(),
            Scadenza.data_scadenza.asc()
        )

        return query.offset(skip).limit(limit).all()

    def update_scadenza(
        self,
        scadenza_id: int,
        data: ScadenzaUpdate,
        user_id: int
    ) -> Optional[Scadenza]:
        """
        Update scadenza with audit logging.

        Args:
            scadenza_id: Scadenza ID to update
            data: Update data
            user_id: ID of user making the update

        Returns:
            Updated Scadenza instance or None
        """
        scadenza = self.get_scadenza(scadenza_id)
        if not scadenza:
            return None

        # Track changes for audit log
        changes = []

        # Update fields
        if data.titolo is not None:
            old_value = scadenza.titolo
            scadenza.titolo = data.titolo
            changes.append(("titolo", old_value, data.titolo))

        if data.descrizione is not None:
            old_value = scadenza.descrizione
            scadenza.descrizione = data.descrizione
            changes.append(("descrizione", old_value, data.descrizione))

        if data.data_scadenza is not None:
            old_value = scadenza.data_scadenza.isoformat()
            scadenza.data_scadenza = data.data_scadenza
            changes.append(("data_scadenza", old_value, data.data_scadenza.isoformat()))

        if data.priorita is not None:
            old_value = scadenza.priorita.value
            scadenza.priorita = data.priorita
            changes.append(("priorita", old_value, data.priorita.value))

        if data.stato is not None:
            old_value = scadenza.stato.value
            scadenza.stato = data.stato
            changes.append(("stato", old_value, data.stato.value))

        # Update recipients if provided
        if data.destinatari_ids is not None:
            # Remove existing recipients
            self.db.query(ScadenzaDestinatario).filter(
                ScadenzaDestinatario.scadenza_id == scadenza_id
            ).delete()

            # Add new recipients
            for dest_user_id in data.destinatari_ids:
                destinatario = ScadenzaDestinatario(
                    scadenza_id=scadenza_id,
                    user_id=dest_user_id
                )
                self.db.add(destinatario)

            changes.append(("destinatari", "modified", str(data.destinatari_ids)))

        scadenza.modificato_il = datetime.utcnow()

        # Log each change
        for campo, old_val, new_val in changes:
            log = ScadenzaLog.log_field_change(
                scadenza_id=scadenza_id,
                user_id=user_id,
                campo=campo,
                old_value=str(old_val) if old_val else None,
                new_value=str(new_val) if new_val else None
            )
            self.db.add(log)

        self.db.commit()
        self.db.refresh(scadenza)
        return scadenza

    def delete_scadenza(self, scadenza_id: int, user_id: int) -> bool:
        """
        Soft delete scadenza (set stato to CANCELLATA).

        Args:
            scadenza_id: Scadenza ID to delete
            user_id: ID of user deleting

        Returns:
            True if deleted, False if not found
        """
        scadenza = self.get_scadenza(scadenza_id)
        if not scadenza:
            return False

        old_stato = scadenza.stato.value
        scadenza.stato = StatoScadenza.CANCELLATA
        scadenza.modificato_il = datetime.utcnow()

        # Log cancellation
        log = ScadenzaLog.log_cancellation(
            scadenza_id=scadenza_id,
            user_id=user_id,
            note=f"Scadenza cancellata: {scadenza.titolo}"
        )
        self.db.add(log)

        self.db.commit()
        return True

    # =============================================================================
    # STATE MANAGEMENT
    # =============================================================================

    def completa_scadenza(
        self,
        scadenza_id: int,
        user_id: int,
        note: Optional[str] = None
    ) -> Optional[Scadenza]:
        """
        Mark scadenza as completed.

        Args:
            scadenza_id: Scadenza ID
            user_id: ID of user completing
            note: Optional completion notes

        Returns:
            Updated Scadenza or None
        """
        scadenza = self.get_scadenza(scadenza_id)
        if not scadenza:
            return None

        old_stato = scadenza.stato.value
        scadenza.stato = StatoScadenza.COMPLETATA
        scadenza.completato_da = user_id
        scadenza.completato_il = datetime.utcnow()
        scadenza.modificato_il = datetime.utcnow()

        # Log completion
        log = ScadenzaLog.log_completion(
            scadenza_id=scadenza_id,
            user_id=user_id,
            note=note or f"Scadenza completata: {scadenza.titolo}"
        )
        self.db.add(log)

        self.db.commit()
        self.db.refresh(scadenza)
        return scadenza

    def posticipa_scadenza(
        self,
        scadenza_id: int,
        nuova_data: date,
        user_id: int,
        note: Optional[str] = None
    ) -> Optional[Scadenza]:
        """
        Postpone scadenza to new date.

        Args:
            scadenza_id: Scadenza ID
            nuova_data: New due date
            user_id: ID of user postponing
            note: Reason for postponement

        Returns:
            Updated Scadenza or None
        """
        scadenza = self.get_scadenza(scadenza_id)
        if not scadenza:
            return None

        old_date = scadenza.data_scadenza.isoformat()
        scadenza.data_scadenza = nuova_data
        scadenza.stato = StatoScadenza.POSTICIPATA
        scadenza.modificato_il = datetime.utcnow()

        # Log postponement
        log = ScadenzaLog.log_postponement(
            scadenza_id=scadenza_id,
            user_id=user_id,
            old_date=old_date,
            new_date=nuova_data.isoformat(),
            note=note
        )
        self.db.add(log)

        self.db.commit()
        self.db.refresh(scadenza)
        return scadenza

    def riattiva_scadenza(
        self,
        scadenza_id: int,
        user_id: int
    ) -> Optional[Scadenza]:
        """
        Reactivate a completed or cancelled scadenza.

        Args:
            scadenza_id: Scadenza ID
            user_id: ID of user reactivating

        Returns:
            Updated Scadenza or None
        """
        scadenza = self.get_scadenza(scadenza_id)
        if not scadenza:
            return None

        old_stato = scadenza.stato.value
        scadenza.stato = StatoScadenza.ATTIVA
        scadenza.completato_da = None
        scadenza.completato_il = None
        scadenza.modificato_il = datetime.utcnow()

        # Log reactivation
        log = ScadenzaLog.log_state_change(
            scadenza_id=scadenza_id,
            user_id=user_id,
            old_state=old_stato,
            new_state=StatoScadenza.ATTIVA.value,
            note="Scadenza riattivata"
        )
        self.db.add(log)

        self.db.commit()
        self.db.refresh(scadenza)
        return scadenza

    def update_overdue_status(self):
        """
        Update stato for all ATTIVA scadenze that are past due.
        Sets stato to SCADUTA automatically, and resets the notificato flag
        on every recipient so the reminder job (which only notifies once per
        "event") sends a fresh "scaduta" notification distinct from the
        earlier "in avvicinamento" one.

        Should be called periodically (e.g., daily cron job).
        """
        today = date.today()

        overdue = self.db.query(Scadenza).filter(
            Scadenza.stato == StatoScadenza.ATTIVA,
            Scadenza.data_scadenza < today
        ).all()

        for scadenza in overdue:
            scadenza.stato = StatoScadenza.SCADUTA
            scadenza.modificato_il = datetime.utcnow()

            for destinatario in scadenza.destinatari:
                destinatario.notificato = False
                destinatario.notificato_il = None

            # Log automatic state change
            log = ScadenzaLog.log_state_change(
                scadenza_id=scadenza.id,
                user_id=None,  # System action
                old_state=StatoScadenza.ATTIVA.value,
                new_state=StatoScadenza.SCADUTA.value,
                note="Aggiornamento automatico: scadenza superata"
            )
            self.db.add(log)

        if overdue:
            self.db.commit()

    # =============================================================================
    # ENTITY-SPECIFIC QUERIES
    # =============================================================================

    def get_scadenze_by_entity(
        self,
        modulo: str,
        entity_type: str,
        entity_id: int,
        include_completed: bool = False
    ) -> List[Scadenza]:
        """
        Get all scadenze for a specific entity.

        Args:
            modulo: Module name
            entity_type: Entity type
            entity_id: Entity ID
            include_completed: Include completed/cancelled scadenze

        Returns:
            List of Scadenza instances
        """
        query = self.db.query(Scadenza).filter(
            Scadenza.modulo == modulo,
            Scadenza.entity_type == entity_type,
            Scadenza.entity_id == entity_id
        )

        if not include_completed:
            query = query.filter(
                Scadenza.stato.notin_([StatoScadenza.COMPLETATA, StatoScadenza.CANCELLATA])
            )

        return query.order_by(Scadenza.data_scadenza).all()

    def get_my_scadenze(
        self,
        user_id: int,
        include_completed: bool = False,
        only_overdue: bool = False
    ) -> List[Scadenza]:
        """
        Get all scadenze visible to a specific user (created by or recipient).

        Args:
            user_id: User ID
            include_completed: Include completed/cancelled scadenze
            only_overdue: Only return overdue scadenze

        Returns:
            List of Scadenza instances
        """
        query = self.db.query(Scadenza).filter(
            or_(
                Scadenza.creato_da == user_id,
                Scadenza.destinatari.any(ScadenzaDestinatario.user_id == user_id)
            )
        )

        if not include_completed:
            query = query.filter(
                Scadenza.stato.notin_([StatoScadenza.COMPLETATA, StatoScadenza.CANCELLATA])
            )

        if only_overdue:
            query = query.filter(
                Scadenza.stato.in_([StatoScadenza.ATTIVA, StatoScadenza.SCADUTA]),
                Scadenza.data_scadenza < date.today()
            )

        return query.order_by(
            Scadenza.priorita.desc(),
            Scadenza.data_scadenza.asc()
        ).all()

    # =============================================================================
    # STATISTICS & BADGE
    # =============================================================================

    def get_badge_info(self, user_id: Optional[int] = None) -> ScadenzaBadgeResponse:
        """
        Get badge info for UI display.

        Args:
            user_id: If provided, filter by user visibility

        Returns:
            ScadenzaBadgeResponse with counts and color
        """
        query = self.db.query(Scadenza).filter(
            Scadenza.stato.notin_([StatoScadenza.COMPLETATA, StatoScadenza.CANCELLATA])
        )

        if user_id:
            query = query.filter(
                or_(
                    Scadenza.creato_da == user_id,
                    Scadenza.destinatari.any(ScadenzaDestinatario.user_id == user_id)
                )
            )

        today = date.today()

        # Count active
        count_attive = query.filter(
            Scadenza.stato == StatoScadenza.ATTIVA,
            Scadenza.data_scadenza >= today
        ).count()

        # Count overdue
        count_scadute = query.filter(
            or_(
                Scadenza.stato == StatoScadenza.SCADUTA,
                and_(
                    Scadenza.stato == StatoScadenza.ATTIVA,
                    Scadenza.data_scadenza < today
                )
            )
        ).count()

        # Count high priority
        count_alta_priorita = query.filter(
            Scadenza.priorita == PrioritaScadenza.ALTA
        ).count()

        # Determine color
        if count_scadute > 0:
            color = "red"
            tooltip = f"{count_scadute} scadenze scadute"
        elif count_alta_priorita > 0:
            color = "yellow"
            tooltip = f"{count_alta_priorita} scadenze ad alta priorità"
        else:
            color = "green"
            tooltip = f"{count_attive} scadenze attive"

        return ScadenzaBadgeResponse(
            count_attive=count_attive,
            count_scadute=count_scadute,
            count_alta_priorita=count_alta_priorita,
            color=color,
            tooltip=tooltip
        )

    def get_statistics(self, user_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Get detailed statistics.

        Args:
            user_id: If provided, filter by user visibility

        Returns:
            Dict with various counts and breakdowns
        """
        query = self.db.query(Scadenza)

        if user_id:
            query = query.filter(
                or_(
                    Scadenza.creato_da == user_id,
                    Scadenza.destinatari.any(ScadenzaDestinatario.user_id == user_id)
                )
            )

        today = date.today()

        return {
            "total": query.count(),
            "attive": query.filter(Scadenza.stato == StatoScadenza.ATTIVA).count(),
            "scadute": query.filter(Scadenza.stato == StatoScadenza.SCADUTA).count(),
            "completate": query.filter(Scadenza.stato == StatoScadenza.COMPLETATA).count(),
            "posticipate": query.filter(Scadenza.stato == StatoScadenza.POSTICIPATA).count(),
            "cancellate": query.filter(Scadenza.stato == StatoScadenza.CANCELLATA).count(),
            "alta_priorita": query.filter(Scadenza.priorita == PrioritaScadenza.ALTA).count(),
            "media_priorita": query.filter(Scadenza.priorita == PrioritaScadenza.MEDIA).count(),
            "bassa_priorita": query.filter(Scadenza.priorita == PrioritaScadenza.BASSA).count(),
            "todo": query.filter(
                Scadenza.modulo.is_(None),
                Scadenza.entity_type.is_(None),
                Scadenza.entity_id.is_(None)
            ).count(),
        }

    # =============================================================================
    # AUDIT LOG
    # =============================================================================

    def get_logs(self, scadenza_id: int) -> List[ScadenzaLog]:
        """
        Get audit log for a scadenza.

        Args:
            scadenza_id: Scadenza ID

        Returns:
            List of ScadenzaLog instances ordered by timestamp desc
        """
        return self.db.query(ScadenzaLog).filter(
            ScadenzaLog.scadenza_id == scadenza_id
        ).order_by(ScadenzaLog.timestamp.desc()).all()
