import { useState } from 'react';
import PlatformBadge from './PlatformBadge';
import './calendario.css';

function CalendarCell({ symbol, data, date }) {
  const [showTooltip, setShowTooltip] = useState(false);

  // Check if there are multiple bookings (conflict)
  const hasConflict = data.filter(d => d.stato === 'PRENOTATO').length > 1;

  const handleMouseEnter = () => {
    setShowTooltip(true);
  };

  const handleMouseLeave = () => {
    setShowTooltip(false);
  };

  return (
    <div
      className={`calendar-cell date-cell ${hasConflict ? 'has-conflict' : ''}`}
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
    >
      {/* Render badges for each platform */}
      <div className="platform-badges">
        {data.map((entry, index) => (
          <PlatformBadge
            key={index}
            symbol={symbol}
            portale={entry.portale}
            stato={entry.stato}
          />
        ))}
      </div>

      {/* Tooltip with details */}
      {showTooltip && data.length > 0 && (
        <div className="cell-tooltip">
          <div className="tooltip-date">
            {date.toLocaleDateString('it-IT', { day: '2-digit', month: 'short' })}
          </div>
          {data.map((entry, index) => (
            <div key={index} className="tooltip-entry">
              <strong>{entry.portale}:</strong>
              {entry.stato === 'PRENOTATO' && (
                <>
                  <div>Prenotazione: {entry.codice_prenotazione}</div>
                  <div>Ospiti: {entry.numero_ospiti}</div>
                  {entry.prezzo_totale && <div>Prezzo: €{entry.prezzo_totale.toFixed(2)}</div>}
                </>
              )}
              {entry.stato === 'CHIUSO' && (
                <>
                  <div>Chiuso: {entry.tipo_blocco}</div>
                  {entry.motivo && <div>Motivo: {entry.motivo}</div>}
                </>
              )}
              {entry.stato === 'LIBERO' && (
                <div>Disponibile</div>
              )}
            </div>
          ))}
          {hasConflict && (
            <div className="tooltip-conflict-warning">
              ⚠️ Conflitto: Più prenotazioni per stessa data!
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default CalendarCell;
