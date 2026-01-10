"""
Seed default document types for anagrafica module.
"""
from sqlalchemy.orm import Session
from anagrafica_italiana.models import TipoDocumento
import logging

logger = logging.getLogger(__name__)


def seed_tipi_documento(db: Session):
    """Upsert default document types"""

    tipi_documento = [
        # Documenti identità
        {
            "codice": "CARTA_IDENTITA",
            "nome": "Carta d'Identità",
            "descrizione": "Documento di identità italiano",
            "categoria": "identita",
            "richiede_scadenza": True
        },
        {
            "codice": "PASSAPORTO",
            "nome": "Passaporto",
            "descrizione": "Documento di identità per viaggi internazionali",
            "categoria": "identita",
            "richiede_scadenza": True
        },
        {
            "codice": "PATENTE",
            "nome": "Patente di Guida",
            "descrizione": "Patente di guida",
            "categoria": "identita",
            "richiede_scadenza": True
        },

        # Documenti fiscali
        {
            "codice": "CODICE_FISCALE",
            "nome": "Codice Fiscale",
            "descrizione": "Tessera codice fiscale",
            "categoria": "fiscale",
            "richiede_scadenza": False
        },
        {
            "codice": "PARTITA_IVA",
            "nome": "Partita IVA",
            "descrizione": "Certificato Partita IVA",
            "categoria": "fiscale",
            "richiede_scadenza": False
        },
        {
            "codice": "VISURA_CAMERALE",
            "nome": "Visura Camerale",
            "descrizione": "Visura Camera di Commercio",
            "categoria": "fiscale",
            "richiede_scadenza": True
        },

        # Documenti professionali
        {
            "codice": "CERTIFICATO_PROFESSIONALE",
            "nome": "Certificato Professionale",
            "descrizione": "Attestato o certificato professionale",
            "categoria": "professionale",
            "richiede_scadenza": True
        },
        {
            "codice": "ISCRIZIONE_ALBO",
            "nome": "Iscrizione Albo Professionale",
            "descrizione": "Certificato iscrizione albo professionale",
            "categoria": "professionale",
            "richiede_scadenza": True
        },

        # Altri documenti
        {
            "codice": "CONTRATTO",
            "nome": "Contratto",
            "descrizione": "Contratto generico",
            "categoria": "altro",
            "richiede_scadenza": False
        },
        {
            "codice": "DOCUMENTO_GENERICO",
            "nome": "Documento Generico",
            "descrizione": "Altro tipo di documento",
            "categoria": "altro",
            "richiede_scadenza": False
        },
    ]

    created = 0
    updated = 0

    for tipo_data in tipi_documento:
        existing = db.query(TipoDocumento).filter(
            TipoDocumento.codice == tipo_data["codice"]
        ).first()
        if existing:
            existing.nome = tipo_data["nome"]
            existing.descrizione = tipo_data["descrizione"]
            existing.categoria = tipo_data["categoria"]
            existing.richiede_scadenza = tipo_data["richiede_scadenza"]
            existing.attivo = True
            updated += 1
        else:
            tipo = TipoDocumento(**tipo_data)
            db.add(tipo)
            created += 1

    db.commit()
    logger.info("✅ Seeded tipi documento: %s created, %s updated", created, updated)
    return created + updated
