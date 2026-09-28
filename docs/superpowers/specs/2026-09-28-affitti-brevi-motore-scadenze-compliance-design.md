# Motore Scadenze Compliance — Affitti Brevi (Sub-progetto A)

**Stato:** Approvato — pronto per il piano di implementazione.
**Data:** 2026-09-28
**Sotto-progetto:** #1 di 4 della roadmap "Compliance affitti brevi" (motore scadenze → tassa di soggiorno → comunicazione Polizia/Alloggiati Web → report ISTAT)

---

## 1. Contesto e obiettivo

Il modulo `affitti_brevi` ha due generazioni sovrapposte di codice per gli adempimenti obbligatori (tassa di soggiorno, comunicazione ospiti alla Polizia, report ISTAT), nessuna funzionante:

1. **Modelli nuovi, nessun servizio**: `Comunicazione` (generico, POLIZIA/ISTAT/TASSA_DICHIARAZIONE, legato a `Soggiorno`), `AttivitaSchedulata`/`Log` (motore di scheduling ricorrente generico), `TassaSoggiorno`/`Config`/`Scaglione`. Modelli coerenti con lo schema attuale, ma non popolati né letti da nessun servizio o route.
2. **Codice vecchio, pre-refactor `Soggiorno`, non importabile**: `services/scadenza_generator.py`, `services/comunicazione_polizia_service.py`, `routes/tasse.py` — riferiscono classi che non esistono più (`TassaPrenotazione`, `ComunicazionePolizia`, `OspitePrenotazione`, `models.scadenza_ext.ScadenzaAffittiBrevi`). Nessuno di questi è raggiungibile da `__init__.py` (route commentate, scheduler mai avviato).

La piattaforma ha già un **motore scadenze core** completo e funzionante (`app/core/platform/models/scadenza.py` + `ScadenzaService`): scadenze polimorfiche (`modulo`/`entity_type`/`entity_id`), mostrate in `NotifichePanel.jsx` (badge, raggruppamento per urgenza), con un link "Apri" che passa da `/scadenze/resolve` → `ScadenzaResolve.jsx`'s `buildTarget()` (oggi wired solo per `anagrafica_italiana`/`SOGGETTO_ANAGRAFICO`) verso la pagina del modulo competente, e un ciclo di vita (`completa_scadenza`/`delete_scadenza`) che il modulo aziona quando l'azione corrispondente è stata fatta.

**Obiettivo di questo sotto-progetto**: collegare `affitti_brevi` a questo motore esistente, validando il pattern end-to-end su due casi pilota deterministici e a rischio zero (nessuna integrazione esterna): la comunicazione Polizia e la richiesta di pagamento tassa di soggiorno. I sotto-progetti B (tassa di soggiorno — calcolo/dichiarazione al comune), C (invio reale Alloggiati Web) e D (report ISTAT) riusano lo stesso motore in spec separate.

Questo lavoro non dipende da, ma si combina bene con, `2026-09-14-notification-service-design.md` (approvato, non ancora implementato): quando quel servizio invierà email/notifiche reali sulle scadenze in avvicinamento, le scadenze create qui ne beneficeranno automaticamente senza modifiche.

## 2. Decisioni di scope

- **`AttivitaSchedulata`/`AttivitaSchedulataLog` vengono eliminati.** Non sono mai eseguiti da nessun runner; il pattern già affermato nel modulo (`SyncScheduler`, APScheduler) e in `gestione_pec` (`polling_scheduler.py`) copre lo stesso bisogno con meno codice da mantenere.
- **Il codice vecchio (`scadenza_generator.py`, `comunicazione_polizia_service.py`, `routes/tasse.py`) viene eliminato**, non recuperato: non è mai stato raggiungibile ed è scritto contro modelli che non esistono più.
- **Trigger Polizia**: 24h dal check-in di ogni `Soggiorno` valido. Genera una `Comunicazione(tipo=POLIZIA)` + `Scadenza` collegata. Il completamento (per ora) è manuale — l'invio automatico reale ad Alloggiati Web è compito del sotto-progetto C.
- **Trigger Tassa di soggiorno**: il giorno del check-in, genera una `Comunicazione(tipo=TASSA_DICHIARAZIONE)` + `Scadenza` collegata, con testo "Richiedi pagamento tassa di soggiorno a [ospite]" e l'importo se già calcolato in `TassaSoggiorno`. È un promemoria per lo **staff**, che poi contatta l'ospite con i mezzi che ha oggi (WhatsApp manuale, di persona, ecc.). **Fuori scope in questa fase**: invio automatico di messaggi, generazione di un link di pagamento, integrazione con un gateway di pagamento. Il completamento è manuale (lo staff segna fatto dopo aver incassato/richiesto).
- Questa spec **non tocca** il calcolo dell'importo tassa (`tassa_soggiorno_calculator.py`) né la dichiarazione periodica al comune — quello è nel sotto-progetto B.

## 3. Architettura e flusso dati

**Nuovo servizio** `backend/modules/affitti_brevi/services/compliance_scadenze_service.py`, classe `ComplianceScadenzeService(db: Session)`:

- `genera_scadenza_polizia(soggiorno: Soggiorno) -> Comunicazione | None`
  Se esiste già una `Comunicazione(soggiorno_id=soggiorno.id, tipo=POLIZIA)`, ritorna quella esistente (idempotente, no-op). Altrimenti crea la `Comunicazione` (stato iniziale `DA_PREPARARE`) e una `Scadenza` core (`modulo="affitti_brevi"`, `entity_type="comunicazione"`, `entity_id=comunicazione.id`, `titolo="Comunicazione Polizia — [nome struttura/codice soggiorno]"`, `data_scadenza = data_checkin + 24h` convertita a `date`, `priorita=ALTA`), tramite `ScadenzaService(db).create_scadenza(...)`. Salva l'id della scadenza collegata sulla `Comunicazione` (nuovo campo, vedi §4). Il job non ha un utente di richiesta: `creato_da` usa `app.core.auth.init_data.get_system_user_id(db)`, già esistente e usato altrove per scadenze generate da job.

- `genera_scadenza_tassa(soggiorno: Soggiorno) -> Comunicazione | None`
  Stessa logica, `tipo=TASSA_DICHIARAZIONE`, `data_scadenza = data_checkin`, `priorita=MEDIA`, descrizione che include l'importo da `soggiorno.tassa_soggiorno.importo_totale` se presente, altrimenti "Importo da calcolare".

- `completa_comunicazione(comunicazione_id: int, note: str = None) -> Comunicazione`
  Marca la `Comunicazione` come inviata (riusa `Comunicazione.mark_inviata()` già esistente sul modello) e chiama `ScadenzaService(db).completa_scadenza(scadenza_id, user_id, note)` sulla scadenza collegata.

**Nuovo job schedulato** `backend/modules/affitti_brevi/services/compliance_scheduler.py`, stesso pattern di `sync_scheduler.py` (bound a singola `Connection`, iterazione sui tenant attivi con `affitti_brevi` abilitato via `_get_active_tenant_schemas()`, riuso possibile della funzione già esistente in `sync_scheduler.py` spostandola in un modulo condiviso o duplicandola — **decisione implementativa lasciata al piano**, non architetturale): ogni ora, per ogni tenant, seleziona i `Soggiorno` con `valido=True` e `data_checkin` nelle prossime 48 ore, e per ciascuno chiama le due funzioni di generazione sopra (idempotenti, quindi sicuro rieseguirle sugli stessi soggiorni ogni ora finché non generano nulla di nuovo).

Avviato da `affitti_brevi/__init__.py`'s `register_module(app)`, accanto (non al posto di) allo start dello `SyncScheduler` esistente, con lo stesso fix già applicato lì per il job iniziale (schedulato come one-off sul thread di background dello scheduler, non eseguito sincrono a import-time — altrimenti bloccherebbe l'import di `app.main`).

**Nuove route** `backend/modules/affitti_brevi/routes/comunicazioni.py`:
- `GET /comunicazioni/{id}` → dettaglio `Comunicazione` (per la pagina di resolve)
- `POST /comunicazioni/{id}/segna-completata` → chiama `completa_comunicazione`

**Frontend**: nuova pagina `frontend/src/modules/affitti_brevi/pages/ComunicazioneDetail.jsx` (route `/affitti-brevi/comunicazioni/:id`), che mostra tipo/stato/scadenza/importo (se tassa) e un pulsante "Segna come completata". Aggiunto un case in `frontend/src/pages/ScadenzaResolve.jsx`'s `buildTarget()`:

```js
if (normalizedModule === 'affitti_brevi' && normalizedType === 'COMUNICAZIONE') {
  return `/affitti-brevi/comunicazioni/${entityId}`;
}
```

## 4. Modifiche ai modelli esistenti

`Comunicazione` (in `models/comunicazione.py`) guadagna un campo per il collegamento inverso alla scadenza core:

```python
scadenza_id = Column(Integer, nullable=True, index=True,
                     comment="FK logica a core_scadenze.id (cross-schema, come Scadenza.entity_id)")
```

Nessuna vera FK (la tabella `core_scadenze` vive nello schema `public`, `ab_comunicazioni` nello schema tenant — stesso motivo per cui `Scadenza.entity_id` è un intero libero, non una FK, verso le tabelle di modulo). Migrazione additiva, non distruttiva.

`AttivitaSchedulata`/`AttivitaSchedulataLog`: rimossi da `models/__init__.py` e cancellati i file; migrazione che droppa `ab_attivita_schedulate`/`ab_attivita_schedulate_log` se già create in qualche tenant (verificare con `\dt` sui tenant esistenti prima di scrivere la migrazione — se le tabelle non sono mai state create, la migrazione si limita a rimuovere eventuali riferimenti residui).

## 5. Error handling

- **Idempotenza**: ogni `genera_scadenza_*` controlla prima l'esistenza di una `Comunicazione(soggiorno_id, tipo)` — se c'è già, no-op. Stesso principio del dedup iCal via `uid_ical`.
- **Isolamento per-tenant nel job**: un errore nella generazione per un singolo soggiorno viene loggato (`logger.error(..., exc_info=True)`) e non interrompe il ciclo sugli altri soggiorni/tenant — stesso pattern di `_sync_tenant()`.
- **Soggiorno non valido**: `Soggiorno.valido == False` (conflitto di prenotazione) → nessuna scadenza generata, nessun log di errore (è un caso normale, non un fallimento).
- **Scadenza orfana**: se la `Scadenza` collegata a una `Comunicazione` è stata cancellata manualmente dal pannello notifiche (`DELETE`), `completa_comunicazione` gestisce `ScadenzaService.completa_scadenza()` che ritorna `None` senza sollevare eccezione — la `Comunicazione` viene comunque marcata come inviata.

## 6. Testing

Test di integrazione in `backend/tests/integration/test_modules/test_affitti_brevi/test_compliance_scadenze.py`, con `pg_session` bound a singola `Connection` (pattern stabilito in questa sessione):

1. `Soggiorno` con check-in tra 12h, `valido=True` → la scan del job crea `Comunicazione(POLIZIA)` + `Comunicazione(TASSA_DICHIARAZIONE)`, ciascuna con una `Scadenza` collegata; verificare `data_scadenza` corrette (checkin+24h per Polizia, checkin per tassa).
2. Rieseguendo la scan sullo stesso soggiorno, nessuna `Comunicazione`/`Scadenza` duplicata.
3. `Soggiorno.valido = False` → nessuna scadenza creata.
4. `POST /comunicazioni/{id}/segna-completata` → `Comunicazione.stato` passa a `INVIATA`, la `Scadenza` collegata passa a `COMPLETATA` (verificare via `ScadenzaService.get_scadenza`).
5. `ScadenzaResolve.jsx`'s `buildTarget()` per `modulo=affitti_brevi, entity_type=comunicazione` — verifica manuale via browser (o test Vitest se la suite per quel file esiste già; da verificare nel piano).

## 7. Riferimenti

- `app/core/platform/models/scadenza.py`, `app/core/platform_services/scadenza_service.py` — motore scadenze core (non modificato da questa spec).
- `frontend/src/components/Platform/Scadenze/NotifichePanel.jsx`, `frontend/src/pages/ScadenzaResolve.jsx` — superficie UI esistente.
- `backend/modules/affitti_brevi/services/sync_scheduler.py` — pattern di riferimento per lo scheduler multi-tenant (bound-Connection, `_get_active_tenant_schemas`).
- `docs/superpowers/specs/2026-09-14-notification-service-design.md` — servizio notifiche core, complementare non bloccante.
- Sotto-progetti successivi (non ancora specificati): B (tassa di soggiorno — calcolo e dichiarazione al comune), C (invio reale Alloggiati Web/Polizia), D (report ISTAT).
