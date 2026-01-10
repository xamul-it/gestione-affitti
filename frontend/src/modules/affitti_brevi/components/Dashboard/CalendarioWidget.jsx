import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import axios from 'axios';
import './CalendarioWidget.css';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

/**
 * CalendarioWidget - Dashboard widget for bookings calendar
 *
 * Shows summary of bookings and conflicts
 */
function CalendarioWidget() {
  const [stats, setStats] = useState({
    bookingsToday: 0,
    bookingsWeek: 0,
    conflicts: 0,
  });
  const [upcomingBookings, setUpcomingBookings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadCalendarData();
  }, []);

  const loadCalendarData = async () => {
    try {
      setLoading(true);
      setError(null);

      const token = localStorage.getItem('access_token');

      // Get current date and next week
      const oggi = new Date();
      const nextWeek = new Date();
      nextWeek.setDate(oggi.getDate() + 7);

      const dataInizio = formatDate(oggi);
      const dataFine = formatDate(nextWeek);

      // Fetch calendar overview
      const response = await axios.get(`${API_BASE_URL}/affitti-brevi/calendario/overview`, {
        params: {
          data_inizio: dataInizio,
          data_fine: dataFine,
        },
        headers: { Authorization: `Bearer ${token}` }
      });

      const calendarData = response.data;

      // Calculate stats
      const todayStr = formatDate(oggi);
      const bookingsToday = calendarData.filter(item => item.data === todayStr).length;
      const bookingsWeek = calendarData.length;

      // Check for conflicts
      const conflictsResponse = await axios.get(`${API_BASE_URL}/affitti-brevi/calendario/conflicts`, {
        params: {
          data_inizio: dataInizio,
          data_fine: dataFine,
        },
        headers: { Authorization: `Bearer ${token}` }
      });

      const conflicts = conflictsResponse.data.conflicts || [];

      setStats({
        bookingsToday,
        bookingsWeek,
        conflicts: conflicts.length,
      });

      // Group by booking and show next 5
      const bookingsByPrenotazione = {};
      calendarData.forEach(item => {
        if (!bookingsByPrenotazione[item.prenotazione_id]) {
          bookingsByPrenotazione[item.prenotazione_id] = item;
        }
      });

      const upcoming = Object.values(bookingsByPrenotazione)
        .sort((a, b) => new Date(a.data) - new Date(b.data))
        .slice(0, 5);

      setUpcomingBookings(upcoming);

    } catch (err) {
      console.error('Error loading calendar data:', err);
      setError('Errore nel caricamento del calendario');
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (date) => {
    return date.toISOString().split('T')[0];
  };

  const formatDisplayDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('it-IT', {
      day: '2-digit',
      month: 'short',
      year: 'numeric'
    });
  };

  const getPortaleIcon = (portale) => {
    const icons = {
      BOOKING: '🅱️',
      AIRBNB: '🅰️',
      VRBO: '🆅',
      ALTRO: '📅'
    };
    return icons[portale] || icons.ALTRO;
  };

  const getPortaleName = (portale) => {
    const names = {
      BOOKING: 'Booking.com',
      AIRBNB: 'Airbnb',
      VRBO: 'Vrbo',
      ALTRO: 'Altro'
    };
    return names[portale] || portale;
  };

  const getStatoColor = (stato) => {
    const colors = {
      PRENOTATO: 'status-confirmed',
      LIBERO: 'status-available',
      CHIUSO: 'status-blocked'
    };
    return colors[stato] || 'status-default';
  };

  if (loading) {
    return (
      <div className="calendario-widget">
        <div className="widget-loading">Caricamento...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="calendario-widget">
        <div className="widget-error">{error}</div>
      </div>
    );
  }

  return (
    <div className="calendario-widget">
      {/* Header */}
      <div className="widget-header">
        <h3>📅 Calendario Prenotazioni</h3>
        <Link to="/affitti-brevi/calendario" className="view-all-link">
          Vedi calendario
        </Link>
      </div>

      {/* Stats Summary */}
      <div className="stats-summary">
        <div className="stat-item stat-primary">
          <div className="stat-value">{stats.bookingsToday}</div>
          <div className="stat-label">Oggi</div>
        </div>
        <div className="stat-item stat-info">
          <div className="stat-value">{stats.bookingsWeek}</div>
          <div className="stat-label">Prossimi 7gg</div>
        </div>
        {stats.conflicts > 0 && (
          <div className="stat-item stat-danger">
            <div className="stat-value">{stats.conflicts}</div>
            <div className="stat-label">Conflitti</div>
          </div>
        )}
      </div>

      {/* Conflicts Warning */}
      {stats.conflicts > 0 && (
        <div className="conflicts-warning">
          <i className="fas fa-exclamation-triangle"></i>
          <span>Attenzione: {stats.conflicts} conflitt{stats.conflicts === 1 ? 'o' : 'i'} rilevat{stats.conflicts === 1 ? 'o' : 'i'}</span>
          <Link to="/affitti-brevi/calendario" className="resolve-link">
            Risolvi →
          </Link>
        </div>
      )}

      {/* Upcoming Bookings List */}
      <div className="bookings-list">
        <h4>Prossime Prenotazioni</h4>
        {upcomingBookings.length === 0 ? (
          <div className="no-bookings">
            <i className="fas fa-calendar-check"></i>
            <p>Nessuna prenotazione nei prossimi 7 giorni</p>
          </div>
        ) : (
          <ul>
            {upcomingBookings.map((booking) => (
              <li key={`${booking.prenotazione_id}-${booking.data}`} className="booking-item">
                <div className="booking-platform">
                  <span className="platform-icon">{getPortaleIcon(booking.portale)}</span>
                  <span className="platform-name">{getPortaleName(booking.portale)}</span>
                </div>
                <div className="booking-info">
                  <div className="booking-date">
                    <i className="fas fa-calendar"></i> {formatDisplayDate(booking.data)}
                  </div>
                  <div className="booking-property">
                    <i className="fas fa-building"></i> Immobile #{booking.immobile_id}
                  </div>
                </div>
                <span className={`booking-status ${getStatoColor(booking.stato)}`}>
                  {booking.stato}
                </span>
              </li>
            ))}
          </ul>
        )}
      </div>

      {/* Quick Actions */}
      <div className="widget-actions">
        <Link to="/affitti-brevi/prenotazioni" className="btn btn-secondary btn-block">
          Vedi Prenotazioni
        </Link>
      </div>
    </div>
  );
}

export default CalendarioWidget;
