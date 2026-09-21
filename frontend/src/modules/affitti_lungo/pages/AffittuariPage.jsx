/**
 * AffittuariPage - Affittuari list page using core components
 *
 * This is a MIGRATION EXAMPLE showing how to use core components.
 *
 * BEFORE (AffittuariList.jsx): ~120 lines of code
 * AFTER (AffittuariPage.jsx): ~80 lines of code (includes form wrapper)
 *
 * The configuration is in: config/affittuari.config.js (~180 lines)
 * But that configuration is REUSABLE across list, form, and detail views.
 *
 * NET REDUCTION: From ~350 lines (list + form) to ~250 lines (config + page)
 * Plus the benefit of consistent behavior, automatic error handling, etc.
 */

import React, { useState, useCallback } from 'react';
import { DataTable, FormBuilder, FormModal } from '../../../core/components';
import DocumentiSection from '../../../components/Documenti/DocumentiSection';
import { affittuariConfig } from '../config';

/**
 * AffittuarioFormModal - Form wrapper component
 *
 * Wraps FormBuilder in a modal and adds DocumentiSection
 * for document uploads (entity-specific feature)
 */
function AffittuarioFormModal({ entity, onClose }) {
  const handleSuccess = useCallback(() => {
    // Close modal after successful save
    setTimeout(() => onClose(), 1000);
  }, [onClose]);

  return (
    <FormModal
      title={entity ? 'Modifica Affittuario' : 'Nuovo Affittuario'}
      onClose={onClose}
      size="large"
    >
      <FormBuilder
        config={affittuariConfig.form}
        entity={entity}
        apiEndpoint={affittuariConfig.endpoint}
        onSuccess={handleSuccess}
        onCancel={onClose}
      />

      {/* Entity-specific: Document uploads (only when editing) */}
      {entity?.id && (
        <div style={{ marginTop: '1.5rem', paddingTop: '1.5rem', borderTop: '1px solid #e5e7eb' }}>
          <DocumentiSection entityType="AFFITTUARIO" entityId={entity.id} />
        </div>
      )}
    </FormModal>
  );
}

/**
 * AffittuariPage - Main page component
 *
 * Uses DataTable with configuration from affittuari.config.js
 */
function AffittuariPage() {
  return (
    <div className="page-container">
      <DataTable
        config={{
          endpoint: affittuariConfig.endpoint,
          title: affittuariConfig.table.title,
          columns: affittuariConfig.table.columns,
          rowActions: affittuariConfig.table.rowActions,
          bulkActions: affittuariConfig.table.bulkActions,
          defaultSort: affittuariConfig.table.defaultSort,
          searchPlaceholder: affittuariConfig.table.searchPlaceholder,
          emptyTitle: affittuariConfig.table.emptyTitle,
          emptyMessage: affittuariConfig.table.emptyMessage,
          addButtonLabel: affittuariConfig.table.addButtonLabel,
        }}
        FormComponent={AffittuarioFormModal}
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

export default AffittuariPage;
