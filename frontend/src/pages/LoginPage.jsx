import { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { useTenant } from '../contexts/TenantContext';
import { Button, Card, FormField } from '../components/UI';
import { ErrorMessage } from '../core/components/common';
import './LoginPage.css';

export default function LoginPage() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [rememberMe, setRememberMe] = useState(true); // Default: true per sviluppo
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const { login } = useAuth();
  const { fetchUserTenants } = useTenant();
  const navigate = useNavigate();
  const location = useLocation();

  // Redirect to the page they tried to visit, or home
  const from = location.state?.from?.pathname || '/';

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    const result = await login(username, password, rememberMe);

    if (result.success) {
      // After successful login, fetch available tenants
      try {
        await fetchUserTenants();
        // Let ProtectedRoute handle tenant selection redirect
        navigate(from, { replace: true });
      } catch (err) {
        console.error('Failed to fetch tenants:', err);
        setError('Accesso effettuato, ma non è stato possibile caricare i database. Ricarica la pagina.');
      }
    } else {
      setError(result.error);
    }

    setLoading(false);
  };

  return (
    <div className="login-page">
      <div className="login-container">
        <Card className="login-card">
          <h1>Gestione Affitti</h1>
          <h2>Accedi al tuo account</h2>

          {error && <ErrorMessage message={error} onDismiss={() => setError('')} />}

          <form onSubmit={handleSubmit}>
            <FormField label="Username" htmlFor="username">
              <input
                type="text"
                id="username"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                required
                autoFocus
                autoComplete="username"
                disabled={loading}
              />
            </FormField>

            <FormField label="Password" htmlFor="password">
              <input
                type="password"
                id="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                autoComplete="current-password"
                disabled={loading}
              />
            </FormField>

            <label className="login-remember">
              <input
                type="checkbox"
                checked={rememberMe}
                onChange={(e) => setRememberMe(e.target.checked)}
                disabled={loading}
              />
              <span>Ricordami (mantieni la sessione per 30 giorni)</span>
            </label>

            <Button type="submit" variant="primary" className="login-submit" loading={loading}>
              {loading ? 'Accesso in corso...' : 'Accedi'}
            </Button>
          </form>

          <div className="login-footer">
            <p>Credenziali di default:</p>
            <p><strong>Username:</strong> admin</p>
            <p><strong>Password:</strong> changeme123</p>
          </div>
        </Card>
      </div>
    </div>
  );
}
