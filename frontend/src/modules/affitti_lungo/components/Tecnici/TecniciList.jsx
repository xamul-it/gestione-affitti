import { useState, useEffect } from 'react';
import { tecniciAPI } from '../../services/affittiAPI';
import TecnicoForm from './TecnicoForm';
import './Tecnici.css';

function TecniciList() {
  const [tecnici, setTecnici] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showForm, setShowForm] = useState(false);
  const [editingTecnico, setEditingTecnico] = useState(null);
  const [attiviSolo, setAttiviSolo] = useState(true);

  useEffect(() => {
    fetchTecnici();
  }, [attiviSolo]);

  const fetchTecnici = async () => {
    try {
      setLoading(true);
      const response = await tecniciAPI.getAll(attiviSolo);
      setTecnici(response.data);
      setError(null);
    } catch (err) {
      setError('Errore nel caricamento dei tecnici');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id) => {
    if (window.confirm('Sei sicuro di voler disattivare questo tecnico?')) {
      try {
        await tecniciAPI.delete(id);
        fetchTecnici();
      } catch (err) {
        setError('Errore nella disattivazione del tecnico');
        console.error(err);
      }
    }
  };

  const handleEdit = (tecnico) => {
    setEditingTecnico(tecnico);
    setShowForm(true);
  };

  const handleFormClose = () => {
    setShowForm(false);
    setEditingTecnico(null);
    fetchTecnici();
  };

  const getSpecializzazioneLabel = (spec) => {
    const labels = {
      ELETTRICISTA: 'Elettricista',
      IDRAULICO: 'Idraulico',
      TERMOTECNICO: 'Termotecnico',
      GEOMETRA: 'Geometra',
      ARCHITETTO: 'Architetto',
      INGEGNERE: 'Ingegnere',
      CERTIFICATORE_ENERGETICO: 'Certificatore Energetico',
      MANUTENTORE_CALDAIE: 'Manutentore Caldaie',
      ALTRO: 'Altro'
    };
    return labels[spec] || spec;
  };

  if (loading) return <div className="loading">Caricamento...</div>;
  if (error) return <div className="error">{error}</div>;

  return (
    <div className="tecnici-container">
      <div className="header">
        <h1>Tecnici</h1>
        <div className="header-actions">
          <label className="filter-checkbox">
            <input
              type="checkbox"
              checked={attiviSolo}
              onChange={(e) => setAttiviSolo(e.target.checked)}
            />
            Solo attivi
          </label>
          <button onClick={() => setShowForm(true)} className="btn btn-primary">
            + Nuovo Tecnico
          </button>
        </div>
      </div>

      {showForm && (
        <TecnicoForm
          tecnico={editingTecnico}
          onClose={handleFormClose}
        />
      )}

      <div className="table-container">
        <table className="data-table">
          <thead>
            <tr>
              <th>Nome</th>
              <th>Cognome</th>
              <th>Ragione Sociale</th>
              <th>Specializzazione</th>
              <th>Telefono</th>
              <th>Email</th>
              <th>Stato</th>
              <th>Azioni</th>
            </tr>
          </thead>
          <tbody>
            {tecnici.length === 0 ? (
              <tr>
                <td colSpan="8" className="text-center">Nessun tecnico trovato</td>
              </tr>
            ) : (
              tecnici.map((tecnico) => (
                <tr key={tecnico.id}>
                  <td>{tecnico.nome}</td>
                  <td>{tecnico.cognome}</td>
                  <td>{tecnico.ragione_sociale || '-'}</td>
                  <td>{getSpecializzazioneLabel(tecnico.specializzazione)}</td>
                  <td>{tecnico.telefono || '-'}</td>
                  <td>{tecnico.email || '-'}</td>
                  <td>
                    <span className={`badge ${tecnico.attivo ? 'badge-success' : 'badge-danger'}`}>
                      {tecnico.attivo ? 'Attivo' : 'Disattivo'}
                    </span>
                  </td>
                  <td>
                    <button onClick={() => handleEdit(tecnico)} className="btn btn-sm btn-secondary">
                      Modifica
                    </button>
                    {tecnico.attivo && (
                      <button onClick={() => handleDelete(tecnico.id)} className="btn btn-sm btn-danger">
                        Disattiva
                      </button>
                    )}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export default TecniciList;
