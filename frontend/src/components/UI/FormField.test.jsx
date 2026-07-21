import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import FormField from './FormField';

describe('FormField', () => {
  it('wires the label to its input via htmlFor/id', () => {
    render(
      <FormField label="Email" htmlFor="email">
        <input id="email" />
      </FormField>
    );
    expect(screen.getByLabelText('Email')).toBeInTheDocument();
  });

  it('renders an error message with role alert when provided', () => {
    render(
      <FormField label="Email" htmlFor="email" error="Campo obbligatorio">
        <input id="email" />
      </FormField>
    );
    expect(screen.getByRole('alert')).toHaveTextContent('Campo obbligatorio');
  });

  it('renders no alert when there is no error', () => {
    render(
      <FormField label="Email" htmlFor="email">
        <input id="email" />
      </FormField>
    );
    expect(screen.queryByRole('alert')).toBeNull();
  });
});
