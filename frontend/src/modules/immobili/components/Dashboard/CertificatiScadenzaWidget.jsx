import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { certificatiEnergeticiAPI, unitaImmobiliariAPI } from '../../services/immobiliAPI';
import './CertificatiScadenzaWidget.css';

/**
 * CertificatiScadenzaWidget - Dashboard widget for expiring energy certificates
 *
 * Shows certificates expiring within the next 90 days and alerts
 */
function CertificatiScadenzaWidget() {
  const [certificati, setCertificati] = useState([]);
  const [stats, setStats] = useState({
    scaduti: 0,
    in_scadenza: 0,
    prossimi_30gg: 0,
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadCertificati();
  }, []);

  const loadCertificati = async () => {
    try {
      setLoading(true);
      setError(null);

      // Get token
      const token = localStorage.getItem('access_token');

      // Configure axios interceptor for authentication
      const setupAuth = (apiCall) => {
        const originalRequest = apiCall;
        originalRequest.defaults = originalRequest.defaults || {};
        originalRequest.defaults.headers = originalRequest.defaults.headers || {};
        originalRequest.defaults.headers.common = originalRequest.defaults.headers.common || {};
        originalRequest.defaults.headers.common['Authorization'] = `Bearer ${token}`;
        return apiCall;
      };

      // Get all certificati and immobili
      const [certificatiRes, immobiliRes] = await Promise.all([
        setupAuth(certificatiEnergeticiAPI).getAll(),
        setupAuth(unitaImmobiliariAPI).getAll(),
      ]);

      const allCertificati = certificatiRes.data;
      const immobili = immobiliRes.data;

      // Create immobili lookup
      const immobiliMap = {};
      immobili.forEach(imm => {
        immobiliMap[imm.id] = imm;
      });

      // Calculate dates
      const today = new Date();
      const in30Days = new Date();
      in30Days.setDate(today.getDate() + 30);
      const in90Days = new Date();
      in90Days.setDate(today.getDate() + 90);

      // Filter and categorize certificates
      let scaduti = 0;
      let in_scadenza = 0;
      let prossimi_30gg = 0;

      const certificatiInScadenza = allCertificati
        .map(cert => {
          const dataScadenza = new Date(cert.data_scadenza);
          const immobile = immobiliMap[cert.unita_immobiliare_id];

          // Calculate urgency
          let urgency = 'ok';
          if (dataScadenza < today) {
            urgency = 'scaduto';
            scaduti++;
          } else if (dataScadenza < in30Days) {
            urgency = 'urgente';
            prossimi_30gg++;
            in_scadenza++;
          } else if (dataScadenza < in90Days) {
            urgency = 'attenzione';
            in_scadenza++;
          }

          return {
            ...cert,
            immobile,
            dataScadenza,
            urgency,
          };
        })
        .filter(cert => cert.urgency !== 'ok')
        .sort((a, b) => a.dataScadenza - b.dataScadenza)
        .slice(0, 5); // Show max 5

      setCertificati(certificatiInScadenza);
      setStats({ scaduti, in_scadenza, prossimi_30gg });
    } catch (err) {
      console.error('Error loading certificati scadenza:', err);
      setError('Errore nel caricamento dei certificati');
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('it-IT', { day: '2-digit', month: '2-digit', year: 'numeric' });
  };

  const getDaysUntil = (dateString) => {
    const today = new Date();
    const target = new Date(dateString);
    const diffTime = target - today;
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    return diffDays;
  };

  if (loading) {
    return (
      <div className="certificati-scadenza-widget">
        <div className="widget-loading">Caricamento...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="certificati-scadenza-widget">
        <div className="widget-error">{error}</div>
      </div>
    );
  }

  return (
    <div className="certificati-scadenza-widget">
      {/* Header */}
      <div className="widget-header">
        <h3>⚠️ Certificati in Scadenza</h3>
        <Link to="/certificati-energetici" className="view-all-link">
          Vedi tutto
        </Link>
      </div>

      {/* Stats Summary */}
      <div className="stats-summary">
        {stats.scaduti > 0 && (
          <div className="stat-badge scaduto">
            <span className="badge-value">{stats.scaduti}</span>
            <span className="badge-label">Scaduti</span>
          </div>
        )}
        {stats.prossimi_30gg > 0 && (
          <div className="stat-badge urgente">
            <span className="badge-value">{stats.prossimi_30gg}</span>
            <span className="badge-label">Entro 30gg</span>
          </div>
        )}
        {stats.in_scadenza > 0 && (
          <div className="stat-badge attenzione">
            <span className="badge-value">{stats.in_scadenza}</span>
            <span className="badge-label">Entro 90gg</span>
          </div>
        )}
      </div>

      {/* Certificates List */}
      {certificati.length > 0 ? (
        <div className="certificati-list">
          {certificati.map(cert => {
            const daysUntil = getDaysUntil(cert.data_scadenza);

            return (
              <div key={cert.id} className={`certificato-item ${cert.urgency}`}>
                <div className="certificato-icon">
                  {cert.urgency === 'scaduto' && '🔴'}
                  {cert.urgency === 'urgente' && '🟠'}
                  {cert.urgency === 'attenzione' && '🟡'}
                </div>
                <div className="certificato-content">
                  <div className="certificato-title">
                    {cert.immobile ? cert.immobile.codice : `Immobile #${cert.unita_immobiliare_id}`}
                  </div>
                  <div className="certificato-subtitle">
                    {cert.immobile?.indirizzo || 'Indirizzo non disponibile'}
                  </div>
                  <div className="certificato-date">
                    Scadenza: {formatDate(cert.data_scadenza)}
                    {daysUntil >= 0 && ` (${daysUntil} giorni)`}
                    {daysUntil < 0 && ` (scaduto da ${Math.abs(daysUntil)} giorni)`}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      ) : (
        <div className="no-certificates">
          <div className="icon">✓</div>
          <p>Nessun certificato in scadenza</p>
        </div>
      )}

      {/* Quick Action */}
      {certificati.length > 0 && (
        <div className="widget-actions">
          <Link to="/certificati-energetici" className="btn btn-warning btn-block">
            Gestisci Certificati
          </Link>
        </div>
      )}
    </div>
  );
}

export default CertificatiScadenzaWidget;
