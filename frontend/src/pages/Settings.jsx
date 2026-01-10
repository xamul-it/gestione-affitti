import { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { authAPI } from '../services/api';
import './Settings.css';

export default function Settings() {
  const { user, updateUser } = useAuth();
  const [activeTab, setActiveTab] = useState('profile');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [loading, setLoading] = useState(false);

  // Profile form
  const [profileData, setProfileData] = useState({
    email: user?.email || '',
    full_name: user?.full_name || '',
    phone: user?.phone || ''
  });

  // Password form
  const [passwordData, setPasswordData] = useState({
    current_password: '',
    new_password: '',
    confirm_password: ''
  });

  const token = localStorage.getItem('access_token');

  const handleProfileUpdate = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');
    setLoading(true);

    try {
      await authAPI.updateUser(user.id, profileData, token);

      // Update local user data
      updateUser({ ...user, ...profileData });

      setSuccess('Profilo aggiornato con successo');
      setTimeout(() => setSuccess(''), 3000);
    } catch (err) {
      setError('Errore nell\'aggiornamento del profilo: ' + (err.response?.data?.detail || err.message));
    } finally {
      setLoading(false);
    }
  };

  const handlePasswordChange = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');

    // Validation
    if (passwordData.new_password !== passwordData.confirm_password) {
      setError('Le password non coincidono');
      return;
    }

    if (passwordData.new_password.length < 8) {
      setError('La nuova password deve essere di almeno 8 caratteri');
      return;
    }

    setLoading(true);

    try {
      // Note: You'll need to implement this endpoint in the backend
      await authAPI.changePassword({
        current_password: passwordData.current_password,
        new_password: passwordData.new_password
      }, token);

      setSuccess('Password modificata con successo');
      setPasswordData({
        current_password: '',
        new_password: '',
        confirm_password: ''
      });
      setTimeout(() => setSuccess(''), 3000);
    } catch (err) {
      setError('Errore nel cambio password: ' + (err.response?.data?.detail || err.message));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="settings">
      <div className="settings-header">
        <h1>
          <span aria-hidden="true">⚙️</span>
          Impostazioni
        </h1>
        <p>Gestisci il tuo profilo e le preferenze</p>
      </div>

      {error && (
        <div className="alert alert-error">
          {error}
          <button onClick={() => setError('')} aria-label="Chiudi messaggio">✖</button>
        </div>
      )}

      {success && (
        <div className="alert alert-success">
          {success}
          <button onClick={() => setSuccess('')} aria-label="Chiudi messaggio">✖</button>
        </div>
      )}

      {/* Tabs */}
      <div className="settings-tabs">
        <button
          className={`settings-tab ${activeTab === 'profile' ? 'active' : ''}`}
          onClick={() => setActiveTab('profile')}
        >
          <span aria-hidden="true">👤</span>
          Profilo
        </button>
        <button
          className={`settings-tab ${activeTab === 'password' ? 'active' : ''}`}
          onClick={() => setActiveTab('password')}
        >
          <span aria-hidden="true">🔒</span>
          Sicurezza
        </button>
        <button
          className={`settings-tab ${activeTab === 'preferences' ? 'active' : ''}`}
          onClick={() => setActiveTab('preferences')}
        >
          <span aria-hidden="true">🎨</span>
          Preferenze
        </button>
      </div>

      {/* Profile Tab */}
      {activeTab === 'profile' && (
        <div className="settings-card">
          <h2>Informazioni Profilo</h2>
          <form onSubmit={handleProfileUpdate}>
            <div className="form-group">
              <label htmlFor="username">Username</label>
              <input
                id="username"
                type="text"
                value={user?.username || ''}
                disabled
                className="disabled-input"
              />
              <small>Username non modificabile</small>
            </div>

            <div className="form-group">
              <label htmlFor="email">Email *</label>
              <input
                id="email"
                type="email"
                value={profileData.email}
                onChange={(e) => setProfileData({...profileData, email: e.target.value})}
                required
              />
            </div>

            <div className="form-group">
              <label htmlFor="full_name">Nome Completo</label>
              <input
                id="full_name"
                type="text"
                value={profileData.full_name}
                onChange={(e) => setProfileData({...profileData, full_name: e.target.value})}
              />
            </div>

            <div className="form-group">
              <label htmlFor="phone">Telefono</label>
              <input
                id="phone"
                type="text"
                value={profileData.phone}
                onChange={(e) => setProfileData({...profileData, phone: e.target.value})}
              />
            </div>

            <div className="form-actions">
              <button type="submit" className="btn-primary" disabled={loading}>
                {loading ? 'Salvataggio...' : 'Salva Modifiche'}
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Password Tab */}
      {activeTab === 'password' && (
        <div className="settings-card">
          <h2>Cambia Password</h2>
          <form onSubmit={handlePasswordChange}>
            <div className="form-group">
              <label htmlFor="current_password">Password Attuale *</label>
              <input
                id="current_password"
                type="password"
                value={passwordData.current_password}
                onChange={(e) => setPasswordData({...passwordData, current_password: e.target.value})}
                required
              />
            </div>

            <div className="form-group">
              <label htmlFor="new_password">Nuova Password *</label>
              <input
                id="new_password"
                type="password"
                value={passwordData.new_password}
                onChange={(e) => setPasswordData({...passwordData, new_password: e.target.value})}
                required
                minLength={8}
              />
              <small>Minimo 8 caratteri</small>
            </div>

            <div className="form-group">
              <label htmlFor="confirm_password">Conferma Nuova Password *</label>
              <input
                id="confirm_password"
                type="password"
                value={passwordData.confirm_password}
                onChange={(e) => setPasswordData({...passwordData, confirm_password: e.target.value})}
                required
                minLength={8}
              />
            </div>

            <div className="form-actions">
              <button type="submit" className="btn-primary" disabled={loading}>
                {loading ? 'Aggiornamento...' : 'Cambia Password'}
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Preferences Tab */}
      {activeTab === 'preferences' && (
        <div className="settings-card">
          <h2>Preferenze</h2>
          <div className="preferences-grid">
            <div className="preference-item">
              <div className="preference-info">
                <h3>🌙 Tema Scuro</h3>
                <p>Attiva il tema scuro per ridurre l'affaticamento degli occhi</p>
              </div>
              <label className="switch">
                <input type="checkbox" disabled />
                <span className="slider"></span>
              </label>
              <small className="coming-soon">Prossimamente</small>
            </div>

            <div className="preference-item">
              <div className="preference-info">
                <h3>🌍 Lingua</h3>
                <p>Seleziona la lingua dell'interfaccia</p>
              </div>
              <select disabled>
                <option>Italiano</option>
                <option>English</option>
              </select>
              <small className="coming-soon">Prossimamente</small>
            </div>

            <div className="preference-item">
              <div className="preference-info">
                <h3>🔔 Notifiche</h3>
                <p>Ricevi notifiche per eventi importanti</p>
              </div>
              <label className="switch">
                <input type="checkbox" disabled />
                <span className="slider"></span>
              </label>
              <small className="coming-soon">Prossimamente</small>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
