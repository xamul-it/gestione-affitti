/**
 * ContrattiPage - Contratti list page using core components
 *
 * This is a MIGRATION from custom components to core reusable components.
 *
 * BEFORE (ContrattiList.jsx + ContrattoForm.jsx): ~565 lines of code
 * AFTER (ContrattiPage.jsx + contratti.config.js): ~500 lines total
 *
 * NET REDUCTION: ~65 lines (~12% reduction)
 * More importantly: Consistent UX, automatic validation, better error handling,
 * WCAG compliance, mobile-friendly design, and maintainable configuration.
 */

import React, { useState, useCallback } from 'react';
import { DataTable, FormBuilder, FormModal } from '../../../core/components';
import DocumentiSection from '../components/Documenti/DocumentiSection';
import { contrattiConfig } from '../config';

/**
 * ContrattoFormModal - Form wrapper component
 *
 * Wraps FormBuilder in a modal and adds DocumentiSection for contract documents
 */
function ContrattoFormModal({ entity, onClose }) {
  const handleSuccess = useCallback(() => {
    // Close modal after successful save
    setTimeout(() => onClose(), 1000);
  }, [onClose]);

  return (
    <FormModal
      title={entity ? 'Modifica Contratto' : 'Nuovo Contratto'}
      onClose={onClose}
      size="xlarge"
    >
      <FormBuilder
        config={contrattiConfig.form}
        entity={entity}
        apiEndpoint={contrattiConfig.endpoint}
        onSuccess={handleSuccess}
        onCancel={onClose}
      />

      {/* Entity-specific: Document uploads (only when editing) */}
      {entity?.id && (
        <div style={{ marginTop: '1.5rem', paddingTop: '1.5rem', borderTop: '1px solid #e5e7eb' }}>
          <DocumentiSection entityType="CONTRATTO" entityId={entity.id} />
        </div>
      )}
    </FormModal>
  );
}

/**
 * ContrattiPage - Main page component
 *
 * Uses DataTable with configuration from contratti.config.js
 * Features complex form with multiple sections, validation, and relationship loading
 */
function ContrattiPage() {
  return (
    <div className="page-container">
      <DataTable
        config={{
          endpoint: contrattiConfig.endpoint,
          title: contrattiConfig.table.title,
          columns: contrattiConfig.table.columns,
          rowActions: contrattiConfig.table.rowActions,
          bulkActions: contrattiConfig.table.bulkActions,
          defaultSort: contrattiConfig.table.defaultSort,
          searchPlaceholder: contrattiConfig.table.searchPlaceholder,
          emptyTitle: contrattiConfig.table.emptyTitle,
          emptyMessage: contrattiConfig.table.emptyMessage,
          addButtonLabel: contrattiConfig.table.addButtonLabel,
        }}
        FormComponent={ContrattoFormModal}
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

export default ContrattiPage;
