/**
 * FormBuilder - Dynamic form generator component
 *
 * Generates forms from configuration, handling layout, validation,
 * and data submission.
 *
 * @example
 * <FormBuilder
 *   config={{ sections: [...] }}
 *   entity={editingEntity}
 *   apiEndpoint="/affittuari/"
 *   onSubmit={handleSave}
 *   onCancel={handleClose}
 * />
 */

import React, { useMemo, useCallback, useEffect, useState } from 'react';
import axios from 'axios';
import { useForm } from '../../hooks';
import { formatApiError } from '../../../utils/errorHandling';
import {
  TextField,
  NumberField,
  SelectField,
  DateField,
  TextareaField,
  CheckboxField,
} from './fields';
import './FormBuilder.css';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

/**
 * Create API client with auth
 */
const createApiClient = () => {
  const client = axios.create({
    baseURL: API_BASE_URL,
    headers: { 'Content-Type': 'application/json' },
  });

  client.interceptors.request.use((config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  });

  return client;
};

/**
 * Field component mapping
 */
const FIELD_COMPONENTS = {
  text: TextField,
  email: TextField,
  tel: TextField,
  password: TextField,
  url: TextField,
  number: NumberField,
  select: SelectField,
  date: DateField,
  textarea: TextareaField,
  checkbox: CheckboxField,
};

/**
 * Extract initial values from config sections
 */
function getInitialValues(sections) {
  const values = {};
  sections.forEach((section) => {
    section.fields?.forEach((field) => {
      values[field.name] = field.defaultValue ?? '';
    });
  });
  return values;
}

/**
 * Extract validation rules from config sections
 */
function getValidationRules(sections) {
  const rules = {};
  sections.forEach((section) => {
    section.fields?.forEach((field) => {
      if (field.required || field.validation) {
        rules[field.name] = {
          required: field.required,
          ...field.validation,
        };
      }
    });
  });
  return rules;
}

/**
 * FormBuilder component
 */
export function FormBuilder({
  config,
  entity,
  apiEndpoint,
  onSubmit,
  onCancel,
  onSuccess,
  onError,
  submitLabel = 'Salva',
  cancelLabel = 'Annulla',
  showCancel = true,
  className = '',
}) {
  const { sections = [] } = config;

  // Extract initial values and validation rules
  const initialValues = useMemo(() => getInitialValues(sections), [sections]);
  const validationRules = useMemo(() => getValidationRules(sections), [sections]);

  // State for dynamic options
  const [dynamicOptions, setDynamicOptions] = useState({});
  const [loadingOptions, setLoadingOptions] = useState({});

  // Form state
  const form = useForm(initialValues, validationRules, { entity });

  // API client
  const api = useMemo(() => createApiClient(), []);

  /**
   * Load dynamic options for fields
   */
  const loadFieldOptions = useCallback(async (field) => {
    if (!field.optionsLoader && !field.optionsEndpoint) return;

    const key = field.name;
    setLoadingOptions((prev) => ({ ...prev, [key]: true }));

    try {
      let options;
      if (field.optionsEndpoint) {
        const response = await api.get(field.optionsEndpoint);
        options = response.data;
      } else if (field.optionsLoader) {
        options = await field.optionsLoader(form.values);
      }

      setDynamicOptions((prev) => ({ ...prev, [key]: options }));
    } catch (err) {
      console.error(`Failed to load options for ${key}:`, err);
    } finally {
      setLoadingOptions((prev) => ({ ...prev, [key]: false }));
    }
  }, [api, form.values]);

  // Load dynamic options on mount and when dependencies change
  useEffect(() => {
    sections.forEach((section) => {
      section.fields?.forEach((field) => {
        if (field.optionsLoader || field.optionsEndpoint) {
          loadFieldOptions(field);
        }
      });
    });
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  /**
   * Handle form submission
   */
  const handleSubmit = form.handleSubmit(async (values) => {
    try {
      // Clean data - convert empty strings to null for optional fields
      const cleanedData = { ...values };
      sections.forEach((section) => {
        section.fields?.forEach((field) => {
          const value = cleanedData[field.name];

          // Convert empty strings to null for non-required fields
          if (value === '' && !field.required) {
            cleanedData[field.name] = null;
          }

          // Convert number strings to numbers
          if (field.type === 'number' && value !== '' && value !== null) {
            cleanedData[field.name] = Number(value);
          }

          // Handle select fields with numeric IDs
          if (field.type === 'select' && value !== '' && value !== null) {
            // Check if it should be a number
            if (field.name.endsWith('_id') || field.numericValue) {
              cleanedData[field.name] = parseInt(value, 10);
            }
          }
        });
      });

      let result;

      // If custom onSubmit provided, use it
      if (onSubmit) {
        result = await onSubmit(cleanedData, entity);
      }
      // Otherwise, use API endpoint
      else if (apiEndpoint) {
        if (entity?.id) {
          const response = await api.put(`${apiEndpoint}${entity.id}`, cleanedData);
          result = response.data;
        } else {
          const response = await api.post(apiEndpoint, cleanedData);
          result = response.data;
        }
      }

      if (onSuccess) {
        onSuccess(result, entity ? 'update' : 'create');
      }

      return result;
    } catch (err) {
      const errorMessage = formatApiError ? formatApiError(err) : err.message;
      if (onError) {
        onError(err, errorMessage);
      }
      throw err;
    }
  });

  /**
   * Check if field should be visible (conditional display)
   */
  const isFieldVisible = useCallback((field) => {
    if (!field.showIf) return true;
    return field.showIf(form.values);
  }, [form.values]);

  /**
   * Render a single field
   */
  const renderField = useCallback((field, index) => {
    if (!isFieldVisible(field)) return null;

    const FieldComponent = FIELD_COMPONENTS[field.type] || TextField;

    // Get field-specific props
    const fieldProps = {
      key: field.name,
      name: field.name,
      label: field.label,
      value: form.values[field.name],
      onChange: form.handleChange,
      onBlur: form.handleBlur,
      error: form.errors[field.name],
      touched: form.touched[field.name],
      placeholder: field.placeholder,
      helpText: field.helpText,
      required: field.required,
      disabled: field.disabled || form.isSubmitting,
      readOnly: field.readOnly,
    };

    // Type-specific props
    switch (field.type) {
      case 'email':
      case 'tel':
      case 'password':
      case 'url':
        fieldProps.type = field.type;
        break;
      case 'number':
        fieldProps.min = field.min;
        fieldProps.max = field.max;
        fieldProps.step = field.step;
        break;
      case 'select':
        fieldProps.options = dynamicOptions[field.name] || field.options || [];
        fieldProps.optionValue = field.optionValue;
        fieldProps.optionLabel = field.optionLabel;
        fieldProps.emptyOption = field.emptyOption !== false;
        fieldProps.placeholder = field.placeholder || 'Seleziona...';
        fieldProps.disabled = fieldProps.disabled || loadingOptions[field.name];
        break;
      case 'date':
        fieldProps.min = field.min;
        fieldProps.max = field.max;
        break;
      case 'textarea':
        fieldProps.rows = field.rows || 3;
        fieldProps.maxLength = field.maxLength;
        break;
      case 'text':
      default:
        fieldProps.maxLength = field.maxLength;
        fieldProps.minLength = field.minLength;
        fieldProps.pattern = field.pattern;
        break;
    }

    // Apply column span
    const style = {};
    if (field.colSpan) {
      style.gridColumn = `span ${field.colSpan}`;
    }

    return (
      <div key={field.name} className="core-form-builder__field" style={style}>
        <FieldComponent {...fieldProps} />
      </div>
    );
  }, [form, dynamicOptions, loadingOptions, isFieldVisible]);

  /**
   * Render a section
   */
  const renderSection = useCallback((section, index) => {
    const visibleFields = section.fields?.filter(isFieldVisible) || [];
    if (visibleFields.length === 0) return null;

    const gridColumns = section.columns || 1;
    const gridStyle = {
      display: 'grid',
      gridTemplateColumns: `repeat(${gridColumns}, 1fr)`,
      gap: '1rem',
    };

    return (
      <div key={section.title || index} className="core-form-builder__section">
        {section.title && (
          <h3 className="core-form-builder__section-title">{section.title}</h3>
        )}
        <div className="core-form-builder__fields" style={gridStyle}>
          {section.fields?.map(renderField)}
        </div>
      </div>
    );
  }, [renderField, isFieldVisible]);

  return (
    <form
      className={`core-form-builder ${className}`}
      onSubmit={handleSubmit}
      noValidate
    >
      {/* Error message */}
      {form.submitError && (
        <div className="core-form-builder__error">
          {form.submitError}
        </div>
      )}

      {/* Sections */}
      <div className="core-form-builder__sections">
        {sections.map(renderSection)}
      </div>

      {/* Actions */}
      <div className="core-form-builder__actions">
        <button
          type="submit"
          className="core-form-builder__submit"
          disabled={form.isSubmitting}
        >
          {form.isSubmitting ? 'Salvataggio...' : submitLabel}
        </button>
        {showCancel && onCancel && (
          <button
            type="button"
            className="core-form-builder__cancel"
            onClick={onCancel}
            disabled={form.isSubmitting}
          >
            {cancelLabel}
          </button>
        )}
      </div>
    </form>
  );
}

export default FormBuilder;
