import { useState } from 'react';
import ImportUploadStep from './ImportUploadStep';
import ImportMappingStep from './ImportMappingStep';
import ImportPreviewStep from './ImportPreviewStep';
import ImportResultsStep from './ImportResultsStep';
import './ImportWizard.css';

/**
 * ImportWizard - Multi-step import wizard with field mapping
 *
 * A complete import system that guides users through:
 * 1. File upload with template/generic CSV/saved config options
 * 2. Field mapping between CSV columns and entity fields
 * 3. Data preview with validation
 * 4. Import execution with detailed results
 *
 * @param {string} moduleName - Backend module name (e.g., "affitti_lungo")
 * @param {string} entityName - Entity name (e.g., "UnitaImmobiliare")
 * @param {string} entityLabel - User-friendly entity label (e.g., "Unità Immobiliari")
 * @param {function} onComplete - Callback when import completes successfully
 * @param {function} onCancel - Callback when user cancels the wizard
 */
function ImportWizard({ moduleName, entityName, entityLabel, onComplete, onCancel }) {
  // Wizard state
  const [currentStep, setCurrentStep] = useState(0);

  // Step data
  const [uploadedFile, setUploadedFile] = useState(null);
  const [csvColumns, setCsvColumns] = useState([]);
  const [entityFields, setEntityFields] = useState([]);
  const [fieldMapping, setFieldMapping] = useState({});
  const [suggestedMapping, setSuggestedMapping] = useState({});
  const [sampleRows, setSampleRows] = useState([]);
  const [previewData, setPreviewData] = useState(null);
  const [importResults, setImportResults] = useState(null);
  const [selectedConfigId, setSelectedConfigId] = useState(null);
  const [useTemplate, setUseTemplate] = useState(false);

  const steps = [
    { label: 'Upload', component: 'upload' },
    { label: 'Mapping', component: 'mapping' },
    { label: 'Preview', component: 'preview' },
    { label: 'Results', component: 'results' }
  ];

  // Navigation handlers
  const handleNext = () => {
    if (currentStep < steps.length - 1) {
      setCurrentStep(currentStep + 1);
    }
  };

  const handleBack = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1);
    }
  };

  const handleCancel = () => {
    if (onCancel) {
      onCancel();
    }
  };

  // Step 1: Upload complete
  const handleUploadComplete = (data) => {
    setUploadedFile(data.file);
    setCsvColumns(data.csvColumns);
    setEntityFields(data.entityFields);
    setSuggestedMapping(data.suggestedMapping);
    setFieldMapping(data.suggestedMapping || {});
    setSampleRows(data.sampleRows || []);
    setSelectedConfigId(data.configId);
    setUseTemplate(data.useTemplate);

    // If using template (no mapping needed), skip to preview
    if (data.useTemplate) {
      setCurrentStep(2); // Skip to preview
    } else {
      handleNext();
    }
  };

  // Step 2: Mapping complete
  const handleMappingComplete = (mapping) => {
    setFieldMapping(mapping);
    handleNext();
  };

  // Step 3: Preview complete (start import)
  const handlePreviewComplete = (preview) => {
    setPreviewData(preview);
    handleNext();
  };

  // Step 4: Import complete
  const handleImportComplete = (results) => {
    setImportResults(results);
    if (onComplete) {
      onComplete(results);
    }
  };

  // Restart wizard
  const handleStartOver = () => {
    setCurrentStep(0);
    setUploadedFile(null);
    setCsvColumns([]);
    setEntityFields([]);
    setFieldMapping({});
    setSuggestedMapping({});
    setSampleRows([]);
    setPreviewData(null);
    setImportResults(null);
    setSelectedConfigId(null);
    setUseTemplate(false);
  };

  return (
    <div className="import-wizard-overlay">
      <div className="import-wizard-container">
        {/* Header */}
        <div className="wizard-header">
          <h2 className="wizard-title">Importa {entityLabel}</h2>
          <button className="wizard-close" onClick={handleCancel} title="Chiudi">
            ×
          </button>
        </div>

        {/* Step Indicator */}
        <div className="wizard-steps">
          {steps.map((step, index) => (
            <div
              key={index}
              className={`wizard-step ${index === currentStep ? 'active' : ''} ${
                index < currentStep ? 'completed' : ''
              }`}
            >
              <div className="step-number">
                {index < currentStep ? '✓' : index + 1}
              </div>
              <div className="step-label">{step.label}</div>
            </div>
          ))}
        </div>

        {/* Step Content */}
        <div className="wizard-content">
          {currentStep === 0 && (
            <ImportUploadStep
              moduleName={moduleName}
              entityName={entityName}
              entityLabel={entityLabel}
              onNext={handleUploadComplete}
              onCancel={handleCancel}
            />
          )}

          {currentStep === 1 && (
            <ImportMappingStep
              csvColumns={csvColumns}
              entityFields={entityFields}
              suggestedMapping={suggestedMapping}
              sampleRows={sampleRows}
              moduleName={moduleName}
              entityName={entityName}
              onBack={handleBack}
              onNext={handleMappingComplete}
            />
          )}

          {currentStep === 2 && (
            <ImportPreviewStep
              file={uploadedFile}
              fieldMapping={useTemplate ? {} : fieldMapping}
              moduleName={moduleName}
              entityName={entityName}
              useTemplate={useTemplate}
              onBack={useTemplate ? () => setCurrentStep(0) : handleBack}
              onNext={handlePreviewComplete}
            />
          )}

          {currentStep === 3 && (
            <ImportResultsStep
              file={uploadedFile}
              fieldMapping={useTemplate ? {} : fieldMapping}
              previewData={previewData}
              moduleName={moduleName}
              entityName={entityName}
              useTemplate={useTemplate}
              onComplete={handleImportComplete}
              onStartOver={handleStartOver}
              onClose={handleCancel}
            />
          )}
        </div>
      </div>
    </div>
  );
}

export default ImportWizard;
