import { useId, useState } from 'react';
import { Button } from '../../../../components/UI';
import { FormModal } from '../../../../core/components/FormBuilder/FormModal';
import { raggruppamentiAPI } from '../../services/immobiliAPI';
import { formatApiError } from '../../../../utils/errorHandling';
import { TIPI_RAMO } from './rami';

/** Create (with an optional parent) or edit a ramo: type, name, description, notes. */
export default function RaggruppamentoForm({ ramo, padreId = null, onClose }) {
  const uid = useId();
  const modifica = Boolean(ramo);
  const [tipo, setTipo] = useState(ramo?.tipo || (padreId ? 'EDIFICIO' : 'COMPLESSO'));
  const [nome, setNome] = useState(ramo?.nome || '');
  const [descrizione, setDescrizione] = useState(ramo?.descrizione || '');
  const [note, setNote] = useState(ramo?.note || '');
  const [error, setError] = useState(null);
  const [manca, setManca] = useState(false);
  const [saving, setSaving] = useState(false);

  const salva = async (e) => {
    e.preventDefault();
    if (!nome.trim()) {
      setManca(true);
      return;
    }
    setSaving(true);
    setError(null);
    const corpo = { tipo, nome: nome.trim(), descrizione: descrizione.trim() || null, note: note.trim() || null };
    try {
      const r = modifica
        ? await raggruppamentiAPI.update(ramo.id, corpo)
        : await raggruppamentiAPI.create({ ...corpo, padre_id: padreId });
      onClose(r.data || true);
    } catch (err) {
      setError(formatApiError(err));
      setSaving(false);
    }
  };

  return (
    <FormModal title={modifica ? 'Modifica raggruppamento' : 'Nuovo raggruppamento'} size="small" onClose={() => onClose(false)}>
      <form className="collegamento-form" onSubmit={salva} noValidate>
        {error && <div className="collegamento-form__errore" role="alert">{error}</div>}
        <div className="collegamento-form__campo">
          <label htmlFor={`${uid}-tipo`}>Tipo</label>
          <select id={`${uid}-tipo`} value={tipo} onChange={(e) => setTipo(e.target.value)}>
            {TIPI_RAMO.map((t) => <option key={t.codice} value={t.codice}>{t.etichetta}</option>)}
          </select>
        </div>
        <div className="collegamento-form__campo">
          <label htmlFor={`${uid}-nome`}>Nome</label>
          <input id={`${uid}-nome`} type="text" value={nome} required
            aria-invalid={manca ? true : undefined} aria-describedby={manca ? `${uid}-errnome` : undefined}
            onChange={(e) => { setNome(e.target.value); setManca(false); }} />
          {manca && <p id={`${uid}-errnome`} className="collegamento-form__errore-campo">Scrivi il nome</p>}
        </div>
        <div className="collegamento-form__campo">
          <label htmlFor={`${uid}-descrizione`}>Descrizione</label>
          <textarea id={`${uid}-descrizione`} rows={2} value={descrizione} onChange={(e) => setDescrizione(e.target.value)} />
        </div>
        <div className="collegamento-form__campo">
          <label htmlFor={`${uid}-note`}>Note</label>
          <textarea id={`${uid}-note`} rows={2} value={note} onChange={(e) => setNote(e.target.value)} />
        </div>
        <div className="collegamento-form__azioni">
          <Button variant="secondary" type="button" onClick={() => onClose(false)} disabled={saving}>Annulla</Button>
          <Button type="submit" disabled={saving}>{saving ? 'Salvataggio…' : 'Salva'}</Button>
        </div>
      </form>
    </FormModal>
  );
}
