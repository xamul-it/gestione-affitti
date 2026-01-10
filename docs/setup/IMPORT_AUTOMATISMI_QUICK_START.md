# Import Automatismi - Quick Start Guide

## Overview

The import automatismi system provides automatic enrichment of property imports with:
- Address normalization and parsing
- Unique code generation (MI00001, BO00042, etc.)
- Cadastral category inference (A/2, C/6, etc.)
- CAP (postal code) lookup
- INSERT/UPDATE detection

---

## Quick Start

### 1. Start the Backend

```bash
cd backend
python app/main.py
```

On startup, the system will automatically:
- Create database tables
- Seed 45+ cadastral categories
- Seed 80+ Italian cities with CAP data

### 2. Use the Enhanced Import

```python
from app.core.platform_services import ImportExportService
from app.modules.affitti_lungo.models import UnitaImmobiliare

service = ImportExportService(db)

# Define field mapping
field_mapping = {
    "codice": "codice",
    "tipo": "tipo",
    "indirizzo": "indirizzo",
    "citta": "citta",
    "cap": "cap",
    "provincia": "provincia",
    "superficie_mq": "superficie_mq",
    "locali": "locali",
    # ... other fields
}

# Import with enrichment
result = service.import_from_csv_with_enrichment(
    model=UnitaImmobiliare,
    csv_data=csv_content,
    field_mapping=field_mapping,
    skip_errors=True,
    enable_updates=True
)

print(f"✅ Created: {result['created']}")
print(f"🔄 Updated: {result['updated']}")
print(f"❌ Errors: {result['errors']}")
print(f"⚠️  Warnings: {len(result['warnings'])}")
```

---

## CSV Format

### Example CSV

```csv
codice,tipo,indirizzo,citta,cap,provincia,superficie_mq,locali
,Appartamento,"MILANO (MI) VIALE UMBRIA, 49 Piano 5",Milano,,MI,72.00,3
,Box,"BOLOGNA (BO) VIA EMILIA, 2",Bologna,,BO,15,
MI00001,Appartamento,"Via Roma, 10",Milano,20100,MI,85.00,4
```

### Rules

1. **ID field**: Leave empty for new records, populate for updates
2. **Codice field**: Leave empty to auto-generate, or specify manually
3. **Address formats supported**:
   - Full: "CITTÀ (PROV) VIA NOME, NUM Piano X"
   - Simple: "Città Via Nome, Numero"
   - Plain: "Via Nome, Numero" (+ separate città field)
4. **Tipo field**: Free text (e.g., "Appartamento", "Box", "Villa")
   - System maps to cadastral categories automatically

---

## What Gets Auto-Enriched

### 1. Address Normalization
**Input**: `"MILANO (MI) VIALE UMBRIA, 49 Piano 5-S1"`
**Extracted**:
- `citta`: "Milano"
- `provincia`: "MI"
- `indirizzo`: "VIALE UMBRIA, 49"
- `piano`: "5-S1"

### 2. CAP Lookup
**Input**: `citta="Milano", provincia="MI"` (no CAP)
**Auto-filled**: `cap="20100"`

### 3. Codice Generation
**Input**: Empty codice, `provincia="MI"`
**Generated**: `codice="MI00001"` (or next progressive)
**Tracking**: `codice_auto_generated=True`

### 4. Categoria Catastale
**Input**: `tipo="Appartamento"`
**Inferred**: `categoria_catastale_id=2` (A/2 - Abitazioni di tipo civile)

**Input**: `tipo="Box"`
**Inferred**: `categoria_catastale_id=25` (C/6 - Autorimesse)

---

## Supported Property Types

Default mappings (extensible):

### Residential
- appartamento → A/2
- casa → A/2
- villa → A/8
- villino → A/7
- attico → A/1
- mansarda → A/3
- loft → A/2

### Garages
- box → C/6
- garage → C/6
- autorimessa → C/6
- posto auto → C/6

### Storage
- cantina → C/2
- magazzino → C/2
- deposito → C/2

### Commercial
- negozio → C/1
- locale commerciale → C/1
- ufficio → A/10
- studio → A/10

---

## INSERT vs UPDATE

The system detects operation mode based on the `id` field:

### INSERT (New Record)
```csv
id,codice,tipo,indirizzo
,MI00001,Appartamento,"Via Roma, 1"
```
- ID is empty → CREATE new record
- Auto-generate codice if empty
- Auto-generate timestamps

### UPDATE (Existing Record)
```csv
id,codice,tipo,indirizzo
42,MI00001,Appartamento,"Via Roma, 10"
```
- ID is populated → UPDATE record with ID=42
- Don't generate new codice
- Update timestamp automatically

---

## Warnings vs Errors

### Warnings (Don't Block Import)
- CAP not found for city
- Address format not recognized (kept as-is)
- Provincia format invalid (2 chars required)

Warnings are:
- Stored in `indirizzo_parsed_warnings` array field
- Included in import result
- Logged for review

### Errors (Block Row Import)
- Record ID not found (UPDATE mode)
- Required field validation failure
- Database constraint violation

With `skip_errors=True` (default):
- Skip error row, continue with next
- Error details captured in result

With `skip_errors=False`:
- Abort entire import on first error
- Rollback transaction

---

## Checking Results

### Query Imported Records

```python
# Find records with auto-generated codes
auto_codes = db.query(UnitaImmobiliare).filter(
    UnitaImmobiliare.codice_auto_generated == True
).all()

# Find records with parsing warnings
with_warnings = db.query(UnitaImmobiliare).filter(
    UnitaImmobiliare.indirizzo_parsed_warnings.isnot(None)
).all()

# Check categoria catastale
with_categoria = db.query(UnitaImmobiliare).filter(
    UnitaImmobiliare.categoria_catastale_id.isnot(None)
).all()
```

### View Cadastral Categories

```python
from app.core.models import CategoriaCatastale

# List all categories
categorie = db.query(CategoriaCatastale).order_by(
    CategoriaCatastale.ordinamento
).all()

for cat in categorie:
    print(f"{cat.codice} - {cat.nome} ({cat.gruppo})")
```

### View Comuni

```python
from app.core.models import ComuneItalia

# Find city by name
milano = db.query(ComuneItalia).filter(
    ComuneItalia.nome_normalized == "milano"
).first()

print(f"{milano.nome} - CAP: {milano.cap}, Prov: {milano.provincia_sigla}")
```

---

## Troubleshooting

### Issue: "CAP not found" warning

**Cause**: City not in comuni_italia table
**Solution**: Add city to database or import complete ISTAT dataset

```python
from app.core.models import ComuneItalia

comune = ComuneItalia(
    nome="Città Mancante",
    nome_normalized="citta mancante",
    codice_istat="123456",
    cap="12345",
    provincia_sigla="XX",
    regione="Regione"
)
db.add(comune)
db.commit()
```

### Issue: "Address format not recognized"

**Cause**: Address doesn't match supported patterns
**Solution**:
1. Use supported format in CSV
2. Or provide separate fields (città, provincia, etc.)
3. Address is kept as-is, you can correct manually

### Issue: Categoria not inferred correctly

**Cause**: Property type not in default mappings
**Solution**: Create manual mapping

```python
from app.core.platform_services import CategoriaCatastaleService

service = CategoriaCatastaleService(db)
categoria_id = service.get_or_create_user_mapping(
    tipo_immobile="tipo speciale",
    categoria_code="A/3"
)
```

### Issue: Codice collision

**Cause**: Manual codice conflicts with existing
**Solution**: Leave codice empty for auto-generation, or use unique value

---

## Performance Tips

### Large Imports (1000+ records)
- Use `skip_errors=True` to avoid full rollback
- Import in batches of 500-1000 records
- Monitor logs for warnings

### Optimize CAP Lookups
For production with many imports, consider:
1. Importing complete ISTAT dataset (~8,000 comuni)
2. Adding LRU cache to AddressNormalizerService

```python
from functools import lru_cache

@lru_cache(maxsize=1000)
def _lookup_cap_cached(self, citta_norm: str, provincia: str):
    # Same logic but cached
    pass
```

---

## API Integration Example

If you want to expose this via API:

```python
from fastapi import APIRouter, UploadFile, File, Query
from app.core.platform_services import ImportExportService

router = APIRouter(prefix="/api/v1/import")

@router.post("/immobili-enriched")
async def import_immobili_enriched(
    file: UploadFile = File(...),
    enable_updates: bool = Query(True),
    skip_errors: bool = Query(True),
    db: Session = Depends(get_db)
):
    """Import properties with automatic enrichment."""

    # Read CSV
    content = await file.read()
    csv_data = content.decode('utf-8')

    # Define mapping
    field_mapping = {
        "codice": "codice",
        "tipo": "tipo",
        "indirizzo": "indirizzo",
        "citta": "citta",
        # ... all fields
    }

    # Import with enrichment
    service = ImportExportService(db)
    result = service.import_from_csv_with_enrichment(
        model=UnitaImmobiliare,
        csv_data=csv_data,
        field_mapping=field_mapping,
        skip_errors=skip_errors,
        enable_updates=enable_updates
    )

    return {
        "success": result["success"],
        "summary": {
            "total": result["total_rows"],
            "created": result["created"],
            "updated": result["updated"],
            "errors": result["errors"]
        },
        "warnings": result["warnings"],
        "error_details": result["error_details"]
    }
```

---

## Configuration

### Add More Cities

Edit `/backend/app/core/seeds/seed_comuni_italia.py` and add entries:

```python
COMUNI_SEED_DATA = [
    # ... existing cities ...
    ("Nuova Città", "999999", "99999", "XX", "Provincia", "Regione"),
]
```

Re-run seed or insert manually.

### Add More Property Type Mappings

Edit `/backend/app/core/platform_services/categoria_catastale_service.py`:

```python
DEFAULT_TIPO_CATEGORIA = {
    # ... existing mappings ...
    "nuovo tipo": "A/2",
}
```

Or create via API/service at runtime.

### Customize Address Patterns

Edit `/backend/app/core/platform_services/address_normalizer_service.py`:

```python
# Add new regex pattern
PATTERN_CUSTOM = re.compile(
    r"your_pattern_here",
    re.IGNORECASE
)
```

---

## Logging

View detailed logs during import:

```bash
# Set log level
export LOG_LEVEL=DEBUG

# Or in Python
import logging
logging.basicConfig(level=logging.DEBUG)
```

Log messages include:
- `INFO`: Major operations (import start/complete, records created/updated)
- `DEBUG`: Detailed steps (address parsing, codice generation)
- `WARNING`: Non-blocking issues (CAP not found, format not recognized)
- `ERROR`: Blocking errors (validation failures, DB errors)

---

## Summary

The import automatismi system makes CSV imports intelligent by:
1. ✅ Parsing Italian addresses automatically
2. ✅ Looking up postal codes from database
3. ✅ Generating unique property codes
4. ✅ Inferring cadastral categories
5. ✅ Supporting both INSERT and UPDATE operations
6. ✅ Providing detailed warnings and error reporting

All enrichment is **fail-safe** - warnings don't block imports, allowing you to review and fix issues after import completes.

---

## Support

For issues or questions:
1. Check `/backend/logs/` for detailed error messages
2. Review `IMPLEMENTATION_SUMMARY.md` for technical details
3. Consult design documents in `/tmp/DESIGN_ARCHITETTURALE_AUTOMATISMI.md`
