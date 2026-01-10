/**
 * useEntityCRUD - Generic CRUD operations hook
 *
 * Provides a standardized way to perform Create, Read, Update, Delete
 * operations on any entity endpoint.
 *
 * @example
 * const { data, loading, error, fetchAll, create, update, remove } = useEntityCRUD('/affittuari/');
 */

import { useState, useCallback, useRef, useEffect } from 'react';
import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

/**
 * Create an axios instance with auth interceptor
 */
const createApiClient = () => {
  const client = axios.create({
    baseURL: API_BASE_URL,
    headers: {
      'Content-Type': 'application/json',
    },
  });

  client.interceptors.request.use(
    (config) => {
      const token = localStorage.getItem('access_token');
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
      return config;
    },
    (error) => Promise.reject(error)
  );

  return client;
};

/**
 * useEntityCRUD hook
 *
 * @param {string} endpoint - API endpoint (e.g., '/affittuari/')
 * @param {Object} options - Configuration options
 * @param {boolean} options.autoFetch - Auto-fetch on mount (default: true)
 * @param {Object} options.defaultParams - Default query parameters
 * @param {Function} options.onError - Error callback
 * @param {Function} options.onSuccess - Success callback
 * @returns {Object} CRUD operations and state
 */
export function useEntityCRUD(endpoint, options = {}) {
  const {
    autoFetch = true,
    defaultParams = {},
    onError,
    onSuccess,
  } = options;

  // State
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [pagination, setPagination] = useState({
    page: 1,
    pageSize: 20,
    total: 0,
    totalPages: 0,
  });

  // Refs
  const apiClient = useRef(createApiClient());
  const abortController = useRef(null);
  const isMounted = useRef(true);

  // Cleanup on unmount
  useEffect(() => {
    isMounted.current = true;
    return () => {
      isMounted.current = false;
      if (abortController.current) {
        abortController.current.abort();
      }
    };
  }, []);

  /**
   * Handle API errors
   */
  const handleError = useCallback((err, operation) => {
    if (axios.isCancel(err)) {
      return; // Ignore cancelled requests
    }

    let errorMessage = `Errore durante ${operation}`;

    if (err.response) {
      // Server responded with error
      const { data: errorData, status } = err.response;

      if (errorData?.detail) {
        if (typeof errorData.detail === 'string') {
          errorMessage = errorData.detail;
        } else if (Array.isArray(errorData.detail)) {
          errorMessage = errorData.detail.map(e => e.msg || e.message).join(', ');
        }
      } else if (status === 404) {
        errorMessage = 'Risorsa non trovata';
      } else if (status === 403) {
        errorMessage = 'Accesso non autorizzato';
      } else if (status === 401) {
        errorMessage = 'Sessione scaduta, effettuare nuovamente il login';
      } else if (status >= 500) {
        errorMessage = 'Errore del server, riprovare piu tardi';
      }
    } else if (err.request) {
      errorMessage = 'Impossibile raggiungere il server';
    }

    if (isMounted.current) {
      setError(errorMessage);
    }

    if (onError) {
      onError(err, errorMessage);
    }

    console.error(`[useEntityCRUD] ${operation}:`, err);
    return errorMessage;
  }, [onError]);

  /**
   * Fetch all entities with optional parameters
   */
  const fetchAll = useCallback(async (params = {}) => {
    // Cancel previous request
    if (abortController.current) {
      abortController.current.abort();
    }
    abortController.current = new AbortController();

    try {
      setLoading(true);
      setError(null);

      const queryParams = { ...defaultParams, ...params };

      const response = await apiClient.current.get(endpoint, {
        params: queryParams,
        signal: abortController.current.signal,
      });

      if (isMounted.current) {
        // Handle paginated response
        if (response.data?.items && response.data?.total !== undefined) {
          setData(response.data.items);
          setPagination({
            page: response.data.page || 1,
            pageSize: response.data.page_size || 20,
            total: response.data.total,
            totalPages: Math.ceil(response.data.total / (response.data.page_size || 20)),
          });
        } else {
          // Handle array response (non-paginated)
          setData(Array.isArray(response.data) ? response.data : [response.data]);
          setPagination(prev => ({
            ...prev,
            total: Array.isArray(response.data) ? response.data.length : 1,
            totalPages: 1,
          }));
        }

        if (onSuccess) {
          onSuccess('fetch', response.data);
        }
      }

      return response.data;
    } catch (err) {
      handleError(err, 'il caricamento dei dati');
      throw err;
    } finally {
      if (isMounted.current) {
        setLoading(false);
      }
    }
  }, [endpoint, defaultParams, handleError, onSuccess]);

  /**
   * Fetch single entity by ID
   */
  const fetchById = useCallback(async (id) => {
    try {
      setLoading(true);
      setError(null);

      const response = await apiClient.current.get(`${endpoint}${id}`);

      if (onSuccess) {
        onSuccess('fetchById', response.data);
      }

      return response.data;
    } catch (err) {
      handleError(err, 'il caricamento del record');
      throw err;
    } finally {
      if (isMounted.current) {
        setLoading(false);
      }
    }
  }, [endpoint, handleError, onSuccess]);

  /**
   * Create new entity
   */
  const create = useCallback(async (entityData) => {
    try {
      setLoading(true);
      setError(null);

      const response = await apiClient.current.post(endpoint, entityData);

      if (isMounted.current) {
        // Add to local data
        setData(prev => [...prev, response.data]);
        setPagination(prev => ({ ...prev, total: prev.total + 1 }));
      }

      if (onSuccess) {
        onSuccess('create', response.data);
      }

      return response.data;
    } catch (err) {
      handleError(err, 'la creazione');
      throw err;
    } finally {
      if (isMounted.current) {
        setLoading(false);
      }
    }
  }, [endpoint, handleError, onSuccess]);

  /**
   * Update existing entity
   */
  const update = useCallback(async (id, entityData) => {
    try {
      setLoading(true);
      setError(null);

      const response = await apiClient.current.put(`${endpoint}${id}`, entityData);

      if (isMounted.current) {
        // Update local data
        setData(prev => prev.map(item =>
          item.id === id ? response.data : item
        ));
      }

      if (onSuccess) {
        onSuccess('update', response.data);
      }

      return response.data;
    } catch (err) {
      handleError(err, "l'aggiornamento");
      throw err;
    } finally {
      if (isMounted.current) {
        setLoading(false);
      }
    }
  }, [endpoint, handleError, onSuccess]);

  /**
   * Delete entity
   */
  const remove = useCallback(async (id) => {
    try {
      setLoading(true);
      setError(null);

      await apiClient.current.delete(`${endpoint}${id}`);

      if (isMounted.current) {
        // Remove from local data
        setData(prev => prev.filter(item => item.id !== id));
        setPagination(prev => ({ ...prev, total: Math.max(0, prev.total - 1) }));
      }

      if (onSuccess) {
        onSuccess('delete', id);
      }

      return true;
    } catch (err) {
      handleError(err, "l'eliminazione");
      throw err;
    } finally {
      if (isMounted.current) {
        setLoading(false);
      }
    }
  }, [endpoint, handleError, onSuccess]);

  /**
   * Bulk delete entities
   */
  const bulkDelete = useCallback(async (ids) => {
    try {
      setLoading(true);
      setError(null);

      // Delete sequentially (could be parallel with Promise.all)
      for (const id of ids) {
        await apiClient.current.delete(`${endpoint}${id}`);
      }

      if (isMounted.current) {
        setData(prev => prev.filter(item => !ids.includes(item.id)));
        setPagination(prev => ({
          ...prev,
          total: Math.max(0, prev.total - ids.length),
        }));
      }

      if (onSuccess) {
        onSuccess('bulkDelete', ids);
      }

      return true;
    } catch (err) {
      handleError(err, "l'eliminazione multipla");
      throw err;
    } finally {
      if (isMounted.current) {
        setLoading(false);
      }
    }
  }, [endpoint, handleError, onSuccess]);

  /**
   * Refresh data (re-fetch with current params)
   */
  const refresh = useCallback(() => {
    return fetchAll();
  }, [fetchAll]);

  /**
   * Clear error state
   */
  const clearError = useCallback(() => {
    setError(null);
  }, []);

  // Auto-fetch on mount
  useEffect(() => {
    if (autoFetch) {
      fetchAll();
    }
  }, [autoFetch]); // eslint-disable-line react-hooks/exhaustive-deps

  return {
    // State
    data,
    loading,
    error,
    pagination,

    // Operations
    fetchAll,
    fetchById,
    create,
    update,
    remove,
    bulkDelete,
    refresh,
    clearError,

    // Setters for external manipulation
    setData,
    setError,
  };
}

export default useEntityCRUD;
