/**
 * CheckboxField - Checkbox input field component
 */

import React from 'react';

export function CheckboxField({
  name,
  label,
  value,
  onChange,
  onBlur,
  error,
  touched,
  helpText,
  required,
  disabled,
  className = '',
}) {
  const hasError = touched && error;

  const handleChange = (e) => {
    onChange({
      target: {
        name,
        value: e.target.checked,
        type: 'checkbox',
        checked: e.target.checked,
      },
    });
  };

  return (
    <div className={`core-form-field core-form-field--checkbox ${hasError ? 'core-form-field--error' : ''} ${className}`}>
      <label className="core-form-field__checkbox-wrapper">
        <input
          id={name}
          name={name}
          type="checkbox"
          checked={!!value}
          onChange={handleChange}
          onBlur={onBlur}
          disabled={disabled}
          className="core-form-field__checkbox"
          aria-invalid={hasError}
          aria-describedby={hasError ? `${name}-error` : helpText ? `${name}-help` : undefined}
        />
        <span className="core-form-field__checkbox-label">
          {label}
          {required && <span className="core-form-field__required">*</span>}
        </span>
      </label>
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

export default CheckboxField;
