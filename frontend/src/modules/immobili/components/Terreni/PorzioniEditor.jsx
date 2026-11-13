import { Button } from '../../../../components/UI';
import { haAreCa } from '../../utils/superficie';

export const PORZIONE_VUOTA = {
  porzione: '', qualita: '', classe: '', superficie_mq: '',
  reddito_dominicale: '', reddito_agrario: '', deduzioni: '',
};

const COLONNE = [
  { campo: 'porzione', etichetta: 'Porzione', placeholder: 'AA', maxLength: 5 },
  { campo: 'qualita', etichetta: 'Qualità', placeholder: 'SEMINATIVO', required: true, maxLength: 100 },
  { campo: 'classe', etichetta: 'Classe', maxLength: 10 },
  { campo: 'superficie_mq', etichetta: 'Superficie m²', tipo: 'number', step: '1', required: true },
  { campo: 'reddito_dominicale', etichetta: 'Reddito dominicale €', tipo: 'number', step: '0.01' },
  { campo: 'reddito_agrario', etichetta: 'Reddito agrario €', tipo: 'number', step: '0.01' },
  { campo: 'deduzioni', etichetta: 'Deduzioni', maxLength: 100 },
];

/**
 * Portions of a land parcel (visura: porzione, qualità, classe, superficie,
 * redditi, deduzioni). Always at least one row; surface is a number of m².
 */
function PorzioniEditor({ value, onChange }) {
  const righe = value && value.length ? value : [PORZIONE_VUOTA];

  const aggiorna = (indice, campo, valore) => {
    const nuove = righe.map((r, i) => {
      if (i !== indice) return r;
      const v = campo === 'superficie_mq' ? (valore === '' ? '' : Number(valore)) : valore;
      return { ...r, [campo]: v };
    });
    onChange(nuove);
  };

  const totale = righe.reduce((somma, r) => somma + (Number(r.superficie_mq) || 0), 0);

  return (
    <div className="porzioni-editor">
      <div className="porzioni-editor__scroll">
        <table className="porzioni-editor__table">
          <thead>
            <tr>
              {COLONNE.map((c) => <th key={c.campo} scope="col">{c.etichetta}{c.required ? ' *' : ''}</th>)}
              <th scope="col"><span className="sr-only">Azioni</span></th>
            </tr>
          </thead>
          <tbody>
            {righe.map((riga, i) => (
              <tr key={i}>
                {COLONNE.map((c) => (
                  <td key={c.campo}>
                    <input
                      type={c.tipo || 'text'}
                      aria-label={`${c.etichetta} porzione ${i + 1}`}
                      value={riga[c.campo] ?? ''}
                      placeholder={c.placeholder}
                      maxLength={c.maxLength}
                      step={c.step}
                      min={c.tipo === 'number' ? '0' : undefined}
                      required={c.required}
                      onChange={(e) => aggiorna(i, c.campo, e.target.value)}
                    />
                  </td>
                ))}
                <td>
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    aria-label={`Togli porzione ${i + 1}`}
                    disabled={righe.length <= 1}
                    onClick={() => onChange(righe.filter((_, j) => j !== i))}
                  >
                    ×
                  </Button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="porzioni-editor__footer">
        <Button type="button" variant="secondary" size="sm" onClick={() => onChange([...righe, { ...PORZIONE_VUOTA }])}>
          Aggiungi porzione
        </Button>
        <span className="porzioni-editor__totale">Superficie totale: {haAreCa(totale)}</span>
      </div>
    </div>
  );
}

export default PorzioniEditor;
