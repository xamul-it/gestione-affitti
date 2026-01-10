import { useState, useEffect } from 'react';
import { tabelleMillesimaliAPI, condominAPI } from '../../services/immobiliAPI';
import TabellaMillesimaleForm from './TabellaMillesimaleForm';
import './TabelleMillesimali.css';

function TabelleMillesimaliList() {
  const [tabelle, setTabelle] = useState([]);
  const [condomini, setCondomini] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showForm, setShowForm] = useState(false);
  const [editingTabella, setEditingTabella] = useState(null);
  const [filtroCondominio, setFiltroCondominio] = useState('');

  useEffect(() => {
    fetchCondomini();
    fetchTabelle();
  }, []);

  const fetchCondomini = async () => {
    try {
      const response = await condominAPI.getAll(true);
      setCondomini(response.data);
    } catch (err) {
      console.error('Errore caricamento condomini:', err);
    }
  };

  const fetchTabelle = async () => {
    try {
      setLoading(true);
      const response = await tabelleMillesimaliAPI.getAll(
        filtroCondominio || null,
        false
      );
      setTabelle(response.data);
      setError(null);
    } catch (err) {
      setError('Errore nel caricamento delle tabelle millesimali');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (condomini.length > 0) {
      fetchTabelle();
    }
  }, [filtroCondominio]);

  const handleDelete = async (id) => {
    if (window.confirm('Sei sicuro di voler eliminare questa tabella millesimale?')) {
      try {
        await tabelleMillesimaliAPI.delete(id);
        fetchTabelle();
      } catch (err) {
        setError('Errore nell\'eliminazione della tabella');
        console.error(err);
      }
    }
  };

  const handleEdit = (tabella) => {
    setEditingTabella(tabella);
    setShowForm(true);
  };

  const handleFormClose = () => {
    setShowForm(false);
    setEditingTabella(null);
    fetchTabelle();
  };

  const getTipoRipartizioneLabel = (tipo) => {
    const labels = {
      'millesimi': 'Millesimi',
      'millesimi_consumo': 'Millesimi + Consumo',
      'occupanti': 'Occupanti',
      'millesimi_piano': 'Millesimi + Piano',
      'personalizzata': 'Personalizzata'
    };
    return labels[tipo] || tipo;
  };

  if (loading) return <div className="loading">Caricamento...</div>;
  if (error) return <div className="error">{error}</div>;

  return (
    <div className="tabelle-millesimali-container">
      <div className="header">
        <h1>Gestione Tabelle Millesimali</h1>
        <button onClick={() => setShowForm(true)}>Nuova Tabella</button>
      </div>

      <div className="filters">
        <div className="form-group">
          <label>Filtra per Condominio:</label>
          <select
            value={filtroCondominio}
            onChange={(e) => setFiltroCondominio(e.target.value)}
          >
            <option value="">Tutti i condomini</option>
            {condomini.map((cond) => (
              <option key={cond.id} value={cond.id}>
                {cond.nome}
              </option>
            ))}
          </select>
        </div>
      </div>

      {showForm && (
        <TabellaMillesimaleForm
          tabella={editingTabella}
          condomini={condomini}
          onClose={handleFormClose}
        />
      )}

      {tabelle.length === 0 ? (
        <div className="card">
          <p>Nessuna tabella millesimale presente. Clicca su "Nuova Tabella" per iniziare.</p>
        </div>
      ) : (
        <table>
          <thead>
            <tr>
              <th>Codice</th>
              <th>Nome</th>
              <th>Condominio</th>
              <th>Tipo Ripartizione</th>
              <th>% Millesimi</th>
              <th>% Consumo</th>
              <th>% Occupanti</th>
              <th>Stato</th>
              <th>Azioni</th>
            </tr>
          </thead>
          <tbody>
            {tabelle.map((tabella) => (
              <tr key={tabella.id}>
                <td>{tabella.codice}</td>
                <td>{tabella.nome}</td>
                <td>
                  {condomini.find(c => c.id === tabella.condominio_id)?.nome || '-'}
                </td>
                <td>{getTipoRipartizioneLabel(tabella.tipo_ripartizione)}</td>
                <td>{tabella.percentuale_millesimi}%</td>
                <td>{tabella.percentuale_consumo}%</td>
                <td>{tabella.percentuale_occupanti}%</td>
                <td>
                  <span className={`badge ${tabella.attiva ? 'success' : 'inactive'}`}>
                    {tabella.attiva ? 'Attiva' : 'Non attiva'}
                  </span>
                </td>
                <td>
                  <div className="action-buttons">
                    <button className="secondary" onClick={() => handleEdit(tabella)}>
                      Modifica
                    </button>
                    <button className="danger" onClick={() => handleDelete(tabella.id)}>
                      Elimina
                    </button>
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

export default TabelleMillesimaliList;
