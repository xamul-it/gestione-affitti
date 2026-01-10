import { useState, useEffect } from 'react';
import { certificatiEnergeticiAPI, unitaImmobiliariAPI } from '../../services/immobiliAPI';
import { tecniciAPI } from '../../../../services/api';
import CertificatoEnergeticoForm from './CertificatoEnergeticoForm';
import './CertificatiEnergetici.css';

function CertificatiEnergeticiList() {
  const [certificati, setCertificati] = useState([]);
  const [immobili, setImmobili] = useState([]);
  const [tecnici, setTecnici] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showForm, setShowForm] = useState(false);
  const [editingCertificato, setEditingCertificato] = useState(null);
  const [validiSolo, setValidiSolo] = useState(true);

  useEffect(() => {
    fetchData();
  }, [validiSolo]);

  const fetchData = async () => {
    try {
      setLoading(true);
      const [certResponse, immResponse, tecResponse] = await Promise.all([
        certificatiEnergeticiAPI.getAll(validiSolo),
        unitaImmobiliariAPI.getAll(),
        tecniciAPI.getAll(true)
      ]);
      setCertificati(certResponse.data);
      setImmobili(immResponse.data);
      setTecnici(tecResponse.data);
      setError(null);
    } catch (err) {
      setError('Errore nel caricamento dei dati');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id) => {
    if (window.confirm('Sei sicuro di voler eliminare questo certificato?')) {
      try {
        await certificatiEnergeticiAPI.delete(id);
        fetchData();
      } catch (err) {
        setError('Errore nell\'eliminazione del certificato');
        console.error(err);
      }
    }
  };

  const handleEdit = (certificato) => {
    setEditingCertificato(certificato);
    setShowForm(true);
  };

  const handleFormClose = () => {
    setShowForm(false);
    setEditingCertificato(null);
    fetchData();
  };

  const getImmobileInfo = (id) => {
    const immobile = immobili.find(i => i.id === id);
    return immobile ? `${immobile.codice} - ${immobile.indirizzo}` : '-';
  };

  const getTecnicoInfo = (id) => {
    const tecnico = tecnici.find(t => t.id === id);
    return tecnico ? `${tecnico.nome} ${tecnico.cognome}` : '-';
  };

  const isScaduto = (dataScadenza) => {
    return new Date(dataScadenza) < new Date();
  };

  if (loading) return <div className="loading">Caricamento...</div>;
  if (error) return <div className="error">{error}</div>;

  return (
    <div className="certificati-container">
      <div className="header">
        <h1>Certificati Energetici</h1>
        <div className="header-actions">
          <label className="filter-checkbox">
            <input
              type="checkbox"
              checked={validiSolo}
              onChange={(e) => setValidiSolo(e.target.checked)}
            />
            Solo validi
          </label>
          <button onClick={() => setShowForm(true)} className="btn btn-primary">
            + Nuovo Certificato
          </button>
        </div>
      </div>

      {showForm && (
        <CertificatoEnergeticoForm
          certificato={editingCertificato}
          immobili={immobili}
          tecnici={tecnici}
          onClose={handleFormClose}
        />
      )}

      <div className="table-container">
        <table className="data-table">
          <thead>
            <tr>
              <th>Immobile</th>
              <th>Tecnico</th>
              <th>Classe</th>
              <th>IPE</th>
              <th>Emissione</th>
              <th>Scadenza</th>
              <th>Protocollo</th>
              <th>Stato</th>
              <th>Azioni</th>
            </tr>
          </thead>
          <tbody>
            {certificati.length === 0 ? (
              <tr>
                <td colSpan="9" className="text-center">Nessun certificato trovato</td>
              </tr>
            ) : (
              certificati.map((cert) => (
                <tr key={cert.id}>
                  <td>{getImmobileInfo(cert.immobile_id)}</td>
                  <td>{getTecnicoInfo(cert.tecnico_id)}</td>
                  <td>
                    <span className={`classe-badge classe-${cert.classe_energetica.toLowerCase()}`}>
                      {cert.classe_energetica}
                    </span>
                  </td>
                  <td>{cert.indice_prestazione_energetica ? `${cert.indice_prestazione_energetica} kWh/m²a` : '-'}</td>
                  <td>{new Date(cert.data_emissione).toLocaleDateString('it-IT')}</td>
                  <td>{new Date(cert.data_scadenza).toLocaleDateString('it-IT')}</td>
                  <td>{cert.numero_protocollo || '-'}</td>
                  <td>
                    <span className={`badge ${isScaduto(cert.data_scadenza) ? 'badge-danger' : 'badge-success'}`}>
                      {isScaduto(cert.data_scadenza) ? 'Scaduto' : 'Valido'}
                    </span>
                  </td>
                  <td>
                    <button onClick={() => handleEdit(cert)} className="btn btn-sm btn-secondary">
                      Modifica
                    </button>
                    <button onClick={() => handleDelete(cert.id)} className="btn btn-sm btn-danger">
                      Elimina
                    </button>
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

export default CertificatiEnergeticiList;
