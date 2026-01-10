# Analisi Tecnico-Funzionale: Modulo Anagrafica Italiana

**Versione:** 1.1
**Data:** 9 Dicembre 2025
**Stato Attuale:** Sistema Ruoli Azienda completato, Sistema Ruoli Business parziale, funzionalità avanzate da implementare
**Ultima Verifica:** 9 Dicembre 2025 (vedi ANAGRAFICA_VERIFICA_IMPLEMENTAZIONE.md)

---

## 1. Panoramica del Modulo

### 1.1 Obiettivi del Modulo

Il modulo **Anagrafica Italiana** (nome tecnico: `anagrafica_italiana`, display: "Anagrafiche") è il modulo fondamentale della piattaforma che gestisce:

- **Soggetti Anagrafici**: persone fisiche e giuridiche secondo normativa italiana
- **Identità Digitale**: collegamento opzionale tra anagrafica e utenti di sistema
- **Ruoli Azienda**: associazioni persona fisica ↔ persona giuridica con ruoli lavorativi (✅ IMPLEMENTATO)
- **Ruoli di Business**: sistema di ruoli trasversali ai moduli per cono di visibilità (⚠️ PARZIALE)
- **Dati di Dominio**: comuni italiani, tipi documento, tipi ruolo azienda
- **Gestione Documentale**: upload e gestione documenti di identità e fiscali

### 1.2 Stato Attuale dell'Implementazione

#### ✅ COMPLETATO

**Backend - Anagrafica Base:**
- ✅ Modello `SoggettoAnagrafico` con campo `user_id` per link a sistema
- ✅ Modello `ComuneItalia` (~8000 comuni italiani con codici ISTAT e CAP)
- ✅ Modello `TipoDocumento` con 11 tipi standard (CI, Passaporto, CF, Patente, etc.)
- ✅ API CRUD complete per soggetti (`/api/v1/anagrafica/soggetti`)
- ✅ API domini per comuni e tipi documento (`/api/v1/anagrafica/domini/...`)
- ✅ Seed data per tipi documento
- ✅ Schema Pydantic per validazione
- ✅ User management: creazione user da soggetto, JWT con soggetto_id

**Backend - Sistema Ruoli Azienda (NUOVO ✅):**
- ✅ Modello `RuoloAzienda` (associazioni persona fisica ↔ persona giuridica)
- ✅ Modello `RuoloAziendaTipo` (domini ruoli standardizzati)
- ✅ API CRUD complete per ruoli azienda (`/api/v1/anagrafica/ruoli-azienda`)
- ✅ API CRUD per domini ruoli (`/api/v1/anagrafica/domini/ruoli-azienda-tipi`)
- ✅ Endpoint `/ruoli-azienda/soggetto/{id}` con formato `{come_persona: [], come_azienda: []}`
- ✅ Seed data: 8 ruoli standard (Segretaria, Amministratore Delegato, ecc.)
- ✅ Supporto storicizzazione (data_inizio, data_fine)
- ✅ Linking domini normalizzati + fallback ruolo testuale

**Backend - Gestione Documenti:**
- ✅ Upload documenti con scadenzario integrato
- ✅ API lista documenti con filtri (categoria, scaduti)
- ✅ Integrazione con DocumentService e ScadenzarioService

**Frontend - UI Completa:**
- ✅ `SoggettiAnagraficiList.jsx` - Lista generale soggetti
- ✅ `PersoneFisicheList.jsx` - Lista persone fisiche
- ✅ `PersoneGiuridicheList.jsx` - Lista persone giuridiche
- ✅ `PersonaFisicaDetail.jsx` - Vista dettaglio persona fisica (tabs: anagrafica, documenti, ruoli azienda)
- ✅ `PersonaGiuridicaDetail.jsx` - Vista dettaglio persona giuridica (tabs: anagrafica, documenti, persone associate)
- ✅ `RuoliAziendaSection.jsx` - Sezione ruoli nelle schede dettaglio (vista adattiva)
- ✅ `RuoliAziendaList.jsx` - Lista centralizzata tutte le associazioni ruolo
- ✅ `RuoloAziendaForm.jsx` - Form creazione/modifica ruolo (SELECT + opzione custom)
- ✅ `RuoliAziendaTipiList.jsx` - CRUD completo domini ruoli
- ✅ `ComuniList.jsx` - Gestione comuni
- ✅ `DocumentoUpload.jsx` - Upload documenti
- ✅ Styling responsive con stati empty/loading/error
- ✅ Menu dinamico registrato da manifest
- ✅ Route complete per tutte le viste

#### ⚠️ PARZIALE

**Sistema Ruoli Business (core):**
- ✅ Modelli esistenti: `RuoloDisponibile`, `SoggettoRuolo` (in `app/core/models/ruoli.py`)
- ✅ Tabelle database create
- ❌ API endpoints non implementati
- ❌ Registrazione automatica da manifest non implementata
- ❌ UI per assegnazione ruoli business assente

**Vista Dettaglio:**
- ⚠️ Implementate viste separate `PersonaFisicaDetail` e `PersonaGiuridicaDetail` invece di `SoggettoDetail` unificato (scelta architetturale)

#### ❌ DA IMPLEMENTARE

**Funzionalità Avanzate:**
- ❌ Sistema Ruoli Business completo (API + UI + registrazione automatica)
- ❌ VisibilityService per cono di visibilità basato su ruoli business
- ❌ Import/Export CSV/Excel con template e validazione
- ❌ AddressNormalizer con autocomplete comuni
- ❌ Dashboard widget anagrafica (StatsSoggettiWidget, documenti in scadenza)
- ❌ Form unificato SoggettoForm (attualmente form separati per PF/PG)

### 1.3 Chiarimento: Due Sistemi di Ruoli Distinti

**IMPORTANTE**: Il modulo anagrafica gestisce DUE sistemi di ruoli completamente diversi, ognuno con scopo e implementazione propri.

| Caratteristica | Sistema Ruoli Azienda | Sistema Ruoli Business |
|----------------|------------------------|------------------------|
| **Scopo** | Tracciare relazioni lavorative PF-PG | Determinare cono di visibilità dati |
| **Esempio** | "Mario Rossi è **Segretaria** presso Azienda X" | "Mario Rossi è **Proprietario** immobile 42" |
| **Gestito da** | Modulo `anagrafica_italiana` | Core platform (`app/core/models/ruoli.py`) |
| **Tabelle DB** | `ruoli_azienda`, `ruoli_azienda_tipi` | `ruoli_disponibili`, `soggetti_ruoli` |
| **Domini** | Segretaria, Amm. Delegato, Direttore, ecc. | Proprietario, Affittuario, Tecnico, Fornitore |
| **Utilizzato per** | Storicizzare impieghi, organigrammi | Filtrare query, permessi visualizzazione |
| **Stato Implementazione** | ✅ **COMPLETO** (backend + frontend) | ⚠️ **PARZIALE** (solo modelli) |
| **API Endpoint** | `/api/v1/anagrafica/ruoli-azienda` | ❌ Non implementati |
| **UI Components** | 4 componenti completi | ❌ Non implementati |

**Entrambi i sistemi coesistono** e servono scopi differenti:
- Un soggetto può essere **Segretaria in Azienda X** (Ruolo Azienda) E **Proprietario dell'immobile 42** (Ruolo Business) contemporaneamente
- I Ruoli Azienda servono per organigrammi e storico lavorativo
- I Ruoli Business servono per determinare quali dati l'utente può vedere quando accede al sistema

**Nota Storica**: Il Sistema Ruoli Azienda è stato implementato completamente ma non era presente nel documento originale di analisi. Questo documento è stato aggiornato il 9 Dicembre 2025 per riflettere lo stato reale dell'implementazione.

---

## 2. Sistema Ruoli Azienda (✅ IMPLEMENTATO)

### 2.1 Panoramica

Il Sistema Ruoli Azienda gestisce le **associazioni tra persone fisiche e persone giuridiche** con ruoli lavorativi specifici. Permette di tracciare:
- Chi lavora dove e con quale ruolo
- Periodi di impiego (data inizio/fine)
- Organigrammi aziendali
- Storico lavorativo delle persone

**Esempio Dati:**
- Giuseppe Verdi (PF) è **Segretaria** presso Azienda Test SRL (PG) dal 2023-01-01
- Mario Rossi (PF) è **Amministratore Delegato** presso Studio Legale Bianchi (PG) dal 2020-05-15 al 2024-12-31
- Laura Neri (PF) è **Consulente** presso TechCorp SpA (PG)

### 2.2 Schema Database

```sql
-- Tabella domini: tipi ruolo azienda standardizzati
CREATE TABLE ruoli_azienda_tipi (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(100) UNIQUE NOT NULL,
    descrizione VARCHAR(500),
    attivo BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL
);

-- Tabella associazioni: link persona fisica ↔ persona giuridica
CREATE TABLE ruoli_azienda (
    id SERIAL PRIMARY KEY,
    persona_fisica_id INT NOT NULL REFERENCES soggetti_anagrafici(id) ON DELETE CASCADE,
    persona_giuridica_id INT NOT NULL REFERENCES soggetti_anagrafici(id) ON DELETE CASCADE,

    -- Ruolo (doppio sistema per backward compatibility)
    ruolo VARCHAR(100),              -- Campo testuale legacy
    ruolo_tipo_id INT REFERENCES ruoli_azienda_tipi(id) ON DELETE SET NULL,  -- FK al dominio

    -- Periodo di validità
    data_inizio DATE,
    data_fine DATE,

    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL
);
```

**Dati Domini (Seed):**
```sql
INSERT INTO ruoli_azienda_tipi (nome, descrizione) VALUES
  ('Segretaria', 'Ruolo di segretaria/o aziendale'),
  ('Amministratore Delegato', 'CEO - Amministratore Delegato'),
  ('Direttore Generale', 'Direttore Generale dell\'azienda'),
  ('Responsabile Amministrativo', 'Responsabile area amministrativa e contabile'),
  ('Responsabile Commerciale', 'Responsabile area commerciale e vendite'),
  ('Responsabile Tecnico', 'Responsabile area tecnica'),
  ('Contabile', 'Addetto alla contabilità'),
  ('Consulente', 'Consulente esterno');
```

### 2.3 Modelli Backend

```python
# backend/modules/anagrafica_italiana/models/ruolo_azienda_tipo.py

class RuoloAziendaTipo(Base):
    """Domini: tipi di ruolo azienda standard."""
    __tablename__ = "ruoli_azienda_tipi"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(100), unique=True, nullable=False, index=True)
    descrizione = Column(String(500), nullable=True)
    attivo = Column(Boolean, default=True, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
```

```python
# backend/modules/anagrafica_italiana/models/ruolo_azienda.py

class RuoloAzienda(Base):
    """Associazione persona fisica ↔ persona giuridica con ruolo."""
    __tablename__ = "ruoli_azienda"

    id = Column(Integer, primary_key=True, index=True)

    # FK ai soggetti
    persona_fisica_id = Column(Integer, ForeignKey("soggetti_anagrafici.id", ondelete="CASCADE"))
    persona_giuridica_id = Column(Integer, ForeignKey("soggetti_anagrafici.id", ondelete="CASCADE"))

    # Ruolo (doppio sistema)
    ruolo = Column(String(100), nullable=True)  # Campo testuale legacy
    ruolo_tipo_id = Column(Integer, ForeignKey("ruoli_azienda_tipi.id", ondelete="SET NULL"))

    # Periodo
    data_inizio = Column(Date, nullable=True)
    data_fine = Column(Date, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    persona_fisica = relationship("SoggettoAnagrafico", foreign_keys=[persona_fisica_id])
    persona_giuridica = relationship("SoggettoAnagrafico", foreign_keys=[persona_giuridica_id])
    ruolo_tipo = relationship("RuoloAziendaTipo")
```

### 2.4 API Endpoints (CRUD Completo)

**Backend:** `/api/v1/anagrafica/ruoli-azienda`

```python
# GET / - Lista tutte le associazioni ruolo
@router.get("/", response_model=List[RuoloAziendaResponse])
def get_all_ruoli_azienda(skip: int = 0, limit: int = 100, ...)

# GET /soggetto/{soggetto_id} - Ruoli di un soggetto
# Restituisce: {come_persona: [], come_azienda: []}
@router.get("/soggetto/{soggetto_id}")
def get_ruoli_by_soggetto(soggetto_id: int, attivi_only: bool = False, ...)

# GET /{ruolo_id} - Dettaglio singolo ruolo
@router.get("/{ruolo_id}", response_model=RuoloAziendaResponse)
def get_ruolo_azienda(ruolo_id: int, ...)

# POST / - Crea associazione ruolo
@router.post("/", response_model=RuoloAziendaResponse, status_code=201)
def create_ruolo_azienda(ruolo_data: RuoloAziendaCreate, ...)

# PUT /{ruolo_id} - Aggiorna associazione
@router.put("/{ruolo_id}", response_model=RuoloAziendaResponse)
def update_ruolo_azienda(ruolo_id: int, ruolo_update: RuoloAziendaUpdate, ...)

# DELETE /{ruolo_id} - Elimina associazione
@router.delete("/{ruolo_id}", status_code=204)
def delete_ruolo_azienda(ruolo_id: int, ...)
```

**Backend:** `/api/v1/anagrafica/domini/ruoli-azienda-tipi`

```python
# CRUD completo per gestione domini tipi ruolo
GET    /       - Lista tipi ruolo
POST   /       - Crea tipo ruolo
PUT    /{id}   - Aggiorna tipo ruolo
DELETE /{id}   - Elimina tipo ruolo
```

### 2.5 Frontend Components (Completo)

#### RuoliAziendaSection.jsx
Componente integrato nelle schede dettaglio di Persona Fisica e Persona Giuridica.

**Caratteristiche:**
- Vista adattiva: mostra "Aziende dove lavora" per PF, "Persone associate" per PG
- Tabella con: controparte, ruolo, periodo, stato (attivo/scaduto)
- Display dinamico: mostra `ruolo_tipo_nome` dal dominio, fallback a `ruolo` testuale
- Badge "⚠ Custom" per ruoli non linkati ai domini
- Filtro "Solo attivi" per nascondere ruoli cessati
- Link a scheda dettaglio controparte
- Azioni: modifica, elimina

#### RuoliAziendaList.jsx
Lista centralizzata di tutte le associazioni ruolo della piattaforma.

**Caratteristiche:**
- Filtri combinabili: per persona, per azienda, per nome ruolo, solo attivi
- Statistiche: totale ruoli, attivi, cessati
- Tabella completa: persona, azienda, ruolo, date, stato
- Form edit inline tramite modal
- Reload manuale

#### RuoloAziendaForm.jsx
Form modale per creazione/modifica associazioni ruolo.

**Caratteristiche:**
- Pre-compilazione soggetto corrente (persona o azienda)
- SELECT dropdown con ruoli standard da dominio
- Opzione "➕ Altro (nuovo ruolo)..." per casi eccezionali
- Quando si seleziona "Altro": campo testo con warning su uso custom
- Toggle tra modalità SELECT e testo custom
- Validazione date (data_fine >= data_inizio)
- Salvataggio: popola sia `ruolo_tipo_id` (FK) che `ruolo` (denormalizzato)

#### RuoliAziendaTipiList.jsx
CRUD completo per gestione domini ruoli azienda.

**Caratteristiche:**
- Tabella ruoli: nome, descrizione, stato (attivo/disattivo)
- Creazione nuovo ruolo (nome, descrizione obbligatori)
- Modifica ruolo esistente
- Attivazione/disattivazione (soft delete)
- Eliminazione fisica (con conferma)

### 2.6 Funzionalità Chiave Implementate

✅ **Domini Normalizzati**: I ruoli sono gestiti come dati di dominio, garantendo coerenza across utenti

✅ **Live Updates**: Le modifiche ai nomi dei ruoli nei domini si propagano immediatamente in tutte le viste (display di `ruolo_tipo_nome` invece di `ruolo` statico)

✅ **Backward Compatibility**: Campo `ruolo` testuale mantenuto per vecchi dati non collegati ai domini

✅ **Storicizzazione**: Tracciamento completo dei periodi di impiego con `data_inizio` e `data_fine`

✅ **Vista Bidirezionale**:
- Dalla persona fisica: vedi tutte le aziende dove lavora/ha lavorato
- Dalla persona giuridica: vedi tutte le persone associate

✅ **Filtri Intelligenti**:
- Solo attivi (ruoli con `data_fine` null o futura)
- Ricerca testuale per nome ruolo
- Filtri combinati per persona e azienda

✅ **Validazione Robusta**:
- Verifica che persona_fisica_id sia effettivamente una persona fisica
- Verifica che persona_giuridica_id sia effettivamente una persona giuridica
- Validazione date (data_fine non può essere prima di data_inizio)

✅ **Badge di Stato**:
- "✓ Attivo" per ruoli correnti
- "✗ Scaduto" per ruoli cessati
- "⚠ Custom" per ruoli non linkati ai domini

---

## 3. Sistema Ruoli di Business (⚠️ PARZIALE)

### 3.1 Concetto Fondamentale

Il sistema distingue tra:

1. **Ruoli di Piattaforma** (Platform Roles): Admin, Manager, User
   - Gestiti da `app/core/auth/models.py`
   - Determinano i **permessi di sistema** (CRUD, visualizzazione moduli)
   - Assegnati a livello di `User`

2. **Ruoli di Business** (Business Roles): Proprietario, Affittuario, Tecnico, Fornitore
   - Gestiti da `app/core/models/ruoli.py` (RuoloDisponibile, SoggettoRuolo)
   - Determinano il **cono di visibilità** (quali dati vede l'utente)
   - Assegnati a livello di `SoggettoAnagrafico`

### 3.2 Schema Database

#### Tabella: `ruoli_disponibili`

```python
class RuoloDisponibile(Base):
    """
    Registry of available business roles across modules.
    Modules declare roles they provide/use via manifest.
    """
    __tablename__ = "ruoli_disponibili"

    id = Column(Integer, primary_key=True, index=True)
    codice = Column(String(50), unique=True, nullable=False, index=True)
    nome_display = Column(String(100), nullable=False)
    descrizione = Column(Text, nullable=True)
    modulo_id = Column(String(50), nullable=False, index=True)  # es. "immobili", "affitti_lungo"
    attivo = Column(Boolean, default=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
```

**Esempio Dati:**
```
codice             | nome_display    | descrizione                       | modulo_id
-------------------|-----------------|-----------------------------------|-------------
proprietario       | Proprietario    | Proprietario di immobili          | immobili
affittuario        | Affittuario     | Affittuario/Inquilino             | affitti_lungo
tecnico            | Tecnico         | Tecnico/Manutentore               | affitti_lungo
fornitore          | Fornitore       | Fornitore di beni/servizi         | contabilita
amministratore_cond| Amministratore  | Amministratore di condominio      | condominio
```

#### Tabella: `soggetti_ruoli`

```python
class SoggettoRuolo(Base):
    """
    Assignment of business roles to anagrafica subjects.
    Links a subject to a role with optional specialization.
    """
    __tablename__ = "soggetti_ruoli"

    id = Column(Integer, primary_key=True, index=True)
    soggetto_id = Column(Integer, ForeignKey("soggetti_anagrafici.id"), nullable=False, index=True)
    ruolo_id = Column(Integer, ForeignKey("ruoli_disponibili.id"), nullable=False, index=True)

    # Optional: link to specific record (es. proprietario di UnitaImmobiliare id=123)
    record_specializzazione_id = Column(Integer, nullable=True, index=True)
    modulo_specializzazione = Column(String(50), nullable=True)  # es. "immobili"
    entity_type_specializzazione = Column(String(50), nullable=True)  # es. "unita_immobiliare"

    attivo = Column(Boolean, default=True)
    note = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    soggetto = relationship("SoggettoAnagrafico", back_populates="ruoli_assegnati")
    ruolo = relationship("RuoloDisponibile")
```

**Esempio Dati:**
```
soggetto_id | ruolo_id | record_specializzazione_id | modulo_specializzazione | entity_type
------------|----------|---------------------------|-------------------------|------------------
15          | 1 (prop) | 42                        | immobili                | unita_immobiliare
15          | 1 (prop) | 43                        | immobili                | unita_immobiliare
22          | 2 (aff)  | 18                        | affitti_lungo           | contratto
```

**Nota:** Il soggetto 15 è proprietario di 2 immobili (id 42 e 43), il soggetto 22 è affittuario nel contratto 18.

### 2.3 Dichiarazione Ruoli nel Manifest

Ogni modulo dichiara i ruoli che utilizza nel proprio `__manifest__.py`:

```python
# backend/modules/immobili/__manifest__.py
manifest = {
    "name": "Gestione Immobili",
    "technical_name": "immobili",

    # Ruoli che questo modulo dichiara/utilizza
    "ruoli_disponibili": [
        {
            "codice": "proprietario",
            "nome_display": "Proprietario",
            "descrizione": "Proprietario di immobili",
            "modulo_origine": "immobili",  # Modulo che dichiara il ruolo
        },
    ],
}
```

```python
# backend/modules/affitti_lungo/__manifest__.py
manifest = {
    "name": "Gestione Affitti",
    "technical_name": "affitti_lungo",

    "ruoli_disponibili": [
        {
            "codice": "affittuario",
            "nome_display": "Affittuario",
            "descrizione": "Affittuario/Inquilino",
            "modulo_origine": "affitti_lungo",
        },
        {
            "codice": "tecnico",
            "nome_display": "Tecnico",
            "descrizione": "Tecnico/Manutentore",
            "modulo_origine": "affitti_lungo",
        },
        # Riutilizzo del ruolo dichiarato da immobili
        {
            "codice": "proprietario",
            "nome_display": "Proprietario",
            "descrizione": "Proprietario di immobili",
            "modulo_origine": "immobili",  # Riferimento al modulo dichiarante
        },
    ],
}
```

### 2.4 Registrazione Automatica Ruoli

Il module loader registra automaticamente i ruoli all'avvio:

```python
# backend/app/core/module_system/loader.py (da implementare)

def register_module_roles(db: Session, module_manifest: dict):
    """
    Register business roles declared in module manifest.
    Creates or updates RuoloDisponibile entries.
    """
    ruoli = module_manifest.get("ruoli_disponibili", [])

    for ruolo_def in ruoli:
        codice = ruolo_def["codice"]
        modulo_origine = ruolo_def["modulo_origine"]

        # Check if role already exists
        existing = db.query(RuoloDisponibile).filter(
            RuoloDisponibile.codice == codice
        ).first()

        if existing:
            # Verify it belongs to declared module
            if existing.modulo_id != modulo_origine:
                logger.warning(
                    f"Module {module_manifest['technical_name']} tries to use role "
                    f"'{codice}' from module '{modulo_origine}', but it's registered "
                    f"by '{existing.modulo_id}'"
                )
            continue

        # Create new role
        nuovo_ruolo = RuoloDisponibile(
            codice=codice,
            nome_display=ruolo_def["nome_display"],
            descrizione=ruolo_def.get("descrizione"),
            modulo_id=modulo_origine,
            attivo=True
        )
        db.add(nuovo_ruolo)

    db.commit()
```

### 2.5 API per Gestione Ruoli

#### Endpoint: Assegna Ruolo a Soggetto

```python
# backend/modules/anagrafica_italiana/routes/ruoli.py (da creare)

@router.post("/soggetti/{soggetto_id}/ruoli")
def assign_ruolo_to_soggetto(
    soggetto_id: int,
    assegnazione: RuoloAssignmentCreate,  # {ruolo_id, record_specializzazione_id?, note?}
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("soggetto.edit"))
):
    """
    Assign a business role to an anagrafica subject.
    Optionally link to a specific record (e.g., proprietario of unit 42).
    """
    # Verify soggetto exists
    soggetto = db.query(SoggettoAnagrafico).filter(
        SoggettoAnagrafico.id == soggetto_id
    ).first()
    if not soggetto:
        raise HTTPException(status_code=404, detail="Soggetto non trovato")

    # Verify ruolo exists
    ruolo = db.query(RuoloDisponibile).filter(
        RuoloDisponibile.id == assegnazione.ruolo_id
    ).first()
    if not ruolo or not ruolo.attivo:
        raise HTTPException(status_code=404, detail="Ruolo non trovato o non attivo")

    # Check if assignment already exists
    existing = db.query(SoggettoRuolo).filter(
        SoggettoRuolo.soggetto_id == soggetto_id,
        SoggettoRuolo.ruolo_id == assegnazione.ruolo_id,
        SoggettoRuolo.record_specializzazione_id == assegnazione.record_specializzazione_id,
        SoggettoRuolo.attivo == True
    ).first()

    if existing:
        raise HTTPException(status_code=400, detail="Ruolo già assegnato")

    # Create assignment
    nuova_assegnazione = SoggettoRuolo(
        soggetto_id=soggetto_id,
        ruolo_id=assegnazione.ruolo_id,
        record_specializzazione_id=assegnazione.record_specializzazione_id,
        modulo_specializzazione=assegnazione.modulo_specializzazione,
        entity_type_specializzazione=assegnazione.entity_type_specializzazione,
        note=assegnazione.note,
        attivo=True
    )

    db.add(nuova_assegnazione)
    db.commit()
    db.refresh(nuova_assegnazione)

    return nuova_assegnazione
```

#### Endpoint: Rimuovi Ruolo

```python
@router.delete("/soggetti/{soggetto_id}/ruoli/{assegnazione_id}")
def remove_ruolo_from_soggetto(
    soggetto_id: int,
    assegnazione_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("soggetto.edit"))
):
    """
    Remove a business role assignment (soft delete: set attivo=False).
    """
    assegnazione = db.query(SoggettoRuolo).filter(
        SoggettoRuolo.id == assegnazione_id,
        SoggettoRuolo.soggetto_id == soggetto_id
    ).first()

    if not assegnazione:
        raise HTTPException(status_code=404, detail="Assegnazione non trovata")

    assegnazione.attivo = False
    db.commit()

    return {"message": "Ruolo rimosso con successo"}
```

#### Endpoint: Lista Ruoli Disponibili

```python
@router.get("/ruoli-disponibili")
def list_ruoli_disponibili(
    modulo_id: Optional[str] = None,
    attivi_solo: bool = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List all available business roles, optionally filtered by module.
    """
    query = db.query(RuoloDisponibile)

    if attivi_solo:
        query = query.filter(RuoloDisponibile.attivo == True)

    if modulo_id:
        query = query.filter(RuoloDisponibile.modulo_id == modulo_id)

    ruoli = query.order_by(RuoloDisponibile.nome_display).all()
    return ruoli
```

---

## 3. Integrazione Utenti-Anagrafica

### 3.1 Relazione User ↔ SoggettoAnagrafico

Un soggetto anagrafico può avere accesso al sistema se collegato a un `User`:

```python
# backend/modules/anagrafica_italiana/models/soggetto_anagrafico.py

class SoggettoAnagrafico(Base):
    __tablename__ = "soggetti_anagrafici"

    id = Column(Integer, primary_key=True, index=True)

    # ... altri campi (nome, cognome, cf, piva, email, telefono, etc.) ...

    # LINK OPZIONALE A USER DI SISTEMA
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, unique=True, index=True)
    user = relationship("User", foreign_keys=[user_id], backref="soggetto_anagrafico")
```

**Regole:**
- `user_id` è **nullable**: non tutti i soggetti hanno accesso al sistema
- `user_id` è **unique**: un User può essere collegato a un solo SoggettoAnagrafico
- Un SoggettoAnagrafico può avere `user_id = NULL` se è solo un'anagrafica (es. fornitore senza accesso web)

### 3.2 Creazione User da Anagrafica

Quando si vuole dare accesso a un soggetto:

```python
# backend/modules/anagrafica_italiana/routes/soggetti.py

@router.post("/soggetti/{soggetto_id}/create-user")
def create_user_for_soggetto(
    soggetto_id: int,
    user_data: UserCreateFromAnagrafica,  # {password, platform_role?}
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("user.create"))
):
    """
    Create a platform User linked to an anagrafica subject.
    Uses subject's email as username.
    """
    # Verify soggetto exists
    soggetto = db.query(SoggettoAnagrafico).filter(
        SoggettoAnagrafico.id == soggetto_id
    ).first()
    if not soggetto:
        raise HTTPException(status_code=404, detail="Soggetto non trovato")

    # Check if already has user
    if soggetto.user_id:
        raise HTTPException(status_code=400, detail="Soggetto già collegato a un utente")

    # Check if email is valid
    if not soggetto.email:
        raise HTTPException(status_code=400, detail="Soggetto non ha email valida")

    # Check if email already used by another user
    existing_user = db.query(User).filter(User.username == soggetto.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email già utilizzata da altro utente")

    # Create User
    from app.core.auth.models import User
    from app.core.auth.utils import hash_password

    nuovo_user = User(
        username=soggetto.email,
        hashed_password=hash_password(user_data.password),
        email=soggetto.email,
        full_name=soggetto.nome_completo,  # property che ritorna "Nome Cognome" o ragione_sociale
        is_active=True
    )

    db.add(nuovo_user)
    db.flush()  # Get user.id

    # Link user to soggetto
    soggetto.user_id = nuovo_user.id

    # Assign default platform role if specified
    if user_data.platform_role:
        from app.core.auth.models import Role
        role = db.query(Role).filter(Role.name == user_data.platform_role).first()
        if role:
            nuovo_user.roles.append(role)

    db.commit()
    db.refresh(soggetto)

    return {
        "message": "Utente creato con successo",
        "user_id": nuovo_user.id,
        "username": nuovo_user.username,
        "soggetto_id": soggetto.id
    }
```

### 3.3 Login e Identificazione

Quando un utente fa login:

```python
# backend/app/core/auth/routes.py

@router.post("/login")
def login(credentials: LoginRequest, db: Session = Depends(get_db)):
    """
    Authenticate user and return JWT token.
    Token payload includes user_id and soggetto_id (if linked).
    """
    user = authenticate_user(db, credentials.username, credentials.password)
    if not user:
        raise HTTPException(status_code=401, detail="Credenziali non valide")

    # Check if user is linked to anagrafica
    soggetto_id = None
    if hasattr(user, 'soggetto_anagrafico') and user.soggetto_anagrafico:
        soggetto_id = user.soggetto_anagrafico.id

    # Create token with extended info
    token_data = {
        "sub": str(user.id),
        "soggetto_id": soggetto_id,  # Useful for business role queries
        "platform_roles": [role.name for role in user.roles]
    }

    if credentials.remember_me:
        access_token = create_access_token(
            data=token_data,
            expires_delta=timedelta(days=30)
        )
    else:
        access_token = create_access_token(data=token_data)

    refresh_token = create_refresh_token(data=token_data)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user_id": user.id,
        "soggetto_id": soggetto_id
    }
```

---

## 4. Cono di Visibilità (Visibility Scope)

### 4.1 Concetto

Il **cono di visibilità** determina quali dati un utente può vedere in base ai suoi **ruoli di business**:

- **Admin/Manager**: vede tutto (platform role)
- **Proprietario**: vede solo i propri immobili e contratti relativi
- **Affittuario**: vede solo i contratti in cui è affittuario
- **Tecnico**: vede solo gli interventi a cui è assegnato

### 4.2 Implementazione Backend

Creare un servizio di filtraggio query:

```python
# backend/app/core/services/visibility_service.py

from sqlalchemy.orm import Query, Session
from app.core.auth.models import User
from app.core.models import RuoloDisponibile, SoggettoRuolo

class VisibilityService:
    """
    Service to apply visibility filters based on user's business roles.
    """

    @staticmethod
    def apply_visibility_filter(
        query: Query,
        user: User,
        model_class,
        db: Session
    ) -> Query:
        """
        Apply visibility filter to a query based on user's business roles.

        Args:
            query: SQLAlchemy query to filter
            user: Current authenticated user
            model_class: Model class being queried (e.g., UnitaImmobiliare)
            db: Database session

        Returns:
            Filtered query
        """
        # Admin/Manager see everything
        if user.is_admin() or user.has_platform_role("Manager"):
            return query

        # Get user's soggetto_id
        if not hasattr(user, 'soggetto_anagrafico') or not user.soggetto_anagrafico:
            # User not linked to anagrafica: no data visible
            return query.filter(False)  # Return empty

        soggetto_id = user.soggetto_anagrafico.id

        # Get user's business roles
        ruoli_assegnati = db.query(SoggettoRuolo).filter(
            SoggettoRuolo.soggetto_id == soggetto_id,
            SoggettoRuolo.attivo == True
        ).all()

        if not ruoli_assegnati:
            # No business roles: no data visible
            return query.filter(False)

        # Apply filters based on model and roles
        from immobili.models import UnitaImmobiliare
        from affitti_lungo.models import Contratto

        if model_class == UnitaImmobiliare:
            return VisibilityService._filter_unita_immobiliare(
                query, soggetto_id, ruoli_assegnati, db
            )
        elif model_class == Contratto:
            return VisibilityService._filter_contratto(
                query, soggetto_id, ruoli_assegnati, db
            )

        # Default: no filter (or raise error for unhandled models)
        return query

    @staticmethod
    def _filter_unita_immobiliare(
        query: Query,
        soggetto_id: int,
        ruoli_assegnati: list,
        db: Session
    ) -> Query:
        """
        Filter UnitaImmobiliare based on user's roles.
        User sees units where they are proprietario.
        """
        from immobili.models import DirittoImmobile, UnitaImmobiliare

        # Check if user has proprietario role
        has_proprietario = any(
            assegnazione.ruolo.codice == "proprietario"
            for assegnazione in ruoli_assegnati
        )

        if not has_proprietario:
            return query.filter(False)  # No units visible

        # Get unit IDs where user is proprietario
        diritti = db.query(DirittoImmobile).join(
            DirittoImmobile.proprietario
        ).filter(
            DirittoImmobile.proprietario.has(soggetto_id=soggetto_id),
            DirittoImmobile.attivo == True
        ).all()

        unit_ids = [diritto.unita_immobiliare_id for diritto in diritti]

        if not unit_ids:
            return query.filter(False)

        # Filter query to only these units
        return query.filter(UnitaImmobiliare.id.in_(unit_ids))

    @staticmethod
    def _filter_contratto(
        query: Query,
        soggetto_id: int,
        ruoli_assegnati: list,
        db: Session
    ) -> Query:
        """
        Filter Contratto based on user's roles.
        - Proprietario: sees contracts on their units
        - Affittuario: sees contracts where they are tenant
        """
        from affitti_lungo.models import Contratto
        from immobili.models import DirittoImmobile

        filters = []

        # Check for affittuario role
        has_affittuario = any(
            assegnazione.ruolo.codice == "affittuario"
            for assegnazione in ruoli_assegnati
        )

        if has_affittuario:
            # See contracts where user is affittuario
            filters.append(
                Contratto.affittuario.has(soggetto_id=soggetto_id)
            )

        # Check for proprietario role
        has_proprietario = any(
            assegnazione.ruolo.codice == "proprietario"
            for assegnazione in ruoli_assegnati
        )

        if has_proprietario:
            # Get unit IDs owned
            diritti = db.query(DirittoImmobile).join(
                DirittoImmobile.proprietario
            ).filter(
                DirittoImmobile.proprietario.has(soggetto_id=soggetto_id),
                DirittoImmobile.attivo == True
            ).all()

            unit_ids = [diritto.unita_immobiliare_id for diritto in diritti]

            if unit_ids:
                # See contracts on owned units
                filters.append(Contratto.unita_immobiliare_id.in_(unit_ids))

        if not filters:
            return query.filter(False)

        # Apply OR logic: see contracts if affittuario OR proprietario
        from sqlalchemy import or_
        return query.filter(or_(*filters))
```

### 4.3 Utilizzo nelle Route

```python
# backend/modules/immobili/routes/unita_immobiliare.py

from app.core.services.visibility_service import VisibilityService

@router.get("/", response_model=List[UnitaImmobiliareResponse])
def list_unita_immobiliare(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List unita immobiliare with visibility filtering.
    """
    query = db.query(UnitaImmobiliare)

    # Apply visibility filter based on user's business roles
    query = VisibilityService.apply_visibility_filter(
        query=query,
        user=current_user,
        model_class=UnitaImmobiliare,
        db=db
    )

    unita = query.offset(skip).limit(limit).all()
    return unita
```

### 4.4 Frontend: Filtraggio Automatico

Nel frontend, le chiamate API devono passare il token JWT che contiene `soggetto_id`:

```javascript
// frontend/src/modules/immobili/services/immobiliAPI.js

export const getUnitaImmobiliare = async (params = {}) => {
  // Token automatically included via getAuthHeader()
  const response = await axios.get(`${API_BASE_URL}/immobili/unita-immobiliare`, {
    headers: getAuthHeader(),
    params
  });

  // Response already filtered by backend based on user's visibility
  return response.data;
};
```

Il backend estrae `soggetto_id` dal token e applica il filtro automaticamente.

---

## 5. Sistema di Gestione Documenti

### 5.1 Servizi di Piattaforma Utilizzati

**✅ IMPLEMENTATO** - Il modulo anagrafica utilizza i seguenti servizi di piattaforma:

1. **DocumentService** (`app/core/platform_services/document_service.py`)
   - Upload sicuro con validazione tipo e dimensione file
   - Download con controlli di accesso
   - Delete con cleanup automatico
   - Gestione metadata

2. **ScadenzarioService** (`app/core/platform_services/scadenzario_service.py`)
   - Monitoraggio scadenze documenti
   - Query per documenti scaduti, in scadenza, futuri
   - Statistiche e dashboard widget data
   - Raggruppamento per entity_type

3. **ImportExportService** (già esistente)
   - Export CSV/Excel
   - Import con validazione

4. **AddressNormalizerService** (già esistente)
   - Normalizzazione indirizzi italiani
   - Autocomplete comuni

### 5.2 Modello Documento Esteso

Il modello `Documento` è stato esteso con supporto scadenze:

```python
# backend/modules/affitti_lungo/models/documenti.py (ESTESO)

class EntityType(str, enum.Enum):
    # ... existing types ...
    SOGGETTO_ANAGRAFICO = "SOGGETTO_ANAGRAFICO"  # ✅ AGGIUNTO

class Documento(Base):
    __tablename__ = "documenti"

    id = Column(Integer, primary_key=True, index=True)

    # Polymorphic association
    entity_type = Column(SQLEnum(EntityType), nullable=False, index=True)
    entity_id = Column(Integer, nullable=False, index=True)

    # Metadata documento
    tipo_documento = Column(SQLEnum(TipoDocumento), nullable=False)
    nome_file = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    mime_type = Column(String(100), nullable=True)
    dimensione = Column(BigInteger, nullable=True)

    # Info aggiuntive
    descrizione = Column(String(500), nullable=True)
    note = Column(String(500), nullable=True)

    # ✅ CAMPI AGGIUNTI PER SCADENZARIO
    data_scadenza = Column(Date, nullable=True, index=True)  # Per CI, patente, certificati
    tipo_documento_id = Column(Integer, ForeignKey("tipi_documento.id"), nullable=True)  # Link a TipoDocumento flessibile

    # Metadata sistema
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
```

### 5.3 API Upload Documento per Soggetto

**✅ IMPLEMENTATO** - `backend/modules/anagrafica_italiana/routes/documenti.py`

```python
# ✅ IMPLEMENTATO - Usa DocumentService di piattaforma

from fastapi import UploadFile, File
from app.core.services.file_storage import save_uploaded_file

@router.post("/soggetti/{soggetto_id}/documenti/upload")
async def upload_documento_soggetto(
    soggetto_id: int,
    file: UploadFile = File(...),
    tipo_documento_id: int = Form(...),
    data_scadenza: Optional[str] = Form(None),  # Format: YYYY-MM-DD
    note: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("soggetto.edit"))
):
    """
    Upload a document for an anagrafica subject (CF, CI, patente, etc).
    """
    # Verify soggetto exists
    soggetto = db.query(SoggettoAnagrafico).filter(
        SoggettoAnagrafico.id == soggetto_id
    ).first()
    if not soggetto:
        raise HTTPException(status_code=404, detail="Soggetto non trovato")

    # Verify tipo documento
    tipo_doc = db.query(TipoDocumento).filter(
        TipoDocumento.id == tipo_documento_id
    ).first()
    if not tipo_doc:
        raise HTTPException(status_code=404, detail="Tipo documento non trovato")

    # Validate expiration date if tipo requires it
    parsed_scadenza = None
    if data_scadenza:
        from datetime import datetime
        try:
            parsed_scadenza = datetime.strptime(data_scadenza, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(status_code=400, detail="Formato data non valido")
    elif tipo_doc.richiede_scadenza:
        raise HTTPException(status_code=400, detail=f"Tipo documento '{tipo_doc.nome}' richiede data di scadenza")

    # Save file to storage
    file_info = await save_uploaded_file(
        file=file,
        entity_type="soggetto_anagrafico",
        entity_id=soggetto_id,
        subfolder="documenti"
    )

    # Create Documento record
    from app.core.models import Documento

    nuovo_documento = Documento(
        entity_type="soggetto_anagrafico",
        entity_id=soggetto_id,
        tipo_documento_id=tipo_documento_id,
        nome_file=file.filename,
        file_path=file_info["file_path"],
        mime_type=file.content_type,
        dimensione_bytes=file_info["size"],
        data_scadenza=parsed_scadenza,
        note=note,
        uploaded_by_user_id=current_user.id
    )

    db.add(nuovo_documento)
    db.commit()
    db.refresh(nuovo_documento)

    return nuovo_documento
```

### 5.4 API Lista Documenti Soggetto

**✅ IMPLEMENTATO** - Con integrazione ScadenzarioService

```python
@router.get("/documenti/soggetto/{soggetto_id}")
def list_documenti_soggetto(
    soggetto_id: int,
    categoria: Optional[str] = None,  # identita, fiscale, etc.
    scaduti: bool = False,  # Show only expired docs
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("soggetto.view"))
):
    """
    List all documents for an anagrafica subject.
    """
    from app.core.models import Documento
    from datetime import date

    query = db.query(Documento).filter(
        Documento.entity_type == "soggetto_anagrafico",
        Documento.entity_id == soggetto_id
    )

    # Filter by categoria
    if categoria:
        query = query.join(TipoDocumento).filter(
            TipoDocumento.categoria == categoria
        )

    # Filter scaduti
    if scaduti:
        query = query.filter(
            Documento.data_scadenza != None,
            Documento.data_scadenza < date.today()
        )

    documenti = query.order_by(Documento.created_at.desc()).all()

    # Enrich with tipo documento info
    result = []
    for doc in documenti:
        result.append({
            "id": doc.id,
            "nome_file": doc.nome_file,
            "tipo_documento": {
                "id": doc.tipo_documento.id,
                "codice": doc.tipo_documento.codice,
                "nome": doc.tipo_documento.nome,
                "categoria": doc.tipo_documento.categoria
            } if doc.tipo_documento else None,
            "data_scadenza": doc.data_scadenza.isoformat() if doc.data_scadenza else None,
            "is_scaduto": doc.data_scadenza < date.today() if doc.data_scadenza else False,
            "dimensione_bytes": doc.dimensione_bytes,
            "note": doc.note,
            "created_at": doc.created_at.isoformat()
        })

    return result
```

### 5.5 Frontend: Upload Component

**✅ IMPLEMENTATO** - `frontend/src/modules/anagrafica_italiana/components/Documenti/DocumentoUpload.jsx`

```jsx
// ✅ IMPLEMENTATO - Con validazione e progress bar

import React, { useState, useEffect } from 'react';
import { getTipiDocumento } from '../../services/anagraficaAPI';
import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

const getAuthHeader = () => {
  const token = localStorage.getItem('access_token');
  return token ? { Authorization: `Bearer ${token}` } : {};
};

export const DocumentoUpload = ({ soggettoId, onUploadSuccess }) => {
  const [tipiDocumento, setTipiDocumento] = useState([]);
  const [selectedFile, setSelectedFile] = useState(null);
  const [tipoDocumentoId, setTipoDocumentoId] = useState('');
  const [dataScadenza, setDataScadenza] = useState('');
  const [note, setNote] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadTipiDocumento();
  }, []);

  const loadTipiDocumento = async () => {
    try {
      const data = await getTipiDocumento();
      setTipiDocumento(data);
    } catch (err) {
      console.error('Errore caricamento tipi documento:', err);
    }
  };

  const handleFileChange = (e) => {
    setSelectedFile(e.target.files[0]);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!selectedFile || !tipoDocumentoId) {
      setError('Seleziona un file e un tipo documento');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const formData = new FormData();
      formData.append('file', selectedFile);
      formData.append('tipo_documento_id', tipoDocumentoId);
      if (dataScadenza) formData.append('data_scadenza', dataScadenza);
      if (note) formData.append('note', note);

      const response = await axios.post(
        `${API_BASE_URL}/anagrafica/soggetti/${soggettoId}/documenti/upload`,
        formData,
        {
          headers: {
            ...getAuthHeader(),
            'Content-Type': 'multipart/form-data'
          }
        }
      );

      // Reset form
      setSelectedFile(null);
      setTipoDocumentoId('');
      setDataScadenza('');
      setNote('');
      e.target.reset();

      // Notify parent
      if (onUploadSuccess) {
        onUploadSuccess(response.data);
      }

    } catch (err) {
      console.error('Errore upload documento:', err);
      setError(err.response?.data?.detail || 'Errore durante il caricamento');
    } finally {
      setLoading(false);
    }
  };

  const selectedTipo = tipiDocumento.find(t => t.id === parseInt(tipoDocumentoId));

  return (
    <div className="documento-upload">
      <h3>Carica Documento</h3>

      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label>Tipo Documento *</label>
          <select
            value={tipoDocumentoId}
            onChange={(e) => setTipoDocumentoId(e.target.value)}
            required
          >
            <option value="">-- Seleziona --</option>
            {tipiDocumento.map(tipo => (
              <option key={tipo.id} value={tipo.id}>
                {tipo.nome} {tipo.categoria ? `(${tipo.categoria})` : ''}
              </option>
            ))}
          </select>
        </div>

        <div className="form-group">
          <label>File *</label>
          <input
            type="file"
            onChange={handleFileChange}
            accept=".pdf,.jpg,.jpeg,.png"
            required
          />
          {selectedFile && (
            <small className="file-info">
              {selectedFile.name} ({(selectedFile.size / 1024).toFixed(1)} KB)
            </small>
          )}
        </div>

        {selectedTipo?.richiede_scadenza && (
          <div className="form-group">
            <label>Data Scadenza *</label>
            <input
              type="date"
              value={dataScadenza}
              onChange={(e) => setDataScadenza(e.target.value)}
              required={selectedTipo?.richiede_scadenza}
            />
          </div>
        )}

        <div className="form-group">
          <label>Note</label>
          <textarea
            value={note}
            onChange={(e) => setNote(e.target.value)}
            rows={3}
          />
        </div>

        {error && <div className="error-message">{error}</div>}

        <button type="submit" disabled={loading}>
          {loading ? 'Caricamento...' : 'Carica Documento'}
        </button>
      </form>
    </div>
  );
};
```

---

## 6. Import/Export Funzionalità

### 6.1 Servizio Platform per Import/Export

Creare un servizio di piattaforma riusabile:

```python
# backend/app/core/services/import_export_service.py

import csv
import io
from typing import List, Dict, Any, Callable
from fastapi import UploadFile
from openpyxl import Workbook, load_workbook

class ImportExportService:
    """
    Platform service for standardized import/export functionality.
    Modules can use this service for consistent CSV/Excel handling.
    """

    @staticmethod
    def export_to_csv(
        data: List[Dict[str, Any]],
        columns: List[Dict[str, str]]  # [{"key": "nome", "label": "Nome"}]
    ) -> str:
        """
        Export data to CSV format.

        Args:
            data: List of dictionaries
            columns: List of column definitions with key and label

        Returns:
            CSV string
        """
        output = io.StringIO()
        writer = csv.writer(output)

        # Write header
        headers = [col["label"] for col in columns]
        writer.writerow(headers)

        # Write data rows
        for row in data:
            values = [row.get(col["key"], "") for col in columns]
            writer.writerow(values)

        return output.getvalue()

    @staticmethod
    def export_to_excel(
        data: List[Dict[str, Any]],
        columns: List[Dict[str, str]],
        sheet_name: str = "Data"
    ) -> bytes:
        """
        Export data to Excel format (XLSX).
        """
        wb = Workbook()
        ws = wb.active
        ws.title = sheet_name

        # Write header
        headers = [col["label"] for col in columns]
        ws.append(headers)

        # Write data rows
        for row in data:
            values = [row.get(col["key"], "") for col in columns]
            ws.append(values)

        # Auto-adjust column widths
        for column in ws.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = min(max_length + 2, 50)
            ws.column_dimensions[column_letter].width = adjusted_width

        # Save to bytes
        output = io.BytesIO()
        wb.save(output)
        output.seek(0)
        return output.read()

    @staticmethod
    async def import_from_csv(
        file: UploadFile,
        column_mapping: Dict[str, str],  # {"CSV Column": "model_field"}
        validator: Callable[[Dict], Dict]  # Function to validate/transform row
    ) -> Dict[str, Any]:
        """
        Import data from CSV file.

        Returns:
            {
                "success": int,
                "errors": List[{"row": int, "error": str}],
                "data": List[Dict]
            }
        """
        content = await file.read()
        decoded = content.decode('utf-8')
        reader = csv.DictReader(io.StringIO(decoded))

        result = {
            "success": 0,
            "errors": [],
            "data": []
        }

        for row_num, row in enumerate(reader, start=2):  # Start at 2 (header is row 1)
            try:
                # Map CSV columns to model fields
                mapped_row = {}
                for csv_col, model_field in column_mapping.items():
                    if csv_col in row:
                        mapped_row[model_field] = row[csv_col]

                # Validate and transform
                validated_row = validator(mapped_row)

                result["data"].append(validated_row)
                result["success"] += 1

            except Exception as e:
                result["errors"].append({
                    "row": row_num,
                    "error": str(e)
                })

        return result

    @staticmethod
    def generate_import_template_csv(
        columns: List[Dict[str, str]],  # [{"key": "nome", "label": "Nome", "example": "Mario"}]
    ) -> str:
        """
        Generate a CSV template with headers and example row.
        """
        output = io.StringIO()
        writer = csv.writer(output)

        # Write header
        headers = [col["label"] for col in columns]
        writer.writerow(headers)

        # Write example row
        examples = [col.get("example", "") for col in columns]
        writer.writerow(examples)

        return output.getvalue()
```

### 6.2 Export Endpoint per Anagrafiche

```python
# backend/modules/anagrafica_italiana/routes/import_export.py (da creare)

from fastapi.responses import StreamingResponse
from app.core.services.import_export_service import ImportExportService

@router.get("/soggetti/export/{format}")
def export_soggetti(
    format: str,  # "csv" or "excel"
    attivi_solo: bool = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("soggetto.view"))
):
    """
    Export anagrafica soggetti to CSV or Excel.
    """
    if format not in ["csv", "excel"]:
        raise HTTPException(status_code=400, detail="Formato non supportato. Usa 'csv' o 'excel'.")

    # Query data
    query = db.query(SoggettoAnagrafico)
    if attivi_solo:
        query = query.filter(SoggettoAnagrafico.attivo == True)

    soggetti = query.all()

    # Prepare data
    data = []
    for s in soggetti:
        data.append({
            "id": s.id,
            "tipo": s.tipo_soggetto,
            "nome": s.nome or "",
            "cognome": s.cognome or "",
            "ragione_sociale": s.ragione_sociale or "",
            "codice_fiscale": s.codice_fiscale or "",
            "partita_iva": s.partita_iva or "",
            "email": s.email or "",
            "telefono": s.telefono or "",
            "indirizzo": s.indirizzo or "",
            "citta": s.citta or "",
            "cap": s.cap or "",
            "provincia": s.provincia or "",
            "attivo": "Sì" if s.attivo else "No"
        })

    # Define columns
    columns = [
        {"key": "id", "label": "ID"},
        {"key": "tipo", "label": "Tipo"},
        {"key": "nome", "label": "Nome"},
        {"key": "cognome", "label": "Cognome"},
        {"key": "ragione_sociale", "label": "Ragione Sociale"},
        {"key": "codice_fiscale", "label": "Codice Fiscale"},
        {"key": "partita_iva", "label": "Partita IVA"},
        {"key": "email", "label": "Email"},
        {"key": "telefono", "label": "Telefono"},
        {"key": "indirizzo", "label": "Indirizzo"},
        {"key": "citta", "label": "Città"},
        {"key": "cap", "label": "CAP"},
        {"key": "provincia", "label": "Provincia"},
        {"key": "attivo", "label": "Attivo"}
    ]

    # Generate file
    if format == "csv":
        csv_content = ImportExportService.export_to_csv(data, columns)
        return StreamingResponse(
            io.StringIO(csv_content),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=anagrafiche.csv"}
        )
    else:  # excel
        excel_bytes = ImportExportService.export_to_excel(data, columns, sheet_name="Anagrafiche")
        return StreamingResponse(
            io.BytesIO(excel_bytes),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": "attachment; filename=anagrafiche.xlsx"}
        )
```

### 6.3 Import Endpoint

```python
@router.post("/soggetti/import")
async def import_soggetti(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("soggetto.create"))
):
    """
    Import anagrafica soggetti from CSV file.
    """
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Solo file CSV supportati")

    # Define column mapping (CSV header → model field)
    column_mapping = {
        "Tipo": "tipo_soggetto",
        "Nome": "nome",
        "Cognome": "cognome",
        "Ragione Sociale": "ragione_sociale",
        "Codice Fiscale": "codice_fiscale",
        "Partita IVA": "partita_iva",
        "Email": "email",
        "Telefono": "telefono",
        "Indirizzo": "indirizzo",
        "Città": "citta",
        "CAP": "cap",
        "Provincia": "provincia"
    }

    # Validator function
    def validate_row(row: Dict) -> Dict:
        # Validate tipo_soggetto
        tipo = row.get("tipo_soggetto", "").upper()
        if tipo not in ["PERSONA_FISICA", "PERSONA_GIURIDICA"]:
            raise ValueError(f"Tipo soggetto non valido: {tipo}")

        # Validate required fields
        if tipo == "PERSONA_FISICA":
            if not row.get("nome") or not row.get("cognome"):
                raise ValueError("Nome e cognome obbligatori per persona fisica")
        else:
            if not row.get("ragione_sociale"):
                raise ValueError("Ragione sociale obbligatoria per persona giuridica")

        if not row.get("codice_fiscale") and not row.get("partita_iva"):
            raise ValueError("Almeno uno tra CF e P.IVA obbligatorio")

        # Check duplicates
        if row.get("codice_fiscale"):
            existing = db.query(SoggettoAnagrafico).filter(
                SoggettoAnagrafico.codice_fiscale == row["codice_fiscale"]
            ).first()
            if existing:
                raise ValueError(f"Codice fiscale già esistente: {row['codice_fiscale']}")

        return row

    # Import data
    result = await ImportExportService.import_from_csv(
        file=file,
        column_mapping=column_mapping,
        validator=validate_row
    )

    # Create records
    created_count = 0
    for row_data in result["data"]:
        try:
            nuovo_soggetto = SoggettoAnagrafico(**row_data)
            db.add(nuovo_soggetto)
            created_count += 1
        except Exception as e:
            result["errors"].append({
                "row": "N/A",
                "error": f"Errore creazione record: {str(e)}"
            })

    db.commit()

    return {
        "message": f"Import completato: {created_count} record creati",
        "success": created_count,
        "errors": result["errors"]
    }
```

### 6.4 Template Download

```python
@router.get("/soggetti/import-template")
def download_import_template(
    current_user: User = Depends(get_current_user)
):
    """
    Download CSV template for import.
    """
    columns = [
        {"key": "tipo", "label": "Tipo", "example": "PERSONA_FISICA"},
        {"key": "nome", "label": "Nome", "example": "Mario"},
        {"key": "cognome", "label": "Cognome", "example": "Rossi"},
        {"key": "ragione_sociale", "label": "Ragione Sociale", "example": ""},
        {"key": "codice_fiscale", "label": "Codice Fiscale", "example": "RSSMRA80A01H501U"},
        {"key": "partita_iva", "label": "Partita IVA", "example": ""},
        {"key": "email", "label": "Email", "example": "mario.rossi@example.com"},
        {"key": "telefono", "label": "Telefono", "example": "3331234567"},
        {"key": "indirizzo", "label": "Indirizzo", "example": "Via Roma 1"},
        {"key": "citta", "label": "Città", "example": "Milano"},
        {"key": "cap", "label": "CAP", "example": "20100"},
        {"key": "provincia", "label": "Provincia", "example": "MI"}
    ]

    csv_template = ImportExportService.generate_import_template_csv(columns)

    return StreamingResponse(
        io.StringIO(csv_template),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=template_import_anagrafiche.csv"}
    )
```

---

## 7. Normalizzatore Indirizzi

### 7.1 Servizio Platform

```python
# backend/app/core/services/address_normalizer.py

from typing import Dict, Optional
from sqlalchemy.orm import Session

class AddressNormalizer:
    """
    Platform service to normalize Italian addresses.
    Uses ComuneItalia data for validation and autocomplete.
    """

    @staticmethod
    def normalize_address(
        indirizzo: str,
        cap: Optional[str] = None,
        citta: Optional[str] = None,
        db: Session = None
    ) -> Dict[str, str]:
        """
        Normalize an Italian address.

        Returns:
            {
                "indirizzo": str,
                "cap": str,
                "citta": str,
                "provincia": str,
                "comune_istat_code": str,
                "normalized": bool
            }
        """
        result = {
            "indirizzo": indirizzo.strip() if indirizzo else "",
            "cap": cap.strip() if cap else "",
            "citta": citta.strip().upper() if citta else "",
            "provincia": "",
            "comune_istat_code": "",
            "normalized": False
        }

        if not db:
            return result

        # Import here to avoid circular dependency
        from anagrafica_italiana.models import ComuneItalia

        # Try to find comune by CAP and city name
        query = db.query(ComuneItalia)

        if cap and citta:
            comune = query.filter(
                ComuneItalia.cap == cap,
                ComuneItalia.nome.ilike(citta)
            ).first()

            if comune:
                result["cap"] = comune.cap
                result["citta"] = comune.nome.upper()
                result["provincia"] = comune.provincia
                result["comune_istat_code"] = comune.codice_istat
                result["normalized"] = True
                return result

        # Try by CAP only
        if cap:
            comune = query.filter(ComuneItalia.cap == cap).first()
            if comune:
                result["cap"] = comune.cap
                result["citta"] = comune.nome.upper()
                result["provincia"] = comune.provincia
                result["comune_istat_code"] = comune.codice_istat
                result["normalized"] = True
                return result

        # Try by city name only
        if citta:
            comune = query.filter(ComuneItalia.nome.ilike(citta)).first()
            if comune:
                result["cap"] = comune.cap
                result["citta"] = comune.nome.upper()
                result["provincia"] = comune.provincia
                result["comune_istat_code"] = comune.codice_istat
                result["normalized"] = True
                return result

        return result

    @staticmethod
    def autocomplete_city(
        search: str,
        limit: int = 10,
        db: Session = None
    ) -> list:
        """
        Autocomplete city names.
        """
        if not db or not search or len(search) < 2:
            return []

        from anagrafica_italiana.models import ComuneItalia

        comuni = db.query(ComuneItalia).filter(
            ComuneItalia.nome.ilike(f"{search}%")
        ).limit(limit).all()

        return [
            {
                "nome": c.nome,
                "provincia": c.provincia,
                "cap": c.cap,
                "codice_istat": c.codice_istat
            }
            for c in comuni
        ]

    @staticmethod
    def validate_cap(cap: str, provincia: Optional[str] = None, db: Session = None) -> bool:
        """
        Validate Italian postal code (CAP).
        """
        if not cap or len(cap) != 5 or not cap.isdigit():
            return False

        if not db:
            return True  # Basic validation only

        from anagrafica_italiana.models import ComuneItalia

        query = db.query(ComuneItalia).filter(ComuneItalia.cap == cap)

        if provincia:
            query = query.filter(ComuneItalia.provincia == provincia.upper())

        return query.first() is not None
```

### 7.2 API Endpoint per Autocomplete

```python
# backend/modules/anagrafica_italiana/routes/domini.py (aggiungere)

from app.core.services.address_normalizer import AddressNormalizer

@router.get("/comuni/autocomplete")
def autocomplete_comuni(
    search: str,
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Autocomplete comuni by name.
    """
    return AddressNormalizer.autocomplete_city(search=search, limit=limit, db=db)


@router.post("/normalize-address")
def normalize_address_endpoint(
    address_data: Dict[str, str],  # {indirizzo, cap, citta}
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Normalize an address using ComuneItalia data.
    """
    return AddressNormalizer.normalize_address(
        indirizzo=address_data.get("indirizzo"),
        cap=address_data.get("cap"),
        citta=address_data.get("citta"),
        db=db
    )
```

### 7.3 Frontend: Autocomplete Component

```jsx
// frontend/src/components/Platform/AddressAutocomplete.jsx

import React, { useState, useEffect } from 'react';
import axios from 'axios';
import debounce from 'lodash/debounce';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

const getAuthHeader = () => {
  const token = localStorage.getItem('access_token');
  return token ? { Authorization: `Bearer ${token}` } : {};
};

export const AddressAutocomplete = ({ value, onChange, onSelect }) => {
  const [suggestions, setSuggestions] = useState([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [loading, setLoading] = useState(false);

  // Debounced search
  const searchComuni = debounce(async (searchTerm) => {
    if (!searchTerm || searchTerm.length < 2) {
      setSuggestions([]);
      return;
    }

    setLoading(true);
    try {
      const response = await axios.get(
        `${API_BASE_URL}/anagrafica/domini/comuni/autocomplete`,
        {
          headers: getAuthHeader(),
          params: { search: searchTerm, limit: 10 }
        }
      );
      setSuggestions(response.data);
      setShowSuggestions(true);
    } catch (err) {
      console.error('Errore ricerca comuni:', err);
      setSuggestions([]);
    } finally {
      setLoading(false);
    }
  }, 300);

  useEffect(() => {
    searchComuni(value);
  }, [value]);

  const handleSelect = (comune) => {
    if (onSelect) {
      onSelect({
        citta: comune.nome,
        provincia: comune.provincia,
        cap: comune.cap,
        comune_istat_code: comune.codice_istat
      });
    }
    setShowSuggestions(false);
  };

  return (
    <div className="address-autocomplete">
      <input
        type="text"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        onFocus={() => setShowSuggestions(true)}
        onBlur={() => setTimeout(() => setShowSuggestions(false), 200)}
        placeholder="Cerca città..."
      />

      {loading && <div className="autocomplete-loading">Caricamento...</div>}

      {showSuggestions && suggestions.length > 0 && (
        <ul className="autocomplete-suggestions">
          {suggestions.map((comune, idx) => (
            <li
              key={idx}
              onClick={() => handleSelect(comune)}
              className="autocomplete-item"
            >
              <strong>{comune.nome}</strong> ({comune.provincia}) - CAP {comune.cap}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
};
```

---

## 8. UI Components Rimanenti

### 8.1 Vista Dettaglio Soggetto

```jsx
// frontend/src/modules/anagrafica_italiana/components/SoggettiAnagrafici/SoggettoDetail.jsx

import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { getSoggettoById, getSoggettoRuoli } from '../../services/anagraficaAPI';
import './SoggettoDetail.css';

export const SoggettoDetail = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [soggetto, setSoggetto] = useState(null);
  const [ruoli, setRuoli] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('anagrafica'); // anagrafica, documenti, ruoli

  useEffect(() => {
    loadSoggetto();
    loadRuoli();
  }, [id]);

  const loadSoggetto = async () => {
    try {
      const data = await getSoggettoById(id);
      setSoggetto(data);
    } catch (err) {
      setError('Errore caricamento soggetto');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const loadRuoli = async () => {
    try {
      const data = await getSoggettoRuoli(id);
      setRuoli(data);
    } catch (err) {
      console.error('Errore caricamento ruoli:', err);
    }
  };

  if (loading) return <div className="loading">Caricamento...</div>;
  if (error) return <div className="error">{error}</div>;
  if (!soggetto) return <div className="error">Soggetto non trovato</div>;

  const getNomeCompleto = () => {
    if (soggetto.tipo_soggetto === 'PERSONA_FISICA') {
      return `${soggetto.nome || ''} ${soggetto.cognome || ''}`.trim();
    }
    return soggetto.ragione_sociale;
  };

  return (
    <div className="soggetto-detail">
      <div className="detail-header">
        <button onClick={() => navigate('/anagrafiche')} className="btn-back">
          ← Torna alla lista
        </button>
        <h1>{getNomeCompleto()}</h1>
        <div className="header-actions">
          <button onClick={() => navigate(`/anagrafiche/${id}/edit`)} className="btn-edit">
            ✏️ Modifica
          </button>
        </div>
      </div>

      <div className="detail-tabs">
        <button
          className={activeTab === 'anagrafica' ? 'active' : ''}
          onClick={() => setActiveTab('anagrafica')}
        >
          Dati Anagrafici
        </button>
        <button
          className={activeTab === 'documenti' ? 'active' : ''}
          onClick={() => setActiveTab('documenti')}
        >
          Documenti
        </button>
        <button
          className={activeTab === 'ruoli' ? 'active' : ''}
          onClick={() => setActiveTab('ruoli')}
        >
          Ruoli ({ruoli.length})
        </button>
      </div>

      <div className="detail-content">
        {activeTab === 'anagrafica' && (
          <div className="anagrafica-tab">
            <div className="info-section">
              <h3>Informazioni Generali</h3>
              <div className="info-grid">
                <div className="info-item">
                  <label>Tipo</label>
                  <span>{soggetto.tipo_soggetto === 'PERSONA_FISICA' ? '👤 Persona Fisica' : '🏢 Persona Giuridica'}</span>
                </div>

                {soggetto.tipo_soggetto === 'PERSONA_FISICA' ? (
                  <>
                    <div className="info-item">
                      <label>Nome</label>
                      <span>{soggetto.nome}</span>
                    </div>
                    <div className="info-item">
                      <label>Cognome</label>
                      <span>{soggetto.cognome}</span>
                    </div>
                  </>
                ) : (
                  <div className="info-item">
                    <label>Ragione Sociale</label>
                    <span>{soggetto.ragione_sociale}</span>
                  </div>
                )}

                <div className="info-item">
                  <label>Codice Fiscale</label>
                  <span>{soggetto.codice_fiscale || '-'}</span>
                </div>
                <div className="info-item">
                  <label>Partita IVA</label>
                  <span>{soggetto.partita_iva || '-'}</span>
                </div>
              </div>
            </div>

            <div className="info-section">
              <h3>Contatti</h3>
              <div className="info-grid">
                <div className="info-item">
                  <label>Email</label>
                  <span>{soggetto.email || '-'}</span>
                </div>
                <div className="info-item">
                  <label>Telefono</label>
                  <span>{soggetto.telefono || '-'}</span>
                </div>
                <div className="info-item">
                  <label>Telefono Secondario</label>
                  <span>{soggetto.telefono_secondario || '-'}</span>
                </div>
              </div>
            </div>

            <div className="info-section">
              <h3>Indirizzo</h3>
              <div className="info-grid">
                <div className="info-item full-width">
                  <label>Indirizzo</label>
                  <span>{soggetto.indirizzo || '-'}</span>
                </div>
                <div className="info-item">
                  <label>Città</label>
                  <span>{soggetto.citta || '-'}</span>
                </div>
                <div className="info-item">
                  <label>CAP</label>
                  <span>{soggetto.cap || '-'}</span>
                </div>
                <div className="info-item">
                  <label>Provincia</label>
                  <span>{soggetto.provincia || '-'}</span>
                </div>
              </div>
            </div>

            <div className="info-section">
              <h3>Accesso Sistema</h3>
              <div className="info-grid">
                <div className="info-item">
                  <label>Utente Collegato</label>
                  <span>{soggetto.user_id ? `Sì (User ID: ${soggetto.user_id})` : 'No'}</span>
                </div>
                <div className="info-item">
                  <label>Stato</label>
                  <span className={`badge ${soggetto.attivo ? 'badge-success' : 'badge-inactive'}`}>
                    {soggetto.attivo ? 'Attivo' : 'Inattivo'}
                  </span>
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'documenti' && (
          <div className="documenti-tab">
            <h3>Gestione Documenti</h3>
            {/* TODO: Implementare DocumentoUpload e DocumentoList */}
            <p className="todo-notice">Sezione documenti da implementare</p>
          </div>
        )}

        {activeTab === 'ruoli' && (
          <div className="ruoli-tab">
            <h3>Ruoli Assegnati</h3>
            {ruoli.length === 0 ? (
              <p className="empty-message">Nessun ruolo assegnato</p>
            ) : (
              <table className="ruoli-table">
                <thead>
                  <tr>
                    <th>Ruolo</th>
                    <th>Modulo</th>
                    <th>Descrizione</th>
                    <th>Record ID</th>
                    <th>Data Assegnazione</th>
                  </tr>
                </thead>
                <tbody>
                  {ruoli.map((ruolo) => (
                    <tr key={ruolo.id}>
                      <td><strong>{ruolo.ruolo_nome}</strong></td>
                      <td>{ruolo.modulo_id}</td>
                      <td>{ruolo.ruolo_descrizione}</td>
                      <td>{ruolo.record_specializzazione_id || '-'}</td>
                      <td>{ruolo.created_at ? new Date(ruolo.created_at).toLocaleDateString('it-IT') : '-'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
            <button className="btn-add-ruolo" style={{marginTop: '20px'}}>
              + Aggiungi Ruolo
            </button>
          </div>
        )}
      </div>
    </div>
  );
};
```

### 8.2 Form Creazione/Modifica

```jsx
// frontend/src/modules/anagrafica_italiana/components/SoggettiAnagrafici/SoggettoForm.jsx

import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { getSoggettoById, createSoggetto, updateSoggetto } from '../../services/anagraficaAPI';
import { AddressAutocomplete } from '../../../../components/Platform/AddressAutocomplete';
import './SoggettoForm.css';

export const SoggettoForm = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const isEdit = Boolean(id);

  const [formData, setFormData] = useState({
    tipo_soggetto: 'PERSONA_FISICA',
    nome: '',
    cognome: '',
    ragione_sociale: '',
    codice_fiscale: '',
    partita_iva: '',
    email: '',
    telefono: '',
    telefono_secondario: '',
    indirizzo: '',
    citta: '',
    cap: '',
    provincia: '',
    attivo: true
  });

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [citySearch, setCitySearch] = useState('');

  useEffect(() => {
    if (isEdit) {
      loadSoggetto();
    }
  }, [id]);

  const loadSoggetto = async () => {
    try {
      const data = await getSoggettoById(id);
      setFormData(data);
      setCitySearch(data.citta || '');
    } catch (err) {
      setError('Errore caricamento soggetto');
      console.error(err);
    }
  };

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
  };

  const handleCitySelect = (comune) => {
    setFormData(prev => ({
      ...prev,
      citta: comune.citta,
      provincia: comune.provincia,
      cap: comune.cap
    }));
    setCitySearch(comune.citta);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      if (isEdit) {
        await updateSoggetto(id, formData);
      } else {
        await createSoggetto(formData);
      }
      navigate('/anagrafiche');
    } catch (err) {
      setError(err.response?.data?.detail || 'Errore durante il salvataggio');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const isPersonaFisica = formData.tipo_soggetto === 'PERSONA_FISICA';

  return (
    <div className="soggetto-form-page">
      <div className="form-header">
        <h1>{isEdit ? 'Modifica Soggetto' : 'Nuovo Soggetto'}</h1>
        <button onClick={() => navigate('/anagrafiche')} className="btn-cancel">
          Annulla
        </button>
      </div>

      <form onSubmit={handleSubmit} className="soggetto-form">
        <div className="form-section">
          <h3>Tipo Soggetto</h3>
          <div className="form-group">
            <label>
              <input
                type="radio"
                name="tipo_soggetto"
                value="PERSONA_FISICA"
                checked={formData.tipo_soggetto === 'PERSONA_FISICA'}
                onChange={handleChange}
              />
              👤 Persona Fisica
            </label>
            <label>
              <input
                type="radio"
                name="tipo_soggetto"
                value="PERSONA_GIURIDICA"
                checked={formData.tipo_soggetto === 'PERSONA_GIURIDICA'}
                onChange={handleChange}
              />
              🏢 Persona Giuridica
            </label>
          </div>
        </div>

        <div className="form-section">
          <h3>Dati Identificativi</h3>

          {isPersonaFisica ? (
            <div className="form-row">
              <div className="form-group">
                <label>Nome *</label>
                <input
                  type="text"
                  name="nome"
                  value={formData.nome}
                  onChange={handleChange}
                  required
                />
              </div>
              <div className="form-group">
                <label>Cognome *</label>
                <input
                  type="text"
                  name="cognome"
                  value={formData.cognome}
                  onChange={handleChange}
                  required
                />
              </div>
            </div>
          ) : (
            <div className="form-group">
              <label>Ragione Sociale *</label>
              <input
                type="text"
                name="ragione_sociale"
                value={formData.ragione_sociale}
                onChange={handleChange}
                required
              />
            </div>
          )}

          <div className="form-row">
            <div className="form-group">
              <label>Codice Fiscale *</label>
              <input
                type="text"
                name="codice_fiscale"
                value={formData.codice_fiscale}
                onChange={handleChange}
                pattern="[A-Z0-9]{16}"
                title="Formato CF: 16 caratteri alfanumerici"
                required={!formData.partita_iva}
              />
            </div>
            <div className="form-group">
              <label>Partita IVA</label>
              <input
                type="text"
                name="partita_iva"
                value={formData.partita_iva}
                onChange={handleChange}
                pattern="[0-9]{11}"
                title="Formato P.IVA: 11 cifre"
              />
            </div>
          </div>
        </div>

        <div className="form-section">
          <h3>Contatti</h3>
          <div className="form-row">
            <div className="form-group">
              <label>Email</label>
              <input
                type="email"
                name="email"
                value={formData.email}
                onChange={handleChange}
              />
            </div>
            <div className="form-group">
              <label>Telefono</label>
              <input
                type="tel"
                name="telefono"
                value={formData.telefono}
                onChange={handleChange}
              />
            </div>
            <div className="form-group">
              <label>Telefono Secondario</label>
              <input
                type="tel"
                name="telefono_secondario"
                value={formData.telefono_secondario}
                onChange={handleChange}
              />
            </div>
          </div>
        </div>

        <div className="form-section">
          <h3>Indirizzo</h3>
          <div className="form-group">
            <label>Indirizzo</label>
            <input
              type="text"
              name="indirizzo"
              value={formData.indirizzo}
              onChange={handleChange}
              placeholder="Via, numero civico"
            />
          </div>

          <div className="form-row">
            <div className="form-group">
              <label>Città</label>
              <AddressAutocomplete
                value={citySearch}
                onChange={setCitySearch}
                onSelect={handleCitySelect}
              />
            </div>
            <div className="form-group">
              <label>CAP</label>
              <input
                type="text"
                name="cap"
                value={formData.cap}
                onChange={handleChange}
                pattern="[0-9]{5}"
                title="Formato CAP: 5 cifre"
              />
            </div>
            <div className="form-group">
              <label>Provincia</label>
              <input
                type="text"
                name="provincia"
                value={formData.provincia}
                onChange={handleChange}
                maxLength={2}
                placeholder="MI"
              />
            </div>
          </div>
        </div>

        <div className="form-section">
          <div className="form-group checkbox-group">
            <label>
              <input
                type="checkbox"
                name="attivo"
                checked={formData.attivo}
                onChange={handleChange}
              />
              Soggetto attivo
            </label>
          </div>
        </div>

        {error && <div className="error-message">{error}</div>}

        <div className="form-actions">
          <button type="button" onClick={() => navigate('/anagrafiche')} className="btn-cancel">
            Annulla
          </button>
          <button type="submit" disabled={loading} className="btn-submit">
            {loading ? 'Salvataggio...' : (isEdit ? 'Aggiorna' : 'Crea')}
          </button>
        </div>
      </form>
    </div>
  );
};
```

---

## 9. Dashboard Specifica Modulo

### 9.1 Widget: Statistiche Anagrafiche

```jsx
// frontend/src/modules/anagrafica_italiana/components/Widgets/StatsSoggettiWidget.jsx

import React, { useState, useEffect } from 'react';
import { getSoggettiAnagrafici } from '../../services/anagraficaAPI';
import './StatsSoggettiWidget.css';

export const StatsSoggettiWidget = () => {
  const [stats, setStats] = useState({
    totale: 0,
    persone_fisiche: 0,
    persone_giuridiche: 0,
    attivi: 0,
    con_accesso_sistema: 0
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadStats();
  }, []);

  const loadStats = async () => {
    try {
      // Fetch all soggetti (consider adding a dedicated stats endpoint)
      const data = await getSoggettiAnagrafici({ limit: 1000 });

      const totale = data.length;
      const persone_fisiche = data.filter(s => s.tipo_soggetto === 'PERSONA_FISICA').length;
      const persone_giuridiche = data.filter(s => s.tipo_soggetto === 'PERSONA_GIURIDICA').length;
      const attivi = data.filter(s => s.attivo).length;
      const con_accesso_sistema = data.filter(s => s.user_id).length;

      setStats({
        totale,
        persone_fisiche,
        persone_giuridiche,
        attivi,
        con_accesso_sistema
      });
    } catch (err) {
      console.error('Errore caricamento statistiche:', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <div className="widget-loading">Caricamento...</div>;

  return (
    <div className="stats-soggetti-widget">
      <h3>Statistiche Anagrafiche</h3>

      <div className="stats-grid">
        <div className="stat-card totale">
          <div className="stat-value">{stats.totale}</div>
          <div className="stat-label">Totale Anagrafiche</div>
        </div>

        <div className="stat-card persone-fisiche">
          <div className="stat-value">👤 {stats.persone_fisiche}</div>
          <div className="stat-label">Persone Fisiche</div>
        </div>

        <div className="stat-card persone-giuridiche">
          <div className="stat-value">🏢 {stats.persone_giuridiche}</div>
          <div className="stat-label">Persone Giuridiche</div>
        </div>

        <div className="stat-card attivi">
          <div className="stat-value">✅ {stats.attivi}</div>
          <div className="stat-label">Attivi</div>
        </div>

        <div className="stat-card con-accesso">
          <div className="stat-value">🔑 {stats.con_accesso_sistema}</div>
          <div className="stat-label">Con Accesso Sistema</div>
        </div>
      </div>
    </div>
  );
};
```

### 9.2 Registrazione Widget

```python
# backend/modules/anagrafica_italiana/__manifest__.py (già presente, verificare)

manifest = {
    # ...
    "widgets": [
        {
            "id": "anagrafica_italiana.stats_soggetti",
            "title": "Statistiche Anagrafiche",
            "component": "StatsSoggettiWidget",
            "default_width": 6,
            "default_height": 4,
            "category": "stats",
            "required_permission": "soggetto.view",
            "description": "Panoramica delle anagrafiche registrate (persone fisiche e giuridiche)",
        },
    ],
}
```

```javascript
// frontend/src/modules/anagrafica_italiana/index.js (aggiungere export)

export { StatsSoggettiWidget } from './components/Widgets/StatsSoggettiWidget';
```

---

## 10. Priorità di Implementazione (AGGIORNATO 9 Dicembre 2025)

### ✅ Sprint 0: Sistema Ruoli Azienda (COMPLETATO - 2 settimane)
- ✅ Modelli RuoloAzienda, RuoloAziendaTipo
- ✅ API CRUD complete per ruoli azienda
- ✅ API CRUD per domini tipi ruolo
- ✅ RuoliAziendaSection.jsx (vista nelle schede soggetto)
- ✅ RuoliAziendaList.jsx (lista centralizzata)
- ✅ RuoloAziendaForm.jsx (form con SELECT + custom)
- ✅ RuoliAziendaTipiList.jsx (CRUD domini)
- ✅ Seed data 8 ruoli standard
- ✅ Display dinamico ruolo_tipo_nome con live updates
- ✅ Storicizzazione periodi impiego

### ⚠️ Sprint 1: Fondamenta Ruoli Business (1-2 settimane) - PARZIALE
- ✅ Modelli RuoloDisponibile, SoggettoRuolo (già esistenti in core)
- ❌ Registrazione automatica ruoli da manifest
- ❌ API per assegnazione/rimozione ruoli business
- ❌ API lista ruoli disponibili
- ❌ Test backend ruoli

### ✅ Sprint 2: Integrazione Utenti (COMPLETATO - 1 settimana)
- ✅ Endpoint creazione User da Soggetto
- ✅ Modifica login per includere soggetto_id in token
- ✅ Test integrazione User-Soggetto

### ❌ Sprint 3: Cono di Visibilità (2 settimane) - DA INIZIARE
- ❌ VisibilityService con filtri per UnitaImmobiliare, Contratto
- ❌ Integrazione nelle route esistenti
- ❌ Test visibilità per diversi ruoli
- ❌ Documentazione pattern per nuovi moduli

### ✅ Sprint 4: UI Componenti Base (COMPLETATO - 2 settimane)
- ✅ PersonaFisicaDetail.jsx completo (con tabs)
- ✅ PersonaGiuridicaDetail.jsx completo (con tabs)
- ✅ Form separati per PF e PG con validazione
- ✅ Route complete e navigation
- ✅ CSS responsive con stati empty/loading/error
- ⚠️ Nota: Implementate viste separate invece di SoggettoDetail unificato (scelta architetturale)

### ✅ Sprint 5: Documenti (COMPLETATO - 1-2 settimane)
- ✅ DocumentoUpload.jsx
- ✅ API upload/download funzionanti
- ✅ Gestione scadenze con ScadenzarioService
- ✅ Integrazione DocumentService platform

### ❌ Sprint 6: Normalizzatore Indirizzi (1 settimana) - DA INIZIARE
- ❌ AddressNormalizer service
- ❌ AddressAutocomplete component
- ❌ Integrazione in form soggetti
- ❌ API autocomplete comuni

### ❌ Sprint 7: Import/Export (1 settimana) - DA INIZIARE
- ❌ ImportExportService platform
- ❌ Endpoint export CSV/Excel
- ❌ Endpoint import con validazione
- ❌ Template download
- ❌ Frontend per trigger import/export

### ❌ Sprint 8: Dashboard e Widget (1 settimana) - DA INIZIARE
- ❌ StatsSoggettiWidget
- ❌ Widget documenti in scadenza
- ❌ Widget ultimi soggetti inseriti
- ❌ Dashboard specifica anagrafica

### ❌ Sprint 9: Testing e Refinement (1 settimana) - DA INIZIARE
- ❌ Test end-to-end completi
- ❌ Performance optimization
- ❌ UX improvements
- ❌ Documentazione utente finale

**Riepilogo Stato Sprint:**
- ✅ **Completati**: Sprint 0 (Ruoli Azienda), Sprint 2 (Integrazione Utenti), Sprint 4 (UI Base), Sprint 5 (Documenti)
- ⚠️ **Parziali**: Sprint 1 (Ruoli Business - solo modelli)
- ❌ **Da iniziare**: Sprint 3, 6, 7, 8, 9

---

## 11. Conclusioni (AGGIORNATE 9 Dicembre 2025)

Questo documento fornisce una roadmap completa per l'implementazione del modulo Anagrafica con tutte le funzionalità richieste.

### ✅ **Implementazioni Completate**

**Sistema Ruoli Azienda (NUOVO):**
- ✅ Backend completo: modelli, API CRUD, domini normalizzati
- ✅ Frontend completo: 4 componenti UI funzionali
- ✅ 8 ruoli standard seeded (Segretaria, Amm. Delegato, ecc.)
- ✅ Storicizzazione periodi impiego
- ✅ Display dinamico con live updates da domini
- ✅ Vista bidirezionale persona↔azienda

**Anagrafica Base:**
- ✅ Modello SoggettoAnagrafico con user_id
- ✅ API CRUD complete per soggetti
- ✅ Domini (ComuneItalia, TipoDocumento, RuoliAziendaTipi)
- ✅ UI complete: liste PF, PG, dettagli con tabs
- ✅ Form separati per persona fisica/giuridica
- ✅ Menu dinamico registrato da manifest

**Gestione Documenti:**
- ✅ Upload documenti con DocumentService
- ✅ Integrazione ScadenzarioService
- ✅ API lista con filtri (categoria, scaduti)

**User Management:**
- ✅ Creazione user da soggetto
- ✅ Login con soggetto_id in JWT
- ✅ Remember me funzionale

### ⚠️ **Implementazioni Parziali**

**Sistema Ruoli Business:**
- ✅ Modelli esistenti (RuoloDisponibile, SoggettoRuolo)
- ✅ Tabelle database create
- ❌ API endpoints non implementati
- ❌ Registrazione automatica da manifest assente
- ❌ UI per assegnazione ruoli assente

### ❌ **Da Implementare (in ordine di priorità)**

1. **Sistema Ruoli Business completo** (API + UI + registrazione automatica)
2. **VisibilityService** per cono di visibilità basato su ruoli business
3. **Import/Export** CSV/Excel con template e validazione
4. **AddressNormalizer** con autocomplete comuni
5. **Dashboard Widget** anagrafica (stats, documenti in scadenza)

### Differenza Critica: Due Sistemi di Ruoli

**IMPORTANTE**: Questo documento è stato aggiornato il 9 Dicembre 2025 per riflettere che il modulo gestisce **DUE sistemi di ruoli distinti**:

1. **Ruoli Azienda** (✅ COMPLETO): Relazioni lavorative PF-PG
2. **Ruoli Business** (⚠️ PARZIALE): Cono di visibilità dati

Vedi sezione 1.3 per dettagli sulla distinzione.

### Stato Complessivo

**Completamento stimato:** ~60% delle funzionalità documentate

**Sprint completati:** 4 su 9 (Sprint 0, 2, 4, 5)
**Sprint rimanenti:** 5 (Sprint 1, 3, 6, 7, 8, 9)

**Tempo stimato per completamento:**
- Ruoli Business completo: 2-3 settimane
- VisibilityService: 2 settimane
- Funzionalità avanzate: 3-4 settimane
- **Totale rimanente:** 7-9 settimane

Il sistema è progettato per essere modulare, riusabile e scalabile. Ogni componente può essere implementato incrementalmente senza bloccare lo sviluppo di altre funzionalità.

### Change Log

**Versione 1.1 (9 Dicembre 2025):**
- ✅ Aggiunta sezione completa Sistema Ruoli Azienda (Sezione 2)
- ✅ Chiarimento differenza Ruoli Azienda vs Ruoli Business (Sezione 1.3)
- ✅ Aggiornato stato implementazione (Sezione 1.2)
- ✅ Aggiornate priorità sprint (Sezione 10)
- ✅ Riferimento a documento di verifica (ANAGRAFICA_VERIFICA_IMPLEMENTAZIONE.md)

**Versione 1.0 (7 Dicembre 2025):**
- Documento iniziale (non includeva Sistema Ruoli Azienda)

---

*Documento aggiornato il 9 Dicembre 2025 - Versione 1.1*
*Vedi anche: ANAGRAFICA_VERIFICA_IMPLEMENTAZIONE.md per analisi dettagliata*
