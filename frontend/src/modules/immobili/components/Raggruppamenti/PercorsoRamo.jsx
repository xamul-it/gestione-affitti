import { Fragment } from 'react';
import { Link } from 'react-router-dom';
import { SEPARATORE } from './rami';

/** Breadcrumb of rami ([{ id, nome }], root first); each step links to its ramo page. */
export default function PercorsoRamo({ percorso, vuoto = 'Nessun raggruppamento', ultimoLink = true }) {
  return (
    <nav aria-label="Raggruppamento" className="percorso-ramo">
      {(!percorso || percorso.length === 0) ? (
        <span className="scheda-muted">{vuoto}</span>
      ) : percorso.map((p, i) => (
        <Fragment key={p.id}>
          {i > 0 && <span aria-hidden="true" className="percorso-ramo__sep">{SEPARATORE.trim()}</span>}
          {ultimoLink || i < percorso.length - 1
            ? <Link to={`/raggruppamenti/${p.id}`}>{p.nome}</Link>
            : <span aria-current="page">{p.nome}</span>}
        </Fragment>
      ))}
    </nav>
  );
}
