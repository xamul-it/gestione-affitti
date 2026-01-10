# Feature Documentation & Design

This directory contains comprehensive documentation of Gestione Affitti features, including design documents, test reports, user experience reviews, and implementation guides.

## Quick Navigation

### By Feature

#### Import System & Automatisms
- **Design Architecture:** `DESIGN_ARCHITETTURALE_AUTOMATISMI.md` - Complete system architecture
- **Address Normalization:** `GUIDA_COMUNI_E_INDIRIZZI.md` - Address parsing and CAP lookup guide
- **Test Results:** `REPORT_FINALE_AUTOMATISMI_IMPORT.md` - Implementation and test results
- **Complete Testing:** `REPORT_TEST_COMPLETO_AUTOMATISMI.md` - Full test coverage and validation

#### User Experience & UI
- **UX Review:** `UX_REVIEW_IMPORT_WIZARD.md` - User experience analysis and recommendations

## Files in This Directory

### DESIGN_ARCHITETTURALE_AUTOMATISMI.md
Comprehensive architecture document for the import automatisms system.

**Contents:**
- System overview and goals
- Service-oriented architecture design
- Detailed service descriptions
- Database schema (new tables and columns)
- Service layer patterns
- Performance optimization strategies
- Fallback and fail-safe mechanisms
- Error handling approach
- Integration architecture
- Implementation roadmap

**Key Systems:**
1. **AddressNormalizerService** - Parses addresses and looks up CAP codes
2. **CodiceGeneratorService** - Generates property codes with province prefixes
3. **CategoriaCatastaleService** - Infers cadastral categories from property types

**Database Components:**
- `categorie_catastali` - 45 official cadastral categories
- `tipo_immobile_categoria_map` - Learning system for type-to-category mapping
- `comuni_italia` - 84 primary Italian municipalities

**For:** System architects, senior backend developers, technical leads

### GUIDA_COMUNI_E_INDIRIZZI.md
Practical guide for address normalization and municipal data handling.

**Contents:**
- Overview of Italian address formats
- Supported address patterns
- CAP (postal code) lookup procedure
- Municipality (Comune) data
- Province codes and naming
- Common address variations and how they're handled
- Troubleshooting unparseable addresses
- Best practices for data entry

**Use Cases:**
- Entering property addresses
- Importing batch address data
- Correcting address parsing issues
- Understanding CAP codes

**For:** Data entry specialists, support staff, developers handling addresses

### REPORT_FINALE_AUTOMATISMI_IMPORT.md
Final implementation and test report for the import automatisms feature.

**Contents:**
- Executive summary
- Implementation overview
- Feature checklist
- Test results summary
- Known issues identified
- Recommendations for next steps
- Performance metrics
- Success criteria assessment

**Test Coverage:**
- 13/14 records imported successfully (93% success rate)
- All automatisms validated
- Performance metrics documented
- Known issues logged

**For:** Project managers, QA leads, stakeholders

### REPORT_TEST_COMPLETO_AUTOMATISMI.md
Complete test report with full validation of all automatisms and features.

**Contents:**
- Detailed test plan
- Test execution results
- Individual feature test results
- Issue resolution log
- Fixes applied and verified
- Final validation checklist
- Performance measurements
- Success metrics

**Test Areas:**
- ID-based INSERT/UPDATE detection
- Automatic timestamp generation
- Code generation functionality
- Category inference accuracy
- Address normalization and parsing
- CAP lookup accuracy
- Error handling and recovery
- Data consistency

**For:** QA engineers, developers, technical reviewers

### UX_REVIEW_IMPORT_WIZARD.md
User experience analysis and recommendations for the import wizard interface.

**Contents:**
- UI/UX overview
- Current user workflows
- Usability findings
- Issues identified
- Recommendations
- Proposed improvements
- Wireframes or mockups (if included)
- User feedback summary
- Priority ranking of improvements

**Review Areas:**
- File upload experience
- Progress feedback
- Error messages and guidance
- Data mapping interface
- Result presentation
- Accessibility considerations

**For:** Product managers, UX/UI designers, frontend developers

## Feature Overview

### The Import System

The import system enables users to bulk-import property data from CSV files with automated data transformation.

#### Key Features:

1. **Automatic Data Type Detection**
   - Detects whether to create new records (INSERT) or update existing ones (UPDATE)
   - Based on ID field presence and value

2. **Automatic Timestamp Management**
   - `created_at` set automatically at creation
   - `updated_at` maintained automatically
   - Prevents user tampering with timestamps

3. **Code Generation**
   - Automatically generates property codes
   - Format: Province code + Progressive number (e.g., MI00001)
   - Ensures uniqueness per province
   - Tracks auto-generated vs. manual codes

4. **Category Inference**
   - Maps property types to official cadastral categories
   - Learning system improves accuracy over time
   - Fallback to standard category for unknown types
   - Supports 45 official Italian cadastral categories

5. **Address Normalization**
   - Parses unstructured address text
   - Extracts city, province, street, floor
   - Looks up CAP (postal code) codes
   - Handles multiple address formats
   - Non-blocking warnings for partially unparseable addresses

### Supported File Formats

- **CSV** - Comma or semicolon delimited
- **Character Encodings:** UTF-8, Latin-1, Windows-1252
- **Size Limit:** Up to 10,000 records per import
- **Timeout:** 30 minutes per import session

### Address Format Examples

The system handles various address formats:

```
MILANO (MI) VIALE UMBRIA, 49 Piano 5
BOLOGNA (BO) VIA EMILIA PONENTE, 2 Piano T
Milano Cadore 45
Via Roma 123, Milano
```

### Cadastral Categories

The system supports all 45 official Italian cadastral categories:

- **Group A:** Residential (A/1 to A/11)
- **Group B:** Rural (B/1 to B/8)
- **Group C:** Commercial (C/1 to C/7)
- **Group D:** Industrial (D/1 to D/10)
- **Group E:** Special Purpose (E/1 to E/9)

## Using the Import Features

### Workflow: Import Properties

1. **Prepare CSV File**
   - Include headers in first row
   - Use consistent formats
   - Include any address information

2. **Upload File**
   - Access import wizard in UI
   - Select CSV file to upload
   - System performs initial validation

3. **Map Fields**
   - Select which CSV columns map to which properties
   - System suggests mappings based on headers
   - Verify or adjust as needed

4. **Preview Data**
   - Review how data will be imported
   - Check for any obvious issues
   - Adjust mappings if needed

5. **Process Import**
   - Click "Import" to start processing
   - System applies all automatisms
   - Watch progress bar
   - Fix any issues that arise

6. **Review Results**
   - See success/failure count
   - Review any error messages
   - Check imported data in system
   - Run validation queries

### Best Practices

1. **Data Preparation**
   - Clean data before importing
   - Use consistent formats
   - Include all required fields
   - Verify addresses are correct

2. **Testing**
   - Test with small sample first
   - Preview before final import
   - Have rollback plan ready
   - Validate results after import

3. **Monitoring**
   - Watch for errors during import
   - Review address parsing results
   - Check categorization accuracy
   - Verify codes were generated correctly

## Known Issues & Limitations

### Current Limitations

1. **Address Parsing**
   - Rural and mountain addresses may not parse correctly
   - Addresses without city/province may fall back to manual entry
   - CAP database limited to 84 major cities

2. **Category Inference**
   - Learning system has limited historical data
   - Very unusual property types may not categorize correctly
   - Manual override may be needed

3. **Scale**
   - Single import limited to 10,000 records
   - Very large batches may be slow
   - Performance depends on server resources

### Recommended Solutions

See `docs/guides/MODULE_DEVELOPMENT_GUIDE.md` for implementing enhancements:

1. Expand CAP database to all Italian municipalities
2. Implement machine learning for better categorization
3. Add support for additional address formats
4. Implement batch import scheduling
5. Add export/download functionality

## References

- `docs/api/` - API documentation for import endpoints
- `docs/guides/IMPORT_WIZARD_IMPLEMENTATION.md` - Frontend implementation
- `docs/setup/IMPORT_AUTOMATISMI_QUICK_START.md` - Quick start guide
- Root `CLAUDE.md` - Development conventions

## Testing & Validation

To test import features:

1. **Functional Testing:** Follow test cases in `REPORT_TEST_COMPLETO_AUTOMATISMI.md`
2. **User Testing:** Use feedback from `UX_REVIEW_IMPORT_WIZARD.md`
3. **Performance Testing:** Check metrics in implementation reports
4. **Regression Testing:** Verify existing features still work

## Future Enhancements

Planned improvements to import system:

- Multi-entity import (import contracts, proprietors, etc. together)
- Scheduled/recurring imports
- Export functionality (mirror of import)
- Enhanced error reporting and suggestions
- Machine learning for better categorization
- Full CAP database (all 8,000+ municipalities)
- Duplicate detection and merging

---

**Last Updated:** 2025-12-04
**Status:** Production Ready
**Test Coverage:** 100% of core features
**Performance:** 93% import success rate
