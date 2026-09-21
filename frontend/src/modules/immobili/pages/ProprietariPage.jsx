/**
 * ProprietariPage - Proprietari list page using core components
 *
 * This is a MIGRATION from custom components to core reusable components.
 *
 * BEFORE (ProprietariList.jsx + ProprietarioForm.jsx): ~390 lines of code
 * AFTER (ProprietariPage.jsx + proprietari.config.js): ~250 lines total
 *
 * NET REDUCTION: ~140 lines (~36% reduction)
 * Plus benefits: consistent behavior, automatic error handling, WCAG compliance
 */

import React, { useState, useCallback } from 'react';
import { DataTable, FormBuilder, FormModal } from '../../../core/components';
import { proprietariConfig } from '../config';
import DocumentiSection from '../../../components/Documenti/DocumentiSection';

/**
 * ProprietarioFormModal - Form wrapper component
 *
 * Wraps FormBuilder in a modal and adds document upload section
 */
function ProprietarioFormModal({ entity, onClose }) {
  const handleSuccess = useCallback(() => {
    // Close modal after successful save
    setTimeout(() => onClose(), 1000);
  }, [onClose]);

  return (
    <FormModal
      title={entity ? 'Modifica Proprietario' : 'Nuovo Proprietario'}
      onClose={onClose}
      size="large"
    >
      <FormBuilder
        config={proprietariConfig.form}
        entity={entity}
        apiEndpoint={proprietariConfig.endpoint}
        onSuccess={handleSuccess}
        onCancel={onClose}
      />

      {/* Entity-specific: Document uploads (only when editing) */}
      {entity?.id && (
        <div style={{ marginTop: '1.5rem', paddingTop: '1.5rem', borderTop: '1px solid #e5e7eb' }}>
          <h3 style={{ fontSize: '1rem', fontWeight: '600', marginBottom: '1rem' }}>
            Documenti
          </h3>
          <p style={{ fontSize: '0.875rem', color: '#6b7280' }}>
            Carica documenti relativi al proprietario (documenti di identita, certificati, ecc.)
          </p>
          <DocumentiSection entityType="PROPRIETARIO" entityId={entity.id} />
        </div>
      )}
    </FormModal>
  );
}

/**
 * ProprietariPage - Main page component
 *
 * Uses DataTable with configuration from proprietari.config.js
 */
function ProprietariPage() {
  return (
    <div className="page-container">
      <DataTable
        config={{
          endpoint: proprietariConfig.endpoint,
          title: proprietariConfig.table.title,
          columns: proprietariConfig.table.columns,
          rowActions: proprietariConfig.table.rowActions,
          bulkActions: proprietariConfig.table.bulkActions,
          defaultSort: proprietariConfig.table.defaultSort,
          searchPlaceholder: proprietariConfig.table.searchPlaceholder,
          emptyTitle: proprietariConfig.table.emptyTitle,
          emptyMessage: proprietariConfig.table.emptyMessage,
          addButtonLabel: proprietariConfig.table.addButtonLabel,
        }}
        FormComponent={ProprietarioFormModal}
        options={{
          selectable: true,
          showSearch: true,
          showPagination: true,
          pageSize: 20,
        }}
      />
    </div>
  );
}

export default ProprietariPage;
