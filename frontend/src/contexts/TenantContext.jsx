import { createContext, useContext, useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { refreshTokenSafe } from '../services/tokenService';

const TenantContext = createContext(null);

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

export function TenantProvider({ children }) {
  const [currentTenant, setCurrentTenant] = useState(null);
  const [availableTenants, setAvailableTenants] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const isFetchingRef = useRef(false); // Use ref to prevent render loops
  const refreshAttemptedRef = useRef(false);

  // Initialize tenant state from localStorage
  useEffect(() => {
    const savedTenant = localStorage.getItem('current_tenant');
    if (savedTenant) {
      try {
        setCurrentTenant(JSON.parse(savedTenant));
      } catch (err) {
        console.error('Failed to parse saved tenant:', err);
        localStorage.removeItem('current_tenant');
      }
    }
  }, []);

  useEffect(() => {
    const token = localStorage.getItem('access_token');
    if (!token || availableTenants.length > 0 || isFetchingRef.current) {
      return;
    }
    fetchUserTenants().catch(() => {
      // Errors are handled inside fetchUserTenants
    });
  }, [availableTenants.length]);

  /**
   * Fetch accessible tenants for the current user
   */
  const fetchUserTenants = async () => {
    // Prevent concurrent fetches using ref
    if (isFetchingRef.current) {
      console.log('[TenantContext] Fetch already in progress, skipping...');
      return availableTenants;
    }

    // Additional safety: check if we already have tenants
    if (availableTenants.length > 0) {
      console.log('[TenantContext] Tenants already loaded, skipping fetch');
      return availableTenants;
    }

    try {
      isFetchingRef.current = true;
      setLoading(true);
      setError(null);

      let token = localStorage.getItem('access_token');
      if (!token) {
        // Use centralized refresh
        token = await refreshTokenSafe();
      }
      if (!token) {
        throw new Error('No access token found');
      }

      console.log('[TenantContext] Fetching tenants...');
      const response = await axios.get(`${API_BASE_URL}/tenants/my-tenants`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      console.log('[TenantContext] Tenants fetched:', response.data.length);
      setAvailableTenants(response.data);

      return response.data;
    } catch (err) {
      const status = err.response?.status;
      if ((status === 401 || status === 403) && !refreshAttemptedRef.current) {
        refreshAttemptedRef.current = true;
        // Use centralized refresh
        const newToken = await refreshTokenSafe();
        if (newToken) {
          try {
            const retryResponse = await axios.get(`${API_BASE_URL}/tenants/my-tenants`, {
              headers: {
                'Authorization': `Bearer ${newToken}`
              }
            });
            setAvailableTenants(retryResponse.data);
            return retryResponse.data;
          } catch (retryErr) {
            console.error('Failed to fetch tenants after refresh:', retryErr);
          }
        }
      }

      const errorMessage = err.response?.data?.detail || 'Failed to fetch tenants';
      setError(errorMessage);
      console.error('Failed to fetch user tenants:', err);
      throw err;
    } finally {
      setLoading(false);
      isFetchingRef.current = false;
      refreshAttemptedRef.current = false;
    }
  };

  /**
   * Switch to a different tenant
   * @param {number} tenantId - The ID of the tenant to switch to
   */
  const switchTenant = async (tenantId) => {
    try {
      setLoading(true);
      setError(null);

      let token = localStorage.getItem('access_token');

      // If no access token, try to refresh first using centralized refresh
      if (!token) {
        token = await refreshTokenSafe();
      }

      if (!token) {
        throw new Error('No access token found');
      }

      // Try to switch tenant
      let response;
      try {
        response = await axios.post(
          `${API_BASE_URL}/tenants/switch`,
          { tenant_id: tenantId },
          {
            headers: {
              'Authorization': `Bearer ${token}`
            }
          }
        );
      } catch (switchErr) {
        // If 401, try refresh and retry once using centralized refresh
        if (switchErr.response?.status === 401) {
          console.log('[TenantContext] Switch got 401, attempting token refresh...');
          const newToken = await refreshTokenSafe();
          if (newToken) {
            // Retry switch with new token
            response = await axios.post(
              `${API_BASE_URL}/tenants/switch`,
              { tenant_id: tenantId },
              {
                headers: {
                  'Authorization': `Bearer ${newToken}`
                }
              }
            );
          } else {
            throw switchErr;
          }
        } else {
          throw switchErr;
        }
      }

      const { access_token, tenant, refresh_token } = response.data;

      // Debug logging
      console.log('[TenantContext] Switch response received');
      console.log('[TenantContext] access_token received:', !!access_token, 'length:', access_token?.length);
      console.log('[TenantContext] refresh_token received:', !!refresh_token, 'length:', refresh_token?.length);

      if (!access_token) {
        throw new Error('No access_token in switch response');
      }

      // Update tokens FIRST
      localStorage.setItem('access_token', access_token);
      if (refresh_token) {
        localStorage.setItem('refresh_token', refresh_token);
      }

      // Verify tokens were saved correctly
      const savedAccess = localStorage.getItem('access_token');
      const savedRefresh = localStorage.getItem('refresh_token');
      console.log('[TenantContext] Token verification:');
      console.log('  - access_token saved correctly:', savedAccess === access_token);
      console.log('  - refresh_token saved correctly:', savedRefresh === refresh_token);

      if (savedAccess !== access_token) {
        console.error('[TenantContext] CRITICAL: access_token was not saved correctly!');
      }

      // Update current tenant
      localStorage.setItem('current_tenant', JSON.stringify(tenant));

      // Force tenant list refresh after switch
      sessionStorage.removeItem('tenants_fetched');

      // Force reload to apply new tenant context
      // Use replace to avoid back button issues
      window.location.replace('/');

      return tenant;
    } catch (err) {
      const errorMessage = err.response?.data?.detail || 'Failed to switch tenant';
      setError(errorMessage);
      console.error('Failed to switch tenant:', err);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  /**
   * Clear tenant context (called on logout)
   */
  const clearTenantContext = () => {
    setCurrentTenant(null);
    setAvailableTenants([]);
    localStorage.removeItem('current_tenant');
  };

  /**
   * Check if user has access to multiple tenants
   */
  const hasMultipleTenants = () => {
    return availableTenants.length > 1;
  };

  /**
   * Get tenant by ID from available tenants
   */
  const getTenantById = (tenantId) => {
    return availableTenants.find(t => t.id === tenantId);
  };

  /**
   * Refresh tenant list without auto-switching
   */
  const refreshTenants = async () => {
    try {
      setLoading(true);
      setError(null);

      let token = localStorage.getItem('access_token');
      if (!token) {
        token = await refreshTokenSafe();
      }
      if (!token) {
        throw new Error('No access token found');
      }

      const response = await axios.get(`${API_BASE_URL}/tenants/my-tenants`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      setAvailableTenants(response.data);
      return response.data;
    } catch (err) {
      const status = err.response?.status;
      if ((status === 401 || status === 403) && !refreshAttemptedRef.current) {
        refreshAttemptedRef.current = true;
        const newToken = await refreshTokenSafe();
        if (newToken) {
          try {
            const retryResponse = await axios.get(`${API_BASE_URL}/tenants/my-tenants`, {
              headers: {
                'Authorization': `Bearer ${newToken}`
              }
            });
            setAvailableTenants(retryResponse.data);
            return retryResponse.data;
          } catch (retryErr) {
            console.error('Failed to refresh tenants after token refresh:', retryErr);
          }
        }
      }

      const errorMessage = err.response?.data?.detail || 'Failed to refresh tenants';
      setError(errorMessage);
      console.error('Failed to refresh tenants:', err);
      throw err;
    } finally {
      setLoading(false);
      refreshAttemptedRef.current = false;
    }
  };

  const value = {
    currentTenant,
    availableTenants,
    loading,
    error,
    fetchUserTenants,
    switchTenant,
    clearTenantContext,
    hasMultipleTenants,
    getTenantById,
    refreshTenants,
    hasTenant: !!currentTenant,
  };

  return <TenantContext.Provider value={value}>{children}</TenantContext.Provider>;
}

export function useTenant() {
  const context = useContext(TenantContext);
  if (!context) {
    throw new Error('useTenant must be used within a TenantProvider');
  }
  return context;
}
