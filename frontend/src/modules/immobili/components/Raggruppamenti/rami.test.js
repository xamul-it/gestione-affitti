import { describe, it, expect } from 'vitest';
import { opzioniRami } from './rami';

const albero = [
  { id: 1, nome: 'Complesso', figli: [
    { id: 2, nome: 'Edificio A', figli: [{ id: 3, nome: 'Cantine', figli: [] }] },
    { id: 4, nome: 'Edificio B', figli: [] },
  ] },
  { id: 5, nome: 'Fondo', figli: [] },
];

describe('opzioniRami', () => {
  it('flattens the tree with the full path, ordered as the tree', () => {
    expect(opzioniRami(albero)).toEqual([
      { id: 1, percorso: 'Complesso' },
      { id: 2, percorso: 'Complesso › Edificio A' },
      { id: 3, percorso: 'Complesso › Edificio A › Cantine' },
      { id: 4, percorso: 'Complesso › Edificio B' },
      { id: 5, percorso: 'Fondo' },
    ]);
  });
  it('leaves out a ramo and everything below it', () => {
    expect(opzioniRami(albero, 2).map((o) => o.id)).toEqual([1, 4, 5]);
  });
});
