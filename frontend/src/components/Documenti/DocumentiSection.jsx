import DocumentiPanel from '../../core/components/Documenti/DocumentiPanel';

/**
 * Backward-compatible entry point used by many forms and detail pages:
 * the documents of an entity, now the core typed panel (types declared by
 * the modules, history, preview, scadenze).
 */
function DocumentiSection({ entityType, entityId, title }) {
  return <DocumentiPanel entityType={entityType} entityId={entityId} title={title} />;
}

export default DocumentiSection;
