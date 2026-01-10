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

// Unita Immobiliari API
export const unitaImmobiliariAPI = {
  getAll: () => api.get('/unita-immobiliari/'),
  getById: (id) => api.get(`/unita-immobiliari/${id}`),
  create: (data) => api.post('/unita-immobiliari/', data),
  update: (id, data) => api.put(`/unita-immobiliari/${id}`, data),
  delete: (id) => api.delete(`/unita-immobiliari/${id}`),
};

// Proprietari API
export const proprietariAPI = {
  getAll: (attiviSolo = false) => api.get('/proprietari/', { params: { attivi_solo: attiviSolo } }),
  getById: (id) => api.get(`/proprietari/${id}`),
  create: (data) => api.post('/proprietari/', data),
  update: (id, data) => api.put(`/proprietari/${id}`, data),
  delete: (id) => api.delete(`/proprietari/${id}`),
};

// Diritti Immobile API
export const dirittiImmobileAPI = {
  getAll: (immobileId = null, proprietarioId = null) => api.get('/diritti-immobile/', {
    params: { immobile_id: immobileId, proprietario_id: proprietarioId }
  }),
  getById: (id) => api.get(`/diritti-immobile/${id}`),
  getByImmobile: (immobileId) => api.get(`/diritti-immobile/immobile/${immobileId}`),
  getByProprietario: (proprietarioId) => api.get(`/diritti-immobile/proprietario/${proprietarioId}`),
  create: (data) => api.post('/diritti-immobile/', data),
  update: (id, data) => api.put(`/diritti-immobile/${id}`, data),
  delete: (id) => api.delete(`/diritti-immobile/${id}`),
};

// Condomini API
export const condominAPI = {
  getAll: (attiviSolo = false) => api.get('/condomini/', { params: { attivi_solo: attiviSolo } }),
  getById: (id) => api.get(`/condomini/${id}`),
  create: (data) => api.post('/condomini/', data),
  update: (id, data) => api.put(`/condomini/${id}`, data),
  delete: (id) => api.delete(`/condomini/${id}`),
};

// Tabelle Millesimali API
export const tabelleMillesimaliAPI = {
  getAll: (condominioId = null, attiveSolo = false) => api.get('/tabelle-millesimali/', {
    params: { condominio_id: condominioId, attive_solo: attiveSolo }
  }),
  getById: (id) => api.get(`/tabelle-millesimali/${id}`),
  getByCondominio: (condominioId) => api.get(`/tabelle-millesimali/condominio/${condominioId}`),
  create: (data) => api.post('/tabelle-millesimali/', data),
  update: (id, data) => api.put(`/tabelle-millesimali/${id}`, data),
  delete: (id) => api.delete(`/tabelle-millesimali/${id}`),
};

// Millesimi Immobile API
export const millesimiImmobileAPI = {
  getAll: (immobileId = null, tabellaId = null) => api.get('/millesimi-immobile/', {
    params: { immobile_id: immobileId, tabella_id: tabellaId }
  }),
  getById: (id) => api.get(`/millesimi-immobile/${id}`),
  getByImmobile: (immobileId) => api.get(`/millesimi-immobile/immobile/${immobileId}`),
  getByTabella: (tabellaId) => api.get(`/millesimi-immobile/tabella/${tabellaId}`),
  create: (data) => api.post('/millesimi-immobile/', data),
  update: (id, data) => api.put(`/millesimi-immobile/${id}`, data),
  delete: (id) => api.delete(`/millesimi-immobile/${id}`),
};

// Certificati Energetici API
export const certificatiEnergeticiAPI = {
  getAll: (validiSolo = false) => api.get('/certificati-energetici/', { params: { validi_solo: validiSolo } }),
  getById: (id) => api.get(`/certificati-energetici/${id}`),
  getByImmobile: (immobileId) => api.get(`/certificati-energetici/immobile/${immobileId}`),
  getValidoByImmobile: (immobileId) => api.get(`/certificati-energetici/immobile/${immobileId}/valido`),
  create: (data) => api.post('/certificati-energetici/', data),
  update: (id, data) => api.put(`/certificati-energetici/${id}`, data),
  delete: (id) => api.delete(`/certificati-energetici/${id}`),
};

// Categorie Catastali API
export const categorieCatastaliAPI = {
  getAll: (attiveSolo = false) => api.get('/categorie-catastali/', { params: { attive_solo: attiveSolo } }),
  getById: (id) => api.get(`/categorie-catastali/${id}`),
  create: (data) => api.post('/categorie-catastali/', data),
  update: (id, data) => api.put(`/categorie-catastali/${id}`, data),
  delete: (id) => api.delete(`/categorie-catastali/${id}`),
};

// Terreni API
export const terreniAPI = {
  getAll: (attiviSolo = false, tipologia = null, comune = null, provincia = null) =>
    api.get('/terreni/', {
      params: {
        attivi_solo: attiviSolo,
        tipologia: tipologia,
        comune: comune,
        provincia: provincia
      }
    }),
  getById: (id) => api.get(`/terreni/${id}`),
  getByCodice: (codice) => api.get(`/terreni/codice/${codice}`),
  create: (data) => api.post('/terreni/', data),
  update: (id, data) => api.put(`/terreni/${id}`, data),
  delete: (id) => api.delete(`/terreni/${id}`),
  restore: (id) => api.post(`/terreni/${id}/restore`),
};

export default {
  unitaImmobiliariAPI,
  proprietariAPI,
  dirittiImmobileAPI,
  condominAPI,
  tabelleMillesimaliAPI,
  millesimiImmobileAPI,
  certificatiEnergeticiAPI,
  categorieCatastaliAPI,
  terreniAPI,
};
