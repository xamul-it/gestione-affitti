/**
 * DocumentoUpload Component
 *
 * Upload component for soggetto anagrafico documents.
 * Integrates with platform DocumentService and ScadenzarioService.
 */
import React, { useState, useEffect } from 'react';
import { getTipiDocumento } from '../../services/anagraficaAPI';
import axios from 'axios';
import './DocumentoUpload.css';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

const getAuthHeader = () => {
  const token = localStorage.getItem('access_token');
  return token ? { Authorization: `Bearer ${token}` } : {};
};

export const DocumentoUpload = ({ soggettoId, soggettoTipo, onUploadSuccess, onCancel }) => {
  const [tipiDocumento, setTipiDocumento] = useState([]);
  const [selectedFile, setSelectedFile] = useState(null);
  const [tipoDocumentoId, setTipoDocumentoId] = useState('');
  const [dataScadenza, setDataScadenza] = useState('');
  const [note, setNote] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [uploadProgress, setUploadProgress] = useState(0);

  useEffect(() => {
    loadTipiDocumento();
  }, []);

  const loadTipiDocumento = async () => {
    try {
      const data = await getTipiDocumento({ attivi_solo: true });
      setTipiDocumento(data);
    } catch (err) {
      console.error('Errore caricamento tipi documento:', err);
      setError('Errore nel caricamento dei tipi documento');
    }
  };

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      // Validate file size (max 50MB)
      const maxSize = 50 * 1024 * 1024; // 50MB
      if (file.size > maxSize) {
        setError('File troppo grande. Massimo 50MB consentiti.');
        return;
      }
      setSelectedFile(file);
      setError(null);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!selectedFile || !tipoDocumentoId) {
      setError('Seleziona un file e un tipo documento');
      return;
    }

    // Validate data scadenza if tipo requires it
    const selectedTipo = tipiDocumento.find(t => t.id === parseInt(tipoDocumentoId));
    if (selectedTipo?.richiede_scadenza && !dataScadenza) {
      setError(`Il tipo documento "${selectedTipo.nome}" richiede una data di scadenza`);
      return;
    }

    setLoading(true);
    setError(null);
    setUploadProgress(0);

    try {
      const formData = new FormData();
      formData.append('file', selectedFile);
      formData.append('soggetto_id', soggettoId);
      formData.append('tipo_documento_id', tipoDocumentoId);
      if (dataScadenza) formData.append('data_scadenza', dataScadenza);
      if (note) formData.append('note', note);

      const response = await axios.post(
        `${API_BASE_URL}/anagrafica/documenti/upload`,
        formData,
        {
          headers: {
            ...getAuthHeader(),
            'Content-Type': 'multipart/form-data'
          },
          onUploadProgress: (progressEvent) => {
            const percentCompleted = Math.round(
              (progressEvent.loaded * 100) / progressEvent.total
            );
            setUploadProgress(percentCompleted);
          }
        }
      );

      // Reset form
      setSelectedFile(null);
      setTipoDocumentoId('');
      setDataScadenza('');
      setNote('');
      setUploadProgress(0);
      e.target.reset();

      // Notify parent
      if (onUploadSuccess) {
        onUploadSuccess(response.data);
      }

    } catch (err) {
      console.error('Errore upload documento:', err);
      setError(err.response?.data?.detail || 'Errore durante il caricamento del documento');
      setUploadProgress(0);
    } finally {
      setLoading(false);
    }
  };

  const selectedTipo = tipiDocumento.find(t => t.id === parseInt(tipoDocumentoId));

  const filteredTipiDocumento = React.useMemo(() => {
    if (!soggettoTipo) return tipiDocumento;
    if (soggettoTipo === 'PERSONA_GIURIDICA') {
      return tipiDocumento.filter((tipo) => (
        tipo.categoria === 'aziendale' || tipo.categoria === 'altro' || !tipo.categoria
      ));
    }
    return tipiDocumento.filter((tipo) => tipo.categoria !== 'aziendale');
  }, [tipiDocumento, soggettoTipo]);

  // Get today's date for min date validation
  const today = new Date().toISOString().split('T')[0];

  return (
    <div className="documento-upload">
      <div className="upload-header">
        <h3>Carica Documento</h3>
        {onCancel && (
          <button type="button" onClick={onCancel} className="btn-close">
            ✕
          </button>
        )}
      </div>

      <form onSubmit={handleSubmit} className="upload-form">
        <div className="form-group">
          <label htmlFor="tipoDocumento">
            Tipo Documento <span className="required">*</span>
          </label>
          <select
            id="tipoDocumento"
            value={tipoDocumentoId}
            onChange={(e) => setTipoDocumentoId(e.target.value)}
            required
            disabled={loading}
          >
            <option value="">-- Seleziona tipo documento --</option>
            {filteredTipiDocumento.map(tipo => (
              <option key={tipo.id} value={tipo.id}>
                {tipo.nome}
                {tipo.categoria ? ` (${tipo.categoria})` : ''}
                {tipo.richiede_scadenza && ' (scadenza)'}
              </option>
            ))}
          </select>
          {selectedTipo && (
            <small className="tipo-info">
              {selectedTipo.descrizione}
            </small>
          )}
        </div>

        <div className="form-group">
          <label htmlFor="file">
            File <span className="required">*</span>
          </label>
          <div className="file-input-wrapper">
            <input
              type="file"
              id="file"
              onChange={handleFileChange}
              accept=".pdf,.jpg,.jpeg,.png,.doc,.docx,.xls,.xlsx,.txt"
              required
              disabled={loading}
            />
            {selectedFile && (
              <div className="file-info">
                <span className="file-name">{selectedFile.name}</span>
                <span className="file-size">
                  {(selectedFile.size / 1024).toFixed(1)} KB
                </span>
              </div>
            )}
          </div>
          <small className="help-text">
            Formati supportati: PDF, immagini (JPG, PNG), documenti Office. Max 50MB.
          </small>
        </div>

        {(selectedTipo?.richiede_scadenza || dataScadenza) && (
          <div className="form-group">
            <label htmlFor="dataScadenza">
              Data Scadenza
              {selectedTipo?.richiede_scadenza && <span className="required">*</span>}
            </label>
            <input
              type="date"
              id="dataScadenza"
              value={dataScadenza}
              onChange={(e) => setDataScadenza(e.target.value)}
              min={today}
              required={selectedTipo?.richiede_scadenza}
              disabled={loading}
            />
            {selectedTipo?.richiede_scadenza && (
              <small className="help-text warning">
                ⚠️ Questo tipo di documento richiede una data di scadenza
              </small>
            )}
          </div>
        )}

        <div className="form-group">
          <label htmlFor="note">Note</label>
          <textarea
            id="note"
            value={note}
            onChange={(e) => setNote(e.target.value)}
            rows={3}
            placeholder="Note aggiuntive sul documento..."
            disabled={loading}
          />
        </div>

        {error && (
          <div className="error-message">
            <span className="error-icon">⚠️</span>
            {error}
          </div>
        )}

        {loading && uploadProgress > 0 && (
          <div className="upload-progress">
            <div className="progress-bar">
              <div
                className="progress-fill"
                style={{ width: `${uploadProgress}%` }}
              />
            </div>
            <span className="progress-text">{uploadProgress}%</span>
          </div>
        )}

        <div className="form-actions">
          {onCancel && (
            <button
              type="button"
              onClick={onCancel}
              className="btn-cancel"
              disabled={loading}
            >
              Annulla
            </button>
          )}
          <button
            type="submit"
            disabled={loading || !selectedFile || !tipoDocumentoId}
            className="btn-submit"
          >
            {loading ? (
              <>
                <span className="spinner">⏳</span> Caricamento...
              </>
            ) : (
              <>
                <span>📤</span> Carica Documento
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  );
};

export default DocumentoUpload;
