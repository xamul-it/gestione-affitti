import CalendarCell from './CalendarCell';
import './calendario.css';

function CalendarGrid({ data, startDate, endDate }) {
  // Generate date range
  const dates = [];
  const current = new Date(startDate);
  while (current <= endDate) {
    dates.push(new Date(current));
    current.setDate(current.getDate() + 1);
  }

  // Group data by property and date
  const groupedData = {};

  data.forEach(entry => {
    const key = `${entry.immobile_id}`;
    if (!groupedData[key]) {
      groupedData[key] = {};
    }

    if (!groupedData[key][entry.data]) {
      groupedData[key][entry.data] = [];
    }

    groupedData[key][entry.data].push(entry);
  });

  // Get unique properties
  const properties = Object.keys(groupedData).sort((a, b) => parseInt(a) - parseInt(b));

  // Assign symbols to properties (A, B, C, ...)
  const propertySymbols = {};
  properties.forEach((propId, index) => {
    propertySymbols[propId] = String.fromCharCode(65 + index); // A=65 in ASCII
  });

  if (properties.length === 0) {
    return (
      <div className="calendar-empty">
        <p>Nessun calendario configurato. Aggiungi calendari iCal nella sezione "Calendari iCal".</p>
      </div>
    );
  }

  return (
    <div className="calendar-grid-wrapper">
      <div className="calendar-grid">
        {/* Header row with dates */}
        <div className="calendar-header-row">
          <div className="calendar-cell calendar-cell-header property-header">
            Immobile
          </div>
          {dates.map((date, index) => (
            <div key={index} className="calendar-cell calendar-cell-header date-header">
              <div className="date-day">{date.getDate()}</div>
              <div className="date-weekday">
                {date.toLocaleDateString('it-IT', { weekday: 'short' })}
              </div>
            </div>
          ))}
        </div>

        {/* Property rows */}
        {properties.map((propertyId) => (
          <div key={propertyId} className="calendar-row">
            {/* Property label cell */}
            <div className="calendar-cell property-label">
              <div className="property-symbol">{propertySymbols[propertyId]}</div>
              <div className="property-id">ID: {propertyId}</div>
            </div>

            {/* Date cells */}
            {dates.map((date, dateIndex) => {
              const dateStr = date.toISOString().split('T')[0];
              const cellData = groupedData[propertyId][dateStr] || [];

              return (
                <CalendarCell
                  key={`${propertyId}-${dateIndex}`}
                  symbol={propertySymbols[propertyId]}
                  data={cellData}
                  date={date}
                />
              );
            })}
          </div>
        ))}
      </div>
    </div>
  );
}

export default CalendarGrid;
