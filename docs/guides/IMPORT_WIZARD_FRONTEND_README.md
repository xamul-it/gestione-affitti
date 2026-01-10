# ImportWizard - Complete Import System with Field Mapping

A comprehensive, multi-step wizard for importing CSV/Excel data with intelligent field mapping and validation.

## Overview

The ImportWizard provides a user-friendly interface for importing data from CSV or Excel files into any entity. It includes:

- **Smart field mapping** with automatic suggestions
- **Data validation** with detailed error reporting
- **Preview** before import
- **Configuration management** to save and reuse mappings
- **Template support** for standard format imports

## Architecture

### Components Structure

```
ImportWizard/
├── ImportWizard.jsx          # Main wizard container & step orchestration
├── ImportWizard.css          # Complete styling for all components
├── ImportUploadStep.jsx      # Step 1: File upload & mode selection
├── ImportMappingStep.jsx     # Step 2: CSV-to-entity field mapping
├── ImportPreviewStep.jsx     # Step 3: Data preview & validation
├── ImportResultsStep.jsx     # Step 4: Import execution & results
├── index.js                  # Module exports
└── README.md                 # This file
```

## Usage

### Basic Integration

```jsx
import { ImportWizard } from './components/Platform/ImportWizard';

function MyEntityList() {
  const [showImportWizard, setShowImportWizard] = useState(false);

  const handleImportComplete = (results) => {
    console.log('Import completed:', results);
    // Refresh your data list
    fetchData();
  };

  return (
    <>
      <button onClick={() => setShowImportWizard(true)}>
        Import Data
      </button>

      {showImportWizard && (
        <ImportWizard
          moduleName="affitti_lungo"
          entityName="UnitaImmobiliare"
          entityLabel="Unità Immobiliari"
          onComplete={handleImportComplete}
          onCancel={() => setShowImportWizard(false)}
        />
      )}
    </>
  );
}
```

### Props

| Prop | Type | Required | Description |
|------|------|----------|-------------|
| `moduleName` | string | Yes | Backend module name (e.g., "affitti_lungo") |
| `entityName` | string | Yes | Entity name (e.g., "UnitaImmobiliare") |
| `entityLabel` | string | Yes | User-friendly label (e.g., "Unità Immobiliari") |
| `onComplete` | function | No | Callback when import completes: `(results) => void` |
| `onCancel` | function | No | Callback when user cancels: `() => void` |

## User Flow

### Step 1: Upload

Users select their import mode:

1. **Use Template** - Standard format, no mapping needed
2. **Upload Generic CSV** - Custom format, requires field mapping
3. **Load Saved Configuration** - Reuse a previously saved mapping

### Step 2: Mapping (for generic CSV only)

- Visual interface showing CSV columns → Entity fields
- Dropdown selectors for each CSV column
- Color coding:
  - **Green**: Successfully mapped
  - **Red**: Required field not mapped
  - **Yellow**: Optional field not mapped
- Sample data preview from CSV
- Option to save configuration for future use

### Step 3: Preview

- Statistics: Total rows, valid rows, invalid rows
- Preview table showing first 20 rows
- Validation status for each row
- Detailed error messages for invalid rows
- Option to skip errors or stop on first error

### Step 4: Results

- Success/error statistics
- Detailed error list with row numbers
- Options to import another file or close

## API Methods

The following API methods are used (from `services/api.js`):

### `analyzeCSV(moduleName, entityName, file)`

Analyzes a CSV file and returns:
- CSV column names
- Entity field definitions
- Suggested field mappings (fuzzy matching)
- Sample rows

### `previewImport(moduleName, entityName, file, fieldMapping)`

Validates data and returns:
- Total row count
- Valid/invalid row counts
- Preview data with validation status
- Validation errors for each invalid row

### `importWithMapping(moduleName, entityName, file, fieldMapping, skipErrors, saveConfig, configName)`

Executes the import and returns:
- Import results (success/error counts)
- Error details with row numbers
- Configuration ID if saved

### Configuration Management

- `getImportConfigurations(moduleName, entityName)` - List saved configs
- `getImportConfiguration(configId)` - Get specific config
- `saveImportConfiguration(config)` - Save new config
- `deleteImportConfiguration(configId)` - Delete config

## Features

### Intelligent Field Mapping

The system uses fuzzy matching to automatically suggest field mappings:

1. **Exact match** (case-insensitive)
2. **Alias matching** (common field name variations)
3. **Similarity scoring** (70%+ threshold)

### Data Validation

Validates each row before import:
- Required field presence
- Data type compatibility
- Pydantic schema validation
- Foreign key constraints

### Error Handling

Comprehensive error reporting:
- Row-by-row validation
- Detailed error messages
- Original data context
- Option to skip errors or stop

### Configuration Management

Save and reuse field mappings:
- Named configurations
- Module/entity scoped
- Date tracking
- Easy selection from dropdown

## Styling

The ImportWizard uses a modern, responsive design:

- **Color Scheme**: Purple gradient header (#667eea → #764ba2)
- **Typography**: Clean, hierarchical
- **Animations**: Smooth transitions and loading states
- **Responsive**: Mobile-friendly layout
- **Accessibility**: Keyboard navigation, ARIA labels

### CSS Classes

Key classes for customization:

```css
.import-wizard-container   /* Main container */
.wizard-header            /* Header with title */
.wizard-steps             /* Step indicator */
.wizard-content           /* Step content area */
.field-mapping-row        /* Mapping UI row */
.preview-table            /* Preview data table */
.results-summary          /* Results card */
```

## Backend Requirements

The backend must implement these endpoints:

```
POST /api/v1/import-export/analyze
POST /api/v1/import-export/preview
POST /api/v1/import-export/import
GET  /api/v1/import-export/configurations
GET  /api/v1/import-export/configurations/{id}
POST /api/v1/import-export/configurations
DELETE /api/v1/import-export/configurations/{id}
```

See `/tmp/IMPORT_SYSTEM_DESIGN.md` for complete backend specification.

## Example: Import Workflow

### Scenario: Import Properties from Agency Excel

1. User clicks "Import" button
2. Selects "Upload Generic CSV" mode
3. Drops file "properties_jan_2025.xlsx"
4. System analyzes file:
   - Detects columns: "Full Address", "City", "ZIP", "Area", "Rooms"
   - Suggests mapping:
     - "Full Address" → `indirizzo`
     - "City" → `citta`
     - "ZIP" → `cap`
     - "Area" → `superficie_mq`
     - "Rooms" → `locali`
5. User confirms mapping, checks "Save configuration"
6. Names it "Import from Agency ABC"
7. Reviews preview: 148 valid, 2 errors (missing ZIP)
8. Selects "Skip errors"
9. Imports 148 records successfully
10. Next month: Selects saved config → automatic mapping

## Error Messages

Common errors and solutions:

| Error | Cause | Solution |
|-------|-------|----------|
| "Campo obbligatorio mancante" | Required field not mapped | Map the required field |
| "File troppo grande" | File > 10MB | Split file or compress |
| "Formato non supportato" | Wrong file type | Use CSV/XLSX/XLS |
| "Errore di validazione" | Invalid data | Check data format |

## Performance

- **File Size Limit**: 10MB (configurable)
- **Max Rows**: 10,000 per import
- **Preview Rows**: First 50 validated, 20 displayed
- **Batch Insert**: Groups of 100 records
- **Validation**: Client-side + server-side

## Future Enhancements

Planned improvements:

1. **Async Processing** - Background jobs for large imports (>1000 rows)
2. **Progress Updates** - Real-time progress bar via WebSocket
3. **Error Report Download** - Export error details as CSV
4. **Drag & Drop Mapping** - Alternative to dropdown selectors
5. **Field Transformation** - Data conversion rules (e.g., date formats)
6. **Duplicate Detection** - Check for existing records
7. **Rollback** - Undo import operation

## Troubleshooting

### Wizard doesn't open
- Check console for errors
- Verify all components are imported
- Ensure CSS is loaded

### Field mapping not working
- Verify backend returns `entity_fields` correctly
- Check field names match between frontend and backend
- Inspect network tab for API errors

### Preview shows all errors
- Check validation rules in backend schema
- Verify data format matches field types
- Review sample CSV for issues

### Import fails silently
- Check browser console
- Verify API endpoint is accessible
- Check backend logs for errors

## Support

For issues or questions:
1. Check this README
2. Review design document: `/tmp/IMPORT_SYSTEM_DESIGN.md`
3. Inspect browser console and network tab
4. Check backend API logs

## License

Part of Gestione Affitti application.
