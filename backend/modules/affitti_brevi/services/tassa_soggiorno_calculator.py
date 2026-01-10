"""
Tourist Tax Calculator Service

Calculates tourist tax (tassa di soggiorno) based on municipality configuration.
Supports three calculation types:
- FISSO: Fixed amount per night per person
- PERCENTUALE: Percentage of nightly rate
- SCAGLIONI: Tiered rates by night count

Handles exemptions (age, max nights) and stores detailed breakdown.
"""
from decimal import Decimal
from typing import Dict, List, Optional, Tuple
from datetime import date
import logging
from sqlalchemy.orm import Session

# Add modules directory to path for cross-module imports
import sys
import os
modules_dir = os.path.join(os.path.dirname(__file__), '../../../modules')
if modules_dir not in sys.path:
    sys.path.insert(0, modules_dir)

from affitti_brevi.models.tassa_soggiorno_config import TassaSoggiornoConfig, TipoCalcoloTassa
from affitti_brevi.models.tassa_soggiorno_scaglione import TassaSoggiornoScaglione
from affitti_brevi.models.tassa_prenotazione import TassaPrenotazione
from affitti_brevi.models.prenotazione import Prenotazione

logger = logging.getLogger(__name__)


class TassaSoggiornoCalculator:
    """
    Tourist Tax Calculator

    Calculates tourist tax for bookings based on municipality configuration.
    """

    def __init__(self, db: Session):
        self.db = db

    def get_active_config_for_comune(self, comune_id: int, reference_date: date) -> Optional[TassaSoggiornoConfig]:
        """
        Get active tax configuration for a municipality

        Args:
            comune_id: Municipality ID
            reference_date: Date to check configuration validity

        Returns:
            Active TassaSoggiornoConfig or None
        """
        config = self.db.query(TassaSoggiornoConfig).filter(
            TassaSoggiornoConfig.comune_id == comune_id,
            TassaSoggiornoConfig.attiva == True,
            TassaSoggiornoConfig.data_inizio_validita <= reference_date,
            (TassaSoggiornoConfig.data_fine_validita.is_(None)) |
            (TassaSoggiornoConfig.data_fine_validita >= reference_date)
        ).first()

        return config

    def calculate_for_prenotazione(self, prenotazione: Prenotazione) -> Tuple[Decimal, Dict]:
        """
        Calculate tourist tax for a booking

        Args:
            prenotazione: Booking to calculate tax for

        Returns:
            Tuple of (total_amount, calculation_breakdown)

        Raises:
            ValueError: If no active config found or calculation fails
        """
        # Get property to determine comune_id
        # Note: In real implementation, get comune_id from unita_immobiliare
        # For now, we'll use a placeholder
        comune_id = 1  # TODO: Get from prenotazione.unita_immobiliare.comune_id

        # Get active config
        config = self.get_active_config_for_comune(comune_id, prenotazione.data_checkin)

        if not config:
            raise ValueError(f"No active tax configuration found for comune_id={comune_id}")

        # Calculate based on tipo_calcolo
        if config.tipo_calcolo == TipoCalcoloTassa.FISSO:
            return self._calculate_fisso(prenotazione, config)
        elif config.tipo_calcolo == TipoCalcoloTassa.PERCENTUALE:
            return self._calculate_percentuale(prenotazione, config)
        elif config.tipo_calcolo == TipoCalcoloTassa.SCAGLIONI:
            return self._calculate_scaglioni(prenotazione, config)
        else:
            raise ValueError(f"Unknown calculation type: {config.tipo_calcolo}")

    def _calculate_fisso(self, prenotazione: Prenotazione, config: TassaSoggiornoConfig) -> Tuple[Decimal, Dict]:
        """
        Calculate tax with fixed amount per night per person

        Formula: importo_fisso * notti_tassabili * ospiti_tassabili
        """
        notti_totali = prenotazione.notti
        ospiti_totali = prenotazione.numero_ospiti

        # Apply max nights exemption
        notti_tassabili = min(notti_totali, config.notti_max) if config.notti_max else notti_totali

        # Apply age exemptions (simplified - assumes all guests are taxable)
        # In real implementation, would need guest ages from OspitePrenotazione
        ospiti_tassabili = ospiti_totali
        ospiti_esenti = 0

        # Calculate total
        importo_totale = Decimal(config.importo_fisso) * notti_tassabili * ospiti_tassabili

        # Build breakdown
        breakdown = {
            "tipo_calcolo": "FISSO",
            "importo_fisso": float(config.importo_fisso),
            "notti_totali": notti_totali,
            "notti_tassabili": notti_tassabili,
            "ospiti_totali": ospiti_totali,
            "ospiti_tassabili": ospiti_tassabili,
            "ospiti_esenti": ospiti_esenti,
            "calcolo": f"{config.importo_fisso} × {notti_tassabili} notti × {ospiti_tassabili} ospiti",
            "importo_totale": float(importo_totale)
        }

        logger.info(f"Tax calculated (FISSO) for booking {prenotazione.id}: €{importo_totale}")
        return (importo_totale, breakdown)

    def _calculate_percentuale(self, prenotazione: Prenotazione, config: TassaSoggiornoConfig) -> Tuple[Decimal, Dict]:
        """
        Calculate tax as percentage of nightly rate

        Formula: prezzo_notte * (percentuale/100) * notti_tassabili
        """
        notti_totali = prenotazione.notti
        ospiti_totali = prenotazione.numero_ospiti

        # Get nightly rate
        prezzo_totale = prenotazione.prezzo_manuale if prenotazione.prezzo_manuale else prenotazione.prezzo_totale

        if not prezzo_totale or prezzo_totale == 0:
            raise ValueError(f"Booking {prenotazione.id} has no price, cannot calculate percentage tax")

        prezzo_notte = Decimal(prezzo_totale) / notti_totali

        # Apply max nights exemption
        notti_tassabili = min(notti_totali, config.notti_max) if config.notti_max else notti_totali

        # Calculate total
        importo_per_notte = prezzo_notte * (Decimal(config.percentuale) / 100)
        importo_totale = importo_per_notte * notti_tassabili

        # Build breakdown
        breakdown = {
            "tipo_calcolo": "PERCENTUALE",
            "percentuale": float(config.percentuale),
            "prezzo_totale_booking": float(prezzo_totale),
            "prezzo_notte": float(prezzo_notte),
            "notti_totali": notti_totali,
            "notti_tassabili": notti_tassabili,
            "ospiti_totali": ospiti_totali,
            "importo_per_notte": float(importo_per_notte),
            "calcolo": f"{prezzo_notte} × {config.percentuale}% × {notti_tassabili} notti",
            "importo_totale": float(importo_totale)
        }

        logger.info(f"Tax calculated (PERCENTUALE) for booking {prenotazione.id}: €{importo_totale}")
        return (importo_totale, breakdown)

    def _calculate_scaglioni(self, prenotazione: Prenotazione, config: TassaSoggiornoConfig) -> Tuple[Decimal, Dict]:
        """
        Calculate tax with tiered rates by night count

        Example:
            Night 1-5:  €2.50 per night per person
            Night 6-10: €1.50 per night per person
            Night 11+:  €1.00 per night per person
        """
        notti_totali = prenotazione.notti
        ospiti_totali = prenotazione.numero_ospiti

        # Apply max nights exemption
        notti_tassabili = min(notti_totali, config.notti_max) if config.notti_max else notti_totali

        # Apply age exemptions (simplified)
        ospiti_tassabili = ospiti_totali
        ospiti_esenti = 0

        # Get scaglioni
        scaglioni = self.db.query(TassaSoggiornoScaglione).filter(
            TassaSoggiornoScaglione.config_id == config.id
        ).order_by(TassaSoggiornoScaglione.notte_da).all()

        if not scaglioni:
            raise ValueError(f"Config {config.id} has tipo_calcolo=SCAGLIONI but no scaglioni defined")

        # Calculate for each tier
        importo_totale = Decimal(0)
        scaglioni_breakdown = []

        for scaglione in scaglioni:
            # Determine how many nights fall in this tier
            notte_da = scaglione.notte_da
            notte_a = scaglione.notte_a if scaglione.notte_a else notti_tassabili

            # Only consider nights up to notti_tassabili
            notte_a_effective = min(notte_a, notti_tassabili)

            if notte_da > notti_tassabili:
                # This tier starts after our max taxable nights
                continue

            notti_in_scaglione = notte_a_effective - notte_da + 1

            if notti_in_scaglione <= 0:
                continue

            # Calculate for this tier
            subtotale = Decimal(scaglione.importo) * notti_in_scaglione * ospiti_tassabili
            importo_totale += subtotale

            notte_a_str = str(notte_a_effective) if scaglione.notte_a else '∞'
            scaglioni_breakdown.append({
                "notti": f"{notte_da}-{notte_a_str}",
                "notti_count": notti_in_scaglione,
                "importo_notte": float(scaglione.importo),
                "ospiti": ospiti_tassabili,
                "calcolo": f"{scaglione.importo} × {notti_in_scaglione} notti × {ospiti_tassabili} ospiti",
                "subtotale": float(subtotale)
            })

        # Build breakdown
        breakdown = {
            "tipo_calcolo": "SCAGLIONI",
            "notti_totali": notti_totali,
            "notti_tassabili": notti_tassabili,
            "ospiti_totali": ospiti_totali,
            "ospiti_tassabili": ospiti_tassabili,
            "ospiti_esenti": ospiti_esenti,
            "scaglioni": scaglioni_breakdown,
            "importo_totale": float(importo_totale)
        }

        logger.info(f"Tax calculated (SCAGLIONI) for booking {prenotazione.id}: €{importo_totale}")
        return (importo_totale, breakdown)

    def create_or_update_tassa(self, prenotazione_id: int) -> TassaPrenotazione:
        """
        Create or update TassaPrenotazione for a booking

        Args:
            prenotazione_id: ID of booking to calculate tax for

        Returns:
            Created/updated TassaPrenotazione

        Raises:
            ValueError: If booking not found or calculation fails
        """
        # Get prenotazione
        prenotazione = self.db.query(Prenotazione).filter(
            Prenotazione.id == prenotazione_id
        ).first()

        if not prenotazione:
            raise ValueError(f"Prenotazione {prenotazione_id} not found")

        # Calculate tax
        try:
            importo_totale, breakdown = self.calculate_for_prenotazione(prenotazione)

            # Get config used
            comune_id = 1  # TODO: Get from prenotazione.unita_immobiliare.comune_id
            config = self.get_active_config_for_comune(comune_id, prenotazione.data_checkin)

            # Check if tassa already exists
            existing = self.db.query(TassaPrenotazione).filter(
                TassaPrenotazione.prenotazione_id == prenotazione_id
            ).first()

            if existing:
                # Update existing
                existing.importo_totale = importo_totale
                existing.numero_ospiti_tassabili = breakdown.get('ospiti_tassabili', prenotazione.numero_ospiti)
                existing.numero_notti_tassabili = breakdown.get('notti_tassabili', prenotazione.notti)
                existing.dettaglio_calcolo = breakdown
                existing.config_id = config.id
                tassa = existing
            else:
                # Create new
                tassa = TassaPrenotazione(
                    prenotazione_id=prenotazione_id,
                    config_id=config.id,
                    importo_totale=importo_totale,
                    numero_ospiti_tassabili=breakdown.get('ospiti_tassabili', prenotazione.numero_ospiti),
                    numero_notti_tassabili=breakdown.get('notti_tassabili', prenotazione.notti),
                    dettaglio_calcolo=breakdown
                )
                self.db.add(tassa)

            self.db.commit()
            self.db.refresh(tassa)

            logger.info(f"TassaPrenotazione {'updated' if existing else 'created'} for booking {prenotazione_id}")
            return tassa

        except Exception as e:
            logger.error(f"Failed to calculate tax for booking {prenotazione_id}: {str(e)}")
            raise
