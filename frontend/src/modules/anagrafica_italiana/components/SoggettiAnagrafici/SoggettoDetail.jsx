import { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { getSoggettoById, deleteSoggetto, getSoggettoRuoli } from '../../services/anagraficaAPI';
import { DocumentoUpload, DocumentoList } from '../Documenti';
import RuoliAziendaSection from '../RuoliAzienda/RuoliAziendaSection';
import './SoggettoDetail.css';

/**
 * SoggettoDetail - Scheda dettaglio anagrafica
 *
 * Visualizza tutti i dati di un soggetto anagrafico con tab:
 * - Anagrafica: dati personali/aziendali
 * - Documenti: gestione documenti con scadenzario
 * - Ruoli: ruoli business assegnati
 */
function SoggettoDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [soggetto, setSoggetto] = useState(null);
  const [ruoli, setRuoli] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('anagrafica');
  const [showUpload, setShowUpload] = useState(false);
  const [refreshDocumenti, setRefreshDocumenti] = useState(0);

  useEffect(() => {
    loadSoggetto();
    loadRuoli();
  }, [id]);

  const loadSoggetto = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await getSoggettoById(id);
      setSoggetto(data);
    } catch (err) {
      console.error('Error loading soggetto:', err);
      setError('Errore nel caricamento dell\'anagrafica');
    } finally {
      setLoading(false);
    }
  };

  const loadRuoli = async () => {
    try {
      const data = await getSoggettoRuoli(id);
      setRuoli(data);
    } catch (err) {
      console.error('Error loading ruoli:', err);
      // Non bloccare il rendering se i ruoli falliscono
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
    if (!confirm('Sei sicuro di voler eliminare questa anagrafica?')) {
      return;
    }

    try {
      await deleteSoggetto(id);
      navigate('/anagrafiche');
    } catch (err) {
      console.error('Error deleting soggetto:', err);
      alert('Errore nell\'eliminazione dell\'anagrafica');
    }
  };

  const getTipoLabel = (tipo) => {
    return tipo === 'PERSONA_FISICA' ? 'Persona Fisica' : 'Persona Giuridica';
  };

  const getTipoIcon = (tipo) => {
    return tipo === 'PERSONA_FISICA' ? '👤' : '🏢';
  };

  const formatDate = (dateString) => {
    if (!dateString) return '-';
    return new Date(dateString).toLocaleDateString('it-IT');
  };

  if (loading) {
    return (
      <div className="soggetto-detail-container">
        <div className="loading">Caricamento anagrafica...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="soggetto-detail-container">
        <div className="error">{error}</div>
        <Link to="/anagrafiche" className="btn btn-secondary">
          Torna all'elenco
        </Link>
      </div>
    );
  }

  if (!soggetto) {
    return (
      <div className="soggetto-detail-container">
        <div className="error">Anagrafica non trovata</div>
        <Link to="/anagrafiche" className="btn btn-secondary">
          Torna all'elenco
        </Link>
      </div>
    );
  }

  return (
    <div className="soggetto-detail-container">
      {/* Breadcrumb */}
      <div className="breadcrumb">
        <Link to="/anagrafiche">Anagrafiche</Link>
        <span className="separator">/</span>
        <span className="current">
          {soggetto.tipo_soggetto === 'PERSONA_FISICA'
            ? `${soggetto.nome || ''} ${soggetto.cognome || ''}`
            : soggetto.ragione_sociale || ''}
        </span>
      </div>

      {/* Header */}
      <div className="soggetto-detail-header">
        <div className="header-title">
          <span className="tipo-icon">{getTipoIcon(soggetto.tipo_soggetto)}</span>
          <h1>
            {soggetto.tipo_soggetto === 'PERSONA_FISICA'
              ? `${soggetto.nome || ''} ${soggetto.cognome || ''}`
              : soggetto.ragione_sociale || ''}
          </h1>
          <span className={`status-badge ${soggetto.attivo ? 'active' : 'inactive'}`}>
            {soggetto.attivo ? 'Attivo' : 'Inattivo'}
          </span>
        </div>
        <div className="header-actions">
          <Link
            to={`/anagrafiche/${soggetto.id}/modifica`}
            className="btn btn-primary"
          >
            ✏️ Modifica
          </Link>
          <button onClick={handleDelete} className="btn btn-danger">
            🗑️ Elimina
          </button>
        </div>
      </div>

      {/* Tabs Navigation */}
      <div className="detail-tabs">
        <button
          className={`tab ${activeTab === 'anagrafica' ? 'active' : ''}`}
          onClick={() => setActiveTab('anagrafica')}
        >
          📋 Dati Anagrafici
        </button>
        <button
          className={`tab ${activeTab === 'ruoli-azienda' ? 'active' : ''}`}
          onClick={() => setActiveTab('ruoli-azienda')}
          style={{backgroundColor: '#ff6b6b', color: 'white'}}
        >
          {soggetto.tipo_soggetto === 'PERSONA_FISICA' ? '🏢 Aziende (NUOVO!)' : '👥 Persone (NUOVO!)'}
        </button>
        <button
          className={`tab ${activeTab === 'documenti' ? 'active' : ''}`}
          onClick={() => setActiveTab('documenti')}
        >
          📄 Documenti
        </button>
        <button
          className={`tab ${activeTab === 'ruoli' ? 'active' : ''}`}
          onClick={() => setActiveTab('ruoli')}
        >
          🎭 Ruoli {ruoli.length > 0 && `(${ruoli.length})`}
        </button>
      </div>

      {/* Tab Content */}
      <div className="soggetto-detail-content">
        {/* Tab: Anagrafica */}
        {activeTab === 'anagrafica' && (
        <div className="tab-content tab-anagrafica">
        {/* Dati Anagrafici */}
        <div className="detail-section">
          <h2>Dati Anagrafici</h2>
          <div className="detail-grid">
            <div className="detail-field">
              <label>Tipo Soggetto</label>
              <div className="field-value">
                {getTipoIcon(soggetto.tipo_soggetto)} {getTipoLabel(soggetto.tipo_soggetto)}
              </div>
            </div>

            {soggetto.tipo_soggetto === 'PERSONA_FISICA' ? (
              <>
                <div className="detail-field">
                  <label>Nome</label>
                  <div className="field-value">{soggetto.nome || '-'}</div>
                </div>
                <div className="detail-field">
                  <label>Cognome</label>
                  <div className="field-value">{soggetto.cognome || '-'}</div>
                </div>
                <div className="detail-field">
                  <label>Data di Nascita</label>
                  <div className="field-value">{formatDate(soggetto.data_nascita)}</div>
                </div>
                <div className="detail-field">
                  <label>Luogo di Nascita</label>
                  <div className="field-value">{soggetto.luogo_nascita || '-'}</div>
                </div>
              </>
            ) : (
              <>
                <div className="detail-field">
                  <label>Ragione Sociale</label>
                  <div className="field-value">{soggetto.ragione_sociale || '-'}</div>
                </div>
                <div className="detail-field">
                  <label>Forma Giuridica</label>
                  <div className="field-value">{soggetto.forma_giuridica || '-'}</div>
                </div>
              </>
            )}

            <div className="detail-field">
              <label>Codice Fiscale</label>
              <div className="field-value">{soggetto.codice_fiscale || '-'}</div>
            </div>
            <div className="detail-field">
              <label>Partita IVA</label>
              <div className="field-value">{soggetto.partita_iva || '-'}</div>
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
                {soggetto.email ? (
                  <a href={`mailto:${soggetto.email}`}>{soggetto.email}</a>
                ) : (
                  '-'
                )}
              </div>
            </div>
            <div className="detail-field">
              <label>PEC</label>
              <div className="field-value">
                {soggetto.pec ? <a href={`mailto:${soggetto.pec}`}>{soggetto.pec}</a> : '-'}
              </div>
            </div>
            <div className="detail-field">
              <label>Telefono</label>
              <div className="field-value">{soggetto.telefono || '-'}</div>
            </div>
            <div className="detail-field">
              <label>Cellulare</label>
              <div className="field-value">{soggetto.cellulare || '-'}</div>
            </div>
          </div>
        </div>

        {/* Indirizzo */}
        <div className="detail-section">
          <h2>Indirizzo</h2>
          <div className="detail-grid">
            <div className="detail-field full-width">
              <label>Indirizzo</label>
              <div className="field-value">{soggetto.indirizzo || '-'}</div>
            </div>
            <div className="detail-field">
              <label>Città</label>
              <div className="field-value">{soggetto.citta || '-'}</div>
            </div>
            <div className="detail-field">
              <label>Provincia</label>
              <div className="field-value">{soggetto.provincia || '-'}</div>
            </div>
            <div className="detail-field">
              <label>CAP</label>
              <div className="field-value">{soggetto.cap || '-'}</div>
            </div>
            <div className="detail-field">
              <label>Nazione</label>
              <div className="field-value">{soggetto.nazione || 'Italia'}</div>
            </div>
          </div>
        </div>


        {/* Accesso Sistema */}
        {soggetto.user_id && (
          <div className="detail-section">
            <h2>Accesso al Sistema</h2>
            <div className="detail-grid">
              <div className="detail-field">
                <label>Utente collegato</label>
                <div className="field-value">
                  ✅ Questo soggetto ha accesso al sistema (User ID: {soggetto.user_id})
                </div>
              </div>
              <div className="detail-field">
                <label>Username</label>
                <div className="field-value">{soggetto.email}</div>
              </div>
            </div>
          </div>
        )}

        {/* Note */}
        {soggetto.note && (
          <div className="detail-section">
            <h2>Note</h2>
            <div className="note-content">{soggetto.note}</div>
          </div>
        )}

        {/* Metadati */}
        <div className="detail-section metadata">
          <h2>Informazioni di Sistema</h2>
          <div className="detail-grid">
            <div className="detail-field">
              <label>ID</label>
              <div className="field-value">{soggetto.id}</div>
            </div>
            <div className="detail-field">
              <label>Creato il</label>
              <div className="field-value">{formatDate(soggetto.created_at)}</div>
            </div>
            <div className="detail-field">
              <label>Ultima modifica</label>
              <div className="field-value">{formatDate(soggetto.updated_at)}</div>
            </div>
          </div>
        </div>
        </div>
        )}

        {/* Tab: Ruoli Azienda */}
        {activeTab === 'ruoli-azienda' && (
          <div className="tab-content tab-ruoli-azienda">
            <RuoliAziendaSection
              soggetto={soggetto}
              onUpdate={loadSoggetto}
            />
          </div>
        )}

        {/* Tab: Documenti */}
        {activeTab === 'documenti' && (
          <div className="tab-content tab-documenti">
            <div className="tab-header">
              <h2>📄 Gestione Documenti</h2>
              {!showUpload && (
                <button
                  onClick={() => setShowUpload(true)}
                  className="btn btn-primary"
                >
                  ➕ Carica Documento
                </button>
              )}
            </div>

            {showUpload && (
              <div className="upload-section">
                <DocumentoUpload
                  soggettoId={parseInt(id)}
                  onUploadSuccess={handleUploadSuccess}
                  onCancel={() => setShowUpload(false)}
                />
              </div>
            )}

            <div className="documents-section">
              <DocumentoList
                soggettoId={parseInt(id)}
                onDocumentDeleted={handleDocumentDeleted}
                refreshTrigger={refreshDocumenti}
              />
            </div>
          </div>
        )}

        {/* Tab: Ruoli */}
        {activeTab === 'ruoli' && (
          <div className="tab-content tab-ruoli">
            <div className="tab-header">
              <h2>👥 Ruoli Assegnati</h2>
              <button className="btn btn-primary">
                ➕ Aggiungi Ruolo
              </button>
            </div>

            {ruoli.length === 0 ? (
              <div className="empty-state">
                <div className="empty-icon">👥</div>
                <p>Nessun ruolo assegnato</p>
                <p className="empty-hint">
                  Aggiungi ruoli per definire le responsabilità di questo soggetto
                  (es. Proprietario, Affittuario, Tecnico)
                </p>
              </div>
            ) : (
              <div className="ruoli-list">
                {ruoli.map((ruolo) => (
                  <div key={ruolo.id} className="ruolo-card">
                    <div className="ruolo-header">
                      <span className="ruolo-nome">{ruolo.ruolo_nome}</span>
                      <span className="ruolo-modulo">{ruolo.modulo_id}</span>
                    </div>
                    {ruolo.ruolo_descrizione && (
                      <div className="ruolo-descrizione">{ruolo.ruolo_descrizione}</div>
                    )}
                    {ruolo.note && (
                      <div className="ruolo-note">
                        <strong>Note:</strong> {ruolo.note}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="soggetto-detail-footer">
        <Link to="/anagrafiche" className="btn btn-secondary">
          ← Torna all'elenco
        </Link>
      </div>
    </div>
  );
}

export default SoggettoDetail;
