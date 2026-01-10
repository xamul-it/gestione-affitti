import { useState, useEffect } from 'react';
import { terreniAPI } from '../../services/immobiliAPI';
import TerrenoForm from './TerrenoForm';
import './Terreni.css';

// Mapping tipologia to display label
const TIPOLOGIA_LABELS = {
  AGR: 'Agricolo',
  EDI: 'Edificabile',
  BOS: 'Bosco/Forestale',
  IND: 'Industriale',
  ALT: 'Altro',
};

function TerreniList() {
  const [terreni, setTerreni] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showForm, setShowForm] = useState(false);
  const [editingTerreno, setEditingTerreno] = useState(null);
  const [filtroTipologia, setFiltroTipologia] = useState('');
  const [filtroAttivi, setFiltroAttivi] = useState(false);

  useEffect(() => {
    fetchTerreni();
  }, [filtroTipologia, filtroAttivi]);

  const fetchTerreni = async () => {
    try {
      setLoading(true);
      const response = await terreniAPI.getAll(filtroAttivi, filtroTipologia || null);
      setTerreni(response.data);
      setError(null);
    } catch (err) {
      setError('Errore nel caricamento dei terreni');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id) => {
    if (window.confirm('Sei sicuro di voler disattivare questo terreno?')) {
      try {
        await terreniAPI.delete(id);
        fetchTerreni();
      } catch (err) {
        setError('Errore nella disattivazione del terreno');
        console.error(err);
      }
    }
  };

  const handleRestore = async (id) => {
    try {
      await terreniAPI.restore(id);
      fetchTerreni();
    } catch (err) {
      setError('Errore nel ripristino del terreno');
      console.error(err);
    }
  };

  const handleEdit = (terreno) => {
    setEditingTerreno(terreno);
    setShowForm(true);
  };

  const handleFormClose = () => {
    setShowForm(false);
    setEditingTerreno(null);
    fetchTerreni();
  };

  const formatSuperficie = (superficie, unitaMisura) => {
    if (!superficie) return '-';
    const unita = unitaMisura || 'mq';
    return `${superficie.toLocaleString('it-IT')} ${unita}`;
  };

  if (loading) return <div className="loading">Caricamento...</div>;
  if (error) return <div className="error">{error}</div>;

  return (
    <div className="terreni-container">
      <div className="header">
        <h1>Gestione Terreni</h1>
        <div className="header-actions">
          <button onClick={() => setShowForm(true)}>Nuovo Terreno</button>
        </div>
      </div>

      <div className="filters-row">
        <div className="filter-group">
          <label>Tipologia:</label>
          <select
            value={filtroTipologia}
            onChange={(e) => setFiltroTipologia(e.target.value)}
          >
            <option value="">Tutte</option>
            <option value="AGR">Agricolo</option>
            <option value="EDI">Edificabile</option>
            <option value="BOS">Bosco/Forestale</option>
            <option value="IND">Industriale</option>
            <option value="ALT">Altro</option>
          </select>
        </div>
        <div className="filter-group">
          <label>
            <input
              type="checkbox"
              checked={filtroAttivi}
              onChange={(e) => setFiltroAttivi(e.target.checked)}
            />
            Solo attivi
          </label>
        </div>
      </div>

      {showForm && (
        <TerrenoForm
          terreno={editingTerreno}
          onClose={handleFormClose}
        />
      )}

      {terreni.length === 0 ? (
        <div className="card">
          <p>Nessun terreno presente. Clicca su "Nuovo Terreno" per iniziare.</p>
        </div>
      ) : (
        <table>
          <thead>
            <tr>
              <th>Codice</th>
              <th>Nome</th>
              <th>Tipologia</th>
              <th>Comune</th>
              <th>Provincia</th>
              <th>Superficie</th>
              <th>Foglio/Particella</th>
              <th>Stato</th>
              <th>Azioni</th>
            </tr>
          </thead>
          <tbody>
            {terreni.map((terreno) => (
              <tr key={terreno.id} className={!terreno.attivo ? 'inactive-row' : ''}>
                <td>{terreno.codice}</td>
                <td>{terreno.nome}</td>
                <td>
                  <span className={`badge tipologia-${terreno.tipologia.toLowerCase()}`}>
                    {TIPOLOGIA_LABELS[terreno.tipologia] || terreno.tipologia}
                  </span>
                </td>
                <td>{terreno.comune}</td>
                <td>{terreno.provincia}</td>
                <td>{formatSuperficie(terreno.superficie, terreno.unita_misura_superficie)}</td>
                <td>
                  {terreno.foglio && terreno.particella
                    ? `${terreno.foglio}/${terreno.particella}`
                    : '-'}
                </td>
                <td>
                  <span className={`badge ${terreno.attivo ? 'active' : 'inactive'}`}>
                    {terreno.attivo ? 'Attivo' : 'Inattivo'}
                  </span>
                </td>
                <td>
                  <div className="action-buttons">
                    <button className="secondary" onClick={() => handleEdit(terreno)}>
                      Modifica
                    </button>
                    {terreno.attivo ? (
                      <button className="danger" onClick={() => handleDelete(terreno.id)}>
                        Disattiva
                      </button>
                    ) : (
                      <button className="success" onClick={() => handleRestore(terreno.id)}>
                        Ripristina
                      </button>
                    )}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}

export default TerreniList;
