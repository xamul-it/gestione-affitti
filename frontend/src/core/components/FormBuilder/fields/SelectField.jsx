/**
 * SelectField - Dropdown select field component
 */

import React, { useMemo } from 'react';

export function SelectField({
  name,
  label,
  value,
  onChange,
  onBlur,
  error,
  touched,
  placeholder = 'Seleziona...',
  helpText,
  required,
  disabled,
  options = [],
  optionValue = 'value',
  optionLabel = 'label',
  emptyOption = true,
  className = '',
}) {
  const hasError = touched && error;

  // Normalize options to { value, label } format
  const normalizedOptions = useMemo(() => {
    return options.map((option) => {
      if (typeof option === 'string' || typeof option === 'number') {
        return { value: option, label: String(option) };
      }
      return {
        value: option[optionValue] ?? option.value ?? option.id,
        label: option[optionLabel] ?? option.label ?? option.name ?? option.nome,
      };
    });
  }, [options, optionValue, optionLabel]);

  return (
    <div className={`core-form-field ${hasError ? 'core-form-field--error' : ''} ${className}`}>
      {label && (
        <label htmlFor={name} className="core-form-field__label">
          {label}
          {required && <span className="core-form-field__required">*</span>}
        </label>
      )}
      <select
        id={name}
        name={name}
        value={value ?? ''}
        onChange={onChange}
        onBlur={onBlur}
        disabled={disabled}
        className="core-form-field__select"
        aria-invalid={hasError}
        aria-describedby={hasError ? `${name}-error` : helpText ? `${name}-help` : undefined}
      >
        {emptyOption && (
          <option value="">{placeholder}</option>
        )}
        {normalizedOptions.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
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

export default SelectField;
