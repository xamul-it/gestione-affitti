import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { documentiAPI } from '../../../../services/documentiAPI';
import { AlertCircle, CircleCheck, Clock } from 'lucide-react';
import { Badge } from '../../../../components/UI';
import '../../../../components/UI/Button.css';
import { renderIcon } from '../../../../components/Navigation/iconRegistry.jsx';
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

      // APE documents expired or expiring within 90 days (effective scadenza).
      const res = await documentiAPI.list({
        entity_type: 'IMMOBILE', tipo_codice: 'APE', scadenza_entro_giorni: 90, limit: 500,
      });
      const allCertificati = (res.data || []).map((doc) => ({
        id: doc.id,
        unita_immobiliare_id: doc.entity_id,
        label: doc.entity_label,
        classe: doc.dati?.classe,
        data_scadenza: doc.data_scadenza_effettiva,
      }));

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
        <div className="widget-error" role="alert">{error}</div>
      </div>
    );
  }

  return (
    <div className="certificati-scadenza-widget">
      {/* Header */}
      <div className="widget-header">
        <h3 className="widget-title">
          <span className="widget-title-icon" aria-hidden="true">
            {renderIcon('leaf', { size: 18 })}
          </span>
          Certificati in Scadenza
        </h3>
        <Link to="/immobili/documenti?tipo=APE" className="view-all-link">
          Vedi tutto
        </Link>
      </div>

      {/* Stats Summary */}
      {(stats.scaduti > 0 || stats.in_scadenza > 0) && (
        <div className="stats-summary">
          {stats.scaduti > 0 && (
            <Badge variant="danger">
              <strong>{stats.scaduti}</strong> Scaduti
            </Badge>
          )}
          {stats.prossimi_30gg > 0 && (
            <Badge variant="warning">
              <strong>{stats.prossimi_30gg}</strong> Entro 30gg
            </Badge>
          )}
          {stats.in_scadenza - stats.prossimi_30gg > 0 && (
            <Badge variant="neutral">
              <strong>{stats.in_scadenza - stats.prossimi_30gg}</strong> Tra 31 e 90gg
            </Badge>
          )}
        </div>
      )}

      {/* Certificates List */}
      {certificati.length > 0 ? (
        <ul className="certificati-list">
          {certificati.map(cert => {
            const daysUntil = getDaysUntil(cert.data_scadenza);
            const UrgencyIcon = cert.urgency === 'scaduto' ? AlertCircle : Clock;

            return (
              <li key={cert.id} className={`certificato-item ${cert.urgency}`}>
                <span className="certificato-icon" aria-hidden="true">
                  <UrgencyIcon size={18} strokeWidth={1.7} />
                </span>
                <div className="certificato-content">
                  <div className="certificato-title">
                    {cert.label || `Immobile #${cert.unita_immobiliare_id}`}
                  </div>
                  <div className="certificato-subtitle">
                    {cert.classe ? `APE classe ${cert.classe}` : 'APE'}
                  </div>
                  <div className="certificato-date">
                    Scadenza: {formatDate(cert.data_scadenza)}
                    {daysUntil >= 0 && ` (${daysUntil} giorni)`}
                    {daysUntil < 0 && ` (scaduto da ${Math.abs(daysUntil)} giorni)`}
                  </div>
                </div>
              </li>
            );
          })}
        </ul>
      ) : (
        <div className="no-certificates">
          <CircleCheck size={40} strokeWidth={1.7} className="no-certificates-icon" aria-hidden="true" />
          <p>Nessun certificato in scadenza</p>
        </div>
      )}

      {/* Quick Action */}
      {certificati.length > 0 && (
        <div className="widget-actions">
          <Link to="/immobili/documenti?tipo=APE" className="ds-btn ds-btn--secondary ds-btn--md widget-action-btn">
            Gestisci Certificati
          </Link>
        </div>
      )}
    </div>
  );
}

export default CertificatiScadenzaWidget;
