import './Card.css';

export default function Card({ children, className = '', ...rest }) {
  const classes = ['ds-card', className].filter(Boolean).join(' ');
  return (
    <div className={classes} {...rest}>
      {children}
    </div>
  );
}
