import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

const api = axios.create({
  baseURL: `${API_BASE_URL}/affitti-brevi`,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add request interceptor to automatically include Authorization header
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Calendari iCal API
export const calendariAPI = {
  getAll: () => api.get('/calendari/'),
  getById: (id) => api.get(`/calendari/${id}`),
  getByImmobile: (immobileId) => api.get(`/calendari/immobile/${immobileId}`),
  create: (data) => api.post('/calendari/', data),
  update: (id, data) => api.put(`/calendari/${id}`, data),
  delete: (id) => api.delete(`/calendari/${id}`),
};

// Sincronizzazione iCal API
export const syncAPI = {
  syncAll: () => api.post('/sync/all'),
  syncCalendario: (calendarioId) => api.post(`/sync/calendario/${calendarioId}`),
  getStatus: () => api.get('/sync/status'),
  getCalendarioStatus: (calendarioId) => api.get(`/sync/calendario/${calendarioId}/status`),
  attiva: (calendarioId) => api.post(`/sync/calendario/${calendarioId}/attiva`),
  disattiva: (calendarioId) => api.post(`/sync/calendario/${calendarioId}/disattiva`),
  resetErrore: (calendarioId) => api.post(`/sync/calendario/${calendarioId}/reset-errore`),
};

// Prenotazioni API
export const prenotazioniAPI = {
  getAll: (params = {}) => api.get('/prenotazioni/', { params }),
  getById: (id) => api.get(`/prenotazioni/${id}`),
  getByImmobile: (immobileId) => api.get(`/prenotazioni/immobile/${immobileId}`),
  create: (data) => api.post('/prenotazioni/', data),
  update: (id, data) => api.put(`/prenotazioni/${id}`, data),
  delete: (id) => api.delete(`/prenotazioni/${id}`),
};

// Ospiti Prenotazione API
export const ospitiAPI = {
  getAll: () => api.get('/ospiti/'),
  getById: (id) => api.get(`/ospiti/${id}`),
  getByPrenotazione: (prenotazioneId) => api.get(`/ospiti/prenotazione/${prenotazioneId}`),
  create: (data) => api.post('/ospiti/', data),
  update: (id, data) => api.put(`/ospiti/${id}`, data),
  delete: (id) => api.delete(`/ospiti/${id}`),
};

// Tasse Soggiorno API
export const tasseAPI = {
  // Config endpoints
  getConfigs: (params = {}) => api.get('/tasse/config', { params }),
  getConfigById: (id) => api.get(`/tasse/config/${id}`),
  getActiveConfigForComune: (comuneId, referenceDate = null) =>
    api.get(`/tasse/config/comune/${comuneId}/active`, {
      params: referenceDate ? { reference_date: referenceDate } : {}
    }),
  createConfig: (data) => api.post('/tasse/config', data),
  createConfigWithScaglioni: (data) => api.post('/tasse/config/with-scaglioni', data),
  updateConfig: (id, data) => api.put(`/tasse/config/${id}`, data),
  deleteConfig: (id) => api.delete(`/tasse/config/${id}`),

  // Scaglioni endpoints
  getScaglioni: (configId) => api.get(`/tasse/config/${configId}/scaglioni`),
  createScaglione: (configId, data) => api.post(`/tasse/config/${configId}/scaglioni`, data),
  updateScaglione: (scaglioneId, data) => api.put(`/tasse/scaglioni/${scaglioneId}`, data),
  deleteScaglione: (scaglioneId) => api.delete(`/tasse/scaglioni/${scaglioneId}`),

  // Calculation endpoints
  calculateTax: (prenotazioneId, forceRecalculate = false) =>
    api.post('/tasse/calculate', {
      prenotazione_id: prenotazioneId,
      force_recalculate: forceRecalculate
    }),

  // TassaPrenotazione endpoints
  getTassePrenotazioni: (params = {}) => api.get('/tasse/prenotazioni', { params }),
  getTassaByPrenotazione: (prenotazioneId) => api.get(`/tasse/prenotazioni/${prenotazioneId}`),
  updateTassaPrenotazione: (prenotazioneId, data) => api.put(`/tasse/prenotazioni/${prenotazioneId}`, data),
  overrideTassa: (prenotazioneId, data) => api.post(`/tasse/prenotazioni/${prenotazioneId}/override`, data),
  removeOverride: (prenotazioneId) => api.delete(`/tasse/prenotazioni/${prenotazioneId}/override`),
};

// Default export
export default {
  calendariAPI,
  prenotazioniAPI,
  ospitiAPI,
  tasseAPI,
};
