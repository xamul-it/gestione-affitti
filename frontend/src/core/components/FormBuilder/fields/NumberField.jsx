/**
 * NumberField - Number input field component
 */

import React from 'react';

export function NumberField({
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
  step = 1,
  className = '',
}) {
  const hasError = touched && error;

  const handleChange = (e) => {
    const newValue = e.target.value;
    // Allow empty string for clearing
    if (newValue === '') {
      onChange({ target: { name, value: '' } });
    } else {
      const numValue = step % 1 !== 0 ? parseFloat(newValue) : parseInt(newValue, 10);
      if (!isNaN(numValue)) {
        onChange({ target: { name, value: numValue } });
      }
    }
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
        type="number"
        value={value ?? ''}
        onChange={handleChange}
        onBlur={onBlur}
        placeholder={placeholder}
        disabled={disabled}
        readOnly={readOnly}
        min={min}
        max={max}
        step={step}
        className="core-form-field__input core-form-field__input--number"
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

export default NumberField;
