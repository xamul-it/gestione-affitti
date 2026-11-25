"""Pure parts of scripts/tenant_prova.py: lost rows and known schema differences."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "scripts"))
import tenant_prova as tp  # noqa: E402

pytestmark = pytest.mark.unit


def test_perdite_righe_e_tabelle():
    prima = {"a": 3, "b": 2, "c": 5}
    dopo = {"a": 3, "b": 1, "d": 0}
    assert tp.perdite(prima, dopo) == ["b: 2 -> 1 righe", "c: tabella sparita (5 righe)"]


def test_nessuna_perdita_se_crescono_o_restano():
    assert tp.perdite({"a": 3}, {"a": 4, "nuova": 0}) == []


def test_solo_differenze_nuove_bloccano():
    nota = next(iter(tp.DIFFERENZE_NOTE))
    assert tp.stampa_differenze([nota]) is True
    assert tp.stampa_differenze([nota, ("x", "colonna mancante", "y")]) is False


def test_rifiuta_schema_non_di_prova():
    for schema in ("tenant_produzione", "tenant_qa_test", "public", "tenant_test_x; DROP"):
        with pytest.raises(SystemExit):
            tp._controlla_nome(schema)
    tp._controlla_nome("tenant_test_nuovo")


def test_non_idempotenti():
    assert tp.non_idempotenti({"a": 2, "b": 1}, {"a": 2, "b": 3, "c": 1}) == ["b: 1 -> 3", "c: 0 -> 1"]


def test_rifiuta_il_db_di_produzione():
    for url in ("postgresql://u:p@localhost:5433/gestione_affitti_prod",
                "postgresql+psycopg2://u@h/gestione_affitti_prod?sslmode=disable"):
        with pytest.raises(SystemExit):
            tp.controlla_db(url)
    tp.controlla_db("postgresql://u:p@localhost:5433/gestione_affitti")


def test_spia_tabelle_create_dai_modelli():
    from app.core.services.tenant_module_service import TenantModuleService
    originale = TenantModuleService._create_module_tables_from_metadata
    TenantModuleService._create_module_tables_from_metadata = staticmethod(lambda *a, **k: ["t1"])
    try:
        with tp.spia_fallback() as create:
            TenantModuleService._create_module_tables_from_metadata("mod", None, "s", None)
        assert create == ["mod: t1"]
        assert TenantModuleService._create_module_tables_from_metadata("x", None, "s", None) == ["t1"]
    finally:
        TenantModuleService._create_module_tables_from_metadata = originale


def test_tabella_vuota_sparita_non_e_una_perdita():
    """A rename or drop of an empty table loses no data: reported, not blocking."""
    assert tp.perdite({"vecchia": 0, "a": 1}, {"a": 1}) == []
    assert tp.tabelle_vuote_sparite({"vecchia": 0, "a": 1}, {"a": 1}) == ["vecchia"]
