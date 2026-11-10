"""
Core role relations (core_relazioni) and RelazioneService: type-driven
scadenza in the core scadenziario, duplicates, one open relation per object.
"""
from datetime import date

import pytest

from app.core.models.tenant import Tenant, TenantModule

from anagrafica_italiana.models import SoggettoAnagrafico
from anagrafica_italiana.models.soggetto_anagrafico import TipoSoggetto
from anagrafica_italiana.__manifest__ import manifest as anagrafica_manifest
from affitti_lungo.__manifest__ import manifest as affitti_manifest
from immobili.__manifest__ import manifest as immobili_manifest
from immobili.models import Condominio
from app.core.platform.models import Scadenza, StatoScadenza
from app.core.platform_services.relation_type_sync import sync_relation_types
from app.core.platform_services.relazione_service import RelazioneService

pytestmark = pytest.mark.integration

from tests.integration.conftest import TEST_TENANT as TENANT


@pytest.fixture
def svc(db_session):
    sync_relation_types(db_session, {
        "immobili": immobili_manifest,
        "affitti_lungo": affitti_manifest,
        "anagrafica_italiana": anagrafica_manifest,
    })
    return RelazioneService(db_session, TENANT, user_id=None)


@pytest.fixture
def rossi(db_session):
    s = SoggettoAnagrafico(tipo_soggetto=TipoSoggetto.PERSONA_FISICA, nome="Mario", cognome="Rossi")
    db_session.add(s)
    db_session.flush()
    return s


@pytest.fixture
def bianchi(db_session):
    s = SoggettoAnagrafico(tipo_soggetto=TipoSoggetto.PERSONA_FISICA, nome="Anna", cognome="Bianchi")
    db_session.add(s)
    db_session.flush()
    return s


@pytest.fixture
def condominio(db_session, unique_suffix):
    c = Condominio(codice=f"COND-{unique_suffix}", nome="Condominio Aurora", indirizzo="Via Po 1", citta="Torino")
    db_session.add(c)
    db_session.flush()
    return c


def _amm(svc, soggetto, condominio, **kw):
    return svc.crea(soggetto.id, "amministratore_condominio", entity_type="CONDOMINIO",
                    entity_id=condominio.id, data_inizio=kw.pop("data_inizio", date(2026, 1, 15)), **kw)


def test_crea_amministratore_calcola_scadenza(svc, db_session, rossi, condominio):
    rel = _amm(svc, rossi, condominio)
    assert rel.data_scadenza == date(2027, 1, 15)
    sc = db_session.get(Scadenza, rel.scadenza_id)
    assert sc.stato == StatoScadenza.ATTIVA
    assert (sc.modulo, sc.entity_type, sc.entity_id) == ("immobili", "CONDOMINIO", condominio.id)
    assert sc.titolo == "Amministratore condominio — Rossi Mario"
    assert sc.data_scadenza == date(2027, 1, 15)


def test_data_scadenza_manuale_ignorata_se_calcolata(svc, rossi, condominio):
    rel = _amm(svc, rossi, condominio, data_scadenza=date(2030, 1, 1))
    assert rel.data_scadenza == date(2027, 1, 15)


def test_unico_per_oggetto(svc, db_session, rossi, bianchi, condominio):
    prima = _amm(svc, rossi, condominio)
    with pytest.raises(ValueError, match="già un amministratore"):
        _amm(svc, bianchi, condominio)
    svc.aggiorna(prima.id, data_fine=date(2026, 6, 30))
    assert db_session.get(Scadenza, prima.scadenza_id).stato == StatoScadenza.COMPLETATA
    seconda = _amm(svc, bianchi, condominio, data_inizio=date(2026, 7, 1))
    assert seconda.data_scadenza == date(2027, 7, 1)


def _attiva_modulo(db, module_id):
    """A test-only module must be enabled in the tenant for its relation types to be writable."""
    tenant = db.query(Tenant).filter_by(schema_name=TENANT).one()
    db.add(TenantModule(tenant_id=tenant.id, module_id=module_id, enabled=True))
    db.flush()


def test_duplicato_aperto(svc, db_session, rossi, condominio, unique_suffix):
    _attiva_modulo(db_session, f"m_{unique_suffix}")
    sync_relation_types(db_session, {f"m_{unique_suffix}": {"relation_types": [
        {"codice": f"cons_{unique_suffix}", "nome": "Consigliere", "entity_types": ["CONDOMINIO"]},
    ]}})
    svc.crea(rossi.id, f"cons_{unique_suffix}", entity_type="CONDOMINIO", entity_id=condominio.id)
    with pytest.raises(ValueError, match="Esiste già"):
        svc.crea(rossi.id, f"cons_{unique_suffix}", entity_type="CONDOMINIO", entity_id=condominio.id)


def test_tipo_modulo_rifiutato(svc, rossi):
    with pytest.raises(ValueError, match="gestito dal modulo"):
        svc.crea(rossi.id, "proprietario")


def test_entity_type_non_applicabile(svc, rossi):
    with pytest.raises(ValueError, match="non si applica"):
        svc.crea(rossi.id, "amministratore_condominio", entity_type="IMMOBILE", entity_id=1)


def test_oggetto_inesistente(svc, rossi):
    with pytest.raises(LookupError):
        svc.crea(rossi.id, "amministratore_condominio", entity_type="CONDOMINIO", entity_id=999999999)


def test_elimina_annulla_scadenza(svc, db_session, rossi, condominio):
    rel = _amm(svc, rossi, condominio)
    scadenza_id = rel.scadenza_id
    svc.elimina(rel.id)
    assert db_session.get(Scadenza, scadenza_id).stato == StatoScadenza.CANCELLATA


def test_rinnova_sposta_di_un_periodo(svc, db_session, rossi, condominio):
    rel = _amm(svc, rossi, condominio)
    scadenza_id = rel.scadenza_id
    rel = svc.rinnova(rel.id)
    assert rel.data_scadenza == date(2028, 1, 15)
    assert rel.scadenza_id == scadenza_id
    assert db_session.get(Scadenza, scadenza_id).data_scadenza == date(2028, 1, 15)


def test_manuale_senza_data_nessuna_scadenza(svc, db_session, rossi, condominio, unique_suffix):
    _attiva_modulo(db_session, f"m_{unique_suffix}")
    sync_relation_types(db_session, {f"m_{unique_suffix}": {"relation_types": [
        {"codice": f"inc_{unique_suffix}", "nome": "Incarico", "entity_types": ["CONDOMINIO"],
         "scadenza": {"manuale": True}},
    ]}})
    rel = svc.crea(rossi.id, f"inc_{unique_suffix}", entity_type="CONDOMINIO", entity_id=condominio.id)
    assert rel.data_scadenza is None and rel.scadenza_id is None
    rel = svc.aggiorna(rel.id, data_scadenza=date(2027, 3, 1))
    assert db_session.get(Scadenza, rel.scadenza_id).data_scadenza == date(2027, 3, 1)


def test_elimina_per_oggetto(svc, db_session, rossi, condominio):
    rel = _amm(svc, rossi, condominio)
    scadenza_id = rel.scadenza_id
    assert svc.elimina_per_oggetto("CONDOMINIO", condominio.id) == 1
    assert db_session.get(Scadenza, scadenza_id).stato == StatoScadenza.CANCELLATA
    assert svc.conta_per_soggetto(rossi.id) == 0


def test_conta_per_soggetto_come_soggetto_e_come_oggetto(svc, db_session, rossi, condominio):
    azienda = SoggettoAnagrafico(tipo_soggetto=TipoSoggetto.PERSONA_GIURIDICA, ragione_sociale="ACME")
    db_session.add(azienda)
    db_session.flush()
    _amm(svc, rossi, condominio)
    svc.crea(rossi.id, "ruolo_azienda", entity_type="SOGGETTO_ANAGRAFICO", entity_id=azienda.id, dati={"ruolo": "Socio"})
    assert svc.conta_per_soggetto(rossi.id) == 2
    assert svc.conta_per_soggetto(azienda.id) == 1


def test_ruoli_azienda_testo_libero_diversi_non_sono_duplicati(svc, db_session, rossi):
    azienda = SoggettoAnagrafico(tipo_soggetto=TipoSoggetto.PERSONA_GIURIDICA, ragione_sociale="ACME")
    db_session.add(azienda)
    db_session.flush()
    kw = dict(entity_type="SOGGETTO_ANAGRAFICO", entity_id=azienda.id)
    svc.crea(rossi.id, "ruolo_azienda", dati={"ruolo": "Socio"}, **kw)
    svc.crea(rossi.id, "ruolo_azienda", dati={"ruolo": "Consulente"}, **kw)
    with pytest.raises(ValueError, match="Esiste già"):
        svc.crea(rossi.id, "ruolo_azienda", dati={"ruolo": "Socio"}, **kw)


def test_fk_cascade_se_l_anagrafica_sparisce(svc, db_session, rossi, condominio):
    from sqlalchemy import text
    rel_id = _amm(svc, rossi, condominio).id
    db_session.execute(text("DELETE FROM anag_soggetti_anagrafici WHERE id = :id"), {"id": rossi.id})
    db_session.expire_all()
    assert db_session.execute(text("SELECT count(*) FROM core_relazioni WHERE id = :id"), {"id": rel_id}).scalar() == 0
