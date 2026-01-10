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

// Affittuari API
export const affittuariAPI = {
  getAll: () => api.get('/affittuari/'),
  getById: (id) => api.get(`/affittuari/${id}`),
  create: (data) => api.post('/affittuari/', data),
  update: (id, data) => api.put(`/affittuari/${id}`, data),
  delete: (id) => api.delete(`/affittuari/${id}`),
};

// Contratti API
export const contrattiAPI = {
  getAll: () => api.get('/contratti/'),
  getById: (id) => api.get(`/contratti/${id}`),
  getByImmobile: (immobileId) => api.get(`/contratti/immobile/${immobileId}`),
  getByAffittuario: (affittuarioId) => api.get(`/contratti/affittuario/${affittuarioId}`),
  create: (data) => api.post('/contratti/', data),
  update: (id, data) => api.put(`/contratti/${id}`, data),
  delete: (id) => api.delete(`/contratti/${id}`),
};

// Spese API
export const speseAPI = {
  getAll: () => api.get('/spese/'),
  getById: (id) => api.get(`/spese/${id}`),
  getByImmobile: (immobileId) => api.get(`/spese/immobile/${immobileId}`),
  create: (data) => api.post('/spese/', data),
  update: (id, data) => api.put(`/spese/${id}`, data),
  delete: (id) => api.delete(`/spese/${id}`),
};

// Incassi API
export const incassiAPI = {
  getAll: () => api.get('/incassi/'),
  getById: (id) => api.get(`/incassi/${id}`),
  getByContratto: (contrattoId) => api.get(`/incassi/contratto/${contrattoId}`),
  create: (data) => api.post('/incassi/', data),
  update: (id, data) => api.put(`/incassi/${id}`, data),
  delete: (id) => api.delete(`/incassi/${id}`),
};

// Tecnici API
export const tecniciAPI = {
  getAll: (attiviSolo = false) => api.get('/tecnici/', { params: { attivi_solo: attiviSolo } }),
  getById: (id) => api.get(`/tecnici/${id}`),
  create: (data) => api.post('/tecnici/', data),
  update: (id, data) => api.put(`/tecnici/${id}`, data),
  delete: (id) => api.delete(`/tecnici/${id}`),
};

// Ripartizioni Spese API
export const ripartizioniSpeseAPI = {
  getAll: (spesaId = null, immobileId = null) => api.get('/ripartizioni-spese/', {
    params: { spesa_id: spesaId, immobile_id: immobileId }
  }),
  getById: (id) => api.get(`/ripartizioni-spese/${id}`),
  getBySpesa: (spesaId) => api.get(`/ripartizioni-spese/spesa/${spesaId}`),
  getByImmobile: (immobileId) => api.get(`/ripartizioni-spese/immobile/${immobileId}`),
  calcolaRipartizione: (spesaId) => api.post(`/ripartizioni-spese/calcola/${spesaId}`),
  create: (data) => api.post('/ripartizioni-spese/', data),
  update: (id, data) => api.put(`/ripartizioni-spese/${id}`, data),
  delete: (id) => api.delete(`/ripartizioni-spese/${id}`),
};

// Documenti API (shared across modules but primarily used in affitti_lungo)
export const documentiAPI = {
  getAll: (entityType, entityId) => api.get('/documenti/', {
    params: { entity_type: entityType, entity_id: entityId }
  }),
  getById: (id) => api.get(`/documenti/${id}`),
  upload: (formData) => api.post('/documenti/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  }),
  download: (id) => api.get(`/documenti/${id}/download`, { responseType: 'blob' }),
  update: (id, data) => api.put(`/documenti/${id}`, data),
  delete: (id) => api.delete(`/documenti/${id}`),
};

export default {
  affittuariAPI,
  contrattiAPI,
  speseAPI,
  incassiAPI,
  tecniciAPI,
  ripartizioniSpeseAPI,
  documentiAPI,
};
