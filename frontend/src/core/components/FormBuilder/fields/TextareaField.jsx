/**
 * TextareaField - Multiline text input field component
 */

import React from 'react';

export function TextareaField({
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
  rows = 3,
  maxLength,
  className = '',
}) {
  const hasError = touched && error;
  const charCount = value ? String(value).length : 0;

  return (
    <div className={`core-form-field ${hasError ? 'core-form-field--error' : ''} ${className}`}>
      {label && (
        <label htmlFor={name} className="core-form-field__label">
          {label}
          {required && <span className="core-form-field__required">*</span>}
        </label>
      )}
      <textarea
        id={name}
        name={name}
        value={value ?? ''}
        onChange={onChange}
        onBlur={onBlur}
        placeholder={placeholder}
        disabled={disabled}
        readOnly={readOnly}
        rows={rows}
        maxLength={maxLength}
        className="core-form-field__textarea"
        aria-invalid={hasError}
        aria-describedby={hasError ? `${name}-error` : helpText ? `${name}-help` : undefined}
      />
      <div className="core-form-field__footer">
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
        {maxLength && (
          <span className="core-form-field__charcount">
            {charCount}/{maxLength}
          </span>
        )}
      </div>
    </div>
  );
}

export default TextareaField;
