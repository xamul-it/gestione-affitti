import RuoloSoggettiPage from '../Soggetti/RuoloSoggettiPage';

/** Holders of rights in rem (owners, usufructuaries, bare owners, surface right holders…). */
function ProprietariList() {
  return (
    <RuoloSoggettiPage
      famiglia="diritti_reali"
      title="Titolari di diritti"
      colonnaTipo="Diritto"
      conQuota
      vuoto="Nessun titolare di diritti registrato"
    />
  );
}

export default ProprietariList;
