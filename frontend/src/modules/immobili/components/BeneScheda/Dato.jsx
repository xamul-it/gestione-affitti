export function Dato({ label, children }) {
  const vuoto = children === null || children === undefined || children === '';
  return (
    <div className="scheda-dato">
      <dt>{label}</dt>
      <dd>{vuoto ? '—' : children}</dd>
    </div>
  );
}
