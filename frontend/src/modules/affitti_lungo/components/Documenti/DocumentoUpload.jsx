import { useState } from 'react';
import { documentiAPI } from '../../services/affittiAPI';
import { formatApiError } from '../../../../utils/errorHandling';

const TIPI_DOCUMENTO = [
  { value: 'CERTIFICATO_ENERGETICO', label: 'Certificato Energetico' },
  { value: 'VISURA_CATASTALE', label: 'Visura Catastale' },
  { value: 'PLANIMETRIA', label: 'Planimetria' },
  { value: 'CONTRATTO_AFFITTO', label: 'Contratto Affitto' },
  { value: 'DOCUMENTO_IDENTITA', label: 'Documento Identità' },
  { value: 'CODICE_FISCALE', label: 'Codice Fiscale' },
  { value: 'FATTURA', label: 'Fattura' },
  { value: 'RICEVUTA_PAGAMENTO', label: 'Ricevuta Pagamento' },
  { value: 'PERIZIA', label: 'Perizia' },
  { value: 'FOTO', label: 'Foto' },
  { value: 'ALTRO', label: 'Altro' }
];

function DocumentoUpload({ entityType, entityId, onClose, onUploadComplete }) {
  const [file, setFile] = useState(null);
  const [tipoDocumento, setTipoDocumento] = useState('ALTRO');
  const [descrizione, setDescrizione] = useState('');
  const [note, setNote] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile) {
      // Verifica dimensione (max 50MB)
      if (selectedFile.size > 50 * 1024 * 1024) {
        setError('Il file è troppo grande (max 50MB)');
        return;
      }
      setFile(selectedFile);
      setError(null);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!file) {
      setError('Seleziona un file da caricare');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('entity_type', entityType);
      formData.append('entity_id', entityId);
      formData.append('tipo_documento', tipoDocumento);
      if (descrizione) formData.append('descrizione', descrizione);
      if (note) formData.append('note', note);

      await documentiAPI.upload(formData);
      onUploadComplete();
    } catch (err) {
      setError(formatApiError(err));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="modal-overlay">
      <div className="modal-content documento-upload-modal">
        <h3>Carica Documento</h3>

        {error && <div className="error-message">{error}</div>}

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label>File *</label>
            <input
              type="file"
              onChange={handleFileChange}
              required
              accept=".pdf,.doc,.docx,.jpg,.jpeg,.png,.xls,.xlsx"
            />
            {file && (
              <div className="file-info">
                📄 {file.name} ({(file.size / 1024).toFixed(1)} KB)
              </div>
            )}
          </div>

          <div className="form-group">
            <label>Tipo Documento *</label>
            <select
              value={tipoDocumento}
              onChange={(e) => setTipoDocumento(e.target.value)}
              required
            >
              {TIPI_DOCUMENTO.map(tipo => (
                <option key={tipo.value} value={tipo.value}>
                  {tipo.label}
                </option>
              ))}
            </select>
          </div>

          <div className="form-group">
            <label>Descrizione</label>
            <input
              type="text"
              value={descrizione}
              onChange={(e) => setDescrizione(e.target.value)}
              placeholder="Breve descrizione del documento"
            />
          </div>

          <div className="form-group">
            <label>Note</label>
            <textarea
              value={note}
              onChange={(e) => setNote(e.target.value)}
              rows="3"
              placeholder="Note aggiuntive"
            />
          </div>

          <div className="form-actions">
            <button
              type="button"
              onClick={onClose}
              className="btn btn-secondary"
              disabled={loading}
            >
              Annulla
            </button>
            <button
              type="submit"
              className="btn btn-primary"
              disabled={loading || !file}
            >
              {loading ? 'Caricamento...' : 'Carica'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default DocumentoUpload;
