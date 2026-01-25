"""
CalendarioUnificatoService - Unified Calendar View Service

Provides a unified calendar view that aggregates all channels for each property.
Key features:
- Single calendar per property aggregating all channels
- Status per channel visible in the same view
- Color/symbol conventions (A=red/Airbnb, B=blue/Booking, D=green/Direct)
- Conflict detection (no overbooking allowed)
- States: LIBERO (border), PRENOTATO (filled ●), CHIUSO (X)
- Aggregate states: Occupato, Libero, Non disponibile, Conflitto

Based on analysis requirements:
- One unified view per property
- Per-channel status visible in same cell
- No overbooking (conflicts are flagged for resolution)
- No internal technical closures (only channel-reported closures)
"""
from datetime import date, timedelta
from typing import List, Dict, Optional, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
import logging

from ..models import (
    Canale,
    CalendarioCanale,
    Prenotazione,
    Soggiorno,
    BloccoCalendario,
    StatoPrenotazione,
    StatoSoggiorno
)

logger = logging.getLogger(__name__)


class StatoGiornaliero:
    """Status constants for calendar cells"""
    LIBERO = "LIBERO"           # Available (border only)
    PRENOTATO = "PRENOTATO"     # Booked (filled ●)
    CHIUSO = "CHIUSO"           # Closed/unavailable (X)


class StatoAggregato:
    """Aggregate status for a property on a day"""
    LIBERO = "LIBERO"               # All channels free
    OCCUPATO = "OCCUPATO"           # At least one channel has booking
    NON_DISPONIBILE = "NON_DISPONIBILE"  # All channels closed
    CONFLITTO = "CONFLITTO"         # Multiple overlapping bookings (!!)


class CalendarioUnificatoService:
    """
    Unified Calendar Service

    Generates the unified calendar view as specified in the analysis:
    - One calendar per property
    - All channels visible per cell
    - Clear status indication with colors and symbols
    """

    def __init__(self, db: Session):
        self.db = db
        self._canali_cache: Dict[int, Canale] = {}

    def get_canali(self) -> List[Canale]:
        """Get all active channels"""
        return self.db.query(Canale).filter(Canale.attivo == True).all()

    def _get_canale(self, canale_id: int) -> Optional[Canale]:
        """Get channel by ID (cached)"""
        if canale_id not in self._canali_cache:
            canale = self.db.query(Canale).filter(Canale.id == canale_id).first()
            if canale:
                self._canali_cache[canale_id] = canale
        return self._canali_cache.get(canale_id)

    def get_calendario_overview(
        self,
        data_inizio: date,
        data_fine: date,
        unita_immobiliare_ids: Optional[List[int]] = None,
        include_dettagli: bool = True
    ) -> Dict[str, Any]:
        """
        Get unified calendar overview for the specified period.

        Returns a structure with:
        - legenda: Channel legend with colors and symbols
        - proprieta: List of properties with their daily statuses
        - conflitti: List of detected conflicts

        Args:
            data_inizio: Start date
            data_fine: End date
            unita_immobiliare_ids: Optional list of property IDs to filter
            include_dettagli: Include booking details in response

        Returns:
            Dict with legenda, proprieta, conflitti
        """
        # Get legend (channels)
        canali = self.get_canali()
        legenda = {
            "canali": [
                {
                    "id": c.id,
                    "codice": c.codice,
                    "nome": c.nome,
                    "colore": c.colore,
                    "simbolo": c.simbolo
                }
                for c in canali
            ],
            "stati": {
                StatoGiornaliero.LIBERO: {"descrizione": "Disponibile", "simbolo": "○"},
                StatoGiornaliero.PRENOTATO: {"descrizione": "Prenotato", "simbolo": "●"},
                StatoGiornaliero.CHIUSO: {"descrizione": "Non disponibile", "simbolo": "✕"},
            },
            "stati_aggregati": {
                StatoAggregato.LIBERO: {"descrizione": "Disponibile su tutti i canali", "colore": "#28A745"},
                StatoAggregato.OCCUPATO: {"descrizione": "Occupato", "colore": "#DC3545"},
                StatoAggregato.NON_DISPONIBILE: {"descrizione": "Non disponibile", "colore": "#6C757D"},
                StatoAggregato.CONFLITTO: {"descrizione": "Conflitto - richiede azione", "colore": "#FFC107"},
            }
        }

        # Get property-channel configurations
        query = self.db.query(CalendarioCanale).filter(CalendarioCanale.attivo == True)
        if unita_immobiliare_ids:
            query = query.filter(CalendarioCanale.unita_immobiliare_id.in_(unita_immobiliare_ids))

        calendari = query.all()

        # Group by property
        proprieta_map: Dict[int, Dict] = {}

        for calendario in calendari:
            immobile_id = calendario.unita_immobiliare_id
            if immobile_id not in proprieta_map:
                proprieta_map[immobile_id] = {
                    "unita_immobiliare_id": immobile_id,
                    "nome": calendario.unita_immobiliare.denominazione if calendario.unita_immobiliare else f"Immobile #{immobile_id}",
                    "canali_attivi": [],
                    "giorni": {}
                }
            proprieta_map[immobile_id]["canali_attivi"].append({
                "canale_id": calendario.canale_id,
                "codice": calendario.canale.codice if calendario.canale else "?",
                "colore": calendario.canale.colore if calendario.canale else "#808080",
                "simbolo": calendario.canale.simbolo if calendario.canale else "?"
            })

        # Generate date range
        date_range = []
        current_date = data_inizio
        while current_date <= data_fine:
            date_range.append(current_date)
            current_date += timedelta(days=1)

        # Get all prenotazioni in the period
        prenotazioni = self.db.query(Prenotazione).filter(
            Prenotazione.stato != StatoPrenotazione.CANCELLATA.value,
            Prenotazione.data_checkout > data_inizio,
            Prenotazione.data_checkin <= data_fine
        )
        if unita_immobiliare_ids:
            prenotazioni = prenotazioni.filter(
                Prenotazione.unita_immobiliare_id.in_(unita_immobiliare_ids)
            )
        prenotazioni = prenotazioni.all()

        # Get all blocchi in the period
        blocchi = self.db.query(BloccoCalendario).filter(
            BloccoCalendario.attivo == True,
            BloccoCalendario.data_fine >= data_inizio,
            BloccoCalendario.data_inizio <= data_fine
        )
        if unita_immobiliare_ids:
            blocchi = blocchi.filter(
                BloccoCalendario.unita_immobiliare_id.in_(unita_immobiliare_ids)
            )
        blocchi = blocchi.all()

        # Build day-by-day status for each property
        conflitti = []

        for immobile_id, prop_data in proprieta_map.items():
            canali_ids = [c["canale_id"] for c in prop_data["canali_attivi"]]

            for giorno in date_range:
                giorno_key = giorno.isoformat()

                # Initialize day data
                giorno_data = {
                    "data": giorno_key,
                    "canali": {},
                    "stato_aggregato": StatoAggregato.LIBERO,
                    "prenotazioni": [],
                    "richiede_azione": False
                }

                # Check each channel
                prenotazioni_giorno = []

                for canale_info in prop_data["canali_attivi"]:
                    canale_id = canale_info["canale_id"]
                    canale_stato = StatoGiornaliero.LIBERO
                    canale_prenotazione = None

                    # Find prenotazione for this channel on this day
                    for pren in prenotazioni:
                        if (pren.unita_immobiliare_id == immobile_id and
                            pren.calendario_canale and
                            pren.calendario_canale.canale_id == canale_id and
                            pren.data_checkin <= giorno < pren.data_checkout):

                            canale_stato = StatoGiornaliero.PRENOTATO
                            canale_prenotazione = pren
                            prenotazioni_giorno.append(pren)
                            break

                    # Check for blocchi
                    if canale_stato == StatoGiornaliero.LIBERO:
                        for blocco in blocchi:
                            if (blocco.unita_immobiliare_id == immobile_id and
                                blocco.copre_data(giorno) and
                                blocco.copre_canale(canale_id)):
                                canale_stato = StatoGiornaliero.CHIUSO
                                break

                    # Store channel status
                    giorno_data["canali"][canale_info["codice"]] = {
                        "stato": canale_stato,
                        "colore": canale_info["colore"],
                        "simbolo": canale_info["simbolo"]
                    }

                    if canale_prenotazione and include_dettagli:
                        giorno_data["canali"][canale_info["codice"]]["prenotazione"] = {
                            "id": canale_prenotazione.id,
                            "codice": canale_prenotazione.codice_prenotazione,
                            "ospiti": canale_prenotazione.numero_ospiti,
                            "nome_ospite": canale_prenotazione.nome_ospite_principale
                        }

                # Calculate aggregate status
                stati_canali = [c["stato"] for c in giorno_data["canali"].values()]

                if len(prenotazioni_giorno) > 1:
                    # Multiple bookings = conflict
                    giorno_data["stato_aggregato"] = StatoAggregato.CONFLITTO
                    giorno_data["richiede_azione"] = True
                    conflitti.append({
                        "unita_immobiliare_id": immobile_id,
                        "data": giorno_key,
                        "prenotazioni": [
                            {
                                "id": p.id,
                                "codice": p.codice_prenotazione,
                                "canale": p.canale_codice if hasattr(p, 'canale_codice') else "?",
                                "checkin": p.data_checkin.isoformat(),
                                "checkout": p.data_checkout.isoformat()
                            }
                            for p in prenotazioni_giorno
                        ]
                    })
                elif StatoGiornaliero.PRENOTATO in stati_canali:
                    giorno_data["stato_aggregato"] = StatoAggregato.OCCUPATO
                elif all(s == StatoGiornaliero.CHIUSO for s in stati_canali):
                    giorno_data["stato_aggregato"] = StatoAggregato.NON_DISPONIBILE
                else:
                    giorno_data["stato_aggregato"] = StatoAggregato.LIBERO

                prop_data["giorni"][giorno_key] = giorno_data

        return {
            "periodo": {
                "inizio": data_inizio.isoformat(),
                "fine": data_fine.isoformat(),
                "giorni": len(date_range)
            },
            "legenda": legenda,
            "proprieta": list(proprieta_map.values()),
            "conflitti": {
                "totale": len(conflitti),
                "dettagli": conflitti
            }
        }

    def get_conflitti(
        self,
        data_inizio: Optional[date] = None,
        data_fine: Optional[date] = None,
        unita_immobiliare_id: Optional[int] = None
    ) -> List[Dict]:
        """
        Detect booking conflicts (same property booked on multiple channels for same dates).

        Args:
            data_inizio: Optional start date filter
            data_fine: Optional end date filter
            unita_immobiliare_id: Optional property filter

        Returns:
            List of conflict details
        """
        query = self.db.query(Prenotazione).filter(
            Prenotazione.stato != StatoPrenotazione.CANCELLATA.value
        )

        if unita_immobiliare_id:
            query = query.filter(Prenotazione.unita_immobiliare_id == unita_immobiliare_id)
        if data_inizio:
            query = query.filter(Prenotazione.data_checkout > data_inizio)
        if data_fine:
            query = query.filter(Prenotazione.data_checkin <= data_fine)

        prenotazioni = query.order_by(
            Prenotazione.unita_immobiliare_id,
            Prenotazione.data_checkin
        ).all()

        conflitti = []
        checked = set()

        for i, pren1 in enumerate(prenotazioni):
            for pren2 in prenotazioni[i+1:]:
                # Skip if different properties
                if pren1.unita_immobiliare_id != pren2.unita_immobiliare_id:
                    continue

                # Skip if same channel (not a conflict)
                if (pren1.calendario_canale_id and pren2.calendario_canale_id and
                    pren1.calendario_canale_id == pren2.calendario_canale_id):
                    continue

                # Check date overlap
                if pren1.data_checkin < pren2.data_checkout and pren2.data_checkin < pren1.data_checkout:
                    conflict_key = tuple(sorted([pren1.id, pren2.id]))

                    if conflict_key not in checked:
                        checked.add(conflict_key)

                        overlap_start = max(pren1.data_checkin, pren2.data_checkin)
                        overlap_end = min(pren1.data_checkout, pren2.data_checkout)

                        conflitti.append({
                            "unita_immobiliare_id": pren1.unita_immobiliare_id,
                            "overlap_start": overlap_start.isoformat(),
                            "overlap_end": overlap_end.isoformat(),
                            "overlap_days": (overlap_end - overlap_start).days,
                            "prenotazioni": [
                                {
                                    "id": pren1.id,
                                    "codice": pren1.codice_prenotazione,
                                    "canale": pren1.canale_codice,
                                    "checkin": pren1.data_checkin.isoformat(),
                                    "checkout": pren1.data_checkout.isoformat(),
                                    "stato": pren1.stato
                                },
                                {
                                    "id": pren2.id,
                                    "codice": pren2.codice_prenotazione,
                                    "canale": pren2.canale_codice,
                                    "checkin": pren2.data_checkin.isoformat(),
                                    "checkout": pren2.data_checkout.isoformat(),
                                    "stato": pren2.stato
                                }
                            ]
                        })

        return conflitti

    def risolvi_conflitto(
        self,
        prenotazione_id_da_mantenere: int,
        prenotazione_id_da_cancellare: int
    ) -> Dict:
        """
        Resolve a booking conflict by canceling one of the bookings.

        Args:
            prenotazione_id_da_mantenere: ID of booking to keep
            prenotazione_id_da_cancellare: ID of booking to cancel

        Returns:
            Result of resolution
        """
        pren_keep = self.db.query(Prenotazione).filter(
            Prenotazione.id == prenotazione_id_da_mantenere
        ).first()
        pren_cancel = self.db.query(Prenotazione).filter(
            Prenotazione.id == prenotazione_id_da_cancellare
        ).first()

        if not pren_keep or not pren_cancel:
            raise ValueError("Prenotazione non trovata")

        # Cancel the booking
        pren_cancel.stato = StatoPrenotazione.CANCELLATA.value

        # If there's a soggiorno, cancel it too
        if pren_cancel.soggiorno:
            pren_cancel.soggiorno.stato = StatoSoggiorno.ANNULLATO.value
            pren_cancel.soggiorno.valido = False

        self.db.commit()

        logger.info(f"Conflitto risolto: mantenuta #{prenotazione_id_da_mantenere}, cancellata #{prenotazione_id_da_cancellare}")

        return {
            "successo": True,
            "prenotazione_mantenuta": prenotazione_id_da_mantenere,
            "prenotazione_cancellata": prenotazione_id_da_cancellare
        }

    def get_disponibilita_proprieta(
        self,
        unita_immobiliare_id: int,
        data_inizio: date,
        data_fine: date
    ) -> List[Dict]:
        """
        Get availability for a specific property over a date range.

        Returns list of days with their status and any bookings.
        """
        overview = self.get_calendario_overview(
            data_inizio=data_inizio,
            data_fine=data_fine,
            unita_immobiliare_ids=[unita_immobiliare_id],
            include_dettagli=True
        )

        if not overview["proprieta"]:
            return []

        prop = overview["proprieta"][0]
        return [
            {
                "data": data,
                **giorno_data
            }
            for data, giorno_data in sorted(prop["giorni"].items())
        ]
