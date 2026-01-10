import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { unitaImmobiliariAPI } from '../../services/immobiliAPI';
import UnitaImmobiliareForm from './UnitaImmobiliareForm';
import ImportButton from '../../../../components/Platform/ImportButton';
import './UnitaImmobiliari.css';

function UnitaImmobiliariList() {
  const [unitaImmobiliari, setUnitaImmobiliari] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showForm, setShowForm] = useState(false);
  const [editingUnitaImmobiliare, setEditingUnitaImmobiliare] = useState(null);

  useEffect(() => {
    fetchUnitaImmobiliari();
  }, []);

  const fetchUnitaImmobiliari = async () => {
    try {
      setLoading(true);
      const response = await unitaImmobiliariAPI.getAll();
      setUnitaImmobiliari(response.data);
      setError(null);
    } catch (err) {
      setError('Errore nel caricamento delle unità immobiliari');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id) => {
    if (window.confirm('Sei sicuro di voler eliminare questa unità immobiliare?')) {
      try {
        await unitaImmobiliariAPI.delete(id);
        fetchUnitaImmobiliari();
      } catch (err) {
        setError('Errore nell\'eliminazione dell\'unità immobiliare');
        console.error(err);
      }
    }
  };

  const handleEdit = (unitaImmobiliare) => {
    setEditingUnitaImmobiliare(unitaImmobiliare);
    setShowForm(true);
  };

  const handleFormClose = () => {
    setShowForm(false);
    setEditingUnitaImmobiliare(null);
    fetchUnitaImmobiliari();
  };

  if (loading) return <div className="loading">Caricamento...</div>;
  if (error) return <div className="error">{error}</div>;

  return (
    <div className="unita-immobiliari-container">
      <div className="header">
        <h1>Gestione Unità Immobiliari</h1>
        <div className="header-actions">
          <ImportButton
            moduleName="affitti_lungo"
            entityName="UnitaImmobiliare"
            entityLabel="Unità Immobiliari"
            onImportComplete={() => fetchUnitaImmobiliari()}
          />
          <button onClick={() => setShowForm(true)}>Nuova Unità Immobiliare</button>
        </div>
      </div>

      {showForm && (
        <UnitaImmobiliareForm
          unitaImmobiliare={editingUnitaImmobiliare}
          onClose={handleFormClose}
        />
      )}

      {unitaImmobiliari.length === 0 ? (
        <div className="card">
          <p>Nessuna unità immobiliare presente. Clicca su "Nuova Unità Immobiliare" per iniziare.</p>
        </div>
      ) : (
        <table>
          <thead>
            <tr>
              <th>Codice</th>
              <th>Tipo</th>
              <th>Categoria Catastale</th>
              <th>Indirizzo</th>
              <th>Città</th>
              <th>Superficie</th>
              <th>Locali</th>
              <th>Azioni</th>
            </tr>
          </thead>
          <tbody>
            {unitaImmobiliari.map((unitaImmobiliare) => (
              <tr key={unitaImmobiliare.id}>
                <td>{unitaImmobiliare.codice}</td>
                <td>{unitaImmobiliare.tipo}</td>
                <td>{unitaImmobiliare.categoria_catastale?.codice || '-'}</td>
                <td>{unitaImmobiliare.indirizzo}</td>
                <td>{unitaImmobiliare.citta}</td>
                <td>{unitaImmobiliare.superficie_mq ? `${unitaImmobiliare.superficie_mq} mq` : '-'}</td>
                <td>{unitaImmobiliare.locali || '-'}</td>
                <td>
                  <div className="action-buttons">
                    <Link to={`/unita-immobiliari/${unitaImmobiliare.id}`}>
                      <button className="primary">Dettagli</button>
                    </Link>
                    <button className="secondary" onClick={() => handleEdit(unitaImmobiliare)}>
                      Modifica
                    </button>
                    <button className="danger" onClick={() => handleDelete(unitaImmobiliare.id)}>
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

export default UnitaImmobiliariList;
