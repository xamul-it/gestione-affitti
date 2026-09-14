# Architettura: Comunicazione tra Moduli e Servizi Core

**Stato:** Approvato — principio architetturale, si applica a partire dal prossimo modulo di dominio che dipende da un altro modulo (vedi "Quando si applica").
**Data:** 2026-09-14
**Tipo:** decisione architetturale trasversale (non un singolo sotto-progetto da implementare subito)

---

## 1. Contesto

La piattaforma "modstack" ospita moduli di dominio (`anagrafica_italiana`, `immobili`, `affitti_lungo`, `affitti_brevi`, `gestione_pec`, ...) pensati per essere installabili/distribuibili in modo indipendente (ZIP, `manage.py module install`). Oggi, quando un modulo ha bisogno di dati di un altro modulo, importa direttamente i suoi modelli SQLAlchemy Python (es. `from immobili.models import UnitaImmobiliare`) e fa query dirette, anche cross-schema.

Questo accoppia i moduli allo schema interno l'uno dell'altro e rende impossibile, in futuro, far girare un modulo come servizio realmente separato (vero microservizio) senza riscrivere tutto.

Obiettivo di questa decisione: fissare **ora** il pattern di comunicazione tra moduli, così che i nuovi moduli/funzionalità lo seguano da subito, evitando un refactor più costoso in seguito. Non richiede di riscrivere subito i moduli esistenti (vedi §7).

## 2. Principio

> **I moduli di dominio comunicano tra loro esclusivamente attraverso l'API pubblica (service layer) dell'altro modulo — mai con query dirette o import dei modelli altrui.** Il trasporto di quella chiamata può essere HTTP REST (deploy separati) oppure una chiamata Python diretta in-process, detta *shortcut* (deploy monolitico, tutti i moduli nello stesso processo/DB) — ma la superficie chiamata è sempre la stessa funzione di servizio.

Questo principio **non** si applica ai servizi core della piattaforma (vedi §3): quelli restano sempre accesso diretto, per ogni modulo, in ogni scenario di deploy.

## 3. Due categorie, due regole diverse

### 3.1 Servizi core della piattaforma — accesso diretto, sempre

Auth/permessi, `NotificationService`, `ScadenzaService`/scadenzario, `document_type_registry`, `module_system`. Vivono in `app/core/` e in schema `public`.

- **Non sono moduli sostituibili**: sono il substrato su cui ogni modulo gira. Non esiste "un core per modulo" — ne esiste uno solo, condiviso.
- Accesso: import Python diretto + `Depends(get_db)` con `search_path` già impostato dal middleware, esattamente come oggi. Nessuna chiamata REST interna, nemmeno in un deploy a moduli separati: ogni modulo (o futuro microservizio) si collega allo **stesso** DB/schema `public` per queste funzioni.
- Perché niente concorrenza/duplicazione: non essendoci mai più di un'istanza logica di "core", non si pone il problema di sincronizzare N copie — è la stessa garanzia che oggi dà lo schema `public` condiviso nel modello multi-tenant.

### 3.2 Moduli di dominio — API pubblica come confine, REST o shortcut come trasporto

`anagrafica_italiana`, `immobili`, `affitti_lungo`, `affitti_brevi`, e futuri moduli di dominio.

- Ogni modulo possiede in modo esclusivo le proprie tabelle. Nessun altro modulo vi accede mai direttamente (niente cross-schema query, niente import dei suoi modelli SQLAlchemy da parte di un altro modulo).
- Un modulo che ha bisogno di dati/azioni di un altro modulo passa sempre dal suo **service layer pubblico** (vedi §4).
- **Deploy separati** (moduli come servizi realmente indipendenti): la chiamata è una vera richiesta HTTP REST verso l'API del modulo target, con il tenant propagato (header/JWT) e il modulo target che imposta il proprio `search_path`.
- **Deploy "tutto insieme"** (monolite, come oggi — tutti i moduli nello stesso processo FastAPI, stesso DB): si usa lo **shortcut**, cioè si invoca direttamente la funzione Python del service layer del modulo target, nella stessa sessione DB/stesso `search_path` già attivo nella request corrente. Non è mai una query SQL diretta sulle tabelle altrui: è la stessa logica che l'endpoint REST richiamerebbe, solo senza il giro HTTP.

## 4. Pattern: service layer a doppia superficie

Ogni modulo di dominio che espone dati/azioni ad altri moduli definisce un modulo Python `services/public_api.py` (o equivalente) con funzioni pure che:

- Accettano `db: Session` (già con `search_path` impostato) + parametri tipizzati.
- Restituiscono dataclass/Pydantic model, mai l'oggetto ORM grezzo (evita che il chiamante dipenda dallo schema interno).
- Sono le **uniche** funzioni chiamabili da un altro modulo.

Le route FastAPI del modulo (`routes/*.py`) diventano un wrapper sottile su queste funzioni: la route fa auth/validazione HTTP e chiama `public_api.qualcosa(db, ...)`. Così la stessa funzione serve sia la vera route REST sia lo shortcut in-process — non si scrive la logica due volte.

```
modulo_a/
├── services/
│   └── public_api.py     # <- superficie pubblica per altri moduli (e per le route)
├── routes/
│   └── qualcosa.py        # route FastAPI: valida HTTP, chiama public_api, serializza risposta
```

Un modulo che consuma un altro modulo lo fa tramite un piccolo **client** (es. `immobili/clients/anagrafica_client.py`) che nasconde la scelta del trasporto:

```python
def get_contatto(db: Session, contatto_id: int) -> ContattoDTO:
    if settings.DEPLOY_MODE == "monolith":
        from anagrafica_italiana.services.public_api import get_contatto as _impl
        return _impl(db, contatto_id)
    else:
        return _http_get(f"{ANAGRAFICA_SERVICE_URL}/api/v1/contatti/{contatto_id}")
```

`DEPLOY_MODE` è una env var di piattaforma (`monolith` di default oggi). Il client è l'unico punto che conosce la differenza; il resto del modulo chiamante non lo sa mai.

## 5. Propagazione del contesto tenant

- **Shortcut in-process**: nessuna propagazione necessaria — stessa request, stessa sessione `db`, `search_path` già corretto.
- **REST reale**: il chiamante include il tenant nella richiesta (stesso schema di oggi: JWT con claim `tenant_schema`, già usato da `TenantMiddleware`); il modulo target esegue la stessa risoluzione JWT → `search_path` che farebbe per una richiesta utente normale. Nessun meccanismo nuovo da inventare: si riusa l'auth esistente, il client interno propaga semplicemente il JWT (o un service-token equivalente) nella chiamata HTTP.

## 6. Cosa succede quando due moduli sono a loro volta in relazione N:M o serve una query aggregata

Non tutto si presta a "chiedi un record alla volta" via API. Se un modulo ha bisogno di liste filtrate/aggregate che dipendono da dati di un altro modulo (es. dashboard che incrocia scadenze di `immobili` per comune), il `public_api.py` del modulo proprietario deve esporre la query aggregata come funzione dedicata (es. `list_unita_by_comune(db, comune_id) -> list[UnitaDTO]`), non lasciare che il chiamante ricostruisca la query da solo. Se una vista ha davvero bisogno di dati da 3+ moduli in tempo reale con performance critiche, si valuta caso per caso (fuori scope qui) — non è la norma, è l'eccezione.

## 7. Impatto sui moduli esistenti — non è un refactor da fare subito

Questa decisione **non** impone di riscrivere oggi `affitti_lungo`/`immobili`/`anagrafica_italiana`, che oggi si importano a vicenda direttamente. Si applica:

- A ogni **nuova** dipendenza cross-modulo che verrà introdotta a partire da ora (es. quando il sotto-progetto "immobili" o "affitti_brevi" avrà bisogno di leggere dati di `anagrafica_italiana`).
- Il refactor degli import diretti esistenti tra `affitti_lungo` → `immobili`/`anagrafica_italiana` è un debito tecnico noto, da pianificare come sotto-progetto a parte quando/se si deciderà di separare davvero quei moduli in deploy indipendenti. Non è un prerequisito bloccante per il lavoro pianificato ora (notifiche → anagrafica → immobili → affitti brevi → affitti lungo).

## 8. Non-scope

- Nessun message broker/coda asincrona (fuori scope: qui si parla solo di richiesta/risposta sincrona tra moduli).
- Nessuna scelta di deploy reale a microservizi separati ora: `DEPLOY_MODE=monolith` resta l'unico modo di girare finché non si decide altrimenti.
- Nessun API gateway/service discovery: quando (e se) si passerà a deploy separati, l'URL del servizio target sarà configurazione esplicita (env var), non discovery dinamica.

## 9. Decisioni aperte (rimandate, non bloccanti)

| # | Decisione | Quando va risolta |
|---|---|---|
| A1 | Formato esatto del "service-token" per chiamate REST modulo→modulo (oggi non serve, nessun modulo gira separato) | Al primo deploy realmente distribuito |
| A2 | Versionamento dell'API pubblica di un modulo (come evolvere `public_api.py` senza rompere i chiamanti) | Quando un secondo modulo consumer dipenderà stabilmente da un primo modulo |
