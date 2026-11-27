import { forwardRef } from 'react';
import './Button.css';

// forwardRef: callers can move the focus back to the button (e.g. after closing an inline panel).
const Button = forwardRef(function Button({
  variant = 'primary',
  size = 'md',
  disabled = false,
  loading = false,
  children,
  className = '',
  ...rest
}, ref) {
  const classes = ['ds-btn', `ds-btn--${variant}`, `ds-btn--${size}`, className]
    .filter(Boolean)
    .join(' ');

  return (
    <button ref={ref} className={classes} disabled={disabled || loading} {...rest}>
      {loading ? <span className="ds-btn__spinner" aria-hidden="true" /> : null}
      {children}
    </button>
  );
});

export default Button;
