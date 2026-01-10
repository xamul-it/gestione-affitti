import { useState, useEffect } from 'react';
import axios from 'axios';
import CalendarGrid from './CalendarGrid';
import ConflictModal from './ConflictModal';
import './calendario.css';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

function CalendarioMultiPiattaforma() {
  const [calendarData, setCalendarData] = useState([]);
  const [conflicts, setConflicts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showConflictModal, setShowConflictModal] = useState(false);

  // Date range state (default: current month)
  const [startDate, setStartDate] = useState(() => {
    const now = new Date();
    return new Date(now.getFullYear(), now.getMonth(), 1);
  });
  const [endDate, setEndDate] = useState(() => {
    const now = new Date();
    return new Date(now.getFullYear(), now.getMonth() + 1, 0);
  });

  // Property filter state
  const [selectedProperties, setSelectedProperties] = useState([]);
  const [availableProperties, setAvailableProperties] = useState([]);

  useEffect(() => {
    fetchCalendarData();
    fetchConflicts();
  }, [startDate, endDate, selectedProperties]);

  const fetchCalendarData = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('access_token');

      const params = {
        data_inizio: formatDate(startDate),
        data_fine: formatDate(endDate),
      };

      if (selectedProperties.length > 0) {
        params.immobile_ids = selectedProperties;
      }

      const response = await axios.get(`${API_BASE_URL}/affitti-brevi/calendario/overview`, {
        params,
        headers: { Authorization: `Bearer ${token}` },
        paramsSerializer: { indexes: null } // For array params
      });

      setCalendarData(response.data);

      // Extract unique properties for filter
      const properties = [...new Set(response.data.map(item => item.immobile_id))];
      setAvailableProperties(properties);

      setError(null);
    } catch (err) {
      setError('Errore nel caricamento del calendario');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const fetchConflicts = async () => {
    try {
      const token = localStorage.getItem('access_token');

      const params = {
        data_inizio: formatDate(startDate),
        data_fine: formatDate(endDate),
      };

      const response = await axios.get(`${API_BASE_URL}/affitti-brevi/calendario/conflicts`, {
        params,
        headers: { Authorization: `Bearer ${token}` }
      });

      setConflicts(response.data.conflicts || []);
    } catch (err) {
      console.error('Error fetching conflicts:', err);
    }
  };

  const formatDate = (date) => {
    return date.toISOString().split('T')[0];
  };

  const handlePreviousMonth = () => {
    const newStart = new Date(startDate.getFullYear(), startDate.getMonth() - 1, 1);
    const newEnd = new Date(startDate.getFullYear(), startDate.getMonth(), 0);
    setStartDate(newStart);
    setEndDate(newEnd);
  };

  const handleNextMonth = () => {
    const newStart = new Date(startDate.getFullYear(), startDate.getMonth() + 1, 1);
    const newEnd = new Date(startDate.getFullYear(), startDate.getMonth() + 2, 0);
    setStartDate(newStart);
    setEndDate(newEnd);
  };

  const handleToday = () => {
    const now = new Date();
    setStartDate(new Date(now.getFullYear(), now.getMonth(), 1));
    setEndDate(new Date(now.getFullYear(), now.getMonth() + 1, 0));
  };

  const handlePropertyFilterChange = (propertyId) => {
    setSelectedProperties(prev => {
      if (prev.includes(propertyId)) {
        return prev.filter(id => id !== propertyId);
      } else {
        return [...prev, propertyId];
      }
    });
  };

  const handleConflictResolved = () => {
    setShowConflictModal(false);
    fetchCalendarData();
    fetchConflicts();
  };

  if (loading) return <div className="loading">Caricamento calendario...</div>;
  if (error) return <div className="error">{error}</div>;

  return (
    <div className="calendario-container">
      <div className="calendario-header">
        <h1>Calendario Multi-Piattaforma</h1>

        <div className="calendario-controls">
          {/* Date navigation */}
          <div className="date-navigation">
            <button onClick={handlePreviousMonth} className="btn btn-sm btn-secondary">
              ← Mese Prec
            </button>
            <button onClick={handleToday} className="btn btn-sm btn-secondary">
              Oggi
            </button>
            <button onClick={handleNextMonth} className="btn btn-sm btn-secondary">
              Mese Succ →
            </button>
          </div>

          {/* Current period display */}
          <div className="current-period">
            <span className="period-label">
              {startDate.toLocaleDateString('it-IT', { month: 'long', year: 'numeric' })}
            </span>
          </div>

          {/* Conflicts indicator */}
          {conflicts.length > 0 && (
            <button
              onClick={() => setShowConflictModal(true)}
              className="btn btn-danger conflicts-btn"
            >
              ⚠️ {conflicts.length} Conflitti
            </button>
          )}
        </div>
      </div>

      {/* Property filter */}
      {availableProperties.length > 0 && (
        <div className="property-filter">
          <label>Filtra Immobili:</label>
          {availableProperties.map(propId => (
            <label key={propId} className="property-checkbox">
              <input
                type="checkbox"
                checked={selectedProperties.includes(propId)}
                onChange={() => handlePropertyFilterChange(propId)}
              />
              <span>Immobile {propId}</span>
            </label>
          ))}
        </div>
      )}

      {/* Legend */}
      <div className="calendar-legend">
        <div className="legend-item">
          <div className="legend-badge prenotato">A</div>
          <span>Prenotato</span>
        </div>
        <div className="legend-item">
          <div className="legend-badge libero">A</div>
          <span>Libero</span>
        </div>
        <div className="legend-item">
          <div className="legend-badge chiuso">
            <span className="strikethrough">A</span>
          </div>
          <span>Chiuso</span>
        </div>
        <div className="legend-colors">
          <span className="color-booking">■ Booking.com</span>
          <span className="color-airbnb">■ Airbnb</span>
          <span className="color-vrbo">■ Vrbo</span>
        </div>
      </div>

      {/* Calendar Grid */}
      <CalendarGrid
        data={calendarData}
        startDate={startDate}
        endDate={endDate}
      />

      {/* Conflict Modal */}
      {showConflictModal && (
        <ConflictModal
          conflicts={conflicts}
          onClose={() => setShowConflictModal(false)}
          onResolved={handleConflictResolved}
        />
      )}
    </div>
  );
}

export default CalendarioMultiPiattaforma;
