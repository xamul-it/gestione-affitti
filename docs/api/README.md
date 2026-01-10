# API Documentation & Import System Design

This directory contains comprehensive documentation of the Gestione Affitti REST API and the automated import system (automatismi).

## Quick Navigation

For API reference and design:

1. **API Quick Reference:** `IMPORT_WIZARD_QUICK_REFERENCE.md` - Endpoint cheat sheet
2. **Import System Design:** `IMPORT_SYSTEM_DESIGN.md` - Architecture and design
3. **Functional Analysis:** `ANALISI_FUNZIONALE_AUTOMATISMI_IMPORT.md` - Detailed functional analysis
4. **Improvements:** `IMPORT_WIZARD_IMPROVEMENTS.md` - Enhancement proposals

## Files in This Directory

### IMPORT_WIZARD_QUICK_REFERENCE.md
Quick reference card for import system API endpoints.

**Contents:**
- Available API endpoints
- Request/response formats
- Parameter descriptions
- Error codes and messages
- Example requests and responses
- Authentication requirements
- Rate limiting (if applicable)

**Quick Lookup:**
- Import endpoints
- Upload endpoints
- Mapping endpoints
- Progress tracking
- Status checks

**For:** Frontend developers, API consumers, QA engineers

### IMPORT_SYSTEM_DESIGN.md
Complete design documentation for the import system and automated features.

**Contents:**
- System architecture
- Design goals and principles
- Supported file formats
- Data transformation pipeline
- Validation strategy
- Error handling approach
- Performance considerations
- Security measures

**Key Features Documented:**
1. ID-based INSERT/UPDATE detection
2. Automatic timestamp generation
3. Code generation with province prefixes
4. Cadastral category inference
5. Address normalization and CAP lookup

**For:** System architects, backend developers, technical leads

### ANALISI_FUNZIONALE_AUTOMATISMI_IMPORT.md
Detailed functional analysis of the import automatisms (automated features).

**Contents:**
- Feature-by-feature breakdown
- Business logic for each automatism
- Data validation rules
- Edge cases and handling
- Dependency analysis
- Integration points
- Test scenarios
- Success criteria

**Features Analyzed:**
- ID Detection (INSERT vs UPDATE)
- Timestamp Management
- Code Generation
- Category Inference
- Address Normalization

**For:** Requirements analysts, QA engineers, project managers

### IMPORT_WIZARD_IMPROVEMENTS.md
Documentation of proposed and implemented improvements to the import system.

**Contents:**
- Identified issues and challenges
- Proposed solutions
- Implementation options with trade-offs
- Performance improvements
- User experience enhancements
- Backward compatibility notes
- Migration guide for upgrades
- Future roadmap

**Topics:**
- Error handling improvements
- Validation enhancements
- Performance optimization
- UI/UX improvements
- Data consistency measures
- Reporting capabilities

**For:** Product managers, system architects, senior developers

## API Overview

### REST Conventions

All Gestione Affitti APIs follow REST conventions:

- `GET /api/v1/entity/` - List all entities (with pagination)
- `GET /api/v1/entity/{id}` - Get single entity by ID
- `POST /api/v1/entity/` - Create new entity
- `PUT /api/v1/entity/{id}` - Update entity
- `DELETE /api/v1/entity/{id}` - Delete entity

### API Endpoints by Module

#### anagrafica_italiana (Italian Registry)
- `GET /api/v1/soggetti/` - List subjects
- `POST /api/v1/soggetti/` - Create subject
- `GET /api/v1/soggetti/{id}` - Get subject
- `PUT /api/v1/soggetti/{id}` - Update subject
- `DELETE /api/v1/soggetti/{id}` - Delete subject

#### immobili (Properties)
- `GET /api/v1/immobili/` - List properties
- `POST /api/v1/immobili/` - Create property
- `GET /api/v1/immobili/{id}` - Get property details
- `PUT /api/v1/immobili/{id}` - Update property
- `DELETE /api/v1/immobili/{id}` - Delete property
- `GET /api/v1/categorie-catastali/` - List cadastral categories
- `GET /api/v1/comuni/` - List Italian municipalities

#### affitti_lungo (Rentals)
- `GET /api/v1/contratti/` - List contracts
- `POST /api/v1/contratti/` - Create contract
- `GET /api/v1/contratti/{id}` - Get contract
- `PUT /api/v1/contratti/{id}` - Update contract
- `GET /api/v1/affittuari/` - List tenants
- `POST /api/v1/affittuari/` - Create tenant
- `GET /api/v1/incassi/` - List income
- `GET /api/v1/spese/` - List expenses

### Import API Endpoints

#### File Upload
- `POST /api/v1/import/upload` - Upload CSV file
- `GET /api/v1/import/preview/{upload_id}` - Preview data

#### Import Processing
- `POST /api/v1/import/{upload_id}/validate` - Validate data
- `POST /api/v1/import/{upload_id}/process` - Process import
- `GET /api/v1/import/{upload_id}/progress` - Get progress status
- `GET /api/v1/import/{upload_id}/result` - Get import result

#### Mapping Configuration
- `GET /api/v1/import/mappings/` - List available mappings
- `POST /api/v1/import/mappings/` - Create custom mapping
- `GET /api/v1/import/mappings/{id}` - Get mapping details

## Key Concepts

### 1. Automatismi (Automated Features)

The import system includes five key automatismi that handle common data transformation tasks:

#### Automatismo 1: ID Detection
Automatically detects whether to INSERT or UPDATE:
- Empty ID field → INSERT new record
- Populated ID field → UPDATE existing record

#### Automatismo 2: Timestamp Management
Automatically manages timestamps:
- `created_at` - Set at creation, never changed
- `updated_at` - Set at creation, updated on each change
- Handled by database server functions

#### Automatismo 3: Code Generation
Automatically generates codes with province prefixes:
- Format: `{SIGLA}{00001}` (e.g., MI00001, BO00042)
- Progressive numbering per province
- Flag `codice_auto_generated` tracks automatic codes

#### Automatismo 4: Category Inference
Automatically infers cadastral categories from property types:
- Maps free-text property types to official categories
- Learning system improves over time
- Fallback to A/2 (standard apartment)

#### Automatismo 5: Address Normalization
Automatically normalizes and parses addresses:
- Extracts city, province, street, floor
- Performs CAP (postal code) lookup
- Handles multiple address formats
- Non-blocking warnings for unparseable parts

### 2. Data Validation

The API validates data at multiple levels:

- **Input validation:** Checks format and required fields
- **Business validation:** Verifies business rules
- **Cross-entity validation:** Checks relationships and consistency
- **Database constraints:** Final safety check

### 3. Error Handling

Error responses include:
- Error code and message
- Field-level errors (if applicable)
- Suggested corrections
- Links to documentation

Example error response:
```json
{
  "error": "VALIDATION_ERROR",
  "message": "Data validation failed",
  "details": {
    "codice_fiscale": "Invalid format (expected 16 characters)"
  }
}
```

## Common API Use Cases

### Case 1: Import Properties from CSV
1. Upload CSV file via `/api/v1/import/upload`
2. Receive upload ID
3. Configure field mappings (if needed)
4. Call `/api/v1/import/{upload_id}/validate`
5. If valid, call `/api/v1/import/{upload_id}/process`
6. Poll `/api/v1/import/{upload_id}/progress`
7. Get results from `/api/v1/import/{upload_id}/result`

### Case 2: List and Filter Entities
```
GET /api/v1/immobili/?skip=0&limit=50&provincia=MI
```

### Case 3: Update Property Details
```
PUT /api/v1/immobili/123
{
  "indirizzo": "New Address",
  "comune": "Milano",
  "CAP": "20100"
}
```

### Case 4: Check Import Progress
```
GET /api/v1/import/abc123/progress
→ { "processed": 45, "total": 100, "status": "in_progress" }
```

## Authentication & Authorization

- API requires authentication token (if enabled)
- Token passed in Authorization header: `Authorization: Bearer {token}`
- Different endpoints have different permission requirements
- User roles determine accessible entities

## Rate Limiting

- Standard rate limit: 100 requests per minute per client
- Import endpoints: Higher limit for batch operations
- File uploads: No strict rate limit but connection timeout after 30 minutes

## Testing the API

### Using curl
```bash
curl -X GET "http://localhost:8000/api/v1/immobili/" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Using Python requests
```python
import requests
response = requests.get("http://localhost:8000/api/v1/immobili/")
print(response.json())
```

### Using the Swagger UI
Navigate to `http://localhost:8000/docs` for interactive API documentation.

## Debugging API Issues

### No Data Returned
- Check authentication token
- Verify entity exists
- Check query parameters

### Import Fails
- Validate CSV format
- Check field mappings
- Review error details in response

### Slow Responses
- Check database performance
- Review query parameters (skip/limit)
- Check server logs

## Performance Considerations

- Pagination recommended: Use `skip` and `limit` parameters
- Bulk imports: Batch requests for better performance
- Database indexes: Available on common query fields
- Caching: Some endpoints support caching headers

## References

- `docs/guides/MODULE_DEVELOPMENT_GUIDE.md` - For adding new API endpoints
- `docs/features/` - Feature-specific documentation
- Root `CLAUDE.md` - API conventions and patterns
- `docs/setup/DEPLOYMENT_GUIDE.md` - API configuration

---

**Last Updated:** 2025-12-04
**API Version:** v1
**Status:** Production Ready
**Endpoints:** 50+
