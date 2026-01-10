import './calendario.css';

function PlatformBadge({ symbol, portale, stato }) {
  // Platform colors (from functional spec)
  const platformColors = {
    'BOOKING_COM': '#003580',  // Blue
    'AIRBNB': '#FF5A5F',        // Red
    'VRBO': '#0D7E83',          // Green
    'ALTRO': '#6c757d',         // Gray
    'DIRETTA': '#28a745'        // Green (direct booking)
  };

  const platformLabels = {
    'BOOKING_COM': 'Booking.com',
    'AIRBNB': 'Airbnb',
    'VRBO': 'Vrbo',
    'ALTRO': 'Altro',
    'DIRETTA': 'Diretta'
  };

  const bgColor = platformColors[portale] || '#6c757d';
  const label = platformLabels[portale] || portale;

  // Visual encoding based on status:
  // PRENOTATO: Colored symbol on colored background
  // LIBERO: Black symbol on colored background
  // CHIUSO: Strikethrough symbol on colored background

  let symbolColor = '#000';  // Default black for LIBERO
  let textDecoration = 'none';

  if (stato === 'PRENOTATO') {
    // Colored symbol (same as background for strong visual)
    symbolColor = bgColor;
  } else if (stato === 'CHIUSO') {
    // Strikethrough
    textDecoration = 'line-through';
  }

  return (
    <div
      className={`platform-badge platform-${portale.toLowerCase()} stato-${stato.toLowerCase()}`}
      style={{
        backgroundColor: bgColor,
        opacity: stato === 'LIBERO' ? 0.3 : 0.9  // Lighter for available
      }}
      title={`${label} - ${stato}`}
    >
      <span
        className="badge-symbol"
        style={{
          color: stato === 'PRENOTATO' ? '#fff' : '#000',  // White for booked, black for others
          textDecoration: textDecoration,
          fontWeight: stato === 'PRENOTATO' ? 'bold' : 'normal'
        }}
      >
        {symbol}
      </span>
    </div>
  );
}

export default PlatformBadge;
