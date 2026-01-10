# ImportWizard - Quick Start Guide

Get started with ImportWizard in 5 minutes!

## 1. Import the Component

```jsx
import { ImportWizard } from './components/Platform/ImportWizard';
```

## 2. Add State

```jsx
const [showImportWizard, setShowImportWizard] = useState(false);
```

## 3. Add Button

```jsx
<button onClick={() => setShowImportWizard(true)}>
  📥 Importa
</button>
```

## 4. Add Wizard

```jsx
{showImportWizard && (
  <ImportWizard
    moduleName="affitti_lungo"
    entityName="UnitaImmobiliare"
    entityLabel="Unità Immobiliari"
    onComplete={(results) => {
      console.log('Imported:', results.imported);
      setShowImportWizard(false);
      // Refresh your data here
    }}
    onCancel={() => setShowImportWizard(false)}
  />
)}
```

## 5. Done!

That's it! Your users can now:
- Upload CSV or Excel files
- Map fields visually
- Preview data before import
- See detailed results

## Complete Example

```jsx
import { useState } from 'react';
import { ImportWizard } from './components/Platform/ImportWizard';
import { unitaImmobiliariAPI } from './services/api';

function UnitaImmobiliariList() {
  const [data, setData] = useState([]);
  const [showImport, setShowImport] = useState(false);

  const fetchData = async () => {
    const response = await unitaImmobiliariAPI.getAll();
    setData(response.data);
  };

  return (
    <div>
      <h1>Unità Immobiliari</h1>

      <button onClick={() => setShowImport(true)}>
        📥 Importa
      </button>

      {showImport && (
        <ImportWizard
          moduleName="affitti_lungo"
          entityName="UnitaImmobiliare"
          entityLabel="Unità Immobiliari"
          onComplete={(results) => {
            alert(`Importati ${results.imported} record!`);
            setShowImport(false);
            fetchData();
          }}
          onCancel={() => setShowImport(false)}
        />
      )}

      {/* Your data table here */}
    </div>
  );
}
```

## Props Reference

| Prop | Type | Required | Description |
|------|------|----------|-------------|
| `moduleName` | string | ✓ | Backend module (e.g., "affitti_lungo") |
| `entityName` | string | ✓ | Entity class (e.g., "UnitaImmobiliare") |
| `entityLabel` | string | ✓ | Display name (e.g., "Unità Immobiliari") |
| `onComplete` | function | - | Called when import finishes: `(results) => void` |
| `onCancel` | function | - | Called when user cancels: `() => void` |

## Entity Examples

### Affittuari (Tenants)
```jsx
<ImportWizard
  moduleName="affitti_lungo"
  entityName="Affittuario"
  entityLabel="Affittuari"
  onComplete={handleComplete}
  onCancel={handleCancel}
/>
```

### Contratti (Contracts)
```jsx
<ImportWizard
  moduleName="affitti_lungo"
  entityName="Contratto"
  entityLabel="Contratti"
  onComplete={handleComplete}
  onCancel={handleCancel}
/>
```

### Spese (Expenses)
```jsx
<ImportWizard
  moduleName="affitti_lungo"
  entityName="Spesa"
  entityLabel="Spese"
  onComplete={handleComplete}
  onCancel={handleCancel}
/>
```

## User Flow

1. **User clicks Import button** → Wizard opens
2. **User selects upload mode**:
   - Use template (standard format)
   - Upload generic CSV (needs mapping)
   - Load saved config (reuse mapping)
3. **User uploads file** → System analyzes it
4. **User maps fields** (if needed) → CSV columns to entity fields
5. **User reviews preview** → Sees valid/invalid rows
6. **User clicks Import** → Data is imported
7. **User sees results** → Success message with stats

## Tips

### Save Time with Configurations
If you import from the same source regularly:
1. Map fields once
2. Check "Save configuration"
3. Give it a name
4. Next time: Select saved config → Skip mapping!

### Handle Errors
```jsx
onComplete={(results) => {
  if (results.errors > 0) {
    alert(`${results.imported} imported, ${results.errors} errors`);
  } else {
    alert(`Success! ${results.imported} records imported`);
  }
  setShowImport(false);
  fetchData();
}
```

### Styling
The wizard inherits your app's base styles. To customize:
```css
/* Override in your component CSS */
.import-wizard-container {
  max-width: 1000px; /* Make wider */
}

.wizard-header {
  background: linear-gradient(135deg, #your-color 0%, #your-color2 100%);
}
```

## Troubleshooting

### Wizard doesn't open
- Check browser console for errors
- Verify ImportWizard is imported correctly
- Ensure CSS file is loaded

### Field mapping not working
- Verify backend `/analyze` endpoint works
- Check network tab for API errors
- Ensure entity has fields defined

### Import fails
- Check backend logs
- Verify data format matches field types
- Test with small sample file first

## Need More Help?

- **Full Documentation**: See `README.md` in this directory
- **Integration Examples**: See `INTEGRATION_EXAMPLE.jsx`
- **Design Spec**: See `/tmp/IMPORT_SYSTEM_DESIGN.md`

## Next Steps

1. Test with a sample CSV file
2. Try field mapping with different formats
3. Save a configuration for reuse
4. Integrate into other entities

Happy importing! 🚀
