import { useState, useEffect } from 'react';

/**
 * ImportMappingStep - Step 2: Field Mapping
 *
 * UI for mapping CSV columns to entity fields with:
 * - Visual mapping interface
 * - Required field validation
 * - Sample data preview
 * - Configuration save option
 */
function ImportMappingStep({
  csvColumns,
  entityFields,
  suggestedMapping,
  sampleRows,
  moduleName,
  entityName,
  onBack,
  onNext
}) {
  const [fieldMapping, setFieldMapping] = useState({});
  const [saveConfig, setSaveConfig] = useState(false);
  const [configName, setConfigName] = useState('');

  // Initialize field mapping with suggestions
  useEffect(() => {
    setFieldMapping(suggestedMapping || {});
  }, [suggestedMapping]);

  // Handle field mapping change
  const handleMappingChange = (csvColumn, entityField) => {
    setFieldMapping(prev => {
      const newMapping = { ...prev };
      if (entityField === '') {
        // Remove mapping (ignore column)
        delete newMapping[csvColumn];
      } else {
        newMapping[csvColumn] = entityField;
      }
      return newMapping;
    });
  };

  // Get mapping status for a CSV column
  const getMappingStatus = (csvColumn) => {
    const mappedField = fieldMapping[csvColumn];
    if (!mappedField) return 'unmapped';

    const field = entityFields.find(f => f.name === mappedField);
    if (field && field.required) return 'mapped-required';
    return 'mapped';
  };

  // Get unmapped required fields
  const getUnmappedRequiredFields = () => {
    const mappedFields = Object.values(fieldMapping);
    return entityFields.filter(
      field => field.required && !mappedFields.includes(field.name)
    );
  };

  // Get sample value for CSV column
  const getSampleValue = (csvColumn) => {
    if (!sampleRows || sampleRows.length === 0) return null;
    const value = sampleRows[0][csvColumn];
    if (value === null || value === undefined || value === '') return null;
    return String(value).length > 30 ? String(value).substring(0, 30) + '...' : value;
  };

  // Get CSS class for mapping row
  const getMappingRowClass = (csvColumn) => {
    const status = getMappingStatus(csvColumn);
    const mappedField = fieldMapping[csvColumn];

    if (!mappedField) {
      // Check if any required field is still unmapped
      const unmappedRequired = getUnmappedRequiredFields();
      return unmappedRequired.length > 0 ? 'unmapped-optional' : 'unmapped-optional';
    }

    const field = entityFields.find(f => f.name === mappedField);
    if (field && field.required) {
      return 'mapped';
    }

    return 'mapped';
  };

  const unmappedRequired = getUnmappedRequiredFields();
  const canProceed = unmappedRequired.length === 0;
  const canSaveConfig = saveConfig && configName.trim() !== '';

  const handleNext = () => {
    if (!canProceed) return;

    const result = {
      fieldMapping,
      saveConfig: canSaveConfig,
      configName: canSaveConfig ? configName.trim() : null
    };

    onNext(result);
  };

  return (
    <div className="mapping-step">
      {/* Instructions */}
      <div className="mapping-instructions">
        <p>
          <strong>Mappatura Campi:</strong> Associa ogni colonna del file CSV a un campo dell'entità.
          I campi obbligatori devono essere mappati per procedere.
        </p>
      </div>

      {/* Field Mappings */}
      <div className="field-mappings">
        {csvColumns.map((csvColumn, index) => {
          const mappedField = fieldMapping[csvColumn];
          const sampleValue = getSampleValue(csvColumn);

          return (
            <div key={index} className={`field-mapping-row ${getMappingRowClass(csvColumn)}`}>
              {/* CSV Column */}
              <div className="csv-column">
                <div className="csv-column-label">{csvColumn}</div>
                {sampleValue && (
                  <div className="csv-column-sample">Es: {sampleValue}</div>
                )}
              </div>

              {/* Arrow */}
              <div className="mapping-arrow">→</div>

              {/* Entity Field Selector */}
              <div className="entity-field-selector">
                <select
                  value={mappedField || ''}
                  onChange={(e) => handleMappingChange(csvColumn, e.target.value)}
                >
                  <option value="">-- Ignora questa colonna --</option>
                  {entityFields.map(field => (
                    <option key={field.name} value={field.name}>
                      {field.label || field.name}
                      {field.required && ' *'}
                      {field.type && ` (${field.type})`}
                    </option>
                  ))}
                </select>
                {mappedField && entityFields.find(f => f.name === mappedField)?.required && (
                  <span className="field-required-badge">Obbligatorio</span>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* Unmapped Required Fields Warning */}
      {unmappedRequired.length > 0 && (
        <div className="unmapped-required-warning">
          <div className="warning-icon">⚠️</div>
          <div className="warning-content">
            <h4>Campi obbligatori non mappati</h4>
            <p>I seguenti campi sono obbligatori e devono essere mappati:</p>
            <ul>
              {unmappedRequired.map(field => (
                <li key={field.name}>
                  <strong>{field.label || field.name}</strong>
                  {field.description && ` - ${field.description}`}
                </li>
              ))}
            </ul>
          </div>
        </div>
      )}

      {/* Save Configuration Section */}
      <div className="save-config-section">
        <div className="save-config-checkbox">
          <input
            type="checkbox"
            id="save-config-checkbox"
            checked={saveConfig}
            onChange={(e) => setSaveConfig(e.target.checked)}
          />
          <label htmlFor="save-config-checkbox">
            Salva questa configurazione per riutilizzarla in futuro
          </label>
        </div>

        {saveConfig && (
          <input
            type="text"
            className="config-name-input"
            placeholder="Nome configurazione (es: Import da Agenzia XYZ)"
            value={configName}
            onChange={(e) => setConfigName(e.target.value)}
          />
        )}
      </div>

      {/* Mapping Summary */}
      <div style={{
        background: '#f8f9fa',
        padding: '15px 20px',
        borderRadius: '8px',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        fontSize: '0.9rem',
        color: '#6c757d'
      }}>
        <div>
          <strong>{Object.keys(fieldMapping).length}</strong> colonne mappate su{' '}
          <strong>{csvColumns.length}</strong> totali
        </div>
        <div>
          <strong>{entityFields.filter(f => f.required).length}</strong> campi obbligatori
        </div>
      </div>

      {/* Action Buttons */}
      <div className="step-actions">
        <button
          className="btn-wizard btn-wizard-secondary"
          onClick={onBack}
        >
          ← Indietro
        </button>
        <button
          className="btn-wizard btn-wizard-primary"
          onClick={handleNext}
          disabled={!canProceed}
          title={!canProceed ? 'Mappa tutti i campi obbligatori per procedere' : ''}
        >
          Anteprima →
        </button>
      </div>
    </div>
  );
}

export default ImportMappingStep;
