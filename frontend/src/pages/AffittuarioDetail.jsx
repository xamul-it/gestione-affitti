import { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { affittuariAPI, contrattiAPI, incassiAPI, documentiAPI } from '../services/api';
import './ImmobileDetail.css';

function AffittuarioDetail() {
  const { id } = useParams();
  const navigate = useNavigate();

  // Main entity
  const [affittuario, setAffittuario] = useState(null);

  // Related entities
  const [contratti, setContratti] = useState([]);
  const [incassi, setIncassi] = useState([]);
  const [documenti, setDocumenti] = useState([]);

  // UI state
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('overview');

  useEffect(() => {
    loadAffittuarioData();
  }, [id]);

  const loadAffittuarioData = async () => {
    try {
      setLoading(true);
      setError(null);

      // Fetch main affittuario
      const affittuarioData = await affittuariAPI.getById(id);
      setAffittuario(affittuarioData);

      // Fetch related data in parallel
      await Promise.all([
        fetchContratti(),
        fetchIncassi(),
        fetchDocumenti()
      ]);

    } catch (err) {
      console.error('Error loading affittuario:', err);
      setError('Errore nel caricamento dell\'affittuario');
    } finally {
      setLoading(false);
    }
  };

  const fetchContratti = async () => {
    try {
      const response = await contrattiAPI.getAll();
      // Filter contratti for this affittuario
      const affittuarioContratti = response.filter(c => c.affittuario_id === parseInt(id));
      setContratti(affittuarioContratti);
    } catch (err) {
      console.error('Error loading contratti:', err);
    }
  };

  const fetchIncassi = async () => {
    try {
      const response = await incassiAPI.getAll();
      // Get all contratti IDs for this affittuario
      const contrattiResponse = await contrattiAPI.getAll();
      const affittuarioContrattiIds = contrattiResponse
        .filter(c => c.affittuario_id === parseInt(id))
        .map(c => c.id);

      // Filter incassi for this affittuario's contracts
      const affittuarioIncassi = response.filter(i =>
        affittuarioContrattiIds.includes(i.contratto_id)
      );
      setIncassi(affittuarioIncassi);
    } catch (err) {
      console.error('Error loading incassi:', err);
    }
  };

  const fetchDocumenti = async () => {
    try {
      const response = await documentiAPI.getAll();
      // Filter documents for this affittuario
      const affittuarioDocumenti = response.filter(
        d => d.entity_type === 'affittuario' && d.entity_id === parseInt(id)
      );
      setDocumenti(affittuarioDocumenti);
    } catch (err) {
      console.error('Error loading documenti:', err);
    }
  };

  const handleDelete = async () => {
    if (window.confirm('Sei sicuro di voler eliminare questo affittuario?')) {
      try {
        await affittuariAPI.delete(id);
        navigate('/affittuari');
      } catch (err) {
        alert('Errore durante l\'eliminazione dell\'affittuario');
      }
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleDateString('it-IT');
  };

  const formatCurrency = (amount) => {
    if (!amount && amount !== 0) return 'N/A';
    return new Intl.NumberFormat('it-IT', {
      style: 'currency',
      currency: 'EUR'
    }).format(amount);
  };

  const getStatoBadgeClass = (stato) => {
    const classes = {
      'ATTIVO': 'badge-success',
      'SCADUTO': 'badge-danger',
      'DISDETTO': 'badge-warning',
      'BOZZA': 'badge-secondary'
    };
    return classes[stato] || 'badge-secondary';
  };

  const calculateTotaleIncassato = () => {
    return incassi
      .filter(i => i.pagato)
      .reduce((sum, i) => sum + (parseFloat(i.importo) || 0), 0);
  };

  const calculateTotaleDaPagare = () => {
    return incassi
      .filter(i => !i.pagato)
      .reduce((sum, i) => sum + (parseFloat(i.importo) || 0), 0);
  };

  const getActiveContratti = () => {
    return contratti.filter(c => c.stato === 'ATTIVO');
  };

  if (loading) {
    return (
      <div className="immobile-detail-container">
        <div className="loading-state">
          <div className="loading-spinner"></div>
          <p>Caricamento affittuario...</p>
        </div>
      </div>
    );
  }

  if (error || !affittuario) {
    return (
      <div className="immobile-detail-container">
        <div className="error-state">
          <h2>Errore</h2>
          <p>{error || 'Affittuario non trovato'}</p>
          <button onClick={() => navigate('/affittuari')} className="btn-primary">
            Torna alla lista
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="immobile-detail-container">
      {/* Header */}
      <div className="detail-header">
        <div className="header-left">
          <button onClick={() => navigate('/affittuari')} className="btn-back">
            ← Torna alla lista
          </button>
          <h1>{affittuario.nome} {affittuario.cognome}</h1>
        </div>
        <div className="header-actions">
          <button onClick={() => navigate(`/affittuari/edit/${id}`)} className="btn-secondary">
            Modifica
          </button>
          <button onClick={handleDelete} className="btn-danger">
            Elimina
          </button>
        </div>
      </div>

      {/* Main Info Card */}
      <div className="immobile-main-card">
        <div className="main-card-content">
          <div className="property-icon">👤</div>
          <div className="property-info">
            <h2>{affittuario.nome} {affittuario.cognome}</h2>
            <p className="property-subtitle">{affittuario.email || 'N/A'}</p>
            <div className="property-badges">
              {getActiveContratti().length > 0 && (
                <span className="badge badge-success">Contratto Attivo</span>
              )}
              {affittuario.codice_fiscale && (
                <span className="badge badge-info">CF: {affittuario.codice_fiscale}</span>
              )}
            </div>
          </div>
        </div>

        {/* Quick Stats */}
        <div className="quick-stats">
          <div className="stat-card">
            <span className="stat-value">{contratti.length}</span>
            <span className="stat-label">Contratti</span>
          </div>
          <div className="stat-card">
            <span className="stat-value">{getActiveContratti().length}</span>
            <span className="stat-label">Contratti Attivi</span>
          </div>
          <div className="stat-card">
            <span className="stat-value">{formatCurrency(calculateTotaleIncassato())}</span>
            <span className="stat-label">Totale Pagato</span>
          </div>
          <div className="stat-card">
            <span className="stat-value">{documenti.length}</span>
            <span className="stat-label">Documenti</span>
          </div>
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="detail-tabs">
        <button
          className={`tab ${activeTab === 'overview' ? 'active' : ''}`}
          onClick={() => setActiveTab('overview')}
        >
          Panoramica
        </button>
        <button
          className={`tab ${activeTab === 'anagrafica' ? 'active' : ''}`}
          onClick={() => setActiveTab('anagrafica')}
        >
          Anagrafica
        </button>
        <button
          className={`tab ${activeTab === 'contratti' ? 'active' : ''}`}
          onClick={() => setActiveTab('contratti')}
        >
          Contratti ({contratti.length})
        </button>
        <button
          className={`tab ${activeTab === 'pagamenti' ? 'active' : ''}`}
          onClick={() => setActiveTab('pagamenti')}
        >
          Storico Pagamenti ({incassi.length})
        </button>
        <button
          className={`tab ${activeTab === 'documenti' ? 'active' : ''}`}
          onClick={() => setActiveTab('documenti')}
        >
          Documenti ({documenti.length})
        </button>
      </div>

      {/* Tab Content */}
      <div className="tab-content">
        {activeTab === 'overview' && <OverviewSection
          affittuario={affittuario}
          contratti={contratti}
          incassi={incassi}
          documenti={documenti}
          formatDate={formatDate}
          formatCurrency={formatCurrency}
          getStatoBadgeClass={getStatoBadgeClass}
        />}

        {activeTab === 'anagrafica' && <AnagraficaSection
          affittuario={affittuario}
          formatDate={formatDate}
        />}

        {activeTab === 'contratti' && <ContrattiSection
          contratti={contratti}
          formatDate={formatDate}
          formatCurrency={formatCurrency}
          getStatoBadgeClass={getStatoBadgeClass}
        />}

        {activeTab === 'pagamenti' && <PagamentiSection
          incassi={incassi}
          formatDate={formatDate}
          formatCurrency={formatCurrency}
        />}

        {activeTab === 'documenti' && <DocumentiSection
          documenti={documenti}
          formatDate={formatDate}
        />}
      </div>
    </div>
  );
}

// Overview Section Component
function OverviewSection({ affittuario, contratti, incassi, documenti, formatDate, formatCurrency, getStatoBadgeClass }) {
  const activeContratti = contratti.filter(c => c.stato === 'ATTIVO');
  const totaleIncassato = incassi.filter(i => i.pagato).reduce((sum, i) => sum + (parseFloat(i.importo) || 0), 0);
  const totaleDaPagare = incassi.filter(i => !i.pagato).reduce((sum, i) => sum + (parseFloat(i.importo) || 0), 0);

  return (
    <div className="overview-section">
      {/* Contact Info Card */}
      <div className="detail-card">
        <h3>Informazioni di Contatto</h3>
        <div className="contact-info">
          {affittuario.email && (
            <div className="contact-item">
              <span className="contact-icon">📧</span>
              <div>
                <span className="contact-label">Email</span>
                <a href={`mailto:${affittuario.email}`} className="contact-value">
                  {affittuario.email}
                </a>
              </div>
            </div>
          )}
          {affittuario.telefono && (
            <div className="contact-item">
              <span className="contact-icon">📞</span>
              <div>
                <span className="contact-label">Telefono</span>
                <a href={`tel:${affittuario.telefono}`} className="contact-value">
                  {affittuario.telefono}
                </a>
              </div>
            </div>
          )}
          {affittuario.cellulare && (
            <div className="contact-item">
              <span className="contact-icon">📱</span>
              <div>
                <span className="contact-label">Cellulare</span>
                <a href={`tel:${affittuario.cellulare}`} className="contact-value">
                  {affittuario.cellulare}
                </a>
              </div>
            </div>
          )}
          {(affittuario.indirizzo || affittuario.citta) && (
            <div className="contact-item">
              <span className="contact-icon">📍</span>
              <div>
                <span className="contact-label">Indirizzo</span>
                <span className="contact-value">
                  {affittuario.indirizzo && `${affittuario.indirizzo}`}
                  {affittuario.citta && `, ${affittuario.citta}`}
                  {affittuario.cap && ` ${affittuario.cap}`}
                </span>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Active Contracts */}
      <div className="detail-card">
        <h3>Contratti Attivi ({activeContratti.length})</h3>
        {activeContratti.length > 0 ? (
          <div className="contracts-grid">
            {activeContratti.map(contratto => (
              <Link
                key={contratto.id}
                to={`/contratti/${contratto.id}`}
                className="contract-card"
              >
                <div className="contract-header">
                  <h4>{contratto.numero_contratto}</h4>
                  <span className={`badge ${getStatoBadgeClass(contratto.stato)}`}>
                    {contratto.stato}
                  </span>
                </div>
                <div className="contract-details">
                  <p className="contract-amount">{formatCurrency(contratto.canone_mensile)}/mese</p>
                  <p className="contract-dates">
                    {formatDate(contratto.data_inizio)} - {formatDate(contratto.data_scadenza)}
                  </p>
                </div>
              </Link>
            ))}
          </div>
        ) : (
          <p className="text-muted">Nessun contratto attivo</p>
        )}
      </div>

      {/* Payment Summary */}
      <div className="detail-card">
        <h3>Riepilogo Pagamenti</h3>
        <div className="summary-grid">
          <div className="summary-item">
            <span className="summary-label">Totale Pagato</span>
            <span className="summary-value text-success">{formatCurrency(totaleIncassato)}</span>
          </div>
          <div className="summary-item">
            <span className="summary-label">Da Pagare</span>
            <span className="summary-value text-danger">{formatCurrency(totaleDaPagare)}</span>
          </div>
          <div className="summary-item">
            <span className="summary-label">Pagamenti Effettuati</span>
            <span className="summary-value">{incassi.filter(i => i.pagato).length}</span>
          </div>
          <div className="summary-item">
            <span className="summary-label">Pagamenti in Sospeso</span>
            <span className="summary-value">{incassi.filter(i => !i.pagato).length}</span>
          </div>
        </div>
      </div>

      {/* Documenti Summary */}
      <div className="detail-card">
        <h3>Documenti ({documenti.length})</h3>
        {documenti.length > 0 ? (
          <ul className="simple-list">
            {documenti.slice(0, 3).map(doc => (
              <li key={doc.id}>{doc.nome_file}</li>
            ))}
            {documenti.length > 3 && (
              <li className="text-muted">...e altri {documenti.length - 3} documenti</li>
            )}
          </ul>
        ) : (
          <p className="text-muted">Nessun documento caricato</p>
        )}
      </div>
    </div>
  );
}

// Anagrafica Section Component
function AnagraficaSection({ affittuario, formatDate }) {
  return (
    <div className="anagrafica-section">
      <div className="detail-card">
        <h3>Dati Anagrafici</h3>
        <div className="detail-grid">
          <div className="detail-item">
            <span className="detail-label">Nome</span>
            <span className="detail-value">{affittuario.nome || 'N/A'}</span>
          </div>
          <div className="detail-item">
            <span className="detail-label">Cognome</span>
            <span className="detail-value">{affittuario.cognome || 'N/A'}</span>
          </div>
          <div className="detail-item">
            <span className="detail-label">Codice Fiscale</span>
            <span className="detail-value">{affittuario.codice_fiscale || 'N/A'}</span>
          </div>
          <div className="detail-item">
            <span className="detail-label">Data di Nascita</span>
            <span className="detail-value">{formatDate(affittuario.data_nascita)}</span>
          </div>
          <div className="detail-item">
            <span className="detail-label">Luogo di Nascita</span>
            <span className="detail-value">{affittuario.luogo_nascita || 'N/A'}</span>
          </div>
          <div className="detail-item">
            <span className="detail-label">Nazionalità</span>
            <span className="detail-value">{affittuario.nazionalita || 'N/A'}</span>
          </div>
        </div>
      </div>

      <div className="detail-card">
        <h3>Recapiti</h3>
        <div className="detail-grid">
          <div className="detail-item">
            <span className="detail-label">Email</span>
            <span className="detail-value">
              {affittuario.email ? (
                <a href={`mailto:${affittuario.email}`}>{affittuario.email}</a>
              ) : 'N/A'}
            </span>
          </div>
          <div className="detail-item">
            <span className="detail-label">Telefono</span>
            <span className="detail-value">
              {affittuario.telefono ? (
                <a href={`tel:${affittuario.telefono}`}>{affittuario.telefono}</a>
              ) : 'N/A'}
            </span>
          </div>
          <div className="detail-item">
            <span className="detail-label">Cellulare</span>
            <span className="detail-value">
              {affittuario.cellulare ? (
                <a href={`tel:${affittuario.cellulare}`}>{affittuario.cellulare}</a>
              ) : 'N/A'}
            </span>
          </div>
        </div>
      </div>

      <div className="detail-card">
        <h3>Residenza</h3>
        <div className="detail-grid">
          <div className="detail-item">
            <span className="detail-label">Indirizzo</span>
            <span className="detail-value">{affittuario.indirizzo || 'N/A'}</span>
          </div>
          <div className="detail-item">
            <span className="detail-label">Città</span>
            <span className="detail-value">{affittuario.citta || 'N/A'}</span>
          </div>
          <div className="detail-item">
            <span className="detail-label">CAP</span>
            <span className="detail-value">{affittuario.cap || 'N/A'}</span>
          </div>
          <div className="detail-item">
            <span className="detail-label">Provincia</span>
            <span className="detail-value">{affittuario.provincia || 'N/A'}</span>
          </div>
        </div>
      </div>

      {affittuario.note && (
        <div className="detail-card">
          <h3>Note</h3>
          <p className="note-content">{affittuario.note}</p>
        </div>
      )}
    </div>
  );
}

// Contratti Section Component
function ContrattiSection({ contratti, formatDate, formatCurrency, getStatoBadgeClass }) {
  if (contratti.length === 0) {
    return (
      <div className="empty-state">
        <div className="empty-icon">📄</div>
        <h3>Nessun contratto</h3>
        <p>Non ci sono contratti registrati per questo affittuario</p>
        <button className="btn-primary">Crea Contratto</button>
      </div>
    );
  }

  return (
    <div className="contratti-section">
      <div className="detail-card">
        <h3>Tutti i Contratti ({contratti.length})</h3>
        <div className="table-responsive">
          <table className="data-table">
            <thead>
              <tr>
                <th>Numero Contratto</th>
                <th>Tipologia</th>
                <th>Data Inizio</th>
                <th>Data Scadenza</th>
                <th>Canone</th>
                <th>Stato</th>
                <th>Azioni</th>
              </tr>
            </thead>
            <tbody>
              {contratti.map(contratto => (
                <tr key={contratto.id}>
                  <td>
                    <Link to={`/contratti/${contratto.id}`} className="entity-link">
                      {contratto.numero_contratto}
                    </Link>
                  </td>
                  <td>{contratto.tipologia_contratto || 'N/A'}</td>
                  <td>{formatDate(contratto.data_inizio)}</td>
                  <td>{formatDate(contratto.data_scadenza)}</td>
                  <td>{formatCurrency(contratto.canone_mensile)}</td>
                  <td>
                    <span className={`badge ${getStatoBadgeClass(contratto.stato)}`}>
                      {contratto.stato || 'N/A'}
                    </span>
                  </td>
                  <td>
                    <Link to={`/contratti/${contratto.id}`} className="btn-sm">
                      Dettagli
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

// Pagamenti Section Component
function PagamentiSection({ incassi, formatDate, formatCurrency }) {
  if (incassi.length === 0) {
    return (
      <div className="empty-state">
        <div className="empty-icon">💰</div>
        <h3>Nessun pagamento</h3>
        <p>Non ci sono pagamenti registrati per questo affittuario</p>
      </div>
    );
  }

  const incassiPagati = incassi.filter(i => i.pagato);
  const incassiDaPagare = incassi.filter(i => !i.pagato);
  const totaleIncassato = incassiPagati.reduce((sum, i) => sum + (parseFloat(i.importo) || 0), 0);
  const totaleDaPagare = incassiDaPagare.reduce((sum, i) => sum + (parseFloat(i.importo) || 0), 0);

  return (
    <div className="pagamenti-section">
      {/* Summary Cards */}
      <div className="summary-cards">
        <div className="summary-card success">
          <h4>Pagato</h4>
          <p className="summary-amount">{formatCurrency(totaleIncassato)}</p>
          <p className="summary-count">{incassiPagati.length} pagamenti</p>
        </div>
        <div className="summary-card danger">
          <h4>Da Pagare</h4>
          <p className="summary-amount">{formatCurrency(totaleDaPagare)}</p>
          <p className="summary-count">{incassiDaPagare.length} in sospeso</p>
        </div>
        <div className="summary-card info">
          <h4>Totale Storico</h4>
          <p className="summary-amount">{formatCurrency(totaleIncassato + totaleDaPagare)}</p>
          <p className="summary-count">{incassi.length} movimenti</p>
        </div>
      </div>

      {/* Payments Table */}
      <div className="detail-card">
        <h3>Storico Completo</h3>
        <div className="table-responsive">
          <table className="data-table">
            <thead>
              <tr>
                <th>Contratto</th>
                <th>Mese</th>
                <th>Anno</th>
                <th>Importo</th>
                <th>Data Pagamento</th>
                <th>Stato</th>
              </tr>
            </thead>
            <tbody>
              {incassi.map(incasso => (
                <tr key={incasso.id}>
                  <td>
                    <Link to={`/contratti/${incasso.contratto_id}`} className="entity-link">
                      Contratto #{incasso.contratto_id}
                    </Link>
                  </td>
                  <td>{incasso.mese || 'N/A'}</td>
                  <td>{incasso.anno || 'N/A'}</td>
                  <td>{formatCurrency(incasso.importo)}</td>
                  <td>{formatDate(incasso.data_pagamento)}</td>
                  <td>
                    <span className={`badge ${incasso.pagato ? 'badge-success' : 'badge-warning'}`}>
                      {incasso.pagato ? 'Pagato' : 'Da Pagare'}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

// Documenti Section Component
function DocumentiSection({ documenti, formatDate }) {
  if (documenti.length === 0) {
    return (
      <div className="empty-state">
        <div className="empty-icon">📄</div>
        <h3>Nessun documento</h3>
        <p>Non ci sono documenti caricati per questo affittuario</p>
        <button className="btn-primary">Carica Documento</button>
      </div>
    );
  }

  return (
    <div className="documenti-section">
      <div className="detail-card">
        <div className="card-header">
          <h3>Documenti ({documenti.length})</h3>
          <button className="btn-primary">Carica Nuovo</button>
        </div>
        <div className="documenti-list">
          {documenti.map(doc => (
            <div key={doc.id} className="documento-item">
              <div className="documento-icon">📄</div>
              <div className="documento-info">
                <h4>{doc.nome_file}</h4>
                <p className="text-muted">
                  {doc.tipo_documento || 'Documento'} • Caricato il {formatDate(doc.data_caricamento)}
                </p>
              </div>
              <div className="documento-actions">
                <button className="btn-icon" title="Scarica">⬇️</button>
                <button className="btn-icon" title="Elimina">🗑️</button>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

export default AffittuarioDetail;
