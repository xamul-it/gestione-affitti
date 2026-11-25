"""
Roles at a date and "who pays what" (services/ruoli_bene.py), pure logic on
in-memory rows. Spec: docs/superpowers/specs/2026-11-10-beni-catastali-design.md,
"Titolari, usufrutto e conduttore".
"""
from datetime import date, timedelta
from decimal import Decimal
from types import SimpleNamespace

import pytest

from immobili.services.ruoli_bene import ruoli_da_righe, voci_riepilogo

pytestmark = pytest.mark.unit

OGGI = date(2026, 11, 25)
_id = iter(range(1, 10_000))


def _soggetto(nome):
    return SimpleNamespace(id=next(_id), nome_completo=nome)


def _diritto(soggetto, tipo, quota=None, inizio=None, fine=None):
    return SimpleNamespace(
        tipo_diritto=tipo, quota_percentuale=None if quota is None else Decimal(quota),
        data_inizio=inizio, data_fine=fine,
        proprietario=SimpleNamespace(soggetto_id=soggetto.id, soggetto=soggetto),
    )


def _conduttore(soggetto, inizio=None, fine=None):
    return SimpleNamespace(
        data_inizio=inizio, data_fine=fine,
        conduttore=SimpleNamespace(soggetto_id=soggetto.id, soggetto=soggetto),
    )


def _voci(diritti, assegnazioni, tipo_bene, d=OGGI):
    ruoli = ruoli_da_righe(diritti, assegnazioni, d)
    return {v.codice: v for v in voci_riepilogo(ruoli, tipo_bene)}, ruoli


def _chi(voce):
    return [(s.nome, s.quota) for s in voce.soggetti]


def test_caso_forli():
    n, u, c = _soggetto("Nudo"), _soggetto("Usufrutto"), _soggetto("Conduttore")
    voci, ruoli = _voci(
        [_diritto(n, "NUDA_PROPRIETA", 100), _diritto(u, "USUFRUTTUARIO", 100)],
        [_conduttore(c, inizio=date(2020, 1, 1))], "TERRENO",
    )
    assert ruoli.usufrutto is True
    assert list(voci) == ["RENDITA", "REDDITO_AGRARIO", "IMU", "SPESE_ORDINARIE", "SPESE_STRAORDINARIE", "CANONE"]
    assert voci["RENDITA"].etichetta == "Reddito dominicale"
    assert _chi(voci["RENDITA"]) == [("Usufrutto", Decimal(100))]
    assert _chi(voci["REDDITO_AGRARIO"]) == [("Conduttore", Decimal(100))]
    assert _chi(voci["IMU"]) == [("Usufrutto", Decimal(100))]
    assert _chi(voci["SPESE_ORDINARIE"]) == [("Conduttore", Decimal(100))]
    assert _chi(voci["SPESE_STRAORDINARIE"]) == [("Nudo", Decimal(100))]
    assert _chi(voci["CANONE"]) == [("Usufrutto", Decimal(100))]
    assert voci["SPESE_STRAORDINARIE"].soggetti[0].ruolo == "NUDA_PROPRIETA"
    assert voci["SPESE_ORDINARIE"].soggetti[0].ruolo == "CONDUTTORE"
    assert voci["IMU"].norma == "L. 160/2019, c. 743"
    assert ruoli.avvisi == []


def test_piena_proprieta_due_comproprietari_senza_conduttore():
    p1, p2 = _soggetto("P1"), _soggetto("P2")
    voci, ruoli = _voci([_diritto(p1, "COMPROPRIETARIO", 50), _diritto(p2, "COMPROPRIETARIO", 50)], [], "UNITA")
    assert "REDDITO_AGRARIO" not in voci
    assert voci["RENDITA"].etichetta == "Rendita catastale"
    for voce in voci.values():
        assert _chi(voce) == [("P1", Decimal(50)), ("P2", Decimal(50))], voce.codice
    assert ruoli.usufrutto is False and ruoli.avvisi == []


def test_conduttore_che_e_titolare():
    p, c = _soggetto("Altro"), _soggetto("Conduce")
    voci, _ = _voci([_diritto(p, "COMPROPRIETARIO", 50), _diritto(c, "COMPROPRIETARIO", 50)],
                    [_conduttore(c)], "TERRENO")
    # Ruling 2026-11-25 (TUIR art. 33): the co-owner who farms the whole parcel
    # takes the agrarian income for his share and the rented one.
    assert _chi(voci["REDDITO_AGRARIO"]) == [("Conduce", Decimal(100))]
    assert _chi(voci["SPESE_ORDINARIE"]) == [("Conduce", Decimal(100))]


def test_diritto_scaduto_non_conta():
    vecchio, nuovo = _soggetto("Vecchio"), _soggetto("Nuovo")
    ieri = (OGGI - timedelta(days=1)).isoformat()
    diritti = [_diritto(vecchio, "PROPRIETARIO", 100, fine=ieri),
               _diritto(nuovo, "PROPRIETARIO", 100, inizio=OGGI.isoformat())]
    voci, _ = _voci(diritti, [], "UNITA")
    assert _chi(voci["IMU"]) == [("Nuovo", Decimal(100))]
    voci, _ = _voci(diritti, [], "UNITA", d=OGGI - timedelta(days=2))
    assert _chi(voci["IMU"]) == [("Vecchio", Decimal(100))]


def test_conduttore_finito_non_conta():
    p, c = _soggetto("P"), _soggetto("C")
    voci, _ = _voci([_diritto(p, "PROPRIETARIO")], [_conduttore(c, fine=OGGI - timedelta(days=1))], "UNITA")
    assert _chi(voci["SPESE_ORDINARIE"]) == [("P", Decimal(100))]


def test_quote_mancanti_e_somma():
    p1, p2 = _soggetto("P1"), _soggetto("P2")
    voci, ruoli = _voci([_diritto(p1, "COMPROPRIETARIO"), _diritto(p2, "COMPROPRIETARIO")], [], "UNITA")
    assert _chi(voci["IMU"]) == [("P1", None), ("P2", None)]
    assert ruoli.avvisi == ["Quote mancanti per titolari del godimento"]
    _, ruoli = _voci([_diritto(p1, "COMPROPRIETARIO", 50), _diritto(p2, "COMPROPRIETARIO", 40)], [], "UNITA")
    assert ruoli.avvisi == ["Le quote di titolari del godimento sommano a 90%"]


def test_quota_unico_soggetto_senza_quota_vale_100():
    voci, ruoli = _voci([_diritto(_soggetto("Solo"), "PROPRIETARIO")], [], "UNITA")
    assert _chi(voci["IMU"]) == [("Solo", Decimal(100))]
    assert ruoli.avvisi == []


def test_due_conduttori_quota_nulla():
    p, c1, c2 = _soggetto("P"), _soggetto("C1"), _soggetto("C2")
    voci, _ = _voci([_diritto(p, "PROPRIETARIO")], [_conduttore(c1), _conduttore(c2)], "UNITA")
    assert _chi(voci["SPESE_ORDINARIE"]) == [("C1", None), ("C2", None)]


def test_diritto_altro_avviso():
    p, a = _soggetto("P"), _soggetto("Strano")
    voci, ruoli = _voci([_diritto(p, "PROPRIETARIO"), _diritto(a, "ALTRO")], [], "UNITA")
    assert _chi(voci["IMU"]) == [("P", Decimal(100))]
    assert ruoli.avvisi == ["Diritto 'ALTRO' di Strano: ripartizione da decidere a mano"]


def test_nessun_diritto():
    voci, ruoli = _voci([], [], "UNITA")
    assert all(v.soggetti == [] for v in voci.values())
    assert ruoli.avvisi == ["Nessun titolare registrato alla data"]


def test_enfiteusi_straordinarie_all_enfiteuta():
    concedente, enfiteuta = _soggetto("Concedente"), _soggetto("Enfiteuta")
    voci, ruoli = _voci([_diritto(concedente, "PROPRIETARIO", 100), _diritto(enfiteuta, "ENFITEUSI", 100)],
                        [], "TERRENO")
    assert ruoli.usufrutto is True
    assert _chi(voci["IMU"]) == [("Enfiteuta", Decimal(100))]
    assert _chi(voci["SPESE_STRAORDINARIE"]) == [("Enfiteuta", Decimal(100))]


@pytest.mark.parametrize("tipo", ["USO", "ABITAZIONE"])
def test_uso_abitazione_straordinarie_al_proprietario(tipo):
    p, titolare = _soggetto("Proprietario"), _soggetto("Titolare")
    voci, _ = _voci([_diritto(p, "PROPRIETARIO", 100), _diritto(titolare, tipo, 100)], [], "UNITA")
    assert _chi(voci["SPESE_STRAORDINARIE"]) == [("Proprietario", Decimal(100))]
    assert _chi(voci["SPESE_ORDINARIE"]) == [("Titolare", Decimal(100))]


def test_usufrutto_su_una_quota_e_piena_proprieta_sull_altra():
    """Succession: spouse has usufruct on the deceased's half, the co-owner keeps his half in full."""
    coniuge, figlio, comproprietario = _soggetto("Coniuge"), _soggetto("Figlio"), _soggetto("Compro")
    voci, ruoli = _voci([
        _diritto(coniuge, "USUFRUTTUARIO", 50), _diritto(figlio, "NUDA_PROPRIETA", 50),
        _diritto(comproprietario, "COMPROPRIETARIO", 50),
    ], [], "UNITA")
    assert _chi(voci["IMU"]) == [("Coniuge", Decimal(50)), ("Compro", Decimal(50))]
    assert _chi(voci["RENDITA"]) == [("Coniuge", Decimal(50)), ("Compro", Decimal(50))]
    assert _chi(voci["SPESE_STRAORDINARIE"]) == [("Figlio", Decimal(50)), ("Compro", Decimal(50))]
    assert ruoli.avvisi == []
