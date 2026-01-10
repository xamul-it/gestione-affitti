"""
Scadenzario Service - Platform service for deadline management.

Provides centralized deadline (scadenze) management for all modules:
- Query documents/entities with upcoming deadlines
- Alert on expired items
- Statistics and reports
- Cross-module deadline tracking

Usage:
    from app.core.platform_services import ScadenzarioService
    from affitti_lungo.models.documenti import Documento

    scad_service = ScadenzarioService(db, model_class=Documento)

    # Get expired documents
    expired = scad_service.get_expired_documents(entity_type="SOGGETTO_ANAGRAFICO")

    # Get documents expiring soon (next 30 days)
    expiring = scad_service.get_expiring_soon(days=30)

    # Get statistics
    stats = scad_service.get_statistics()
"""
from typing import List, Dict, Any, Optional, Type
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from datetime import date, timedelta


class ScadenzarioService:
    """
    Platform service for deadline management with dependency injection.

    Tracks deadlines across all entity types with data_scadenza field.
    Uses dependency injection to accept any model class, making it truly platform-generic.

    The model_class must have a 'data_scadenza' field for deadline tracking.
    Optional fields for filtering: entity_type, entity_id, tipo, tipo_documento, nome_file.
    """

    def __init__(self, db: Session, model_class: Type):
        """
        Initialize scadenzario service with dependency injection.

        Args:
            db: Database session
            model_class: SQLAlchemy model class to query (must have data_scadenza field)
        """
        self.db = db
        self.model_class = model_class

    def get_expired_documents(
        self,
        entity_type: Optional[str] = None,
        entity_id: Optional[int] = None,
        tipo_documento: Optional[str] = None
    ) -> List[Any]:
        """
        Get all expired documents/entities (data_scadenza < today).

        Args:
            entity_type: Optional filter by entity type (e.g., "SOGGETTO_ANAGRAFICO")
            entity_id: Optional filter by specific entity ID
            tipo_documento: Optional filter by document type

        Returns:
            List of expired model instances
        """
        today = date.today()

        query = self.db.query(self.model_class).filter(
            self.model_class.data_scadenza.isnot(None),
            self.model_class.data_scadenza < today
        )

        # Only apply filters if the model has those attributes
        if entity_type and hasattr(self.model_class, 'entity_type'):
            query = query.filter(self.model_class.entity_type == entity_type)

        if entity_id and hasattr(self.model_class, 'entity_id'):
            query = query.filter(self.model_class.entity_id == entity_id)

        if tipo_documento and hasattr(self.model_class, 'tipo_documento'):
            query = query.filter(self.model_class.tipo_documento == tipo_documento)

        return query.order_by(self.model_class.data_scadenza).all()

    def get_expiring_soon(
        self,
        days: int = 30,
        entity_type: Optional[str] = None,
        entity_id: Optional[int] = None,
        tipo_documento: Optional[str] = None
    ) -> List[Any]:
        """
        Get documents/entities expiring within the next N days.

        Args:
            days: Number of days to look ahead (default: 30)
            entity_type: Optional filter by entity type
            entity_id: Optional filter by specific entity ID
            tipo_documento: Optional filter by document type

        Returns:
            List of model instances expiring soon
        """
        today = date.today()
        future_date = today + timedelta(days=days)

        query = self.db.query(self.model_class).filter(
            self.model_class.data_scadenza.isnot(None),
            self.model_class.data_scadenza >= today,
            self.model_class.data_scadenza <= future_date
        )

        if entity_type and hasattr(self.model_class, 'entity_type'):
            query = query.filter(self.model_class.entity_type == entity_type)

        if entity_id and hasattr(self.model_class, 'entity_id'):
            query = query.filter(self.model_class.entity_id == entity_id)

        if tipo_documento and hasattr(self.model_class, 'tipo_documento'):
            query = query.filter(self.model_class.tipo_documento == tipo_documento)

        return query.order_by(self.model_class.data_scadenza).all()

    def get_statistics(
        self,
        entity_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get deadline statistics.

        Args:
            entity_type: Optional filter by entity type

        Returns:
            Dict with counts of expired, expiring_soon, and upcoming items
        """
        today = date.today()
        thirty_days = today + timedelta(days=30)

        base_query = self.db.query(self.model_class).filter(
            self.model_class.data_scadenza.isnot(None)
        )

        if entity_type and hasattr(self.model_class, 'entity_type'):
            base_query = base_query.filter(self.model_class.entity_type == entity_type)

        # Count expired
        expired_count = base_query.filter(self.model_class.data_scadenza < today).count()

        # Count expiring in next 30 days
        expiring_soon_count = base_query.filter(
            self.model_class.data_scadenza >= today,
            self.model_class.data_scadenza <= thirty_days
        ).count()

        # Count future (beyond 30 days)
        upcoming_count = base_query.filter(
            self.model_class.data_scadenza > thirty_days
        ).count()

        # Total with deadlines
        total_with_deadlines = base_query.count()

        return {
            "expired": expired_count,
            "expiring_soon_30d": expiring_soon_count,
            "upcoming": upcoming_count,
            "total_with_deadlines": total_with_deadlines
        }

    def get_by_entity(
        self,
        entity_type: str,
        entity_id: int,
        include_expired: bool = True
    ) -> Dict[str, List[Any]]:
        """
        Get all documents with deadlines for a specific entity, grouped by status.

        Args:
            entity_type: Entity type (e.g., "SOGGETTO_ANAGRAFICO")
            entity_id: Entity ID
            include_expired: Whether to include expired documents

        Returns:
            Dict with keys: expired, expiring_soon, upcoming
        """
        result = {
            "expired": [],
            "expiring_soon": [],
            "upcoming": []
        }

        if include_expired:
            result["expired"] = self.get_expired_documents(
                entity_type=entity_type,
                entity_id=entity_id
            )

        result["expiring_soon"] = self.get_expiring_soon(
            days=30,
            entity_type=entity_type,
            entity_id=entity_id
        )

        # Get upcoming (beyond 30 days)
        today = date.today()
        thirty_days = today + timedelta(days=30)

        query = self.db.query(self.model_class).filter(
            self.model_class.data_scadenza.isnot(None),
            self.model_class.data_scadenza > thirty_days
        )

        if hasattr(self.model_class, 'entity_type'):
            query = query.filter(self.model_class.entity_type == entity_type)
        if hasattr(self.model_class, 'entity_id'):
            query = query.filter(self.model_class.entity_id == entity_id)

        result["upcoming"] = query.order_by(self.model_class.data_scadenza).all()

        return result

    def get_expired_by_type(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get expired items grouped by entity type.

        Useful for dashboard widgets showing expired items across all modules.

        Returns:
            Dict with entity_type as keys and list of expired items as values
        """
        today = date.today()

        query = self.db.query(self.model_class).filter(
            self.model_class.data_scadenza.isnot(None),
            self.model_class.data_scadenza < today
        )

        # Order by entity_type if available
        if hasattr(self.model_class, 'entity_type'):
            query = query.order_by(self.model_class.entity_type, self.model_class.data_scadenza)
        else:
            query = query.order_by(self.model_class.data_scadenza)

        expired = query.all()

        # Group by entity_type (if model has it)
        result = {}
        for item in expired:
            # Get entity_type if available, otherwise use "default"
            if hasattr(item, 'entity_type'):
                entity_type = item.entity_type.value if hasattr(item.entity_type, 'value') else str(item.entity_type)
            else:
                entity_type = "default"

            if entity_type not in result:
                result[entity_type] = []

            # Build result dict with available fields
            item_dict = {
                "id": item.id,
                "data_scadenza": item.data_scadenza.isoformat(),
                "days_overdue": (today - item.data_scadenza).days
            }

            # Add optional fields if available
            if hasattr(item, 'entity_id'):
                item_dict["entity_id"] = item.entity_id
            if hasattr(item, 'tipo_documento'):
                item_dict["tipo_documento"] = item.tipo_documento.value if hasattr(item.tipo_documento, 'value') else str(item.tipo_documento)
            if hasattr(item, 'nome_file'):
                item_dict["nome_file"] = item.nome_file

            result[entity_type].append(item_dict)

        return result

    def check_document_expired(self, item_id: int) -> bool:
        """
        Check if a specific item is expired.

        Args:
            item_id: Item ID

        Returns:
            True if expired, False otherwise
        """
        item = self.db.query(self.model_class).filter(self.model_class.id == item_id).first()

        if not item or not hasattr(item, 'data_scadenza') or not item.data_scadenza:
            return False

        return item.data_scadenza < date.today()

    def get_dashboard_widget_data(self) -> Dict[str, Any]:
        """
        Get data formatted for dashboard widget.

        Returns:
            Dict with counts and lists suitable for dashboard display
        """
        stats = self.get_statistics()
        expired_by_type = self.get_expired_by_type()

        # Get top 5 expiring soon
        expiring = self.get_expiring_soon(days=30)[:5]

        # Build top_expiring_soon with available fields
        top_expiring = []
        for item in expiring:
            item_dict = {
                "id": item.id,
                "data_scadenza": item.data_scadenza.isoformat(),
                "days_until_expiry": (item.data_scadenza - date.today()).days
            }

            # Add optional fields if available
            if hasattr(item, 'entity_type'):
                item_dict["entity_type"] = item.entity_type.value if hasattr(item.entity_type, 'value') else str(item.entity_type)
            if hasattr(item, 'entity_id'):
                item_dict["entity_id"] = item.entity_id
            if hasattr(item, 'tipo_documento'):
                item_dict["tipo_documento"] = item.tipo_documento.value if hasattr(item.tipo_documento, 'value') else str(item.tipo_documento)
            if hasattr(item, 'nome_file'):
                item_dict["nome_file"] = item.nome_file

            top_expiring.append(item_dict)

        return {
            "statistics": stats,
            "expired_by_type": expired_by_type,
            "top_expiring_soon": top_expiring
        }
