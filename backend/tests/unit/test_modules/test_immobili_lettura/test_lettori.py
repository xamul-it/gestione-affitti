from immobili.services.lettura_documenti.lettori import LETTORI, MSG_RLI, normalizza, riconosci_tipo
from immobili.services.lettura_documenti.motore import applica

from .fixtures import APE_CON_CLASSE, APE_ER, PLANIMETRIA, RLI12, TESTO_QUALSIASI, VISURA_IMMOBILE


def _letti(testo):
    r = riconosci_tipo(testo)
    return r, normalizza(r.codice, r.campi)


def test_ape_formato_emilia_romagna():
    r, dati = _letti(APE_ER)
    assert r.codice == "APE"
    assert {
        "codice_comune": "L219", "foglio": "12", "particella": "345", "subalterno": "6",
        "comune": "TORINO", "indirizzo": "VIA PO n.3", "piano": "2",
        "ep_gl_nren": 111.24, "data_emissione": "2021-02-23", "valido_fino_al": "2031-02-23",
    }.items() <= dati.items()


def test_ape_classe_assente_se_grafica():
    _, dati = _letti(APE_ER)
    assert "classe" not in dati


def test_ape_classe_testuale():
    _, dati = _letti(APE_CON_CLASSE)
    assert dati["classe"] == "D"


def test_rli_scartato_con_messaggio():
    r = riconosci_tipo(RLI12)
    spec = next(s for s in LETTORI if s.codice == r.codice)
    assert spec.scarto == MSG_RLI
    assert MSG_RLI == "Ricevuta di registrazione del contratto: caricala dal contratto, nel modulo Affitti"


def test_visura_riconosciuta():
    assert riconosci_tipo(VISURA_IMMOBILE).codice == "VISURA_CATASTALE"


def test_planimetria_identificativi():
    r, dati = _letti(PLANIMETRIA)
    assert r.codice == "PLANIMETRIA_CATASTALE"
    assert {"comune": "TORINO", "foglio": "12", "particella": "345", "subalterno": "6"}.items() <= dati.items()


def test_testo_qualsiasi_nessun_tipo():
    assert riconosci_tipo(TESTO_QUALSIASI) is None


def test_ape_non_scambiato_per_visura_o_planimetria():
    for spec in LETTORI:
        if spec.codice != "APE":
            assert not applica(spec, APE_ER).riconosciuto, spec.codice
