import { useState, useEffect } from 'react';
import { contrattiAPI } from '../../services/affittiAPI';
import { formatApiError } from '../../../../utils/errorHandling';
import DocumentiSection from '../Documenti/DocumentiSection';

function ContrattoForm({ contratto, immobili, affittuari, onClose }) {
  const [formData, setFormData] = useState({
    numero_contratto: '',
    immobile_id: '',
    affittuario_id: '',
    uso_immobile: 'ABITATIVO',
    tipologia_contratto: 'LIBERO_MERCATO',
    durata_anni_iniziale: 4,
    durata_anni_rinnovo: 4,
    data_inizio: '',
    data_fine: '',
    canone_mensile: '',
    giorno_pagamento: 1,
    deposito_cauzionale: '',
    regime_fiscale: 'ORDINARIO_IRPEF',
    adeguamento_istat: false,
    percentuale_istat: '',
    data_ultimo_adeguamento: '',
    registrazione_numero: '',
    registrazione_data: '',
    registrazione_agenzia: '',
    stato: 'ATTIVO',
    note: '',
  });
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(false);

  useEffect(() => {
    if (contratto) {
      setFormData(contratto);
    }
  }, [contratto]);

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const dataToSend = {
        ...formData,
        immobile_id: parseInt(formData.immobile_id),
        affittuario_id: parseInt(formData.affittuario_id),
        durata_anni_iniziale: parseInt(formData.durata_anni_iniziale),
        durata_anni_rinnovo: formData.durata_anni_rinnovo ? parseInt(formData.durata_anni_rinnovo) : null,
        canone_mensile: parseFloat(formData.canone_mensile),
        giorno_pagamento: parseInt(formData.giorno_pagamento),
        deposito_cauzionale: formData.deposito_cauzionale ? parseFloat(formData.deposito_cauzionale) : null,
        percentuale_istat: formData.percentuale_istat ? parseFloat(formData.percentuale_istat) : null,
        data_ultimo_adeguamento: formData.data_ultimo_adeguamento || null,
        registrazione_data: formData.registrazione_data || null,
      };

      if (contratto) {
        await contrattiAPI.update(contratto.id, dataToSend);
      } else {
        await contrattiAPI.create(dataToSend);
      }
      setSuccess(true);
      setTimeout(() => {
        onClose();
      }, 1500);
    } catch (err) {
      setError(formatApiError(err));
      console.error(err);
    }
  };

  return (
    <div className="modal-overlay">
      <div className="modal-content">
        <div className="modal-header">
          <h2>{contratto ? 'Modifica Contratto' : 'Nuovo Contratto'}</h2>
          <button className="close-btn" onClick={onClose}>×</button>
        </div>

        {error && <div className="error">{error}</div>}
        {success && <div className="success">Operazione completata con successo!</div>}

        <form onSubmit={handleSubmit}>
          {/* Dati identificativi */}
          <div className="form-group">
            <label>Numero Contratto *</label>
            <input
              type="text"
              name="numero_contratto"
              value={formData.numero_contratto}
              onChange={handleChange}
              required
            />
          </div>

          <div className="form-row">
            <div className="form-group">
              <label>Immobile *</label>
              <select
                name="immobile_id"
                value={formData.immobile_id}
                onChange={handleChange}
                required
              >
                <option value="">Seleziona immobile...</option>
                {immobili.map(immobile => (
                  <option key={immobile.id} value={immobile.id}>
                    {immobile.codice} - {immobile.indirizzo}, {immobile.citta}
                  </option>
                ))}
              </select>
            </div>

            <div className="form-group">
              <label>Affittuario *</label>
              <select
                name="affittuario_id"
                value={formData.affittuario_id}
                onChange={handleChange}
                required
              >
                <option value="">Seleziona affittuario...</option>
                {affittuari.map(affittuario => (
                  <option key={affittuario.id} value={affittuario.id}>
                    {affittuario.nome} {affittuario.cognome} - {affittuario.codice_fiscale}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* Tipologia e uso immobile */}
          <div className="form-row">
            <div className="form-group">
              <label>Uso Immobile *</label>
              <select
                name="uso_immobile"
                value={formData.uso_immobile}
                onChange={handleChange}
                required
              >
                <option value="ABITATIVO">Abitativo</option>
                <option value="COMMERCIALE">Commerciale</option>
                <option value="UFFICIO">Ufficio</option>
                <option value="MAGAZZINO">Magazzino</option>
                <option value="ALTRO">Altro</option>
              </select>
            </div>

            <div className="form-group">
              <label>Tipologia Contratto *</label>
              <select
                name="tipologia_contratto"
                value={formData.tipologia_contratto}
                onChange={handleChange}
                required
              >
                <option value="LIBERO_MERCATO">Libero Mercato (4+4 abitativo)</option>
                <option value="CANONE_CONCORDATO">Canone Concordato (3+2)</option>
                <option value="TRANSITORIO">Transitorio</option>
                <option value="STUDENTI">Studenti</option>
                <option value="FORESTERIA">Foresteria</option>
                <option value="COMMERCIALE_LIBERO">Commerciale Libero (6+6, 9+9)</option>
                <option value="ALTRO">Altro</option>
              </select>
            </div>
          </div>

          {/* Durata contratto */}
          <div className="form-row">
            <div className="form-group">
              <label>Durata Iniziale (anni) *</label>
              <input
                type="number"
                min="1"
                max="99"
                name="durata_anni_iniziale"
                value={formData.durata_anni_iniziale}
                onChange={handleChange}
                required
              />
              <small>Es. 4 per contratto 4+4, 3 per 3+2</small>
            </div>

            <div className="form-group">
              <label>Durata Rinnovo (anni)</label>
              <input
                type="number"
                min="1"
                max="99"
                name="durata_anni_rinnovo"
                value={formData.durata_anni_rinnovo}
                onChange={handleChange}
              />
              <small>Es. 4 per contratto 4+4, 2 per 3+2 (opzionale)</small>
            </div>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label>Data Inizio *</label>
              <input
                type="date"
                name="data_inizio"
                value={formData.data_inizio}
                onChange={handleChange}
                required
              />
            </div>

            <div className="form-group">
              <label>Data Fine *</label>
              <input
                type="date"
                name="data_fine"
                value={formData.data_fine}
                onChange={handleChange}
                required
              />
            </div>
          </div>

          {/* Aspetti economici */}
          <div className="form-row">
            <div className="form-group">
              <label>Canone Mensile (€) *</label>
              <input
                type="number"
                step="0.01"
                name="canone_mensile"
                value={formData.canone_mensile}
                onChange={handleChange}
                required
              />
            </div>

            <div className="form-group">
              <label>Giorno Pagamento</label>
              <input
                type="number"
                min="1"
                max="31"
                name="giorno_pagamento"
                value={formData.giorno_pagamento}
                onChange={handleChange}
              />
            </div>

            <div className="form-group">
              <label>Deposito Cauzionale (€)</label>
              <input
                type="number"
                step="0.01"
                name="deposito_cauzionale"
                value={formData.deposito_cauzionale}
                onChange={handleChange}
              />
            </div>
          </div>

          {/* Regime fiscale */}
          <div className="form-group">
            <label>Regime Fiscale *</label>
            <select
              name="regime_fiscale"
              value={formData.regime_fiscale}
              onChange={handleChange}
              required
            >
              <option value="ORDINARIO_IRPEF">Ordinario IRPEF</option>
              <option value="CEDOLARE_SECCA_21">Cedolare Secca 21% (Libero Mercato)</option>
              <option value="CEDOLARE_SECCA_10">Cedolare Secca 10% (Canone Concordato)</option>
            </select>
          </div>

          {/* Adeguamento ISTAT */}
          <div className="form-group">
            <label>
              <input
                type="checkbox"
                name="adeguamento_istat"
                checked={formData.adeguamento_istat}
                onChange={handleChange}
              />
              {' '}Adeguamento ISTAT
            </label>
          </div>

          {formData.adeguamento_istat && (
            <div className="form-row">
              <div className="form-group">
                <label>Percentuale ISTAT (%)</label>
                <input
                  type="number"
                  step="0.01"
                  min="0"
                  max="100"
                  name="percentuale_istat"
                  value={formData.percentuale_istat}
                  onChange={handleChange}
                />
                <small>Es. 75.00 per 75% dell'indice ISTAT</small>
              </div>

              <div className="form-group">
                <label>Data Ultimo Adeguamento</label>
                <input
                  type="date"
                  name="data_ultimo_adeguamento"
                  value={formData.data_ultimo_adeguamento}
                  onChange={handleChange}
                />
              </div>
            </div>
          )}

          {/* Registrazione */}
          <div className="form-row">
            <div className="form-group">
              <label>Numero Registrazione</label>
              <input
                type="text"
                name="registrazione_numero"
                value={formData.registrazione_numero}
                onChange={handleChange}
              />
            </div>

            <div className="form-group">
              <label>Data Registrazione</label>
              <input
                type="date"
                name="registrazione_data"
                value={formData.registrazione_data}
                onChange={handleChange}
              />
            </div>
          </div>

          <div className="form-group">
            <label>Agenzia Registrazione</label>
            <input
              type="text"
              name="registrazione_agenzia"
              value={formData.registrazione_agenzia}
              onChange={handleChange}
            />
            <small>Es. Agenzia delle Entrate di Roma 1</small>
          </div>

          {/* Stato e note */}
          <div className="form-group">
            <label>Stato</label>
            <select name="stato" value={formData.stato} onChange={handleChange}>
              <option value="ATTIVO">Attivo</option>
              <option value="SCADUTO">Scaduto</option>
              <option value="DISDETTO">Disdetto</option>
              <option value="TERMINATO">Terminato</option>
            </select>
          </div>

          <div className="form-group">
            <label>Note</label>
            <textarea
              name="note"
              value={formData.note}
              onChange={handleChange}
              rows="3"
            />
          </div>

          <div className="btn-group">
            <button type="submit">Salva</button>
            <button type="button" className="secondary" onClick={onClose}>
              Annulla
            </button>
          </div>
        </form>

        <DocumentiSection entityType="CONTRATTO" entityId={contratto?.id} />
      </div>
    </div>
  );
}

export default ContrattoForm;
