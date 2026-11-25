import RuoloSoggettiPage from '../Soggetti/RuoloSoggettiPage';

/** Enjoyment of the beni: tenants, borrowers (comodatari), other occupants. */
function ConduttoriList() {
  return (
    <RuoloSoggettiPage
      famiglia="godimento"
      title="Godimento"
      colonnaTipo="Tipo"
      vuoto="Nessun godimento registrato"
    />
  );
}

export default ConduttoriList;
