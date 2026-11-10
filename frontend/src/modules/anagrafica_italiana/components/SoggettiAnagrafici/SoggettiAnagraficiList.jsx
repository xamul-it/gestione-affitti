import { useNavigate } from 'react-router-dom';
import SoggettiTable from './SoggettiTable';

function SoggettiAnagraficiList() {
  const navigate = useNavigate();
  return (
    <SoggettiTable
      title="Anagrafiche"
      showFiltroRuolo
      onAdd={() => navigate('/anagrafiche/nuovo')}
      onView={(row) => navigate(`/anagrafiche/${row.id}`)}
      onEdit={(row) => navigate(`/anagrafiche/${row.id}/modifica`)}
    />
  );
}

export default SoggettiAnagraficiList;
