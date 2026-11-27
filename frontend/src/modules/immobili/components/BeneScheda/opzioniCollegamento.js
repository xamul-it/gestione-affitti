// What can be linked from a bene's page. The server stays the authority:
// this list only avoids offering impossible choices.
const PERTINENZE = ['C/2', 'C/6', 'C/7'];

function categoria(bene) {
  return bene?.categoria_catastale?.codice || null;
}

export function opzioniCollegamento(bene) {
  if (!bene) return [];
  if (bene.tipo_bene === 'TERRENO') {
    return [
      // A farm is a FONDO raggruppamento, not a link.
      { tipo: 'FABBRICATO_SU_PARTICELLA', questo_e: 'PRINCIPALE', etichetta: 'Aggiungi fabbricato', tipoAltro: 'UNITA' },
    ];
  }
  const cat = categoria(bene);
  const opzioni = [];
  if (cat && cat.startsWith('A/') && cat !== 'A/10') {
    opzioni.push({ tipo: 'PERTINENZA', questo_e: 'PRINCIPALE', etichetta: 'Aggiungi pertinenza', tipoAltro: 'UNITA' });
  }
  if (PERTINENZE.includes(cat)) {
    opzioni.push({ tipo: 'PERTINENZA', questo_e: 'COLLEGATO', etichetta: 'È pertinenza di…', tipoAltro: 'UNITA' });
  }
  opzioni.push({ tipo: 'FABBRICATO_SU_PARTICELLA', questo_e: 'COLLEGATO', etichetta: 'Costruita sulla particella…', tipoAltro: 'TERRENO' });
  return opzioni;
}
