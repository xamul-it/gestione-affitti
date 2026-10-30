"""
Unit tests for the catasto visura parser (immobili.services.visura).

Fixtures are real Agenzia delle Entrate PDFs (user-approved, see
docs/superpowers/specs/2026-10-30-import-visure-catastali-design.md).
"""
from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

from immobili.models.diritti_immobile import TipoDiritto
from immobili.services.visura import (
    FormatoVisura,
    VisuraFormatError,
    parse_diritto,
    parse_visura,
)

FIXTURES = Path(__file__).resolve().parents[3] / "fixtures" / "visure"


@pytest.fixture(autouse=True)
def override_get_db():
    """Shadow conftest.py's autouse override_get_db(db_session): pure parser tests need no DB."""
    yield


def _load(name: str) -> bytes:
    return (FIXTURES / name).read_bytes()


@pytest.fixture(scope="module")
def sintetica():
    return parse_visura(_load("sintetica.pdf"))


def _unit(visura, foglio, particella, sub):
    matches = [
        f for f in visura.fabbricati
        if (f.foglio, f.particella, f.subalterno) == (foglio, particella, sub)
    ]
    assert len(matches) == 1, f"expected one unit {foglio}/{particella}/{sub}, got {len(matches)}"
    return matches[0]


def test_detect_formato_riepilogo_imu_rejected():
    with pytest.raises(VisuraFormatError):
        parse_visura(_load("riepilogo_imu.pdf"))


def test_not_a_pdf_rejected():
    with pytest.raises(VisuraFormatError):
        parse_visura(b"not a pdf at all")


def test_sintetica_header(sintetica):
    assert sintetica.formato == FormatoVisura.SINTETICA
    assert sintetica.numero == "T234664/2025"
    assert sintetica.data == date(2025, 12, 16)
    assert sintetica.soggetto_cf == "ZNDLMT73E17F205F"
    assert len(sintetica.fabbricati) == 9
    assert sintetica.terreni_count == 0


def test_sintetica_unit_592_2(sintetica):
    u = _unit(sintetica, "99", "592", "2")
    assert u.codice_catastale_comune == "A944"
    assert u.comune == "BOLOGNA"
    assert u.categoria == "C/2"
    assert u.classe == "2"
    assert u.superficie_totale == Decimal("118")
    assert u.rendita == Decimal("548.58")
    assert u.indirizzo == "VIA EMILIA PONENTE n. 2"
    assert u.piano == "T"
    assert [
        (i.nominativo, i.codice_fiscale, i.persona_giuridica, i.tipo_diritto, i.quota_percentuale)
        for i in u.intestati
    ] == [
        ("DEMANIO DELLO STATO - RAMO FERROVIA", None, True, TipoDiritto.PROPRIETARIO, Decimal("100.00")),
        ("ZANDERIGHI Luigi Matteo Massimiliano", "ZNDLMT73E17F205F", False, TipoDiritto.USO, Decimal("100.00")),
    ]
    luigi = u.intestati[1]
    assert luigi.cognome == "ZANDERIGHI"
    assert luigi.nome == "Luigi Matteo Massimiliano"
    assert luigi.data_nascita == date(1973, 5, 17)
    assert luigi.luogo_nascita == "MILANO"
    assert luigi.diritto_testo == "Uso 1/1 in regime di separazione dei beni"
    demanio = u.intestati[0]
    assert demanio.ragione_sociale == "DEMANIO DELLO STATO - RAMO FERROVIA"
    assert demanio.cognome is None and demanio.nome is None


def test_sintetica_unit_666_9(sintetica):
    u = _unit(sintetica, "99", "666", "9")
    assert u.categoria == "A/3"
    assert u.classe == "1"
    assert u.vani == Decimal("4.5")
    assert u.superficie_escluse_aree == Decimal("80")
    assert u.rendita == Decimal("499.67")
    assert u.piano == "2-S1"
    assert u.indirizzo == "VIA EMILIA PONENTE n. 356"
    assert [i.tipo_diritto for i in u.intestati] == [TipoDiritto.USUFRUTTUARIO, TipoDiritto.NUDA_PROPRIETA]
    assert u.intestati[0].codice_fiscale == "ZNDLCN38R19F205K"


def test_sintetica_unit_666_19(sintetica):
    u = _unit(sintetica, "99", "666", "19")
    assert u.vani == Decimal("10.0")
    assert u.superficie_escluse_aree == Decimal("294")
    assert u.rendita == Decimal("1316.97")
    assert u.indirizzo == "VIA EMILIA PONENTE n. 354"
    assert u.piano == "S1-T - 1"


@pytest.mark.parametrize("testo,tipo,quota", [
    ("Proprieta' 1/1", TipoDiritto.PROPRIETARIO, Decimal("100.00")),
    ("Proprieta' 1/2", TipoDiritto.COMPROPRIETARIO, Decimal("50.00")),
    ("Nuda proprieta' 1/1", TipoDiritto.NUDA_PROPRIETA, Decimal("100.00")),
    ("Usufrutto 1/3", TipoDiritto.USUFRUTTUARIO, Decimal("33.33")),
    ("Uso 1/1 in regime di separazione dei beni", TipoDiritto.USO, Decimal("100.00")),
    ("Diritto del concedente 1/1", TipoDiritto.ALTRO, Decimal("100.00")),
])
def test_parse_diritto(testo, tipo, quota):
    assert parse_diritto(testo) == (tipo, quota)
