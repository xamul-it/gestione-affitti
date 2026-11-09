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


@pytest.fixture(scope="module")
def analitica():
    return parse_visura(_load("analitica.pdf"))


def test_analitica_header(analitica):
    assert analitica.formato == FormatoVisura.ANALITICA
    assert analitica.numero == "T233852/2025"
    assert analitica.data == date(2025, 12, 16)
    assert len(analitica.fabbricati) == 9
    assert analitica.terreni_count == 0


def _signature(visura):
    return {
        (f.foglio, f.particella, f.subalterno): (
            f.categoria, f.classe, f.rendita, f.indirizzo, f.piano,
            [(i.codice_fiscale, i.tipo_diritto, i.quota_percentuale) for i in f.intestati],
        )
        for f in visura.fabbricati
    }


def test_analitica_matches_sintetica(analitica, sintetica):
    assert _signature(analitica) == _signature(sintetica)


def test_analitica_unit_666_19(analitica):
    u = _unit(analitica, "99", "666", "19")
    assert u.zona_censuaria == "2"
    assert u.categoria == "A/3"
    assert u.consistenza == "10,0 vani"
    assert u.superficie_escluse_aree == Decimal("294")
    assert u.provincia == "BO"
    for value in vars(u).values():
        if isinstance(value, str):
            assert "FRAZIONAMENTO" not in value


# --- Visure per immobile (Milano) -------------------------------------------

@pytest.fixture(scope="module")
def immobile_tabellare():
    """Older tabular "Visura per immobile" (single unit, one intestato)."""
    return parse_visura(_load("immobile_tabellare.pdf"))


@pytest.fixture(scope="module")
def immobile_attuale():
    """"Visura attuale per immobile": descriptive two-column layout, two intestati."""
    return parse_visura(_load("immobile_attuale.pdf"))


def test_immobile_tabellare_header(immobile_tabellare):
    assert immobile_tabellare.formato == FormatoVisura.SINTETICA
    assert immobile_tabellare.numero == "T27278"
    assert immobile_tabellare.data == date(2021, 2, 21)
    assert immobile_tabellare.terreni_count == 0
    assert immobile_tabellare.warnings == []
    assert len(immobile_tabellare.fabbricati) == 1


def test_immobile_tabellare_unit(immobile_tabellare):
    u = _unit(immobile_tabellare, "481", "60", "21")
    assert u.comune == "MILANO"
    assert u.codice_catastale_comune == "F205"
    assert u.sezione_urbana is None
    assert u.zona_censuaria == "2"
    assert u.categoria == "A/3"
    assert u.classe == "4"
    assert u.consistenza == "6 vani"
    assert u.vani == Decimal("6")
    assert u.superficie_totale == Decimal("143")
    assert u.superficie_escluse_aree == Decimal("142")
    assert u.rendita == Decimal("821.17")
    assert u.indirizzo == "VIALE UMBRIA n. 49 interno 23"
    assert u.piano == "5-S1-7"
    assert len(u.intestati) == 1
    i = u.intestati[0]
    assert i.codice_fiscale == "ZNDLMT73E17F205F"
    assert i.cognome == "ZANDERIGHI"
    assert i.nome == "Luigi Matteo Massimiliano"
    assert i.data_nascita == date(1973, 5, 17)
    assert i.luogo_nascita == "MILANO"
    assert i.tipo_diritto == TipoDiritto.PROPRIETARIO
    assert i.quota_percentuale == Decimal("100.00")


def test_immobile_attuale_header(immobile_attuale):
    assert immobile_attuale.formato == FormatoVisura.ANALITICA
    assert immobile_attuale.numero == "T431866/2024"
    assert immobile_attuale.data == date(2024, 4, 4)
    assert immobile_attuale.warnings == []
    assert len(immobile_attuale.fabbricati) == 1


def test_immobile_attuale_unit(immobile_attuale):
    u = _unit(immobile_attuale, "393", "457", "716")
    assert u.comune == "MILANO"
    assert u.codice_catastale_comune == "F205"
    assert u.provincia == "MI"
    assert u.zona_censuaria == "2"
    assert u.categoria == "A/3"
    assert u.classe == "4"
    assert u.consistenza == "4 vani"
    assert u.superficie_totale == Decimal("64")
    assert u.superficie_escluse_aree == Decimal("64")
    assert u.rendita == Decimal("547.44")
    assert u.indirizzo == "VIA ARCHIMEDE n. 73A"
    assert u.piano == "T"
    cfs = sorted(i.codice_fiscale for i in u.intestati)
    assert cfs == ["BRSSFN72L45F205G", "ZNDLMT73E17F205F"]
    for i in u.intestati:
        assert i.tipo_diritto == TipoDiritto.COMPROPRIETARIO
        assert i.quota_percentuale == Decimal("50.00")


# --- Analitica per soggetto with bulleted identificativi ("• Foglio ...") -----

@pytest.fixture(scope="module")
def analitica_bullet():
    """Milano analitica per soggetto: the identificativi line starts with "• ",
    followed by "Particelle corrispondenti al catasto terreni" (no subalterno)."""
    return parse_visura(_load("analitica_milano_bullet.pdf"))


def test_analitica_bullet_keeps_subalterni(analitica_bullet):
    assert analitica_bullet.warnings == []
    idents = [(f.foglio, f.particella, f.subalterno) for f in analitica_bullet.fabbricati]
    assert len(idents) == 4
    assert all(sub for _, _, sub in idents), idents
    assert len(set(idents)) == 4
    assert ("483", "65", "54") in idents
    assert ("393", "457", "716") in idents


# --- Analitica with a long comune name: "(C310) (GR)" wraps to the next line --
# Layout as produced by pdftotext -layout on a real visura; people are fictitious.

_COMUNE_A_CAPO = """\
                                                                                  Data: 10/11/2026
Direzione Provinciale di Grosseto                                                 Ora: 00:06:01
Ufficio Provinciale - Territorio                                                  Numero Pratica: T999/2026
Servizi Catastali                                                                 Pag: 1 - Segue

                                Visura attuale per soggetto
                        Situazione degli atti informatizzati al 10/11/2026

Dati della richiesta
Terreni e Fabbricati siti in tutta la provincia di GROSSETO

          Soggetto richiesto:
          ROSSI Mario nato a MILANO (MI) il 01/01/1970 (CF: RSSMRA70A01F205X)
          Totali immobili: di catasto fabbricati 1

          Immobile di catasto fabbricati -                       Causali di aggiornamento ed annotazioni
          n.1

  Dati identificativi
  Comune di CASTIGLIONE DELLA PESCAIA                    VARIAZIONE DELLA DESTINAZIONE del 25/06/2013
  (C310) (GR)                                            Pratica n. GR0000001 in atti dal 25/06/2013 UFFICIO-
                                                         ABITAZIONE (n. 1.1/2013)
  Foglio 106 Particella 105 Subalterno 7

  Particelle corrispondenti al catasto terreni
  Comune di CASTIGLIONE DELLA PESCAIA
  (C310) (GR)
  Foglio 106 Particella 105

  Indirizzo
  VIA DEL MARE n. 5 Piano 2                              VARIAZIONE DELLA DESTINAZIONE del 25/06/2013

  Dati di classamento
  Rendita: Euro 650,74                                   VARIAZIONE NEL CLASSAMENTO del 23/04/2014
  Categoria A/2a), Classe 5, Consistenza 3,5 vani        Pratica n. GR0000002      in atti dal 23/04/2014

  Dati di superficie
  Totale: 79 m2                                        Superficie di impianto pubblicata il 09/11/2015
  Totale escluse aree scoperte b): 79 m2

  Intestazione attuale dell'immobile n. 1 - totale righe intestati: 1

  1. ROSSI Mario                                       1. Atto del 17/06/2022 Pubblico ufficiale
  (CF RSSMRA70A01F205X)
  nato a MILANO (MI) il 01/01/1970
  Diritto di: Proprieta' per 1/1

"""


def test_analitica_comune_wrapped_code():
    from immobili.services.visura.parser_analitica import parse_analitica
    visura = parse_analitica(_COMUNE_A_CAPO)
    assert visura.warnings == []
    [f] = visura.fabbricati
    assert (f.comune, f.codice_catastale_comune, f.provincia) == ("CASTIGLIONE DELLA PESCAIA", "C310", "GR")
    assert (f.foglio, f.particella, f.subalterno) == ("106", "105", "7")
    assert (f.indirizzo, f.piano) == ("VIA DEL MARE n. 5", "2")
    assert (f.categoria, f.classe, f.rendita) == ("A/2", "5", Decimal("650.74"))
