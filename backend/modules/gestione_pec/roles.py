"""
Definizione dei ruoli del modulo Gestione PEC.

Questi ruoli vengono registrati dinamicamente nel sistema al caricamento del modulo.
"""
import logging
from sqlalchemy.orm import Session
from app.core.services.role_registry import RoleRegistry

logger = logging.getLogger(__name__)

# ID del modulo
MODULE_ID = "gestione_pec"

# Definizione dei ruoli gestiti da questo modulo
ROLES = [
    {
        "codice": "pec_admin",
        "nome_display": "PEC Amministratore",
        "descrizione": "Configura caselle PEC e gestisce gli utenti abilitati",
        "attivo": True,
    },
    {
        "codice": "pec_operator",
        "nome_display": "PEC Operatore",
        "descrizione": "Legge e risponde ai messaggi PEC",
        "attivo": True,
    },
    {
        "codice": "pec_viewer",
        "nome_display": "PEC Lettore",
        "descrizione": "Legge i messaggi PEC in sola lettura",
        "attivo": True,
    },
]


def register_roles(db: Session) -> dict:
    """
    Registra i ruoli del modulo gestione_pec.

    Viene chiamato durante l'inizializzazione del modulo.

    Args:
        db: Database session

    Returns:
        Dizionario con statistiche della registrazione
    """
    logger.info("Registrazione ruoli modulo '%s'...", MODULE_ID)

    result = RoleRegistry.register_roles(
        db=db,
        modulo_id=MODULE_ID,
        roles=ROLES,
        overwrite=False,  # Non sovrascrivere ruoli esistenti
    )

    if result["errors"]:
        logger.warning(
            "Registrazione ruoli completata con errori: %s", result["errors"]
        )
    else:
        logger.info(
            "Registrati %s ruoli, %s già esistenti",
            result["created"],
            result["skipped"],
        )

    return result


def unregister_roles(db: Session) -> int:
    """
    Rimuove tutti i ruoli del modulo gestione_pec.

    ATTENZIONE: Rimuove anche tutte le assegnazioni di questi ruoli.
    Usare solo durante la disinstallazione del modulo.

    Args:
        db: Database session

    Returns:
        Numero di ruoli rimossi
    """
    logger.warning("Rimozione ruoli modulo '%s'...", MODULE_ID)

    count = RoleRegistry.unregister_module_roles(
        db=db,
        modulo_id=MODULE_ID,
    )

    logger.info("Rimossi %s ruoli del modulo '%s'", count, MODULE_ID)

    return count
