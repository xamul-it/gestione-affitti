import { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { authAPI } from '../services/api';
import { formatApiError } from '../utils/errorHandling';
import { Lock, Palette, User } from 'lucide-react';
import { Button, Card, FormField, Badge } from '../components/UI';
import { ErrorMessage } from '../core/components/common';
import { useToast } from '../core/hooks';
import './Settings.css';

export default function Settings() {
  const { user, updateUser } = useAuth();
  const [activeTab, setActiveTab] = useState('profile');
  const [error, setError] = useState('');
  const toast = useToast();
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
    setLoading(true);

    try {
      await authAPI.updateUser(user.id, profileData, token);

      // Update local user data
      updateUser({ ...user, ...profileData });

      toast.success('Profilo aggiornato con successo');
    } catch (err) {
      setError('Errore nell\'aggiornamento del profilo: ' + (err.response?.data?.detail || err.message));
    } finally {
      setLoading(false);
    }
  };

  const handlePasswordChange = async (e) => {
    e.preventDefault();
    setError('');

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
      await authAPI.changePassword({
        old_password: passwordData.current_password,
        new_password: passwordData.new_password
      }, token);

      toast.success('Password modificata con successo');
      setPasswordData({
        current_password: '',
        new_password: '',
        confirm_password: ''
      });
    } catch (err) {
      setError('Errore nel cambio password: ' + formatApiError(err));
    } finally {
      setLoading(false);
    }
  };

  const tabs = [
    { id: 'profile', label: 'Profilo', Icon: User },
    { id: 'password', label: 'Sicurezza', Icon: Lock },
    { id: 'preferences', label: 'Preferenze', Icon: Palette },
  ];

  return (
    <div className="settings">
      <div className="settings-header">
        <h1>Impostazioni</h1>
        <p>Gestisci il tuo profilo e le preferenze</p>
      </div>

      <ErrorMessage message={error} onDismiss={() => setError('')} />

      {/* Tabs */}
      <div className="settings-tabs" role="tablist" aria-label="Sezioni impostazioni">
        {tabs.map(({ id, label, Icon }) => (
          <button
            key={id}
            type="button"
            role="tab"
            aria-selected={activeTab === id}
            className={`settings-tab ${activeTab === id ? 'active' : ''}`}
            onClick={() => setActiveTab(id)}
          >
            <Icon size={18} strokeWidth={1.7} aria-hidden="true" />
            {label}
          </button>
        ))}
      </div>

      {/* Profile Tab */}
      {activeTab === 'profile' && (
        <Card className="settings-card" role="tabpanel">
          <h2>Informazioni Profilo</h2>
          <form onSubmit={handleProfileUpdate}>
            <FormField label="Username" htmlFor="username">
              <input
                id="username"
                type="text"
                value={user?.username || ''}
                disabled
              />
              <small>Username non modificabile</small>
            </FormField>

            <FormField label="Email *" htmlFor="email">
              <input
                id="email"
                type="email"
                value={profileData.email}
                onChange={(e) => setProfileData({...profileData, email: e.target.value})}
                required
              />
            </FormField>

            <FormField label="Nome Completo" htmlFor="full_name">
              <input
                id="full_name"
                type="text"
                value={profileData.full_name}
                onChange={(e) => setProfileData({...profileData, full_name: e.target.value})}
              />
            </FormField>

            <FormField label="Telefono" htmlFor="phone">
              <input
                id="phone"
                type="text"
                value={profileData.phone}
                onChange={(e) => setProfileData({...profileData, phone: e.target.value})}
              />
            </FormField>

            <div className="form-actions">
              <Button type="submit" variant="primary" loading={loading}>
                {loading ? 'Salvataggio...' : 'Salva Modifiche'}
              </Button>
            </div>
          </form>
        </Card>
      )}

      {/* Password Tab */}
      {activeTab === 'password' && (
        <Card className="settings-card" role="tabpanel">
          <h2>Cambia Password</h2>
          <form onSubmit={handlePasswordChange}>
            <FormField label="Password Attuale *" htmlFor="current_password">
              <input
                id="current_password"
                type="password"
                autoComplete="current-password"
                value={passwordData.current_password}
                onChange={(e) => setPasswordData({...passwordData, current_password: e.target.value})}
                required
              />
            </FormField>

            <FormField label="Nuova Password *" htmlFor="new_password">
              <input
                id="new_password"
                type="password"
                autoComplete="new-password"
                value={passwordData.new_password}
                onChange={(e) => setPasswordData({...passwordData, new_password: e.target.value})}
                required
                minLength={8}
              />
              <small>Minimo 8 caratteri</small>
            </FormField>

            <FormField label="Conferma Nuova Password *" htmlFor="confirm_password">
              <input
                id="confirm_password"
                type="password"
                autoComplete="new-password"
                value={passwordData.confirm_password}
                onChange={(e) => setPasswordData({...passwordData, confirm_password: e.target.value})}
                required
                minLength={8}
              />
            </FormField>

            <div className="form-actions">
              <Button type="submit" variant="primary" loading={loading}>
                {loading ? 'Aggiornamento...' : 'Cambia Password'}
              </Button>
            </div>
          </form>
        </Card>
      )}

      {/* Preferences Tab */}
      {activeTab === 'preferences' && (
        <Card className="settings-card" role="tabpanel">
          <h2>Preferenze</h2>
          <div className="preferences-grid">
            <div className="preference-item">
              <div className="preference-info">
                <h3>Tema Scuro</h3>
                <p>Attiva il tema scuro per ridurre l'affaticamento degli occhi</p>
              </div>
              <label className="switch">
                <input type="checkbox" disabled aria-label="Tema scuro" />
                <span className="slider"></span>
              </label>
              <Badge variant="warning" className="coming-soon">Prossimamente</Badge>
            </div>

            <div className="preference-item">
              <div className="preference-info">
                <h3>Lingua</h3>
                <p>Seleziona la lingua dell'interfaccia</p>
              </div>
              <select disabled aria-label="Lingua">
                <option>Italiano</option>
                <option>English</option>
              </select>
              <Badge variant="warning" className="coming-soon">Prossimamente</Badge>
            </div>

            <div className="preference-item">
              <div className="preference-info">
                <h3>Notifiche</h3>
                <p>Ricevi notifiche per eventi importanti</p>
              </div>
              <label className="switch">
                <input type="checkbox" disabled aria-label="Notifiche" />
                <span className="slider"></span>
              </label>
              <Badge variant="warning" className="coming-soon">Prossimamente</Badge>
            </div>
          </div>
        </Card>
      )}
    </div>
  );
}
