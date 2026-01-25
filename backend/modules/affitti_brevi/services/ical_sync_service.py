"""
ICalSyncService - iCal Calendar Synchronization

Handles importing bookings from external platforms via iCal feeds.
Supports:
- Booking.com
- Airbnb
- VRBO
- Other platforms with standard iCal

Key features:
- Automatic sync at configurable intervals
- Price extraction from event descriptions
- Deduplication based on UID
- Automatic Soggiorno creation for new bookings
"""
import requests
from icalendar import Calendar
from datetime import datetime, date, timedelta, timezone
from typing import List, Dict, Optional, Tuple
from sqlalchemy.orm import Session
from decimal import Decimal
import re
import logging
import json

from ..models import (
    CalendarioCanale,
    Prenotazione,
    Soggiorno,
    StatoSincronizzazione,
    StatoPrenotazione
)
from .soggiorno_service import SoggiornoService

logger = logging.getLogger(__name__)


class ICalSyncService:
    """
    iCal Synchronization Service

    Fetches and parses iCal feeds from booking platforms,
    creating/updating Prenotazione records.
    """

    def __init__(self, db: Session):
        self.db = db
        self.soggiorno_service = SoggiornoService(db)

    def fetch_ical(self, url: str, timeout: int = 30) -> str:
        """
        Fetch iCal data from URL.

        Args:
            url: iCal feed URL
            timeout: Request timeout in seconds

        Returns:
            Raw iCal data

        Raises:
            requests.RequestException on HTTP errors
        """
        try:
            response = requests.get(url, timeout=timeout)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            logger.error(f"Failed to fetch iCal from {url}: {e}")
            raise

    def parse_ical(self, ical_data: str) -> List[Dict]:
        """
        Parse iCal content and extract booking events.

        Args:
            ical_data: Raw iCal content

        Returns:
            List of event dictionaries
        """
        try:
            calendar = Calendar.from_ical(ical_data)
        except Exception as e:
            logger.error(f"Failed to parse iCal: {e}")
            raise ValueError(f"Invalid iCal format: {e}")

        events = []
        for component in calendar.walk():
            if component.name == "VEVENT":
                try:
                    event = self._extract_event(component)
                    if event:
                        events.append(event)
                except Exception as e:
                    logger.warning(f"Failed to extract event: {e}")
                    continue

        logger.info(f"Extracted {len(events)} events from iCal")
        return events

    def _extract_event(self, component) -> Optional[Dict]:
        """Extract booking data from VEVENT component"""
        summary = str(component.get('SUMMARY', ''))
        description = str(component.get('DESCRIPTION', ''))
        uid = str(component.get('UID', ''))

        dtstart = component.get('DTSTART')
        dtend = component.get('DTEND')

        if not dtstart or not dtend:
            return None

        # Extract dates
        checkin = dtstart.dt if hasattr(dtstart, 'dt') else dtstart
        checkout = dtend.dt if hasattr(dtend, 'dt') else dtend

        if isinstance(checkin, datetime):
            checkin = checkin.date()
        if isinstance(checkout, datetime):
            checkout = checkout.date()

        # Extract booking code
        codice = self._extract_booking_code(summary, uid)

        # Extract price
        prezzo = self._extract_price(description, summary)

        # Extract guest name
        nome_ospite = self._extract_guest_name(summary, description)

        return {
            'uid': uid,
            'codice_prenotazione': codice,
            'data_checkin': checkin,
            'data_checkout': checkout,
            'prezzo_totale': prezzo,
            'nome_ospite': nome_ospite,
            'summary': summary,
            'description': description,
            'raw_data': {
                'summary': summary,
                'description': description,
                'uid': uid
            }
        }

    def _extract_booking_code(self, summary: str, uid: str) -> str:
        """Extract booking code from summary or UID"""
        if summary:
            # Remove common prefixes
            code = summary.replace('Reserved', '').replace('Blocked', '').replace('Not available', '')
            code = code.replace('Prenotazione', '').replace('Booking', '').strip()

            # Look for alphanumeric code patterns
            match = re.search(r'[A-Z0-9]{6,}', code)
            if match:
                return match.group()[:100]

            if code:
                return code[:100]

        # Fallback to UID
        if uid:
            return uid.split('@')[0][:100]

        return f"SYNC_{datetime.now().strftime('%Y%m%d%H%M%S')}"

    def _extract_price(self, description: str, summary: str) -> Optional[Decimal]:
        """Extract price from event description or summary"""
        text = f"{description} {summary}"

        # Common price patterns
        patterns = [
            r'(?:€|EUR|EURO)\s*(\d+(?:[.,]\d{2})?)',
            r'(\d+(?:[.,]\d{2})?)\s*(?:€|EUR|EURO)',
            r'[Pp]rice[:\s]*(\d+(?:[.,]\d{2})?)',
            r'[Tt]otal[:\s]*(\d+(?:[.,]\d{2})?)',
            r'[Ii]mporto[:\s]*(\d+(?:[.,]\d{2})?)',
        ]

        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                price_str = match.group(1).replace(',', '.')
                try:
                    return Decimal(price_str)
                except:
                    pass

        return None

    def _extract_guest_name(self, summary: str, description: str) -> Optional[str]:
        """Extract guest name from event data"""
        # Try to find name patterns
        text = f"{summary} {description}"

        patterns = [
            r'(?:Guest|Ospite|Nome)[:\s]*([A-Za-z\s]+)',
            r'Prenotazione di ([A-Za-z\s]+)',
            r'Booking by ([A-Za-z\s]+)',
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                name = match.group(1).strip()
                if len(name) > 2:
                    return name[:200]

        return None

    def sync_calendario(self, calendario_id: int) -> Tuple[int, int, int, Optional[str]]:
        """
        Synchronize a single CalendarioCanale.

        Args:
            calendario_id: CalendarioCanale ID

        Returns:
            Tuple of (created, updated, skipped, error_message)
        """
        calendario = self.db.query(CalendarioCanale).filter(
            CalendarioCanale.id == calendario_id
        ).first()

        if not calendario:
            return (0, 0, 0, f"Calendario {calendario_id} non trovato")

        if not calendario.attivo or not calendario.url_ical:
            return (0, 0, 0, "Calendario non attivo o URL mancante")

        created = 0
        updated = 0
        skipped = 0
        error = None

        try:
            # Mark sync started
            calendario.mark_sync_started()
            self.db.commit()

            # Fetch and parse
            ical_data = self.fetch_ical(calendario.url_ical)
            events = self.parse_ical(ical_data)

            # Process events
            for event in events:
                try:
                    result = self._process_event(calendario, event)
                    if result == 'created':
                        created += 1
                    elif result == 'updated':
                        updated += 1
                    else:
                        skipped += 1
                except Exception as e:
                    logger.error(f"Error processing event {event.get('codice_prenotazione')}: {e}")
                    skipped += 1

            # Mark success
            calendario.mark_sync_success(created)
            self.db.commit()

            logger.info(f"Sync completed for calendario {calendario_id}: {created} created, {updated} updated, {skipped} skipped")

        except Exception as e:
            error = str(e)
            logger.error(f"Sync failed for calendario {calendario_id}: {error}")
            calendario.mark_sync_error(error)
            self.db.commit()

        return (created, updated, skipped, error)

    def _process_event(self, calendario: CalendarioCanale, event: Dict) -> str:
        """
        Process a single event, creating or updating Prenotazione.

        Returns:
            'created', 'updated', or 'skipped'
        """
        # Find existing by UID or code
        existing = self.db.query(Prenotazione).filter(
            Prenotazione.calendario_canale_id == calendario.id,
            Prenotazione.uid_ical == event['uid']
        ).first()

        if not existing:
            # Try by code
            existing = self.db.query(Prenotazione).filter(
                Prenotazione.calendario_canale_id == calendario.id,
                Prenotazione.codice_prenotazione == event['codice_prenotazione'],
                Prenotazione.data_checkin == event['data_checkin']
            ).first()

        if existing:
            # Update existing
            if (existing.data_checkout != event['data_checkout'] or
                (event['prezzo_totale'] and not existing.prezzo_totale)):

                existing.data_checkout = event['data_checkout']
                if event['prezzo_totale']:
                    existing.prezzo_totale = event['prezzo_totale']
                existing.ultima_modifica_ical = datetime.now(timezone.utc)
                existing.dati_originali = json.dumps(event['raw_data'])
                self.db.commit()
                return 'updated'
            return 'skipped'

        # Create new
        prenotazione = Prenotazione(
            unita_immobiliare_id=calendario.unita_immobiliare_id,
            calendario_canale_id=calendario.id,
            codice_prenotazione=event['codice_prenotazione'],
            data_checkin=event['data_checkin'],
            data_checkout=event['data_checkout'],
            numero_ospiti=1,  # Default, can be updated
            nome_ospite_principale=event.get('nome_ospite'),
            prezzo_totale=event.get('prezzo_totale'),
            stato=StatoPrenotazione.CONFERMATA.value,
            importata_da_ical=1,
            uid_ical=event['uid'],
            ultima_modifica_ical=datetime.now(timezone.utc),
            dati_originali=json.dumps(event['raw_data'])
        )

        self.db.add(prenotazione)
        self.db.commit()
        self.db.refresh(prenotazione)

        # Create soggiorno automatically
        try:
            self.soggiorno_service.crea_soggiorno_da_prenotazione(prenotazione)
        except Exception as e:
            logger.error(f"Failed to create soggiorno for prenotazione {prenotazione.id}: {e}")

        return 'created'

    def sync_all_calendari(self) -> Dict:
        """
        Synchronize all active calendari.

        Returns:
            Summary of sync results
        """
        calendari = self.db.query(CalendarioCanale).filter(
            CalendarioCanale.attivo == True,
            CalendarioCanale.sync_attiva == True,
            CalendarioCanale.url_ical.isnot(None)
        ).all()

        results = {
            'calendari_processati': 0,
            'prenotazioni_create': 0,
            'prenotazioni_aggiornate': 0,
            'prenotazioni_saltate': 0,
            'errori': 0,
            'dettagli': []
        }

        for calendario in calendari:
            created, updated, skipped, error = self.sync_calendario(calendario.id)

            results['calendari_processati'] += 1
            results['prenotazioni_create'] += created
            results['prenotazioni_aggiornate'] += updated
            results['prenotazioni_saltate'] += skipped

            if error:
                results['errori'] += 1

            results['dettagli'].append({
                'calendario_id': calendario.id,
                'unita_immobiliare_id': calendario.unita_immobiliare_id,
                'canale': calendario.canale.codice if calendario.canale else '?',
                'create': created,
                'aggiornate': updated,
                'saltate': skipped,
                'errore': error
            })

        logger.info(f"Sync all completed: {results['calendari_processati']} calendars, "
                   f"{results['prenotazioni_create']} created, {results['errori']} errors")

        return results

    def sync_calendari_pendenti(self) -> Dict:
        """
        Sync only calendars that are due for synchronization.

        Returns:
            Summary of sync results
        """
        calendari = self.db.query(CalendarioCanale).filter(
            CalendarioCanale.attivo == True,
            CalendarioCanale.sync_attiva == True,
            CalendarioCanale.url_ical.isnot(None)
        ).all()

        pendenti = [c for c in calendari if c.is_sync_pending]

        if not pendenti:
            return {'message': 'Nessun calendario da sincronizzare', 'calendari_processati': 0}

        results = {
            'calendari_processati': 0,
            'prenotazioni_create': 0,
            'prenotazioni_aggiornate': 0,
            'errori': 0,
            'dettagli': []
        }

        for calendario in pendenti:
            created, updated, skipped, error = self.sync_calendario(calendario.id)

            results['calendari_processati'] += 1
            results['prenotazioni_create'] += created
            results['prenotazioni_aggiornate'] += updated

            if error:
                results['errori'] += 1

            results['dettagli'].append({
                'calendario_id': calendario.id,
                'canale': calendario.canale.codice if calendario.canale else '?',
                'create': created,
                'errore': error
            })

        return results
