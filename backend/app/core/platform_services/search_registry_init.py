"""
Search Registry Initialization

Registers all searchable entities from modules at application startup.
"""
import logging

logger = logging.getLogger(__name__)


def init_search_registry():
    """
    Initialize the unified search registry with entities from all modules.

    This function should be called during application startup after all
    module models are loaded.
    """
    from app.core.platform_services.unified_search import register_searchable_entity

    logger.info("[UnifiedSearch] Initializing search registry...")

    # =========================================================================
    # ANAGRAFICA ITALIANA MODULE
    # =========================================================================
    try:
        from anagrafica_italiana.models import SoggettoAnagrafico

        # Persone Fisiche
        register_searchable_entity(
            module_name="anagrafica_italiana",
            entity_name="PersonaFisica",
            display_name="Persona Fisica",
            display_name_plural="Persone Fisiche",
            model_class=SoggettoAnagrafico,
            search_fields=[
                {"name": "nome", "label": "Nome", "weight": 2},
                {"name": "cognome", "label": "Cognome", "weight": 2},
                {"name": "codice_fiscale", "label": "Codice Fiscale", "weight": 3},
                {"name": "email", "label": "Email"},
                {"name": "telefono", "label": "Telefono"},
                {"name": "citta", "label": "Città"},
            ],
            title_template="{nome} {cognome}",
            subtitle_template="{codice_fiscale} - {email}",
            url_template="/anagrafiche/persone-fisiche/{id}",
            icon="user",
            color="#3498db",
            default_order_by="cognome",
        )

        # Persone Giuridiche
        register_searchable_entity(
            module_name="anagrafica_italiana",
            entity_name="PersonaGiuridica",
            display_name="Persona Giuridica",
            display_name_plural="Persone Giuridiche",
            model_class=SoggettoAnagrafico,
            search_fields=[
                {"name": "ragione_sociale", "label": "Ragione Sociale", "weight": 3},
                {"name": "partita_iva", "label": "Partita IVA", "weight": 2},
                {"name": "codice_fiscale", "label": "Codice Fiscale", "weight": 2},
                {"name": "email", "label": "Email"},
                {"name": "pec", "label": "PEC"},
                {"name": "citta", "label": "Città"},
            ],
            title_template="{ragione_sociale}",
            subtitle_template="P.IVA: {partita_iva} - {email}",
            url_template="/anagrafiche/persone-giuridiche/{id}",
            icon="building",
            color="#9b59b6",
            default_order_by="ragione_sociale",
        )

        logger.info("[UnifiedSearch] Registered anagrafica_italiana entities")

    except ImportError as e:
        logger.warning(f"[UnifiedSearch] Could not register anagrafica_italiana: {e}")

    # =========================================================================
    # IMMOBILI MODULE
    # =========================================================================
    try:
        from immobili.models import UnitaImmobiliare, Condominio

        # Unità Immobiliari
        register_searchable_entity(
            module_name="immobili",
            entity_name="UnitaImmobiliare",
            display_name="Unità Immobiliare",
            display_name_plural="Unità Immobiliari",
            model_class=UnitaImmobiliare,
            search_fields=[
                {"name": "codice", "label": "Codice", "weight": 3},
                {"name": "indirizzo", "label": "Indirizzo", "weight": 2},
                {"name": "citta", "label": "Città", "weight": 2},
                {"name": "cap", "label": "CAP"},
                {"name": "tipo", "label": "Tipo"},
            ],
            title_template="{indirizzo}",
            subtitle_template="{citta} ({cap}) - {tipo}",
            url_template="/unita-immobiliari/{id}",
            icon="home",
            color="#27ae60",
            default_order_by="-created_at",
        )

        # Condomini
        register_searchable_entity(
            module_name="immobili",
            entity_name="Condominio",
            display_name="Condominio",
            display_name_plural="Condomini",
            model_class=Condominio,
            search_fields=[
                {"name": "codice", "label": "Codice", "weight": 3},
                {"name": "nome", "label": "Nome", "weight": 2},
                {"name": "indirizzo", "label": "Indirizzo", "weight": 2},
                {"name": "citta", "label": "Città"},
            ],
            title_template="{nome}",
            subtitle_template="{indirizzo}, {citta}",
            url_template="/condomini/{id}",
            icon="building-2",
            color="#16a085",
            default_order_by="nome",
        )

        logger.info("[UnifiedSearch] Registered immobili entities")

    except ImportError as e:
        logger.warning(f"[UnifiedSearch] Could not register immobili: {e}")

    # =========================================================================
    # AFFITTI LUNGO MODULE
    # =========================================================================
    try:
        from affitti_lungo.models import Contratto, Affittuario, Spesa

        # Contratti
        def build_contratto_result(contratto):
            """Custom result builder for Contratto to include related data."""
            # Get affittuario name if available
            affittuario_nome = ""
            if hasattr(contratto, "affittuario") and contratto.affittuario:
                aff = contratto.affittuario
                if hasattr(aff, "soggetto") and aff.soggetto:
                    sogg = aff.soggetto
                    affittuario_nome = f"{sogg.nome} {sogg.cognome}".strip() or sogg.ragione_sociale or ""

            # Get immobile address if available
            immobile_indirizzo = ""
            if hasattr(contratto, "unita_immobiliare") and contratto.unita_immobiliare:
                immobile_indirizzo = contratto.unita_immobiliare.indirizzo or ""

            return {
                "id": contratto.id,
                "title": f"Contratto {contratto.numero_contratto}",
                "subtitle": f"{affittuario_nome} - {immobile_indirizzo}".strip(" -"),
                "url": f"/contratti/{contratto.id}",
                "type": "Contratto",
                "module": "affitti_lungo",
            }

        register_searchable_entity(
            module_name="affitti_lungo",
            entity_name="Contratto",
            display_name="Contratto",
            display_name_plural="Contratti",
            model_class=Contratto,
            search_fields=[
                {"name": "numero_contratto", "label": "Numero Contratto", "weight": 3},
            ],
            title_template="Contratto {numero_contratto}",
            subtitle_template="",
            url_template="/contratti/{id}",
            icon="file-text",
            color="#e74c3c",
            default_order_by="-data_inizio",
            result_builder=build_contratto_result,
        )

        # Affittuari
        def build_affittuario_result(affittuario):
            """Custom result builder for Affittuario to include soggetto data."""
            nome = ""
            email = ""
            if hasattr(affittuario, "soggetto") and affittuario.soggetto:
                sogg = affittuario.soggetto
                nome = f"{sogg.nome} {sogg.cognome}".strip() or sogg.ragione_sociale or ""
                email = sogg.email or ""

            return {
                "id": affittuario.id,
                "title": nome or f"Affittuario #{affittuario.id}",
                "subtitle": email,
                "url": f"/affittuari/{affittuario.id}",
                "type": "Affittuario",
                "module": "affitti_lungo",
            }

        register_searchable_entity(
            module_name="affitti_lungo",
            entity_name="Affittuario",
            display_name="Affittuario",
            display_name_plural="Affittuari",
            model_class=Affittuario,
            search_fields=[
                {"name": "id", "label": "ID"},  # Will search via related soggetto
            ],
            title_template="Affittuario #{id}",
            subtitle_template="",
            url_template="/affittuari/{id}",
            icon="users",
            color="#f39c12",
            default_order_by="-created_at",
            result_builder=build_affittuario_result,
        )

        logger.info("[UnifiedSearch] Registered affitti_lungo entities")

    except ImportError as e:
        logger.warning(f"[UnifiedSearch] Could not register affitti_lungo: {e}")

    # =========================================================================
    # AFFITTI BREVI MODULE
    # =========================================================================
    try:
        from affitti_brevi.models import Prenotazione, Soggiorno

        # Prenotazioni
        register_searchable_entity(
            module_name="affitti_brevi",
            entity_name="Prenotazione",
            display_name="Prenotazione",
            display_name_plural="Prenotazioni",
            model_class=Prenotazione,
            search_fields=[
                {"name": "codice_prenotazione", "label": "Codice", "weight": 3},
                {"name": "nome_ospite", "label": "Nome Ospite", "weight": 2},
                {"name": "email_ospite", "label": "Email"},
            ],
            title_template="{codice_prenotazione}",
            subtitle_template="{nome_ospite} - {email_ospite}",
            url_template="/affitti-brevi/prenotazioni/{id}",
            icon="calendar-check",
            color="#3498db",
            default_order_by="-data_checkin",
        )

        logger.info("[UnifiedSearch] Registered affitti_brevi entities")

    except ImportError as e:
        logger.warning(f"[UnifiedSearch] Could not register affitti_brevi: {e}")

    # =========================================================================
    # ESEMPIO COMPONENTI MODULE
    # =========================================================================
    try:
        from esempio_componenti.models import ElementoEsempio

        register_searchable_entity(
            module_name="esempio_componenti",
            entity_name="ElementoEsempio",
            display_name="Elemento Esempio",
            display_name_plural="Elementi Esempio",
            model_class=ElementoEsempio,
            search_fields=[
                {"name": "codice", "label": "Codice", "weight": 3},
                {"name": "titolo", "label": "Titolo", "weight": 2},
                {"name": "descrizione", "label": "Descrizione"},
            ],
            title_template="{titolo}",
            subtitle_template="{codice} - {stato}",
            url_template="/esempio/elementi/{id}",
            icon="puzzle",
            color="#9b59b6",
            default_order_by="-created_at",
        )

        logger.info("[UnifiedSearch] Registered esempio_componenti entities")

    except ImportError as e:
        logger.warning(f"[UnifiedSearch] Could not register esempio_componenti: {e}")

    logger.info("[UnifiedSearch] Search registry initialization complete")
