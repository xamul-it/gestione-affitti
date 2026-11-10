"""
Role relations and the tenant module lifecycle: a disabled module's relations
are hidden and can't be written, their scadenze are cancelled and reopened on
re-enable; dropping a module's tables deletes its core relations; a module
can't be disabled or uninstalled while an enabled module depends on it.
"""
from datetime import date

import pytest
from fastapi import HTTPException

from anagrafica_italiana.__manifest__ import manifest as anagrafica_manifest
from anagrafica_italiana.models import SoggettoAnagrafico
from anagrafica_italiana.models.soggetto_anagrafico import TipoSoggetto
from affitti_lungo.__manifest__ import manifest as affitti_manifest
from immobili.__manifest__ import manifest as immobili_manifest
from immobili.models import Condominio
from app.core.auth.models import User
from app.core.models.tenant import TenantModule
from app.core.platform.models import Relazione, Scadenza, StatoScadenza
from app.core.platform_services import relazioni_query as rq
from app.core.platform_services.relation_type_sync import sync_relation_types
from app.core.platform_services.relazione_service import RelazioneService
from app.core.routes.tenants import disable_module, uninstall_module
from app.core.services.tenant_module_service import TenantModuleService
from tests.integration.conftest import TEST_TENANT

pytestmark = pytest.mark.integration

DIPENDENTI = ("affitti_lungo", "affitti_brevi")


@pytest.fixture
def ctx(db_session, test_tenant, unique_suffix, monkeypatch):
    db = db_session
    sync_relation_types(db, {"immobili": immobili_manifest, "affitti_lungo": affitti_manifest,
                             "anagrafica_italiana": anagrafica_manifest})
    s = SoggettoAnagrafico(tipo_soggetto=TipoSoggetto.PERSONA_FISICA, nome="Mario", cognome=f"M{unique_suffix}")
    c = Condominio(codice=f"RM-{unique_suffix}", nome="Aurora", indirizzo="Via Po 1", citta="Torino")
    db.add_all([s, c])
    db.flush()
    rel = RelazioneService(db, TEST_TENANT).crea(s.id, "amministratore_condominio", entity_type="CONDOMINIO",
                                               entity_id=c.id, data_inizio=date.today())
    db.flush()
    # Never drop real tables here: the drop step only sees an empty table list.
    monkeypatch.setattr(TenantModuleService, "_get_tenant_tables", staticmethod(lambda *a, **k: []))
    monkeypatch.setattr(TenantModuleService, "_get_tenant_tables_for_module", staticmethod(lambda *a, **k: []))
    return db, test_tenant, s, c, rel


def _spegni_dipendenti(db, tenant):
    for m in DIPENDENTI:
        tm = db.query(TenantModule).filter_by(tenant_id=tenant.id, module_id=m).first()
        if tm:
            tm.enabled = False
    db.flush()


def _tipi_visibili(db, soggetto_id):
    return {r["tipo"] for r in rq.elenca(db, TEST_TENANT, permessi={"*"}, soggetto_ids=[soggetto_id])}


def test_disabilitare_nasconde_e_annulla_le_scadenze(ctx):
    db, tenant, s, c, rel = ctx
    scadenza_id = rel.scadenza_id
    assert "amministratore_condominio" in _tipi_visibili(db, s.id)
    _spegni_dipendenti(db, tenant)

    TenantModuleService.disable_module_for_tenant(tenant.id, "immobili", db)

    assert "amministratore_condominio" not in _tipi_visibili(db, s.id)
    assert db.get(Scadenza, scadenza_id).stato == StatoScadenza.CANCELLATA
    assert db.get(Relazione, rel.id) is not None and db.get(Relazione, rel.id).scadenza_id is None
    with pytest.raises(ValueError, match="non è attivo"):
        RelazioneService(db, TEST_TENANT).crea(s.id, "amministratore_condominio", entity_type="CONDOMINIO",
                                               entity_id=c.id, data_inizio=date(2020, 1, 1),
                                               data_fine=date(2020, 6, 1))
    with pytest.raises(ValueError, match="non è attivo"):
        RelazioneService(db, TEST_TENANT).rinnova(rel.id)


def test_riattivare_riapre_le_scadenze(ctx):
    db, tenant, s, c, rel = ctx
    _spegni_dipendenti(db, tenant)
    TenantModuleService.disable_module_for_tenant(tenant.id, "immobili", db)

    TenantModuleService._register_module(tenant.id, "immobili", db)

    db.refresh(rel)
    assert "amministratore_condominio" in _tipi_visibili(db, s.id)
    assert rel.scadenza_id is not None
    assert db.get(Scadenza, rel.scadenza_id).stato == StatoScadenza.ATTIVA


def test_disabilitare_rifiutato_se_un_modulo_dipende(ctx):
    db, tenant, *_ = ctx
    with pytest.raises(ValueError, match="affitti_lungo"):
        TenantModuleService.disable_module_for_tenant(tenant.id, "immobili", db)
    assert db.query(TenantModule).filter_by(tenant_id=tenant.id, module_id="immobili").one().enabled is True


def test_disinstallare_rifiutato_se_un_modulo_dipende(ctx):
    db, tenant, *_ = ctx
    with pytest.raises(ValueError, match="affitti_lungo"):
        TenantModuleService.uninstall_module_for_tenant(tenant.id, "immobili", False, db)


def test_rotta_disabilita_risponde_400_sulle_dipendenze(ctx):
    db, tenant, *_ = ctx
    admin = User(id=1, username="a", is_superuser=True, is_active=True, roles=[])
    with pytest.raises(HTTPException) as exc:
        disable_module(tenant.id, "immobili", current_user=admin, db=db)
    assert exc.value.status_code == 400
    with pytest.raises(HTTPException) as exc:
        uninstall_module(tenant.id, "immobili", current_user=admin, db=db)
    assert exc.value.status_code == 400


def test_disinstallare_con_tabelle_elimina_le_relazioni(ctx):
    db, tenant, s, c, rel = ctx
    rel_id, scadenza_id = rel.id, rel.scadenza_id
    _spegni_dipendenti(db, tenant)

    TenantModuleService.uninstall_module_for_tenant(tenant.id, "immobili", True, db)

    assert db.get(Relazione, rel_id) is None
    assert db.get(Scadenza, scadenza_id).stato == StatoScadenza.CANCELLATA


def test_disabilitare_cancellando_le_tabelle_elimina_le_relazioni(ctx):
    db, tenant, s, c, rel = ctx
    rel_id = rel.id
    _spegni_dipendenti(db, tenant)

    TenantModuleService.disable_module_for_tenant(tenant.id, "immobili", db, drop_tables=True)

    assert db.get(Relazione, rel_id) is None


def test_disinstallare_senza_tabelle_conserva_le_relazioni(ctx):
    db, tenant, s, c, rel = ctx
    _spegni_dipendenti(db, tenant)

    TenantModuleService.uninstall_module_for_tenant(tenant.id, "immobili", False, db)

    assert db.get(Relazione, rel.id) is not None
    assert "amministratore_condominio" not in _tipi_visibili(db, s.id)


def test_riattivare_non_riapre_scadenze_chiuse_a_mano(ctx):
    """_register_module also runs on every release (sync_modules): a scadenza
    the user completed in the scadenziario must stay completed."""
    db, tenant, s, c, rel = ctx
    db.get(Scadenza, rel.scadenza_id).stato = StatoScadenza.COMPLETATA
    db.flush()
    prima = rel.scadenza_id

    TenantModuleService._register_module(tenant.id, "immobili", db)

    db.refresh(rel)
    assert rel.scadenza_id == prima
    assert db.query(Scadenza).filter_by(entity_type="CONDOMINIO", entity_id=c.id,
                                        stato=StatoScadenza.ATTIVA).count() == 0
