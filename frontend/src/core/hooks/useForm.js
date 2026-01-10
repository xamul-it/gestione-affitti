/**
 * useForm - Form state management hook
 *
 * Provides form state, validation, and submission handling.
 *
 * @example
 * const { values, errors, handleChange, handleSubmit, isValid } = useForm(
 *   { nome: '', email: '' },
 *   { nome: { required: true }, email: { required: true, email: true } }
 * );
 */

import { useState, useCallback, useMemo, useRef, useEffect } from 'react';
import { fromConfig } from '../utils/validators';

/**
 * Get initial values from entity or defaults
 */
function getInitialValues(fields, entity) {
  const values = {};

  // If we have an entity, use its values
  if (entity) {
    return { ...entity };
  }

  // Otherwise, use field defaults
  if (Array.isArray(fields)) {
    fields.forEach(field => {
      values[field.name] = field.defaultValue ?? '';
    });
  } else if (typeof fields === 'object') {
    Object.keys(fields).forEach(key => {
      values[key] = fields[key].defaultValue ?? '';
    });
  }

  return values;
}

/**
 * Create validators from field config
 */
function createValidators(fields) {
  const validators = {};

  if (Array.isArray(fields)) {
    fields.forEach(field => {
      if (field.validation || field.required) {
        validators[field.name] = fromConfig({
          required: field.required,
          ...field.validation,
        });
      }
    });
  } else if (typeof fields === 'object') {
    Object.keys(fields).forEach(key => {
      const field = fields[key];
      if (field.validation || field.required) {
        validators[key] = fromConfig({
          required: field.required,
          ...field.validation,
        });
      }
    });
  }

  return validators;
}

/**
 * useForm hook
 *
 * @param {Object|Array} fieldsOrInitialValues - Field configurations or initial values
 * @param {Object} validationRules - Validation rules (optional if using field configs)
 * @param {Object} options - Additional options
 * @returns {Object} Form state and handlers
 */
export function useForm(fieldsOrInitialValues = {}, validationRules = {}, options = {}) {
  const {
    entity = null,
    validateOnChange = true,
    validateOnBlur = true,
    resetOnSubmit = false,
  } = options;

  // Determine if we received field configs or initial values
  const isFieldConfig = Array.isArray(fieldsOrInitialValues) ||
    (typeof fieldsOrInitialValues === 'object' &&
      Object.values(fieldsOrInitialValues).some(v => v && typeof v === 'object' && 'name' in v));

  // Compute initial values and validators
  const initialValues = useMemo(() =>
    isFieldConfig ? getInitialValues(fieldsOrInitialValues, entity) : { ...fieldsOrInitialValues, ...entity }
  , [isFieldConfig, fieldsOrInitialValues, entity]);

  const validators = useMemo(() =>
    isFieldConfig ? { ...createValidators(fieldsOrInitialValues), ...validationRules } : validationRules
  , [isFieldConfig, fieldsOrInitialValues, validationRules]);

  // State
  const [values, setValues] = useState(initialValues);
  const [errors, setErrors] = useState({});
  const [touched, setTouched] = useState({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitCount, setSubmitCount] = useState(0);
  const [submitError, setSubmitError] = useState(null);

  // Refs
  const initialValuesRef = useRef(initialValues);
  const validatorsRef = useRef(validators);

  // Update refs when props change
  useEffect(() => {
    validatorsRef.current = validators;
  }, [validators]);

  // Reset form when entity changes
  useEffect(() => {
    if (entity) {
      const newValues = isFieldConfig
        ? getInitialValues(fieldsOrInitialValues, entity)
        : { ...fieldsOrInitialValues, ...entity };
      setValues(newValues);
      initialValuesRef.current = newValues;
      setErrors({});
      setTouched({});
    }
  }, [entity, isFieldConfig, fieldsOrInitialValues]);

  /**
   * Validate a single field
   */
  const validateField = useCallback((name, value, allValues) => {
    const validator = validatorsRef.current[name];
    if (!validator) return null;

    return validator(value, allValues || values);
  }, [values]);

  /**
   * Validate all fields
   */
  const validateAll = useCallback((valuesToValidate) => {
    const vals = valuesToValidate || values;
    const newErrors = {};
    let isValid = true;

    Object.keys(validatorsRef.current).forEach(name => {
      const error = validatorsRef.current[name](vals[name], vals);
      if (error) {
        newErrors[name] = error;
        isValid = false;
      }
    });

    setErrors(newErrors);
    return isValid;
  }, [values]);

  /**
   * Handle field change
   */
  const handleChange = useCallback((eventOrName, valueArg) => {
    let name, value;

    // Support both event and direct value
    if (eventOrName && eventOrName.target) {
      const target = eventOrName.target;
      name = target.name;
      value = target.type === 'checkbox' ? target.checked : target.value;
    } else {
      name = eventOrName;
      value = valueArg;
    }

    setValues(prev => {
      const newValues = { ...prev, [name]: value };

      // Validate on change if enabled
      if (validateOnChange) {
        const error = validateField(name, value, newValues);
        setErrors(prevErrors => {
          if (error) {
            return { ...prevErrors, [name]: error };
          }
          const { [name]: _, ...rest } = prevErrors;
          return rest;
        });
      }

      return newValues;
    });
  }, [validateOnChange, validateField]);

  /**
   * Handle field blur
   */
  const handleBlur = useCallback((eventOrName) => {
    const name = typeof eventOrName === 'string' ? eventOrName : eventOrName?.target?.name;
    if (!name) return;

    setTouched(prev => ({ ...prev, [name]: true }));

    // Validate on blur if enabled
    if (validateOnBlur) {
      const error = validateField(name, values[name]);
      setErrors(prev => {
        if (error) {
          return { ...prev, [name]: error };
        }
        const { [name]: _, ...rest } = prev;
        return rest;
      });
    }
  }, [validateOnBlur, validateField, values]);

  /**
   * Set field value programmatically
   */
  const setFieldValue = useCallback((name, value, shouldValidate = validateOnChange) => {
    setValues(prev => {
      const newValues = { ...prev, [name]: value };

      if (shouldValidate) {
        const error = validateField(name, value, newValues);
        setErrors(prevErrors => {
          if (error) {
            return { ...prevErrors, [name]: error };
          }
          const { [name]: _, ...rest } = prevErrors;
          return rest;
        });
      }

      return newValues;
    });
  }, [validateOnChange, validateField]);

  /**
   * Set field error programmatically
   */
  const setFieldError = useCallback((name, error) => {
    setErrors(prev => {
      if (error) {
        return { ...prev, [name]: error };
      }
      const { [name]: _, ...rest } = prev;
      return rest;
    });
  }, []);

  /**
   * Set multiple values at once
   */
  const setFieldValues = useCallback((newValues, shouldValidate = false) => {
    setValues(prev => ({ ...prev, ...newValues }));
    if (shouldValidate) {
      validateAll({ ...values, ...newValues });
    }
  }, [values, validateAll]);

  /**
   * Handle form submission
   */
  const handleSubmit = useCallback((onSubmit) => async (event) => {
    if (event) {
      event.preventDefault();
    }

    setSubmitCount(prev => prev + 1);
    setSubmitError(null);

    // Mark all fields as touched
    const allTouched = {};
    Object.keys(values).forEach(key => {
      allTouched[key] = true;
    });
    setTouched(allTouched);

    // Validate all fields
    const isValid = validateAll();
    if (!isValid) {
      return;
    }

    setIsSubmitting(true);

    try {
      await onSubmit(values);

      if (resetOnSubmit) {
        setValues(initialValuesRef.current);
        setTouched({});
        setErrors({});
      }
    } catch (err) {
      const errorMessage = err.response?.data?.detail || err.message || 'Errore durante il salvataggio';
      setSubmitError(errorMessage);
      throw err;
    } finally {
      setIsSubmitting(false);
    }
  }, [values, validateAll, resetOnSubmit]);

  /**
   * Reset form to initial values
   */
  const reset = useCallback((newInitialValues) => {
    const vals = newInitialValues || initialValuesRef.current;
    setValues(vals);
    setErrors({});
    setTouched({});
    setSubmitCount(0);
    setSubmitError(null);
    if (newInitialValues) {
      initialValuesRef.current = newInitialValues;
    }
  }, []);

  /**
   * Check if form is dirty (has changes)
   */
  const isDirty = useMemo(() => {
    return JSON.stringify(values) !== JSON.stringify(initialValuesRef.current);
  }, [values]);

  /**
   * Check if form is valid
   */
  const isValid = useMemo(() => {
    return Object.keys(errors).length === 0;
  }, [errors]);

  /**
   * Get field props helper
   */
  const getFieldProps = useCallback((name) => ({
    name,
    value: values[name] ?? '',
    onChange: handleChange,
    onBlur: handleBlur,
  }), [values, handleChange, handleBlur]);

  /**
   * Get field meta helper
   */
  const getFieldMeta = useCallback((name) => ({
    touched: !!touched[name],
    error: errors[name] || null,
    hasError: !!errors[name],
    isValid: !errors[name],
  }), [touched, errors]);

  return {
    // State
    values,
    errors,
    touched,
    isDirty,
    isValid,
    isSubmitting,
    submitCount,
    submitError,

    // Handlers
    handleChange,
    handleBlur,
    handleSubmit,

    // Setters
    setFieldValue,
    setFieldError,
    setFieldValues,
    setValues,
    setErrors,

    // Utilities
    reset,
    validateAll,
    validateField,
    getFieldProps,
    getFieldMeta,
  };
}

export default useForm;
