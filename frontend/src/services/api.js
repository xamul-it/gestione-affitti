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

// ============================================================================
// MODULAR API EXPORTS
// ============================================================================
// NOTE: APIs are now organized by module. Import from module-specific files
// for better code organization and lazy loading support.
//
// Module structure:
// - modules/anagrafica_italiana/services/anagraficaAPI.js
// - modules/immobili/services/immobiliAPI.js
// - modules/affitti_lungo/services/affittiAPI.js
//
// This file maintains backward compatibility by re-exporting all APIs.
// New code should import directly from module files.
// ============================================================================

// Import module APIs
import * as anagraficaModule from '../modules/anagrafica_italiana/services/anagraficaAPI.js';
import * as immobiliModule from '../modules/immobili/services/immobiliAPI.js';
import * as affittiModule from '../modules/affitti_lungo/services/affittiAPI.js';

// Re-export from anagrafica_italiana module
export const { soggettiAnagraficiAPI } = anagraficaModule;

// Re-export from immobili module
export const {
  unitaImmobiliariAPI,
  proprietariAPI,
  dirittiImmobileAPI,
  condominAPI,
  tabelleMillesimaliAPI,
  millesimiImmobileAPI,
  certificatiEnergeticiAPI,
  categorieCatastaliAPI,
} = immobiliModule;

// Re-export from affitti_lungo module
export const {
  affittuariAPI,
  contrattiAPI,
  speseAPI,
  incassiAPI,
  tecniciAPI,
  ripartizioniSpeseAPI,
  documentiAPI,
} = affittiModule;

// Legacy aliases for backward compatibility
export const immobiliAPI = unitaImmobiliariAPI;

// ============================================================================
// PLATFORM-LEVEL APIs (not module-specific)
// ============================================================================

// Search API (platform-level feature)
export const searchAPI = {
  // Legacy flat search (backward compatibility)
  search: (query, limit = 10) => api.get('/search/', {
    params: { q: query, limit }
  }),

  // Unified search with grouped results by entity type
  searchUnified: (query, options = {}) => {
    const params = { q: query };
    if (options.limit_per_entity) params.limit_per_entity = options.limit_per_entity;
    if (options.limit) params.limit = options.limit;
    if (options.modules) params.modules = options.modules;
    if (options.entities) params.entities = options.entities;
    return api.get('/search/unified', { params });
  },

  // Get list of searchable entities for UI
  getSearchableEntities: () => api.get('/search/entities'),
};

// Import/Export API (platform-level feature)
export const importExportAPI = {
  // Import data from CSV (legacy - simple import)
  import: (moduleName, entityName, file, skipErrors = true, enableEnrichment = true, enableUpdates = true) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post('/import-export/import', formData, {
      params: {
        module_name: moduleName,
        entity_name: entityName,
        skip_errors: skipErrors,
        enable_enrichment: enableEnrichment,
        enable_updates: enableUpdates
      },
      headers: { 'Content-Type': 'multipart/form-data' }
    });
  },

  // Export data to CSV/Excel/JSON
  export: (moduleName, entityName, format = 'csv', fields = null) => {
    return api.get('/import-export/export', {
      params: { module_name: moduleName, entity_name: entityName, format, fields },
      responseType: format === 'excel' ? 'blob' : 'json'
    });
  },

  // Get import template
  getTemplate: (moduleName, entityName, includeSample = false) => {
    return api.get('/import-export/template', {
      params: { module_name: moduleName, entity_name: entityName, include_sample: includeSample }
    });
  },

  // === New Import Wizard Methods ===

  // Analyze CSV file and suggest field mappings
  analyzeCSV: (moduleName, entityName, file) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post('/import-export/analyze', formData, {
      params: { module_name: moduleName, entity_name: entityName },
      headers: { 'Content-Type': 'multipart/form-data' }
    });
  },

  // Preview import with field mapping and validation
  previewImport: (moduleName, entityName, file, fieldMapping) => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('field_mapping', JSON.stringify(fieldMapping));
    return api.post('/import-export/preview', formData, {
      params: { module_name: moduleName, entity_name: entityName },
      headers: { 'Content-Type': 'multipart/form-data' }
    });
  },

  // Import data with custom field mapping
  importWithMapping: (moduleName, entityName, file, fieldMapping, skipErrors = true, enableEnrichment = true, enableUpdates = true, saveConfig = false, configName = null) => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('field_mapping', JSON.stringify(fieldMapping));
    if (saveConfig && configName) {
      formData.append('save_configuration', 'true');
      formData.append('configuration_name', configName);
    }
    return api.post('/import-export/import', formData, {
      params: {
        module_name: moduleName,
        entity_name: entityName,
        skip_errors: skipErrors,
        enable_enrichment: enableEnrichment,
        enable_updates: enableUpdates
      },
      headers: { 'Content-Type': 'multipart/form-data' }
    });
  },

  // Get saved import configurations for an entity
  getImportConfigurations: (moduleName, entityName) => {
    return api.get('/import-export/configurations', {
      params: { module_name: moduleName, entity_name: entityName }
    });
  },

  // Get a specific configuration by ID
  getImportConfiguration: (configId) => {
    return api.get(`/import-export/configurations/${configId}`);
  },

  // Save a new import configuration
  saveImportConfiguration: (config) => {
    return api.post('/import-export/configurations', config);
  },

  // Delete an import configuration
  deleteImportConfiguration: (configId) => {
    return api.delete(`/import-export/configurations/${configId}`);
  },

  // === Download Methods (direct file downloads) ===

  // Download export as file (CSV or Excel)
  downloadExport: (moduleName, entityName, format = 'csv', fields = null) => {
    return api.get('/import-export/download', {
      params: {
        module_name: moduleName,
        entity_name: entityName,
        format,
        fields
      },
      responseType: 'blob'
    });
  },

  // Download import template as file
  downloadTemplate: (moduleName, entityName, includeSample = false) => {
    return api.get('/import-export/download-template', {
      params: {
        module_name: moduleName,
        entity_name: entityName,
        include_sample: includeSample
      },
      responseType: 'blob'
    });
  },

  // Helper to trigger browser file download from blob response
  triggerDownload: (blob, filename) => {
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
  }
};

// Document parsing debug API (platform admin)
export const documentParsingDebugAPI = {
  getLogs: (params = {}) => api.get('/document-parsing/debug/logs', { params }),
  getJobs: (params = {}) => api.get('/document-parsing/debug/jobs', { params }),
};

// Parsing services configuration (platform admin)
export const parsingServicesAPI = {
  list: () => api.get('/platform/parsing-services'),
  upsert: (payload) => api.post('/platform/parsing-services', payload),
  summary: () => api.get('/platform/parsing-services/summary'),
};

// Auth API - Users and Roles Management (platform-level)
export const authAPI = {
  // Users
  getAllUsers: (token) => api.get('/auth/users', {
    headers: { 'Authorization': `Bearer ${token}` }
  }),
  getUserById: (id, token) => api.get(`/auth/users/${id}`, {
    headers: { 'Authorization': `Bearer ${token}` }
  }),
  createUser: (data, token) => api.post('/auth/users', data, {
    headers: { 'Authorization': `Bearer ${token}` }
  }),
  updateUser: (id, data, token) => api.put(`/auth/users/${id}`, data, {
    headers: { 'Authorization': `Bearer ${token}` }
  }),
  deleteUser: (id, token) => api.delete(`/auth/users/${id}`, {
    headers: { 'Authorization': `Bearer ${token}` }
  }),

  // Role assignment
  assignRole: (userId, roleId, token) => api.post(`/auth/users/${userId}/roles/${roleId}`, {}, {
    headers: { 'Authorization': `Bearer ${token}` }
  }),
  removeRole: (userId, roleId, token) => api.delete(`/auth/users/${userId}/roles/${roleId}`, {
    headers: { 'Authorization': `Bearer ${token}` }
  }),

  // Change password
  changePassword: (data, token) => api.post('/auth/change-password', data, {
    headers: { 'Authorization': `Bearer ${token}` }
  }),
};

// Roles API (platform-level)
export const rolesAPI = {
  getAll: (token) => api.get('/roles/', {
    headers: { 'Authorization': `Bearer ${token}` }
  }),
  getById: (id, token) => api.get(`/roles/${id}`, {
    headers: { 'Authorization': `Bearer ${token}` }
  }),
  getAvailable: (token, attivoOnly = true) => api.get('/ruoli-disponibili/', {
    headers: { 'Authorization': `Bearer ${token}` },
    params: { attivo_only: attivoOnly }
  }),
  getAllWithPermissions: (token) => api.get('/roles-debug/with-permissions', {
    headers: { 'Authorization': `Bearer ${token}` }
  }),
};

// Scadenze API (platform-level - Universal Deadline/Reminder System)
export const scadenzeAPI = {
  // CRUD operations
  create: (data) => api.post('/scadenze/', data),
  createTodo: (data) => api.post('/scadenze/todo', data),
  get: (id) => api.get(`/scadenze/${id}`),
  list: (filters = {}) => api.get('/scadenze/', { params: filters }),
  update: (id, data) => api.put(`/scadenze/${id}`, data),
  delete: (id) => api.delete(`/scadenze/${id}`),

  // State management
  completa: (id, note = null) => api.post(`/scadenze/${id}/completa`, { note }),
  posticipa: (id, nuova_data, note = null) => api.post(`/scadenze/${id}/posticipa`, { nuova_data, note }),
  riattiva: (id) => api.post(`/scadenze/${id}/riattiva`),

  // Entity-specific queries
  getByEntity: (modulo, entityType, entityId, includeCompleted = false) =>
    api.get(`/scadenze/entity/${modulo}/${entityType}/${entityId}`, {
      params: { include_completed: includeCompleted }
    }),

  // My scadenze (created by or recipient)
  getMyScadenze: (includeCompleted = false, onlyOverdue = false) =>
    api.get('/scadenze/my/scadenze', {
      params: {
        include_completed: includeCompleted,
        only_overdue: onlyOverdue
      }
    }),

  // Statistics & Badge info
  getBadgeInfo: () => api.get('/scadenze/badge/info'),
  getStatistics: () => api.get('/scadenze/statistics/summary'),

  // Audit log
  getLogs: (id) => api.get(`/scadenze/${id}/logs`),
};

// Notifiche API (platform-level - Generic Notification System)
export const notificheAPI = {
  list: (params = {}) => api.get('/notifiche/', { params }),
  segnaLetta: (id) => api.post(`/notifiche/${id}/segna-letta`),
  segnaTutteLette: () => api.post('/notifiche/segna-tutte-lette'),
  getBadge: () => api.get('/notifiche/badge'),
};

export default api;
