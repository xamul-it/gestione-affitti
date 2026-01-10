import { Link } from 'react-router-dom';
import { renderIcon } from '../../../../components/Navigation/iconRegistry.jsx';
import './SoggettoNew.css';

function SoggettoNew() {
  return (
    <div className="soggetto-new">
      <div className="soggetto-new-header">
        <h1>Nuova Anagrafica</h1>
        <p>Seleziona il tipo di soggetto da creare.</p>
      </div>

      <div className="soggetto-new-grid">
        <Link to="/anagrafiche/persone-fisiche/nuovo" className="soggetto-new-card">
          <div className="soggetto-new-icon" aria-hidden="true">
            {renderIcon('user', { size: 20, className: 'soggetto-new-icon-svg', fallbackClassName: 'nav-emoji-icon' })}
          </div>
          <div className="soggetto-new-title">Persona Fisica</div>
          <div className="soggetto-new-desc">
            Crea un soggetto anagrafico per persone fisiche.
          </div>
        </Link>
        <Link to="/anagrafiche/persone-giuridiche/nuovo" className="soggetto-new-card">
          <div className="soggetto-new-icon" aria-hidden="true">
            {renderIcon('building', { size: 20, className: 'soggetto-new-icon-svg', fallbackClassName: 'nav-emoji-icon' })}
          </div>
          <div className="soggetto-new-title">Persona Giuridica</div>
          <div className="soggetto-new-desc">
            Crea un soggetto anagrafico per aziende o enti.
          </div>
        </Link>
      </div>
    </div>
  );
}

export default SoggettoNew;
