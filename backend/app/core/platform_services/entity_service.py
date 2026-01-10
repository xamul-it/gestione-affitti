"""
Entity Service - Platform service for standardized CRUD operations.

This service provides a base class for all entity operations, ensuring:
- Consistent API across all modules
- Proper error handling and validation
- Database session management
- Pagination and filtering
- Module isolation (modules access data through this service, not direct DB)

Usage:
    class ImmobileService(EntityService[Immobile, ImmobileCreate, ImmobileUpdate]):
        pass

    # In module code:
    service = ImmobileService(db, Immobile)
    immobile = service.create(data)
    all_immobili = service.get_all(skip=0, limit=10)
"""
from typing import Generic, TypeVar, Type, Optional, List, Any, Dict
from sqlalchemy.orm import Session
from sqlalchemy import inspect
from pydantic import BaseModel
from fastapi import HTTPException, status


# Generic types for entity model, create schema, and update schema
ModelType = TypeVar("ModelType")
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class EntityService(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """
    Base service class for entity CRUD operations.

    This provides standardized operations that modules should use
    instead of direct database access.
    """

    def __init__(self, db: Session, model: Type[ModelType]):
        """
        Initialize the entity service.

        Args:
            db: Database session
            model: SQLAlchemy model class
        """
        self.db = db
        self.model = model

    def get(self, id: int) -> Optional[ModelType]:
        """
        Get entity by ID.

        Args:
            id: Entity ID

        Returns:
            Entity instance or None if not found
        """
        return self.db.query(self.model).filter(self.model.id == id).first()

    def get_or_404(self, id: int) -> ModelType:
        """
        Get entity by ID or raise 404.

        Args:
            id: Entity ID

        Returns:
            Entity instance

        Raises:
            HTTPException: 404 if not found
        """
        entity = self.get(id)
        if not entity:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"{self.model.__name__} with id {id} not found"
            )
        return entity

    def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[str] = None
    ) -> List[ModelType]:
        """
        Get all entities with pagination and optional filtering.

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            filters: Dictionary of field->value filters
            order_by: Field name to order by (prefix with '-' for DESC)

        Returns:
            List of entities
        """
        query = self.db.query(self.model)

        # Apply filters
        if filters:
            for field, value in filters.items():
                if hasattr(self.model, field):
                    query = query.filter(getattr(self.model, field) == value)

        # Apply ordering
        if order_by:
            if order_by.startswith('-'):
                # Descending order
                field = order_by[1:]
                if hasattr(self.model, field):
                    query = query.order_by(getattr(self.model, field).desc())
            else:
                # Ascending order
                if hasattr(self.model, order_by):
                    query = query.order_by(getattr(self.model, order_by))

        return query.offset(skip).limit(limit).all()

    def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """
        Count entities matching filters.

        Args:
            filters: Dictionary of field->value filters

        Returns:
            Count of matching entities
        """
        query = self.db.query(self.model)

        if filters:
            for field, value in filters.items():
                if hasattr(self.model, field):
                    query = query.filter(getattr(self.model, field) == value)

        return query.count()

    def create(self, obj_in: CreateSchemaType) -> ModelType:
        """
        Create new entity.

        Args:
            obj_in: Pydantic schema with creation data

        Returns:
            Created entity
        """
        # Convert Pydantic model to dict
        obj_data = obj_in.model_dump()

        # Create model instance
        db_obj = self.model(**obj_data)

        # Add to session and commit
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)

        return db_obj

    def update(
        self,
        id: int,
        obj_in: UpdateSchemaType,
        partial: bool = True
    ) -> ModelType:
        """
        Update existing entity.

        Args:
            id: Entity ID
            obj_in: Pydantic schema with update data
            partial: If True, only update provided fields (PATCH behavior)
                    If False, update all fields (PUT behavior)

        Returns:
            Updated entity

        Raises:
            HTTPException: 404 if not found
        """
        db_obj = self.get_or_404(id)

        # Get update data, excluding unset fields if partial update
        if partial:
            update_data = obj_in.model_dump(exclude_unset=True)
        else:
            update_data = obj_in.model_dump()

        # Update fields
        for field, value in update_data.items():
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)

        self.db.commit()
        self.db.refresh(db_obj)

        return db_obj

    def delete(self, id: int) -> bool:
        """
        Delete entity by ID.

        Args:
            id: Entity ID

        Returns:
            True if deleted, False if not found
        """
        db_obj = self.get(id)
        if not db_obj:
            return False

        self.db.delete(db_obj)
        self.db.commit()

        return True

    def delete_or_404(self, id: int) -> ModelType:
        """
        Delete entity by ID or raise 404.

        Args:
            id: Entity ID

        Returns:
            Deleted entity

        Raises:
            HTTPException: 404 if not found
        """
        db_obj = self.get_or_404(id)
        self.db.delete(db_obj)
        self.db.commit()
        return db_obj

    def exists(self, id: int) -> bool:
        """
        Check if entity exists.

        Args:
            id: Entity ID

        Returns:
            True if exists, False otherwise
        """
        return self.db.query(self.model).filter(self.model.id == id).count() > 0

    def find_by(self, **kwargs) -> Optional[ModelType]:
        """
        Find first entity matching given criteria.

        Args:
            **kwargs: Field->value pairs to match

        Returns:
            First matching entity or None
        """
        query = self.db.query(self.model)
        for field, value in kwargs.items():
            if hasattr(self.model, field):
                query = query.filter(getattr(self.model, field) == value)
        return query.first()

    def find_all_by(self, **kwargs) -> List[ModelType]:
        """
        Find all entities matching given criteria.

        Args:
            **kwargs: Field->value pairs to match

        Returns:
            List of matching entities
        """
        query = self.db.query(self.model)
        for field, value in kwargs.items():
            if hasattr(self.model, field):
                query = query.filter(getattr(self.model, field) == value)
        return query.all()
