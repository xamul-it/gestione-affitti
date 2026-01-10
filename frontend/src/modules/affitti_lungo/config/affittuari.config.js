/**
 * Affittuari Entity Configuration
 *
 * This file defines the complete configuration for the Affittuari entity,
 * including table columns, form fields, and detail view settings.
 *
 * Using core components, this single file replaces:
 * - AffittuariList.jsx (~120 lines)
 * - AffittuarioForm.jsx (~225 lines)
 *
 * Total: ~350 lines reduced to ~150 lines of configuration
 */

export const affittuariConfig = {
  // Entity identification
  entity: 'affittuari',
  displayName: 'Affittuari',
  displayNameSingular: 'Affittuario',

  // API endpoint
  endpoint: '/affittuari/',

  // ===== TABLE CONFIGURATION =====
  table: {
    title: 'Gestione Affittuari',
    searchPlaceholder: 'Cerca per nome, cognome, codice fiscale, email...',
    emptyTitle: 'Nessun affittuario trovato',
    emptyMessage: 'Non ci sono affittuari registrati. Clicca su "Nuovo Affittuario" per iniziare.',
    addButtonLabel: 'Nuovo Affittuario',

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
        field: 'citta_residenza',
        label: 'Citta',
        render: (value) => value || '-',
      },
    ],

    defaultSort: { field: 'cognome', order: 'asc' },

    rowActions: [
      {
        id: 'view',
        label: 'Dettagli',
        to: '/affittuari/:id',
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
        label: 'Elimina',
        action: 'delete',
        variant: 'danger',
      },
    ],

    bulkActions: [
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
            name: 'indirizzo_residenza',
            label: 'Indirizzo',
            type: 'text',
            placeholder: 'Via/Piazza e numero civico',
            colSpan: 3,
          },
          {
            name: 'citta_residenza',
            label: 'Citta',
            type: 'text',
            placeholder: 'Nome della citta',
          },
          {
            name: 'cap_residenza',
            label: 'CAP',
            type: 'text',
            placeholder: '00100',
            validation: {
              maxLength: 5,
              pattern: /^\d{5}$/,
            },
          },
          {
            name: 'provincia_residenza',
            label: 'Provincia',
            type: 'text',
            placeholder: 'RM',
            validation: {
              maxLength: 2,
            },
          },
        ],
      },
      {
        title: 'Note',
        fields: [
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
    icon: 'user',
    backLink: '/affittuari',

    headerBadges: [
      {
        field: 'codice_fiscale',
        prefix: 'CF: ',
        variant: 'info',
      },
    ],

    quickStats: [
      {
        id: 'contratti',
        label: 'Contratti',
        field: 'contratti_count',
        icon: 'file-contract',
      },
      {
        id: 'attivi',
        label: 'Contratti Attivi',
        field: 'contratti_attivi_count',
        icon: 'check',
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
              { field: 'indirizzo_residenza', label: 'Indirizzo' },
              { field: 'citta_residenza', label: 'Citta' },
              { field: 'cap_residenza', label: 'CAP' },
              { field: 'provincia_residenza', label: 'Provincia' },
            ],
          },
        ],
      },
      {
        id: 'contratti',
        label: 'Contratti',
        component: 'RelatedList',
        config: {
          endpoint: '/contratti/',
          filterField: 'affittuario_id',
          columns: [
            { field: 'numero_contratto', label: 'Numero', linkTo: '/contratti/:id' },
            { field: 'data_inizio', label: 'Data Inizio', type: 'date' },
            { field: 'data_fine', label: 'Data Fine', type: 'date' },
            { field: 'canone_mensile', label: 'Canone', type: 'currency' },
            { field: 'stato', label: 'Stato', type: 'badge' },
          ],
        },
      },
      {
        id: 'documenti',
        label: 'Documenti',
        component: 'DocumentList',
        config: {
          entityType: 'AFFITTUARIO',
        },
      },
    ],
  },
};

export default affittuariConfig;
