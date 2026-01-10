"""
iCal Parser Service

Parses iCal feeds from booking platforms (Booking.com, Airbnb, Vrbo)
and creates/updates Prenotazione records in the database.

Follows RFC 5545 (iCalendar) specification.
"""
import requests
from icalendar import Calendar
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from sqlalchemy.orm import Session
import logging

# Add modules directory to path for cross-module imports
import sys
import os
modules_dir = os.path.join(os.path.dirname(__file__), '../../../modules')
if modules_dir not in sys.path:
    sys.path.insert(0, modules_dir)

from affitti_brevi.models.calendario_ical import CalendarioIcal, StatoSincronizzazione
from affitti_brevi.models.prenotazione import Prenotazione, StatoPrenotazione, OriginePrenotazione
from affitti_brevi.services.price_extractor import PriceExtractor

logger = logging.getLogger(__name__)


class ICalParser:
    """
    iCal Parser for booking platform calendars

    Parses iCal feeds and extracts booking information including:
    - Check-in/check-out dates
    - Booking codes
    - Prices (from DESCRIPTION field)
    - Guest information (when available)
    """

    def __init__(self, db: Session):
        self.db = db
        self.price_extractor = PriceExtractor()

    def fetch_ical_data(self, url: str, timeout: int = 30) -> str:
        """
        Fetch iCal data from URL

        Args:
            url: iCal feed URL
            timeout: Request timeout in seconds

        Returns:
            Raw iCal data as string

        Raises:
            requests.RequestException: If HTTP request fails
        """
        try:
            response = requests.get(url, timeout=timeout)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            logger.error(f"Failed to fetch iCal from {url}: {str(e)}")
            raise

    def parse_ical_content(self, ical_data: str) -> Calendar:
        """
        Parse iCal content string into Calendar object

        Args:
            ical_data: Raw iCal data string

        Returns:
            Parsed Calendar object

        Raises:
            ValueError: If iCal content is invalid
        """
        try:
            return Calendar.from_ical(ical_data)
        except Exception as e:
            logger.error(f"Failed to parse iCal content: {str(e)}")
            raise ValueError(f"Invalid iCal format: {str(e)}")

    def extract_events(self, calendar: Calendar) -> List[Dict]:
        """
        Extract booking events from Calendar

        Args:
            calendar: Parsed Calendar object

        Returns:
            List of event dictionaries with extracted data
        """
        events = []

        for component in calendar.walk():
            if component.name == "VEVENT":
                try:
                    event_data = self._extract_event_data(component)
                    if event_data:
                        events.append(event_data)
                except Exception as e:
                    logger.warning(f"Failed to extract event data: {str(e)}")
                    continue

        logger.info(f"Extracted {len(events)} events from calendar")
        return events

    def _extract_event_data(self, event) -> Optional[Dict]:
        """
        Extract data from a single VEVENT component

        Args:
            event: VEVENT component

        Returns:
            Dictionary with event data or None if invalid
        """
        # Extract basic fields
        summary = str(event.get('SUMMARY', ''))
        description = str(event.get('DESCRIPTION', ''))
        uid = str(event.get('UID', ''))

        # Extract dates
        dtstart = event.get('DTSTART')
        dtend = event.get('DTEND')

        if not dtstart or not dtend:
            logger.warning(f"Event missing dates: {summary}")
            return None

        # Convert to datetime if needed
        checkin = dtstart.dt if hasattr(dtstart, 'dt') else dtstart
        checkout = dtend.dt if hasattr(dtend, 'dt') else dtend

        # Ensure dates are date objects (not datetime)
        if isinstance(checkin, datetime):
            checkin = checkin.date()
        if isinstance(checkout, datetime):
            checkout = checkout.date()

        # Extract booking code from SUMMARY or UID
        codice_prenotazione = self._extract_booking_code(summary, uid)

        # Extract price from DESCRIPTION
        prezzo_totale = self.price_extractor.extract_price(description, summary)

        return {
            'codice_prenotazione': codice_prenotazione,
            'data_checkin': checkin,
            'data_checkout': checkout,
            'summary': summary,
            'description': description,
            'uid': uid,
            'prezzo_totale': prezzo_totale,
        }

    def _extract_booking_code(self, summary: str, uid: str) -> str:
        """
        Extract booking code from summary or UID

        Args:
            summary: Event SUMMARY field
            uid: Event UID field

        Returns:
            Extracted booking code
        """
        # Try to extract from summary first (usually contains booking code)
        if summary and summary.strip():
            # Remove common prefixes
            code = summary.replace('Reserved', '').replace('Blocked', '').strip()
            if code:
                return code[:100]  # Limit to 100 chars

        # Fallback to UID (unique identifier)
        if uid:
            # Take first part of UID (before @)
            code = uid.split('@')[0]
            return code[:100]

        # Last resort: generate code from timestamp
        return f"SYNC_{datetime.now().strftime('%Y%m%d%H%M%S')}"

    def sync_calendario(self, calendario_id: int) -> Tuple[int, int, str]:
        """
        Synchronize a single calendario iCal

        Args:
            calendario_id: ID of CalendarioIcal to sync

        Returns:
            Tuple of (created_count, updated_count, error_message)
        """
        # Get calendario
        calendario = self.db.query(CalendarioIcal).filter(
            CalendarioIcal.id == calendario_id
        ).first()

        if not calendario:
            return (0, 0, f"Calendario {calendario_id} not found")

        if not calendario.attivo:
            return (0, 0, "Calendario not active")

        created_count = 0
        updated_count = 0
        error_message = None

        try:
            # Update status to IN_CORSO
            calendario.stato_sincronizzazione = StatoSincronizzazione.IN_CORSO
            self.db.commit()

            # Fetch and parse iCal
            ical_data = self.fetch_ical_data(calendario.url_ical)
            calendar = self.parse_ical_content(ical_data)
            events = self.extract_events(calendar)

            # Map platform to enum
            portale_map = {
                'BOOKING_COM': OriginePrenotazione.BOOKING_COM,
                'AIRBNB': OriginePrenotazione.AIRBNB,
                'VRBO': OriginePrenotazione.VRBO,
                'ALTRO': OriginePrenotazione.ALTRO,
            }
            portale_origine = portale_map.get(calendario.portale.value, OriginePrenotazione.ALTRO)

            # Create/update prenotazioni
            for event in events:
                try:
                    existing = self.db.query(Prenotazione).filter(
                        Prenotazione.codice_prenotazione == event['codice_prenotazione'],
                        Prenotazione.portale_origine == portale_origine,
                        Prenotazione.unita_immobiliare_id == calendario.unita_immobiliare_id
                    ).first()

                    if existing:
                        # Update existing prenotazione
                        existing.data_checkin = event['data_checkin']
                        existing.data_checkout = event['data_checkout']
                        if event['prezzo_totale']:
                            existing.prezzo_totale = event['prezzo_totale']
                        existing.ultima_modifica_ical = datetime.now()
                        updated_count += 1
                    else:
                        # Create new prenotazione
                        new_prenotazione = Prenotazione(
                            unita_immobiliare_id=calendario.unita_immobiliare_id,
                            calendario_ical_id=calendario.id,
                            codice_prenotazione=event['codice_prenotazione'],
                            portale_origine=portale_origine,
                            data_checkin=event['data_checkin'],
                            data_checkout=event['data_checkout'],
                            numero_ospiti=1,  # Default, can be updated manually
                            prezzo_totale=event['prezzo_totale'],
                            stato=StatoPrenotazione.CONFERMATA,
                            importata_da_ical=1,
                            ultima_modifica_ical=datetime.now()
                        )
                        self.db.add(new_prenotazione)
                        created_count += 1
                except Exception as e:
                    logger.error(f"Failed to process event {event.get('codice_prenotazione')}: {str(e)}")
                    continue

            # Commit all changes
            self.db.commit()

            # Update calendario status to SUCCESSO
            calendario.stato_sincronizzazione = StatoSincronizzazione.SUCCESSO
            calendario.ultima_sincronizzazione = datetime.now()
            calendario.errore_sincronizzazione = None
            self.db.commit()

        except Exception as e:
            error_message = str(e)
            logger.error(f"Sync failed for calendario {calendario_id}: {error_message}")

            # Update status to ERRORE
            calendario.stato_sincronizzazione = StatoSincronizzazione.ERRORE
            calendario.errore_sincronizzazione = error_message[:500]  # Limit error message length
            self.db.commit()

        return (created_count, updated_count, error_message or "")

    def sync_all_calendari(self) -> Dict[str, int]:
        """
        Synchronize all active calendari

        Returns:
            Dictionary with sync statistics
        """
        calendari = self.db.query(CalendarioIcal).filter(
            CalendarioIcal.attivo == True
        ).all()

        total_created = 0
        total_updated = 0
        total_errors = 0

        for calendario in calendari:
            created, updated, error = self.sync_calendario(calendario.id)
            total_created += created
            total_updated += updated
            if error:
                total_errors += 1

        logger.info(f"Sync completed: {total_created} created, {total_updated} updated, {total_errors} errors")

        return {
            'calendari_processed': len(calendari),
            'prenotazioni_created': total_created,
            'prenotazioni_updated': total_updated,
            'errors': total_errors
        }
