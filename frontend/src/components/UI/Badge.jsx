import './Badge.css';

export default function Badge({ variant = 'neutral', children, className = '' }) {
  const classes = ['ds-badge', `ds-badge--${variant}`, className].filter(Boolean).join(' ');
  return <span className={classes}>{children}</span>;
}
