import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

const api = axios.create({
  baseURL: API_BASE_URL,
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

export const caselleAPI = {
  getAll: () => api.get('/pec/caselle'),
  getById: (id) => api.get(`/pec/caselle/${id}`),
  create: (data) => api.post('/pec/caselle', data),
  update: (id, data) => api.put(`/pec/caselle/${id}`, data),
  delete: (id) => api.delete(`/pec/caselle/${id}`),
  testConnessione: (id) => api.post(`/pec/caselle/${id}/test-connessione`),
  getUtenti: (id) => api.get(`/pec/caselle/${id}/utenti`),
  addUtente: (id, data) => api.post(`/pec/caselle/${id}/utenti`, data),
  updateUtente: (casellaId, userId, data) =>
    api.put(`/pec/caselle/${casellaId}/utenti/${userId}`, data),
  removeUtente: (casellaId, userId) =>
    api.delete(`/pec/caselle/${casellaId}/utenti/${userId}`),
};

export const messaggiAPI = {
  // params: { casella_id, page, page_size, solo_non_letti, q }
  getAll: (params) => api.get('/pec/messaggi', { params }),
  getById: (id) => api.get(`/pec/messaggi/${id}`),
  segnaLetto: (id, letto = true) =>
    api.post(`/pec/messaggi/${id}/segna-letto`, { letto }),
  getThread: (id) => api.get(`/pec/messaggi/${id}/thread`),
  rispondi: (id, data) => api.post(`/pec/messaggi/${id}/rispondi`, data),
  getRisposte: (id) => api.get(`/pec/messaggi/${id}/risposte`),
};

export const schedulerAPI = {
  getStatus: () => api.get('/pec/scheduler/status'),
  triggerCasella: (id) => api.post(`/pec/scheduler/trigger/${id}`),
  triggerAll: () => api.post('/pec/scheduler/trigger-all'),
};

// params: { casella_id, user_id, azione, limit, offset }
export const auditAPI = {
  getAccessi: (params) => api.get('/pec/audit/accessi', { params }),
  getRisposte: (params) => api.get('/pec/audit/risposte', { params }),
};

export default { caselleAPI, messaggiAPI, schedulerAPI, auditAPI };
