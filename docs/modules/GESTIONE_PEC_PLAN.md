# Piano di Implementazione: Modulo `gestione_pec`

**Stato:** Pianificazione completata — implementazione non ancora iniziata
**Data pianificazione:** 2026-03-19
**Complessità stimata:** ALTA

---

## Indice

1. [Contesto e obiettivo](#1-contesto-e-obiettivo)
2. [Analisi della complessità](#2-analisi-della-complessità)
3. [Modelli dati](#3-modelli-dati)
4. [Struttura file del modulo](#4-struttura-file-del-modulo)
5. [API endpoints](#5-api-endpoints)
6. [Logica di background](#6-logica-di-background)
7. [Frontend](#7-frontend)
8. [Dipendenze aggiuntive](#8-dipendenze-aggiuntive)
9. [Manifest e permessi](#9-manifest-e-permessi)
10. [Rischi e punti critici](#10-rischi-e-punti-critici)
11. [Fasi di implementazione](#11-fasi-di-implementazione)
12. [Decisioni aperte](#12-decisioni-aperte)

---

## 1. Contesto e obiettivo

Il modulo `gestione_pec` gestisce caselle PEC (Posta Elettronica Certificata) per conto dei clienti del tenant. Funziona come un **client di posta web** con audit completo, senza mai modificare o cancellare messaggi dal server remoto.

### Requisiti funzionali

| # | Requisito |
|---|---|
| R1 | L'amministratore configura le caselle PEC dei clienti (nome, credenziali IMAP/SMTP, intervallo polling) |
| R2 | I messaggi restano sempre sul server remoto — mai scaricati né eliminati |
| R3 | Gli utenti abilitati vedono i messaggi e possono rispondere come un normale client di posta |
| R4 | Ogni accesso alle caselle e ogni risposta inviata viene tracciata in un log di audit |
| R5 | Gli utenti abilitati ricevono una notifica via email quando arriva una nuova PEC per un cliente |
| R6 | Per ogni risposta inviata viene salvato uno snapshot immutabile del messaggio ricevuto e della risposta data |

### Vincoli tecnici

- **IMAP PEEK obbligatorio**: i flag `\Seen` sul server remoto non devono mai essere modificati
- **Credenziali cifrate a riposo**: le password IMAP/SMTP dei clienti vanno cifrate con Fernet
- **Multi-tenant**: ogni tenant ha le proprie caselle; il polling gira in background e deve impostare il `search_path` manualmente (nessun request context)
- **Schema target**: `tenant` (tutte le tabelle vivono nello schema del tenant)

### Dipendenze da altri moduli

Nessuna dipendenza da moduli applicativi. Dipende solo dalla piattaforma core.

---

## 2. Analisi della complessità

**Complessità: ALTA**

Non per difficoltà delle singole parti, ma per la loro combinazione:

| Rischio | Impatto | Dettaglio |
|---|---|---|
| Cifratura credenziali | Critico | Fernet con chiave derivata da `SECRET_KEY`; se la chiave cambia tutte le caselle diventano inaccessibili |
| IMAP PEEK + stato locale | Alto | Lo stato "letto" non si propaga mai al server; gestione completa lato DB |
| Scheduler multi-casella multi-tenant | Alto | Un job APScheduler per casella; il job deve impostare `SET search_path` manualmente |
| SMTP autenticato come casella PEC | Medio | Rispondere "da" `cliente@legalmail.it` richiede auth SMTP con credenziali di quella casella; alcuni provider PEC impongono IP allowlist |
| Primo sync caselle storiche | Medio | Caselle attive da anni possono avere migliaia di messaggi; il primo polling deve essere limitato |
| Rendering HTML sicuro | Alto | I corpi delle PEC sono HTML non trusted — XSS reale se non sanitizzato |

---

## 3. Modelli dati

Tutte le tabelle hanno prefisso `pec_` e schema target `tenant`.

### 3.1 `pec_caselle`

Configurazione di una casella PEC di un cliente.

```python
class PecCasella(Base):
    __tablename__ = "pec_caselle"

    id                          Integer PK
    nome_display                String(200)     # "PEC Rossi SpA"
    indirizzo_pec               String(255)     # "rossi@legalmail.it"

    # IMAP (lettura)
    imap_host                   String(255)     # "imappec.legalmail.it"
    imap_port                   Integer         # default 993
    imap_ssl                    Boolean         # default True
    imap_folder                 String(100)     # default "INBOX"

    # SMTP (invio risposte)
    smtp_host                   String(255)
    smtp_port                   Integer         # default 465
    smtp_tls                    String(20)      # "SSL" | "STARTTLS" | "none"

    # Credenziali (sempre cifrate con Fernet)
    username_enc                Text
    password_enc                Text

    # Polling
    polling_intervallo_minuti   Integer         # default 15, min 5
    is_attiva                   Boolean         # default True
    ultimo_polling_at           DateTime
    ultimo_uid_visto            String(100)     # per polling incrementale
    errori_consecutivi          Integer         # default 0
    ultimo_errore               Text

    note                        Text
    created_at                  DateTime
    updated_at                  DateTime
```

**Constraint:** `UNIQUE(indirizzo_pec)` per tenant.

### 3.2 `pec_utenti_abilitati`

Quale utente di piattaforma può accedere a quale casella.

```python
class PecUtenteAbilitato(Base):
    __tablename__ = "pec_utenti_abilitati"

    id              Integer PK
    casella_id      FK → pec_caselle.id CASCADE
    user_id         Integer             # riferimento a core_users.id (cross-schema)
    puo_rispondere  Boolean             # default False
    notifica_email  Boolean             # default True

    created_at      DateTime
```

**Constraint:** `UNIQUE(casella_id, user_id)`.

### 3.3 `pec_messaggi`

Cache locale dei messaggi. Il corpo viene salvato per permettere la risposta e l'audit, ma i messaggi non vengono mai eliminati dal server remoto.

```python
class PecMessaggio(Base):
    __tablename__ = "pec_messaggi"

    id              Integer PK
    casella_id      FK → pec_caselle.id CASCADE

    # Identificatori IMAP/RFC 822
    uid_imap        String(100)         # UID IMAP (stabile, non sequence number)
    message_id      String(500)         # Header Message-ID
    in_reply_to     String(500)         # Header In-Reply-To
    thread_id       String(500)         # Message-ID della radice del thread (calcolato)

    # Headers
    da              String(500)
    a               Text
    cc              Text
    oggetto         String(1000)
    data_invio      DateTime            # Header Date
    data_ricezione  DateTime            # Timestamp del nostro polling

    # Corpo
    corpo_testo     Text                # part text/plain
    corpo_html      Text                # part text/html

    # Allegati (solo metadati, mai i file)
    allegati_meta   JSON                # [{nome, content_type, dimensione_bytes, part_id}]

    # Stato locale (MAI propagato al server)
    is_letto        Boolean             # default False
    is_risposto     Boolean             # default False

    # Deduplicazione
    hash_contenuto  String(64)          # SHA-256(da + oggetto + data_invio)

    created_at      DateTime
```

**Constraint:** `UNIQUE(casella_id, uid_imap)`.

### 3.4 `pec_audit_accessi`

Ogni apertura di casella o lettura di messaggio da parte di un utente.

```python
class PecAuditAccesso(Base):
    __tablename__ = "pec_audit_accessi"

    id              Integer PK
    casella_id      FK → pec_caselle.id
    messaggio_id    FK → pec_messaggi.id nullable
    user_id         Integer
    azione          String(50)          # OPEN_CASELLA | READ_MESSAGE | SEARCH
    ip_address      String(45)
    user_agent      Text
    dettagli        JSON                # contesto aggiuntivo
    timestamp       DateTime            # server_default=now(), no update
```

**Nota:** tabella append-only, nessun update, nessun delete.

### 3.5 `pec_audit_risposte`

Snapshot immutabile per ogni risposta inviata (requisito R6).

```python
class PecAuditRisposta(Base):
    __tablename__ = "pec_audit_risposte"

    id                          Integer PK
    casella_id                  FK → pec_caselle.id
    messaggio_originale_id      FK → pec_messaggi.id
    user_id                     Integer

    # Risposta inviata
    destinatari                 Text
    oggetto_risposta            String(1000)
    corpo_risposta_testo        Text
    corpo_risposta_html         Text
    message_id_risposta         String(500)     # Message-ID assegnato all'invio

    # Snapshot immutabile del messaggio originale al momento della risposta
    snapshot_da                 String(500)
    snapshot_oggetto            String(1000)
    snapshot_corpo_testo        Text
    snapshot_data_invio         DateTime

    # Stato invio
    smtp_status                 String(20)      # SENT | FAILED | QUEUED
    smtp_error                  Text

    # Integrità
    hash_integrita              String(64)      # SHA-256 del contenuto completo

    inviato_at                  DateTime
    created_at                  DateTime
```

**Nota:** tabella append-only. Il campo `hash_integrita` garantisce non-ripudio.

### 3.6 `pec_notifiche_log`

Log delle notifiche email inviate agli utenti alla ricezione di nuove PEC.

```python
class PecNotificaLog(Base):
    __tablename__ = "pec_notifiche_log"

    id                  Integer PK
    casella_id          FK → pec_caselle.id
    messaggio_id        FK → pec_messaggi.id
    user_id             Integer
    email_destinatario  String(255)
    stato               String(20)      # SENT | FAILED
    errore              Text
    sent_at             DateTime
```

### Relazioni tra tabelle

```
pec_caselle ─┬─< pec_utenti_abilitati (N utenti per casella)
             ├─< pec_messaggi (N messaggi per casella)
             │     └─< pec_audit_accessi (N accessi per messaggio)
             │     └─< pec_audit_risposte (N risposte per messaggio)
             │     └─< pec_notifiche_log (N notifiche per messaggio)
             └─< pec_audit_accessi (accessi alla casella senza msg specifico)
```

---

## 4. Struttura file del modulo

```
backend/modules/gestione_pec/
├── __manifest__.py
├── __init__.py                     # register(), install(), register_module(app), ROUTERS
├── roles.py                        # register_roles() — pec.admin, pec.read, pec.reply, pec.audit.view
│
├── models/
│   ├── __init__.py
│   ├── casella.py
│   ├── utente_abilitato.py
│   ├── messaggio.py
│   ├── audit_accesso.py
│   ├── audit_risposta.py
│   └── notifica_log.py
│
├── schemas/
│   ├── __init__.py
│   ├── casella.py                  # CasellaCreate, CasellaUpdate, CasellaRead, CasellaReadAdmin
│   ├── utente_abilitato.py         # UtenteAbilitatoCreate, UtenteAbilitatoRead
│   ├── messaggio.py                # MessaggioList, MessaggioDetail
│   ├── risposta.py                 # RispostaCreate, RispostaRead
│   └── audit.py                    # AuditAccessoRead, AuditRispostaRead
│
├── routes/
│   ├── __init__.py
│   ├── caselle.py                  # CRUD caselle + gestione utenti abilitati (pec.admin)
│   ├── messaggi.py                 # Lista e lettura messaggi (pec.read)
│   ├── risposte.py                 # Invio risposte (pec.reply)
│   ├── audit.py                    # Log audit (pec.audit.view)
│   └── scheduler.py               # Status e trigger manuale polling (pec.admin)
│
├── services/
│   ├── __init__.py
│   ├── crypto_service.py           # Fernet encrypt/decrypt credenziali
│   ├── imap_service.py             # Connessione IMAP, PEEK fetch, parsing MIME
│   ├── smtp_service.py             # Invio SMTP autenticato come casella PEC
│   ├── polling_scheduler.py        # APScheduler: un job per casella attiva
│   ├── notification_service.py     # Notifiche email via SMTP applicativo
│   └── audit_service.py            # Scrittura centralizzata audit log
│
├── migrations/
│   └── versions/
│       └── 2026031901_create_pec_tables.py
│
└── seeds/
    └── __init__.py                 # Nessun seed (caselle create dall'admin)

frontend/src/modules/gestione_pec/
├── manifest.js
├── index.js
│
├── services/
│   └── pecAPI.js
│
├── components/
│   ├── Caselle/
│   │   ├── CaselleList.jsx         # Lista caselle con stato polling (admin)
│   │   ├── CasellaForm.jsx         # Crea/modifica casella, test connessione
│   │   └── UtentiAbilitatiPanel.jsx # Gestione accessi utenti per casella
│   │
│   ├── Messaggi/
│   │   ├── MessaggiList.jsx        # Lista messaggi: Da/Oggetto/Data/Letto, filtri, paginazione
│   │   ├── MessaggioDetail.jsx     # Corpo (HTML sanitizzato), allegati, pulsante Rispondi
│   │   └── MessaggioThread.jsx     # Vista thread messaggi correlati
│   │
│   ├── Risposta/
│   │   ├── RispostaModal.jsx       # Composer risposta con editor
│   │   └── RispostaConfirm.jsx     # Conferma esplicita prima dell'invio
│   │
│   ├── Audit/
│   │   ├── AuditAccessiTable.jsx
│   │   └── AuditRisposteTable.jsx  # Con espansione snapshot messaggio originale
│   │
│   └── Widgets/
│       └── PecSummaryWidget.jsx    # Dashboard: N nuove PEC per casella
│
└── pages/
    ├── PecInboxPage.jsx            # Shell: selezione casella + lista messaggi
    └── PecAdminPage.jsx            # Tab caselle / utenti / audit / scheduler
```

---

## 5. API endpoints

Prefisso: `/api/v1/pec`

### Caselle (permesso: `pec.admin`)

| Metodo | Path | Descrizione |
|---|---|---|
| `GET` | `/caselle` | Lista caselle con stato polling |
| `POST` | `/caselle` | Crea nuova casella |
| `GET` | `/caselle/{id}` | Dettaglio casella (password sempre oscurata) |
| `PUT` | `/caselle/{id}` | Modifica casella |
| `DELETE` | `/caselle/{id}` | Disattiva casella (soft delete) |
| `POST` | `/caselle/{id}/test-connessione` | Test IMAP live, risposta entro timeout |
| `GET` | `/caselle/{id}/utenti` | Lista utenti abilitati |
| `POST` | `/caselle/{id}/utenti` | Abilita utente |
| `PUT` | `/caselle/{id}/utenti/{user_id}` | Modifica permessi utente |
| `DELETE` | `/caselle/{id}/utenti/{user_id}` | Revoca accesso |

### Messaggi (permesso: `pec.read`)

| Metodo | Path | Descrizione |
|---|---|---|
| `GET` | `/messaggi` | Lista messaggi (query: `casella_id`, `is_letto`, `page`, `q`) |
| `GET` | `/messaggi/{id}` | Dettaglio messaggio (registra audit READ_MESSAGE) |
| `POST` | `/messaggi/{id}/segna-letto` | Marca come letto localmente |
| `GET` | `/messaggi/{id}/thread` | Tutti i messaggi del thread |
| `GET` | `/caselle/{id}/messaggi` | Messaggi di una casella specifica |

### Risposte (permesso: `pec.reply`)

| Metodo | Path | Descrizione |
|---|---|---|
| `POST` | `/messaggi/{id}/rispondi` | Invia risposta + salva audit_risposta con snapshot |
| `GET` | `/messaggi/{id}/risposte` | Storico risposte a questo messaggio |

### Audit (permesso: `pec.audit.view`)

| Metodo | Path | Descrizione |
|---|---|---|
| `GET` | `/audit/accessi` | Log accessi con filtri (casella, utente, periodo) |
| `GET` | `/audit/risposte` | Log risposte con filtri |
| `GET` | `/audit/risposte/{id}` | Dettaglio risposta con snapshot completo |

### Scheduler (permesso: `pec.admin`)

| Metodo | Path | Descrizione |
|---|---|---|
| `GET` | `/scheduler/status` | Stato job (attivi, prossima esecuzione, errori) |
| `POST` | `/scheduler/trigger/{casella_id}` | Polling immediato per una casella |
| `POST` | `/scheduler/trigger-all` | Polling immediato su tutte le caselle attive |

---

## 6. Logica di background

### 6.1 Polling IMAP (`polling_scheduler.py`)

**Pattern di riferimento:** `backend/modules/affitti_brevi/services/sync_scheduler.py`

**Differenze chiave rispetto al sync_scheduler esistente:**

- Un job APScheduler **per casella** (non uno globale). `job_id = f"pec_poll_{casella.id}"`.
- L'intervallo è letto da `casella.polling_intervallo_minuti` (configurabile per casella).
- Il job include il `tenant_schema` nel suo contesto — passato come parametro alla funzione del job.
- Nel job: `db = SessionLocal()` + `db.execute(text(f"SET search_path TO {tenant_schema}, public"))` (nessun `get_db()` dependency disponibile fuori da request context).
- `max_instances=1` per job per evitare connessioni IMAP concorrenti sulla stessa casella.

**Algoritmo polling:**

```
1. Connetti IMAP con credenziali decifrate (imap_service.connect())
2. SELECT INBOX
3. IMAP UID SEARCH: "UID {ultimo_uid_visto}:*" (solo messaggi nuovi)
4. Per ogni UID trovato (escluso ultimo_uid_visto stesso):
   a. FETCH con BODY.PEEK[] (non imposta \Seen sul server)
   b. Parsa MIME: estrai headers, corpo testo/html, metadati allegati
   c. Calcola hash_contenuto per deduplicazione
   d. INSERT INTO pec_messaggi (ignora se UNIQUE conflict)
   e. Aggiorna casella.ultimo_uid_visto
5. Se nuovi messaggi inseriti: chiama notification_service
6. Aggiorna casella.ultimo_polling_at, azzera errori_consecutivi
7. Su errore: incrementa errori_consecutivi, salva ultimo_errore
   Se errori_consecutivi >= 5: disattiva casella, notifica admin
```

**Primo sync (caselle storiche):**

Al primo polling (`ultimo_uid_visto IS NULL`), limitare a **ultimi 500 UID** o **ultimi 30 giorni** per evitare sync infiniti su caselle con anni di storia.

### 6.2 Gestione dinamica dei job

All'avvio del modulo (`register_module(app)`):
- Query su `pec_caselle WHERE is_attiva = True` per tutti i tenant attivi
- `scheduler.add_job(...)` per ogni casella

Alle modifiche via API:
- `POST /caselle` → `scheduler.add_job(...)`
- `PUT /caselle/{id}` (cambio intervallo) → `scheduler.reschedule_job(...)`
- `DELETE /caselle/{id}` → `scheduler.remove_job(...)`
- Attivazione/disattivazione → `scheduler.pause_job` / `scheduler.resume_job`

### 6.3 Notifiche email (`notification_service.py`)

Invocato dal polling job dopo ogni batch di nuovi messaggi.

- Query `pec_utenti_abilitati WHERE casella_id=X AND notifica_email=True`
- Per ogni utente: recupera email da `core_users` (query cross-schema con `public.core_users`)
- Invia via **SMTP applicativo** (configurato in `Settings`, distinto dalla PEC del cliente):
  ```
  NOTIFICHE_SMTP_HOST
  NOTIFICHE_SMTP_PORT
  NOTIFICHE_SMTP_USER
  NOTIFICHE_SMTP_PASSWORD
  NOTIFICHE_FROM_EMAIL
  ```
- Salva esito in `pec_notifiche_log`
- Errori di notifica non bloccano il polling (try/except per ogni utente)

### 6.4 Cifratura credenziali (`crypto_service.py`)

```python
# Chiave derivata da SECRET_KEY della piattaforma (non salvata in DB)
key = base64.urlsafe_b64encode(PBKDF2HMAC(SECRET_KEY, salt=b"pec_creds").derive())
fernet = Fernet(key)

encrypt(plaintext: str) -> str   # cifra e restituisce stringa base64
decrypt(ciphertext: str) -> str  # decifra, lancia eccezione se chiave errata
```

**Importante:** le credenziali decifrate non vengono mai loggate né serializzate in JSON di risposta. Gli schema Pydantic `CasellaRead` non includono i campi `*_enc`.

---

## 7. Frontend

### Flusso principale (utente abilitato)

```
PecInboxPage
├── Sidebar: lista caselle a cui ho accesso (con badge messaggi non letti)
├── MessaggiList: tabella Da / Oggetto / Data / icona-letto
│   ├── Filtri: Non letti / Tutti / Con risposta
│   ├── Ricerca full-text su oggetto/da
│   └── Polling automatico ogni 60s (setInterval)
└── MessaggioDetail (pannello destro o pagina dedicata)
    ├── Header: Da, A, CC, Oggetto, Data
    ├── Corpo: HTML sanitizzato con DOMPurify o iframe sandbox
    ├── Allegati: lista con nome/dimensione (no download diretto, apre via API)
    └── Azioni: [Rispondi] (visibile solo se puo_rispondere=True)
```

### Rendering HTML sicuro

Due opzioni, scegliere in implementazione:
- **DOMPurify**: `dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(corpo_html) }}`
- **iframe sandbox**: `<iframe sandbox="allow-same-origin" srcdoc={corpo_html} />`

Preferire l'iframe per isolamento completo.

### Composer risposta (`RispostaModal`)

- Prepopola: `To = {da originale}`, `Subject = Re: {oggetto}`
- Editor: textarea semplice (non rich-text in v1, riduce la complessità)
- Pulsante "Invia" disabilitato dopo il primo click (prevenzione doppio invio)
- Conferma esplicita: "Stai per inviare una risposta a nome di {indirizzo_pec}. Confermi?"

### Pagina admin (`PecAdminPage`)

Tab 1 — **Caselle:** DataTable caselle con stato polling, errori, ultima esecuzione. Pulsante Test Connessione che chiama l'endpoint live e mostra esito.

Tab 2 — **Utenti abilitati:** per casella selezionata, gestione chi può leggere / rispondere / ricevere notifiche.

Tab 3 — **Audit accessi:** tabella con filtri per casella, utente, azione, periodo.

Tab 4 — **Audit risposte:** tabella espandibile con snapshot completo messaggio originale + risposta inviata.

Tab 5 — **Scheduler:** stato job attivi, prossima esecuzione, pulsante "Forza polling" per casella.

### Widget dashboard

`PecSummaryWidget`: lista caselle a cui l'utente ha accesso con badge N nuovi messaggi non letti. Refresh automatico ogni 5 minuti.

---

## 8. Dipendenze aggiuntive

### Python (aggiungere a `requirements.txt`)

```
imapclient>=2.3.1      # wrapper IMAP con UID, SSL, PEEK più comodo di imaplib nativo
cryptography>=41.0     # Fernet — verificare se già presente come dep transitiva di python-jose
```

`smtplib`, `email` (MIME), `hashlib` sono stdlib — nessuna installazione richiesta.

### Frontend (aggiungere a `package.json`)

```
dompurify               # sanitizzazione HTML email
@types/dompurify        # se TypeScript
```

### Non necessario installare

- `apscheduler` — già in `requirements.txt`
- `aiosmtplib` — il polling è sincrono (BackgroundScheduler), smtplib stdlib è sufficiente

---

## 9. Manifest e permessi

```python
manifest = {
    "name": "Gestione PEC",
    "technical_name": "gestione_pec",
    "version": "2026031901",
    "module_short_code": "pec",
    "schema_target": "tenant",
    "migrations_path": "migrations/versions",
    "seeds_path": "seeds",
    "author": "Modstack Team",
    "sequence": 200,
    "dependencies": [],             # nessuna dipendenza da altri moduli applicativi

    "endpoints": {
        "register_roles": "roles:register_roles",
    },

    "tenant_tables": [
        "pec_caselle",
        "pec_utenti_abilitati",
        "pec_messaggi",
        "pec_audit_accessi",
        "pec_audit_risposte",
        "pec_notifiche_log",
    ],

    "permissions": [
        {"name": "pec.admin",       "description": "Configurare caselle PEC e utenti abilitati"},
        {"name": "pec.read",        "description": "Leggere messaggi PEC"},
        {"name": "pec.reply",       "description": "Rispondere a messaggi PEC"},
        {"name": "pec.audit.view",  "description": "Visualizzare log di audit PEC"},
    ],

    "ruoli_disponibili": [
        {"codice": "pec_admin",    "nome_display": "PEC Amministratore"},
        {"codice": "pec_operator", "nome_display": "PEC Operatore"},
        {"codice": "pec_viewer",   "nome_display": "PEC Lettore"},
    ],

    "menu_items": [
        {
            "id": "pec_inbox",
            "label": "Caselle PEC",
            "icon": "EnvelopeIcon",
            "path": "/pec",
            "permission": "pec.read",
            "order": 50,
        },
        {
            "id": "pec_admin",
            "label": "Configura PEC",
            "icon": "CogIcon",
            "path": "/pec/admin",
            "permission": "pec.admin",
            "parent": "admin",
            "order": 60,
        },
    ],

    "widgets": [
        {
            "id": "pec_summary",
            "name": "PEC Summary",
            "component": "PecSummaryWidget",
            "permission": "pec.read",
        },
    ],
}
```

---

## 10. Rischi e punti critici

### R1 — Cifratura credenziali (CRITICO)

**Problema:** se `SECRET_KEY` cambia, tutte le credenziali cifrate diventano illeggibili.

**Mitigazione:**
- Documentare esplicitamente che `SECRET_KEY` non deve cambiare in produzione
- Aggiungere health-check all'avvio: tenta decifratura di ogni casella attiva, logga warning se fallisce
- Prevedere un comando CLI `manage.py pec rekey --old-key X --new-key Y` per rotazione chiave

### R2 — Connessioni IMAP concorrenti (ALTO)

**Problema:** alcuni provider PEC (Aruba, Legalmail, Namirial) limitano le connessioni simultanee dallo stesso IP.

**Mitigazione:**
- `max_instances=1` per job in APScheduler (già disponibile)
- Aggiungere jitter randomico all'avvio dei job (evita che tutti i job partano insieme)
- Esporre `errori_consecutivi` nell'API scheduler per monitoraggio

### R3 — Primo sync caselle storiche (MEDIO)

**Problema:** caselle con anni di storico bloccano il server al primo polling.

**Mitigazione:**
- Al primo polling (`ultimo_uid_visto IS NULL`): `UID SEARCH UID *-500:*` (ultimi 500) oppure `SINCE {30_giorni_fa}`
- Aggiungere campo `sync_mode` in manifest: `"incremental"` (default) o `"full"` (solo per admin esperti)

### R4 — SMTP outbound come PEC cliente (MEDIO)

**Problema:** rispondere "da" la casella PEC del cliente richiede SMTP auth con le sue credenziali. Alcune configurazioni PEC richiedono che l'IP mittente sia in allowlist.

**Mitigazione:**
- Test connessione SMTP nell'endpoint `/test-connessione` (non solo IMAP)
- Esporre `smtp_status` nell'audit risposta per diagnostica
- Gestire timeout SMTP con valore configurabile

### R5 — Multi-tenancy nel job background (MEDIO)

**Problema:** il job APScheduler non ha request context FastAPI, quindi `get_db()` non funziona con il `search_path` corretto.

**Mitigazione (pattern dal `sync_scheduler.py` esistente):**
```python
def poll_job(casella_id: int, tenant_schema: str):
    db = SessionLocal()
    try:
        db.execute(text(f"SET search_path TO {tenant_schema}, public"))
        # ... logica polling
    finally:
        db.close()
```

### R6 — XSS nel rendering HTML (ALTO)

**Problema:** il corpo HTML di una PEC può contenere script malevoli.

**Mitigazione:**
- Sanitizzare **sempre** con DOMPurify prima del render, oppure usare `<iframe sandbox>`
- Mai usare `dangerouslySetInnerHTML` senza sanitizzazione
- Aggiungere Content Security Policy header alla risposta API per il corpo HTML

---

## 11. Fasi di implementazione

### Fase 1 — Fondamenta (Effort: MEDIO)

**Obiettivo:** caselle configurabili, credenziali sicure, test connessione.

Deliverable:
- [ ] Tutti i modelli SQLAlchemy + migration Alembic
- [ ] `crypto_service.py` con test unitari
- [ ] Schema Pydantic (oscuramento password in output)
- [ ] Route CRUD caselle (admin)
- [ ] Route gestione utenti abilitati
- [ ] Endpoint `POST /caselle/{id}/test-connessione` (IMAP live)
- [ ] `__manifest__.py` completo
- [ ] Frontend: `PecAdminPage` Tab Caselle + `CasellaForm`

**Pattern da seguire:** `affitti_lungo/__manifest__.py` per manifest, `anagrafica_italiana/models/` per struttura modelli.

---

### Fase 2 — Polling IMAP (Effort: ALTO)

**Obiettivo:** messaggi che arrivano automaticamente nel DB locale.

Deliverable:
- [ ] `imap_service.py`: connessione, PEEK fetch, parsing MIME completo
- [ ] `polling_scheduler.py`: gestione dinamica job per casella, backoff su errori
- [ ] Integrazione con `register_module(app)` per avvio scheduler al boot
- [ ] Deduplicazione su `(casella_id, uid_imap)`
- [ ] Limite primo sync (500 UID o 30 giorni)
- [ ] Test con mock IMAP (`unittest.mock`)

**Pattern da seguire:** `affitti_brevi/services/sync_scheduler.py`

---

### Fase 3 — Lettura messaggi (Effort: BASSO-MEDIO)

**Obiettivo:** gli utenti vedono e leggono i messaggi.

Deliverable:
- [ ] Route messaggi: lista paginata, filtri, dettaglio
- [ ] `audit_service.py`: registrazione accessi
- [ ] Frontend: `PecInboxPage`, `MessaggiList`, `MessaggioDetail`
- [ ] Rendering HTML sicuro (DOMPurify o iframe)
- [ ] Polling automatico FE ogni 60s

---

### Fase 4 — Risposta e audit completo (Effort: MEDIO)

**Obiettivo:** gli utenti possono rispondere; ogni risposta viene archiviata.

Deliverable:
- [ ] `smtp_service.py`: SMTP autenticato, costruzione MIME reply, gestione errori
- [ ] Route `POST /messaggi/{id}/rispondi` con salvataggio snapshot immutabile
- [ ] Hash integrità su `pec_audit_risposte`
- [ ] Frontend: `RispostaModal`, `RispostaConfirm`
- [ ] Frontend: `AuditRisposteTable` con espansione snapshot

---

### Fase 5 — Notifiche (Effort: BASSO)

**Obiettivo:** gli utenti ricevono email quando arriva una nuova PEC.

Deliverable:
- [ ] `notification_service.py`: SMTP applicativo, template email notifica
- [ ] Variabili `NOTIFICHE_SMTP_*` in `app/core/config.py`
- [ ] Health-check SMTP notifiche all'avvio modulo
- [ ] Log in `pec_notifiche_log`

---

### Fase 6 — Dashboard e rilascio (Effort: BASSO-MEDIO)

**Obiettivo:** widget, pagina admin completa, pacchetto ZIP.

Deliverable:
- [ ] Frontend: `PecSummaryWidget` per dashboard
- [ ] Frontend: tab Audit e Scheduler in `PecAdminPage`
- [ ] Frontend: `AuditAccessiTable`
- [ ] Test end-to-end con provider PEC reale (Aruba o Legalmail sandbox)
- [ ] Build ZIP: `./build_module.sh gestione_pec`
- [ ] Documentazione operativa (credenziali, rotazione chiave, primo sync)

---

## 12. Decisioni aperte

| # | Decisione | Opzioni | Default suggerito |
|---|---|---|---|
| D1 | Provider SMTP per notifiche applicativo | Stesso server della piattaforma / SMTP dedicato / SendGrid | SMTP configurabile in `.env` |
| D2 | Rendering HTML email | DOMPurify + dangerouslySetInnerHTML / iframe sandbox | iframe sandbox (più sicuro) |
| D3 | Editor risposta | Textarea plain / Rich-text (Quill/TipTap) | Textarea in v1, rich-text in v2 |
| D4 | Download allegati | Mai / Solo metadati / Proxy download via API | Proxy via API (allegati mai esposti direttamente) |
| D5 | Limite primo sync | 500 UID / 30 giorni / configurabile per casella | 30 giorni, configurabile |
| D6 | Rotazione chiave Fernet | Comando CLI / Processo manuale | Comando CLI `manage.py pec rekey` (da implementare) |
| D7 | Real-time notifiche FE | Polling ogni 60s / WebSocket / SSE | Polling in v1 |

---

## File di riferimento nel progetto

| File | Perché è rilevante |
|---|---|
| `backend/modules/affitti_lungo/__manifest__.py` | Pattern manifest completo con permessi, menu, widget, ruoli |
| `backend/modules/affitti_brevi/services/sync_scheduler.py` | Pattern APScheduler da replicare per polling IMAP |
| `backend/modules/affitti_brevi/__init__.py` | Pattern `register_module(app)` con avvio scheduler |
| `backend/app/core/database.py` | `SessionLocal()` + search_path per background job |
| `backend/app/core/config.py` | Dove aggiungere variabili SMTP notifiche e chiave Fernet |
| `backend/manage.py` | CLI `module link` per sviluppo del modulo in repo separato |
| `build_module.sh` | Build ZIP per distribuzione |
