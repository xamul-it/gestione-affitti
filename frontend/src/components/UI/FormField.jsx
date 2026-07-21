import './FormField.css';

export default function FormField({ label, htmlFor, error, children }) {
  return (
    <div className="ds-field">
      {label ? (
        <label className="ds-field__label" htmlFor={htmlFor}>
          {label}
        </label>
      ) : null}
      {children}
      {error ? (
        <p className="ds-field__error" role="alert">
          {error}
        </p>
      ) : null}
    </div>
  );
}
