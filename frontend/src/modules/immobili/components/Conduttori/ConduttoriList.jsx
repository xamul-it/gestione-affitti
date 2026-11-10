import RuoloSoggettiPage from '../Soggetti/RuoloSoggettiPage';
import ConduttoreForm from './ConduttoreForm';
import { conduttoriAPI } from '../../services/immobiliAPI';
import './Conduttori.css';

const TESTI = {
  azione: 'Togli dai conduttori',
  fatto: 'Tolto dai conduttori',
  vuoto: 'Nessun conduttore registrato. Clicca su "Nuovo Conduttore" per iniziare.',
  conferma: (nome) => `Togliere ${nome} dai conduttori? Verranno rimosse anche le sue assegnazioni. L'anagrafica resta.`,
};

function ConduttoriList() {
  return (
    <RuoloSoggettiPage
      ruolo="conduttore"
      title="Conduttori"
      colonnaOggetti="Unità occupate"
      recordsAPI={conduttoriAPI}
      noteField="note"
      FormComponent={ConduttoreForm}
      formProp="conduttore"
      addButtonLabel="Nuovo Conduttore"
      testi={TESTI}
    />
  );
}

export default ConduttoriList;
