import ImportVisuraModal from '../ImportVisura/ImportVisuraModal';

/**
 * Document form of the VISURA_CATASTALE type: the visura import (reader +
 * review of the differences), started with the files dropped in the upload.
 * The import attaches the visura to every unit it contains.
 */
export default function VisuraDocumentForm({ initialFiles, onSaved, onCancel }) {
  return (
    <ImportVisuraModal
      embedded
      initialFiles={initialFiles}
      onImported={(totali) => onSaved?.(totali)}
      onClose={onCancel}
    />
  );
}
