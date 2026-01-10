/**
 * Contratti Entity Configuration
 *
 * This file defines the complete configuration for the Contratti entity,
 * including table columns, complex form fields with multiple sections,
 * and detail view settings.
 *
 * Using core components, this single file replaces:
 * - ContrattiList.jsx (~170 lines)
 * - ContrattoForm.jsx (~395 lines)
 *
 * Total: ~565 lines reduced to ~420 lines of configuration
 * Plus benefits: consistent behavior, automatic validation, better UX
 */

export const contrattiConfig = {
  // Entity identification
  entity: 'contratti',
  displayName: 'Contratti',
  displayNameSingular: 'Contratto',

  // API endpoint
  endpoint: '/contratti/',

  // ===== TABLE CONFIGURATION =====
  table: {
    title: 'Gestione Contratti',
    searchPlaceholder: 'Cerca per numero contratto, affittuario, immobile...',
    emptyTitle: 'Nessun contratto trovato',
    emptyMessage: 'Non ci sono contratti registrati. Clicca su "Nuovo Contratto" per iniziare.',
    addButtonLabel: 'Nuovo Contratto',

    columns: [
      {
        field: 'numero_contratto',
        label: 'Numero',
        sortable: true,
        filterable: true,
        width: 150,
      },
      {
        field: 'affittuario',
        label: 'Affittuario',
        render: (value, row) => {
          if (row.affittuario_nome && row.affittuario_cognome) {
            return `${row.affittuario_nome} ${row.affittuario_cognome}`;
          }
          return '-';
        },
      },
      {
        field: 'immobile',
        label: 'Immobile',
        render: (value, row) => {
          if (row.immobile_codice) {
            return `${row.immobile_codice} - ${row.immobile_indirizzo || ''}`;
          }
          return '-';
        },
      },
      {
        field: 'tipologia_contratto',
        label: 'Tipologia',
        render: (value) => {
          const labels = {
            LIBERO_MERCATO: 'Libero Mercato',
            CANONE_CONCORDATO: 'Canone Concordato',
            TRANSITORIO: 'Transitorio',
            STUDENTI: 'Studenti',
            FORESTERIA: 'Foresteria',
            COMMERCIALE_LIBERO: 'Comm. Libero',
            ALTRO: 'Altro',
          };
          return labels[value] || value;
        },
      },
      {
        field: 'data_inizio',
        label: 'Data Inizio',
        type: 'date',
        sortable: true,
      },
      {
        field: 'data_fine',
        label: 'Data Fine',
        type: 'date',
        sortable: true,
      },
      {
        field: 'canone_mensile',
        label: 'Canone',
        render: (value) => `€ ${parseFloat(value).toFixed(2)}`,
        align: 'right',
      },
      {
        field: 'stato',
        label: 'Stato',
        render: (value) => {
          const variants = {
            ATTIVO: 'success',
            SCADUTO: 'warning',
            DISDETTO: 'secondary',
            TERMINATO: 'secondary',
          };
          const labels = {
            ATTIVO: 'Attivo',
            SCADUTO: 'Scaduto',
            DISDETTO: 'Disdetto',
            TERMINATO: 'Terminato',
          };
          // Return badge config object instead of JSX
          return {
            type: 'badge',
            variant: variants[value] || 'secondary',
            label: labels[value] || value,
          };
        },
      },
    ],

    defaultSort: { field: 'data_inizio', order: 'desc' },

    rowActions: [
      {
        id: 'view',
        label: 'Dettagli',
        to: '/contratti/:id',
        variant: 'primary',
      },
      {
        id: 'edit',
        label: 'Modifica',
        action: 'edit',
        variant: 'secondary',
      },
      {
        id: 'incassi',
        label: 'Gestisci Incassi',
        to: '/contratti/:id/incassi',
        variant: 'info',
      },
      {
        id: 'delete',
        label: 'Elimina',
        action: 'delete',
        variant: 'danger',
        confirmMessage: 'Sei sicuro di voler eliminare questo contratto?',
      },
    ],

    bulkActions: [
      {
        id: 'export',
        label: 'Esporta selezionati',
        action: 'export',
        variant: 'secondary',
      },
      {
        id: 'bulkDelete',
        label: 'Elimina selezionati',
        action: 'bulkDelete',
        variant: 'danger',
      },
    ],
  },

  // ===== FORM CONFIGURATION =====
  form: {
    sections: [
      {
        title: 'Dati Identificativi',
        columns: 2,
        fields: [
          {
            name: 'numero_contratto',
            label: 'Numero Contratto',
            type: 'text',
            required: true,
            placeholder: 'Es. CONTR-2024-001',
            colSpan: 2,
          },
          {
            name: 'uso_immobile',
            label: 'Uso Immobile',
            type: 'select',
            required: true,
            options: [
              { value: 'ABITATIVO', label: 'Abitativo' },
              { value: 'COMMERCIALE', label: 'Commerciale' },
              { value: 'UFFICIO', label: 'Ufficio' },
              { value: 'MAGAZZINO', label: 'Magazzino' },
              { value: 'ALTRO', label: 'Altro' },
            ],
            defaultValue: 'ABITATIVO',
          },
          {
            name: 'tipologia_contratto',
            label: 'Tipologia Contratto',
            type: 'select',
            required: true,
            options: [
              { value: 'LIBERO_MERCATO', label: 'Libero Mercato (4+4 abitativo)' },
              { value: 'CANONE_CONCORDATO', label: 'Canone Concordato (3+2)' },
              { value: 'TRANSITORIO', label: 'Transitorio' },
              { value: 'STUDENTI', label: 'Studenti' },
              { value: 'FORESTERIA', label: 'Foresteria' },
              { value: 'COMMERCIALE_LIBERO', label: 'Commerciale Libero (6+6, 9+9)' },
              { value: 'ALTRO', label: 'Altro' },
            ],
            defaultValue: 'LIBERO_MERCATO',
          },
        ],
      },
      {
        title: 'Parti Contrattuali',
        columns: 2,
        fields: [
          {
            name: 'unita_immobiliare_id',
            label: 'Immobile',
            type: 'select',
            required: true,
            placeholder: 'Seleziona immobile...',
            options: [], // Will be loaded dynamically
            loadOptions: async () => {
              const response = await fetch(`${import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1'}/unita-immobiliari/?limit=1000`, {
                headers: {
                  'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
                },
              });
              const data = await response.json();
              return data.map(immobile => ({
                value: immobile.id,
                label: `${immobile.codice} - ${immobile.indirizzo}, ${immobile.citta}`,
              }));
            },
          },
          {
            name: 'affittuario_id',
            label: 'Affittuario',
            type: 'select',
            required: true,
            placeholder: 'Seleziona affittuario...',
            options: [], // Will be loaded dynamically
            loadOptions: async () => {
              const response = await fetch(`${import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1'}/affittuari/?limit=1000`, {
                headers: {
                  'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
                },
              });
              const data = await response.json();
              return data.map(affittuario => ({
                value: affittuario.id,
                label: `${affittuario.nome} ${affittuario.cognome} - ${affittuario.codice_fiscale}`,
              }));
            },
          },
        ],
      },
      {
        title: 'Durata Contratto',
        columns: 2,
        fields: [
          {
            name: 'durata_anni_iniziale',
            label: 'Durata Iniziale (anni)',
            type: 'number',
            required: true,
            min: 1,
            max: 99,
            defaultValue: 4,
            help: 'Es. 4 per contratto 4+4, 3 per 3+2',
          },
          {
            name: 'durata_anni_rinnovo',
            label: 'Durata Rinnovo (anni)',
            type: 'number',
            min: 1,
            max: 99,
            help: 'Es. 4 per contratto 4+4, 2 per 3+2 (opzionale)',
          },
          {
            name: 'data_inizio',
            label: 'Data Inizio',
            type: 'date',
            required: true,
            validation: {
              custom: (value, formData) => {
                if (formData.data_fine && new Date(value) >= new Date(formData.data_fine)) {
                  return 'Data inizio deve essere prima della data fine';
                }
                return null;
              },
            },
          },
          {
            name: 'data_fine',
            label: 'Data Fine',
            type: 'date',
            required: true,
            validation: {
              custom: (value, formData) => {
                if (formData.data_inizio && new Date(value) <= new Date(formData.data_inizio)) {
                  return 'Data fine deve essere dopo la data inizio';
                }
                return null;
              },
            },
          },
        ],
      },
      {
        title: 'Condizioni Economiche',
        columns: 3,
        fields: [
          {
            name: 'canone_mensile',
            label: 'Canone Mensile (€)',
            type: 'number',
            required: true,
            step: 0.01,
            min: 0,
            placeholder: '0.00',
          },
          {
            name: 'giorno_pagamento',
            label: 'Giorno Pagamento',
            type: 'number',
            min: 1,
            max: 31,
            defaultValue: 1,
            help: 'Giorno del mese (1-31)',
          },
          {
            name: 'deposito_cauzionale',
            label: 'Deposito Cauzionale (€)',
            type: 'number',
            step: 0.01,
            min: 0,
            placeholder: '0.00',
          },
        ],
      },
      {
        title: 'Regime Fiscale',
        columns: 1,
        fields: [
          {
            name: 'regime_fiscale',
            label: 'Regime Fiscale',
            type: 'select',
            required: true,
            options: [
              { value: 'ORDINARIO_IRPEF', label: 'Ordinario IRPEF' },
              { value: 'CEDOLARE_SECCA_21', label: 'Cedolare Secca 21% (Libero Mercato)' },
              { value: 'CEDOLARE_SECCA_10', label: 'Cedolare Secca 10% (Canone Concordato)' },
            ],
            defaultValue: 'ORDINARIO_IRPEF',
          },
        ],
      },
      {
        title: 'Adeguamento ISTAT',
        columns: 3,
        fields: [
          {
            name: 'adeguamento_istat',
            label: 'Adeguamento ISTAT',
            type: 'checkbox',
            defaultValue: false,
            colSpan: 3,
          },
          {
            name: 'percentuale_istat',
            label: 'Percentuale ISTAT (%)',
            type: 'number',
            step: 0.01,
            min: 0,
            max: 100,
            placeholder: '75.00',
            help: 'Es. 75.00 per 75% dell\'indice ISTAT',
            showIf: (formData) => formData.adeguamento_istat,
          },
          {
            name: 'data_ultimo_adeguamento',
            label: 'Data Ultimo Adeguamento',
            type: 'date',
            colSpan: 2,
            showIf: (formData) => formData.adeguamento_istat,
          },
        ],
      },
      {
        title: 'Registrazione',
        columns: 2,
        fields: [
          {
            name: 'registrazione_numero',
            label: 'Numero Registrazione',
            type: 'text',
            placeholder: 'Es. REG-2024-12345',
            colSpan: 2,
          },
          {
            name: 'registrazione_data',
            label: 'Data Registrazione',
            type: 'date',
          },
          {
            name: 'registrazione_agenzia',
            label: 'Agenzia Registrazione',
            type: 'text',
            placeholder: 'Es. Agenzia delle Entrate di Roma 1',
          },
        ],
      },
      {
        title: 'Stato e Note',
        columns: 1,
        fields: [
          {
            name: 'stato',
            label: 'Stato',
            type: 'select',
            options: [
              { value: 'ATTIVO', label: 'Attivo' },
              { value: 'SCADUTO', label: 'Scaduto' },
              { value: 'DISDETTO', label: 'Disdetto' },
              { value: 'TERMINATO', label: 'Terminato' },
            ],
            defaultValue: 'ATTIVO',
          },
          {
            name: 'note',
            label: 'Note',
            type: 'textarea',
            rows: 4,
            placeholder: 'Note aggiuntive sul contratto...',
          },
        ],
      },
    ],
  },

  // ===== DETAIL VIEW CONFIGURATION =====
  detail: {
    title: 'Contratto :numero_contratto',
    icon: 'file-contract',
    backLink: '/contratti',

    headerBadges: [
      {
        field: 'tipologia_contratto',
        render: (value) => {
          const labels = {
            LIBERO_MERCATO: 'Libero Mercato',
            CANONE_CONCORDATO: 'Canone Concordato',
            TRANSITORIO: 'Transitorio',
            STUDENTI: 'Studenti',
            FORESTERIA: 'Foresteria',
            COMMERCIALE_LIBERO: 'Comm. Libero',
            ALTRO: 'Altro',
          };
          return labels[value] || value;
        },
        variant: 'info',
      },
      {
        field: 'stato',
        render: (value) => {
          const labels = {
            ATTIVO: 'Attivo',
            SCADUTO: 'Scaduto',
            DISDETTO: 'Disdetto',
            TERMINATO: 'Terminato',
          };
          return labels[value] || value;
        },
        variant: (value) => {
          const variants = {
            ATTIVO: 'success',
            SCADUTO: 'warning',
            DISDETTO: 'secondary',
            TERMINATO: 'secondary',
          };
          return variants[value] || 'secondary';
        },
      },
    ],

    quickStats: [
      {
        id: 'canone',
        label: 'Canone Mensile',
        field: 'canone_mensile',
        icon: 'euro',
        format: (value) => `€ ${parseFloat(value).toFixed(2)}`,
      },
      {
        id: 'durata',
        label: 'Durata',
        render: (data) => {
          const anni = data.durata_anni_iniziale;
          const rinnovo = data.durata_anni_rinnovo;
          return rinnovo ? `${anni}+${rinnovo} anni` : `${anni} anni`;
        },
        icon: 'calendar',
      },
      {
        id: 'incassi',
        label: 'Incassi',
        field: 'incassi_count',
        icon: 'coins',
      },
    ],

    tabs: [
      {
        id: 'info',
        label: 'Informazioni',
        sections: [
          {
            title: 'Parti Contrattuali',
            fields: [
              { field: 'affittuario_nome', label: 'Affittuario', linkTo: '/affittuari/:affittuario_id' },
              { field: 'immobile_codice', label: 'Immobile', linkTo: '/immobili/:unita_immobiliare_id' },
              { field: 'uso_immobile', label: 'Uso Immobile' },
            ],
          },
          {
            title: 'Tipologia e Durata',
            fields: [
              { field: 'tipologia_contratto', label: 'Tipologia' },
              { field: 'durata_anni_iniziale', label: 'Durata Iniziale (anni)' },
              { field: 'durata_anni_rinnovo', label: 'Durata Rinnovo (anni)' },
              { field: 'data_inizio', label: 'Data Inizio', type: 'date' },
              { field: 'data_fine', label: 'Data Fine', type: 'date' },
            ],
          },
          {
            title: 'Condizioni Economiche',
            fields: [
              { field: 'canone_mensile', label: 'Canone Mensile', type: 'currency' },
              { field: 'giorno_pagamento', label: 'Giorno Pagamento' },
              { field: 'deposito_cauzionale', label: 'Deposito Cauzionale', type: 'currency' },
              { field: 'regime_fiscale', label: 'Regime Fiscale' },
            ],
          },
          {
            title: 'Registrazione',
            fields: [
              { field: 'registrazione_numero', label: 'Numero Registrazione' },
              { field: 'registrazione_data', label: 'Data Registrazione', type: 'date' },
              { field: 'registrazione_agenzia', label: 'Agenzia Registrazione' },
            ],
          },
        ],
      },
      {
        id: 'incassi',
        label: 'Incassi',
        component: 'RelatedList',
        config: {
          endpoint: '/incassi/',
          filterField: 'contratto_id',
          columns: [
            { field: 'mese_riferimento', label: 'Mese', type: 'date' },
            { field: 'importo', label: 'Importo', type: 'currency' },
            { field: 'data_pagamento', label: 'Data Pagamento', type: 'date' },
            { field: 'stato_pagamento', label: 'Stato', type: 'badge' },
          ],
        },
      },
      {
        id: 'documenti',
        label: 'Documenti',
        component: 'DocumentList',
        config: {
          entityType: 'CONTRATTO',
        },
      },
    ],
  },
};

export default contrattiConfig;
