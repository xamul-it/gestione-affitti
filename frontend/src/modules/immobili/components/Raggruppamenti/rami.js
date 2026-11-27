// Helpers on the raggruppamenti tree returned by GET /raggruppamenti/?vista=albero.

export const TIPI_RAMO = [
  { codice: 'COMPLESSO', etichetta: 'Complesso' },
  { codice: 'EDIFICIO', etichetta: 'Edificio' },
  { codice: 'FONDO', etichetta: 'Fondo' },
  { codice: 'ALTRO', etichetta: 'Altro' },
];

export const etichettaTipo = (codice) => TIPI_RAMO.find((t) => t.codice === codice)?.etichetta || codice;

export const SEPARATORE = ' › ';

/**
 * Flat list of the rami as { id, percorso }, in tree order. With escludiId the ramo
 * and everything below it are left out (they cannot become its parent).
 */
export function opzioniRami(albero, escludiId = null) {
  const out = [];
  const visita = (nodi, prefisso) => {
    (nodi || []).forEach((n) => {
      if (n.id === escludiId) return;
      const percorso = prefisso ? `${prefisso}${SEPARATORE}${n.nome}` : n.nome;
      out.push({ id: n.id, percorso });
      visita(n.figli, percorso);
    });
  };
  visita(albero, '');
  return out;
}
