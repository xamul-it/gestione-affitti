"""
Generic import/export on a joined-inheritance model (UnitaImmobiliare is a
Bene): fields are the API names (citta, not the bene's comune) and never the
polymorphic discriminator.
"""
from unittest.mock import MagicMock

from app.core.platform_services.import_export_service import ImportExportService
from immobili.models import UnitaImmobiliare


def test_campi_unita_usano_citta_e_non_il_discriminatore():
    nomi = [f["name"] for f in ImportExportService(MagicMock()).get_entity_fields(UnitaImmobiliare)]
    assert "citta" in nomi and "indirizzo" in nomi and "codice" in nomi
    assert "comune" not in nomi
    assert "tipo_bene" not in nomi
    assert len(nomi) == len(set(nomi))


def test_modello_di_import_unita_ha_citta_con_esempio():
    csv = ImportExportService(MagicMock()).generate_import_template(UnitaImmobiliare, include_sample_data=True)
    intestazione, esempio = csv.splitlines()[:2]
    colonne = intestazione.split(",")
    assert "citta" in colonne and "tipo_bene" not in colonne and "comune" not in colonne
    assert esempio.split(",")[colonne.index("citta")] != ""
