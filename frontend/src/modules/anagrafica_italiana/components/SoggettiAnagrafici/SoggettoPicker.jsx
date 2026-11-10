import { useEffect, useId, useRef, useState } from 'react';
import { getSoggettiAnagrafici } from '../../services/anagraficaAPI';
import { nomeSoggetto } from './SoggettiTable';
import Button from '../../../../components/UI/Button';
import './SoggettoPicker.css';

const ATTESA_MS = 250;

/**
 * Search an anagrafica by name or codice fiscale and pick it.
 * Calls onSelect(soggetto); shows the choice with a "Cambia" button.
 */
function SoggettoPicker({ label = 'Anagrafica', value, onSelect, placeholder = 'Cerca per nome o codice fiscale...' }) {
  const inputId = useId();
  const labelId = useId();
  const listId = useId();
  const [term, setTerm] = useState('');
  const [risultati, setRisultati] = useState(null);
  const [loading, setLoading] = useState(false);
  const richiesta = useRef(0);

  useEffect(() => {
    const testo = term.trim();
    if (testo.length < 2) {
      setRisultati(null);
      return undefined;
    }
    const numero = ++richiesta.current;
    const timer = setTimeout(async () => {
      setLoading(true);
      try {
        const tutti = await getSoggettiAnagrafici({ limit: 1000 });
        if (numero !== richiesta.current) return; // a newer search is running
        const t = testo.toLowerCase();
        setRisultati(tutti.filter((s) => (
          nomeSoggetto(s).toLowerCase().includes(t) || (s.codice_fiscale || '').toLowerCase().includes(t)
        )).slice(0, 15));
      } catch {
        if (numero === richiesta.current) setRisultati([]);
      } finally {
        if (numero === richiesta.current) setLoading(false);
      }
    }, ATTESA_MS);
    return () => clearTimeout(timer);
  }, [term]);

  if (value) {
    return (
      <div className="soggetto-picker" role="group" aria-labelledby={labelId}>
        <span id={labelId} className="soggetto-picker__label">{label}</span>
        <div className="soggetto-picker__scelto">
          <span>{nomeSoggetto(value)}</span>
          <Button type="button" variant="secondary" size="sm" onClick={() => onSelect(null)}>Cambia</Button>
        </div>
      </div>
    );
  }

  const stato = loading ? 'Ricerca…' : risultati && risultati.length === 0 ? 'Nessuna anagrafica trovata' : '';

  return (
    <div className="soggetto-picker">
      <label className="soggetto-picker__label" htmlFor={inputId}>{label}</label>
      <input
        id={inputId}
        type="text"
        role="combobox"
        aria-expanded={Boolean(risultati && risultati.length)}
        aria-controls={listId}
        aria-autocomplete="list"
        value={term}
        onChange={(e) => setTerm(e.target.value)}
        placeholder={placeholder}
        autoComplete="off"
      />
      <span className="soggetto-picker__info" aria-live="polite">{stato}</span>
      {risultati && risultati.length > 0 && (
        <ul id={listId} className="soggetto-picker__risultati">
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
