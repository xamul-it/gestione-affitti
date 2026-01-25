"""
TassaSoggiornoService - Tourist Tax Calculation Service

Calculates tourist tax for stays based on municipality configuration.
Supports multiple calculation types:
- FISSO: Fixed amount per night per person
- PERCENTUALE: Percentage of nightly rate
- SCAGLIONI: Tiered rates by night count
- CATEGORIA: Based on property classification

Handles exemptions based on:
- Age (minors, elderly)
- Maximum taxable nights
- Special categories (disabled, residents, etc.)
"""
from decimal import Decimal
from datetime import date, datetime, timezone
from typing import Dict, List, Optional, Tuple
from sqlalchemy.orm import Session
import json
import logging

from ..models import (
    Soggiorno,
    OspiteSoggiorno,
    TassaSoggiornoConfig,
    TassaSoggiornoScaglione,
    TassaSoggiorno,
    TipoCalcoloTassa,
    StatoPagamentoTassa,
    StatoCompliance
)

logger = logging.getLogger(__name__)


class TassaSoggiornoService:
    """
    Tourist Tax Calculation Service

    Calculates tourist tax for stays and manages payment tracking.
    """

    def __init__(self, db: Session):
        self.db = db

    def get_config_attiva(self, comune_id: int, data_riferimento: date) -> Optional[TassaSoggiornoConfig]:
        """
        Get active tax configuration for a municipality and date.

        Args:
            comune_id: Municipality ID
            data_riferimento: Reference date

        Returns:
            Active TassaSoggiornoConfig or None
        """
        return self.db.query(TassaSoggiornoConfig).filter(
            TassaSoggiornoConfig.comune_id == comune_id,
            TassaSoggiornoConfig.attiva == True,
            TassaSoggiornoConfig.data_inizio_validita <= data_riferimento,
            (TassaSoggiornoConfig.data_fine_validita.is_(None)) |
            (TassaSoggiornoConfig.data_fine_validita >= data_riferimento)
        ).first()

    def calcola_tassa_soggiorno(self, soggiorno_id: int) -> TassaSoggiorno:
        """
        Calculate tourist tax for a stay.

        Creates or updates TassaSoggiorno record with calculation breakdown.

        Args:
            soggiorno_id: Stay ID

        Returns:
            TassaSoggiorno record

        Raises:
            ValueError if soggiorno not found or no valid config
        """
        soggiorno = self.db.query(Soggiorno).filter(
            Soggiorno.id == soggiorno_id
        ).first()

        if not soggiorno:
            raise ValueError(f"Soggiorno {soggiorno_id} non trovato")

        # Get municipality ID from property
        comune_id = None
        if soggiorno.unita_immobiliare:
            # Try to get comune_id from property (if available)
            comune_id = getattr(soggiorno.unita_immobiliare, 'comune_id', None)

        # For now, use first active config if no comune_id
        if not comune_id:
            config = self.db.query(TassaSoggiornoConfig).filter(
                TassaSoggiornoConfig.attiva == True,
                TassaSoggiornoConfig.data_inizio_validita <= soggiorno.data_checkin,
                (TassaSoggiornoConfig.data_fine_validita.is_(None)) |
                (TassaSoggiornoConfig.data_fine_validita >= soggiorno.data_checkin)
            ).first()
        else:
            config = self.get_config_attiva(comune_id, soggiorno.data_checkin)

        if not config:
            logger.warning(f"No active tax config found for soggiorno {soggiorno_id}")
            # Create zero-tax record
            return self._crea_tassa_zero(soggiorno, "Nessuna configurazione attiva")

        # Calculate based on type
        if config.tipo_calcolo == TipoCalcoloTassa.FISSO.value:
            importo, dettaglio = self._calcola_fisso(soggiorno, config)
        elif config.tipo_calcolo == TipoCalcoloTassa.PERCENTUALE.value:
            importo, dettaglio = self._calcola_percentuale(soggiorno, config)
        elif config.tipo_calcolo == TipoCalcoloTassa.SCAGLIONI.value:
            importo, dettaglio = self._calcola_scaglioni(soggiorno, config)
        else:
            importo, dettaglio = self._calcola_fisso(soggiorno, config)  # Default

        # Create or update TassaSoggiorno
        tassa = self.db.query(TassaSoggiorno).filter(
            TassaSoggiorno.soggiorno_id == soggiorno_id
        ).first()

        if tassa:
            # Update existing
            tassa.importo_totale = importo
            tassa.config_id = config.id
            tassa.numero_notti_totali = dettaglio['notti_totali']
            tassa.numero_notti_tassabili = dettaglio['notti_tassabili']
            tassa.numero_ospiti_totali = dettaglio['ospiti_totali']
            tassa.numero_ospiti_tassabili = dettaglio['ospiti_tassabili']
            tassa.numero_ospiti_esenti = dettaglio['ospiti_esenti']
            tassa.set_dettaglio_calcolo(dettaglio)
            tassa.data_calcolo = datetime.now(timezone.utc)
            tassa.stato = StatoPagamentoTassa.CALCOLATA.value
        else:
            # Create new
            tassa = TassaSoggiorno(
                soggiorno_id=soggiorno_id,
                config_id=config.id,
                importo_totale=importo,
                numero_notti_totali=dettaglio['notti_totali'],
                numero_notti_tassabili=dettaglio['notti_tassabili'],
                numero_ospiti_totali=dettaglio['ospiti_totali'],
                numero_ospiti_tassabili=dettaglio['ospiti_tassabili'],
                numero_ospiti_esenti=dettaglio['ospiti_esenti'],
                data_calcolo=datetime.now(timezone.utc),
                stato=StatoPagamentoTassa.CALCOLATA.value
            )
            tassa.set_dettaglio_calcolo(dettaglio)
            self.db.add(tassa)

        # Update soggiorno compliance status
        if importo == Decimal(0):
            soggiorno.stato_tassa_soggiorno = StatoCompliance.COMPLETATO.value
        else:
            soggiorno.stato_tassa_soggiorno = StatoCompliance.IN_ATTESA.value

        self.db.commit()
        self.db.refresh(tassa)

        logger.info(f"Calculated tax for soggiorno {soggiorno_id}: €{importo}")

        return tassa

    def _crea_tassa_zero(self, soggiorno: Soggiorno, motivo: str) -> TassaSoggiorno:
        """Create a zero-tax record"""
        tassa = TassaSoggiorno(
            soggiorno_id=soggiorno.id,
            importo_totale=Decimal(0),
            numero_notti_totali=soggiorno.notti,
            numero_notti_tassabili=0,
            numero_ospiti_totali=soggiorno.numero_ospiti_previsti,
            numero_ospiti_tassabili=0,
            numero_ospiti_esenti=soggiorno.numero_ospiti_previsti,
            data_calcolo=datetime.now(timezone.utc),
            stato=StatoPagamentoTassa.ESENTE.value,
            note=motivo
        )
        self.db.add(tassa)
        soggiorno.stato_tassa_soggiorno = StatoCompliance.COMPLETATO.value
        self.db.commit()
        self.db.refresh(tassa)
        return tassa

    def _calcola_esenzioni_ospiti(
        self,
        soggiorno: Soggiorno,
        config: TassaSoggiornoConfig
    ) -> Tuple[int, int, List[Dict]]:
        """
        Calculate guest exemptions based on configuration.

        Returns:
            Tuple of (ospiti_tassabili, ospiti_esenti, dettaglio_per_ospite)
        """
        ospiti = soggiorno.ospiti or []
        dettaglio = []
        ospiti_tassabili = 0
        ospiti_esenti = 0

        # If no guests registered, use expected count
        if not ospiti:
            return (soggiorno.numero_ospiti_previsti, 0, [])

        eta_min = config.eta_minima_soggetta or 0
        eta_max = config.eta_massima_soggetta

        for ospite in ospiti:
            ospite.calcola_esenzione_tassa(eta_min, eta_max)

            if ospite.esente_tassa:
                ospiti_esenti += 1
                dettaglio.append({
                    'nome': ospite.nome_completo,
                    'eta': ospite.eta,
                    'esente': True,
                    'motivo': ospite.motivo_esenzione,
                    'importo': 0
                })
            else:
                ospiti_tassabili += 1
                dettaglio.append({
                    'nome': ospite.nome_completo,
                    'eta': ospite.eta,
                    'esente': False,
                    'motivo': None
                })

        return (ospiti_tassabili, ospiti_esenti, dettaglio)

    def _calcola_fisso(
        self,
        soggiorno: Soggiorno,
        config: TassaSoggiornoConfig
    ) -> Tuple[Decimal, Dict]:
        """
        Calculate fixed-rate tourist tax.

        Formula: importo_fisso * notti_tassabili * ospiti_tassabili
        """
        notti_totali = soggiorno.notti
        notti_tassabili = min(notti_totali, config.notti_max_tassabili) if config.notti_max_tassabili else notti_totali

        ospiti_tassabili, ospiti_esenti, dettaglio_ospiti = self._calcola_esenzioni_ospiti(soggiorno, config)

        importo_notte = Decimal(config.importo_fisso or 0)
        importo_totale = importo_notte * notti_tassabili * ospiti_tassabili

        # Update ospite details with amounts
        for ospite_det in dettaglio_ospiti:
            if not ospite_det['esente']:
                ospite_det['notti'] = notti_tassabili
                ospite_det['importo'] = float(importo_notte * notti_tassabili)

        dettaglio = {
            'tipo_calcolo': 'FISSO',
            'importo_notte_persona': float(importo_notte),
            'notti_totali': notti_totali,
            'notti_tassabili': notti_tassabili,
            'ospiti_totali': soggiorno.numero_ospiti_previsti,
            'ospiti_tassabili': ospiti_tassabili,
            'ospiti_esenti': ospiti_esenti,
            'ospiti': dettaglio_ospiti,
            'formula': f"€{importo_notte} × {notti_tassabili} notti × {ospiti_tassabili} ospiti",
            'importo_totale': float(importo_totale)
        }

        return (importo_totale, dettaglio)

    def _calcola_percentuale(
        self,
        soggiorno: Soggiorno,
        config: TassaSoggiornoConfig
    ) -> Tuple[Decimal, Dict]:
        """
        Calculate percentage-based tourist tax.

        Formula: prezzo_notte * (percentuale/100) * notti_tassabili
        """
        notti_totali = soggiorno.notti
        notti_tassabili = min(notti_totali, config.notti_max_tassabili) if config.notti_max_tassabili else notti_totali

        # Get nightly rate from prenotazione
        prezzo_totale = Decimal(0)
        if soggiorno.prenotazione:
            prezzo_totale = soggiorno.prenotazione.prezzo_totale or Decimal(0)

        if prezzo_totale == 0 or notti_totali == 0:
            return (Decimal(0), {
                'tipo_calcolo': 'PERCENTUALE',
                'errore': 'Prezzo non disponibile',
                'notti_totali': notti_totali,
                'notti_tassabili': 0,
                'ospiti_totali': soggiorno.numero_ospiti_previsti,
                'ospiti_tassabili': 0,
                'ospiti_esenti': 0,
                'importo_totale': 0
            })

        prezzo_notte = prezzo_totale / notti_totali
        percentuale = Decimal(config.percentuale or 0) / 100

        importo_per_notte = prezzo_notte * percentuale

        # Apply max if configured
        if config.importo_massimo_percentuale:
            importo_per_notte = min(importo_per_notte, Decimal(config.importo_massimo_percentuale))

        importo_totale = importo_per_notte * notti_tassabili

        ospiti_tassabili, ospiti_esenti, dettaglio_ospiti = self._calcola_esenzioni_ospiti(soggiorno, config)

        dettaglio = {
            'tipo_calcolo': 'PERCENTUALE',
            'percentuale': float(config.percentuale or 0),
            'prezzo_totale_soggiorno': float(prezzo_totale),
            'prezzo_notte': float(prezzo_notte),
            'importo_notte': float(importo_per_notte),
            'notti_totali': notti_totali,
            'notti_tassabili': notti_tassabili,
            'ospiti_totali': soggiorno.numero_ospiti_previsti,
            'ospiti_tassabili': ospiti_tassabili,
            'ospiti_esenti': ospiti_esenti,
            'formula': f"€{prezzo_notte:.2f} × {config.percentuale}% × {notti_tassabili} notti",
            'importo_totale': float(importo_totale)
        }

        return (importo_totale, dettaglio)

    def _calcola_scaglioni(
        self,
        soggiorno: Soggiorno,
        config: TassaSoggiornoConfig
    ) -> Tuple[Decimal, Dict]:
        """
        Calculate tiered tourist tax.

        Uses different rates for different night ranges.
        """
        notti_totali = soggiorno.notti
        notti_tassabili = min(notti_totali, config.notti_max_tassabili) if config.notti_max_tassabili else notti_totali

        ospiti_tassabili, ospiti_esenti, dettaglio_ospiti = self._calcola_esenzioni_ospiti(soggiorno, config)

        # Get scaglioni
        scaglioni = self.db.query(TassaSoggiornoScaglione).filter(
            TassaSoggiornoScaglione.config_id == config.id
        ).order_by(TassaSoggiornoScaglione.notte_da).all()

        if not scaglioni:
            return (Decimal(0), {
                'tipo_calcolo': 'SCAGLIONI',
                'errore': 'Nessuno scaglione configurato',
                'importo_totale': 0
            })

        importo_totale = Decimal(0)
        scaglioni_applicati = []

        for scaglione in scaglioni:
            notte_da = scaglione.notte_da
            notte_a = scaglione.notte_a if scaglione.notte_a else notti_tassabili

            if notte_da > notti_tassabili:
                continue

            notte_a_eff = min(notte_a, notti_tassabili)
            notti_scaglione = notte_a_eff - notte_da + 1

            if notti_scaglione <= 0:
                continue

            subtotale = Decimal(scaglione.importo) * notti_scaglione * ospiti_tassabili
            importo_totale += subtotale

            scaglioni_applicati.append({
                'notti_range': f"{notte_da}-{notte_a_eff}",
                'notti_count': notti_scaglione,
                'importo_notte': float(scaglione.importo),
                'ospiti': ospiti_tassabili,
                'subtotale': float(subtotale)
            })

        dettaglio = {
            'tipo_calcolo': 'SCAGLIONI',
            'notti_totali': notti_totali,
            'notti_tassabili': notti_tassabili,
            'ospiti_totali': soggiorno.numero_ospiti_previsti,
            'ospiti_tassabili': ospiti_tassabili,
            'ospiti_esenti': ospiti_esenti,
            'scaglioni': scaglioni_applicati,
            'importo_totale': float(importo_totale)
        }

        return (importo_totale, dettaglio)

    def registra_pagamento(
        self,
        tassa_id: int,
        metodo: str,
        ricevuta_numero: Optional[str] = None
    ) -> TassaSoggiorno:
        """
        Register tax payment.

        Args:
            tassa_id: TassaSoggiorno ID
            metodo: Payment method (CONTANTI, CARTA, etc.)
            ricevuta_numero: Receipt number

        Returns:
            Updated TassaSoggiorno
        """
        tassa = self.db.query(TassaSoggiorno).filter(
            TassaSoggiorno.id == tassa_id
        ).first()

        if not tassa:
            raise ValueError(f"Tassa {tassa_id} non trovata")

        tassa.mark_pagata(metodo, ricevuta_numero)

        # Update soggiorno compliance
        if tassa.soggiorno:
            tassa.soggiorno.stato_tassa_soggiorno = StatoCompliance.COMPLETATO.value

        self.db.commit()
        self.db.refresh(tassa)

        logger.info(f"Payment registered for tassa {tassa_id}: €{tassa.importo_totale}")

        return tassa

    def get_riepilogo_periodo(
        self,
        data_inizio: date,
        data_fine: date,
        unita_immobiliare_id: Optional[int] = None
    ) -> Dict:
        """
        Get tax summary for a period.

        Returns aggregated data for municipal reporting.
        """
        query = self.db.query(TassaSoggiorno).join(Soggiorno).filter(
            Soggiorno.data_checkin >= data_inizio,
            Soggiorno.data_checkin <= data_fine
        )

        if unita_immobiliare_id:
            query = query.filter(Soggiorno.unita_immobiliare_id == unita_immobiliare_id)

        tasse = query.all()

        totale_dovuto = sum(t.importo_effettivo for t in tasse)
        totale_pagato = sum(t.importo_pagato or Decimal(0) for t in tasse)
        totale_residuo = totale_dovuto - totale_pagato

        return {
            'periodo': {
                'inizio': data_inizio.isoformat(),
                'fine': data_fine.isoformat()
            },
            'soggiorni_totali': len(tasse),
            'totale_dovuto': float(totale_dovuto),
            'totale_pagato': float(totale_pagato),
            'totale_residuo': float(totale_residuo),
            'soggiorni_per_stato': {
                'da_pagare': sum(1 for t in tasse if t.stato == StatoPagamentoTassa.CALCOLATA.value),
                'pagati': sum(1 for t in tasse if t.stato == StatoPagamentoTassa.PAGATA.value),
                'versati': sum(1 for t in tasse if t.stato == StatoPagamentoTassa.VERSATA.value),
                'esenti': sum(1 for t in tasse if t.stato == StatoPagamentoTassa.ESENTE.value),
            }
        }
