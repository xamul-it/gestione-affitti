import { Dato } from './Dato';
import { euro, mq } from './formatters';

/** Data of a unit of the Catasto Fabbricati. */
export default function DatiUnita({ unita }) {
  const identificativi = [unita.foglio, unita.particella, unita.subalterno].filter(Boolean).join(' / ');
  return (
    <dl className="scheda-dati">
      <Dato label="Foglio / particella / sub">{identificativi}</Dato>
      <Dato label="Categoria">{unita.categoria_catastale?.codice}</Dato>
      <Dato label="Rendita catastale">{unita.rendita_catastale != null ? euro(unita.rendita_catastale) : null}</Dato>
      <Dato label="Superficie">{unita.superficie_mq != null ? mq(unita.superficie_mq) : null}</Dato>
      <Dato label="Locali">{unita.locali}</Dato>
      <Dato label="Piano">{unita.piano}</Dato>
    </dl>
  );
}
