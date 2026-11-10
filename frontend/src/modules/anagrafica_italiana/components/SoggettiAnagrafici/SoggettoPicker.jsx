import { useId, useState } from 'react';
import { getSoggettiAnagrafici } from '../../services/anagraficaAPI';
import { nomeSoggetto } from './SoggettiTable';
import './SoggettoPicker.css';

/**
 * Search an anagrafica by name or codice fiscale and pick it.
 * Calls onSelect(soggetto); shows the choice with a "Cambia" button.
 */
function SoggettoPicker({ label = 'Anagrafica', value, onSelect, placeholder = 'Cerca per nome o codice fiscale...' }) {
  const inputId = useId();
  const [term, setTerm] = useState('');
  const [risultati, setRisultati] = useState(null);
  const [loading, setLoading] = useState(false);

  const cerca = async (testo) => {
    setTerm(testo);
    if (testo.trim().length < 2) {
      setRisultati(null);
      return;
    }
    setLoading(true);
    try {
      const tutti = await getSoggettiAnagrafici({ limit: 1000 });
      const t = testo.toLowerCase();
      setRisultati(tutti.filter((s) => (
        nomeSoggetto(s).toLowerCase().includes(t) || (s.codice_fiscale || '').toLowerCase().includes(t)
      )).slice(0, 15));
    } catch {
      setRisultati([]);
    } finally {
      setLoading(false);
    }
  };

  if (value) {
    return (
      <div className="soggetto-picker">
        <span className="soggetto-picker__label">{label}</span>
        <div className="soggetto-picker__scelto">
          <span>{nomeSoggetto(value)}</span>
          <button type="button" className="btn btn-secondary" onClick={() => onSelect(null)}>Cambia</button>
        </div>
      </div>
    );
  }

  return (
    <div className="soggetto-picker">
      <label className="soggetto-picker__label" htmlFor={inputId}>{label}</label>
      <input
        id={inputId}
        type="text"
        value={term}
        onChange={(e) => cerca(e.target.value)}
        placeholder={placeholder}
        autoComplete="off"
      />
      {risultati !== null && (
        <ul className="soggetto-picker__risultati">
          {loading && <li className="soggetto-picker__info">Ricerca…</li>}
          {!loading && risultati.length === 0 && <li className="soggetto-picker__info">Nessuna anagrafica trovata</li>}
          {risultati.map((s) => (
            <li key={s.id}>
              <button type="button" onClick={() => { setTerm(''); setRisultati(null); onSelect(s); }}>
                {nomeSoggetto(s)}
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

export default SoggettoPicker;
