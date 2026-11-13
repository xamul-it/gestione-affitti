import { Dato } from './Dato';
import { euro } from './formatters';
import { haAreCa } from '../../utils/superficie';

const siNo = (v) => (v ? 'Sì' : 'No');

/** Data of a land parcel of the Catasto Terreni, with its portions. */
export default function DatiTerreno({ terreno }) {
  const identificativi = [terreno.foglio, terreno.particella, terreno.subalterno].filter(Boolean).join(' / ');
  const porzioni = terreno.porzioni || [];
  return (
    <>
      <dl className="scheda-dati">
        <Dato label="Foglio / particella">{identificativi}</Dato>
        <Dato label="Sezione">{terreno.sezione_catastale}</Dato>
        <Dato label="Tipologia">{terreno.tipologia?.nome}</Dato>
        <Dato label="Superficie">{terreno.superficie_mq != null ? haAreCa(terreno.superficie_mq) : null}</Dato>
        <Dato label="Reddito dominicale">{terreno.reddito_dominicale_totale != null ? euro(terreno.reddito_dominicale_totale) : null}</Dato>
        <Dato label="Reddito agrario">{terreno.reddito_agrario_totale != null ? euro(terreno.reddito_agrario_totale) : null}</Dato>
        <Dato label="Edificabile">{siNo(terreno.edificabile)}</Dato>
        <Dato label="Esente IMU (montano)">{siNo(terreno.esente_imu_montano)}</Dato>
        <Dato label="Servitù">{terreno.servitu}</Dato>
      </dl>
      <div className="scheda-tabella">
        <table className="scheda-porzioni" aria-label="Porzioni">
          <thead>
            <tr>
              <th scope="col">Porzione</th>
              <th scope="col">Qualità</th>
              <th scope="col">Classe</th>
              <th scope="col">Superficie</th>
              <th scope="col">Reddito dominicale</th>
              <th scope="col">Reddito agrario</th>
              <th scope="col">Deduzioni</th>
            </tr>
          </thead>
          <tbody>
            {porzioni.map((p) => (
              <tr key={p.id}>
                <td>{p.porzione || '—'}</td>
                <td>{p.qualita}</td>
                <td>{p.classe || '—'}</td>
                <td>{haAreCa(p.superficie_mq)}</td>
                <td>{euro(p.reddito_dominicale)}</td>
                <td>{euro(p.reddito_agrario)}</td>
                <td>{p.deduzioni || '—'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  );
}
