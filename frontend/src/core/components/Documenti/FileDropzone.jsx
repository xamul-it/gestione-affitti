import { useRef, useState } from 'react';
import { FileUp } from 'lucide-react';

/**
 * Drag & drop area for one or more files, keyboard accessible.
 * Styles: .doc-dropzone in Documenti.css (design tokens).
 */
export default function FileDropzone({
  onFiles,
  disabled = false,
  multiple = true,
  accept,
  title = 'Trascina qui i file',
  hint = 'oppure fai clic per sceglierli · più file insieme',
  inputLabel = 'File del documento',
  id = 'doc-dropzone',
}) {
  const inputRef = useRef(null);
  const [over, setOver] = useState(false);

  const handleDrop = (e) => {
    e.preventDefault();
    setOver(false);
    if (!disabled) onFiles(Array.from(e.dataTransfer.files || []));
  };

  return (
    <div
      className={`doc-dropzone${over ? ' doc-dropzone--over' : ''}`}
      onDragOver={(e) => { e.preventDefault(); if (!disabled) setOver(true); }}
      onDragLeave={() => setOver(false)}
      onDrop={handleDrop}
      onClick={() => inputRef.current?.click()}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); inputRef.current?.click(); }
      }}
      role="button"
      tabIndex={0}
      aria-label={title}
      aria-describedby={`${id}-hint`}
    >
      <FileUp size={28} strokeWidth={1.7} className="doc-dropzone__icon" aria-hidden="true" />
      <p className="doc-dropzone__title">{title}</p>
      <p id={`${id}-hint`} className="doc-muted">{hint}</p>
      <input
        ref={inputRef}
        type="file"
        multiple={multiple}
        accept={accept}
        aria-label={inputLabel}
        tabIndex={-1}
        className="doc-dropzone__input"
        onClick={(e) => e.stopPropagation()}
        onChange={(e) => { onFiles(Array.from(e.target.files || [])); e.target.value = ''; }}
      />
    </div>
  );
}
