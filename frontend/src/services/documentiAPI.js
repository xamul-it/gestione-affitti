import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

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

// Generic entity-polymorphic document registry (app/core) — usable by any
// module's entities via entity_type/entity_id, not tied to any one module.
export const documentiAPI = {
  getAll: (entityType, entityId) => api.get('/documenti/', {
    params: { entity_type: entityType, entity_id: entityId }
  }),
  // Document types applicable to an entity type (manifest-declared, with tenant overrides).
  getTipi: (entityType) => api.get('/documenti/tipi', { params: { entity_type: entityType } }),
  // Filters: entity_type, entity_id, tipo_codice, modulo, includi_sostituiti, scadenza_entro_giorni.
  list: (params) => api.get('/documenti/', { params }),
  storico: (id) => api.get(`/documenti/${id}/storico`),
  // Preview needs the Authorization header: fetch as blob, show via object URL.
  view: (id) => api.get(`/documenti/${id}/view`, { responseType: 'blob' }),
  viewFile: (fileId) => api.get(`/documenti/files/${fileId}/view`, { responseType: 'blob' }),
  remove: (id) => api.delete(`/documenti/${id}`),
  getById: (id) => api.get(`/documenti/${id}`),
  upload: (formData) => api.post('/documenti/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  }),
  download: (id) => api.get(`/documenti/${id}/download`, { responseType: 'blob' }),
  update: (id, data) => api.put(`/documenti/${id}`, data),
  delete: (id) => api.delete(`/documenti/${id}`),
};

export default documentiAPI;
