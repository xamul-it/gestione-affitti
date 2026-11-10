import RuoloSoggettiPage from '../Soggetti/RuoloSoggettiPage';
import ProprietarioForm from './ProprietarioForm';
import { proprietariAPI } from '../../services/immobiliAPI';
import './Proprietari.css';

const TESTI = {
  azione: 'Togli dai proprietari',
  fatto: 'Tolto dai proprietari',
  vuoto: 'Nessun proprietario registrato. Clicca su "Nuovo Proprietario" per iniziare.',
  conferma: (nome) => `Togliere ${nome} dai proprietari? Verranno rimossi anche i suoi diritti sulle unità immobiliari. L'anagrafica resta.`,
};

function ProprietariList() {
  return (
    <RuoloSoggettiPage
      ruolo="proprietario"
      title="Proprietari"
      colonnaOggetti="Immobili"
      recordsAPI={proprietariAPI}
      noteField="note_proprietario"
      FormComponent={ProprietarioForm}
      formProp="proprietario"
      addButtonLabel="Nuovo Proprietario"
      testi={TESTI}
    />
  );
}

export default ProprietariList;
