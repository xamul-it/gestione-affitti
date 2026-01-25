#!/usr/bin/env python3
"""
Script per creare dati di test per il modulo Affitti Brevi
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path('.').resolve() / 'modules'))

from datetime import date, datetime, timedelta
from decimal import Decimal
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import random

from app.core.config import settings
from app.core.database import Base

# Import models
from anagrafica_italiana.models import SoggettoAnagrafico, TipoSoggetto
from immobili.models import UnitaImmobiliare, ComuneItalia
from affitti_brevi.models import (
    CalendarioIcal, Prenotazione, OspitePrenotazione, BloccoCalendario,
    StatoPrenotazione, OriginePrenotazione, PortaleBooking, TassaSoggiornoConfig,
    TipoCalcoloTassa, TassaPrenotazione, TipoBlocco, PortaleBlocco,
    StatoSincronizzazione
)
from app.core.platform.models.scadenza import Scadenza, PrioritaScadenza, StatoScadenza
from affitti_brevi.models.scadenza_ext import ScadenzaAffittiBrevi, TipoScadenzaAffittiBrevi

# Setup
engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

def seed_tenant_test():
    """Popola il tenant_test con dati di test"""

    db = SessionLocal()

    try:
        # Set search path to tenant_test
        db.execute(text("SET search_path TO tenant_test, public"))
        print("🎯 Connected to tenant_test schema")

        # 1. Crea comuni se non esistono (nel public schema)
        db.execute(text("SET search_path TO public"))
        comune_venezia = db.query(ComuneItalia).filter_by(nome="Venezia").first()
        if not comune_venezia:
            comune_venezia = ComuneItalia(
                nome="Venezia",
                provincia="VE",
                regione="Veneto",
                cap="30100",
                codice_catastale="L736"
            )
            db.add(comune_venezia)
            db.commit()
            print(f"✅ Created comune: Venezia")

        # Switch back to tenant_test
        db.execute(text("SET search_path TO tenant_test, public"))

        # 2. Crea soggetti anagrafici (ospiti)
        print("\n👥 Creating soggetti anagrafici (guests)...")
        ospiti = []
        ospiti_data = [
            ("Mario", "Rossi", "RSSMRA85M01H501Z", "mario.rossi@email.it", "+39 348 1234567"),
            ("Laura", "Bianchi", "BNCLRA90H41F205W", "laura.bianchi@email.it", "+39 347 2345678"),
            ("Giovanni", "Verdi", "VRDGNN88C15L219X", "giovanni.verdi@email.it", "+39 349 3456789"),
            ("Anna", "Neri", "NRANNA92D45H501K", "anna.neri@email.it", "+39 346 4567890"),
            ("Paolo", "Gialli", "GLLPLA86T10A944Y", "paolo.gialli@email.it", "+39 345 5678901"),
            ("Francesca", "Rosa", "RSOFNC89P48D612H", "francesca.rosa@email.it", "+39 344 6789012"),
            ("Marco", "Blu", "BLUMRC91L20F839N", "marco.blu@email.it", "+39 343 7890123"),
            ("Giulia", "Viola", "VLNGLI93S60H501P", "giulia.viola@email.it", "+39 342 8901234"),
        ]

        for nome, cognome, cf, email, telefono in ospiti_data:
            existing = db.query(SoggettoAnagrafico).filter_by(codice_fiscale=cf).first()
            if not existing:
                ospite = SoggettoAnagrafico(
                    tipo_soggetto=TipoSoggetto.PERSONA_FISICA,
                    codice_fiscale=cf,
                    nome=nome,
                    cognome=cognome,
                    email=email,
                    telefono=telefono,
                    attivo=True
                )
                db.add(ospite)
                ospiti.append(ospite)

        db.commit()
        print(f"✅ Created {len(ospiti)} guests")

        # Re-query to get all ospiti with IDs
        ospiti = db.query(SoggettoAnagrafico).filter(
            SoggettoAnagrafico.codice_fiscale.in_([cf for _, _, cf, _, _ in ospiti_data])
        ).all()

        # 3. Crea unità immobiliari
        print("\n🏠 Creating unità immobiliari...")
        unita = []
        unita_data = [
            ("ABV001", "Appartamento", "Calle Larga, 123", "30100", 3, "Trilocale fronte mare con vista laguna"),
            ("ABV002", "Appartamento", "Via dei Monti, 45", "30100", 2, "Bilocale con giardino privato"),
            ("ABV003", "Appartamento", "Piazza San Marco, 7", "30100", 4, "Attico di lusso con terrazza panoramica"),
            ("ABV004", "Appartamento", "Via Garibaldi, 89", "30100", 1, "Monolocale moderno recentemente ristrutturato"),
        ]

        for codice, tipo, indirizzo, cap, locali, descrizione in unita_data:
            existing = db.query(UnitaImmobiliare).filter_by(codice=codice).first()
            if not existing:
                unita_obj = UnitaImmobiliare(
                    codice=codice,
                    tipo=tipo,
                    indirizzo=indirizzo,
                    citta="Venezia",
                    cap=cap,
                    provincia="VE",
                    superficie_mq=float(random.randint(45, 120)),
                    locali=locali,
                    descrizione=descrizione
                )
                db.add(unita_obj)
                unita.append(unita_obj)

        db.commit()
        print(f"✅ Created {len(unita)} properties")

        # Re-query to get all unita with IDs
        unita = db.query(UnitaImmobiliare).filter(
            UnitaImmobiliare.codice.in_([codice for codice, _, _, _, _, _ in unita_data])
        ).all()

        # 4. Crea calendari iCal
        print("\n📅 Creating calendari iCal...")
        calendari = []
        portali = [PortaleBooking.BOOKING_COM, PortaleBooking.AIRBNB, PortaleBooking.VRBO]

        for unita_obj in unita[:3]:  # Primi 3 appartamenti
            for portale in portali[:2]:  # Booking e Airbnb per ognuno
                existing = db.query(CalendarioIcal).filter_by(
                    unita_immobiliare_id=unita_obj.id,
                    portale=portale
                ).first()

                if not existing:
                    calendario = CalendarioIcal(
                        unita_immobiliare_id=unita_obj.id,
                        portale=portale,
                        url_ical=f"https://www.{portale.value.lower().replace('_', '')}.com/calendar/ical/{random.randint(100000, 999999)}.ics",
                        attivo=True,
                        stato_sincronizzazione=StatoSincronizzazione.SUCCESSO,
                        ultima_sincronizzazione=datetime.now() - timedelta(hours=random.randint(1, 12))
                    )
                    db.add(calendario)
                    calendari.append(calendario)

        db.commit()
        print(f"✅ Created {len(calendari)} iCal calendars")

        # 5. Crea prenotazioni
        print("\n📝 Creating prenotazioni...")
        prenotazioni = []
        oggi = date.today()

        # Prenotazioni passate
        for i in range(5):
            unita_obj = random.choice(unita[:3])
            ospite = random.choice(ospiti)

            checkin = oggi - timedelta(days=random.randint(30, 90))
            checkout = checkin + timedelta(days=random.randint(3, 14))

            prenotazione = Prenotazione(
                unita_immobiliare_id=unita_obj.id,
                data_checkin=checkin,
                data_checkout=checkout,
                numero_ospiti=random.randint(1, 4),
                prezzo_totale=Decimal(random.randint(300, 1500)),
                stato=StatoPrenotazione.CHECK_OUT_EFFETTUATO,
                portale_origine=random.choice(list(OriginePrenotazione)),
                codice_prenotazione=f"BK{random.randint(100000, 999999)}",
                note="Prenotazione completata senza problemi"
            )
            db.add(prenotazione)
            db.flush()

            # Aggiungi ospite
            ospite_pren = OspitePrenotazione(
                prenotazione_id=prenotazione.id,
                soggetto_anagrafico_id=ospite.id,
                ospite_principale=True
            )
            db.add(ospite_pren)
            prenotazioni.append(prenotazione)

        # Prenotazioni attuali
        for i in range(3):
            unita_obj = random.choice(unita[:3])
            ospite = random.choice(ospiti)

            checkin = oggi - timedelta(days=random.randint(1, 5))
            checkout = oggi + timedelta(days=random.randint(2, 10))

            prenotazione = Prenotazione(
                unita_immobiliare_id=unita_obj.id,
                data_checkin=checkin,
                data_checkout=checkout,
                numero_ospiti=random.randint(1, 4),
                prezzo_totale=Decimal(random.randint(400, 1800)),
                stato=StatoPrenotazione.CONFERMATA,
                portale_origine=random.choice(list(OriginePrenotazione)),
                codice_prenotazione=f"AB{random.randint(100000, 999999)}"
            )
            db.add(prenotazione)
            db.flush()

            # Aggiungi ospiti (2-3 per prenotazione)
            num_ospiti = random.randint(2, 3)
            for j in range(num_ospiti):
                ospite_sel = random.choice(ospiti)
                ospite_pren = OspitePrenotazione(
                    prenotazione_id=prenotazione.id,
                    soggetto_anagrafico_id=ospite_sel.id,
                    ospite_principale=(j == 0)
                )
                db.add(ospite_pren)

            prenotazioni.append(prenotazione)

        # Prenotazioni future
        for i in range(8):
            unita_obj = random.choice(unita[:3])
            ospite = random.choice(ospiti)

            checkin = oggi + timedelta(days=random.randint(5, 60))
            checkout = checkin + timedelta(days=random.randint(3, 14))

            prenotazione = Prenotazione(
                unita_immobiliare_id=unita_obj.id,
                data_checkin=checkin,
                data_checkout=checkout,
                numero_ospiti=random.randint(1, 4),
                prezzo_totale=Decimal(random.randint(350, 2000)),
                stato=StatoPrenotazione.CONFERMATA,
                portale_origine=random.choice(list(OriginePrenotazione)),
                codice_prenotazione=f"VR{random.randint(100000, 999999)}"
            )
            db.add(prenotazione)
            db.flush()

            # Aggiungi ospite
            ospite_pren = OspitePrenotazione(
                prenotazione_id=prenotazione.id,
                soggetto_anagrafico_id=ospite.id,
                ospite_principale=True
            )
            db.add(ospite_pren)
            prenotazioni.append(prenotazione)

        db.commit()
        print(f"✅ Created {len(prenotazioni)} bookings")

        # 6. Crea blocchi calendario
        print("\n🚫 Creating blocchi calendario...")
        blocchi = []

        for unita_obj in unita[:2]:
            # Blocco manutenzione
            data_inizio = oggi + timedelta(days=random.randint(20, 40))
            data_fine = data_inizio + timedelta(days=random.randint(5, 10))

            blocco = BloccoCalendario(
                immobile_id=unita_obj.id,
                portale=PortaleBlocco.TUTTI,
                data_inizio=data_inizio,
                data_fine=data_fine,
                tipo_blocco=TipoBlocco.MANUTENZIONE,
                motivo="Manutenzione programmata",
                note="Ristrutturazione bagno"
            )
            db.add(blocco)
            blocchi.append(blocco)

        db.commit()
        print(f"✅ Created {len(blocchi)} calendar blocks")

        # 7. Crea configurazione tassa soggiorno
        print("\n💰 Creating tassa soggiorno config...")
        # Re-query comune from public schema
        comune_venezia_id = db.execute(
            text("SELECT id FROM public.anag_comuni_italia WHERE nome = 'Venezia' LIMIT 1")
        ).scalar()
        existing_config = db.query(TassaSoggiornoConfig).filter_by(comune_id=comune_venezia_id).first() if comune_venezia_id else None

        if not existing_config and comune_venezia_id:
            config = TassaSoggiornoConfig(
                comune_id=comune_venezia_id,
                comune_nome="Venezia",
                tipo_calcolo=TipoCalcoloTassa.FISSO,
                importo_fisso=Decimal("3.50"),
                eta_minima=14,
                notti_max=5,
                data_inizio_validita=date(2024, 1, 1),
                attiva=True,
                note="Tassa soggiorno Comune di Venezia - €3.50 per notte per persona"
            )
            db.add(config)
            db.commit()
            print("✅ Created tourist tax configuration")

            # Crea tasse per prenotazioni completate
            for pren in prenotazioni[:5]:  # Prime 5 prenotazioni
                notti = (pren.data_checkout - pren.data_checkin).days
                notti_tassabili = min(notti, 5)  # Max 5 notti

                tassa = TassaPrenotazione(
                    prenotazione_id=pren.id,
                    config_id=config.id,
                    importo_totale=Decimal("3.50") * notti_tassabili * pren.numero_ospiti,
                    numero_notti_tassabili=notti_tassabili,
                    numero_ospiti_tassabili=pren.numero_ospiti,
                    dettaglio_calcolo={
                        "tipo_calcolo": "FISSO",
                        "ospiti_totali": pren.numero_ospiti,
                        "ospiti_tassabili": pren.numero_ospiti,
                        "notti_totali": notti,
                        "notti_tassabili": notti_tassabili,
                        "importo_notte": "3.50",
                        "importo_totale": float(Decimal("3.50") * notti_tassabili * pren.numero_ospiti)
                    }
                )
                db.add(tassa)

            db.commit()
            print(f"✅ Created tourist tax records for completed bookings")

        # 8. Crea scadenze
        print("\n⏰ Skipping scadenze creation (not critical for testing)")
        scadenze_create = 0

        # TODO: Fix creato_da FK to allow scadenze creation
        # admin_user_id = db.execute(text("SELECT id FROM public.users WHERE username = 'admin' LIMIT 1")).scalar()

        if False:  # Temporarily disabled
            # Scadenze comunicazione polizia per prenotazioni attuali e future
            prenotazioni_attive = [p for p in prenotazioni if p.stato in [StatoPrenotazione.CONFERMATA, StatoPrenotazione.CHECK_IN_EFFETTUATO]]

            for pren in prenotazioni_attive[:5]:  # Prime 5 prenotazioni attive
                pass  # Disabled for now

            # Determina priorità e stato
            if data_scadenza < oggi:
                priorita = PrioritaScadenza.ALTA
                stato = StatoScadenza.SCADUTA
            elif data_scadenza <= oggi + timedelta(days=3):
                priorita = PrioritaScadenza.ALTA
                stato = StatoScadenza.ATTIVA
            else:
                priorita = PrioritaScadenza.MEDIA
                stato = StatoScadenza.ATTIVA

            # Crea scadenza core
            scadenza = Scadenza(
                modulo="affitti_brevi",
                entity_type="prenotazione",
                entity_id=pren.id,
                titolo=f"Comunicazione polizia - {pren.codice_prenotazione}",
                descrizione=f"Comunicazione obbligatoria entro 24h dal check-in per prenotazione {pren.codice_prenotazione}",
                data_scadenza=data_scadenza,
                priorita=priorita,
                stato=stato,
                creato_da=None  # Admin user
            )
            db.add(scadenza)
            db.flush()

            # Crea estensione affitti_brevi
            scadenza_ext = ScadenzaAffittiBrevi(
                scadenza_id=scadenza.id,
                tipo_scadenza=TipoScadenzaAffittiBrevi.COMUNICAZIONE_POLIZIA,
                ricorrente=False
            )
            db.add(scadenza_ext)
            scadenze_create += 1

        # Scadenze disabled for now (FK issues)
        # prossimo_mese = (oggi.replace(day=1) + timedelta(days=32)).replace(day=1)
        # ...

        print(f"⏩ Skipped {0} deadlines (temporarily disabled)")

        print("\n" + "="*60)
        print("🎉 DATI DI TEST CREATI CON SUCCESSO!")
        print("="*60)
        print(f"👥 Ospiti: {len(ospiti)}")
        print(f"🏠 Unità immobiliari: {len(unita)}")
        print(f"📅 Calendari iCal: {len(calendari)}")
        print(f"📝 Prenotazioni: {len(prenotazioni)}")
        print(f"   - Passate: 5")
        print(f"   - Attuali: 3")
        print(f"   - Future: 8")
        print(f"🚫 Blocchi calendario: {len(blocchi)}")
        print(f"💰 Configurazione tasse: 1")
        print(f"⏰ Scadenze: {scadenze_create}")
        print("="*60)

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    print("🚀 Starting seed script for Affitti Brevi...")
    print()
    seed_tenant_test()
