"""
Definizione dei ruoli del modulo Affitti Lungo.

Questi ruoli vengono registrati dinamicamente nel sistema al caricamento del modulo.
"""
import logging
from sqlalchemy.orm import Session
from app.core.services.role_registry import RoleRegistry

logger = logging.getLogger(__name__)

# ID del modulo
MODULE_ID = "affitti_lungo"

# Definizione dei ruoli gestiti da questo modulo
ROLES = [
    {
        "codice": "proprietario",
        "nome_display": "Proprietario",
        "descrizione": "Proprietario di immobili",
        "tabella_specializzazione": "proprietari",
        "attivo": True
    },
    {
        "codice": "affittuario",
        "nome_display": "Affittuario / Inquilino",
        "descrizione": "Affittuario o inquilino di un immobile",
        "tabella_specializzazione": "affittuari",
        "attivo": True
    },
    {
        "codice": "tecnico",
        "nome_display": "Tecnico",
        "descrizione": "Tecnico manutentore (elettricista, idraulico, etc.)",
        "tabella_specializzazione": "tecnici",
        "attivo": True
    }
]


def register_roles(db: Session) -> dict:
    """
    Registra i ruoli del modulo affitti_lungo.

    Viene chiamato durante l'inizializzazione del modulo.

    Args:
        db: Database session

    Returns:
        Dizionario con statistiche della registrazione
    """
    logger.info(f"Registrazione ruoli modulo '{MODULE_ID}'...")

    result = RoleRegistry.register_roles(
        db=db,
        modulo_id=MODULE_ID,
        roles=ROLES,
        overwrite=False  # Non sovrascrivere ruoli esistenti
    )

    if result["errors"]:
        logger.warning(
            f"Registrazione ruoli completata con errori: {result['errors']}"
        )
    else:
        logger.info(
            f"✅ Registrati {result['created']} ruoli, "
            f"{result['skipped']} già esistenti"
        )

    return result


def unregister_roles(db: Session) -> int:
    """
    Rimuove tutti i ruoli del modulo affitti_lungo.

    ATTENZIONE: Rimuove anche tutte le assegnazioni di questi ruoli.
    Usare solo durante la disinstallazione del modulo.

    Args:
        db: Database session

    Returns:
        Numero di ruoli rimossi
    """
    logger.warning(f"Rimozione ruoli modulo '{MODULE_ID}'...")

    count = RoleRegistry.unregister_module_roles(
        db=db,
        modulo_id=MODULE_ID
    )

    logger.info(f"✅ Rimossi {count} ruoli del modulo '{MODULE_ID}'")

    return count
