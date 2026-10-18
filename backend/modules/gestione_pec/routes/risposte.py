"""
Route per l'invio di risposte PEC e la lettura dell'audit delle risposte.

Tutti gli endpoint richiedono almeno il permesso `pec.read`.
L'invio richiede `pec.reply` e che l'utente abbia puo_rispondere=True
in pec_utenti_abilitati (con bypass per pec.admin/superuser).
"""
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.auth.dependencies import get_current_active_user, require_permission
from app.core.auth.models import User

from ..models.audit_risposta import PecAuditRisposta
from ..models.messaggio import PecMessaggio
from ..models.utente_abilitato import PecUtenteAbilitato
from ..routes.messaggi import _ha_permesso_admin, _verifica_accesso_casella
from ..schemas.risposta import RispostaCreate, RispostaRead
from ..services.audit_service import AzioneAudit, log_accesso
from ..services.crypto_service import decrypt_credential
from ..services.smtp_service import SmtpService, calcola_hash_integrita

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/pec/messaggi",
    tags=["PEC - Risposte"],
)


def _get_messaggio_or_404(messaggio_id: int, db: Session) -> PecMessaggio:
    msg = db.query(PecMessaggio).filter(PecMessaggio.id == messaggio_id).first()
    if not msg:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Messaggio con ID {messaggio_id} non trovato",
        )
    return msg


@router.post(
    "/{messaggio_id}/rispondi",
    response_model=RispostaRead,
    dependencies=[Depends(require_permission("pec.reply"))],
)
def rispondi_messaggio(
    messaggio_id: int,
    payload: RispostaCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> PecAuditRisposta:
    """
    Invia una risposta PEC a un messaggio esistente.

    Salva sempre un record di audit (PecAuditRisposta) anche in caso di
    fallimento SMTP, garantendo l'audit trail completo.
    Se SMTP fallisce, ritorna 200 con smtp_status=FAILED (non 500).
    """
    # 1. Carica il messaggio originale
    msg = _get_messaggio_or_404(messaggio_id, db)

    # 2. Verifica accesso alla casella
    casella = _verifica_accesso_casella(db, msg.casella_id, current_user)

    # 3. Verifica che l'utente possa rispondere (bypass per admin/superuser)
    if not _ha_permesso_admin(current_user):
        abilitato = (
            db.query(PecUtenteAbilitato)
            .filter(
                PecUtenteAbilitato.casella_id == msg.casella_id,
                PecUtenteAbilitato.user_id == current_user.id,
            )
            .first()
        )
        if not abilitato or not abilitato.puo_rispondere:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Non sei autorizzato a rispondere per questa casella",
            )

    # 4. Verifica configurazione SMTP
    if not casella.smtp_host:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Configurazione SMTP non presente per questa casella",
        )

    # 5. Decifra credenziali
    username_plain = decrypt_credential(casella.username_enc)
    password_plain = decrypt_credential(casella.password_enc)

    # 6. Invia via SMTP
    smtp_svc = SmtpService(casella, username_plain, password_plain)
    risultato = smtp_svc.invia_risposta(
        destinatari=payload.destinatari,
        oggetto=payload.oggetto,
        corpo_testo=payload.corpo_testo,
        corpo_html=payload.corpo_html,
        in_reply_to=msg.message_id,
        references=msg.message_id,
    )

    # 7. Calcola hash integrità
    timestamp_iso = datetime.now(timezone.utc).isoformat()
    destinatari_joined = ", ".join(payload.destinatari)
    oggetto_risposta = payload.oggetto
    if not oggetto_risposta.lower().startswith("re:"):
        oggetto_risposta = f"Re: {oggetto_risposta}"

    hash_val = calcola_hash_integrita(
        user_id=current_user.id,
        casella_pec=casella.indirizzo_pec,
        destinatari=destinatari_joined,
        oggetto=oggetto_risposta,
        corpo=payload.corpo_testo,
        timestamp=timestamp_iso,
    )

    # 8. Salva PecAuditRisposta — sempre, anche in caso di errore SMTP
    smtp_status = "SENT" if risultato.successo else "FAILED"
    inviato_at = datetime.now(timezone.utc) if risultato.successo else None

    audit = PecAuditRisposta(
        casella_id=msg.casella_id,
        messaggio_originale_id=msg.id,
        user_id=current_user.id,
        destinatari=destinatari_joined,
        oggetto_risposta=oggetto_risposta,
        corpo_risposta_testo=payload.corpo_testo,
        corpo_risposta_html=payload.corpo_html,
        message_id_risposta=risultato.message_id,
        # Snapshot immutabile del messaggio originale al momento della risposta
        snapshot_da=msg.da,
        snapshot_oggetto=msg.oggetto,
        snapshot_corpo_testo=msg.corpo_testo,
        snapshot_data_invio=msg.data_invio,
        smtp_status=smtp_status,
        smtp_error=risultato.errore,
        hash_integrita=hash_val,
        inviato_at=inviato_at,
    )
    db.add(audit)

    # 9. Aggiorna is_risposto solo se SMTP ha avuto successo
    if risultato.successo:
        msg.is_risposto = True

    db.commit()
    db.refresh(audit)

    # 10. Registra audit log
    ip = request.client.host if request.client else None
    ua = request.headers.get("user-agent")
    log_accesso(
        db=db,
        casella_id=msg.casella_id,
        user_id=current_user.id,
        azione=AzioneAudit.REPLY_SENT,
        messaggio_id=msg.id,
        ip_address=ip,
        user_agent=ua,
        dettagli={"smtp_status": smtp_status, "destinatari": destinatari_joined},
    )
    db.commit()

    return audit


@router.get(
    "/{messaggio_id}/risposte",
    response_model=list[RispostaRead],
    dependencies=[Depends(require_permission("pec.read"))],
)
def get_risposte(
    messaggio_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> list[PecAuditRisposta]:
    """
    Restituisce tutte le risposte inviate per un messaggio,
    ordinate per created_at DESC.
    """
    msg = _get_messaggio_or_404(messaggio_id, db)
    _verifica_accesso_casella(db, msg.casella_id, current_user)

    risposte = (
        db.query(PecAuditRisposta)
        .filter(PecAuditRisposta.messaggio_originale_id == messaggio_id)
        .order_by(PecAuditRisposta.created_at.desc())
        .all()
    )
    return risposte
