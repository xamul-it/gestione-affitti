import { useState, useEffect } from 'react';
import { millesimiImmobileAPI, tabelleMillesimaliAPI, unitaImmobiliariAPI, condominAPI } from '../../services/immobiliAPI';
import MillesimiForm from './MillesimiForm';
import './MillesimiImmobile.css';

function MillesimiImmobileList() {
  const [millesimi, setMillesimi] = useState([]);
  const [tabelle, setTabelle] = useState([]);
  const [immobili, setImmobili] = useState([]);
  const [condomini, setCondomini] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showForm, setShowForm] = useState(false);
  const [editingMillesimi, setEditingMillesimi] = useState(null);
  const [filtroTabella, setFiltroTabella] = useState('');
  const [filtroCondominio, setFiltroCondominio] = useState('');

  useEffect(() => {
    fetchAll();
  }, []);

  const fetchAll = async () => {
    try {
      setLoading(true);
      const [condRes, immRes] = await Promise.all([
        condominAPI.getAll(true),
        unitaImmobiliariAPI.getAll()
      ]);
      setCondomini(condRes.data);
      setImmobili(immRes.data);
    } catch (err) {
      console.error('Errore caricamento dati:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (filtroCondominio) {
      fetchTabelleByCondominio(filtroCondominio);
    } else {
      setTabelle([]);
      setFiltroTabella('');
    }
  }, [filtroCondominio]);

  const fetchTabelleByCondominio = async (condominioId) => {
    try {
      const response = await tabelleMillesimaliAPI.getByCondominio(condominioId);
      setTabelle(response.data);
    } catch (err) {
      console.error('Errore caricamento tabelle:', err);
    }
  };

  useEffect(() => {
    if (filtroTabella) {
      fetchMillesimiByTabella();
    } else {
      setMillesimi([]);
    }
  }, [filtroTabella]);

  const fetchMillesimiByTabella = async () => {
    try {
      const response = await millesimiImmobileAPI.getByTabella(filtroTabella);
      setMillesimi(response.data);
      setError(null);
    } catch (err) {
      setError('Errore nel caricamento dei millesimi');
      console.error(err);
    }
  };

  const handleDelete = async (id) => {
    if (window.confirm('Sei sicuro di voler eliminare questo record?')) {
      try {
        await millesimiImmobileAPI.delete(id);
        fetchMillesimiByTabella();
      } catch (err) {
        setError('Errore nell\'eliminazione');
        console.error(err);
      }
    }
  };

  const handleEdit = (millesimo) => {
    setEditingMillesimi(millesimo);
    setShowForm(true);
  };

  const handleFormClose = () => {
    setShowForm(false);
    setEditingMillesimi(null);
    if (filtroTabella) {
      fetchMillesimiByTabella();
    }
  };

  const getImmobileInfo = (immobileId) => {
    const imm = immobili.find(i => i.id === immobileId);
    return imm ? `${imm.codice} - ${imm.indirizzo}` : '-';
  };

  const getTabellaInfo = (tabellaId) => {
    const tab = tabelle.find(t => t.id === tabellaId);
    return tab ? tab.nome : '-';
  };

  if (loading) return <div className="loading">Caricamento...</div>;

  return (
    <div className="millesimi-immobile-container">
      <div className="header">
        <h1>Gestione Millesimi Immobili</h1>
        {filtroTabella && (
          <button onClick={() => setShowForm(true)}>Aggiungi Millesimi</button>
        )}
      </div>

      <div className="filters">
        <div className="form-row">
          <div className="form-group">
            <label>Condominio:</label>
            <select
              value={filtroCondominio}
              onChange={(e) => setFiltroCondominio(e.target.value)}
            >
              <option value="">Seleziona condominio</option>
              {condomini.map((cond) => (
                <option key={cond.id} value={cond.id}>
                  {cond.nome}
                </option>
              ))}
            </select>
          </div>
          {filtroCondominio && (
            <div className="form-group">
              <label>Tabella Millesimale:</label>
              <select
                value={filtroTabella}
                onChange={(e) => setFiltroTabella(e.target.value)}
              >
                <option value="">Seleziona tabella</option>
                {tabelle.map((tab) => (
                  <option key={tab.id} value={tab.id}>
                    {tab.nome}
                  </option>
                ))}
              </select>
            </div>
          )}
        </div>
      </div>

      {error && <div className="error">{error}</div>}

      {showForm && filtroTabella && (
        <MillesimiForm
          millesimo={editingMillesimi}
          tabellaId={parseInt(filtroTabella)}
          immobili={immobili.filter(i => i.condominio_id === parseInt(filtroCondominio))}
          tabella={tabelle.find(t => t.id === parseInt(filtroTabella))}
          onClose={handleFormClose}
        />
      )}

      {!filtroCondominio && (
        <div className="card">
          <p>Seleziona un condominio per visualizzare e gestire i millesimi.</p>
        </div>
      )}

      {filtroCondominio && !filtroTabella && (
        <div className="card">
          <p>Seleziona una tabella millesimale per visualizzare e gestire i millesimi.</p>
        </div>
      )}

      {filtroTabella && millesimi.length === 0 && (
        <div className="card">
          <p>Nessun immobile associato a questa tabella. Clicca su "Aggiungi Millesimi" per iniziare.</p>
        </div>
      )}

      {filtroTabella && millesimi.length > 0 && (
        <div>
          <div className="info-box">
            <strong>Totale millesimi: {millesimi.reduce((sum, m) => sum + m.millesimi, 0).toFixed(3)}</strong>
          </div>
          <table>
            <thead>
              <tr>
                <th>Immobile</th>
                <th>Millesimi</th>
                <th>Piano</th>
                <th>Occupanti</th>
                <th>Consumo</th>
                <th>Azioni</th>
              </tr>
            </thead>
            <tbody>
              {millesimi.map((millesimo) => (
                <tr key={millesimo.id}>
                  <td>{getImmobileInfo(millesimo.immobile_id)}</td>
                  <td><strong>{millesimo.millesimi}</strong></td>
                  <td>{millesimo.piano !== null ? millesimo.piano : '-'}</td>
                  <td>{millesimo.numero_occupanti || '-'}</td>
                  <td>
                    {millesimo.consumo ?
                      `${millesimo.consumo} ${millesimo.unita_misura_consumo || ''}` : '-'}
                  </td>
                  <td>
                    <div className="action-buttons">
                      <button className="secondary" onClick={() => handleEdit(millesimo)}>
                        Modifica
                      </button>
                      <button className="danger" onClick={() => handleDelete(millesimo.id)}>
                        Elimina
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

export default MillesimiImmobileList;
