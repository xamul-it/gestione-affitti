"""
Platform-level import/export API endpoints.

Provides generic import/export functionality that works with any entity.
"""
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from pydantic import BaseModel

from app.core.database import get_db
from app.core.platform_services.import_export_service import ImportExportService

router = APIRouter(prefix="/import-export", tags=["Import/Export"])


class ImportConfig(BaseModel):
    """Configuration for import operation."""
    module_name: str
    entity_name: str
    field_mapping: Optional[dict[str, str]] = None
    skip_errors: bool = True
    validate: bool = True


class ImportResult(BaseModel):
    """Result of import operation."""
    success: bool
    total_rows: int
    imported: int
    errors: int
    error_details: List[dict]


class ExportConfig(BaseModel):
    """Configuration for export operation."""
    module_name: str
    entity_name: str
    fields: Optional[List[str]] = None
    filters: Optional[dict] = None
    format: str = "csv"  # csv, excel, json


@router.post("/import", response_model=ImportResult)
async def import_data(
    file: UploadFile = File(...),
    module_name: str = Query(..., description="Module technical name (e.g., 'affitti_lungo')"),
    entity_name: str = Query(..., description="Entity name (e.g., 'UnitaImmobiliare')"),
    skip_errors: bool = Query(True, description="Skip invalid rows"),
    enable_enrichment: bool = Query(True, description="Enable automatic enrichment (address parsing, CAP lookup, etc.)"),
    enable_updates: bool = Query(True, description="Enable UPDATE mode for records with ID"),
    db: Session = Depends(get_db)
):
    """
    Generic import endpoint for any entity.

    Automatically handles:
    - CSV parsing
    - Data validation
    - Error reporting
    - Batch creation
    - **NEW: Automatic enrichment** (address parsing, CAP lookup, categoria catastale, codice generation)

    **Enrichment Features** (when enable_enrichment=True):
    - ID-based INSERT/UPDATE detection
    - Automatic timestamp management
    - Address normalization and CAP lookup
    - Codice generation (format: {PROVINCIA}{00001})
    - Categoria catastale inference from tipo_immobile

    Example:
        POST /api/v1/import-export/import?module_name=affitti_lungo&entity_name=UnitaImmobiliare&enable_enrichment=true

        CSV file with columns matching entity fields.
    """
    # Read CSV content with encoding detection
    content = await file.read()

    # Try multiple encodings
    for encoding in ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252', 'iso-8859-1']:
        try:
            csv_data = content.decode(encoding)
            break
        except UnicodeDecodeError:
            continue
    else:
        # If all encodings fail, use utf-8 with error handling
        csv_data = content.decode('utf-8', errors='replace')

    # Get model and schema from module registry
    try:
        model_class = _get_model_class(module_name, entity_name)
        create_schema = _get_create_schema(module_name, entity_name)
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid module or entity: {str(e)}"
        )

    # Perform import with optional enrichment
    service = ImportExportService(db)

    # Use enrichment for UnitaImmobiliare when enabled
    if enable_enrichment and entity_name == "UnitaImmobiliare":
        # Step 1: Analyze CSV to get columns
        csv_structure = service.analyze_csv_structure(csv_data, max_sample_rows=0)
        csv_columns = csv_structure["csv_columns"]

        # Step 2: Get entity fields from schema
        entity_fields = []
        if create_schema:
            for field_name, field_info in create_schema.model_fields.items():
                entity_fields.append({
                    "name": field_name,
                    "type": str(field_info.annotation),
                    "required": field_info.is_required()
                })

        # Step 3: Infer field mapping
        field_mapping = service.infer_field_mapping(csv_columns, entity_fields)

        # Step 4: Import with enrichment (all automatismi active)
        result = service.import_from_csv_with_enrichment(
            model=model_class,
            csv_data=csv_data,
            field_mapping=field_mapping,
            create_schema=create_schema,
            skip_errors=skip_errors,
            enable_updates=enable_updates
        )
        # Transform enrichment result to match ImportResult schema
        # Enrichment returns: {created, updated, errors, ...}
        # ImportResult expects: {imported, errors, ...}
        result["imported"] = result.get("created", 0) + result.get("updated", 0)
    else:
        # Standard import without enrichment
        result = service.import_from_csv(
            model=model_class,
            csv_data=csv_data,
            create_schema=create_schema,
            validate=True,
            skip_errors=skip_errors
        )

    return ImportResult(**result)


@router.get("/export")
async def export_data(
    module_name: str = Query(...),
    entity_name: str = Query(...),
    format: str = Query("csv", regex="^(csv|excel|json)$"),
    fields: Optional[str] = Query(None, description="Comma-separated field names"),
    db: Session = Depends(get_db)
):
    """
    Generic export endpoint for any entity.

    Supports CSV, Excel, and JSON formats.

    Example:
        GET /api/v1/import-export/export?module_name=affitti_lungo&entity_name=UnitaImmobiliare&format=csv
    """
    try:
        model_class = _get_model_class(module_name, entity_name)
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid module or entity: {str(e)}"
        )

    # Parse fields
    field_list = fields.split(',') if fields else None

    service = ImportExportService(db)

    if format == "csv":
        data = service.export_to_csv(model=model_class, fields=field_list)
        return {
            "content": data,
            "filename": f"{entity_name}_export.csv",
            "content_type": "text/csv"
        }
    elif format == "excel":
        data = service.export_to_excel(model=model_class, fields=field_list)
        return {
            "content": data,
            "filename": f"{entity_name}_export.xlsx",
            "content_type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        }
    else:  # json
        data = service.export_to_dict(model=model_class, fields=field_list)
        return {
            "data": data,
            "count": len(data)
        }


@router.get("/template")
async def get_import_template(
    module_name: str = Query(...),
    entity_name: str = Query(...),
    include_sample: bool = Query(False),
    db: Session = Depends(get_db)
):
    """
    Generate import template for an entity.

    Returns a CSV template with column headers (and optionally a sample row).

    Example:
        GET /api/v1/import-export/template?module_name=affitti_lungo&entity_name=UnitaImmobiliare&include_sample=true
    """
    try:
        model_class = _get_model_class(module_name, entity_name)
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid module or entity: {str(e)}"
        )

    service = ImportExportService(db)
    template = service.generate_import_template(
        model=model_class,
        include_sample_data=include_sample
    )

    return {
        "content": template,
        "filename": f"{entity_name}_import_template.csv",
        "content_type": "text/csv"
    }


def _get_model_class(module_name: str, entity_name: str):
    """
    Get SQLAlchemy model class from module and entity name.

    Uses dynamic import to load the model.
    """
    try:
        # Import module models
        models_module = __import__(
            f"app.modules.{module_name}.models",
            fromlist=[entity_name]
        )

        # Get model class
        model_class = getattr(models_module, entity_name)
        return model_class
    except (ImportError, AttributeError) as e:
        raise ValueError(f"Model {entity_name} not found in module {module_name}: {str(e)}")


def _get_create_schema(module_name: str, entity_name: str):
    """
    Get Pydantic Create schema for validation.

    Looks for {EntityName}Create schema.
    """
    try:
        # Import module schemas
        schemas_module = __import__(
            f"app.modules.{module_name}.schemas",
            fromlist=[f"{entity_name}Create"]
        )

        # Get create schema
        create_schema = getattr(schemas_module, f"{entity_name}Create")
        return create_schema
    except (ImportError, AttributeError):
        # Return None if schema not found - import will work without validation
        return None

# ==================== NEW: Field Mapping & Analysis Endpoints ====================

class AnalyzeResponse(BaseModel):
    """Response from CSV analysis."""
    csv_columns: List[str]
    entity_fields: List[dict]
    suggested_mapping: dict[str, str]
    sample_rows: List[dict]


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_csv(
    file: UploadFile = File(...),
    module_name: str = Query(...),
    entity_name: str = Query(...),
    db: Session = Depends(get_db)
):
    """
    Analyze CSV file and suggest field mappings.

    Returns:
    - CSV columns
    - Entity fields with metadata
    - Suggested automatic mappings
    - Sample rows for preview

    Example:
        POST /api/v1/import-export/analyze?module_name=affitti_lungo&entity_name=UnitaImmobiliare
        Body: CSV file
    """
    # Read and decode CSV
    content = await file.read()
    for encoding in ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252', 'iso-8859-1']:
        try:
            csv_data = content.decode(encoding)
            break
        except UnicodeDecodeError:
            continue
    else:
        csv_data = content.decode('utf-8', errors='replace')

    # Get model and schema
    try:
        model_class = _get_model_class(module_name, entity_name)
        create_schema = _get_create_schema(module_name, entity_name)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid module or entity: {str(e)}")

    # Analyze CSV
    service = ImportExportService(db)

    csv_analysis = service.analyze_csv_structure(csv_data)
    entity_fields = service.get_entity_fields(model_class, create_schema)
    suggested_mapping = service.infer_field_mapping(
        csv_analysis["csv_columns"],
        entity_fields
    )

    return AnalyzeResponse(
        csv_columns=csv_analysis["csv_columns"],
        entity_fields=entity_fields,
        suggested_mapping=suggested_mapping,
        sample_rows=csv_analysis["sample_rows"]
    )


class PreviewResponse(BaseModel):
    """Response from import preview."""
    total_rows: int
    valid_rows: int
    invalid_rows: int
    preview_data: List[dict]


@router.post("/preview", response_model=PreviewResponse)
async def preview_import(
    file: UploadFile = File(...),
    module_name: str = Query(...),
    entity_name: str = Query(...),
    field_mapping: str = Query(..., description="JSON string of field mapping"),
    db: Session = Depends(get_db)
):
    """
    Preview import with validation, without saving to database.

    Args:
        field_mapping: JSON string like '{"CSV_Col": "entity_field"}'

    Returns validation results for each row.

    Example:
        POST /api/v1/import-export/preview?module_name=affitti_lungo&entity_name=UnitaImmobiliare&field_mapping={"Indirizzo":"indirizzo"}
    """
    import json

    # Parse field mapping
    try:
        mapping_dict = json.loads(field_mapping)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid field_mapping JSON")

    # Read and decode CSV
    content = await file.read()
    for encoding in ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252', 'iso-8859-1']:
        try:
            csv_data = content.decode(encoding)
            break
        except UnicodeDecodeError:
            continue
    else:
        csv_data = content.decode('utf-8', errors='replace')

    # Get model and schema
    try:
        model_class = _get_model_class(module_name, entity_name)
        create_schema = _get_create_schema(module_name, entity_name)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid module or entity: {str(e)}")

    if not create_schema:
        raise HTTPException(status_code=400, detail="Create schema not found for validation")

    # Validate preview
    service = ImportExportService(db)
    preview_result = service.validate_import_preview(
        csv_data=csv_data,
        field_mapping=mapping_dict,
        create_schema=create_schema
    )

    return PreviewResponse(**preview_result)


# ==================== Configuration Management Endpoints ====================

from app.core.schemas.import_configuration import (
    ImportConfigurationCreate,
    ImportConfigurationUpdate,
    ImportConfigurationResponse
)
from app.core.models.import_configuration import ImportConfiguration


@router.post("/configurations", response_model=ImportConfigurationResponse)
async def create_configuration(
    config: ImportConfigurationCreate,
    db: Session = Depends(get_db)
):
    """
    Save an import configuration for reuse.

    Example:
        POST /api/v1/import-export/configurations
        Body: {
            "name": "Import Agenzia ABC",
            "module_name": "affitti_lungo",
            "entity_name": "UnitaImmobiliare",
            "field_mapping": {"Indirizzo": "indirizzo", "Città": "citta"}
        }
    """
    db_config = ImportConfiguration(**config.model_dump())
    db.add(db_config)
    db.commit()
    db.refresh(db_config)
    return db_config


@router.get("/configurations", response_model=List[ImportConfigurationResponse])
async def list_configurations(
    module_name: Optional[str] = Query(None),
    entity_name: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """
    List saved import configurations.

    Optional filters by module and entity.

    Example:
        GET /api/v1/import-export/configurations?module_name=affitti_lungo&entity_name=UnitaImmobiliare
    """
    query = db.query(ImportConfiguration)

    if module_name:
        query = query.filter(ImportConfiguration.module_name == module_name)
    if entity_name:
        query = query.filter(ImportConfiguration.entity_name == entity_name)

    configs = query.order_by(ImportConfiguration.created_at.desc()).all()
    return configs


@router.get("/configurations/{config_id}", response_model=ImportConfigurationResponse)
async def get_configuration(
    config_id: int,
    db: Session = Depends(get_db)
):
    """
    Get a specific import configuration by ID.

    Example:
        GET /api/v1/import-export/configurations/1
    """
    config = db.query(ImportConfiguration).filter(ImportConfiguration.id == config_id).first()

    if not config:
        raise HTTPException(status_code=404, detail="Configuration not found")

    return config


@router.put("/configurations/{config_id}", response_model=ImportConfigurationResponse)
async def update_configuration(
    config_id: int,
    config_update: ImportConfigurationUpdate,
    db: Session = Depends(get_db)
):
    """
    Update an existing import configuration.

    Example:
        PUT /api/v1/import-export/configurations/1
        Body: {"name": "New Name", "field_mapping": {...}}
    """
    config = db.query(ImportConfiguration).filter(ImportConfiguration.id == config_id).first()

    if not config:
        raise HTTPException(status_code=404, detail="Configuration not found")

    # Update fields
    update_data = config_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(config, field, value)

    db.commit()
    db.refresh(config)
    return config


@router.delete("/configurations/{config_id}")
async def delete_configuration(
    config_id: int,
    db: Session = Depends(get_db)
):
    """
    Delete an import configuration.

    Example:
        DELETE /api/v1/import-export/configurations/1
    """
    config = db.query(ImportConfiguration).filter(ImportConfiguration.id == config_id).first()

    if not config:
        raise HTTPException(status_code=404, detail="Configuration not found")

    db.delete(config)
    db.commit()

    return {"success": True, "message": "Configuration deleted"}


# ==================== Enhanced Import with Mapping ====================

@router.post("/import-with-mapping", response_model=ImportResult)
async def import_with_mapping(
    file: UploadFile = File(...),
    module_name: str = Query(...),
    entity_name: str = Query(...),
    field_mapping: str = Query(..., description="JSON string of field mapping"),
    skip_errors: bool = Query(True),
    save_configuration: bool = Query(False),
    configuration_name: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Import with explicit field mapping.

    Optionally saves the configuration for future reuse.

    Example:
        POST /api/v1/import-export/import-with-mapping?module_name=affitti_lungo&entity_name=UnitaImmobiliare&field_mapping={"Indirizzo":"indirizzo"}&save_configuration=true&configuration_name=MyConfig
    """
    import json

    # Parse field mapping
    try:
        mapping_dict = json.loads(field_mapping)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid field_mapping JSON")

    # Read and decode CSV
    content = await file.read()
    for encoding in ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252', 'iso-8859-1']:
        try:
            csv_data = content.decode(encoding)
            break
        except UnicodeDecodeError:
            continue
    else:
        csv_data = content.decode('utf-8', errors='replace')

    # Get model and schema
    try:
        model_class = _get_model_class(module_name, entity_name)
        create_schema = _get_create_schema(module_name, entity_name)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid module or entity: {str(e)}")

    # Perform import with mapping
    service = ImportExportService(db)
    result = service.import_from_csv(
        model=model_class,
        csv_data=csv_data,
        field_mapping=mapping_dict,
        create_schema=create_schema,
        validate=True,
        skip_errors=skip_errors
    )

    # Save configuration if requested
    if save_configuration and configuration_name:
        config = ImportConfiguration(
            name=configuration_name,
            module_name=module_name,
            entity_name=entity_name,
            field_mapping=mapping_dict
        )
        db.add(config)
        db.commit()

    return ImportResult(**result)
