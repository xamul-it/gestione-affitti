/**
 * DateField - Date input field component
 */

import React from 'react';

export function DateField({
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
  min,
  max,
  className = '',
}) {
  const hasError = touched && error;

  // Format date for input (YYYY-MM-DD)
  const formatDateForInput = (dateValue) => {
    if (!dateValue) return '';
    if (typeof dateValue === 'string') {
      // If already in YYYY-MM-DD format, return as is
      if (/^\d{4}-\d{2}-\d{2}$/.test(dateValue)) {
        return dateValue;
      }
      // Try to parse and format
      const date = new Date(dateValue);
      if (!isNaN(date.getTime())) {
        return date.toISOString().split('T')[0];
      }
    }
    if (dateValue instanceof Date && !isNaN(dateValue.getTime())) {
      return dateValue.toISOString().split('T')[0];
    }
    return '';
  };

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
        type="date"
        value={formatDateForInput(value)}
        onChange={onChange}
        onBlur={onBlur}
        placeholder={placeholder}
        disabled={disabled}
        readOnly={readOnly}
        min={formatDateForInput(min)}
        max={formatDateForInput(max)}
        className="core-form-field__input core-form-field__input--date"
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

export default DateField;
