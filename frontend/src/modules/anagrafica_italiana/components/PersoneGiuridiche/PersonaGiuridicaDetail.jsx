import { useState, useEffect } from 'react';
import { useParams, Link, useNavigate, useLocation } from 'react-router-dom';
import { getSoggettoById, deleteSoggetto } from '../../services/anagraficaAPI';
import { DocumentoUpload, DocumentoList, DocumentoParsingPending } from '../Documenti';
import RuoliAziendaSection from '../RuoliAzienda/RuoliAziendaSection';
import { renderIcon } from '../../../../components/Navigation/iconRegistry.jsx';
import '../SoggettiAnagrafici/SoggettoDetail.css';

/**
 * PersonaGiuridicaDetail - Scheda dettaglio persona giuridica
 *
 * Vista ottimizzata per persone giuridiche (aziende, società) con campi specifici:
 * - Ragione Sociale, Forma Giuridica
 * - P.IVA e Codice Fiscale aziendale
 * - Nota informativa: le persone giuridiche NON possono avere account utente
 */
function PersonaGiuridicaDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const location = useLocation();
  const [azienda, setAzienda] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('anagrafica');
  const [showUpload, setShowUpload] = useState(false);
  const [refreshDocumenti, setRefreshDocumenti] = useState(0);

  useEffect(() => {
    loadAzienda();
  }, [id]);

  useEffect(() => {
    const params = new URLSearchParams(location.search);
    const tab = params.get('tab');
    if (tab) {
      setActiveTab(tab);
    }
  }, [location.search]);

  const loadAzienda = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await getSoggettoById(id);

      // Verifica che sia effettivamente una persona giuridica
      if (data.tipo_soggetto !== 'PERSONA_GIURIDICA') {
        setError('Questo soggetto non è una persona giuridica');
        return;
      }

      setAzienda(data);
    } catch (err) {
      console.error('Error loading azienda:', err);
      setError('Errore nel caricamento della persona giuridica');
    } finally {
      setLoading(false);
    }
  };

  const handleUploadSuccess = () => {
    setShowUpload(false);
    setRefreshDocumenti(prev => prev + 1);
  };

  const handleDocumentDeleted = () => {
    setRefreshDocumenti(prev => prev + 1);
  };

  const handleDelete = async () => {
    if (!confirm('Sei sicuro di voler eliminare questa azienda/ente?')) {
      return;
    }

    try {
      await deleteSoggetto(id);
      navigate('/anagrafiche/persone-giuridiche');
    } catch (err) {
      console.error('Error deleting azienda:', err);
      alert('Errore nell\'eliminazione dell\'azienda/ente');
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return '-';
    return new Date(dateString).toLocaleDateString('it-IT');
  };

  if (loading) {
    return (
      <div className="soggetto-detail-container">
        <div className="loading">Caricamento persona giuridica...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="soggetto-detail-container">
        <div className="error">{error}</div>
        <Link to="/anagrafiche/persone-giuridiche" className="btn btn-secondary">
          Torna all'elenco
        </Link>
      </div>
    );
  }

  if (!azienda) {
    return (
      <div className="soggetto-detail-container">
        <div className="error">Persona giuridica non trovata</div>
        <Link to="/anagrafiche/persone-giuridiche" className="btn btn-secondary">
          Torna all'elenco
        </Link>
      </div>
    );
  }

  return (
    <div className="soggetto-detail-container">
      {/* Breadcrumb */}
      <div className="breadcrumb">
        <Link to="/anagrafiche/persone-giuridiche">Persone Giuridiche</Link>
        <span className="separator">/</span>
        <span className="current">{azienda.ragione_sociale || '(Non specificato)'}</span>
      </div>

      {/* Header */}
      <div className="soggetto-detail-header">
        <div className="header-title">
          {renderIcon('building', { size: 30, className: 'detail-icon', fallbackClassName: 'nav-emoji-icon' })}
          <h1>{azienda.ragione_sociale || '(Non specificato)'}</h1>
          <span className={`status-badge ${azienda.attivo ? 'active' : 'inactive'}`}>
            {azienda.attivo ? 'Attivo' : 'Inattivo'}
          </span>
        </div>
        <div className="header-actions">
          <Link
            to={`/anagrafiche/persone-giuridiche/${azienda.id}/modifica`}
            className="btn btn-primary"
          >
            <span className="button-icon">
              {renderIcon('pencil', { size: 16, className: 'detail-icon', fallbackClassName: 'nav-emoji-icon' })}
            </span>
            Modifica
          </Link>
          <button onClick={handleDelete} className="btn btn-danger">
            <span className="button-icon">
              {renderIcon('trash', { size: 16, className: 'detail-icon', fallbackClassName: 'nav-emoji-icon' })}
            </span>
            Elimina
          </button>
        </div>
      </div>

      {/* Tabs Navigation */}
      <div className="detail-tabs">
        <button
          className={`tab ${activeTab === 'anagrafica' ? 'active' : ''}`}
          onClick={() => setActiveTab('anagrafica')}
        >
          <span className="tab-icon">
            {renderIcon('list', { size: 16, className: 'detail-icon', fallbackClassName: 'nav-emoji-icon' })}
          </span>
          Dati Anagrafici
        </button>
        <button
          className={`tab ${activeTab === 'ruoli-azienda' ? 'active' : ''}`}
          onClick={() => setActiveTab('ruoli-azienda')}
        >
          <span className="tab-icon">
            {renderIcon('users', { size: 16, className: 'detail-icon', fallbackClassName: 'nav-emoji-icon' })}
          </span>
          Persone
        </button>
        <button
          className={`tab ${activeTab === 'documenti' ? 'active' : ''}`}
          onClick={() => setActiveTab('documenti')}
        >
          <span className="tab-icon">
            {renderIcon('file-text', { size: 16, className: 'detail-icon', fallbackClassName: 'nav-emoji-icon' })}
          </span>
          Documenti
        </button>
      </div>

      {/* Tab Content */}
      <div className="soggetto-detail-content">
        {/* Tab: Anagrafica */}
        {activeTab === 'anagrafica' && (
          <div className="tab-content tab-anagrafica">
            {/* Info importante - Persone giuridiche non possono avere account */}
            <div className="info-note" style={{
              marginBottom: '20px',
              padding: '12px 16px',
              backgroundColor: '#fff3cd',
              borderLeft: '4px solid #ffc107',
              color: '#856404'
            }}>
              <span className="inline-icon">
                {renderIcon('info', { size: 16, className: 'detail-icon', fallbackClassName: 'nav-emoji-icon' })}
              </span>
              <strong>Nota:</strong> Le persone giuridiche (aziende, società) <strong>non possono avere account utente</strong>.
              Per accedere al sistema, crea un account per una persona fisica che rappresenta l'azienda.
            </div>

            {/* Dati Anagrafici */}
            <div className="detail-section">
              <h2>Dati Anagrafici</h2>
              <div className="detail-grid">
                <div className="detail-field">
                  <label>Tipo Soggetto</label>
                  <div className="field-value">
                    <span className="inline-icon">
                      {renderIcon('building', { size: 16, className: 'detail-icon', fallbackClassName: 'nav-emoji-icon' })}
                    </span>
                    Persona Giuridica
                  </div>
                </div>
                <div className="detail-field">
                  <label>Ragione Sociale</label>
                  <div className="field-value">{azienda.ragione_sociale || '-'}</div>
                </div>
                <div className="detail-field">
                  <label>Forma Giuridica</label>
                  <div className="field-value">{azienda.forma_giuridica || '-'}</div>
                </div>
              </div>
            </div>

            {/* Identificativi Fiscali */}
            <div className="detail-section">
              <h2>Identificativi Fiscali</h2>
              <div className="detail-grid">
                <div className="detail-field">
                  <label>Partita IVA</label>
                  <div className="field-value">
                    {azienda.partita_iva ? (
                      <code className="piva-badge">{azienda.partita_iva}</code>
                    ) : (
                      '-'
                    )}
                  </div>
                </div>
                <div className="detail-field">
                  <label>Codice Fiscale</label>
                  <div className="field-value">
                    {azienda.codice_fiscale ? (
                      <code className="cf-badge">{azienda.codice_fiscale}</code>
                    ) : (
                      '-'
                    )}
                  </div>
                </div>
              </div>
            </div>

            {/* Contatti */}
            <div className="detail-section">
              <h2>Contatti</h2>
              <div className="detail-grid">
                <div className="detail-field">
                  <label>Email</label>
                  <div className="field-value">
                    {azienda.email ? (
                      <a href={`mailto:${azienda.email}`}>{azienda.email}</a>
                    ) : (
                      '-'
                    )}
                  </div>
                </div>
                <div className="detail-field">
                  <label>PEC</label>
                  <div className="field-value">
                    {azienda.pec ? <a href={`mailto:${azienda.pec}`}>{azienda.pec}</a> : '-'}
                  </div>
                </div>
                <div className="detail-field">
                  <label>Telefono</label>
                  <div className="field-value">{azienda.telefono || '-'}</div>
                </div>
                <div className="detail-field">
                  <label>Cellulare</label>
                  <div className="field-value">{azienda.cellulare || '-'}</div>
                </div>
              </div>
            </div>

            {/* Sede Legale */}
            <div className="detail-section">
              <h2>Sede Legale</h2>
              <div className="detail-grid">
                <div className="detail-field full-width">
                  <label>Indirizzo</label>
                  <div className="field-value">{azienda.indirizzo || '-'}</div>
                </div>
                <div className="detail-field">
                  <label>Città</label>
                  <div className="field-value">{azienda.citta || '-'}</div>
                </div>
                <div className="detail-field">
                  <label>Provincia</label>
                  <div className="field-value">{azienda.provincia || '-'}</div>
                </div>
                <div className="detail-field">
                  <label>CAP</label>
                  <div className="field-value">{azienda.cap || '-'}</div>
                </div>
                <div className="detail-field">
                  <label>Nazione</label>
                  <div className="field-value">{azienda.nazione || 'Italia'}</div>
                </div>
              </div>
            </div>

            {/* Note */}
            {azienda.note && (
              <div className="detail-section">
                <h2>Note</h2>
                <div className="note-content">{azienda.note}</div>
              </div>
            )}

            {/* Metadati */}
            <div className="detail-section metadata">
              <h2>Informazioni di Sistema</h2>
              <div className="detail-grid">
                <div className="detail-field">
                  <label>ID</label>
                  <div className="field-value">{azienda.id}</div>
                </div>
                <div className="detail-field">
                  <label>Creato il</label>
                  <div className="field-value">{formatDate(azienda.created_at)}</div>
                </div>
                <div className="detail-field">
                  <label>Ultima modifica</label>
                  <div className="field-value">{formatDate(azienda.updated_at)}</div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Tab: Persone Associate */}
        {activeTab === 'ruoli-azienda' && (
          <div className="tab-content tab-ruoli-azienda">
            <RuoliAziendaSection
              soggetto={azienda}
              onUpdate={loadAzienda}
            />
          </div>
        )}

        {/* Tab: Documenti */}
        {activeTab === 'documenti' && (
          <div className="tab-content tab-documenti">
            <div className="tab-header">
              <h2>
                <span className="tab-icon">
                  {renderIcon('file-text', { size: 18, className: 'detail-icon', fallbackClassName: 'nav-emoji-icon' })}
                </span>
                Gestione Documenti
              </h2>
              {!showUpload && (
                <button
                  onClick={() => setShowUpload(true)}
                  className="btn btn-primary"
                >
                  <span className="button-icon">
                    {renderIcon('plus', { size: 16, className: 'detail-icon', fallbackClassName: 'nav-emoji-icon' })}
                  </span>
                  Carica Documento
                </button>
              )}
            </div>

            {showUpload && (
              <div className="upload-section">
                <DocumentoUpload
                  soggettoId={parseInt(id)}
                  soggettoTipo={azienda?.tipo_soggetto}
                  onUploadSuccess={handleUploadSuccess}
                  onCancel={() => setShowUpload(false)}
                />
              </div>
            )}

            <div className="documents-section">
              <DocumentoParsingPending
                soggettoId={parseInt(id)}
                onCompleted={() => {
                  setRefreshDocumenti(prev => prev + 1);
                  loadAzienda();
                }}
              />
              <DocumentoList
                soggettoId={parseInt(id)}
                onDocumentDeleted={handleDocumentDeleted}
                refreshTrigger={refreshDocumenti}
              />
            </div>
          </div>
        )}

      </div>

      {/* Footer */}
      <div className="soggetto-detail-footer">
        <Link to="/anagrafiche/persone-giuridiche" className="btn btn-secondary">
          <span className="button-icon">
            {renderIcon('list', { size: 16, className: 'detail-icon', fallbackClassName: 'nav-emoji-icon' })}
          </span>
          Torna all'elenco persone giuridiche
        </Link>
      </div>
    </div>
  );
}

export default PersonaGiuridicaDetail;
