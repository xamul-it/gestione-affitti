import { describe, it, expect } from 'vitest';
import { opzioniCollegamento } from './opzioniCollegamento';

const unita = (codice) => ({ tipo_bene: 'UNITA', categoria_catastale: codice ? { codice } : null });
const chiavi = (bene) => opzioniCollegamento(bene).map((o) => `${o.tipo}/${o.questo_e}/${o.tipoAltro}`);

describe('opzioniCollegamento', () => {
  it('abitazione A/3: pertinenza e particella', () => {
    expect(chiavi(unita('A/3'))).toEqual(['PERTINENZA/PRINCIPALE/UNITA', 'FABBRICATO_SU_PARTICELLA/COLLEGATO/TERRENO']);
    expect(opzioniCollegamento(unita('A/3'))[0].etichetta).toBe('Aggiungi pertinenza');
  });
  it('ufficio A/10 e unità senza categoria: solo particella', () => {
    expect(chiavi(unita('A/10'))).toEqual(['FABBRICATO_SU_PARTICELLA/COLLEGATO/TERRENO']);
    expect(chiavi(unita(null))).toEqual(['FABBRICATO_SU_PARTICELLA/COLLEGATO/TERRENO']);
  });
  it('box C/6: è pertinenza di…', () => {
    expect(chiavi(unita('C/6'))).toEqual(['PERTINENZA/COLLEGATO/UNITA', 'FABBRICATO_SU_PARTICELLA/COLLEGATO/TERRENO']);
    expect(opzioniCollegamento(unita('C/6'))[0].etichetta).toBe('È pertinenza di…');
  });
  it('terreno: fabbricato e fondo nei due versi', () => {
    expect(chiavi({ tipo_bene: 'TERRENO' })).toEqual([
      'FABBRICATO_SU_PARTICELLA/PRINCIPALE/UNITA', 'PARTE_DI_FONDO/PRINCIPALE/TERRENO', 'PARTE_DI_FONDO/COLLEGATO/TERRENO',
    ]);
  });
});
