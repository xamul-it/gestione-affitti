import { describe, it, expect } from 'vitest';
import { haAreCa } from './superficie';

describe('haAreCa', () => {
  it('splits square metres into hectares, ares and centiares', () => {
    expect(haAreCa(91896)).toBe('9 ha 18 a 96 ca');
    expect(haAreCa(536)).toBe('5 a 36 ca');
    expect(haAreCa(27)).toBe('27 ca');
  });

  it('shows zero as centiares and keeps inner zeros out', () => {
    expect(haAreCa(0)).toBe('0 ca');
    expect(haAreCa(10000)).toBe('1 ha');
    expect(haAreCa(10027)).toBe('1 ha 27 ca');
  });

  it('returns a dash for missing values', () => {
    expect(haAreCa(null)).toBe('-');
    expect(haAreCa(undefined)).toBe('-');
  });
});
