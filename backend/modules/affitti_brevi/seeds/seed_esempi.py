"""
Example data of affitti_brevi (seed_test_data=True): a holiday flat of this
module (AB-ESEMPIO-1, created through the immobili model this module depends
on, never looked up among the immobili example data), a channel calendar (no
sync), a booking with its stay and two guests, the tourist tax rule of the
town with one band and the stay's tax, the police communication and a
personal-use block.

Idempotent: everything hangs off the booking ESEMPIO-0001 and the rule
"Milano (esempio)" (scripts/tenant_prova.py reruns it).
"""
from datetime import date, datetime, timezone

from sqlalchemy.orm import Session

from ..models import (
    BloccoCalendario, CalendarioCanale, Canale, Comunicazione, OspiteSoggiorno, Prenotazione,
    Soggiorno, TassaSoggiorno, TassaSoggiornoConfig, TassaSoggiornoScaglione,
)

PRENOTAZIONE = "ESEMPIO-0001"
UNITA = "AB-ESEMPIO-1"
COMUNE_TASSA = "Milano (esempio)"


def _unita(db: Session) -> int:
    from immobili.models import UnitaImmobiliare
    unita = db.query(UnitaImmobiliare).filter(UnitaImmobiliare.codice == UNITA).first()
    if not unita:
        unita = UnitaImmobiliare(codice=UNITA, tipo="Appartamento", indirizzo="Via del Mare 3", citta="Milano",
                                 provincia="MI", descrizione="Casa vacanze di esempio del modulo affitti_brevi")
        db.add(unita)
        db.flush()
    return unita.id


def seed_esempi(db: Session) -> dict:
    canale = db.query(Canale).order_by(Canale.id).first()
    if not canale:
        return {}
    if db.query(Prenotazione).filter(Prenotazione.codice_prenotazione == PRENOTAZIONE).first():
        return {}
    unita_id = _unita(db)

    calendario = CalendarioCanale(unita_immobiliare_id=unita_id, canale_id=canale.id,
                                  codice_esterno="ESEMPIO", sync_attiva=False,
                                  note="Calendario di esempio, senza sincronizzazione")
    db.add(calendario)
    db.flush()
    prenotazione = Prenotazione(
        unita_immobiliare_id=unita_id, calendario_canale_id=calendario.id,
        codice_prenotazione=PRENOTAZIONE, data_checkin=date(2026, 7, 10), data_checkout=date(2026, 7, 14),
        numero_ospiti=2, nome_ospite_principale="Anna Esempio", prezzo_totale=520, prezzo_notte_medio=130,
        commissione_canale=78, incasso_netto=442,
    )
    db.add(prenotazione)
    db.flush()
    soggiorno = Soggiorno(prenotazione_id=prenotazione.id, unita_immobiliare_id=unita_id,
                          data_checkin=prenotazione.data_checkin, data_checkout=prenotazione.data_checkout,
                          numero_ospiti_previsti=2)
    db.add(soggiorno)
    db.flush()
    db.add_all([
        OspiteSoggiorno(soggiorno_id=soggiorno.id, ruolo="PRINCIPALE", principale=True,
                        cognome="Esempio", nome="Anna", data_nascita=date(1985, 4, 2),
                        tipo_documento="CARTA_IDENTITA", numero_documento="CA00000AA"),
        OspiteSoggiorno(soggiorno_id=soggiorno.id, ruolo="ACCOMPAGNATORE",
                        cognome="Esempio", nome="Marco", data_nascita=date(1983, 9, 21)),
    ])

    config = db.query(TassaSoggiornoConfig).filter(TassaSoggiornoConfig.comune_nome == COMUNE_TASSA).first()
    if not config:
        config = TassaSoggiornoConfig(comune_nome=COMUNE_TASSA, provincia="MI", importo_fisso=5,
                                      eta_minima_soggetta=18, notti_max_tassabili=14,
                                      data_inizio_validita=date(2026, 1, 1))
        db.add(config)
        db.flush()
        db.add(TassaSoggiornoScaglione(config_id=config.id, notte_da=1, notte_a=14, importo=5))
    db.add(TassaSoggiorno(soggiorno_id=soggiorno.id, config_id=config.id, importo_totale=40,
                          numero_notti_totali=4, numero_notti_tassabili=4, numero_ospiti_totali=2,
                          numero_ospiti_tassabili=2, stato="CALCOLATA"))
    db.add(Comunicazione(soggiorno_id=soggiorno.id, unita_immobiliare_id=unita_id, tipo="POLIZIA",
                         data_scadenza=datetime(2026, 7, 11, 10, tzinfo=timezone.utc)))
    db.add(BloccoCalendario(unita_immobiliare_id=unita_id, data_inizio=date(2026, 8, 1),
                            data_fine=date(2026, 8, 15), tipo="USO_PERSONALE", motivo="Ferie (esempio)"))
    db.flush()
    return {"ab_prenotazioni": 1, "ab_soggiorni": 1, "ab_ospiti_soggiorni": 2}
