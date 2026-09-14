# Servizio Notifiche Core

**Stato:** Approvato — pronto per il piano di implementazione.
**Data:** 2026-09-14
**Sotto-progetto:** #1 della roadmap "Gestione Immobiliare" (notifiche → anagrafica → immobili → affitti brevi → affitti lungo)

---

## 1. Contesto e obiettivo

Oggi non esiste un servizio di notifica generico nella piattaforma: l'unico esempio (`gestione_pec/services/notification_service.py`) è ad-hoc, solo email, e specifico del modulo PEC. Lo scadenzario esistente (`app/core/platform_services/scadenza_service.py`) traccia già chi va notificato per ogni scadenza (`ScadenzaDestinatario.notificato` / `notificato_il`) ma **non invia nulla** — il campo esiste e non viene mai aggiornato da nessun job.

Obiettivo: un servizio core (`NotificationService`) che ogni modulo/servizio della piattaforma può usare per notificare uno o più utenti via email e/o in-app, più un job che chiude il gap reale nello scadenzario (reminder automatico sulle scadenze in avvicinamento/scadute).

È un **servizio core della piattaforma** (vedi `2026-09-14-module-communication-architecture-design.md`, §3.1): accesso diretto via import Python da qualunque modulo, nessuna API REST interna necessaria.

## 2. Modello dati

Nuova tabella **tenant** (ogni tenant ha le proprie notifiche, come già `core_scadenze`): `core_notifiche`.

```python
class Notifica(Base):
    __tablename__ = "core_notifiche"

    id              Integer PK
    user_id         Integer          # destinatario (FK logica a core_users, cross-schema come Scadenza)

    tipo            String(100)      # namespace libero, es. "scadenza.reminder", "scadenza.scaduta"
    titolo          String(255)
    corpo           Text

    # Link opzionale all'entità che ha originato la notifica (pattern polimorfico, come Documento/Scadenza)
    entity_type     String(50)   nullable
    entity_id       Integer      nullable
    link_url        String(500)  nullable   # path frontend per il click-through, es. "/scadenze/42"

    canali          String(20)       # "IN_APP" | "EMAIL" | "ENTRAMBI"
    stato_email     String(20)       # "NON_RICHIESTA" | "PENDING" | "SENT" | "FAILED"
    errore_email    Text         nullable

    letta           Boolean          default False
    letta_il        DateTime     nullable

    creata_il       DateTime         server_default=now()
```

Indici: `(user_id, letta)` per il badge/lista, `(tipo)` per query di debug.

Nessuna tabella di log separata (a differenza di `pec_notifiche_log`): lo stato invio email vive direttamente sulla riga `Notifica` (`stato_email`/`errore_email`), non serve un log distinto perché qui il "log" e la "notifica" coincidono concettualmente (una notifica in-app che ha anche un tentativo di invio email).

## 3. `NotificationService`

`app/core/platform_services/notification_service.py`, pattern identico a `ScadenzaService` (classe con `db: Session` iniettato).

```python
class NotificationService:
    def __init__(self, db: Session): ...

    def notify(
        self,
        user_ids: list[int],
        tipo: str,
        titolo: str,
        corpo: str,
        entity_type: str | None = None,
        entity_id: int | None = None,
        link_url: str | None = None,
        canali: Canale = Canale.ENTRAMBI,
    ) -> list[Notifica]:
        """Crea una Notifica per ciascun user_id. Se canali include EMAIL, invia
        subito via SMTP applicativo e aggiorna stato_email. Non solleva mai
        eccezioni per un fallimento email (pattern try/except identico a
        gestione_pec: logga e segna FAILED, la notifica in-app resta comunque
        creata)."""

    def list_for_user(self, user_id: int, solo_non_lette: bool = False, skip=0, limit=50) -> list[Notifica]: ...
    def segna_letta(self, notifica_id: int, user_id: int) -> Notifica | None: ...
    def segna_tutte_lette(self, user_id: int) -> int: ...
    def badge_count(self, user_id: int) -> int: ...
```

**Invio email**: riusa le impostazioni `NOTIFICHE_SMTP_*` già presenti in `app/core/config.py` (introdotte per `gestione_pec`) — stesso SMTP applicativo, non se ne aggiunge un secondo. Se `NOTIFICHE_SMTP_HOST` non è configurato: `stato_email = "NON_RICHIESTA"` anche se richiesta EMAIL, nessun errore (coerente col comportamento no-op già presente in PEC).

## 4. Route core

Prefisso `/api/v1/notifiche` (route del **core**, non di un modulo — vive in `app/core/routes/notifiche.py`, registrata sempre, non condizionata a manifest di moduli):

| Metodo | Path | Descrizione |
|---|---|---|
| `GET` | `/notifiche` | Lista notifiche dell'utente autenticato (filtro `solo_non_lette`, paginazione) |
| `POST` | `/notifiche/{id}/segna-letta` | Segna una notifica come letta |
| `POST` | `/notifiche/segna-tutte-lette` | Segna tutte lette |
| `GET` | `/notifiche/badge` | `{ "count_non_lette": N }` |

Nessun permesso speciale richiesto oltre l'autenticazione: ogni utente vede solo le proprie notifiche (`user_id` preso dal token, mai da query param).

## 5. Job reminder scadenze

Nuovo modulo `app/core/platform_services/scadenza_reminder_job.py`, registrato come job APScheduler globale all'avvio della piattaforma (non di un modulo specifico — vive nel core, gira per ogni tenant attivo), pattern preso da `affitti_brevi/services/sync_scheduler.py`:

```python
def run_reminder_check(tenant_schema: str):
    db = SessionLocal()
    try:
        db.execute(text(f"SET search_path TO {tenant_schema}, public"))
        _check_scadenze_in_avvicinamento(db)
        _check_scadenze_scadute(db)
    finally:
        db.close()
```

- **Frequenza**: 1 volta al giorno (orario configurabile, default 07:00).
- **Soglia "in avvicinamento"**: `REMINDER_GIORNI_PRIMA` in config, default 3 giorni. Scadenze `ATTIVA` con `data_scadenza` tra oggi e oggi+N.
- **Scadute**: scadenze che sono appena passate a `SCADUTA` (già gestito da `ScadenzaService.update_overdue_status()`, che va chiamato prima del check reminder nello stesso job).
- **Anti-spam**: si notifica **una volta per soglia**, non ogni giorno. Si usa il flag esistente `ScadenzaDestinatario.notificato`: se è già `True` non si rinotifica per lo stesso "evento" (in-avvicinamento). Quando la scadenza passa da `ATTIVA` a `SCADUTA`, si resetta `notificato = False` per poter notificare di nuovo l'evento "scaduta" (un evento diverso, una notifica diversa) — il reset avviene dentro `update_overdue_status()`.
- Per ogni scadenza da notificare: destinatari = `creato_da` + tutti gli `ScadenzaDestinatario`; chiama `NotificationService.notify(...)` con `tipo="scadenza.reminder"` o `"scadenza.scaduta"`, `entity_type="scadenza"`, `entity_id=scadenza.id`, `link_url=f"/scadenze/{scadenza.id}"`; poi marca ogni destinatario `mark_notified()`.
- **Isolamento errori**: ogni scadenza processata in try/except indipendente — un errore su una non blocca le altre (stesso principio del polling PEC).

## 6. Frontend

Componente piattaforma (non di un modulo di dominio): `frontend/src/components/Notifications/NotificationBell.jsx`, montato nell'header/Sidebar accanto al badge scadenze già esistente.

- Polling badge ogni 60s (stesso pattern già usato per PEC/scadenze).
- Dropdown con le ultime notifiche non lette; click → segna letta + naviga a `link_url` se presente.
- Nessun modulo nuovo, nessuna voce di menu: è infrastruttura di piattaforma sempre presente.

## 7. Error handling

- Fallimento invio email non blocca mai la creazione della notifica in-app (già creata prima del tentativo email).
- Job reminder: try/except per singola scadenza, log e continua.
- Nessuna eccezione propagata all'utente per problemi SMTP: al massimo `stato_email = "FAILED"` visibile solo internamente (non esposto nell'UI utente finale, la notifica in-app resta comunque affidabile).

## 8. Testing

- Unit test `NotificationService` (mock SMTP): creazione notifica, invio email con successo/fallimento, badge count, segna-letta.
- Unit test job reminder: scadenze a distanze diverse dalla soglia (oggi, oggi+2, oggi+3, oggi+4 con soglia=3) verificano che solo quelle nella finestra vengano notificate; verifica anti-spam (seconda esecuzione dello stesso giorno non rinotifica).
- Integration test route `/notifiche/*` (lista, segna-letta, badge) con utente autenticato, isolamento tra utenti diversi (utente A non vede notifiche di utente B).

## 9. Fuori scope

- WebSocket/SSE per push realtime — resta polling.
- Unificazione con `gestione_pec/services/notification_service.py` — resta separato, modulo standalone pensato per distribuzione indipendente (vedi memoria di progetto).
- Digest/raggruppamento di più notifiche in una sola email.
- Preferenze utente per canale (es. "solo in-app, mai email") — v1 usa sempre il default richiesto dal chiamante.
