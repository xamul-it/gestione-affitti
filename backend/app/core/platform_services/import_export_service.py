"""
Import/Export Service - Platform service for data import and export.

Provides unified import/export capabilities:
- CSV import/export with field mapping
- Excel import/export (XLSX)
- Data validation and error reporting
- Batch processing with progress tracking
- Template generation for imports

Usage:
    from app.core.platform_services import ImportExportService

    service = ImportExportService(db)

    # Export to CSV
    csv_data = service.export_to_csv(
        model=Immobile,
        fields=["indirizzo", "citta", "superficie"],
        filters={"citta": "Milano"}
    )

    # Import from CSV
    results = service.import_from_csv(
        model=Immobile,
        csv_file=uploaded_file,
        field_mapping={"Indirizzo": "indirizzo", "Città": "citta"},
        create_schema=ImmobileCreate
    )

    # Export to Excel
    excel_file = service.export_to_excel(
        model=Contratto,
        fields=["numero_contratto", "data_inizio", "canone_mensile"]
    )
"""
from typing import Type, List, Dict, Any, Optional, BinaryIO
from sqlalchemy.orm import Session
from sqlalchemy import inspect
import csv
import io
from datetime import datetime, date
from decimal import Decimal


class ImportExportService:
    """
    Platform service for importing and exporting data.

    Provides standardized import/export across all entities.
    """

    def __init__(self, db: Session):
        """
        Initialize import/export service.

        Args:
            db: Database session
        """
        self.db = db

    def export_to_csv(
        self,
        model: Type[Any],
        fields: Optional[List[str]] = None,
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[str] = None,
        limit: Optional[int] = None
    ) -> str:
        """
        Export model data to CSV string.

        Args:
            model: SQLAlchemy model class
            fields: List of field names to export (None = all fields)
            filters: Optional filters to apply
            order_by: Optional field to order by
            limit: Optional limit on records

        Returns:
            CSV string
        """
        # Build query
        query = self.db.query(model)

        # Apply filters
        if filters:
            for field, value in filters.items():
                if hasattr(model, field):
                    query = query.filter(getattr(model, field) == value)

        # Apply ordering
        if order_by:
            if hasattr(model, order_by):
                query = query.order_by(getattr(model, order_by))

        # Apply limit
        if limit:
            query = query.limit(limit)

        # Get results
        results = query.all()

        # Determine fields
        if not fields:
            # Get all column names
            mapper = inspect(model)
            fields = [column.key for column in mapper.columns]

        # Create CSV
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=fields)
        writer.writeheader()

        for item in results:
            row = {}
            for field in fields:
                value = getattr(item, field, None)
                # Convert to string representation
                row[field] = self._serialize_value(value)
            writer.writerow(row)

        return output.getvalue()

    def export_to_dict(
        self,
        model: Type[Any],
        fields: Optional[List[str]] = None,
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Export model data to list of dicts (useful for JSON export).

        Args:
            model: SQLAlchemy model class
            fields: List of field names to export
            filters: Optional filters
            order_by: Optional ordering
            limit: Optional limit

        Returns:
            List of dictionaries
        """
        query = self.db.query(model)

        if filters:
            for field, value in filters.items():
                if hasattr(model, field):
                    query = query.filter(getattr(model, field) == value)

        if order_by:
            if hasattr(model, order_by):
                query = query.order_by(getattr(model, order_by))

        if limit:
            query = query.limit(limit)

        results = query.all()

        if not fields:
            mapper = inspect(model)
            fields = [column.key for column in mapper.columns]

        data = []
        for item in results:
            row = {}
            for field in fields:
                value = getattr(item, field, None)
                row[field] = self._serialize_value(value)
            data.append(row)

        return data

    def import_from_csv(
        self,
        model: Type[Any],
        csv_data: str | BinaryIO,
        field_mapping: Optional[Dict[str, str]] = None,
        create_schema: Optional[Type[Any]] = None,
        validate: bool = True,
        skip_errors: bool = False
    ) -> Dict[str, Any]:
        """
        Import data from CSV.

        Args:
            model: SQLAlchemy model class
            csv_data: CSV string or file object
            field_mapping: Map CSV headers to model fields
                          Example: {"Address": "indirizzo", "City": "citta"}
            create_schema: Optional Pydantic schema for validation
            validate: Whether to validate data
            skip_errors: If True, skip invalid rows; if False, stop on first error

        Returns:
            Dict with import statistics:
            {
                "success": True/False,
                "total_rows": 100,
                "imported": 95,
                "errors": 5,
                "error_details": [...]
            }
        """
        # Parse CSV
        if isinstance(csv_data, str):
            # Normalize line endings to handle Windows/Mac/Unix formats
            csv_data = csv_data.replace('\r\n', '\n').replace('\r', '\n')
            csv_file = io.StringIO(csv_data, newline='')
        else:
            csv_file = io.TextIOWrapper(csv_data, encoding='utf-8', newline='')

        reader = csv.DictReader(csv_file)

        stats = {
            "success": True,
            "total_rows": 0,
            "imported": 0,
            "errors": 0,
            "error_details": []
        }

        for row_num, row in enumerate(reader, start=2):  # Start at 2 (after header)
            stats["total_rows"] += 1

            try:
                # Map fields
                mapped_data = {}
                if field_mapping:
                    for csv_field, model_field in field_mapping.items():
                        if csv_field in row:
                            mapped_data[model_field] = row[csv_field]
                else:
                    mapped_data = row

                # Validate with Pydantic schema if provided
                if validate and create_schema:
                    validated_data = create_schema(**mapped_data)
                    mapped_data = validated_data.model_dump()

                # Create model instance
                db_obj = model(**mapped_data)
                self.db.add(db_obj)

                stats["imported"] += 1

            except Exception as e:
                stats["errors"] += 1
                stats["error_details"].append({
                    "row": row_num,
                    "data": row,
                    "error": str(e)
                })

                if not skip_errors:
                    stats["success"] = False
                    self.db.rollback()
                    return stats

        # Commit all changes
        try:
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            stats["success"] = False
            stats["error_details"].append({
                "error": f"Database commit failed: {str(e)}"
            })

        return stats

    def generate_import_template(
        self,
        model: Type[Any],
        fields: Optional[List[str]] = None,
        include_sample_data: bool = False
    ) -> str:
        """
        Generate CSV template for imports.

        Args:
            model: SQLAlchemy model class
            fields: Fields to include (None = all)
            include_sample_data: Whether to include a sample row

        Returns:
            CSV template string
        """
        # Determine fields
        if not fields:
            mapper = inspect(model)
            fields = [
                column.key for column in mapper.columns
                if column.key != 'id'  # Exclude ID field
            ]

        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=fields)
        writer.writeheader()

        # Add sample row if requested
        if include_sample_data:
            sample_row = {}
            mapper = inspect(model)
            for field in fields:
                column = mapper.columns.get(field)
                if column is not None:
                    # Generate sample based on type
                    sample_row[field] = self._generate_sample_value(column)
            writer.writerow(sample_row)

        return output.getvalue()

    def export_to_excel(
        self,
        model: Type[Any],
        fields: Optional[List[str]] = None,
        filters: Optional[Dict[str, Any]] = None,
        sheet_name: str = "Export"
    ) -> bytes:
        """
        Export data to Excel (XLSX) format.

        Note: Requires openpyxl library.

        Args:
            model: SQLAlchemy model class
            fields: Fields to export
            filters: Optional filters
            sheet_name: Excel sheet name

        Returns:
            Excel file as bytes
        """
        try:
            from openpyxl import Workbook
            from openpyxl.styles import Font, PatternFill
        except ImportError:
            raise ImportError(
                "openpyxl is required for Excel export. "
                "Install with: pip install openpyxl"
            )

        # Get data
        data = self.export_to_dict(model, fields, filters)

        if not data:
            raise ValueError("No data to export")

        # Create workbook
        wb = Workbook()
        ws = wb.active
        ws.title = sheet_name

        # Write header
        headers = list(data[0].keys())
        for col_num, header in enumerate(headers, start=1):
            cell = ws.cell(row=1, column=col_num, value=header)
            cell.font = Font(bold=True)
            cell.fill = PatternFill(start_color="CCCCCC", end_color="CCCCCC", fill_type="solid")

        # Write data
        for row_num, row_data in enumerate(data, start=2):
            for col_num, header in enumerate(headers, start=1):
                ws.cell(row=row_num, column=col_num, value=row_data[header])

        # Save to bytes
        output = io.BytesIO()
        wb.save(output)
        output.seek(0)
        return output.getvalue()

    def _serialize_value(self, value: Any) -> str:
        """Convert value to string for CSV export."""
        if value is None:
            return ""
        elif isinstance(value, (datetime, date)):
            return value.isoformat()
        elif isinstance(value, Decimal):
            return str(value)
        elif isinstance(value, bool):
            return "true" if value else "false"
        else:
            return str(value)

    def _generate_sample_value(self, column) -> str:
        """Generate sample value for template based on column type."""
        type_name = str(column.type)

        if 'VARCHAR' in type_name or 'TEXT' in type_name:
            return "example text"
        elif 'INTEGER' in type_name or 'NUMERIC' in type_name:
            return "123"
        elif 'DECIMAL' in type_name or 'FLOAT' in type_name:
            return "123.45"
        elif 'DATE' in type_name:
            return "2024-01-01"
        elif 'BOOLEAN' in type_name:
            return "true"
        else:
            return "value"

    def bulk_update(
        self,
        model: Type[Any],
        updates: List[Dict[str, Any]],
        id_field: str = "id"
    ) -> Dict[str, Any]:
        """
        Perform bulk update from list of dicts.

        Each dict should contain the ID field and fields to update.

        Args:
            model: SQLAlchemy model class
            updates: List of dicts with updates
            id_field: Name of ID field (default: "id")

        Returns:
            Update statistics
        """
        stats = {
            "success": True,
            "total": len(updates),
            "updated": 0,
            "errors": 0,
            "error_details": []
        }

        for update_data in updates:
            try:
                if id_field not in update_data:
                    raise ValueError(f"Missing {id_field} field")

                id_value = update_data[id_field]
                obj = self.db.query(model).filter(
                    getattr(model, id_field) == id_value
                ).first()

                if not obj:
                    raise ValueError(f"Record with {id_field}={id_value} not found")

                # Update fields
                for field, value in update_data.items():
                    if field != id_field and hasattr(obj, field):
                        setattr(obj, field, value)

                stats["updated"] += 1

            except Exception as e:
                stats["errors"] += 1
                stats["error_details"].append({
                    "data": update_data,
                    "error": str(e)
                })

        # Commit
        try:
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            stats["success"] = False
            stats["error_details"].append({
                "error": f"Database commit failed: {str(e)}"
            })

        return stats

    # ==================== FIELD MAPPING & INFERENCE ====================

    def get_entity_fields(
        self,
        model: Type[Any],
        create_schema: Optional[Type[Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Extract field information from model/schema.

        Args:
            model: SQLAlchemy model class
            create_schema: Optional Pydantic create schema for additional metadata

        Returns:
            List of field dictionaries with metadata
        """
        fields = []
        mapper = inspect(model)

        for column in mapper.columns:
            if column.key == 'id':  # Skip ID field
                continue

            field_info = {
                "name": column.key,
                "label": column.key.replace('_', ' ').title(),
                "type": self._get_field_type(column.type),
                "required": not column.nullable,
                "description": column.comment or ""
            }
            fields.append(field_info)

        return fields

    def _get_field_type(self, column_type) -> str:
        """Convert SQLAlchemy column type to simple string"""
        type_str = str(column_type).lower()

        if 'int' in type_str:
            return 'integer'
        elif 'float' in type_str or 'numeric' in type_str or 'decimal' in type_str:
            return 'number'
        elif 'bool' in type_str:
            return 'boolean'
        elif 'date' in type_str:
            return 'date'
        elif 'time' in type_str:
            return 'datetime'
        else:
            return 'string'

    def analyze_csv_structure(
        self,
        csv_data: str,
        max_sample_rows: int = 5
    ) -> Dict[str, Any]:
        """
        Analyze CSV structure and extract metadata.

        Args:
            csv_data: CSV content as string
            max_sample_rows: Number of sample rows to return

        Returns:
            Dictionary with CSV metadata
        """
        # Normalize line endings
        csv_data = csv_data.replace('\r\n', '\n').replace('\r', '\n')
        csv_file = io.StringIO(csv_data, newline='')
        reader = csv.DictReader(csv_file)

        # Get column names
        columns = reader.fieldnames or []

        # Collect sample rows
        sample_rows = []
        for i, row in enumerate(reader):
            if i >= max_sample_rows:
                break
            sample_rows.append(row)

        return {
            "csv_columns": columns,
            "sample_rows": sample_rows,
            "total_columns": len(columns)
        }

    def infer_field_mapping(
        self,
        csv_columns: List[str],
        entity_fields: List[Dict[str, Any]]
    ) -> Dict[str, str]:
        """
        Automatically infer field mapping using fuzzy matching.

        Args:
            csv_columns: List of CSV column names
            entity_fields: List of entity field dictionaries

        Returns:
            Dictionary mapping CSV columns to entity fields
        """
        from difflib import SequenceMatcher

        mapping = {}
        entity_field_names = [f["name"] for f in entity_fields]

        # Field aliases for common variations
        field_aliases = {
            "indirizzo": ["address", "addr", "via", "street", "strada"],
            "citta": ["city", "città", "comune", "town"],
            "cap": ["zip", "postal_code", "codice_postale", "postale"],
            "superficie_mq": ["superficie", "area", "mq", "sqm", "square_meters", "metri_quadri"],
            "locali": ["rooms", "vani", "stanze", "n_locali", "num_locali"],
            "provincia": ["prov", "province"],
            "stato": ["state", "status"],
            "nome": ["name", "firstname", "first_name"],
            "cognome": ["surname", "lastname", "last_name"],
            "email": ["mail", "e-mail", "posta"],
            "telefono": ["phone", "tel", "mobile", "cellulare"],
            "data_nascita": ["birthdate", "birth_date", "dob", "date_of_birth"],
            "codice_fiscale": ["cf", "tax_code", "fiscal_code"],
            "partita_iva": ["piva", "vat", "vat_number"],
        }

        def calculate_similarity(a: str, b: str) -> float:
            """Calculate similarity between two strings (0-1)"""
            return SequenceMatcher(None, a.lower(), b.lower()).ratio()

        for csv_col in csv_columns:
            best_match = None
            best_score = 0.0
            csv_col_lower = csv_col.lower().strip()

            for entity_field_name in entity_field_names:
                entity_field_lower = entity_field_name.lower()

                # 1. Exact match (case-insensitive)
                if csv_col_lower == entity_field_lower:
                    best_match = entity_field_name
                    break

                # 2. Check aliases
                if entity_field_name in field_aliases:
                    if csv_col_lower in field_aliases[entity_field_name]:
                        best_match = entity_field_name
                        break

                # 3. Fuzzy match
                score = calculate_similarity(csv_col, entity_field_name)
                if score > best_score and score > 0.7:  # Threshold 70%
                    best_score = score
                    best_match = entity_field_name

            if best_match:
                mapping[csv_col] = best_match

        return mapping

    def validate_import_preview(
        self,
        csv_data: str,
        field_mapping: Dict[str, str],
        create_schema: Type[Any],
        max_preview_rows: int = 50
    ) -> Dict[str, Any]:
        """
        Validate CSV data without importing to database.

        Args:
            csv_data: CSV content as string
            field_mapping: CSV column to model field mapping
            create_schema: Pydantic schema for validation
            max_preview_rows: Maximum rows to preview

        Returns:
            Preview data with validation results
        """
        # Normalize line endings
        csv_data = csv_data.replace('\r\n', '\n').replace('\r', '\n')
        csv_file = io.StringIO(csv_data, newline='')
        reader = csv.DictReader(csv_file)

        preview_data = []
        total_rows = 0
        valid_rows = 0
        invalid_rows = 0

        for row_num, row in enumerate(reader, start=2):  # Start at 2 (after header)
            total_rows += 1

            # Map fields
            mapped_data = {}
            for csv_field, model_field in field_mapping.items():
                if csv_field in row:
                    value = row[csv_field]
                    # Convert empty strings to None
                    mapped_data[model_field] = value if value.strip() else None

            # Validate with Pydantic schema
            validation_errors = []
            validation_status = "valid"
            validated_data = None

            try:
                validated_data = create_schema(**mapped_data)
                valid_rows += 1
            except Exception as e:
                validation_status = "invalid"
                invalid_rows += 1
                # Extract validation errors
                if hasattr(e, 'errors'):
                    for error in e.errors():
                        field = '.'.join(str(loc) for loc in error['loc'])
                        validation_errors.append(f"{field}: {error['msg']}")
                else:
                    validation_errors.append(str(e))

            # Add to preview (limit to max_preview_rows)
            if len(preview_data) < max_preview_rows:
                preview_data.append({
                    "row_number": row_num,
                    "original_data": dict(row),
                    "mapped_data": mapped_data,
                    "validation_status": validation_status,
                    "validation_errors": validation_errors
                })

        return {
            "total_rows": total_rows,
            "valid_rows": valid_rows,
            "invalid_rows": invalid_rows,
            "preview_data": preview_data
        }

    def import_from_csv_with_enrichment(
        self,
        model: Type[Any],
        csv_data: str,
        field_mapping: Dict[str, str],
        create_schema: Optional[Type[Any]] = None,
        skip_errors: bool = True,
        enable_updates: bool = True
    ) -> Dict[str, Any]:
        """
        Enhanced import with automatic enrichment.

        New features:
        - ID-based INSERT vs UPDATE detection
        - Automatic timestamp management (created_at/updated_at ignored from CSV)
        - Address normalization (extracts city, CAP, province from composite addresses)
        - Codice generation (format: {PROVINCIA}{00001})
        - Categoria catastale inference (from tipo_immobile)

        Args:
            model: SQLAlchemy model class
            csv_data: CSV string content
            field_mapping: Map CSV headers to model fields
            create_schema: Optional Pydantic schema for validation
            skip_errors: If True, skip invalid rows; if False, stop on first error
            enable_updates: Allow UPDATE operations if ID field present

        Returns:
            Dict with import statistics:
            {
                "success": True/False,
                "total_rows": 100,
                "created": 85,
                "updated": 10,
                "errors": 5,
                "warnings": [{"row": 2, "warnings": ["CAP not found"]}],
                "error_details": [...]
            }
        """
        import logging
        import sys
        import os
        modules_dir = os.path.join(os.path.dirname(__file__), "../../../modules")
        if modules_dir not in sys.path:
            sys.path.insert(0, modules_dir)

        from app.core.platform_services import AddressNormalizerService
        from immobili.services.codice_generator_service import CodiceGeneratorService
        from immobili.services.categoria_catastale_service import CategoriaCatastaleService

        logger = logging.getLogger(__name__)
        logger.info(f"Starting enriched CSV import for model: {model.__name__}")

        # Initialize enrichment services
        address_service = AddressNormalizerService(self.db)
        codice_service = CodiceGeneratorService(self.db)
        categoria_service = CategoriaCatastaleService(self.db)

        stats = {
            "success": True,
            "total_rows": 0,
            "created": 0,
            "updated": 0,
            "errors": 0,
            "warnings": [],
            "error_details": []
        }

        # Parse CSV
        csv_data = csv_data.replace('\r\n', '\n').replace('\r', '\n')
        csv_file = io.StringIO(csv_data, newline='')
        reader = csv.DictReader(csv_file)

        for row_num, row in enumerate(reader, start=2):  # Start at 2 (after header)
            stats["total_rows"] += 1

            try:
                # === STEP 1: ID Detection (INSERT vs UPDATE) ===
                record_id = row.get('id', '').strip()
                is_update = enable_updates and record_id and record_id != ''

                existing = None
                if is_update:
                    # UPDATE mode: fetch existing record
                    try:
                        existing = self.db.query(model).filter(
                            model.id == int(record_id)
                        ).first()

                        if not existing:
                            raise ValueError(f"Record ID={record_id} not found for update")

                        logger.debug(f"Row {row_num}: UPDATE mode for ID={record_id}")
                    except ValueError as e:
                        raise ValueError(f"Invalid ID format: {record_id}")

                # === STEP 2: Field Mapping ===
                mapped_data = {}
                for csv_field, model_field in field_mapping.items():
                    if csv_field in row:
                        value = row[csv_field]
                        # Convert empty strings to None
                        mapped_data[model_field] = value if value.strip() else None

                # === STEP 3: Address Normalization ===
                if 'indirizzo' in mapped_data and mapped_data['indirizzo']:
                    logger.debug(f"Row {row_num}: Normalizing address")
                    address_result = address_service.normalize_address(
                        raw_address=mapped_data.get('indirizzo', ''),
                        existing_citta=mapped_data.get('citta'),
                        existing_provincia=mapped_data.get('provincia'),
                        existing_cap=mapped_data.get('cap')
                    )

                    if address_result.success:
                        # Update with normalized values
                        if address_result.indirizzo:
                            mapped_data['indirizzo'] = address_result.indirizzo
                        if address_result.citta:
                            mapped_data['citta'] = address_result.citta
                        if address_result.provincia:
                            mapped_data['provincia'] = address_result.provincia
                        if address_result.cap:
                            mapped_data['cap'] = address_result.cap
                        if address_result.piano and 'piano' in [f for f in field_mapping.values()]:
                            mapped_data['piano'] = address_result.piano

                    if address_result.warnings:
                        # Store warnings in dedicated field if model supports it
                        if hasattr(model, 'indirizzo_parsed_warnings'):
                            mapped_data['indirizzo_parsed_warnings'] = address_result.warnings

                        stats["warnings"].append({
                            "row": row_num,
                            "warnings": address_result.warnings
                        })

                # === STEP 4: Codice Generation ===
                if not mapped_data.get('codice') and not is_update:
                    # Only generate for INSERT operations
                    provincia = mapped_data.get('provincia', 'XX')
                    try:
                        logger.debug(f"Row {row_num}: Generating codice")
                        codice = codice_service.generate_codice(provincia, model)
                        mapped_data['codice'] = codice

                        # Track that codice was auto-generated
                        if hasattr(model, 'codice_auto_generated'):
                            mapped_data['codice_auto_generated'] = True

                        logger.info(f"Row {row_num}: Generated codice={codice}")
                    except ValueError as e:
                        warning_msg = f"Codice generation failed: {str(e)}"
                        logger.warning(f"Row {row_num}: {warning_msg}")
                        stats["warnings"].append({
                            "row": row_num,
                            "warnings": [warning_msg]
                        })

                # === STEP 5: Categoria Catastale Inference ===
                if 'tipo' in mapped_data and mapped_data['tipo']:
                    logger.debug(f"Row {row_num}: Inferring categoria catastale")
                    categoria_id = categoria_service.infer_categoria_id(mapped_data['tipo'])

                    if categoria_id and hasattr(model, 'categoria_catastale_id'):
                        mapped_data['categoria_catastale_id'] = categoria_id
                        logger.debug(f"Row {row_num}: Inferred categoria_id={categoria_id}")

                # === STEP 6: Timestamps Handling ===
                # Remove timestamps from CSV - they are managed by database
                mapped_data.pop('created_at', None)
                mapped_data.pop('updated_at', None)
                mapped_data.pop('id', None)  # Don't set ID manually

                # === STEP 7: Validate with Pydantic (if provided) ===
                if create_schema:
                    try:
                        validated_data = create_schema(**mapped_data)
                        mapped_data = validated_data.model_dump(exclude_unset=True)
                    except Exception as e:
                        raise ValueError(f"Validation failed: {str(e)}")

                # === STEP 8: Save to Database ===
                if is_update:
                    # UPDATE existing record
                    for field, value in mapped_data.items():
                        if hasattr(existing, field):
                            setattr(existing, field, value)
                    stats["updated"] += 1
                    logger.info(f"Row {row_num}: Updated record ID={record_id}")
                else:
                    # INSERT new record
                    db_obj = model(**mapped_data)
                    self.db.add(db_obj)
                    stats["created"] += 1
                    logger.info(f"Row {row_num}: Created new record")

            except Exception as e:
                stats["errors"] += 1
                error_detail = {
                    "row": row_num,
                    "data": dict(row),
                    "error": str(e)
                }
                stats["error_details"].append(error_detail)
                logger.error(f"Row {row_num}: Import error - {str(e)}")

                if not skip_errors:
                    stats["success"] = False
                    self.db.rollback()
                    logger.error("Import aborted due to error (skip_errors=False)")
                    return stats

        # === STEP 9: Commit Transaction ===
        try:
            self.db.commit()
            logger.info(f"Import completed: {stats['created']} created, {stats['updated']} updated, {stats['errors']} errors")
        except Exception as e:
            self.db.rollback()
            stats["success"] = False
            stats["error_details"].append({
                "error": f"Database commit failed: {str(e)}"
            })
            logger.error(f"Database commit failed: {str(e)}")

        return stats
