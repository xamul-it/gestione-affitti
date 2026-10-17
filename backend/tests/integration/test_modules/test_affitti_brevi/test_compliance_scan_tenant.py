"""
Test di integrazione per compliance_scheduler._scan_tenant — verifica il
filtro valido=True/data_checkin sulla query, che ComplianceScadenzeService
da solo non applica (riceve solo il Soggiorno che il chiamante gli passa).

Usa pg_session bound a singola Connection (stesso pattern di
test_compliance_scadenze_service.py / test_ical_sync.py).
"""
from datetime import date, timedelta

import pytest
from sqlalchemy import text

from affitti_brevi.models import Comunicazione, Prenotazione, Soggiorno, StatoSoggiorno
from affitti_brevi.services.compliance_scadenze_service import ComplianceScadenzeService
from affitti_brevi.services.compliance_scheduler import _scan_tenant
from app.core.platform.models import Scadenza, ScadenzaDestinatario
from immobili.models import UnitaImmobiliare

TENANT = "tenant_qa_test"


@pytest.fixture(autouse=True)
def override_get_db():
    """Shadow conftest.py's autouse override_get_db(db_session) for this module only — see test_notifica_model.py for rationale."""
    yield


@pytest.fixture
def pg_session():
    from app.core.database import engine
    from sqlalchemy.orm import Session as SASession

    connection = engine.connect()
    connection.execute(text(f"SET search_path TO {TENANT}, public"))
    connection.commit()
    session = SASession(bind=connection)
    try:
        yield session
    finally:
        session.close()
        connection.close()


def _crea_soggiorno(pg_session, codice, valido=True, stato=None):
    unita = UnitaImmobiliare(codice=codice, tipo="Appartamento", indirizzo="Via Test 1", citta="Testville")
    pg_session.add(unita)
    pg_session.flush()

    prenotazione = Prenotazione(
        unita_immobiliare_id=unita.id,
        codice_prenotazione=f"{codice}-PREN",
        data_checkin=date.today(),
        data_checkout=date.today() + timedelta(days=2),
    )
    pg_session.add(prenotazione)
    pg_session.flush()

    soggiorno = Soggiorno(
        prenotazione_id=prenotazione.id,
        unita_immobiliare_id=unita.id,
        data_checkin=date.today(),
        data_checkout=date.today() + timedelta(days=2),
        valido=valido,
    )
    if stato is not None:
        soggiorno.stato = stato
    pg_session.add(soggiorno)
    pg_session.commit()
    return unita, prenotazione, soggiorno


def _cleanup_soggiorni(pg_session, entries):
    """Ripulisce Comunicazione/Soggiorno/Prenotazione/UnitaImmobiliare e le
    Scadenze core collegate create da _scan_tenant, per evitare accumulo
    tra run successivi (stessa lezione di test_compliance_scadenze_service.py)."""
    soggiorno_ids = [soggiorno.id for _, _, soggiorno in entries]

    scadenza_ids = [
        row[0] for row in
        pg_session.query(Comunicazione.scadenza_id)
        .filter(
            Comunicazione.soggiorno_id.in_(soggiorno_ids),
            Comunicazione.scadenza_id.isnot(None),
        )
        .all()
    ]

    for unita, prenotazione, soggiorno in entries:
        pg_session.query(Comunicazione).filter_by(soggiorno_id=soggiorno.id).delete()
        pg_session.query(Soggiorno).filter_by(id=soggiorno.id).delete()
        pg_session.query(Prenotazione).filter_by(id=prenotazione.id).delete()
        pg_session.query(UnitaImmobiliare).filter_by(id=unita.id).delete()

    if scadenza_ids:
        pg_session.query(ScadenzaDestinatario).filter(
            ScadenzaDestinatario.scadenza_id.in_(scadenza_ids)
        ).delete(synchronize_session=False)
        pg_session.query(Scadenza).filter(
            Scadenza.id.in_(scadenza_ids)
        ).delete(synchronize_session=False)

    pg_session.commit()


def test_scan_tenant_ignora_soggiorni_non_validi(pg_session):
    unita_ok, pren_ok, soggiorno_ok = _crea_soggiorno(pg_session, "TEST-SCAN-OK")
    unita_ko, pren_ko, soggiorno_ko = _crea_soggiorno(pg_session, "TEST-SCAN-KO", valido=False)

    try:
        stats = _scan_tenant(TENANT)

        assert stats["errori"] == 0
        comunicazioni_ok = pg_session.query(Comunicazione).filter_by(soggiorno_id=soggiorno_ok.id).count()
        comunicazioni_ko = pg_session.query(Comunicazione).filter_by(soggiorno_id=soggiorno_ko.id).count()

        assert comunicazioni_ok == 2  # Polizia + tassa
        assert comunicazioni_ko == 0
    finally:
        # Le Comunicazioni create dalla scan possono aver generato Scadenze
        # core collegate (ComplianceScadenzeService -> ScadenzaService.
        # create_scadenza). Queste vivono nella stessa connessione
        # (search_path già include lo schema tenant) ma non sono coperte da
        # cascade su Comunicazione/Soggiorno — vanno ripulite esplicitamente
        # per evitare accumulo tra run successivi (stessa lezione di
        # test_compliance_scadenze_service.py).
        scadenza_ids = [
            row[0] for row in
            pg_session.query(Comunicazione.scadenza_id)
            .filter(
                Comunicazione.soggiorno_id.in_([soggiorno_ok.id, soggiorno_ko.id]),
                Comunicazione.scadenza_id.isnot(None),
            )
            .all()
        ]

        for unita, prenotazione, soggiorno in [(unita_ok, pren_ok, soggiorno_ok), (unita_ko, pren_ko, soggiorno_ko)]:
            pg_session.query(Comunicazione).filter_by(soggiorno_id=soggiorno.id).delete()
            pg_session.query(Soggiorno).filter_by(id=soggiorno.id).delete()
            pg_session.query(Prenotazione).filter_by(id=prenotazione.id).delete()
            pg_session.query(UnitaImmobiliare).filter_by(id=unita.id).delete()

        if scadenza_ids:
            pg_session.query(ScadenzaDestinatario).filter(
                ScadenzaDestinatario.scadenza_id.in_(scadenza_ids)
            ).delete(synchronize_session=False)
            pg_session.query(Scadenza).filter(
                Scadenza.id.in_(scadenza_ids)
            ).delete(synchronize_session=False)

        pg_session.commit()


def test_scan_tenant_ignora_soggiorni_annullati(pg_session):
    """Un Soggiorno valido=True ma stato=ANNULLATO (ospite che ha
    cancellato) non deve generare alcuna Comunicazione, anche se il
    check-in rientra nella finestra di scan. valido=True/False è un
    concetto diverso da cancellazione — vedi design doc."""
    unita, prenotazione, soggiorno = _crea_soggiorno(
        pg_session, "TEST-SCAN-ANNULLATO", valido=True, stato=StatoSoggiorno.ANNULLATO.value
    )

    try:
        stats = _scan_tenant(TENANT)

        assert stats["errori"] == 0
        comunicazioni = pg_session.query(Comunicazione).filter_by(soggiorno_id=soggiorno.id).count()
        assert comunicazioni == 0
    finally:
        _cleanup_soggiorni(pg_session, [(unita, prenotazione, soggiorno)])


def test_scan_tenant_isola_fallimento_per_soggiorno_rollback(pg_session, monkeypatch):
    """Regressione: se la generazione fallisce per un soggiorno a metà
    flush/commit (fallimento reale a livello DB), la Session resta in uno
    stato di transazione fallita finché non si chiama db.rollback(). Senza
    quel rollback nell'except di _scan_tenant, ogni query successiva sulla
    stessa Session solleva PendingRollbackError — un solo soggiorno
    difettoso blocca silenziosamente la generazione per tutti i soggiorni
    successivi dello stesso tenant. Qui il primo soggiorno fallisce con un
    vero errore DB (divisione per zero lato Postgres, non una semplice
    eccezione Python) e verifichiamo che il secondo riceva comunque le sue
    Comunicazioni."""
    unita_bad, pren_bad, soggiorno_bad = _crea_soggiorno(pg_session, "TEST-ROLLBACK-BAD")
    unita_ok, pren_ok, soggiorno_ok = _crea_soggiorno(pg_session, "TEST-ROLLBACK-OK")

    original = ComplianceScadenzeService.genera_scadenza_polizia

    def _genera_scadenza_polizia_con_fallimento(self, soggiorno):
        if soggiorno.id == soggiorno_bad.id:
            # Errore reale a livello di database (non una semplice
            # eccezione Python): manda la transazione della Session in
            # stato fallito, proprio come farebbe un IntegrityError durante
            # un flush/commit interno a ComplianceScadenzeService.
            self.db.execute(text("SELECT 1/0"))
        return original(self, soggiorno)

    monkeypatch.setattr(
        ComplianceScadenzeService, "genera_scadenza_polizia", _genera_scadenza_polizia_con_fallimento
    )

    try:
        stats = _scan_tenant(TENANT)

        assert stats["errori"] >= 1

        comunicazioni_bad = pg_session.query(Comunicazione).filter_by(soggiorno_id=soggiorno_bad.id).count()
        comunicazioni_ok = pg_session.query(Comunicazione).filter_by(soggiorno_id=soggiorno_ok.id).count()

        assert comunicazioni_bad == 0
        # Il punto della regressione: il soggiorno "ok" deve ricevere le sue
        # Comunicazioni nonostante il fallimento del primo. Senza
        # db.rollback() nell'except di _scan_tenant, questo fallisce con
        # comunicazioni_ok == 0 (PendingRollbackError silenziosamente
        # inghiottito dallo stesso except).
        assert comunicazioni_ok == 2
    finally:
        _cleanup_soggiorni(
            pg_session,
            [(unita_bad, pren_bad, soggiorno_bad), (unita_ok, pren_ok, soggiorno_ok)],
        )
