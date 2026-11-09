export const DEFAULT_PROMEMORIA_GIORNI = 90;

export function formatDate(iso) {
  if (!iso) return '';
  const [y, m, d] = iso.slice(0, 10).split('-');
  return `${d}/${m}/${y}`;
}

export function todayIso() {
  const d = new Date();
  const pad = (n) => String(n).padStart(2, '0');
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
}

export function addMonthsIso(iso, months) {
  if (!iso) return null;
  const [y, m, d] = iso.split('-').map(Number);
  const target = new Date(Date.UTC(y, m - 1 + months, 1));
  const lastDay = new Date(Date.UTC(target.getUTCFullYear(), target.getUTCMonth() + 1, 0)).getUTCDate();
  target.setUTCDate(Math.min(d, lastDay));
  return target.toISOString().slice(0, 10);
}

function daysUntil(iso) {
  const [y, m, d] = iso.slice(0, 10).split('-').map(Number);
  const now = new Date();
  const today = Date.UTC(now.getFullYear(), now.getMonth(), now.getDate());
  return Math.round((Date.UTC(y, m - 1, d) - today) / 86400000);
}

/** Badge for a document's effective scadenza: { label, variant } or null. */
export function statoScadenza(documento, tipo) {
  const scadenza = documento?.data_scadenza_effettiva;
  if (!scadenza) return null;
  const giorni = daysUntil(scadenza);
  const soglia = Math.max(...(tipo?.promemoria_giorni?.length ? tipo.promemoria_giorni : [DEFAULT_PROMEMORIA_GIORNI]));
  if (giorni < 0) return { label: 'Scaduto', variant: 'danger' };
  if (giorni <= soglia) return { label: 'In scadenza', variant: 'warning' };
  return { label: 'Valido', variant: 'success' };
}

export function fileSize(bytes) {
  if (!bytes && bytes !== 0) return '';
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`;
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
}
