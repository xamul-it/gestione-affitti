/**
 * Core Components - Main export file
 *
 * This file re-exports all core components for easy importing.
 *
 * @example
 * import { DataTable, FormBuilder, FormModal, Badge } from '@/core/components';
 */

// DataTable
export { DataTable } from './DataTable';

// FormBuilder
export { FormBuilder, FormModal } from './FormBuilder';
export * from './FormBuilder/fields';

// Common components
export * from './common';

// Re-export hooks for convenience
export { useEntityCRUD, useForm, useDataTable } from '../hooks';

// Re-export utils for convenience
export { formatters, validators } from '../utils';
