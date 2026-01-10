/**
 * Hello Module - Frontend Component
 *
 * Demonstrates a complete module with both backend and frontend.
 * This component calls the hello_module backend API endpoints.
 */
import { useState, useEffect } from 'react';
import './HelloPage.css';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

export function HelloPage() {
  const [unitaList, setUnitaList] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadData();
  }, []);

  async function loadData() {
    try {
      setLoading(true);

      // Fetch unita immobiliari from hello_module endpoint
      const unitaResponse = await fetch(`${API_BASE_URL}/hello/unita-demo`);
      if (!unitaResponse.ok) throw new Error('Failed to fetch unita');
      const unitaData = await unitaResponse.json();
      setUnitaList(unitaData);

      // Fetch stats from hello_module endpoint
      const statsResponse = await fetch(`${API_BASE_URL}/hello/stats-demo`);
      if (!statsResponse.ok) throw new Error('Failed to fetch stats');
      const statsData = await statsResponse.json();
      setStats(statsData);

      setLoading(false);
    } catch (err) {
      console.error('[HelloPage] Error loading data:', err);
      setError(err.message);
      setLoading(false);
    }
  }

  if (loading) {
    return (
      <div className="hello-page">
        <div className="loading">Caricamento modulo Hello...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="hello-page">
        <div className="error">
          <h2>Errore</h2>
          <p>{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="hello-page">
      <header className="hello-header">
        <h1>🔥 Hello Module Demo</h1>
        <p className="subtitle">Modulo di esempio con frontend e backend</p>
      </header>

      <section className="stats-section">
        <h2>Statistiche</h2>
        {stats && (
          <div className="stats-grid">
            <div className="stat-card">
              <div className="stat-value">{stats.total_unita}</div>
              <div className="stat-label">Unità Immobiliari</div>
            </div>
            <div className="stat-card">
              <div className="stat-value">{stats.superficie_totale_mq} m²</div>
              <div className="stat-label">Superficie Totale</div>
            </div>
            <div className="stat-card">
              <div className="stat-value">{stats.superficie_media_mq} m²</div>
              <div className="stat-label">Superficie Media</div>
            </div>
          </div>
        )}
      </section>

      <section className="unita-section">
        <h2>Unità Immobiliari Recenti</h2>
        <div className="unita-list">
          {unitaList.length === 0 ? (
            <p className="empty-message">Nessuna unità immobiliare trovata</p>
          ) : (
            <table className="unita-table">
              <thead>
                <tr>
                  <th>Indirizzo</th>
                  <th>Città</th>
                  <th>Superficie</th>
                  <th>Locali</th>
                  <th>Stato</th>
                </tr>
              </thead>
              <tbody>
                {unitaList.map((unita) => (
                  <tr key={unita.id}>
                    <td>{unita.indirizzo}</td>
                    <td>{unita.citta}</td>
                    <td>{unita.superficie_mq} m²</td>
                    <td>{unita.numero_locali || 'N/A'}</td>
                    <td>
                      <span className={`status-badge status-${unita.stato}`}>
                        {unita.stato}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </section>

      <section className="info-section">
        <div className="info-box">
          <h3>ℹ️ Informazioni Modulo</h3>
          <p>
            Questo è un modulo di esempio che dimostra l'integrazione completa frontend-backend
            nel sistema modulare di Gestione Affitti.
          </p>
          <ul>
            <li>✅ Backend API registrato dinamicamente</li>
            <li>✅ Frontend component caricato dinamicamente</li>
            <li>✅ Route registrata dal modulo</li>
            <li>✅ Menu item aggiunto automaticamente</li>
          </ul>
        </div>
      </section>
    </div>
  );
}

export default HelloPage;
