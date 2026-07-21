import './Button.css';

export default function Button({
  variant = 'primary',
  size = 'md',
  disabled = false,
  loading = false,
  children,
  className = '',
  ...rest
}) {
  const classes = ['ds-btn', `ds-btn--${variant}`, `ds-btn--${size}`, className]
    .filter(Boolean)
    .join(' ');

  return (
    <button className={classes} disabled={disabled || loading} {...rest}>
      {loading ? <span className="ds-btn__spinner" aria-hidden="true" /> : null}
      {children}
    </button>
  );
}
