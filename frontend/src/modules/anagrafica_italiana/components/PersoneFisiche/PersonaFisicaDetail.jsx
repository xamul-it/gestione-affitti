import { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { getSoggettoById, deleteSoggetto, getSoggettoRuoli } from '../../services/anagraficaAPI';
import { renderIcon } from '../../../../components/Navigation/iconRegistry.jsx';
import { DocumentoUpload, DocumentoList } from '../Documenti';
import RuoliAziendaSection from '../RuoliAzienda/RuoliAziendaSection';
import '../SoggettiAnagrafici/SoggettoDetail.css';

/**
 * PersonaFisicaDetail - Scheda dettaglio persona fisica
 *
 * Vista ottimizzata per persone fisiche con campi specifici:
 * - Nome, Cognome, Data Nascita, Luogo Nascita
 * - Sezione Account Utente prominente (solo persone fisiche possono accedere)
 */
function PersonaFisicaDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [persona, setPersona] = useState(null);
  const [ruoli, setRuoli] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('anagrafica');
  const [showUpload, setShowUpload] = useState(false);
  const [refreshDocumenti, setRefreshDocumenti] = useState(0);

  useEffect(() => {
    loadPersona();
    loadRuoli();
  }, [id]);

  const loadPersona = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await getSoggettoById(id);

      // Verifica che sia effettivamente una persona fisica
      if (data.tipo_soggetto !== 'PERSONA_FISICA') {
        setError('Questo soggetto non è una persona fisica');
        return;
      }

      setPersona(data);
    } catch (err) {
      console.error('Error loading persona:', err);
      setError('Errore nel caricamento della persona fisica');
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
    if (!confirm('Sei sicuro di voler eliminare questa persona?')) {
      return;
    }

    try {
      await deleteSoggetto(id);
      navigate('/anagrafiche/persone-fisiche');
    } catch (err) {
      console.error('Error deleting persona:', err);
      alert('Errore nell\'eliminazione della persona');
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return '-';
    return new Date(dateString).toLocaleDateString('it-IT');
  };

  const getNomeCompleto = () => {
    if (!persona) return '';
    return `${persona.nome || ''} ${persona.cognome || ''}`.trim() || '(Non specificato)';
  };

  if (loading) {
    return (
      <div className="soggetto-detail-container">
        <div className="loading">Caricamento persona fisica...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="soggetto-detail-container">
        <div className="error">{error}</div>
        <Link to="/anagrafiche/persone-fisiche" className="btn btn-secondary">
          Torna all'elenco
        </Link>
      </div>
    );
  }

  if (!persona) {
    return (
      <div className="soggetto-detail-container">
        <div className="error">Persona fisica non trovata</div>
        <Link to="/anagrafiche/persone-fisiche" className="btn btn-secondary">
          Torna all'elenco
        </Link>
      </div>
    );
  }

  return (
    <div className="soggetto-detail-container">
      {/* Breadcrumb */}
      <div className="breadcrumb">
        <Link to="/anagrafiche/persone-fisiche">Persone Fisiche</Link>
        <span className="separator">/</span>
        <span className="current">{getNomeCompleto()}</span>
      </div>

      {/* Header */}
      <div className="soggetto-detail-header">
        <div className="header-title">
          <span className="tipo-icon" aria-hidden="true">
            {renderIcon('user', { size: 26, className: 'detail-icon', fallbackClassName: 'nav-emoji-icon' })}
          </span>
          <h1>{getNomeCompleto()}</h1>
          <span className={`status-badge ${persona.attivo ? 'active' : 'inactive'}`}>
            {persona.attivo ? 'Attivo' : 'Inattivo'}
          </span>
        </div>
        <div className="header-actions">
          <Link
            to={`/anagrafiche/persone-fisiche/${persona.id}/modifica`}
            className="btn btn-primary"
          >
            <span className="button-icon" aria-hidden="true">
              {renderIcon('pencil', { size: 16, className: 'detail-icon', fallbackClassName: 'nav-emoji-icon' })}
            </span>
            Modifica
          </Link>
          <button onClick={handleDelete} className="btn btn-danger">
            <span className="button-icon" aria-hidden="true">
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
          <span className="tab-icon" aria-hidden="true">
            {renderIcon('list', { size: 16, className: 'detail-icon', fallbackClassName: 'nav-emoji-icon' })}
          </span>
          Dati Anagrafici
        </button>
        <button
          className={`tab ${activeTab === 'ruoli-azienda' ? 'active' : ''}`}
          onClick={() => setActiveTab('ruoli-azienda')}
        >
          <span className="tab-icon" aria-hidden="true">
            {renderIcon('building', { size: 16, className: 'detail-icon', fallbackClassName: 'nav-emoji-icon' })}
          </span>
          Aziende
        </button>
        <button
          className={`tab ${activeTab === 'documenti' ? 'active' : ''}`}
          onClick={() => setActiveTab('documenti')}
        >
          <span className="tab-icon" aria-hidden="true">
            {renderIcon('file-text', { size: 16, className: 'detail-icon', fallbackClassName: 'nav-emoji-icon' })}
          </span>
          Documenti
        </button>
        <button
          className={`tab ${activeTab === 'ruoli' ? 'active' : ''}`}
          onClick={() => setActiveTab('ruoli')}
        >
          <span className="tab-icon" aria-hidden="true">
            {renderIcon('users', { size: 16, className: 'detail-icon', fallbackClassName: 'nav-emoji-icon' })}
          </span>
          Ruoli {ruoli.length > 0 && `(${ruoli.length})`}
        </button>
      </div>

      {/* Tab Content */}
      <div className="soggetto-detail-content">
        {/* Tab: Anagrafica */}
        {activeTab === 'anagrafica' && (
          <div className="tab-content tab-anagrafica">
            {/* Dati Anagrafici */}
            <details className="detail-section collapsible" open>
              <summary className="detail-section-summary">
                <span className="detail-section-title">
                  <span className="detail-section-icon" aria-hidden="true">
                    {renderIcon('list', { size: 18, className: 'detail-icon', fallbackClassName: 'nav-emoji-icon' })}
                  </span>
                  Dati Anagrafici
                </span>
              </summary>
              <div className="detail-section-body">
                <div className="detail-grid">
                <div className="detail-field">
                  <label>Tipo Soggetto</label>
                  <div className="field-value">
                    <span className="inline-icon" aria-hidden="true">
                      {renderIcon('user', { size: 14, className: 'detail-icon', fallbackClassName: 'nav-emoji-icon' })}
                    </span>
                    Persona Fisica
                  </div>
                </div>
                <div className="detail-field">
                  <label>Nome</label>
                  <div className="field-value">{persona.nome || '-'}</div>
                </div>
                <div className="detail-field">
                  <label>Cognome</label>
                  <div className="field-value">{persona.cognome || '-'}</div>
                </div>
                <div className="detail-field">
                  <label>Codice Fiscale</label>
                  <div className="field-value">
                    <code className="cf-badge">{persona.codice_fiscale || '-'}</code>
                  </div>
                </div>
                <div className="detail-field">
                  <label>Data di Nascita</label>
                  <div className="field-value">{formatDate(persona.data_nascita)}</div>
                </div>
                <div className="detail-field">
                  <label>Luogo di Nascita</label>
                  <div className="field-value">{persona.luogo_nascita || '-'}</div>
                </div>
              </div>
              </div>
            </details>

            {/* Attività Professionale */}
            {persona.partita_iva && (
              <details className="detail-section collapsible">
                <summary className="detail-section-summary">
                  <span className="detail-section-title">
                    <span className="detail-section-icon" aria-hidden="true">
                      {renderIcon('briefcase', { size: 18, className: 'detail-icon', fallbackClassName: 'nav-emoji-icon' })}
                    </span>
                    Attività Professionale
                  </span>
                </summary>
                <div className="detail-section-body">
                  <div className="detail-grid">
                  <div className="detail-field">
                    <label>Partita IVA</label>
                    <div className="field-value">
                      <code className="piva-badge">{persona.partita_iva}</code>
                    </div>
                  </div>
                </div>
                <div className="info-note" style={{ marginTop: '10px' }}>
                  <span className="inline-icon" aria-hidden="true">
                    {renderIcon('briefcase', { size: 14, className: 'detail-icon', fallbackClassName: 'nav-emoji-icon' })}
                  </span>
                  <em>Questa persona esercita attività professionale con Partita IVA</em>
                </div>
                </div>
              </details>
            )}

            {/* Accesso Sistema - Sezione prominente per persone fisiche */}
            <details className="detail-section collapsible" open>
              <summary className="detail-section-summary">
                <span className="detail-section-title">
                  <span className="detail-section-icon" aria-hidden="true">
                    {renderIcon('lock', { size: 18, className: 'detail-icon', fallbackClassName: 'nav-emoji-icon' })}
                  </span>
                  Accesso al Sistema
                </span>
              </summary>
              <div className="detail-section-body">
                {persona.user_id ? (
                  <div className="detail-grid">
                    <div className="detail-field full-width">
                      <div className="field-value" style={{
                        padding: '12px',
                        backgroundColor: '#e8f5e9',
                        borderLeft: '4px solid #4caf50',
                        borderRadius: '4px'
                      }}>
                        <span className="inline-icon" aria-hidden="true">
                          {renderIcon('badge-check', { size: 14, className: 'detail-icon', fallbackClassName: 'nav-emoji-icon' })}
                        </span>
                        <strong>Questa persona ha accesso al sistema</strong> (User ID: {persona.user_id})
                      </div>
                    </div>
                    <div className="detail-field">
                      <label>Username</label>
                      <div className="field-value">{persona.email || '-'}</div>
                    </div>
                  </div>
                ) : (
                  <div className="info-note">
                    <span className="inline-icon" aria-hidden="true">
                      {renderIcon('info', { size: 14, className: 'detail-icon', fallbackClassName: 'nav-emoji-icon' })}
                    </span>
                    <em>Questa persona non ha ancora un account utente.
                    Le persone fisiche possono avere accesso al sistema per gestire i propri dati.</em>
                  </div>
                )}
              </div>
            </details>

            {/* Contatti */}
            <details className="detail-section collapsible" open>
              <summary className="detail-section-summary">
                <span className="detail-section-title">
                  <span className="detail-section-icon" aria-hidden="true">
                    {renderIcon('users', { size: 18, className: 'detail-icon', fallbackClassName: 'nav-emoji-icon' })}
                  </span>
                  Contatti
                </span>
              </summary>
              <div className="detail-section-body">
                <div className="detail-grid">
                <div className="detail-field">
                  <label>Email</label>
                  <div className="field-value">
                    {persona.email ? (
                      <a href={`mailto:${persona.email}`}>{persona.email}</a>
                    ) : (
                      '-'
                    )}
                  </div>
                </div>
                <div className="detail-field">
                  <label>PEC</label>
                  <div className="field-value">
                    {persona.pec ? <a href={`mailto:${persona.pec}`}>{persona.pec}</a> : '-'}
                  </div>
                </div>
                <div className="detail-field">
                  <label>Telefono</label>
                  <div className="field-value">{persona.telefono || '-'}</div>
                </div>
                <div className="detail-field">
                  <label>Cellulare</label>
                  <div className="field-value">{persona.cellulare || '-'}</div>
                </div>
              </div>
              </div>
            </details>

            {/* Residenza */}
            <details className="detail-section collapsible" open>
              <summary className="detail-section-summary">
                <span className="detail-section-title">
                  <span className="detail-section-icon" aria-hidden="true">
                    {renderIcon('building', { size: 18, className: 'detail-icon', fallbackClassName: 'nav-emoji-icon' })}
                  </span>
                  Residenza
                </span>
              </summary>
              <div className="detail-section-body">
                <div className="detail-grid">
                <div className="detail-field full-width">
                  <label>Indirizzo</label>
                  <div className="field-value">{persona.indirizzo || '-'}</div>
                </div>
                <div className="detail-field">
                  <label>Città</label>
                  <div className="field-value">{persona.citta || '-'}</div>
                </div>
                <div className="detail-field">
                  <label>Provincia</label>
                  <div className="field-value">{persona.provincia || '-'}</div>
                </div>
                <div className="detail-field">
                  <label>CAP</label>
                  <div className="field-value">{persona.cap || '-'}</div>
                </div>
                <div className="detail-field">
                  <label>Nazione</label>
                  <div className="field-value">{persona.nazione || 'Italia'}</div>
                </div>
              </div>
              </div>
            </details>

            {/* Note */}
            {persona.note && (
              <details className="detail-section collapsible">
                <summary className="detail-section-summary">
                  <span className="detail-section-title">
                    <span className="detail-section-icon" aria-hidden="true">
                      {renderIcon('list', { size: 18, className: 'detail-icon', fallbackClassName: 'nav-emoji-icon' })}
                    </span>
                    Note
                  </span>
                </summary>
                <div className="detail-section-body">
                  <div className="note-content">{persona.note}</div>
                </div>
              </details>
            )}

            {/* Metadati */}
            <details className="detail-section collapsible metadata">
              <summary className="detail-section-summary">
                <span className="detail-section-title">
                  <span className="detail-section-icon" aria-hidden="true">
                    {renderIcon('info', { size: 18, className: 'detail-icon', fallbackClassName: 'nav-emoji-icon' })}
                  </span>
                  Informazioni di Sistema
                </span>
              </summary>
              <div className="detail-section-body">
                <div className="detail-grid">
                <div className="detail-field">
                  <label>ID</label>
                  <div className="field-value">{persona.id}</div>
                </div>
                <div className="detail-field">
                  <label>Creato il</label>
                  <div className="field-value">{formatDate(persona.created_at)}</div>
                </div>
                <div className="detail-field">
                  <label>Ultima modifica</label>
                  <div className="field-value">{formatDate(persona.updated_at)}</div>
                </div>
              </div>
              </div>
            </details>
          </div>
        )}

        {/* Tab: Ruoli Azienda */}
        {activeTab === 'ruoli-azienda' && (
          <div className="tab-content tab-ruoli-azienda">
            <RuoliAziendaSection
              soggetto={persona}
              onUpdate={loadPersona}
            />
          </div>
        )}

        {/* Tab: Documenti */}
        {activeTab === 'documenti' && (
          <div className="tab-content tab-documenti">
            <div className="tab-header">
              <h2>
                <span className="inline-icon" aria-hidden="true">
                  {renderIcon('file-text', { size: 18, className: 'detail-icon', fallbackClassName: 'nav-emoji-icon' })}
                </span>
                Gestione Documenti
              </h2>
              {!showUpload && (
                <button
                  onClick={() => setShowUpload(true)}
                  className="btn btn-primary"
                >
                  <span className="button-icon" aria-hidden="true">
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
              <h2>
                <span className="inline-icon" aria-hidden="true">
                  {renderIcon('users', { size: 18, className: 'detail-icon', fallbackClassName: 'nav-emoji-icon' })}
                </span>
                Ruoli Assegnati
              </h2>
              <button className="btn btn-primary">
                <span className="button-icon" aria-hidden="true">
                  {renderIcon('plus', { size: 16, className: 'detail-icon', fallbackClassName: 'nav-emoji-icon' })}
                </span>
                Aggiungi Ruolo
              </button>
            </div>

            {ruoli.length === 0 ? (
              <div className="empty-state">
                <div className="empty-icon" aria-hidden="true">
                  {renderIcon('users', { size: 48, className: 'detail-icon', fallbackClassName: 'nav-emoji-icon' })}
                </div>
                <p>Nessun ruolo assegnato</p>
                <p className="empty-hint">
                  Aggiungi ruoli per definire le responsabilità di questa persona
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
        <Link to="/anagrafiche/persone-fisiche" className="btn btn-secondary">
          ← Torna all'elenco persone fisiche
        </Link>
      </div>
    </div>
  );
}

export default PersonaFisicaDetail;
