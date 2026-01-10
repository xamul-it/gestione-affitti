/**
 * DocumentoList Component
 *
 * Display list of documents for a soggetto anagrafico with deadline tracking.
 * Shows expired, expiring soon, and upcoming documents with visual indicators.
 */
import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './DocumentoList.css';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

const getAuthHeader = () => {
  const token = localStorage.getItem('access_token');
  return token ? { Authorization: `Bearer ${token}` } : {};
};

export const DocumentoList = ({ soggettoId, onDocumentDeleted, refreshTrigger }) => {
  const [documenti, setDocumenti] = useState([]);
  const [scadenzario, setScadenzario] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [view, setView] = useState('all'); // 'all', 'expired', 'expiring', 'upcoming'
  const [deleteConfirm, setDeleteConfirm] = useState(null);

  useEffect(() => {
    loadDocumenti();
    loadScadenzario();
  }, [soggettoId, refreshTrigger]);

  const loadDocumenti = async () => {
    try {
      const response = await axios.get(
        `${API_BASE_URL}/anagrafica/documenti/soggetto/${soggettoId}`,
        { headers: getAuthHeader() }
      );
      setDocumenti(response.data);
      setError(null);
    } catch (err) {
      console.error('Errore caricamento documenti:', err);
      setError('Errore nel caricamento dei documenti');
    } finally {
      setLoading(false);
    }
  };

  const loadScadenzario = async () => {
    try {
      const response = await axios.get(
        `${API_BASE_URL}/anagrafica/documenti/scadenzario/soggetto/${soggettoId}`,
        { headers: getAuthHeader() }
      );
      setScadenzario(response.data);
    } catch (err) {
      console.error('Errore caricamento scadenzario:', err);
    }
  };

  const handleDownload = async (documentoId, nomeFile) => {
    try {
      const response = await axios.get(
        `${API_BASE_URL}/anagrafica/documenti/${documentoId}/download`,
        {
          headers: getAuthHeader(),
          responseType: 'blob'
        }
      );

      // Create download link
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', nomeFile);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error('Errore download documento:', err);
      alert('Errore durante il download del documento');
    }
  };

  const handleDelete = async (documentoId) => {
    try {
      await axios.delete(
        `${API_BASE_URL}/anagrafica/documenti/${documentoId}`,
        { headers: getAuthHeader() }
      );

      // Refresh lists
      loadDocumenti();
      loadScadenzario();
      setDeleteConfirm(null);

      if (onDocumentDeleted) {
        onDocumentDeleted(documentoId);
      }
    } catch (err) {
      console.error('Errore eliminazione documento:', err);
      alert('Errore durante l\'eliminazione del documento');
    }
  };

  const getScadenzaStatus = (doc) => {
    if (!doc.data_scadenza) return 'none';
    if (doc.is_scaduto) return 'expired';
    if (doc.days_to_expiry !== null && doc.days_to_expiry <= 30) return 'expiring';
    return 'upcoming';
  };

  const getScadenzaBadge = (doc) => {
    if (!doc.data_scadenza) return null;

    const status = getScadenzaStatus(doc);
    const daysText = doc.days_to_expiry !== null
      ? Math.abs(doc.days_to_expiry) === 1
        ? '1 giorno'
        : `${Math.abs(doc.days_to_expiry)} giorni`
      : '';

    const badges = {
      expired: (
        <span className="badge badge-expired">
          ⚠️ Scaduto ({daysText} fa)
        </span>
      ),
      expiring: (
        <span className="badge badge-expiring">
          ⏰ Scade tra {daysText}
        </span>
      ),
      upcoming: (
        <span className="badge badge-upcoming">
          📅 Scade tra {daysText}
        </span>
      )
    };

    return badges[status];
  };

  const getFilteredDocumenti = () => {
    if (view === 'all') return documenti;
    return documenti.filter(doc => getScadenzaStatus(doc) === view || (view === 'upcoming' && getScadenzaStatus(doc) === 'upcoming'));
  };

  const formatDate = (dateString) => {
    if (!dateString) return '-';
    return new Date(dateString).toLocaleDateString('it-IT', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  };

  const filteredDocumenti = getFilteredDocumenti();

  if (loading) {
    return <div className="documento-list-loading">Caricamento documenti...</div>;
  }

  return (
    <div className="documento-list">
      {/* Scadenzario Summary */}
      {scadenzario && (
        <div className="scadenzario-summary">
          <h4>📋 Riepilogo Scadenze</h4>
          <div className="summary-cards">
            <div
              className={`summary-card expired ${view === 'expired' ? 'active' : ''}`}
              onClick={() => setView('expired')}
            >
              <div className="card-value">{scadenzario.expired.length}</div>
              <div className="card-label">Scaduti</div>
            </div>
            <div
              className={`summary-card expiring ${view === 'expiring' ? 'active' : ''}`}
              onClick={() => setView('expiring')}
            >
              <div className="card-value">{scadenzario.expiring_soon.length}</div>
              <div className="card-label">In scadenza</div>
            </div>
            <div
              className={`summary-card upcoming ${view === 'upcoming' ? 'active' : ''}`}
              onClick={() => setView('upcoming')}
            >
              <div className="card-value">{scadenzario.upcoming.length}</div>
              <div className="card-label">Futuri</div>
            </div>
            <div
              className={`summary-card all ${view === 'all' ? 'active' : ''}`}
              onClick={() => setView('all')}
            >
              <div className="card-value">{documenti.length}</div>
              <div className="card-label">Totali</div>
            </div>
          </div>
        </div>
      )}

      {/* Documents List */}
      {error && <div className="error-message">{error}</div>}

      {filteredDocumenti.length === 0 ? (
        <div className="empty-state">
          <div className="empty-icon">📄</div>
          <p>
            {view === 'all'
              ? 'Nessun documento caricato'
              : view === 'expired'
              ? 'Nessun documento scaduto'
              : view === 'expiring'
              ? 'Nessun documento in scadenza'
              : 'Nessun documento futuro'}
          </p>
        </div>
      ) : (
        <div className="documenti-table">
          <table>
            <thead>
              <tr>
                <th>Tipo Documento</th>
                <th>Nome File</th>
                <th>Data Scadenza</th>
                <th>Stato</th>
                <th>Dimensione</th>
                <th>Caricato il</th>
                <th>Azioni</th>
              </tr>
            </thead>
            <tbody>
              {filteredDocumenti.map((doc) => (
                <tr key={doc.id} className={`doc-row ${getScadenzaStatus(doc)}`}>
                  <td className="tipo-col">
                    {doc.tipo_documento ? (
                      <div className="tipo-info">
                        <span className="tipo-nome">{doc.tipo_documento.nome}</span>
                        {doc.tipo_documento.categoria && (
                          <span className="tipo-categoria">
                            {doc.tipo_documento.categoria}
                          </span>
                        )}
                      </div>
                    ) : (
                      <span className="tipo-unknown">-</span>
                    )}
                  </td>
                  <td className="file-col">
                    <div className="file-info">
                      <span className="file-icon">📄</span>
                      <span className="file-name">{doc.nome_file}</span>
                    </div>
                    {doc.note && (
                      <div className="file-note">{doc.note}</div>
                    )}
                  </td>
                  <td className="scadenza-col">
                    {formatDate(doc.data_scadenza)}
                  </td>
                  <td className="status-col">
                    {getScadenzaBadge(doc)}
                  </td>
                  <td className="size-col">
                    {doc.dimensione
                      ? `${(doc.dimensione / 1024).toFixed(1)} KB`
                      : '-'}
                  </td>
                  <td className="date-col">
                    {formatDate(doc.created_at)}
                  </td>
                  <td className="actions-col">
                    <div className="actions">
                      <button
                        onClick={() => handleDownload(doc.id, doc.nome_file)}
                        className="btn-action btn-download"
                        title="Download"
                      >
                        📥
                      </button>
                      <button
                        onClick={() => setDeleteConfirm(doc.id)}
                        className="btn-action btn-delete"
                        title="Elimina"
                      >
                        🗑️
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Delete Confirmation Modal */}
      {deleteConfirm && (
        <div className="modal-overlay" onClick={() => setDeleteConfirm(null)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <h3>Conferma Eliminazione</h3>
            <p>Sei sicuro di voler eliminare questo documento?</p>
            <p className="warning-text">
              ⚠️ Questa azione non può essere annullata.
            </p>
            <div className="modal-actions">
              <button
                onClick={() => setDeleteConfirm(null)}
                className="btn-cancel"
              >
                Annulla
              </button>
              <button
                onClick={() => handleDelete(deleteConfirm)}
                className="btn-confirm-delete"
              >
                Elimina
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default DocumentoList;
