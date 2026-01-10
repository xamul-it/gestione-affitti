import { useState, useEffect } from 'react';
import { documentiAPI } from '../../services/affittiAPI';
import DocumentoUpload from './DocumentoUpload';
import './Documenti.css';

const TIPO_DOCUMENTO_LABELS = {
  CERTIFICATO_ENERGETICO: 'Certificato Energetico',
  VISURA_CATASTALE: 'Visura Catastale',
  PLANIMETRIA: 'Planimetria',
  CONTRATTO_AFFITTO: 'Contratto Affitto',
  DOCUMENTO_IDENTITA: 'Documento Identità',
  CODICE_FISCALE: 'Codice Fiscale',
  FATTURA: 'Fattura',
  RICEVUTA_PAGAMENTO: 'Ricevuta Pagamento',
  PERIZIA: 'Perizia',
  FOTO: 'Foto',
  ALTRO: 'Altro'
};

function DocumentiSection({ entityType, entityId }) {
  const [documenti, setDocumenti] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [showUpload, setShowUpload] = useState(false);

  useEffect(() => {
    if (entityId) {
      fetchDocumenti();
    }
  }, [entityId, entityType]);

  const fetchDocumenti = async () => {
    try {
      setLoading(true);
      const response = await documentiAPI.getAll(entityType, entityId);
      setDocumenti(response.data);
      setError(null);
    } catch (err) {
      setError('Errore nel caricamento dei documenti');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleDownload = async (doc) => {
    try {
      const response = await documentiAPI.download(doc.id);
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.download = doc.nome_file;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (err) {
      alert('Errore nel download del documento');
      console.error(err);
    }
  };

  const handleDelete = async (id) => {
    if (window.confirm('Sei sicuro di voler eliminare questo documento?')) {
      try {
        await documentiAPI.delete(id);
        fetchDocumenti();
      } catch (err) {
        alert('Errore nell\'eliminazione del documento');
        console.error(err);
      }
    }
  };

  const handleUploadComplete = () => {
    setShowUpload(false);
    fetchDocumenti();
  };

  const formatFileSize = (bytes) => {
    if (!bytes) return '-';
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('it-IT');
  };

  if (!entityId) {
    return (
      <div className="documenti-section">
        <p className="info-message">Salva prima l'entità per poter caricare documenti</p>
      </div>
    );
  }

  return (
    <div className="documenti-section">
      <div className="documenti-header">
        <h3>Documenti</h3>
        <button onClick={() => setShowUpload(true)} className="btn btn-sm btn-primary">
          + Carica Documento
        </button>
      </div>

      {showUpload && (
        <DocumentoUpload
          entityType={entityType}
          entityId={entityId}
          onClose={() => setShowUpload(false)}
          onUploadComplete={handleUploadComplete}
        />
      )}

      {error && <div className="error-message">{error}</div>}

      {loading ? (
        <div className="loading">Caricamento...</div>
      ) : documenti.length === 0 ? (
        <p className="no-data">Nessun documento caricato</p>
      ) : (
        <div className="documenti-list">
          {documenti.map((doc) => (
            <div key={doc.id} className="documento-card">
              <div className="documento-icon">
                📄
              </div>
              <div className="documento-info">
                <div className="documento-nome">{doc.nome_file}</div>
                <div className="documento-meta">
                  <span className="badge badge-info">
                    {TIPO_DOCUMENTO_LABELS[doc.tipo_documento] || doc.tipo_documento}
                  </span>
                  <span className="documento-size">{formatFileSize(doc.dimensione)}</span>
                  <span className="documento-date">{formatDate(doc.created_at)}</span>
                </div>
                {doc.descrizione && (
                  <div className="documento-descrizione">{doc.descrizione}</div>
                )}
              </div>
              <div className="documento-actions">
                <button
                  onClick={() => handleDownload(doc)}
                  className="btn btn-sm btn-secondary"
                  title="Download"
                >
                  ⬇
                </button>
                <button
                  onClick={() => handleDelete(doc.id)}
                  className="btn btn-sm btn-danger"
                  title="Elimina"
                >
                  🗑
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default DocumentiSection;
