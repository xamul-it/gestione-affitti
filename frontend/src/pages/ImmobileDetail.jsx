import { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import {
  unitaImmobiliariAPI,
  certificatiEnergeticiAPI,
  dirittiImmobileAPI,
  proprietariAPI
} from '../modules/immobili/services/immobiliAPI';
import { getSoggettoById } from '../modules/anagrafica_italiana/services/anagraficaAPI';
import { contrattiAPI, speseAPI, documentiAPI } from '../services/api';
import { UnitaImmobiliareForm } from '../modules/immobili';
import ScadenzeSection from '../components/Platform/Scadenze/ScadenzeSection';
import './ImmobileDetail.css';

function ImmobileDetail() {
  const { id } = useParams();
  const navigate = useNavigate();

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Main entity
  const [immobile, setImmobile] = useState(null);

  // Related data
  const [contratti, setContratti] = useState([]);
  const [spese, setSpese] = useState([]);
  const [certificati, setCertificati] = useState([]);
  const [documenti, setDocumenti] = useState([]);
  const [diritti, setDiritti] = useState([]);

  // UI state
  const [activeTab, setActiveTab] = useState('overview');
  const [showEditForm, setShowEditForm] = useState(false);
  const [loadingRelated, setLoadingRelated] = useState({
    contratti: true,
    spese: true,
    certificati: true,
    documenti: true,
    diritti: true
  });

  useEffect(() => {
    fetchData();
  }, [id]);

  const fetchData = async () => {
    setLoading(true);
    setError(null);

    try {
      // 1. Fetch main entity
      const immobileResponse = await unitaImmobiliariAPI.getById(id);
      setImmobile(immobileResponse.data);

      // 2. Fetch related data in parallel
      Promise.all([
        fetchContratti(),
        fetchSpese(),
        fetchCertificati(),
        fetchDocumenti(),
        fetchDiritti()
      ]);

      setLoading(false);
    } catch (err) {
      console.error('Error fetching immobile:', err);
      setError('Errore nel caricamento dei dati');
      setLoading(false);
    }
  };

  const fetchContratti = async () => {
    try {
      const response = await contrattiAPI.getByImmobile(id);
      setContratti(response.data);
    } catch (err) {
      console.error('Error fetching contratti:', err);
    } finally {
      setLoadingRelated(prev => ({ ...prev, contratti: false }));
    }
  };

  const fetchSpese = async () => {
    try {
      const response = await speseAPI.getByImmobile(id);
      setSpese(response.data);
    } catch (err) {
      console.error('Error fetching spese:', err);
    } finally {
      setLoadingRelated(prev => ({ ...prev, spese: false }));
    }
  };

  const fetchCertificati = async () => {
    try {
      const response = await certificatiEnergeticiAPI.getByImmobile(id);
      setCertificati(response.data);
    } catch (err) {
      console.error('Error fetching certificati:', err);
    } finally {
      setLoadingRelated(prev => ({ ...prev, certificati: false }));
    }
  };

  const fetchDocumenti = async () => {
    try {
      const response = await documentiAPI.getByEntity('immobile', id);
      setDocumenti(response.data);
    } catch (err) {
      console.error('Error fetching documenti:', err);
    } finally {
      setLoadingRelated(prev => ({ ...prev, documenti: false }));
    }
  };

  const fetchDiritti = async () => {
    try {
      const response = await dirittiImmobileAPI.getByImmobile(id);
      const diritti = response.data;

      // DirittoImmobileResponse only carries proprietario_id — resolve the
      // display name through the proprietario's linked soggetto anagrafico.
      const proprietariIds = [...new Set(diritti.map(d => d.proprietario_id))];
      const proprietariById = {};
      await Promise.all(
        proprietariIds.map(async (propId) => {
          try {
            const propResp = await proprietariAPI.getById(propId);
            const soggetto = await getSoggettoById(propResp.data.soggetto_id);
            const nome = soggetto.ragione_sociale || [soggetto.nome, soggetto.cognome].filter(Boolean).join(' ');
            proprietariById[propId] = { id: propId, nome: nome || `Soggetto #${propResp.data.soggetto_id}`, cognome: '' };
          } catch (err) {
            console.error(`Errore caricamento proprietario ${propId}:`, err);
            proprietariById[propId] = { id: propId, nome: `Proprietario #${propId}`, cognome: '' };
          }
        })
      );

      setDiritti(diritti.map(d => ({ ...d, proprietario: proprietariById[d.proprietario_id] })));
    } catch (err) {
      console.error('Error fetching diritti:', err);
    } finally {
      setLoadingRelated(prev => ({ ...prev, diritti: false }));
    }
  };

  const getStatoContrattoColor = (stato) => {
    const colors = {
      'ATTIVO': 'success',
      'SCADUTO': 'warning',
      'DISDETTO': 'danger',
      'TERMINATO': 'secondary'
    };
    return colors[stato] || 'secondary';
  };

  const getClasseEnergeticaColor = (classe) => {
    const colors = {
      'A4': '#00a152', 'A3': '#2e7d32', 'A2': '#558b2f', 'A1': '#689f38',
      'B': '#9ccc65', 'C': '#c0ca33', 'D': '#fdd835',
      'E': '#ffb300', 'F': '#f57c00', 'G': '#e64a19'
    };
    return colors[classe] || '#9e9e9e';
  };

  if (loading && !immobile) {
    return (
      <div className="immobile-detail-container">
        <div className="loading-skeleton">
          <div className="skeleton-header" />
          <div className="skeleton-body" />
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="immobile-detail-container">
        <div className="error-message">
          <span className="error-icon">⚠️</span>
          <p>{error}</p>
          <button onClick={() => navigate('/immobili')}>
            Torna alla lista
          </button>
        </div>
      </div>
    );
  }

  if (!immobile) {
    return <div>Immobile non trovato</div>;
  }

  // Calculate stats
  const contrattoAttivo = contratti.find(c => c.stato === 'ATTIVO');
  const totaleSpese = spese.reduce((sum, s) => sum + parseFloat(s.importo || 0), 0);
  const speseNonPagate = spese.filter(s => s.pagata === 0).length;
  const certificatoValido = certificati.find(c => {
    if (!c.data_scadenza) return false;
    return new Date(c.data_scadenza) > new Date();
  });

  return (
    <div className="immobile-detail-container">
      {/* Header with Back Button */}
      <div className="detail-header">
        <button className="back-button" onClick={() => navigate('/unita-immobiliari')}>
          ← Torna alla lista
        </button>
        <div className="header-actions">
          <button className="btn-secondary" onClick={() => setShowEditForm(true)}>
            Modifica
          </button>
          <button className="btn-primary">
            Nuovo Contratto
          </button>
        </div>
      </div>

      {/* Edit Form Modal */}
      {showEditForm && (
        <UnitaImmobiliareForm
          unitaImmobiliare={immobile}
          onClose={() => {
            setShowEditForm(false);
            fetchData(); // Refresh data after edit
          }}
        />
      )}

      {/* Main Info Card */}
      <div className="immobile-main-card">
        <div className="card-header">
          <div className="property-icon">🏢</div>
          <div className="property-info">
            <h1>{immobile.indirizzo}</h1>
            <p className="subtitle">
              {immobile.citta} ({immobile.cap}) • Codice: {immobile.codice}
            </p>
          </div>
          <div className="status-badges">
            {contrattoAttivo && (
              <span className="badge badge-success">
                Affittato
              </span>
            )}
            {!contrattoAttivo && (
              <span className="badge badge-warning">
                Libero
              </span>
            )}
            {certificatoValido && (
              <span
                className="badge badge-energy"
                style={{ backgroundColor: getClasseEnergeticaColor(certificatoValido.classe_energetica) }}
              >
                Classe {certificatoValido.classe_energetica}
              </span>
            )}
          </div>
        </div>

        {/* Key Stats */}
        <div className="quick-stats">
          <div className="stat-card">
            <span className="stat-icon">📄</span>
            <div className="stat-content">
              <div className="stat-value">{contratti.length}</div>
              <div className="stat-label">Contratti</div>
            </div>
          </div>
          <div className="stat-card">
            <span className="stat-icon">💰</span>
            <div className="stat-content">
              <div className="stat-value">€ {totaleSpese.toLocaleString('it-IT')}</div>
              <div className="stat-label">Totale Spese</div>
            </div>
          </div>
          <div className="stat-card">
            <span className="stat-icon">⚠️</span>
            <div className="stat-content">
              <div className="stat-value">{speseNonPagate}</div>
              <div className="stat-label">Spese da pagare</div>
            </div>
          </div>
          <div className="stat-card">
            <span className="stat-icon">📎</span>
            <div className="stat-content">
              <div className="stat-value">{documenti.length}</div>
              <div className="stat-label">Documenti</div>
            </div>
          </div>
        </div>

        {/* Property Details Grid */}
        <div className="property-details-grid">
          <div className="detail-item">
            <span className="detail-label">Tipo</span>
            <span className="detail-value">{immobile.tipo || 'N/D'}</span>
          </div>
          <div className="detail-item">
            <span className="detail-label">Categoria Catastale</span>
            <span className="detail-value">
              {immobile.categoria_catastale
                ? `${immobile.categoria_catastale.codice} - ${immobile.categoria_catastale.nome}`
                : 'N/D'}
            </span>
          </div>
          <div className="detail-item">
            <span className="detail-label">Superficie</span>
            <span className="detail-value">{immobile.superficie ? `${immobile.superficie} m²` : 'N/D'}</span>
          </div>
          <div className="detail-item">
            <span className="detail-label">Locali</span>
            <span className="detail-value">{immobile.numero_locali || 'N/D'}</span>
          </div>
          <div className="detail-item">
            <span className="detail-label">Bagni</span>
            <span className="detail-value">{immobile.numero_bagni || 'N/D'}</span>
          </div>
          <div className="detail-item">
            <span className="detail-label">Piano</span>
            <span className="detail-value">{immobile.piano || 'N/D'}</span>
          </div>
          <div className="detail-item">
            <span className="detail-label">Box/Posto Auto</span>
            <span className="detail-value">{immobile.box_auto ? 'Sì' : 'No'}</span>
          </div>
        </div>

        {/* Cadastral Data */}
        {(immobile.foglio || immobile.particella || immobile.subalterno) && (
          <div className="cadastral-section">
            <h3>Dati Catastali</h3>
            <div className="cadastral-grid">
              {immobile.foglio && (
                <div className="cadastral-item">
                  <span className="label">Foglio</span>
                  <span className="value">{immobile.foglio}</span>
                </div>
              )}
              {immobile.particella && (
                <div className="cadastral-item">
                  <span className="label">Particella</span>
                  <span className="value">{immobile.particella}</span>
                </div>
              )}
              {immobile.subalterno && (
                <div className="cadastral-item">
                  <span className="label">Subalterno</span>
                  <span className="value">{immobile.subalterno}</span>
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Tabs Navigation */}
      <div className="detail-tabs">
        <button
          className={`tab ${activeTab === 'overview' ? 'active' : ''}`}
          onClick={() => setActiveTab('overview')}
        >
          Panoramica
        </button>
        <button
          className={`tab ${activeTab === 'contratti' ? 'active' : ''}`}
          onClick={() => setActiveTab('contratti')}
        >
          Contratti ({contratti.length})
        </button>
        <button
          className={`tab ${activeTab === 'spese' ? 'active' : ''}`}
          onClick={() => setActiveTab('spese')}
        >
          Spese ({spese.length})
        </button>
        <button
          className={`tab ${activeTab === 'certificati' ? 'active' : ''}`}
          onClick={() => setActiveTab('certificati')}
        >
          Certificati ({certificati.length})
        </button>
        <button
          className={`tab ${activeTab === 'documenti' ? 'active' : ''}`}
          onClick={() => setActiveTab('documenti')}
        >
          Documenti ({documenti.length})
        </button>
        <button
          className={`tab ${activeTab === 'proprieta' ? 'active' : ''}`}
          onClick={() => setActiveTab('proprieta')}
        >
          Proprietà ({diritti.length})
        </button>
      </div>

      {/* Tab Content */}
      <div className="tab-content">
        {activeTab === 'overview' && (
          <div className="overview-grid">
            {/* Quick view of all sections */}
            <OverviewSection
              title="Contratto Attivo"
              icon="📄"
              data={contrattoAttivo}
              emptyMessage="Nessun contratto attivo"
            >
              {contrattoAttivo && (
                <div className="overview-card">
                  <div className="overview-header">
                    <h4>{contrattoAttivo.numero_contratto}</h4>
                    <span className={`badge badge-${getStatoContrattoColor(contrattoAttivo.stato)}`}>
                      {contrattoAttivo.stato}
                    </span>
                  </div>
                  <div className="overview-details">
                    <p><strong>Affittuario:</strong> {contrattoAttivo.affittuario?.nome} {contrattoAttivo.affittuario?.cognome}</p>
                    <p><strong>Canone:</strong> € {parseFloat(contrattoAttivo.canone_mensile).toLocaleString('it-IT')}/mese</p>
                    <p><strong>Scadenza:</strong> {new Date(contrattoAttivo.data_fine).toLocaleDateString('it-IT')}</p>
                  </div>
                  <Link to={`/contratti/${contrattoAttivo.id}`} className="link-detail">
                    Vedi dettagli →
                  </Link>
                </div>
              )}
            </OverviewSection>

            <OverviewSection
              title="Spese Recenti"
              icon="💰"
              data={spese.slice(0, 3)}
              emptyMessage="Nessuna spesa registrata"
            >
              <div className="spese-quick-list">
                {spese.slice(0, 3).map(spesa => (
                  <div key={spesa.id} className="spesa-quick-item">
                    <div className="spesa-info">
                      <span className="spesa-desc">{spesa.descrizione}</span>
                      <span className="spesa-date">
                        {new Date(spesa.data).toLocaleDateString('it-IT')}
                      </span>
                    </div>
                    <div className="spesa-amount">
                      <span className="amount">€ {parseFloat(spesa.importo).toLocaleString('it-IT')}</span>
                      {spesa.pagata === 0 && (
                        <span className="badge badge-warning badge-small">Da pagare</span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
              {spese.length > 3 && (
                <button
                  className="show-all-link"
                  onClick={() => setActiveTab('spese')}
                >
                  Vedi tutte le spese ({spese.length}) →
                </button>
              )}
            </OverviewSection>

            <OverviewSection
              title="Certificato Energetico"
              icon="⚡"
              data={certificatoValido}
              emptyMessage="Nessun certificato valido"
            >
              {certificatoValido && (
                <div className="cert-overview-card">
                  <div
                    className="cert-class-badge"
                    style={{ backgroundColor: getClasseEnergeticaColor(certificatoValido.classe_energetica) }}
                  >
                    Classe {certificatoValido.classe_energetica}
                  </div>
                  <div className="cert-details">
                    <p><strong>EPgl,nren:</strong> {certificatoValido.indice_prestazione_energetica} kWh/m²anno</p>
                    <p><strong>Scadenza:</strong> {new Date(certificatoValido.data_scadenza).toLocaleDateString('it-IT')}</p>
                    <p><strong>Certificatore:</strong> {certificatoValido.certificatore}</p>
                  </div>
                </div>
              )}
            </OverviewSection>

            <OverviewSection
              title="Proprietari"
              icon="👥"
              data={diritti}
              emptyMessage="Nessun proprietario registrato"
            >
              <div className="proprietari-list">
                {diritti.map(diritto => (
                  <div key={diritto.id} className="proprietario-item">
                    <span className="prop-name">
                      {diritto.proprietario?.nome}
                    </span>
                    <span className="prop-quota">
                      {diritto.quota_percentuale != null ? `${diritto.quota_percentuale}% • ` : ''}{diritto.tipo_diritto}
                    </span>
                  </div>
                ))}
              </div>
            </OverviewSection>
          </div>
        )}

        {activeTab === 'contratti' && (
          <ContrattiSection
            contratti={contratti}
            loading={loadingRelated.contratti}
            onRefresh={fetchContratti}
          />
        )}

        {activeTab === 'spese' && (
          <SpeseSection
            spese={spese}
            loading={loadingRelated.spese}
            onRefresh={fetchSpese}
          />
        )}

        {activeTab === 'certificati' && (
          <CertificatiSection
            certificati={certificati}
            loading={loadingRelated.certificati}
            onRefresh={fetchCertificati}
          />
        )}

        {activeTab === 'documenti' && (
          <DocumentiSection
            documenti={documenti}
            loading={loadingRelated.documenti}
            onRefresh={fetchDocumenti}
            entityType="immobile"
            entityId={id}
          />
        )}

        {activeTab === 'proprieta' && (
          <ProprietaSection
            diritti={diritti}
            loading={loadingRelated.diritti}
            onRefresh={fetchDiritti}
          />
        )}
      </div>

      {/* Scadenze Section */}
      <ScadenzeSection
        modulo="immobili"
        entityType="unita_immobiliare"
        entityId={parseInt(id)}
        title="Scadenze Immobile"
        initialCollapsed={false}
      />
    </div>
  );
}

// Helper Components
function OverviewSection({ title, icon, data, emptyMessage, children }) {
  const hasData = Array.isArray(data) ? data.length > 0 : data;

  return (
    <div className="overview-section">
      <div className="section-header">
        <span className="section-icon">{icon}</span>
        <h3>{title}</h3>
      </div>
      {hasData ? (
        children
      ) : (
        <div className="empty-state">
          <p>{emptyMessage}</p>
        </div>
      )}
    </div>
  );
}

function ContrattiSection({ contratti, loading }) {
  if (loading) return <div className="loading">Caricamento contratti...</div>;

  if (contratti.length === 0) {
    return (
      <div className="empty-state-large">
        <span className="empty-icon">📄</span>
        <h3>Nessun contratto</h3>
        <p>Non ci sono contratti associati a questo immobile</p>
        <button className="btn-primary">Crea Nuovo Contratto</button>
      </div>
    );
  }

  return (
    <div className="contratti-table-wrapper">
      <table className="detail-table">
        <thead>
          <tr>
            <th>Numero</th>
            <th>Affittuario</th>
            <th>Periodo</th>
            <th>Canone</th>
            <th>Stato</th>
            <th>Azioni</th>
          </tr>
        </thead>
        <tbody>
          {contratti.map(contratto => (
            <tr key={contratto.id}>
              <td>
                <Link to={`/contratti/${contratto.id}`} className="table-link">
                  {contratto.numero_contratto}
                </Link>
              </td>
              <td>
                {contratto.affittuario && (
                  <Link to={`/affittuari/${contratto.affittuario_id}`} className="table-link">
                    {contratto.affittuario.nome} {contratto.affittuario.cognome}
                  </Link>
                )}
              </td>
              <td>
                {new Date(contratto.data_inizio).toLocaleDateString('it-IT')} -
                {new Date(contratto.data_fine).toLocaleDateString('it-IT')}
              </td>
              <td className="amount">€ {parseFloat(contratto.canone_mensile).toLocaleString('it-IT')}</td>
              <td>
                <span className={`badge badge-${contratto.stato === 'ATTIVO' ? 'success' : 'secondary'}`}>
                  {contratto.stato}
                </span>
              </td>
              <td>
                <div className="action-buttons">
                  <button className="btn-icon" title="Vedi dettagli">
                    👁️
                  </button>
                  <button className="btn-icon" title="Modifica">
                    ✏️
                  </button>
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function SpeseSection({ spese, loading }) {
  if (loading) return <div className="loading">Caricamento spese...</div>;

  if (spese.length === 0) {
    return (
      <div className="empty-state-large">
        <span className="empty-icon">💰</span>
        <h3>Nessuna spesa</h3>
        <p>Non ci sono spese registrate per questo immobile</p>
        <button className="btn-primary">Registra Spesa</button>
      </div>
    );
  }

  const totale = spese.reduce((sum, s) => sum + parseFloat(s.importo || 0), 0);
  const pagate = spese.filter(s => s.pagata === 1).reduce((sum, s) => sum + parseFloat(s.importo || 0), 0);
  const daPagare = totale - pagate;

  return (
    <div>
      <div className="spese-summary">
        <div className="summary-card">
          <span className="summary-label">Totale Spese</span>
          <span className="summary-value">€ {totale.toLocaleString('it-IT')}</span>
        </div>
        <div className="summary-card success">
          <span className="summary-label">Pagate</span>
          <span className="summary-value">€ {pagate.toLocaleString('it-IT')}</span>
        </div>
        <div className="summary-card warning">
          <span className="summary-label">Da Pagare</span>
          <span className="summary-value">€ {daPagare.toLocaleString('it-IT')}</span>
        </div>
      </div>

      <table className="detail-table">
        <thead>
          <tr>
            <th>Data</th>
            <th>Descrizione</th>
            <th>Categoria</th>
            <th>Fornitore</th>
            <th>Importo</th>
            <th>Stato</th>
          </tr>
        </thead>
        <tbody>
          {spese.map(spesa => (
            <tr key={spesa.id}>
              <td>{new Date(spesa.data).toLocaleDateString('it-IT')}</td>
              <td>{spesa.descrizione}</td>
              <td>
                <span className="badge badge-secondary">{spesa.categoria}</span>
              </td>
              <td>{spesa.fornitore || '-'}</td>
              <td className="amount">€ {parseFloat(spesa.importo).toLocaleString('it-IT')}</td>
              <td>
                {spesa.pagata === 1 ? (
                  <span className="badge badge-success">Pagata</span>
                ) : (
                  <span className="badge badge-warning">Da pagare</span>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function CertificatiSection({ certificati, loading }) {
  if (loading) return <div className="loading">Caricamento certificati...</div>;

  if (certificati.length === 0) {
    return (
      <div className="empty-state-large">
        <span className="empty-icon">⚡</span>
        <h3>Nessun certificato</h3>
        <p>Non ci sono certificati energetici per questo immobile</p>
        <button className="btn-primary">Aggiungi Certificato</button>
      </div>
    );
  }

  return (
    <div className="certificati-grid">
      {certificati.map(cert => {
        const isValido = cert.data_scadenza && new Date(cert.data_scadenza) > new Date();
        const getClasseColor = (classe) => {
          const colors = {
            'A4': '#00a152', 'A3': '#2e7d32', 'A2': '#558b2f', 'A1': '#689f38',
            'B': '#9ccc65', 'C': '#c0ca33', 'D': '#fdd835',
            'E': '#ffb300', 'F': '#f57c00', 'G': '#e64a19'
          };
          return colors[classe] || '#9e9e9e';
        };

        return (
          <div key={cert.id} className="certificato-card">
            <div className="cert-header">
              <div
                className="cert-class"
                style={{ backgroundColor: getClasseColor(cert.classe_energetica) }}
              >
                Classe {cert.classe_energetica}
              </div>
              {isValido ? (
                <span className="badge badge-success">Valido</span>
              ) : (
                <span className="badge badge-danger">Scaduto</span>
              )}
            </div>
            <div className="cert-body">
              <div className="cert-detail">
                <span className="label">EPgl,nren</span>
                <span className="value">{cert.indice_prestazione_energetica} kWh/m²anno</span>
              </div>
              <div className="cert-detail">
                <span className="label">Emissione</span>
                <span className="value">{new Date(cert.data_emissione).toLocaleDateString('it-IT')}</span>
              </div>
              <div className="cert-detail">
                <span className="label">Scadenza</span>
                <span className="value">{new Date(cert.data_scadenza).toLocaleDateString('it-IT')}</span>
              </div>
              <div className="cert-detail">
                <span className="label">Certificatore</span>
                <span className="value">{cert.certificatore}</span>
              </div>
              {cert.numero_protocollo && (
                <div className="cert-detail">
                  <span className="label">Protocollo</span>
                  <span className="value">{cert.numero_protocollo}</span>
                </div>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}

function DocumentiSection({ documenti, loading }) {
  if (loading) return <div className="loading">Caricamento documenti...</div>;

  if (documenti.length === 0) {
    return (
      <div className="empty-state-large">
        <span className="empty-icon">📎</span>
        <h3>Nessun documento</h3>
        <p>Non ci sono documenti allegati a questo immobile</p>
        <button className="btn-primary">Carica Documento</button>
      </div>
    );
  }

  const handleDownload = async (doc) => {
    try {
      const response = await documentiAPI.download(doc.id);
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', doc.nome_file);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (err) {
      console.error('Error downloading:', err);
      alert('Errore nel download del documento');
    }
  };

  const getFileIcon = (filename) => {
    const ext = filename.split('.').pop().toLowerCase();
    const icons = {
      'pdf': '📄',
      'doc': '📝', 'docx': '📝',
      'xls': '📊', 'xlsx': '📊',
      'jpg': '🖼️', 'jpeg': '🖼️', 'png': '🖼️', 'gif': '🖼️',
      'zip': '📦', 'rar': '📦'
    };
    return icons[ext] || '📎';
  };

  return (
    <div className="documenti-list">
      {documenti.map(doc => (
        <div key={doc.id} className="documento-item">
          <span className="doc-icon">{getFileIcon(doc.nome_file)}</span>
          <div className="doc-info">
            <div className="doc-name">{doc.nome_file}</div>
            <div className="doc-meta">
              {doc.descrizione && <span className="doc-desc">{doc.descrizione}</span>}
              <span className="doc-date">
                Caricato il {new Date(doc.data_upload).toLocaleDateString('it-IT')}
              </span>
            </div>
          </div>
          <button
            className="btn-icon download"
            onClick={() => handleDownload(doc)}
            title="Scarica"
          >
            ⬇️
          </button>
        </div>
      ))}
    </div>
  );
}

function ProprietaSection({ diritti, loading }) {
  if (loading) return <div className="loading">Caricamento dati proprietà...</div>;

  if (diritti.length === 0) {
    return (
      <div className="empty-state-large">
        <span className="empty-icon">👥</span>
        <h3>Nessun proprietario</h3>
        <p>Non ci sono proprietari registrati per questo immobile</p>
        <button className="btn-primary">Aggiungi Proprietario</button>
      </div>
    );
  }

  const totalePossesso = diritti.reduce((sum, d) => sum + parseFloat(d.quota_percentuale || 0), 0);

  return (
    <div>
      <div className="proprieta-summary">
        <h3>Quote di Possesso</h3>
        <div className="progress-bar-container">
          {diritti.map((diritto, index) => (
            <div
              key={diritto.id}
              className="progress-segment"
              style={{
                width: `${diritto.quota_percentuale || 0}%`,
                backgroundColor: `hsl(${index * 60}, 70%, 50%)`
              }}
              title={`${diritto.proprietario?.nome}: ${diritto.quota_percentuale ?? '-'}%`}
            />
          ))}
        </div>
        {totalePossesso !== 100 && (
          <div className="warning-message">
            ⚠️ Attenzione: Le quote sommano al {totalePossesso}% (dovrebbe essere 100%)
          </div>
        )}
      </div>

      <table className="detail-table">
        <thead>
          <tr>
            <th>Proprietario</th>
            <th>Tipo Diritto</th>
            <th>Quota Possesso</th>
            <th>Data Inizio</th>
            <th>Data Fine</th>
            <th>Azioni</th>
          </tr>
        </thead>
        <tbody>
          {diritti.map(diritto => (
            <tr key={diritto.id}>
              <td>
                {diritto.proprietario && (
                  <Link to="/proprietari" className="table-link">
                    {diritto.proprietario.nome}
                  </Link>
                )}
              </td>
              <td>
                <span className="badge badge-info">{diritto.tipo_diritto}</span>
              </td>
              <td>
                <strong>{diritto.quota_percentuale != null ? `${diritto.quota_percentuale}%` : '-'}</strong>
              </td>
              <td>{diritto.data_inizio ? new Date(diritto.data_inizio).toLocaleDateString('it-IT') : '-'}</td>
              <td>{diritto.data_fine ? new Date(diritto.data_fine).toLocaleDateString('it-IT') : 'Indefinito'}</td>
              <td>
                <div className="action-buttons">
                  <button className="btn-icon" title="Modifica">
                    ✏️
                  </button>
                  <button className="btn-icon danger" title="Elimina">
                    🗑️
                  </button>
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default ImmobileDetail;
