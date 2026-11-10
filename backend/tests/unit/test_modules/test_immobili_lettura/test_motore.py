from immobili.services.lettura_documenti.motore import SpecTipo, applica

SPEC = SpecTipo(
    codice="PROVA",
    riconosci=[r"Catasto", r"Foglio"],
    campi={"foglio": r"Foglio:\s*(?P<v>\d+)", "sub": r"Sub(?:alterno)?:\s*(?P<v>\d+)"},
)


def test_riconosce_solo_se_tutte_le_frasi():
    assert applica(SPEC, "Catasto\nFoglio: 1").riconosciuto is True
    assert applica(SPEC, "Foglio: 1").riconosciuto is False


def test_campo_prima_corrispondenza_gruppo_v():
    r = applica(SPEC, "Catasto Foglio:  12 \nFoglio: 99\nSubalterno: 6")
    assert r.campi == {"foglio": "12", "sub": "6"}


def test_campo_assente_non_compare():
    assert "sub" not in applica(SPEC, "Catasto Foglio: 12").campi


def test_to_dict_forma_contratto():
    assert SPEC.to_dict() == {"codice": "PROVA", "riconosci": SPEC.riconosci, "campi": SPEC.campi}
