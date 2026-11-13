/**
 * Surface of a land parcel as the cadastre writes it: hectares, ares and
 * centiares (1 ha = 100 a = 10 000 ca = 10 000 m²).
 *   haAreCa(91896) === '9 ha 18 a 96 ca'
 */
export function haAreCa(mq) {
  if (mq === null || mq === undefined || mq === '' || Number.isNaN(Number(mq))) return '-';
  const totale = Math.round(Number(mq));
  const ha = Math.floor(totale / 10000);
  const are = Math.floor((totale % 10000) / 100);
  const ca = totale % 100;
  const parti = [];
  if (ha) parti.push(`${ha} ha`);
  if (are) parti.push(`${are} a`);
  if (ca || parti.length === 0) parti.push(`${ca} ca`);
  return parti.join(' ');
}
