import { createContext, useContext, useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { refreshTokenSafe, clearTokens } from '../services/tokenService';

const AuthContext = createContext(null);

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const refreshAttemptedRef = useRef(false);

  // Initialize auth state from localStorage
  useEffect(() => {
    const initAuth = async () => {
      const token = localStorage.getItem('access_token');
      if (token) {
        // Validate token and fetch user info
        fetchCurrentUser(token);
        return;
      }

      // No access token, try to refresh using centralized service
      const refreshToken = localStorage.getItem('refresh_token');
      if (refreshToken) {
        refreshAttemptedRef.current = true;
        const newToken = await refreshTokenSafe();
        refreshAttemptedRef.current = false;
        if (newToken) {
          fetchCurrentUser(newToken);
          return;
        }
      }
      setLoading(false);
    };

    initAuth();
  }, []);

  const fetchCurrentUser = async (token) => {
    try {
      const response = await axios.get(`${API_BASE_URL}/auth/me`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      setUser(response.data);
      setError(null);
    } catch (err) {
      const status = err.response?.status;
      if ((status === 401 || status === 403) && !refreshAttemptedRef.current) {
        refreshAttemptedRef.current = true;
        // Use centralized token refresh
        const newToken = await refreshTokenSafe();
        if (newToken) {
          try {
            const retryResponse = await axios.get(`${API_BASE_URL}/auth/me`, {
              headers: {
                'Authorization': `Bearer ${newToken}`
              }
            });
            setUser(retryResponse.data);
            setError(null);
            return;
          } catch (retryErr) {
            console.error('Failed to fetch user after refresh:', retryErr);
          }
        }
      }
      console.error('Failed to fetch user:', err);
      // Token is invalid, clear it
      clearTokens();
      setUser(null);
      setError('Session expired. Please login again.');
    } finally {
      setLoading(false);
      refreshAttemptedRef.current = false;
    }
  };

  const login = async (username, password, rememberMe = false) => {
    try {
      setError(null);
      const response = await axios.post(`${API_BASE_URL}/auth/login`, {
        username,
        password,
        remember_me: rememberMe
      });

      const { access_token, refresh_token } = response.data;

      // Store tokens
      localStorage.setItem('access_token', access_token);
      localStorage.setItem('refresh_token', refresh_token);

      // Fetch user info
      await fetchCurrentUser(access_token);

      return { success: true };
    } catch (err) {
      // Messaggio di errore dettagliato per sviluppo
      let errorMessage = 'Login failed';
      let debugInfo = [];

      if (err.response) {
        // Il server ha risposto con un errore
        const status = err.response.status;
        const detail = err.response.data?.detail;

        errorMessage = `Login fallito (HTTP ${status})`;

        if (status === 401) {
          errorMessage += ': Username o password errati';
        } else if (status === 500) {
          errorMessage += ': Errore del server (possibile problema database)';
        } else if (status === 503) {
          errorMessage += ': Servizio non disponibile';
        }

        if (detail) {
          errorMessage += `\n\nDettagli: ${detail}`;
        }

        debugInfo.push(`Status: ${status}`);
        debugInfo.push(`URL: ${API_BASE_URL}/auth/login`);
        if (detail) debugInfo.push(`Server message: ${detail}`);

      } else if (err.request) {
        // La richiesta è stata fatta ma nessuna risposta ricevuta
        errorMessage = `❌ Backend non raggiungibile\n\nURL tentato: ${API_BASE_URL}/auth/login\n\n`;
        errorMessage += `Possibili cause:\n`;
        errorMessage += `• Il backend non è avviato\n`;
        errorMessage += `• Problemi di rete/firewall\n`;
        errorMessage += `• URL non corretto nel file .env\n\n`;
        errorMessage += `Verifica che il backend sia in esecuzione su ${API_BASE_URL.replace('/api/v1', '')}`;

        debugInfo.push(`Request made but no response`);
        debugInfo.push(`URL: ${API_BASE_URL}/auth/login`);
        debugInfo.push(`Network error or CORS issue`);

      } else {
        // Errore nella configurazione della richiesta
        errorMessage = `Errore di configurazione: ${err.message}`;
        debugInfo.push(`Configuration error: ${err.message}`);
      }

      // Log dettagliato nella console per debug
      console.group('🔴 LOGIN ERROR');
      console.error('Error object:', err);
      console.log('Error message:', errorMessage);
      console.log('API Base URL:', API_BASE_URL);
      console.log('Debug info:', debugInfo);
      console.log('Full error:', {
        message: err.message,
        response: err.response,
        request: err.request,
        config: err.config
      });
      console.groupEnd();

      setError(errorMessage);
      return { success: false, error: errorMessage };
    }
  };

  const logout = (clearTenantContextFn) => {
    // Use centralized token service
    clearTokens();
    setUser(null);
    setError(null);

    // Clear tenant context if provided
    if (clearTenantContextFn) {
      clearTenantContextFn();
    }
  };

  const updateUser = (userData) => {
    setUser(prevUser => ({ ...prevUser, ...userData }));
  };

  const changePassword = async (oldPassword, newPassword) => {
    try {
      const token = localStorage.getItem('access_token');
      await axios.post(
        `${API_BASE_URL}/auth/change-password`,
        {
          old_password: oldPassword,
          new_password: newPassword
        },
        {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        }
      );
      return { success: true };
    } catch (err) {
      const errorMessage = err.response?.data?.detail || 'Failed to change password';
      return { success: false, error: errorMessage };
    }
  };

  const hasRole = (roleName) => {
    if (!user || !user.roles) return false;
    return user.roles.some(role => role.name === roleName);
  };

  const hasPermission = (permissionName) => {
    if (!user) return false;
    if (user.is_superuser) return true;
    return user.permissions?.includes(permissionName) || false;
  };

  const isAdmin = () => hasRole('Admin') || user?.is_superuser;
  const isManager = () => hasRole('Manager');
  const isViewer = () => hasRole('Viewer');

  const value = {
    user,
    loading,
    error,
    login,
    logout,
    updateUser,
    changePassword,
    hasRole,
    hasPermission,
    isAdmin,
    isManager,
    isViewer,
    isAuthenticated: !!user,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
