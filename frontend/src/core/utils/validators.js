/**
 * Core Validators - Validation functions for forms
 *
 * These validators are used by FormBuilder for field validation.
 * Each validator returns an error message string or null if valid.
 */

/**
 * Check if value is not empty
 * @param {*} value - Value to check
 * @param {string} message - Custom error message
 * @returns {string|null} Error message or null
 */
export function required(value, message = 'Questo campo e obbligatorio') {
  if (value === null || value === undefined) return message;
  if (typeof value === 'string' && value.trim() === '') return message;
  if (Array.isArray(value) && value.length === 0) return message;
  return null;
}

/**
 * Check minimum length
 * @param {number} min - Minimum length
 * @param {string} message - Custom error message
 * @returns {Function} Validator function
 */
export function minLength(min, message) {
  return (value) => {
    if (!value) return null; // Skip if empty (use required for that)
    const defaultMsg = `Deve contenere almeno ${min} caratteri`;
    if (String(value).length < min) return message || defaultMsg;
    return null;
  };
}

/**
 * Check maximum length
 * @param {number} max - Maximum length
 * @param {string} message - Custom error message
 * @returns {Function} Validator function
 */
export function maxLength(max, message) {
  return (value) => {
    if (!value) return null;
    const defaultMsg = `Deve contenere al massimo ${max} caratteri`;
    if (String(value).length > max) return message || defaultMsg;
    return null;
  };
}

/**
 * Check minimum value for numbers
 * @param {number} min - Minimum value
 * @param {string} message - Custom error message
 * @returns {Function} Validator function
 */
export function minValue(min, message) {
  return (value) => {
    if (value === null || value === undefined || value === '') return null;
    const numValue = Number(value);
    const defaultMsg = `Il valore minimo e ${min}`;
    if (isNaN(numValue) || numValue < min) return message || defaultMsg;
    return null;
  };
}

/**
 * Check maximum value for numbers
 * @param {number} max - Maximum value
 * @param {string} message - Custom error message
 * @returns {Function} Validator function
 */
export function maxValue(max, message) {
  return (value) => {
    if (value === null || value === undefined || value === '') return null;
    const numValue = Number(value);
    const defaultMsg = `Il valore massimo e ${max}`;
    if (isNaN(numValue) || numValue > max) return message || defaultMsg;
    return null;
  };
}

/**
 * Validate email format
 * @param {string} message - Custom error message
 * @returns {Function} Validator function
 */
export function email(message = 'Inserire un indirizzo email valido') {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return (value) => {
    if (!value) return null;
    if (!emailRegex.test(value)) return message;
    return null;
  };
}

/**
 * Validate phone number format
 * @param {string} message - Custom error message
 * @returns {Function} Validator function
 */
export function phone(message = 'Inserire un numero di telefono valido') {
  // Accept various phone formats
  const phoneRegex = /^[\d\s\-+()]{6,20}$/;
  return (value) => {
    if (!value) return null;
    if (!phoneRegex.test(value)) return message;
    return null;
  };
}

/**
 * Validate Italian codice fiscale
 * @param {string} message - Custom error message
 * @returns {Function} Validator function
 */
export function codiceFiscale(message = 'Codice fiscale non valido') {
  const cfRegex = /^[A-Z]{6}\d{2}[A-EHLMPR-T]\d{2}[A-Z]\d{3}[A-Z]$/i;
  return (value) => {
    if (!value) return null;
    const cleaned = value.toUpperCase().replace(/\s/g, '');
    if (cleaned.length !== 16) return message;
    if (!cfRegex.test(cleaned)) return message;
    return null;
  };
}

/**
 * Validate Italian partita IVA
 * @param {string} message - Custom error message
 * @returns {Function} Validator function
 */
export function partitaIva(message = 'Partita IVA non valida') {
  return (value) => {
    if (!value) return null;
    const cleaned = value.replace(/\s/g, '');
    if (!/^\d{11}$/.test(cleaned)) return message;

    // Luhn algorithm check for Italian VAT
    let sum = 0;
    for (let i = 0; i < 11; i++) {
      let digit = parseInt(cleaned[i], 10);
      if (i % 2 === 1) {
        digit *= 2;
        if (digit > 9) digit -= 9;
      }
      sum += digit;
    }
    if (sum % 10 !== 0) return message;

    return null;
  };
}

/**
 * Validate against a regex pattern
 * @param {RegExp} pattern - Regex pattern
 * @param {string} message - Custom error message
 * @returns {Function} Validator function
 */
export function pattern(patternRegex, message = 'Formato non valido') {
  return (value) => {
    if (!value) return null;
    if (!patternRegex.test(value)) return message;
    return null;
  };
}

/**
 * Validate date is not in the past
 * @param {string} message - Custom error message
 * @returns {Function} Validator function
 */
export function futureDate(message = 'La data deve essere futura') {
  return (value) => {
    if (!value) return null;
    const date = new Date(value);
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    if (date < today) return message;
    return null;
  };
}

/**
 * Validate date is not in the future
 * @param {string} message - Custom error message
 * @returns {Function} Validator function
 */
export function pastDate(message = 'La data deve essere passata') {
  return (value) => {
    if (!value) return null;
    const date = new Date(value);
    const today = new Date();
    today.setHours(23, 59, 59, 999);
    if (date > today) return message;
    return null;
  };
}

/**
 * Validate date is after another date
 * @param {string} fieldName - Name of the field to compare
 * @param {string} fieldLabel - Label of the field for error message
 * @param {string} message - Custom error message
 * @returns {Function} Validator function
 */
export function afterDate(fieldName, fieldLabel, message) {
  return (value, formData) => {
    if (!value || !formData[fieldName]) return null;
    const date = new Date(value);
    const compareDate = new Date(formData[fieldName]);
    const defaultMsg = `La data deve essere successiva a ${fieldLabel}`;
    if (date <= compareDate) return message || defaultMsg;
    return null;
  };
}

/**
 * Validate date is before another date
 * @param {string} fieldName - Name of the field to compare
 * @param {string} fieldLabel - Label of the field for error message
 * @param {string} message - Custom error message
 * @returns {Function} Validator function
 */
export function beforeDate(fieldName, fieldLabel, message) {
  return (value, formData) => {
    if (!value || !formData[fieldName]) return null;
    const date = new Date(value);
    const compareDate = new Date(formData[fieldName]);
    const defaultMsg = `La data deve essere precedente a ${fieldLabel}`;
    if (date >= compareDate) return message || defaultMsg;
    return null;
  };
}

/**
 * Validate Italian CAP (postal code)
 * @param {string} message - Custom error message
 * @returns {Function} Validator function
 */
export function cap(message = 'CAP non valido (5 cifre)') {
  return (value) => {
    if (!value) return null;
    if (!/^\d{5}$/.test(value)) return message;
    return null;
  };
}

/**
 * Validate Italian provincia code (2 letters)
 * @param {string} message - Custom error message
 * @returns {Function} Validator function
 */
export function provincia(message = 'Provincia non valida (2 lettere)') {
  return (value) => {
    if (!value) return null;
    if (!/^[A-Z]{2}$/i.test(value)) return message;
    return null;
  };
}

/**
 * Validate URL format
 * @param {string} message - Custom error message
 * @returns {Function} Validator function
 */
export function url(message = 'URL non valido') {
  return (value) => {
    if (!value) return null;
    try {
      new URL(value);
      return null;
    } catch {
      return message;
    }
  };
}

/**
 * Validate that value matches another field
 * @param {string} fieldName - Name of the field to match
 * @param {string} fieldLabel - Label for error message
 * @param {string} message - Custom error message
 * @returns {Function} Validator function
 */
export function matches(fieldName, fieldLabel, message) {
  return (value, formData) => {
    if (!value) return null;
    const defaultMsg = `I valori non corrispondono a ${fieldLabel}`;
    if (value !== formData[fieldName]) return message || defaultMsg;
    return null;
  };
}

/**
 * Custom validator function
 * @param {Function} validateFn - Validation function (value, formData) => string|null
 * @returns {Function} Validator function
 */
export function custom(validateFn) {
  return (value, formData) => validateFn(value, formData);
}

/**
 * Compose multiple validators
 * @param  {...Function} validators - Validator functions
 * @returns {Function} Combined validator function
 */
export function compose(...validators) {
  return (value, formData) => {
    for (const validator of validators) {
      const error = validator(value, formData);
      if (error) return error;
    }
    return null;
  };
}

/**
 * Create validators from a config object
 * @param {Object} config - Validation configuration
 * @returns {Function} Composed validator function
 */
export function fromConfig(config) {
  const validators = [];

  if (config.required) {
    validators.push(required);
  }
  if (config.minLength) {
    validators.push(minLength(config.minLength));
  }
  if (config.maxLength) {
    validators.push(maxLength(config.maxLength));
  }
  if (config.min !== undefined) {
    validators.push(minValue(config.min));
  }
  if (config.max !== undefined) {
    validators.push(maxValue(config.max));
  }
  if (config.email) {
    validators.push(email());
  }
  if (config.phone) {
    validators.push(phone());
  }
  if (config.codiceFiscale) {
    validators.push(codiceFiscale());
  }
  if (config.partitaIva) {
    validators.push(partitaIva());
  }
  if (config.cap) {
    validators.push(cap());
  }
  if (config.provincia) {
    validators.push(provincia());
  }
  if (config.url) {
    validators.push(url());
  }
  if (config.pattern) {
    validators.push(pattern(config.pattern, config.patternMessage));
  }
  if (config.custom) {
    validators.push(custom(config.custom));
  }

  return validators.length > 0 ? compose(...validators) : () => null;
}

export default {
  required,
  minLength,
  maxLength,
  minValue,
  maxValue,
  email,
  phone,
  codiceFiscale,
  partitaIva,
  pattern,
  futureDate,
  pastDate,
  afterDate,
  beforeDate,
  cap,
  provincia,
  url,
  matches,
  custom,
  compose,
  fromConfig,
};
