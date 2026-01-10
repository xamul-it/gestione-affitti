/**
 * TextField - Text input field component
 */

import React from 'react';

export function TextField({
  name,
  label,
  value,
  onChange,
  onBlur,
  error,
  touched,
  placeholder,
  helpText,
  required,
  disabled,
  readOnly,
  type = 'text', // text, email, tel, password, url
  maxLength,
  minLength,
  pattern,
  autoComplete,
  className = '',
}) {
  const hasError = touched && error;

  return (
    <div className={`core-form-field ${hasError ? 'core-form-field--error' : ''} ${className}`}>
      {label && (
        <label htmlFor={name} className="core-form-field__label">
          {label}
          {required && <span className="core-form-field__required">*</span>}
        </label>
      )}
      <input
        id={name}
        name={name}
        type={type}
        value={value ?? ''}
        onChange={onChange}
        onBlur={onBlur}
        placeholder={placeholder}
        disabled={disabled}
        readOnly={readOnly}
        maxLength={maxLength}
        minLength={minLength}
        pattern={pattern}
        autoComplete={autoComplete}
        className="core-form-field__input"
        aria-invalid={hasError}
        aria-describedby={hasError ? `${name}-error` : helpText ? `${name}-help` : undefined}
      />
      {hasError && (
        <p id={`${name}-error`} className="core-form-field__error">
          {error}
        </p>
      )}
      {helpText && !hasError && (
        <p id={`${name}-help`} className="core-form-field__help">
          {helpText}
        </p>
      )}
    </div>
  );
}

export default TextField;
