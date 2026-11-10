import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

const api = axios.create({ baseURL: API_BASE_URL, headers: { 'Content-Type': 'application/json' } });

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// Role relations soggetto -> object of a module (core /relazioni):
// catalog of relation types, listing (core + module-derived) and core writes.
export const relazioniAPI = {
  getTipi: (entityType) => api.get('/relazioni/tipi', { params: entityType ? { entity_type: entityType } : {} }),
  // Filters: soggetto_id, tipo, entity_type, entity_id, solo_correnti.
  list: (params) => api.get('/relazioni/', { params }),
  create: (data) => api.post('/relazioni/', data),
  update: (id, data) => api.put(`/relazioni/${id}`, data),
  remove: (id) => api.delete(`/relazioni/${id}`),
  rinnova: (id) => api.post(`/relazioni/${id}/rinnova`),
};

export default relazioniAPI;
