#!/usr/bin/env python3
"""
Script to create all tables in tenant schemas
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path('.').resolve() / 'modules'))

from sqlalchemy import create_engine, text
from app.core.config import settings
from app.core.database import Base

# Import all models to register them with Base.metadata
# Core models
from app.core.auth.models import User
from app.core.platform.models import MenuItem, Widget, UserDashboard, Scadenza, ScadenzaDestinatario, ScadenzaLog

# Module models
from anagrafica_italiana.models import SoggettoAnagrafico
from immobili.models import (
    UnitaImmobiliare, Condominio, CertificatoEnergetico,
    TabellaMillesimale, MillesimiUnita, DirittoImmobile,
    CategoriaCatastale, ComuneItalia
)
from affitti_lungo.models import (
    Affittuario, Contratto, Incasso, Spesa, Tecnico, Documento
)
from affitti_brevi.models import (
    CalendarioIcal, Prenotazione, OspitePrenotazione, BloccoCalendario,
    TassaSoggiornoConfig, TassaSoggiornoScaglione, TassaPrenotazione,
    ComunicazionePolizia, ScadenzaAffittiBrevi
)

# Create engine
engine = create_engine(settings.DATABASE_URL)

# Create tables in tenant_test
print("🚀 Creating tables in tenant_test...")
with engine.connect() as conn:
    conn.execute(text("SET search_path TO tenant_test, public"))
    conn.commit()

    Base.metadata.create_all(bind=engine, checkfirst=True)
    print("✅ Tables created in tenant_test")

# Create tables in tenant_produzione
print("\n🚀 Creating tables in tenant_produzione...")
with engine.connect() as conn:
    conn.execute(text("SET search_path TO tenant_produzione, public"))
    conn.commit()

    Base.metadata.create_all(bind=engine, checkfirst=True)
    print("✅ Tables created in tenant_produzione")

print("\n✅ All tables created successfully!")
