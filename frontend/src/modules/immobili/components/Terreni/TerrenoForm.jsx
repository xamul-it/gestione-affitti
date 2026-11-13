import { Button } from '../../../../components/UI';
import { useState, useEffect } from 'react';
import { terreniAPI, tipologieTerrenoAPI } from '../../services/immobiliAPI';
import { formatApiError } from '../../../../utils/errorHandling';
import PorzioniEditor, { PORZIONE_VUOTA } from './PorzioniEditor';

// Fields sent to the API; everything else in the loaded parcel (id,
// tipo_bene, totals, timestamps, tipologia object) is computed by the server.
const CAMPI = [
  'codice', 'nome', 'descrizione', 'tipologia_id', 'indirizzo', 'comune', 'cap', 'provincia', 'nazione',
  'sezione_catastale', 'foglio', 'particella', 'subalterno', 'note', 'attivo',
  'edificabile', 'esente_imu_montano', 'servitu',
];
const CAMPI_PORZIONE = Object.keys(PORZIONE_VUOTA);

const VUOTO = {
  codice: '', nome: '', descrizione: '', tipologia_id: '', indirizzo: '', comune: '', cap: '',
  provincia: '', nazione: 'Italia', sezione_catastale: '', foglio: '', particella: '', subalterno: '',
  note: '', attivo: true, edificabile: false, esente_imu_montano: false, servitu: '',
};

const nulloSeVuoto = (v) => (v === '' || v === undefined ? null : v);

function datiDaInviare(form, porzioni) {
  const dati = {};
  for (const campo of CAMPI) {
    const v = form[campo];
    dati[campo] = typeof v === 'boolean' ? v : nulloSeVuoto(v);
  }
  if (dati.tipologia_id !== null) dati.tipologia_id = Number(dati.tipologia_id);
  dati.nazione = dati.nazione || 'Italia';
  dati.porzioni = porzioni.map((p) => {
    const porzione = {};
    for (const campo of CAMPI_PORZIONE) porzione[campo] = nulloSeVuoto(p[campo]);
    return porzione;
  });
  return dati;
}

function Campo({ id, label, required, children }) {
  return (
    <div className="form-group">
      <label htmlFor={id}>{label}{required ? ' *' : ''}</label>
      {children}
    </div>
  );
}

function TerrenoForm({ terreno, onClose }) {
  const [form, setForm] = useState(VUOTO);
  const [porzioni, setPorzioni] = useState([{ ...PORZIONE_VUOTA }]);
  const [tipologie, setTipologie] = useState([]);
  const [error, setError] = useState(null);
  const [salvataggio, setSalvataggio] = useState(false);

  useEffect(() => {
    tipologieTerrenoAPI.getAll(true)
      .then((res) => setTipologie(res.data || []))
      .catch(() => setTipologie([]));
  }, []);

  useEffect(() => {
    if (!terreno) return;
    const caricato = { ...VUOTO };
    for (const campo of CAMPI) {
      if (terreno[campo] !== null && terreno[campo] !== undefined) caricato[campo] = terreno[campo];
    }
    setForm(caricato);
    if (terreno.porzioni?.length) {
      setPorzioni(terreno.porzioni.map((p) => {
        const riga = {};
        for (const campo of CAMPI_PORZIONE) riga[campo] = p[campo] ?? '';
        return riga;
      }));
    }
  }, [terreno]);

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setForm((prev) => ({ ...prev, [name]: type === 'checkbox' ? checked : value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setSalvataggio(true);
    try {
      const dati = datiDaInviare(form, porzioni);
      if (terreno) {
        await terreniAPI.update(terreno.id, dati);
      } else {
        await terreniAPI.create(dati);
      }
      onClose();
    } catch (err) {
      setError(formatApiError(err));
    } finally {
      setSalvataggio(false);
    }
  };

  const testo = (name, label, props = {}) => (
    <Campo id={`terreno-${name}`} label={label} required={props.required}>
      <input id={`terreno-${name}`} type="text" name={name} value={form[name] ?? ''} onChange={handleChange} {...props} />
    </Campo>
  );

  const spunta = (name, label) => (
    <label className="checkbox-label">
      <input type="checkbox" name={name} checked={!!form[name]} onChange={handleChange} />
      {label}
    </label>
  );

  return (
    <div className="modal-overlay">
      <div className="modal-content modal-content--wide">
        <div className="modal-header">
          <h2>{terreno ? 'Modifica terreno' : 'Nuovo terreno'}</h2>
          <Button type="button" variant="ghost" size="sm" aria-label="Chiudi" onClick={onClose}>×</Button>
        </div>

        {error && <div className="error" role="alert">{error}</div>}

        <form onSubmit={handleSubmit}>
          <h3 className="section-title">Identificazione</h3>
          <div className="form-row">
            {testo('codice', 'Codice', { required: true, maxLength: 50, placeholder: 'es. TER-001' })}
            {testo('nome', 'Nome', { maxLength: 255, placeholder: 'Nome descrittivo (facoltativo)' })}
          </div>
          <div className="form-row">
            <Campo id="terreno-tipologia_id" label="Tipologia">
              <select id="terreno-tipologia_id" name="tipologia_id" value={form.tipologia_id ?? ''} onChange={handleChange}>
                <option value="">—</option>
                {tipologie.map((t) => <option key={t.id} value={t.id}>{t.nome}</option>)}
              </select>
            </Campo>
            <div className="form-group">
              <span className="form-group__label">Stato</span>
              {spunta('attivo', 'Attivo')}
            </div>
          </div>
          <Campo id="terreno-descrizione" label="Descrizione">
            <textarea id="terreno-descrizione" name="descrizione" value={form.descrizione ?? ''} onChange={handleChange} rows="2" />
          </Campo>

          <h3 className="section-title">Ubicazione</h3>
          {testo('indirizzo', 'Indirizzo / località', { maxLength: 255, placeholder: 'es. Località Le Vigne' })}
          <div className="form-row">
            {testo('comune', 'Comune', { required: true, maxLength: 100 })}
            {testo('cap', 'CAP', { maxLength: 10 })}
            {testo('provincia', 'Provincia', { required: true, maxLength: 2, placeholder: 'es. FC' })}
            {testo('nazione', 'Nazione', { maxLength: 100 })}
          </div>

          <h3 className="section-title">Dati catastali</h3>
          <div className="form-row">
            {testo('sezione_catastale', 'Sezione', { maxLength: 20 })}
            {testo('foglio', 'Foglio', { maxLength: 20 })}
            {testo('particella', 'Particella', { maxLength: 20 })}
            {testo('subalterno', 'Subalterno', { maxLength: 20 })}
          </div>

          <h3 className="section-title">Porzioni</h3>
          <PorzioniEditor value={porzioni} onChange={setPorzioni} />

          <h3 className="section-title">Uso e vincoli</h3>
          <div className="form-row">
            {spunta('edificabile', 'Edificabile')}
            {spunta('esente_imu_montano', 'Esente IMU (terreno montano)')}
          </div>
          <Campo id="terreno-servitu" label="Servitù">
            <textarea id="terreno-servitu" name="servitu" value={form.servitu ?? ''} onChange={handleChange} rows="2" />
          </Campo>
          <Campo id="terreno-note" label="Note">
            <textarea id="terreno-note" name="note" value={form.note ?? ''} onChange={handleChange} rows="3" />
          </Campo>

          <div className="btn-group">
            <Button type="button" variant="secondary" onClick={onClose}>Annulla</Button>
            <Button type="submit" disabled={salvataggio}>Salva</Button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default TerrenoForm;
