"""
Search Service - Platform service for unified search and filtering.

Provides advanced search capabilities:
- Full-text search across multiple fields
- Complex filters with operators (eq, ne, gt, lt, like, in, between)
- Multi-field sorting
- Pagination with total count
- Cross-entity search (search across multiple models)

Usage:
    from app.core.platform_services import SearchService

    search = SearchService(db)

    # Simple search
    results = search.search(
        model=Immobile,
        search_term="Milano",
        search_fields=["indirizzo", "citta"],
        skip=0,
        limit=20
    )

    # Advanced filters
    results = search.search(
        model=Contratto,
        filters={
            "canone_mensile__gte": 500,
            "data_inizio__lte": "2024-01-01",
            "tipo__in": ["residenziale", "commerciale"]
        }
    )
"""
from typing import Type, List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, func, cast, String
from datetime import datetime, date
import re


class SearchService:
    """
    Unified search service for all entities.

    Provides consistent search and filtering across all models.
    """

    # Supported filter operators
    OPERATORS = {
        'eq': lambda field, value: field == value,
        'ne': lambda field, value: field != value,
        'gt': lambda field, value: field > value,
        'gte': lambda field, value: field >= value,
        'lt': lambda field, value: field < value,
        'lte': lambda field, value: field <= value,
        'like': lambda field, value: field.like(f"%{value}%"),
        'ilike': lambda field, value: field.ilike(f"%{value}%"),
        'in': lambda field, value: field.in_(value if isinstance(value, list) else [value]),
        'not_in': lambda field, value: ~field.in_(value if isinstance(value, list) else [value]),
        'is_null': lambda field, value: field.is_(None) if value else field.isnot(None),
        'between': lambda field, value: field.between(value[0], value[1]) if isinstance(value, (list, tuple)) and len(value) == 2 else True,
    }

    def __init__(self, db: Session):
        """
        Initialize search service.

        Args:
            db: Database session
        """
        self.db = db

    def search(
        self,
        model: Type[Any],
        search_term: Optional[str] = None,
        search_fields: Optional[List[str]] = None,
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[List[str]] = None,
        skip: int = 0,
        limit: int = 100,
        return_count: bool = False
    ) -> List[Any] | Tuple[List[Any], int]:
        """
        Perform unified search on a model.

        Args:
            model: SQLAlchemy model class
            search_term: Text to search for (applied to search_fields with OR)
            search_fields: List of fields to search in
            filters: Dictionary of filters with format:
                     - Simple: {"field": value}
                     - With operator: {"field__operator": value}
                     Examples:
                       {"canone_mensile__gte": 500}  # canone >= 500
                       {"citta__ilike": "milano"}     # citta ILIKE '%milano%'
                       {"tipo__in": ["A", "B"]}       # tipo IN ('A', 'B')
            order_by: List of fields to order by (prefix with '-' for DESC)
            skip: Number of records to skip
            limit: Maximum records to return
            return_count: If True, return (results, total_count) tuple

        Returns:
            List of model instances, or (list, count) tuple if return_count=True
        """
        query = self.db.query(model)

        # Apply full-text search
        if search_term and search_fields:
            search_conditions = []
            for field_name in search_fields:
                if hasattr(model, field_name):
                    field = getattr(model, field_name)
                    # Cast to string for non-string fields
                    search_conditions.append(
                        cast(field, String).ilike(f"%{search_term}%")
                    )

            if search_conditions:
                query = query.filter(or_(*search_conditions))

        # Apply filters
        if filters:
            filter_conditions = self._build_filter_conditions(model, filters)
            if filter_conditions:
                query = query.filter(and_(*filter_conditions))

        # Get total count before pagination
        total_count = query.count() if return_count else None

        # Apply ordering
        if order_by:
            for order_field in order_by:
                if order_field.startswith('-'):
                    # Descending
                    field_name = order_field[1:]
                    if hasattr(model, field_name):
                        query = query.order_by(getattr(model, field_name).desc())
                else:
                    # Ascending
                    if hasattr(model, order_field):
                        query = query.order_by(getattr(model, order_field))

        # Apply pagination
        query = query.offset(skip).limit(limit)

        # Execute query
        results = query.all()

        if return_count:
            return results, total_count
        return results

    def _build_filter_conditions(self, model: Type[Any], filters: Dict[str, Any]) -> List[Any]:
        """
        Build SQLAlchemy filter conditions from filter dictionary.

        Args:
            model: SQLAlchemy model
            filters: Filter dictionary

        Returns:
            List of SQLAlchemy filter conditions
        """
        conditions = []

        for filter_key, value in filters.items():
            # Parse field name and operator
            if '__' in filter_key:
                field_name, operator = filter_key.rsplit('__', 1)
            else:
                field_name = filter_key
                operator = 'eq'

            # Check if field exists
            if not hasattr(model, field_name):
                continue

            field = getattr(model, field_name)

            # Apply operator
            if operator in self.OPERATORS:
                condition = self.OPERATORS[operator](field, value)
                conditions.append(condition)

        return conditions

    def search_multiple(
        self,
        searches: List[Dict[str, Any]],
        skip: int = 0,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Search across multiple models and combine results.

        Useful for global search across entities like immobili, affittuari, etc.

        Args:
            searches: List of search configurations, each with:
                      - model: SQLAlchemy model
                      - search_term: Search term
                      - search_fields: Fields to search
                      - label: Label for results (e.g., "Immobili", "Affittuari")
            skip: Records to skip (applied globally)
            limit: Max records per model

        Returns:
            List of dicts with structure:
            [
                {
                    "type": "Immobili",
                    "results": [...]
                },
                ...
            ]
        """
        combined_results = []

        for search_config in searches:
            model = search_config.get('model')
            search_term = search_config.get('search_term')
            search_fields = search_config.get('search_fields')
            label = search_config.get('label', model.__name__)

            results = self.search(
                model=model,
                search_term=search_term,
                search_fields=search_fields,
                skip=skip,
                limit=limit
            )

            if results:
                combined_results.append({
                    "type": label,
                    "count": len(results),
                    "results": results
                })

        return combined_results

    def autocomplete(
        self,
        model: Type[Any],
        field: str,
        search_term: str,
        limit: int = 10
    ) -> List[str]:
        """
        Get autocomplete suggestions for a field.

        Args:
            model: SQLAlchemy model
            field: Field name to search
            search_term: Partial text to match
            limit: Max suggestions

        Returns:
            List of unique values matching search term
        """
        if not hasattr(model, field):
            return []

        field_obj = getattr(model, field)

        results = (
            self.db.query(field_obj)
            .filter(field_obj.ilike(f"%{search_term}%"))
            .distinct()
            .limit(limit)
            .all()
        )

        return [r[0] for r in results if r[0]]

    def aggregate(
        self,
        model: Type[Any],
        aggregations: Dict[str, Tuple[str, str]],
        filters: Optional[Dict[str, Any]] = None,
        group_by: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Perform aggregations on model data.

        Args:
            model: SQLAlchemy model
            aggregations: Dict of {result_name: (field, operation)}
                         Operations: sum, avg, count, min, max
                         Example: {"total_canone": ("canone_mensile", "sum")}
            filters: Optional filters to apply before aggregation
            group_by: Optional fields to group by

        Returns:
            List of dicts with aggregation results
        """
        # Build select columns
        select_cols = []

        # Add group by columns
        if group_by:
            for field_name in group_by:
                if hasattr(model, field_name):
                    select_cols.append(getattr(model, field_name))

        # Add aggregation columns
        agg_funcs = {
            'sum': func.sum,
            'avg': func.avg,
            'count': func.count,
            'min': func.min,
            'max': func.max,
        }

        agg_labels = {}
        for result_name, (field_name, operation) in aggregations.items():
            if hasattr(model, field_name) and operation in agg_funcs:
                field = getattr(model, field_name)
                agg_col = agg_funcs[operation](field).label(result_name)
                select_cols.append(agg_col)
                agg_labels[result_name] = True

        # Build query
        query = self.db.query(*select_cols)

        # Apply filters
        if filters:
            filter_conditions = self._build_filter_conditions(model, filters)
            if filter_conditions:
                query = query.filter(and_(*filter_conditions))

        # Apply group by
        if group_by:
            for field_name in group_by:
                if hasattr(model, field_name):
                    query = query.group_by(getattr(model, field_name))

        # Execute and format results
        results = query.all()

        formatted_results = []
        for row in results:
            result_dict = {}
            if group_by:
                for i, field_name in enumerate(group_by):
                    result_dict[field_name] = row[i]

            # Add aggregation values
            offset = len(group_by) if group_by else 0
            for i, result_name in enumerate(aggregations.keys()):
                result_dict[result_name] = row[offset + i]

            formatted_results.append(result_dict)

        return formatted_results
