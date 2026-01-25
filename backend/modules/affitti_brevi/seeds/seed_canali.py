"""
Seed Canali - Default Booking Channels

Creates the default booking channels for short-term rentals:
- Airbnb
- Booking.com
- Vrbo
- Direct (manual bookings)
- Other

Visual conventions follow the functional analysis:
- A (red) = Airbnb
- B (blue) = Booking.com
- V (purple) = Vrbo
- D (green) = Direct
- ? (gray) = Other
"""
from sqlalchemy.orm import Session
from ..models import Canale


# Default channels with visual properties
DEFAULT_CANALI = [
    {
        "codice": "AIRBNB",
        "nome": "Airbnb",
        "colore": "#FF5A5F",
        "simbolo": "A",
        "icona": "airbnb",
        "supporta_ical": True,
        "attivo": True,
        "note": "Piattaforma leader per affitti brevi. Supporta sincronizzazione iCal bidirezionale."
    },
    {
        "codice": "BOOKING_COM",
        "nome": "Booking.com",
        "colore": "#003580",
        "simbolo": "B",
        "icona": "booking",
        "supporta_ical": True,
        "attivo": True,
        "note": "Piattaforma globale per prenotazioni alberghiere e appartamenti. Supporta sincronizzazione iCal."
    },
    {
        "codice": "VRBO",
        "nome": "Vrbo",
        "colore": "#5D3B9E",
        "simbolo": "V",
        "icona": "vrbo",
        "supporta_ical": True,
        "attivo": True,
        "note": "Piattaforma per case vacanze del gruppo Expedia. Supporta sincronizzazione iCal."
    },
    {
        "codice": "DIRETTO",
        "nome": "Prenotazione Diretta",
        "colore": "#2E8B57",
        "simbolo": "D",
        "icona": "phone",
        "supporta_ical": False,
        "attivo": True,
        "note": "Prenotazioni ricevute direttamente (telefono, email, sito web proprietario)."
    },
    {
        "codice": "ALTRO",
        "nome": "Altro Canale",
        "colore": "#808080",
        "simbolo": "?",
        "icona": "question",
        "supporta_ical": True,
        "attivo": True,
        "note": "Canale generico per piattaforme non specificamente supportate."
    },
]


def seed_canali(db: Session, force: bool = False) -> dict:
    """
    Seed default booking channels.

    Args:
        db: Database session
        force: If True, update existing channels with default values

    Returns:
        dict with counts of created, updated, skipped channels
    """
    created = 0
    updated = 0
    skipped = 0

    for canale_data in DEFAULT_CANALI:
        codice = canale_data["codice"]

        # Check if channel exists
        existing = db.query(Canale).filter(Canale.codice == codice).first()

        if existing:
            if force:
                # Update existing channel
                for key, value in canale_data.items():
                    setattr(existing, key, value)
                updated += 1
            else:
                skipped += 1
        else:
            # Create new channel
            new_canale = Canale(**canale_data)
            db.add(new_canale)
            created += 1

    db.commit()

    return {
        "created": created,
        "updated": updated,
        "skipped": skipped,
        "total": len(DEFAULT_CANALI)
    }


def seed_canali_for_tenant(db: Session, tenant_schema: str, force: bool = False) -> dict:
    """
    Seed channels for a specific tenant schema.

    This function sets the search_path before seeding to ensure
    channels are created in the correct tenant schema.

    Args:
        db: Database session
        tenant_schema: Name of the tenant schema
        force: If True, update existing channels

    Returns:
        dict with seed results
    """
    from sqlalchemy import text

    # Set search path to tenant schema
    db.execute(text(f"SET search_path TO {tenant_schema}, public"))

    result = seed_canali(db, force)

    # Reset search path
    db.execute(text("SET search_path TO public"))

    return result
