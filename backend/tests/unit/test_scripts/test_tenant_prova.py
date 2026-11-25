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
