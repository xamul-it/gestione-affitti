/**
 * Form Fields - Re-export all field components
 */

export { TextField } from './TextField';
export { NumberField } from './NumberField';
export { SelectField } from './SelectField';
export { DateField } from './DateField';
export { TextareaField } from './TextareaField';
export { CheckboxField } from './CheckboxField';

// Field type mapping for dynamic rendering
export const fieldComponents = {
  text: 'TextField',
  email: 'TextField',
  tel: 'TextField',
  password: 'TextField',
  url: 'TextField',
  number: 'NumberField',
  select: 'SelectField',
  date: 'DateField',
  textarea: 'TextareaField',
  checkbox: 'CheckboxField',
};
