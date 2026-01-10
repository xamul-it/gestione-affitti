import { useState, useEffect, useRef } from 'react';
import { importExportAPI } from '../../../services/api';

/**
 * ImportUploadStep - Step 1: File Upload
 *
 * Allows users to:
 * 1. Use standard template (no mapping needed)
 * 2. Upload generic CSV (requires mapping)
 * 3. Load saved configuration
 */
function ImportUploadStep({ moduleName, entityName, entityLabel, onNext, onCancel }) {
  const [uploadMode, setUploadMode] = useState('generic'); // 'template', 'generic', 'saved'
  const [file, setFile] = useState(null);
  const [savedConfigs, setSavedConfigs] = useState([]);
  const [selectedConfigId, setSelectedConfigId] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [dragOver, setDragOver] = useState(false);
  const fileInputRef = useRef(null);

  // Load saved configurations on mount
  useEffect(() => {
    loadSavedConfigs();
  }, [moduleName, entityName]);

  const loadSavedConfigs = async () => {
    try {
      const response = await importExportAPI.getImportConfigurations(moduleName, entityName);
      setSavedConfigs(response.data.configurations || []);
    } catch (err) {
      console.error('Error loading saved configurations:', err);
      // Not critical error, continue without saved configs
    }
  };

  const handleFileSelect = (selectedFile) => {
    // Validate file type
    if (!selectedFile.name.match(/\.(csv|xlsx|xls)$/i)) {
      setError('Per favore seleziona un file CSV o Excel (.csv, .xlsx, .xls)');
      return;
    }

    // Validate file size (10MB limit)
    const maxSize = 10 * 1024 * 1024; // 10MB
    if (selectedFile.size > maxSize) {
      setError('Il file è troppo grande. Dimensione massima: 10MB');
      return;
    }

    setFile(selectedFile);
    setError(null);
  };

  const handleFileInputChange = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile) {
      handleFileSelect(selectedFile);
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    setDragOver(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    setDragOver(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setDragOver(false);

    const droppedFile = e.dataTransfer.files[0];
    if (droppedFile) {
      handleFileSelect(droppedFile);
    }
  };

  const handleRemoveFile = () => {
    setFile(null);
    setError(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const handleAnalyzeFile = async () => {
    if (!file) {
      setError('Per favore seleziona un file');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      if (uploadMode === 'template') {
        // Template mode - no analysis needed, skip to preview
        onNext({
          file,
          useTemplate: true,
          csvColumns: [],
          entityFields: [],
          suggestedMapping: {},
          sampleRows: []
        });
      } else if (uploadMode === 'saved' && selectedConfigId) {
        // Load saved configuration
        const configResponse = await importExportAPI.getImportConfiguration(selectedConfigId);
        const config = configResponse.data;

        // Analyze file to get columns and validate
        const analysisResponse = await importExportAPI.analyzeCSV(moduleName, entityName, file);
        const analysis = analysisResponse.data;

        // Use saved field mapping
        onNext({
          file,
          useTemplate: false,
          csvColumns: analysis.csv_columns,
          entityFields: analysis.entity_fields,
          suggestedMapping: config.field_mapping,
          sampleRows: analysis.sample_rows || [],
          configId: selectedConfigId
        });
      } else {
        // Generic CSV - analyze and suggest mapping
        const response = await importExportAPI.analyzeCSV(moduleName, entityName, file);
        const analysis = response.data;

        onNext({
          file,
          useTemplate: false,
          csvColumns: analysis.csv_columns,
          entityFields: analysis.entity_fields,
          suggestedMapping: analysis.suggested_mapping || {},
          sampleRows: analysis.sample_rows || []
        });
      }
    } catch (err) {
      console.error('Error analyzing file:', err);
      setError(
        err.response?.data?.detail ||
        'Errore durante l\'analisi del file. Verifica che il formato sia corretto.'
      );
    } finally {
      setLoading(false);
    }
  };

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
  };

  const canProceed = file && (uploadMode !== 'saved' || selectedConfigId);

  return (
    <div className="upload-step">
      {/* Upload Mode Selector */}
      <div className="upload-mode-selector">
        <h3 style={{ marginTop: 0, marginBottom: 15, color: '#2c3e50' }}>
          Modalità di Importazione
        </h3>

        {/* Template Mode */}
        <div
          className={`upload-mode-option ${uploadMode === 'template' ? 'selected' : ''}`}
          onClick={() => setUploadMode('template')}
        >
          <input
            type="radio"
            name="uploadMode"
            value="template"
            checked={uploadMode === 'template'}
            onChange={(e) => setUploadMode(e.target.value)}
          />
          <div className="upload-mode-content">
            <div className="upload-mode-title">Usa Template Standard</div>
            <p className="upload-mode-description">
              Il file CSV segue il template standard dell'applicazione.
              Non è necessaria la mappatura dei campi.
            </p>
          </div>
        </div>

        {/* Generic CSV Mode */}
        <div
          className={`upload-mode-option ${uploadMode === 'generic' ? 'selected' : ''}`}
          onClick={() => setUploadMode('generic')}
        >
          <input
            type="radio"
            name="uploadMode"
            value="generic"
            checked={uploadMode === 'generic'}
            onChange={(e) => setUploadMode(e.target.value)}
          />
          <div className="upload-mode-content">
            <div className="upload-mode-title">Carica CSV Generico</div>
            <p className="upload-mode-description">
              Il file ha un formato personalizzato. Sarà necessario mappare le colonne
              del file sui campi dell'entità.
            </p>
          </div>
        </div>

        {/* Saved Config Mode */}
        {savedConfigs.length > 0 && (
          <div
            className={`upload-mode-option ${uploadMode === 'saved' ? 'selected' : ''}`}
            onClick={() => setUploadMode('saved')}
          >
            <input
              type="radio"
              name="uploadMode"
              value="saved"
              checked={uploadMode === 'saved'}
              onChange={(e) => setUploadMode(e.target.value)}
            />
            <div className="upload-mode-content">
              <div className="upload-mode-title">Usa Configurazione Salvata</div>
              <p className="upload-mode-description">
                Riutilizza una configurazione di mappatura precedentemente salvata.
              </p>

              {uploadMode === 'saved' && (
                <div className="saved-config-selector" onClick={(e) => e.stopPropagation()}>
                  <label htmlFor="config-select">Seleziona configurazione:</label>
                  <select
                    id="config-select"
                    value={selectedConfigId}
                    onChange={(e) => setSelectedConfigId(e.target.value)}
                  >
                    <option value="">-- Seleziona --</option>
                    {savedConfigs.map(config => (
                      <option key={config.id} value={config.id}>
                        {config.name} (creata il {new Date(config.created_at).toLocaleDateString()})
                      </option>
                    ))}
                  </select>
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      {/* File Upload Area */}
      <div
        className={`upload-area ${file ? 'has-file' : ''} ${dragOver ? 'drag-over' : ''}`}
        onClick={() => !file && fileInputRef.current?.click()}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".csv,.xlsx,.xls"
          onChange={handleFileInputChange}
          style={{ display: 'none' }}
        />

        {!file ? (
          <div className="upload-prompt">
            <div className="upload-icon">📁</div>
            <p className="upload-text">
              Clicca per selezionare o trascina qui il file
            </p>
            <p className="upload-hint">
              Formati supportati: CSV, Excel (.csv, .xlsx, .xls) - Max 10MB
            </p>
          </div>
        ) : (
          <div className="file-selected">
            <div className="file-icon">📄</div>
            <div className="file-info">
              <div className="file-name">{file.name}</div>
              <div className="file-size">{formatFileSize(file.size)}</div>
            </div>
            <button
              className="btn-remove-file"
              onClick={(e) => {
                e.stopPropagation();
                handleRemoveFile();
              }}
              title="Rimuovi file"
            >
              ×
            </button>
          </div>
        )}
      </div>

      {/* Error Message */}
      {error && (
        <div className="error-message">
          <div className="error-message-icon">⚠️</div>
          <div>{error}</div>
        </div>
      )}

      {/* Action Buttons */}
      <div className="step-actions">
        <button
          className="btn-wizard btn-wizard-secondary"
          onClick={onCancel}
          disabled={loading}
        >
          Annulla
        </button>
        <button
          className="btn-wizard btn-wizard-primary"
          onClick={handleAnalyzeFile}
          disabled={!canProceed || loading}
        >
          {loading ? (
            <>
              <span className="spinner" style={{
                width: 16,
                height: 16,
                border: '2px solid white',
                borderTopColor: 'transparent'
              }}></span>
              Analisi in corso...
            </>
          ) : (
            <>
              Analizza File →
            </>
          )}
        </button>
      </div>
    </div>
  );
}

export default ImportUploadStep;
