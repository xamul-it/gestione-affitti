"""RelationTypeDefinition: families, shares and parse_quota."""
import pytest

from app.core.platform_services.quote import parse_quota
from app.core.platform_services.relation_type_registry import RelationTypeDefinition

pytestmark = pytest.mark.unit


def test_definizione_famiglia_e_quota():
    d = RelationTypeDefinition(codice="x", nome="X", modulo="m", famiglia="godimento", ammette_quota=True)
    assert d.ammette_quota is True and d.famiglia == "godimento" and d.solo_beni is False
    base = RelationTypeDefinition(codice="x", nome="X", modulo="m")
    assert base.famiglia is None and base.ammette_quota is False


def test_famiglia_non_stringa():
    with pytest.raises(ValueError):
        RelationTypeDefinition(codice="x", nome="X", modulo="m", famiglia=3)


@pytest.mark.parametrize("campo", ["ammette_quota", "solo_beni"])
def test_flag_non_booleani(campo):
    with pytest.raises(ValueError):
        RelationTypeDefinition(codice="x", nome="X", modulo="m", **{campo: "si"})


def test_parse_quota():
    assert parse_quota("1/3") == (1, 3)
    assert parse_quota("1 / 2") == (1, 2)
    assert parse_quota("2/4") == (2, 4)
    assert parse_quota("3/3") == (3, 3)
    for bad in ("0/3", "4/3", "1/0", "50%", "metà", "", "1/2/3", "-1/2", "1.5/2"):
        with pytest.raises(ValueError):
            parse_quota(bad)
