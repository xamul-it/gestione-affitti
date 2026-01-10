/**
 * Proprietari Entity Configuration
 *
 * This file defines the complete configuration for the Proprietari entity,
 * including table columns, form fields, and detail view settings.
 *
 * Using core components, this single file replaces:
 * - ProprietariList.jsx (~150 lines)
 * - ProprietarioForm.jsx (~240 lines)
 *
 * Total: ~390 lines reduced to ~180 lines of configuration
 */

export const proprietariConfig = {
  // Entity identification
  entity: 'proprietari',
  displayName: 'Proprietari',
  displayNameSingular: 'Proprietario',

  // API endpoint
  endpoint: '/proprietari/',

  // ===== TABLE CONFIGURATION =====
  table: {
    title: 'Gestione Proprietari',
    searchPlaceholder: 'Cerca per nome, cognome, codice fiscale, email...',
    emptyTitle: 'Nessun proprietario trovato',
    emptyMessage: 'Non ci sono proprietari registrati. Clicca su "Nuovo Proprietario" per iniziare.',
    addButtonLabel: 'Nuovo Proprietario',

    columns: [
      {
        field: 'nome',
        label: 'Nome',
        sortable: true,
        filterable: true,
      },
      {
        field: 'cognome',
        label: 'Cognome',
        sortable: true,
        filterable: true,
      },
      {
        field: 'codice_fiscale',
        label: 'Codice Fiscale',
        width: 180,
      },
      {
        field: 'email',
        label: 'Email',
        render: (value) => value || '-',
      },
      {
        field: 'telefono',
        label: 'Telefono',
        render: (value, row) => value || row.cellulare || '-',
      },
      {
        field: 'citta',
        label: 'Citta',
        render: (value) => value || '-',
      },
      {
        field: 'attivo',
        label: 'Stato',
        render: (value) => ({
          type: 'badge',
          variant: value ? 'success' : 'secondary',
          label: value ? 'Attivo' : 'Inattivo',
        }),
      },
    ],

    defaultSort: { field: 'cognome', order: 'asc' },

    rowActions: [
      {
        id: 'view',
        label: 'Dettagli',
        to: '/proprietari/:id',
        variant: 'primary',
      },
      {
        id: 'edit',
        label: 'Modifica',
        action: 'edit',
        variant: 'secondary',
      },
      {
        id: 'delete',
        label: 'Disattiva',
        action: 'delete',
        variant: 'danger',
        confirmMessage: 'Sei sicuro di voler disattivare questo proprietario?',
      },
    ],

    bulkActions: [
      {
        id: 'bulkDelete',
        label: 'Disattiva selezionati',
        action: 'bulkDelete',
        variant: 'danger',
      },
    ],
  },

  // ===== FORM CONFIGURATION =====
  form: {
    sections: [
      {
        title: 'Dati Personali',
        columns: 2,
        fields: [
          {
            name: 'nome',
            label: 'Nome',
            type: 'text',
            required: true,
            placeholder: 'Inserisci il nome',
          },
          {
            name: 'cognome',
            label: 'Cognome',
            type: 'text',
            required: true,
            placeholder: 'Inserisci il cognome',
          },
          {
            name: 'codice_fiscale',
            label: 'Codice Fiscale',
            type: 'text',
            required: true,
            placeholder: 'RSSMRA80A01H501X',
            colSpan: 2,
            validation: {
              maxLength: 16,
              pattern: /^[A-Z]{6}\d{2}[A-Z]\d{2}[A-Z]\d{3}[A-Z]$/i,
              message: 'Codice fiscale non valido (formato: RSSMRA80A01H501X)',
            },
          },
          {
            name: 'data_nascita',
            label: 'Data di Nascita',
            type: 'date',
          },
          {
            name: 'luogo_nascita',
            label: 'Luogo di Nascita',
            type: 'text',
            placeholder: 'Citta di nascita',
          },
        ],
      },
      {
        title: 'Contatti',
        columns: 2,
        fields: [
          {
            name: 'email',
            label: 'Email',
            type: 'email',
            placeholder: 'email@esempio.com',
            colSpan: 2,
          },
          {
            name: 'telefono',
            label: 'Telefono',
            type: 'tel',
            placeholder: '02 1234567',
          },
          {
            name: 'cellulare',
            label: 'Cellulare',
            type: 'tel',
            placeholder: '333 1234567',
          },
        ],
      },
      {
        title: 'Residenza',
        columns: 3,
        fields: [
          {
            name: 'indirizzo',
            label: 'Indirizzo',
            type: 'text',
            placeholder: 'Via/Piazza e numero civico',
            colSpan: 3,
          },
          {
            name: 'citta',
            label: 'Citta',
            type: 'text',
            placeholder: 'Nome della citta',
          },
          {
            name: 'cap',
            label: 'CAP',
            type: 'text',
            placeholder: '00100',
            validation: {
              maxLength: 5,
              pattern: /^\d{5}$/,
              message: 'CAP deve essere di 5 cifre',
            },
          },
          {
            name: 'provincia',
            label: 'Provincia',
            type: 'text',
            placeholder: 'RM',
            validation: {
              maxLength: 2,
              message: 'Provincia deve essere di 2 caratteri',
            },
          },
        ],
      },
      {
        title: 'Stato e Note',
        fields: [
          {
            name: 'attivo',
            label: 'Attivo',
            type: 'checkbox',
            defaultValue: true,
            help: 'Deseleziona per disattivare il proprietario',
          },
          {
            name: 'note',
            label: 'Note',
            type: 'textarea',
            rows: 3,
            placeholder: 'Note aggiuntive...',
          },
        ],
      },
    ],
  },

  // ===== DETAIL VIEW CONFIGURATION =====
  detail: {
    title: ':nome :cognome',
    icon: 'user-tie',
    backLink: '/proprietari',

    headerBadges: [
      {
        field: 'codice_fiscale',
        prefix: 'CF: ',
        variant: 'info',
      },
      {
        field: 'attivo',
        render: (value) => value ? 'Attivo' : 'Inattivo',
        variant: (value) => value ? 'success' : 'secondary',
      },
    ],

    quickStats: [
      {
        id: 'immobili',
        label: 'Immobili',
        field: 'immobili_count',
        icon: 'building',
      },
      {
        id: 'diritti',
        label: 'Diritti',
        field: 'diritti_count',
        icon: 'file-contract',
      },
    ],

    tabs: [
      {
        id: 'info',
        label: 'Informazioni',
        sections: [
          {
            title: 'Dati Personali',
            fields: [
              { field: 'nome', label: 'Nome' },
              { field: 'cognome', label: 'Cognome' },
              { field: 'codice_fiscale', label: 'Codice Fiscale' },
              { field: 'data_nascita', label: 'Data di Nascita', type: 'date' },
              { field: 'luogo_nascita', label: 'Luogo di Nascita' },
            ],
          },
          {
            title: 'Contatti',
            fields: [
              { field: 'email', label: 'Email', type: 'email' },
              { field: 'telefono', label: 'Telefono', type: 'phone' },
              { field: 'cellulare', label: 'Cellulare', type: 'phone' },
            ],
          },
          {
            title: 'Residenza',
            fields: [
              { field: 'indirizzo', label: 'Indirizzo' },
              { field: 'citta', label: 'Citta' },
              { field: 'cap', label: 'CAP' },
              { field: 'provincia', label: 'Provincia' },
            ],
          },
        ],
      },
      {
        id: 'diritti',
        label: 'Diritti Immobiliari',
        component: 'RelatedList',
        config: {
          endpoint: '/diritti-immobile/',
          filterField: 'proprietario_id',
          columns: [
            { field: 'immobile_codice', label: 'Immobile', linkTo: '/immobili/:immobile_id' },
            { field: 'tipo_diritto', label: 'Tipo Diritto' },
            { field: 'percentuale_possesso', label: 'Percentuale', format: (v) => `${v}%` },
            { field: 'data_inizio', label: 'Data Inizio', type: 'date' },
            { field: 'data_fine', label: 'Data Fine', type: 'date' },
          ],
        },
      },
      {
        id: 'documenti',
        label: 'Documenti',
        component: 'DocumentList',
        config: {
          entityType: 'PROPRIETARIO',
        },
      },
    ],
  },
};

export default proprietariConfig;
