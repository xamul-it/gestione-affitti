import { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { contrattiAPI, unitaImmobiliariAPI, affittuariAPI, incassiAPI, documentiAPI } from '../services/api';
import ScadenzeSection from '../components/Platform/Scadenze/ScadenzeSection';
import './ImmobileDetail.css';

function ContrattoDetail() {
  const { id } = useParams();
  const navigate = useNavigate();

  // Main entity
  const [contratto, setContratto] = useState(null);

  // Related entities
  const [immobile, setImmobile] = useState(null);
  const [affittuario, setAffittuario] = useState(null);
  const [incassi, setIncassi] = useState([]);
  const [documenti, setDocumenti] = useState([]);

  // UI state
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('overview');

  useEffect(() => {
    loadContrattoData();
  }, [id]);

  const loadContrattoData = async () => {
    try {
      setLoading(true);
      setError(null);

      // Fetch main contratto
      const contrattoData = await contrattiAPI.getById(id);
      setContratto(contrattoData);

      // Fetch related data in parallel
      await Promise.all([
        fetchImmobile(contrattoData.immobile_id),
        fetchAffittuario(contrattoData.affittuario_id),
        fetchIncassi(),
        fetchDocumenti()
      ]);

    } catch (err) {
      console.error('Error loading contratto:', err);
      setError('Errore nel caricamento del contratto');
    } finally {
      setLoading(false);
    }
  };

  const fetchImmobile = async (immobileId) => {
    if (!immobileId) return;
    try {
      const data = await unitaImmobiliariAPI.getById(immobileId);
      setImmobile(data);
    } catch (err) {
      console.error('Error loading immobile:', err);
    }
  };

  const fetchAffittuario = async (affittuarioId) => {
    if (!affittuarioId) return;
    try {
      const data = await affittuariAPI.getById(affittuarioId);
      setAffittuario(data);
    } catch (err) {
      console.error('Error loading affittuario:', err);
    }
  };

  const fetchIncassi = async () => {
    try {
      const response = await incassiAPI.getAll();
      // Filter incassi for this contract
      const contrattoIncassi = response.filter(i => i.contratto_id === parseInt(id));
      setIncassi(contrattoIncassi);
    } catch (err) {
      console.error('Error loading incassi:', err);
    }
  };

  const fetchDocumenti = async () => {
    try {
      const response = await documentiAPI.getAll();
      // Filter documents for this contract
      const contrattoDocumenti = response.filter(
        d => d.entity_type === 'contratto' && d.entity_id === parseInt(id)
      );
      setDocumenti(contrattoDocumenti);
    } catch (err) {
      console.error('Error loading documenti:', err);
    }
  };

  const handleDelete = async () => {
    if (window.confirm('Sei sicuro di voler eliminare questo contratto?')) {
      try {
        await contrattiAPI.delete(id);
        navigate('/contratti');
      } catch (err) {
        alert('Errore durante l\'eliminazione del contratto');
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

  if (loading) {
    return (
      <div className="immobile-detail-container">
        <div className="loading-state">
          <div className="loading-spinner"></div>
          <p>Caricamento contratto...</p>
        </div>
      </div>
    );
  }

  if (error || !contratto) {
    return (
      <div className="immobile-detail-container">
        <div className="error-state">
          <h2>Errore</h2>
          <p>{error || 'Contratto non trovato'}</p>
          <button onClick={() => navigate('/contratti')} className="btn-primary">
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
          <button onClick={() => navigate('/contratti')} className="btn-back">
            ← Torna alla lista
          </button>
          <h1>Contratto {contratto.numero_contratto}</h1>
        </div>
        <div className="header-actions">
          <button onClick={() => navigate(`/contratti/edit/${id}`)} className="btn-secondary">
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
          <div className="property-icon">📄</div>
          <div className="property-info">
            <h2>{contratto.numero_contratto}</h2>
            <p className="property-subtitle">{contratto.tipologia_contratto || 'N/A'}</p>
            <div className="property-badges">
              <span className={`badge ${getStatoBadgeClass(contratto.stato)}`}>
                {contratto.stato || 'N/A'}
              </span>
              <span className="badge badge-info">
                {contratto.uso_immobile || 'N/A'}
              </span>
            </div>
          </div>
        </div>

        {/* Quick Stats */}
        <div className="quick-stats">
          <div className="stat-card">
            <span className="stat-value">{formatCurrency(contratto.canone_mensile)}</span>
            <span className="stat-label">Canone Mensile</span>
          </div>
          <div className="stat-card">
            <span className="stat-value">{incassi.length}</span>
            <span className="stat-label">Incassi</span>
          </div>
          <div className="stat-card">
            <span className="stat-value">{formatCurrency(calculateTotaleIncassato())}</span>
            <span className="stat-label">Totale Incassato</span>
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
          className={`tab ${activeTab === 'details' ? 'active' : ''}`}
          onClick={() => setActiveTab('details')}
        >
          Dettagli Contratto
        </button>
        <button
          className={`tab ${activeTab === 'parties' ? 'active' : ''}`}
          onClick={() => setActiveTab('parties')}
        >
          Parti Contraenti
        </button>
        <button
          className={`tab ${activeTab === 'incassi' ? 'active' : ''}`}
          onClick={() => setActiveTab('incassi')}
        >
          Incassi ({incassi.length})
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
          contratto={contratto}
          immobile={immobile}
          affittuario={affittuario}
          incassi={incassi}
          documenti={documenti}
          formatDate={formatDate}
          formatCurrency={formatCurrency}
        />}

        {activeTab === 'details' && <DetailsSection
          contratto={contratto}
          formatDate={formatDate}
          formatCurrency={formatCurrency}
        />}

        {activeTab === 'parties' && <PartiesSection
          immobile={immobile}
          affittuario={affittuario}
        />}

        {activeTab === 'incassi' && <IncassiSection
          incassi={incassi}
          formatDate={formatDate}
          formatCurrency={formatCurrency}
        />}

        {activeTab === 'documenti' && <DocumentiSection
          documenti={documenti}
          formatDate={formatDate}
        />}
      </div>

      {/* Scadenze Section */}
      <ScadenzeSection
        modulo="affitti_lungo"
        entityType="contratto"
        entityId={parseInt(id)}
        title="Scadenze Contratto"
        initialCollapsed={false}
      />
    </div>
  );
}

// Overview Section Component
function OverviewSection({ contratto, immobile, affittuario, incassi, documenti, formatDate, formatCurrency }) {
  const totaleIncassato = incassi
    .filter(i => i.pagato)
    .reduce((sum, i) => sum + (parseFloat(i.importo) || 0), 0);
  const totaleDaPagare = incassi
    .filter(i => !i.pagato)
    .reduce((sum, i) => sum + (parseFloat(i.importo) || 0), 0);

  return (
    <div className="overview-section">
      {/* Contract Timeline */}
      <div className="detail-card">
        <h3>Timeline Contratto</h3>
        <div className="timeline">
          <div className="timeline-item">
            <div className="timeline-icon">📅</div>
            <div className="timeline-content">
              <h4>Data Inizio</h4>
              <p>{formatDate(contratto.data_inizio)}</p>
            </div>
          </div>
          <div className="timeline-item">
            <div className="timeline-icon">⏰</div>
            <div className="timeline-content">
              <h4>Data Scadenza</h4>
              <p>{formatDate(contratto.data_scadenza)}</p>
            </div>
          </div>
          {contratto.data_disdetta && (
            <div className="timeline-item">
              <div className="timeline-icon">⚠️</div>
              <div className="timeline-content">
                <h4>Data Disdetta</h4>
                <p>{formatDate(contratto.data_disdetta)}</p>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Immobile Card */}
      <div className="detail-card">
        <h3>Immobile</h3>
        {immobile ? (
          <div className="entity-card">
            <div className="entity-icon">🏠</div>
            <div className="entity-info">
              <Link to={`/unita-immobiliari/${immobile.id}`} className="entity-link">
                <h4>{immobile.indirizzo}</h4>
              </Link>
              <p>{immobile.citta} ({immobile.cap})</p>
              <p className="text-muted">{immobile.tipo || 'N/A'} - {immobile.superficie_mq}m²</p>
            </div>
          </div>
        ) : (
          <p className="text-muted">Nessun immobile associato</p>
        )}
      </div>

      {/* Affittuario Card */}
      <div className="detail-card">
        <h3>Affittuario</h3>
        {affittuario ? (
          <div className="entity-card">
            <div className="entity-icon">👤</div>
            <div className="entity-info">
              <Link to={`/affittuari/${affittuario.id}`} className="entity-link">
                <h4>{affittuario.nome} {affittuario.cognome}</h4>
              </Link>
              <p>{affittuario.email || 'N/A'}</p>
              <p className="text-muted">{affittuario.telefono || 'N/A'}</p>
            </div>
          </div>
        ) : (
          <p className="text-muted">Nessun affittuario associato</p>
        )}
      </div>

      {/* Incassi Summary */}
      <div className="detail-card">
        <h3>Riepilogo Incassi</h3>
        <div className="summary-grid">
          <div className="summary-item">
            <span className="summary-label">Totale Incassato</span>
            <span className="summary-value text-success">{formatCurrency(totaleIncassato)}</span>
          </div>
          <div className="summary-item">
            <span className="summary-label">Da Incassare</span>
            <span className="summary-value text-danger">{formatCurrency(totaleDaPagare)}</span>
          </div>
          <div className="summary-item">
            <span className="summary-label">Totale Incassi</span>
            <span className="summary-value">{incassi.length}</span>
          </div>
          <div className="summary-item">
            <span className="summary-label">Incassi Pagati</span>
            <span className="summary-value">{incassi.filter(i => i.pagato).length}</span>
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

// Details Section Component
function DetailsSection({ contratto, formatDate, formatCurrency }) {
  return (
    <div className="details-section">
      <div className="detail-card">
        <h3>Informazioni Contrattuali</h3>
        <div className="detail-grid">
          <div className="detail-item">
            <span className="detail-label">Numero Contratto</span>
            <span className="detail-value">{contratto.numero_contratto}</span>
          </div>
          <div className="detail-item">
            <span className="detail-label">Tipologia</span>
            <span className="detail-value">{contratto.tipologia_contratto || 'N/A'}</span>
          </div>
          <div className="detail-item">
            <span className="detail-label">Uso Immobile</span>
            <span className="detail-value">{contratto.uso_immobile || 'N/A'}</span>
          </div>
          <div className="detail-item">
            <span className="detail-label">Regime Fiscale</span>
            <span className="detail-value">{contratto.regime_fiscale || 'N/A'}</span>
          </div>
          <div className="detail-item">
            <span className="detail-label">Stato</span>
            <span className="detail-value">{contratto.stato || 'N/A'}</span>
          </div>
          <div className="detail-item">
            <span className="detail-label">Registrato</span>
            <span className="detail-value">{contratto.registrato ? 'Sì' : 'No'}</span>
          </div>
        </div>
      </div>

      <div className="detail-card">
        <h3>Date</h3>
        <div className="detail-grid">
          <div className="detail-item">
            <span className="detail-label">Data Inizio</span>
            <span className="detail-value">{formatDate(contratto.data_inizio)}</span>
          </div>
          <div className="detail-item">
            <span className="detail-label">Data Scadenza</span>
            <span className="detail-value">{formatDate(contratto.data_scadenza)}</span>
          </div>
          <div className="detail-item">
            <span className="detail-label">Data Registrazione</span>
            <span className="detail-value">{formatDate(contratto.data_registrazione)}</span>
          </div>
          <div className="detail-item">
            <span className="detail-label">Data Disdetta</span>
            <span className="detail-value">{formatDate(contratto.data_disdetta)}</span>
          </div>
        </div>
      </div>

      <div className="detail-card">
        <h3>Condizioni Economiche</h3>
        <div className="detail-grid">
          <div className="detail-item">
            <span className="detail-label">Canone Mensile</span>
            <span className="detail-value">{formatCurrency(contratto.canone_mensile)}</span>
          </div>
          <div className="detail-item">
            <span className="detail-label">Deposito Cauzionale</span>
            <span className="detail-value">{formatCurrency(contratto.deposito_cauzionale)}</span>
          </div>
          <div className="detail-item">
            <span className="detail-label">Spese Condominiali Incluse</span>
            <span className="detail-value">{contratto.spese_condominiali_incluse ? 'Sì' : 'No'}</span>
          </div>
        </div>
      </div>

      {contratto.note && (
        <div className="detail-card">
          <h3>Note</h3>
          <p className="note-content">{contratto.note}</p>
        </div>
      )}
    </div>
  );
}

// Parties Section Component
function PartiesSection({ immobile, affittuario }) {
  return (
    <div className="parties-section">
      <div className="detail-card">
        <h3>Immobile</h3>
        {immobile ? (
          <div className="party-card">
            <div className="party-header">
              <div className="entity-icon">🏠</div>
              <Link to={`/unita-immobiliari/${immobile.id}`} className="entity-link">
                <h4>{immobile.indirizzo}</h4>
              </Link>
            </div>
            <div className="detail-grid">
              <div className="detail-item">
                <span className="detail-label">Città</span>
                <span className="detail-value">{immobile.citta}</span>
              </div>
              <div className="detail-item">
                <span className="detail-label">CAP</span>
                <span className="detail-value">{immobile.cap}</span>
              </div>
              <div className="detail-item">
                <span className="detail-label">Tipo</span>
                <span className="detail-value">{immobile.tipo || 'N/A'}</span>
              </div>
              <div className="detail-item">
                <span className="detail-label">Superficie</span>
                <span className="detail-value">{immobile.superficie_mq}m²</span>
              </div>
              <div className="detail-item">
                <span className="detail-label">Locali</span>
                <span className="detail-value">{immobile.numero_locali || 'N/A'}</span>
              </div>
              <div className="detail-item">
                <span className="detail-label">Piano</span>
                <span className="detail-value">{immobile.piano || 'N/A'}</span>
              </div>
            </div>
          </div>
        ) : (
          <div className="empty-state">
            <p>Nessun immobile associato</p>
          </div>
        )}
      </div>

      <div className="detail-card">
        <h3>Affittuario</h3>
        {affittuario ? (
          <div className="party-card">
            <div className="party-header">
              <div className="entity-icon">👤</div>
              <Link to={`/affittuari/${affittuario.id}`} className="entity-link">
                <h4>{affittuario.nome} {affittuario.cognome}</h4>
              </Link>
            </div>
            <div className="detail-grid">
              <div className="detail-item">
                <span className="detail-label">Codice Fiscale</span>
                <span className="detail-value">{affittuario.codice_fiscale || 'N/A'}</span>
              </div>
              <div className="detail-item">
                <span className="detail-label">Email</span>
                <span className="detail-value">{affittuario.email || 'N/A'}</span>
              </div>
              <div className="detail-item">
                <span className="detail-label">Telefono</span>
                <span className="detail-value">{affittuario.telefono || 'N/A'}</span>
              </div>
              <div className="detail-item">
                <span className="detail-label">Cellulare</span>
                <span className="detail-value">{affittuario.cellulare || 'N/A'}</span>
              </div>
              <div className="detail-item">
                <span className="detail-label">Indirizzo</span>
                <span className="detail-value">{affittuario.indirizzo || 'N/A'}</span>
              </div>
              <div className="detail-item">
                <span className="detail-label">Città</span>
                <span className="detail-value">{affittuario.citta || 'N/A'}</span>
              </div>
            </div>
          </div>
        ) : (
          <div className="empty-state">
            <p>Nessun affittuario associato</p>
          </div>
        )}
      </div>
    </div>
  );
}

// Incassi Section Component
function IncassiSection({ incassi, formatDate, formatCurrency }) {
  if (incassi.length === 0) {
    return (
      <div className="empty-state">
        <div className="empty-icon">💰</div>
        <h3>Nessun incasso registrato</h3>
        <p>Non ci sono ancora incassi per questo contratto</p>
      </div>
    );
  }

  const incassiPagati = incassi.filter(i => i.pagato);
  const incassiDaPagare = incassi.filter(i => !i.pagato);

  return (
    <div className="incassi-section">
      {/* Summary Cards */}
      <div className="summary-cards">
        <div className="summary-card success">
          <h4>Incassato</h4>
          <p className="summary-amount">
            {formatCurrency(incassiPagati.reduce((sum, i) => sum + (parseFloat(i.importo) || 0), 0))}
          </p>
          <p className="summary-count">{incassiPagati.length} pagamenti</p>
        </div>
        <div className="summary-card danger">
          <h4>Da Incassare</h4>
          <p className="summary-amount">
            {formatCurrency(incassiDaPagare.reduce((sum, i) => sum + (parseFloat(i.importo) || 0), 0))}
          </p>
          <p className="summary-count">{incassiDaPagare.length} in sospeso</p>
        </div>
      </div>

      {/* Incassi Table */}
      <div className="detail-card">
        <h3>Tutti gli Incassi</h3>
        <div className="table-responsive">
          <table className="data-table">
            <thead>
              <tr>
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
        <p>Non ci sono documenti caricati per questo contratto</p>
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

export default ContrattoDetail;
