import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { contrattiAPI, affittuariAPI } from '../../services/affittiAPI';
import { unitaImmobiliariAPI } from '../../../../services/api';
import ContrattoForm from './ContrattoForm';
import './Contratti.css';

function ContrattiList() {
  const [contratti, setContratti] = useState([]);
  const [immobili, setImmobili] = useState([]);
  const [affittuari, setAffittuari] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showForm, setShowForm] = useState(false);
  const [editingContratto, setEditingContratto] = useState(null);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      setLoading(true);
      const [contrattiRes, immobiliRes, affittuariRes] = await Promise.all([
        contrattiAPI.getAll(),
        unitaImmobiliariAPI.getAll(),
        affittuariAPI.getAll(),
      ]);
      setContratti(contrattiRes.data);
      setImmobili(immobiliRes.data);
      setAffittuari(affittuariRes.data);
      setError(null);
    } catch (err) {
      setError('Errore nel caricamento dei dati');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id) => {
    if (window.confirm('Sei sicuro di voler eliminare questo contratto?')) {
      try {
        await contrattiAPI.delete(id);
        fetchData();
      } catch (err) {
        setError('Errore nell\'eliminazione del contratto');
        console.error(err);
      }
    }
  };

  const handleEdit = (contratto) => {
    setEditingContratto(contratto);
    setShowForm(true);
  };

  const handleFormClose = () => {
    setShowForm(false);
    setEditingContratto(null);
    fetchData();
  };

  const getImmobileNome = (id) => {
    const immobile = immobili.find(i => i.id === id);
    return immobile ? `${immobile.codice} - ${immobile.indirizzo}` : '-';
  };

  const getAffittuarioNome = (id) => {
    const affittuario = affittuari.find(a => a.id === id);
    return affittuario ? `${affittuario.nome} ${affittuario.cognome}` : '-';
  };

  if (loading) return <div className="loading">Caricamento...</div>;
  if (error) return <div className="error">{error}</div>;

  return (
    <div className="contratti-container">
      <div className="header">
        <h1>Gestione Contratti</h1>
        <button onClick={() => setShowForm(true)}>Nuovo Contratto</button>
      </div>

      {showForm && (
        <ContrattoForm
          contratto={editingContratto}
          immobili={immobili}
          affittuari={affittuari}
          onClose={handleFormClose}
        />
      )}

      {contratti.length === 0 ? (
        <div className="card">
          <p>Nessun contratto presente. Clicca su "Nuovo Contratto" per iniziare.</p>
        </div>
      ) : (
        <table>
          <thead>
            <tr>
              <th>Numero</th>
              <th>Immobile</th>
              <th>Affittuario</th>
              <th>Tipologia</th>
              <th>Durata</th>
              <th>Data Inizio</th>
              <th>Data Fine</th>
              <th>Canone</th>
              <th>Regime Fiscale</th>
              <th>Stato</th>
              <th>Azioni</th>
            </tr>
          </thead>
          <tbody>
            {contratti.map((contratto) => (
              <tr key={contratto.id}>
                <td>{contratto.numero_contratto}</td>
                <td>{getImmobileNome(contratto.immobile_id)}</td>
                <td>{getAffittuarioNome(contratto.affittuario_id)}</td>
                <td>
                  {contratto.tipologia_contratto === 'LIBERO_MERCATO' && 'Libero Mercato'}
                  {contratto.tipologia_contratto === 'CANONE_CONCORDATO' && 'Canone Concordato'}
                  {contratto.tipologia_contratto === 'TRANSITORIO' && 'Transitorio'}
                  {contratto.tipologia_contratto === 'STUDENTI' && 'Studenti'}
                  {contratto.tipologia_contratto === 'FORESTERIA' && 'Foresteria'}
                  {contratto.tipologia_contratto === 'COMMERCIALE_LIBERO' && 'Comm. Libero'}
                  {contratto.tipologia_contratto === 'ALTRO' && 'Altro'}
                </td>
                <td>
                  {contratto.durata_anni_iniziale}
                  {contratto.durata_anni_rinnovo && `+${contratto.durata_anni_rinnovo}`}
                </td>
                <td>{new Date(contratto.data_inizio).toLocaleDateString('it-IT')}</td>
                <td>{new Date(contratto.data_fine).toLocaleDateString('it-IT')}</td>
                <td>€ {contratto.canone_mensile}</td>
                <td>
                  {contratto.regime_fiscale === 'ORDINARIO_IRPEF' && 'IRPEF'}
                  {contratto.regime_fiscale === 'CEDOLARE_SECCA_21' && 'Ced. 21%'}
                  {contratto.regime_fiscale === 'CEDOLARE_SECCA_10' && 'Ced. 10%'}
                </td>
                <td>
                  <span className={`badge badge-${contratto.stato?.toLowerCase()}`}>
                    {contratto.stato}
                  </span>
                </td>
                <td>
                  <div className="action-buttons">
                    <Link to={`/contratti/${contratto.id}`}>
                      <button className="primary">Dettagli</button>
                    </Link>
                    <button className="secondary" onClick={() => handleEdit(contratto)}>
                      Modifica
                    </button>
                    <button className="danger" onClick={() => handleDelete(contratto.id)}>
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

export default ContrattiList;
