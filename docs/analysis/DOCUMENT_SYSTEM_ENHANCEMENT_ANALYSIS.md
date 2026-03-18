# Analisi Interventi Sistema Gestione Documenti
**Data**: 2026-01-31
**Versione**: 1.0
**Status**: Analisi Preliminare

## Indice
1. [Executive Summary](#executive-summary)
2. [Stato Attuale](#stato-attuale)
3. [Requisiti Funzionali](#requisiti-funzionali)
4. [Analisi Gap](#analisi-gap)
5. [Architettura Proposta](#architettura-proposta)
6. [Piano di Implementazione](#piano-di-implementazione)
7. [Impatto e Rischi](#impatto-e-rischi)

---

## Executive Summary

### Obiettivo
Evolvere il sistema di gestione documenti dalla attuale architettura single-file verso un sistema multi-file con:
- Parsing automatico intelligente
- Normalizzazione formato visualizzazione
- Merge automatico anagrafiche
- Workflow di validazione e aggiornamento dati

### Criticità Identificate
- ⚠️ **Alta Complessità**: Richiede modifiche a core platform e modulo anagrafica
- ⚠️ **Migrazione Dati**: Necessità di migrare documenti esistenti
- ⚠️ **Performance**: Conversione file può impattare su storage e CPU
- ✅ **Architettura Esistente Solida**: Sistema parsing già implementato e funzionante

---

## Stato Attuale

### 1. Architettura Corrente

#### Backend - Core Platform
```
app/core/
├── platform/models/
│   ├── document_job.py              # Job parsing asincrono ✓
│   ├── document_parsing_log.py      # Log debug servizi esterni ✓
│   └── parsing_service_config.py    # Config servizi parsing ✓
│
├── platform_services/
│   ├── document_parsing_service.py  # Orchestrazione parsing ✓
│   └── document_type_registry.py    # Registry tipi documento ✓
│
├── routes/
│   ├── document_parsing.py          # API parsing core ✓
│   └── document_parsing_debug.py    # API debug parsing ✓
│
└── file_storage.py                   # Storage multi-tenant ✓
```

#### Backend - Modulo Anagrafica
```
modules/anagrafica_italiana/
├── models/
│   ├── documento.py                  # **SINGLE FILE MODEL** ⚠️
│   ├── tipo_documento.py            # Configurazione parsing ✓
│   └── stato_documento.py           # Stati workflow ✓
│
├── routes/
│   ├── documenti.py                 # CRUD documenti
│   └── anagrafica_from_document.py  # Creazione da documento ✓
│
├── services/
│   └── document_service.py          # Business logic documenti ✓
│
└── schemas/
    └── document_parsing.py          # DTO parsing
```

### 2. Funzionalità Esistenti ✅

#### Sistema di Parsing Asincrono
- **DocumentJob**: Tracciamento job di parsing
  - Status: PENDING → QUEUED → PROCESSING → COMPLETED/FAILED
  - Multi-tenancy support
  - Retry logic (max 3 tentativi)
  - Confidence score (0-100)
  - Callback integration

- **DocumentParsingService**: Orchestrazione workflow
  - Upload file temp
  - Submit a servizi esterni (HTTP/Redis/WebSocket)
  - Gestione callback
  - Creazione notifiche (Scadenze)
  - Logging completo (DocumentParsingLog)

- **TipoDocumento**: Configurazione parsing per tipo
  ```python
  parsing_service: str          # "mrz", "contract_parser", etc.
  parsing_config: JSON          # Config servizio
  parsing_callback_url: str     # URL callback custom
  ```

#### Workflow "Crea Anagrafica da Documento"
1. Upload documento identità → `POST /anagrafica/from-document/upload-identity-document`
2. DocumentJob creato (status=PENDING)
3. File salvato in temp storage: `storage/{tenant}/temp_uploads/{job_uuid}/`
4. Submit a servizio parsing (es: MRZ per CI/Passaporti)
5. Callback servizio → status=COMPLETED, parsing_result salvato
6. Scadenza creata per notificare utente
7. Utente rivede dati → `POST /anagrafica/from-document/complete`
8. SoggettoAnagrafico creato
9. File spostato da temp a permanente: `storage/{tenant}/{entity_type}/{entity_id}/`
10. Documento record creato e linkato

#### File Storage Multi-Tenant
- **Path structure**: `storage/{tenant_schema}/{entity_type}/{entity_id}/{uuid}_{filename}`
- **Temp uploads**: `storage/{tenant_schema}/temp_uploads/{job_uuid}/{filename}`
- **Security**: Validazione path, no directory traversal
- **Operations**: save_file, delete_file, move_from_temp, get_file_path

### 3. Limitazioni Attuali ⚠️

#### A. Modello Single-File
```python
# Documento attuale (modules/anagrafica_italiana/models/documento.py)
class Documento(Base):
    id: int
    entity_type: str              # SOGGETTO_ANAGRAFICO, IMMOBILE, etc.
    entity_id: int
    tipo_documento: TipoDocumentoEnum
    nome_file: str                # ⚠️ SINGOLO FILE
    file_path: str                # ⚠️ SINGOLO PATH
    mime_type: str
    dimensione: int
    descrizione: str
    data_scadenza: Date
    # NO MULTI-PAGE SUPPORT
    # NO PARSED DATA STORAGE
```

**Problemi**:
- ❌ Non supporta documenti multi-pagina (fronte/retro CI, passaporti multi-page)
- ❌ Dati parsati salvati in DocumentJob.parsing_result (separato da Documento)
- ❌ No metadata strutturati nel documento
- ❌ Difficile gestire versioni/revisioni documento

#### B. Parsing Data Separation
```python
# Dati parsati salvati in DocumentJob (core platform)
DocumentJob.parsing_result: JSON   # Dati estratti dal servizio

# Documento (anagrafica module) non contiene dati parsati
Documento                          # Solo riferimento file
```

**Problemi**:
- ❌ Dati parsati e documento fisico sono disaccoppiati
- ❌ Difficile query su dati parsati (es: trova documenti con CF=XXX)
- ❌ DocumentJob potrebbe essere eliminato dopo workflow completion

#### C. No Document Normalization
- ❌ File salvati nel formato originale (JPG, PNG, PDF, etc.)
- ❌ Frontend deve gestire rendering diversi formati
- ❌ Servizi parsing ricevono formati eterogenei
- ❌ No cache formato normalizzato

#### D. No Merge/Deduplication Logic
- ❌ Sistema non suggerisce anagrafiche esistenti simili
- ❌ Rischio duplicati (stessa persona con CF scritto diversamente)
- ❌ No rilevamento incongruenze dati documento vs anagrafica

#### E. Frontend Viewing
- Componenti base esistono ma limitati:
  - `DocumentoList.jsx`: Lista documenti entity
  - `DocumentoUpload.jsx`: Upload singolo file
  - NO visualizzatore multi-page
  - NO viewer formato standardizzato

---

## Requisiti Funzionali

### REQ-1: Documenti Multi-File ⭐⭐⭐ (ALTA PRIORITÀ)

**Descrizione**: Un documento deve supportare più file/immagini associate.

**User Story**:
> "Come utente, voglio caricare fronte e retro della carta d'identità come un unico documento,
> così che siano sempre associati e non devo gestire due documenti separati."

**Acceptance Criteria**:
- [ ] Un Documento può avere N file associati (relazione 1-to-many)
- [ ] Ogni file ha: `nome_file`, `file_path`, `mime_type`, `dimensione`, `ordine`, `tipo_pagina` (fronte/retro/pagina_N)
- [ ] Upload supporta multi-file in singola operazione
- [ ] API GET documento restituisce tutti i file associati
- [ ] Eliminazione documento elimina tutti i file associati (cascade)

**Modelli Impattati**:
- `Documento` (anagrafica_italiana) → parent
- `DocumentoFile` (nuovo) → child con FK a Documento

**API Changes**:
```python
# Nuovo modello
class DocumentoFile(Base):
    id: int
    documento_id: int              # FK a Documento
    file_path: str
    nome_file: str
    mime_type: str
    dimensione: int
    ordine: int                    # Ordine visualizzazione (1, 2, 3...)
    tipo_pagina: str               # "fronte", "retro", "pagina_1", "pagina_2", etc.
    file_normalizzato_path: str    # Path file convertito (cache)
    created_at: DateTime

# Documento modificato
class Documento(Base):
    id: int
    entity_type: str
    entity_id: int
    tipo_documento_id: int
    descrizione: str
    data_scadenza: Date
    metadata_parsato: JSON         # NUOVO: dati estratti da parsing
    confidence_score: int          # NUOVO: score complessivo parsing
    # Files → relationship a DocumentoFile
```

**Workflow Upload Multi-File**:
1. `POST /documenti/upload-multi` con array di file
2. Crea 1 Documento parent
3. Crea N DocumentoFile child
4. Se tipo_documento ha parsing_service:
   - Crea 1 DocumentJob per file
   - Quando tutti job completati → merge risultati in Documento.metadata_parsato

---

### REQ-2: Parsing Opzionale Per File ⭐⭐ (MEDIA PRIORITÀ)

**Descrizione**: Ogni file può avere parsing automatico, ma non è obbligatorio.

**User Story**:
> "Come utente, voglio che il fronte della CI venga parsato automaticamente per estrarre i dati,
> mentre il retro viene solo archiviato senza parsing."

**Acceptance Criteria**:
- [ ] TipoDocumento definisce se parsing è richiesto/opzionale
- [ ] DocumentoFile può avere `parsing_job_id` (nullable) → FK a DocumentJob
- [ ] Configurazione parsing a livello tipo_documento specifica quali pagine parsare
- [ ] Frontend permette di scegliere quali file inviare a parsing

**Configurazione Esempio**:
```json
// TipoDocumento.parsing_config
{
  "pages": {
    "fronte": {
      "parsing_required": true,
      "service": "mrz",
      "config": {"format": "td1"}
    },
    "retro": {
      "parsing_required": false
    }
  }
}
```

---

### REQ-3: Storage Dati Parsati in Documento ⭐⭐⭐ (ALTA PRIORITÀ)

**Descrizione**: Dati estratti dal parsing salvati come metadata del documento.

**User Story**:
> "Come utente, voglio che i dati estratti dalla CI (nome, cognome, CF) siano salvati nel documento,
> così posso interrogarli e usarli anche dopo eliminazione del DocumentJob."

**Acceptance Criteria**:
- [ ] Documento ha campo `metadata_parsato: JSON` con dati estratti
- [ ] Documento ha campo `confidence_score: int` con score medio parsing
- [ ] Callback parsing aggiorna Documento.metadata_parsato (oltre a DocumentJob.parsing_result)
- [ ] API GET documento include metadata parsati
- [ ] Possibile query su metadata (es: trova documenti con CF=XXX)

**Schema Metadata**:
```json
{
  "codice_fiscale": "RSSMRA80A01H501Z",
  "nome": "MARIO",
  "cognome": "ROSSI",
  "data_nascita": "1980-01-01",
  "luogo_nascita": "ROMA",
  "sesso": "M",
  "data_emissione": "2020-01-15",
  "data_scadenza": "2030-01-15",
  "numero_documento": "CA12345AB",
  "autorita_emissione": "COMUNE DI ROMA",
  "confidence_scores": {
    "codice_fiscale": 0.98,
    "nome": 0.95,
    "cognome": 0.97,
    "overall": 0.96
  }
}
```

---

### REQ-4: Aggiornamento Anagrafica da Documento ⭐⭐⭐ (ALTA PRIORITÀ)

**Descrizione**: Possibilità di aggiornare dati anagrafica esistente con dati da documento parsato.

**User Story**:
> "Come utente, quando carico un nuovo documento su un'anagrafica esistente,
> voglio vedere le differenze tra dati attuali e dati estratti dal documento,
> e scegliere se aggiornare l'anagrafica."

**Acceptance Criteria**:
- [ ] API confronta dati documento parsato vs dati anagrafica
- [ ] Frontend mostra diff side-by-side (old value / new value)
- [ ] Utente può selezionare quali campi aggiornare
- [ ] Aggiornamento crea audit trail (chi, quando, da quale documento)

**API Endpoint**:
```python
POST /anagrafica/soggetti/{id}/update-from-document
{
  "documento_id": 123,
  "fields_to_update": ["telefono", "indirizzo", "cap"]
}
→ Returns: updated SoggettoAnagrafico
```

**Frontend Flow**:
1. Carico documento su anagrafica esistente
2. Documento parsato → metadata_parsato popolato
3. Frontend mostra:
   ```
   Campo           | Valore Attuale      | Valore Documento  | Azione
   ----------------|---------------------|-------------------|--------
   Nome            | Mario               | Mario             | [=]
   Cognome         | Rossi               | Rossi             | [=]
   CF              | RSSMRA80A01H501Z    | RSSMRA80A01H501Z  | [=]
   Telefono        | 06-12345678         | 06-87654321       | [Aggiorna]
   Indirizzo       | Via Roma 1          | Via Napoli 5      | [Aggiorna]
   ```
4. Utente seleziona campi da aggiornare → click "Aggiorna"
5. API aggiorna SoggettoAnagrafico + log modifica

---

### REQ-5: Creazione Anagrafica con Merge Intelligente ⭐⭐⭐ (ALTA PRIORITÀ)

**Descrizione**: Quando creo anagrafica da documento, sistema suggerisce anagrafiche esistenti simili.

**User Story**:
> "Come utente, quando carico un documento di identità senza selezionare un'anagrafica,
> voglio che il sistema mi suggerisca se esiste già un'anagrafica simile (stesso CF, nome/cognome simile),
> così evito di creare duplicati."

**Acceptance Criteria**:
- [ ] Algoritmo similarity matching su:
  - Codice Fiscale (exact match → 100% match)
  - Nome + Cognome + Data Nascita (fuzzy match → 80-99% match)
  - Solo Nome + Cognome (fuzzy match → 50-79% match)
- [ ] API restituisce lista anagrafiche candidate con score
- [ ] Frontend mostra candidates + opzione "Crea Nuovo"
- [ ] Se utente seleziona candidate → aggiunge documento a anagrafica esistente
- [ ] Se utente sceglie "Crea Nuovo" → crea nuova anagrafica

**API Endpoint**:
```python
POST /anagrafica/find-similar
{
  "codice_fiscale": "RSSMRA80A01H501Z",
  "nome": "Mario",
  "cognome": "Rossi",
  "data_nascita": "1980-01-01"
}
→ Returns:
[
  {
    "soggetto_id": 45,
    "similarity_score": 1.0,  # 100% - CF exact match
    "match_reason": "Codice fiscale identico",
    "soggetto": {...}
  },
  {
    "soggetto_id": 67,
    "similarity_score": 0.85, # 85% - nome/cognome simile
    "match_reason": "Nome e cognome molto simili (Mario Rossi vs Mario De Rossi)",
    "soggetto": {...}
  }
]
```

**Algoritmo Similarity**:
```python
def calculate_similarity(parsed_data, existing_soggetto):
    score = 0

    # CF exact match = 100%
    if parsed_data["codice_fiscale"] == existing_soggetto.codice_fiscale:
        return 1.0

    # Nome + Cognome + Data Nascita
    nome_score = levenshtein_similarity(parsed_data["nome"], existing_soggetto.nome)
    cognome_score = levenshtein_similarity(parsed_data["cognome"], existing_soggetto.cognome)

    if parsed_data["data_nascita"] == existing_soggetto.data_nascita:
        birth_score = 1.0
    else:
        birth_score = 0.0

    # Weighted average
    score = (nome_score * 0.3) + (cognome_score * 0.3) + (birth_score * 0.4)
    return score
```

---

### REQ-6: Rilevamento Incongruenze ⭐⭐ (MEDIA PRIORITÀ)

**Descrizione**: Se carico documento su anagrafica esistente e dati non coincidono, sistema avvisa.

**User Story**:
> "Come utente, se carico una CI su un'anagrafica ma il CF del documento è diverso da quello registrato,
> voglio che il sistema mi avvisi che potrebbero essere due persone diverse."

**Acceptance Criteria**:
- [ ] Validazione dati parsati vs anagrafica al salvataggio documento
- [ ] Se CF diverso → warning "Il codice fiscale del documento non corrisponde"
- [ ] Se nome/cognome molto diversi → warning "Nome e cognome differiscono significativamente"
- [ ] Utente può:
  - Ignorare warning (documento salvato comunque)
  - Aggiornare anagrafica con dati documento
  - Creare nuova anagrafica

**API Response**:
```json
{
  "documento_id": 123,
  "warnings": [
    {
      "field": "codice_fiscale",
      "type": "MISMATCH",
      "severity": "HIGH",
      "message": "Il codice fiscale del documento (RSSMRA80A01H501Z) differisce da quello registrato (RSSMRA80A01H501A)",
      "suggested_action": "CREATE_NEW_SUBJECT"
    },
    {
      "field": "nome",
      "type": "SIMILARITY_LOW",
      "severity": "MEDIUM",
      "message": "Il nome del documento (Marco) è diverso da quello registrato (Mario)",
      "suggested_action": "UPDATE_SUBJECT"
    }
  ]
}
```

---

### REQ-7: Visualizzatore Documento Standard ⭐⭐⭐ (ALTA PRIORITÀ)

**Descrizione**: Componente frontend standardizzato per visualizzare documenti multi-page.

**User Story**:
> "Come utente, voglio visualizzare tutti i documenti (immagini, PDF) in un formato uniforme,
> con navigazione tra pagine, zoom, e annotazioni."

**Acceptance Criteria**:
- [ ] Componente `<DocumentViewer documento_id={123} />`
- [ ] Supporta multi-page navigation (frecce, thumbnails)
- [ ] Rendering formato normalizzato (sempre JPEG o PNG)
- [ ] Features:
  - Zoom in/out
  - Rotate
  - Download originale
  - Full-screen mode
- [ ] Overlay metadata parsati (opzionale)

**Tecnologie Suggerite**:
- **PDF rendering**: PDF.js o React-PDF
- **Image viewing**: React Image Gallery o PhotoSwipe
- **Unified viewer**: react-viewer o custom component

---

### REQ-8: Normalizzazione Formato File ⭐⭐⭐ (ALTA PRIORITÀ)

**Descrizione**: Convertire tutti i file in un formato standard per visualizzazione e parsing.

**User Story**:
> "Come utente, voglio che tutti i documenti siano visualizzati in modo consistente,
> indipendentemente dal formato originale (JPG, PNG, PDF, HEIC, etc.)."

**Acceptance Criteria**:
- [ ] Formato target: **JPEG** (universale, compresso, supporto browser)
- [ ] Conversione on-upload:
  - PDF → JPEG per pagina
  - PNG → JPEG
  - HEIC/HEIF → JPEG
  - TIFF → JPEG
- [ ] File convertiti salvati in cache: `{file_path}_normalized.jpg`
- [ ] DocumentoFile ha campo `file_normalizzato_path`
- [ ] Servizi parsing ricevono sempre JPEG

**Workflow**:
1. Upload file originale (es: passport.pdf)
2. Save originale: `storage/tenant_test/SOGGETTO/45/uuid_passport.pdf`
3. Convert a JPEG:
   - Pagina 1 → `storage/tenant_test/SOGGETTO/45/uuid_passport_p1.jpg`
   - Pagina 2 → `storage/tenant_test/SOGGETTO/45/uuid_passport_p2.jpg`
4. Create DocumentoFile records:
   ```python
   DocumentoFile(
       file_path="tenant_test/SOGGETTO/45/uuid_passport.pdf",
       file_normalizzato_path="tenant_test/SOGGETTO/45/uuid_passport_p1.jpg",
       ordine=1
   )
   ```
5. Submit a parsing: usa `file_normalizzato_path`

**Librerie Conversione**:
- **Python**: Pillow (PIL), pdf2image (poppler), img2pdf
- **Formato**: JPEG quality 85%, max dimension 2048px

**Vantaggi**:
- ✅ Parsing services ricevono sempre immagini ottimizzate
- ✅ Frontend rendering uniforme
- ✅ Riduzione storage (JPEG compresso vs PDF/PNG)
- ✅ Compatibilità universale browser

---

## Analisi Gap

### Gap Tecnici

| Funzionalità | Stato Attuale | Stato Richiesto | Gap | Priorità |
|--------------|---------------|-----------------|-----|----------|
| Multi-file per documento | ❌ Single file | ✅ N file per documento | ALTO | ⭐⭐⭐ |
| Metadata parsati in Documento | ❌ Solo in DocumentJob | ✅ In Documento.metadata_parsato | ALTO | ⭐⭐⭐ |
| Normalizzazione file | ❌ Formato originale | ✅ Conversione JPEG | ALTO | ⭐⭐⭐ |
| Merge anagrafica | ❌ No algoritmo | ✅ Similarity matching | ALTO | ⭐⭐⭐ |
| Aggiornamento da documento | ❌ No workflow | ✅ Diff + selective update | MEDIO | ⭐⭐ |
| Rilevamento incongruenze | ❌ No validazione | ✅ Warning + suggestions | MEDIO | ⭐⭐ |
| Visualizzatore standard | ⚠️ Base components | ✅ Viewer unificato | MEDIO | ⭐⭐ |
| Parsing per file | ⚠️ Per documento | ✅ Per singolo file | BASSO | ⭐ |

### Gap Architetturali

#### 1. Separazione Responsabilità
**Problema**: Documento (anagrafica module) e DocumentJob (core platform) duplicano logiche.

**Soluzione Proposta**:
- **Core Platform**: Solo orchestrazione parsing (DocumentJob, parsing service)
- **Anagrafica Module**: Ownership completo documenti (Documento, DocumentoFile, metadata)
- **Flow**: DocumentJob → callback → aggiorna Documento.metadata_parsato → DocumentJob può essere archiviato

#### 2. Multi-Tenancy File Normalizzati
**Problema**: Cache file normalizzati deve rispettare isolamento tenant.

**Soluzione**:
```
storage/
└── {tenant_schema}/
    ├── temp_uploads/          # Upload temporanei
    ├── SOGGETTO_ANAGRAFICO/   # Documenti permanenti
    │   └── {entity_id}/
    │       ├── uuid_original.pdf        # File originale
    │       └── uuid_original_p1.jpg     # File normalizzato
    └── cache/                 # Cache varie (opzionale)
```

#### 3. Migration Strategy
**Problema**: Documenti esistenti hanno struttura old (single-file).

**Soluzione Migration**:
1. **Fase 1**: Dual-mode support
   - Documento ha `file_path` (old) + relationship `files` (new)
   - Se `files` empty → usa `file_path` (legacy)
   - Se `files` present → usa `files` (new)

2. **Fase 2**: Migration script
   ```python
   for doc in Documento.all():
       if doc.file_path and not doc.files:
           # Crea DocumentoFile da file singolo
           DocumentoFile.create(
               documento_id=doc.id,
               file_path=doc.file_path,
               nome_file=doc.nome_file,
               ordine=1,
               tipo_pagina="unico"
           )
   ```

3. **Fase 3**: Deprecate old fields
   - Remove `Documento.file_path`, `nome_file`, etc.

---

## Architettura Proposta

### 1. Data Model

#### Documento (Modificato)
```python
class Documento(Base):
    __tablename__ = "anag_documenti"

    id = Column(Integer, primary_key=True)
    entity_type = Column(String(50), nullable=False)
    entity_id = Column(Integer, nullable=False)
    tipo_documento_id = Column(Integer, ForeignKey("public.anag_tipi_documento.id"))

    descrizione = Column(String(500))
    note = Column(String(500))
    data_scadenza = Column(Date)

    # NUOVO: Metadata parsati aggregati
    metadata_parsato = Column(JSON, nullable=True, comment="Dati estratti da parsing")
    confidence_score = Column(Integer, nullable=True, comment="Score medio parsing (0-100)")

    # LEGACY (mantenuti per backward compatibility, poi deprecati)
    nome_file = Column(String(255), nullable=True)  # ⚠️ DEPRECATED
    file_path = Column(String(500), nullable=True)  # ⚠️ DEPRECATED
    mime_type = Column(String(100), nullable=True)  # ⚠️ DEPRECATED
    dimensione = Column(BigInteger, nullable=True)  # ⚠️ DEPRECATED

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    files = relationship("DocumentoFile", back_populates="documento", cascade="all, delete-orphan")
    tipo = relationship("TipoDocumento")
```

#### DocumentoFile (Nuovo)
```python
class DocumentoFile(Base):
    __tablename__ = "anag_documenti_files"

    id = Column(Integer, primary_key=True)
    documento_id = Column(Integer, ForeignKey("anag_documenti.id", ondelete="CASCADE"), nullable=False)

    file_path = Column(String(500), nullable=False, comment="Path file originale")
    nome_file = Column(String(255), nullable=False)
    mime_type = Column(String(100))
    dimensione = Column(BigInteger)

    ordine = Column(Integer, default=1, comment="Ordine visualizzazione")
    tipo_pagina = Column(String(50), comment="fronte, retro, pagina_1, etc.")

    # File normalizzato (cache)
    file_normalizzato_path = Column(String(500), comment="Path JPEG convertito")
    normalizzato_width = Column(Integer)
    normalizzato_height = Column(Integer)

    # Parsing job (optional)
    parsing_job_id = Column(Integer, ForeignKey("public.core_document_jobs.id"), nullable=True)
    parsing_result = Column(JSON, comment="Dati parsati da questo file specifico")
    confidence_score = Column(Integer, comment="Score parsing file (0-100)")

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    documento = relationship("Documento", back_populates="files")
    parsing_job = relationship("DocumentJob")
```

#### TipoDocumento (Esteso)
```python
class TipoDocumento(Base):
    # ... campi esistenti ...

    # NUOVO: Config parsing multi-file
    parsing_multi_file_config = Column(JSON, comment="Config parsing per tipo_pagina")

    # Esempio:
    # {
    #   "fronte": {
    #     "parsing_required": true,
    #     "service": "mrz",
    #     "config": {"format": "td1"}
    #   },
    #   "retro": {
    #     "parsing_required": false
    #   }
    # }
```

### 2. API Endpoints

#### Upload Multi-File
```python
POST /anagrafica/documenti/upload-multi
Content-Type: multipart/form-data

Form Data:
- entity_type: "SOGGETTO_ANAGRAFICO"
- entity_id: 45
- tipo_documento_id: 1  # CARTA_IDENTITA
- descrizione: "Carta identità rinnovata 2026"
- files[0]: fronte.jpg (tipo_pagina=fronte)
- files[1]: retro.jpg (tipo_pagina=retro)

Response:
{
  "documento": {
    "id": 123,
    "entity_type": "SOGGETTO_ANAGRAFICO",
    "entity_id": 45,
    "files": [
      {
        "id": 456,
        "nome_file": "fronte.jpg",
        "file_path": "tenant_test/SOGGETTO/45/uuid_fronte.jpg",
        "file_normalizzato_path": "tenant_test/SOGGETTO/45/uuid_fronte_norm.jpg",
        "ordine": 1,
        "tipo_pagina": "fronte",
        "parsing_job_uuid": "abc-123-def"
      },
      {
        "id": 457,
        "nome_file": "retro.jpg",
        "file_path": "tenant_test/SOGGETTO/45/uuid_retro.jpg",
        "file_normalizzato_path": "tenant_test/SOGGETTO/45/uuid_retro_norm.jpg",
        "ordine": 2,
        "tipo_pagina": "retro",
        "parsing_job_uuid": null  # No parsing per retro
      }
    ]
  },
  "parsing_jobs": [
    {
      "job_uuid": "abc-123-def",
      "file_id": 456,
      "status": "QUEUED"
    }
  ]
}
```

#### Find Similar Anagrafiche
```python
POST /anagrafica/soggetti/find-similar
{
  "codice_fiscale": "RSSMRA80A01H501Z",
  "nome": "Mario",
  "cognome": "Rossi",
  "data_nascita": "1980-01-01"
}

Response:
{
  "candidates": [
    {
      "soggetto_id": 45,
      "similarity_score": 1.0,
      "match_reason": "Codice fiscale identico",
      "match_fields": ["codice_fiscale"],
      "soggetto": {
        "id": 45,
        "nome": "Mario",
        "cognome": "Rossi",
        "codice_fiscale": "RSSMRA80A01H501Z",
        "email": "mario.rossi@example.com"
      }
    }
  ]
}
```

#### Update Anagrafica from Documento
```python
POST /anagrafica/soggetti/{id}/update-from-documento
{
  "documento_id": 123,
  "fields_to_update": ["telefono", "indirizzo", "cap", "citta"]
}

Response:
{
  "soggetto": { ... updated data ... },
  "updated_fields": ["telefono", "indirizzo", "cap", "citta"],
  "audit_log_id": 789
}
```

### 3. Frontend Components

#### DocumentViewer Component
```jsx
// frontend/src/components/Platform/Documents/DocumentViewer.jsx

import React, { useState, useEffect } from 'react';
import { ChevronLeft, ChevronRight, ZoomIn, ZoomOut, Download, RotateCw } from 'lucide-react';

const DocumentViewer = ({ documentoId, showMetadata = false }) => {
  const [documento, setDocumento] = useState(null);
  const [currentPage, setCurrentPage] = useState(0);
  const [zoom, setZoom] = useState(1.0);
  const [rotation, setRotation] = useState(0);

  useEffect(() => {
    // Load documento with files
    fetchDocumento(documentoId).then(setDocumento);
  }, [documentoId]);

  if (!documento) return <div>Caricamento...</div>;

  const currentFile = documento.files[currentPage];
  const imageUrl = `/api/v1/documenti/file/${currentFile.id}/view-normalized`;

  return (
    <div className="document-viewer">
      <div className="viewer-toolbar">
        <button onClick={() => setCurrentPage(p => Math.max(0, p - 1))} disabled={currentPage === 0}>
          <ChevronLeft />
        </button>
        <span>Pagina {currentPage + 1} di {documento.files.length}</span>
        <button onClick={() => setCurrentPage(p => Math.min(documento.files.length - 1, p + 1))} disabled={currentPage === documento.files.length - 1}>
          <ChevronRight />
        </button>

        <div className="divider" />

        <button onClick={() => setZoom(z => Math.min(3.0, z + 0.25))}>
          <ZoomIn />
        </button>
        <span>{Math.round(zoom * 100)}%</span>
        <button onClick={() => setZoom(z => Math.max(0.5, z - 0.25))}>
          <ZoomOut />
        </button>

        <button onClick={() => setRotation(r => (r + 90) % 360)}>
          <RotateCw />
        </button>

        <button onClick={() => downloadFile(currentFile.id)}>
          <Download /> Scarica Originale
        </button>
      </div>

      <div className="viewer-content">
        <img
          src={imageUrl}
          alt={currentFile.nome_file}
          style={{
            transform: `scale(${zoom}) rotate(${rotation}deg)`,
            transition: 'transform 0.2s'
          }}
        />

        {showMetadata && documento.metadata_parsato && (
          <div className="metadata-overlay">
            <h4>Dati Estratti</h4>
            <dl>
              {Object.entries(documento.metadata_parsato).map(([key, value]) => (
                <div key={key}>
                  <dt>{key}</dt>
                  <dd>{JSON.stringify(value)}</dd>
                </div>
              ))}
            </dl>
          </div>
        )}
      </div>

      <div className="viewer-thumbnails">
        {documento.files.map((file, idx) => (
          <div
            key={file.id}
            className={`thumbnail ${idx === currentPage ? 'active' : ''}`}
            onClick={() => setCurrentPage(idx)}
          >
            <img src={`/api/v1/documenti/file/${file.id}/thumbnail`} alt={file.tipo_pagina} />
            <span>{file.tipo_pagina}</span>
          </div>
        ))}
      </div>
    </div>
  );
};

export default DocumentViewer;
```

#### SimilarityMatchDialog Component
```jsx
// frontend/src/modules/anagrafica_italiana/components/Documenti/SimilarityMatchDialog.jsx

const SimilarityMatchDialog = ({ parsedData, onSelect, onCreateNew }) => {
  const [candidates, setCandidates] = useState([]);

  useEffect(() => {
    // Find similar anagrafiche
    api.post('/anagrafica/soggetti/find-similar', parsedData)
      .then(res => setCandidates(res.data.candidates));
  }, [parsedData]);

  return (
    <Dialog open={true}>
      <DialogTitle>Anagrafica Esistente Rilevata</DialogTitle>
      <DialogContent>
        <p>Abbiamo trovato {candidates.length} anagrafiche simili ai dati del documento.</p>

        {candidates.map(candidate => (
          <Card key={candidate.soggetto_id} className="similarity-card">
            <div className="similarity-score">
              <CircularProgress value={candidate.similarity_score * 100} />
              <span>{Math.round(candidate.similarity_score * 100)}% match</span>
            </div>

            <div className="candidate-info">
              <h4>{candidate.soggetto.nome} {candidate.soggetto.cognome}</h4>
              <p>CF: {candidate.soggetto.codice_fiscale}</p>
              <p className="match-reason">{candidate.match_reason}</p>
            </div>

            <Button onClick={() => onSelect(candidate.soggetto_id)}>
              Aggiungi Documento a Questa Anagrafica
            </Button>
          </Card>
        ))}

        <Button variant="outlined" onClick={onCreateNew}>
          No, Crea Nuova Anagrafica
        </Button>
      </DialogContent>
    </Dialog>
  );
};
```

### 4. File Normalization Service

```python
# backend/app/core/file_normalization.py

from PIL import Image
import pdf2image
from pathlib import Path
from typing import List, Tuple
import logging

logger = logging.getLogger(__name__)

class FileNormalizationService:
    """
    Service for normalizing document files to JPEG format.
    """

    TARGET_FORMAT = "JPEG"
    MAX_DIMENSION = 2048
    JPEG_QUALITY = 85

    def normalize_file(
        self,
        input_path: str,
        output_path: str,
        page_number: int = 1
    ) -> Tuple[str, int, int]:
        """
        Convert file to normalized JPEG.

        Args:
            input_path: Path to original file
            output_path: Path to save normalized file
            page_number: For multi-page PDFs (1-indexed)

        Returns:
            (normalized_path, width, height)
        """
        input_path = Path(input_path)
        output_path = Path(output_path)

        mime_type = self._detect_mime_type(input_path)

        if mime_type == "application/pdf":
            image = self._pdf_to_image(input_path, page_number)
        elif mime_type.startswith("image/"):
            image = Image.open(input_path)
        else:
            raise ValueError(f"Unsupported file type: {mime_type}")

        # Convert to RGB (JPEG doesn't support transparency)
        if image.mode in ("RGBA", "LA", "P"):
            background = Image.new("RGB", image.size, (255, 255, 255))
            if image.mode == "P":
                image = image.convert("RGBA")
            background.paste(image, mask=image.split()[-1] if image.mode in ("RGBA", "LA") else None)
            image = background
        elif image.mode != "RGB":
            image = image.convert("RGB")

        # Resize if too large
        image = self._resize_if_needed(image)

        # Save as JPEG
        output_path.parent.mkdir(parents=True, exist_ok=True)
        image.save(output_path, "JPEG", quality=self.JPEG_QUALITY, optimize=True)

        logger.info(f"Normalized {input_path.name} → {output_path.name} ({image.width}x{image.height})")

        return str(output_path), image.width, image.height

    def normalize_pdf_multi_page(
        self,
        input_path: str,
        output_dir: str,
        base_filename: str
    ) -> List[Tuple[str, int, int]]:
        """
        Convert multi-page PDF to multiple JPEGs.

        Args:
            input_path: Path to PDF
            output_dir: Directory to save JPEGs
            base_filename: Base name (will add _p1, _p2, etc.)

        Returns:
            List of (normalized_path, width, height) for each page
        """
        input_path = Path(input_path)
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Convert PDF to images (all pages)
        images = pdf2image.convert_from_path(input_path, dpi=200)

        results = []
        for idx, image in enumerate(images, start=1):
            output_path = output_dir / f"{base_filename}_p{idx}.jpg"

            # Process image (same logic as normalize_file)
            if image.mode != "RGB":
                image = image.convert("RGB")
            image = self._resize_if_needed(image)

            image.save(output_path, "JPEG", quality=self.JPEG_QUALITY, optimize=True)
            results.append((str(output_path), image.width, image.height))

            logger.info(f"Normalized PDF page {idx}/{len(images)} → {output_path.name}")

        return results

    def _detect_mime_type(self, file_path: Path) -> str:
        import mimetypes
        mime_type, _ = mimetypes.guess_type(str(file_path))
        return mime_type or "application/octet-stream"

    def _pdf_to_image(self, pdf_path: Path, page_number: int) -> Image:
        """Convert single PDF page to PIL Image"""
        images = pdf2image.convert_from_path(pdf_path, first_page=page_number, last_page=page_number, dpi=200)
        return images[0]

    def _resize_if_needed(self, image: Image) -> Image:
        """Resize image if larger than MAX_DIMENSION"""
        width, height = image.size

        if width <= self.MAX_DIMENSION and height <= self.MAX_DIMENSION:
            return image

        # Calculate new size maintaining aspect ratio
        if width > height:
            new_width = self.MAX_DIMENSION
            new_height = int(height * (self.MAX_DIMENSION / width))
        else:
            new_height = self.MAX_DIMENSION
            new_width = int(width * (self.MAX_DIMENSION / height))

        return image.resize((new_width, new_height), Image.Resampling.LANCZOS)


# Global instance
file_normalization = FileNormalizationService()
```

---

## Piano di Implementazione

### Fase 1: Foundation (2-3 settimane) ⭐⭐⭐

**Obiettivo**: Creare struttura base multi-file senza breaking changes.

#### Tasks:
1. **Backend - Data Model**
   - [ ] Creare migration `DocumentoFile` table
   - [ ] Aggiungere campi a `Documento`: `metadata_parsato`, `confidence_score`
   - [ ] Aggiungere relationship `Documento.files`
   - [ ] Mantenere campi legacy per backward compatibility

2. **Backend - File Normalization**
   - [ ] Implementare `FileNormalizationService`
   - [ ] Installare dependencies: `Pillow`, `pdf2image`, `poppler-utils`
   - [ ] Test conversione PDF → JPEG
   - [ ] Test conversione PNG/HEIC → JPEG

3. **Backend - Upload Multi-File**
   - [ ] Nuovo endpoint `POST /anagrafica/documenti/upload-multi`
   - [ ] Logica creazione `Documento` + N `DocumentoFile`
   - [ ] Normalizzazione file on-upload
   - [ ] Test upload multi-file

4. **Backend - DocumentJob Callback Enhancement**
   - [ ] Modificare callback per aggiornare `Documento.metadata_parsato`
   - [ ] Merge multi-file parsing results
   - [ ] Test callback con multi-file

**Deliverables**:
- ✅ Database schema aggiornato
- ✅ Upload multi-file funzionante
- ✅ File normalizzati salvati
- ✅ Metadata parsati in Documento

**Testing**:
```bash
# Upload multi-file
curl -X POST /api/v1/anagrafica/documenti/upload-multi \
  -F "entity_type=SOGGETTO_ANAGRAFICO" \
  -F "entity_id=45" \
  -F "tipo_documento_id=1" \
  -F "files[0]=@fronte.jpg" \
  -F "files[1]=@retro.jpg"

# Verify normalization
ls storage/tenant_test/SOGGETTO/45/
# Should show: uuid_fronte.jpg, uuid_fronte_norm.jpg, uuid_retro.jpg, uuid_retro_norm.jpg
```

---

### Fase 2: Similarity Matching (2 settimane) ⭐⭐⭐

**Obiettivo**: Algoritmo merge anagrafiche e workflow creazione intelligente.

#### Tasks:
1. **Backend - Similarity Algorithm**
   - [ ] Implementare `SimilarityMatchingService`
   - [ ] Algoritmi:
     - Codice Fiscale exact match
     - Levenshtein distance per nome/cognome
     - Data nascita comparison
   - [ ] Test con dataset anagrafiche

2. **Backend - Find Similar API**
   - [ ] Endpoint `POST /anagrafica/soggetti/find-similar`
   - [ ] Query optimization (indexes su CF, nome, cognome)
   - [ ] Cache results (Redis optional)

3. **Frontend - SimilarityMatchDialog**
   - [ ] Componente dialog con candidates
   - [ ] Visualizzazione similarity score
   - [ ] Azioni: "Aggiungi a Esistente" / "Crea Nuovo"

4. **Integration - Workflow Creazione Anagrafica**
   - [ ] Modificare `POST /anagrafica/from-document/complete`
   - [ ] Step 1: Find similar
   - [ ] Step 2: User choice
   - [ ] Step 3: Create or link

**Deliverables**:
- ✅ Algoritmo similarity matching
- ✅ API find-similar
- ✅ UI similarity dialog
- ✅ Workflow creazione con merge

**Testing**:
```python
# Test similarity algorithm
from services.similarity_matching import calculate_similarity

parsed_data = {
    "codice_fiscale": "RSSMRA80A01H501Z",
    "nome": "Mario",
    "cognome": "Rossi"
}

existing = SoggettoAnagrafico(
    codice_fiscale="RSSMRA80A01H501Z",
    nome="Mario",
    cognome="Rossi"
)

score = calculate_similarity(parsed_data, existing)
assert score == 1.0  # Perfect match
```

---

### Fase 3: Document Viewer (1-2 settimane) ⭐⭐

**Obiettivo**: Componente visualizzazione standard con multi-page support.

#### Tasks:
1. **Frontend - DocumentViewer Component**
   - [ ] Implementare componente base
   - [ ] Features:
     - Navigation tra pagine
     - Zoom in/out
     - Rotate
     - Download originale
     - Thumbnails sidebar
   - [ ] CSS styling

2. **Backend - View Endpoints**
   - [ ] `GET /documenti/file/{id}/view-normalized` → restituisce JPEG normalizzato
   - [ ] `GET /documenti/file/{id}/thumbnail` → restituisce thumbnail (320px)
   - [ ] `GET /documenti/file/{id}/download-original` → restituisce file originale

3. **Integration**
   - [ ] Usare DocumentViewer in:
     - SoggettoDetail page
     - ConsumeDocumentPage (anagrafica from doc)
     - DocumentoList

**Deliverables**:
- ✅ DocumentViewer component
- ✅ API view/download file
- ✅ Integration in key pages

**Testing**:
```jsx
// Test component
<DocumentViewer documentoId={123} showMetadata={true} />

// Should render:
// - Image viewer with current page
// - Navigation buttons
// - Zoom/rotate controls
// - Thumbnails sidebar
// - Metadata overlay (if showMetadata=true)
```

---

### Fase 4: Update from Document (1 settimana) ⭐⭐

**Obiettivo**: Workflow aggiornamento anagrafica da documento parsato.

#### Tasks:
1. **Backend - Diff Service**
   - [ ] Implementare `DocumentDiffService`
   - [ ] Compare `SoggettoAnagrafico` vs `Documento.metadata_parsato`
   - [ ] Restituire diff strutturato

2. **Backend - Update API**
   - [ ] Endpoint `POST /anagrafica/soggetti/{id}/update-from-documento`
   - [ ] Validazione campi selezionati
   - [ ] Audit log aggiornamenti

3. **Frontend - DiffView Component**
   - [ ] Componente tabella diff side-by-side
   - [ ] Checkbox per selezionare campi da aggiornare
   - [ ] Button "Aggiorna Selezionati"

**Deliverables**:
- ✅ API diff + update
- ✅ UI diff view
- ✅ Audit trail modifiche

---

### Fase 5: Incongruenze Detection (1 settimana) ⭐

**Obiettivo**: Validazione e warning su incongruenze dati.

#### Tasks:
1. **Backend - Validation Service**
   - [ ] `DocumentValidationService`
   - [ ] Rules:
     - CF mismatch → HIGH severity
     - Nome/Cognome differenza > 30% → MEDIUM severity
     - Data nascita differenza → HIGH severity

2. **Backend - Upload Validation**
   - [ ] Integrare validation in upload documento
   - [ ] Restituire warnings in response

3. **Frontend - Warning Dialog**
   - [ ] Mostrare warnings prima del salvataggio
   - [ ] Opzioni:
     - Ignora e salva
     - Aggiorna anagrafica
     - Crea nuova anagrafica

**Deliverables**:
- ✅ Validation service
- ✅ Warnings in upload response
- ✅ UI warning dialog

---

### Fase 6: Migration & Cleanup (1 settimana)

**Obiettivo**: Migrare documenti esistenti e deprecare old fields.

#### Tasks:
1. **Data Migration Script**
   - [ ] Script per migrare documenti single-file a multi-file
   - [ ] Creare `DocumentoFile` da `Documento.file_path`
   - [ ] Normalizzare file esistenti
   - [ ] Backup database prima della migration

2. **Deprecation**
   - [ ] Rimuovere campi legacy da `Documento` (opzionale)
   - [ ] Update API docs

3. **Testing & QA**
   - [ ] Test end-to-end tutti i workflow
   - [ ] Performance testing (upload, normalization, viewing)
   - [ ] User acceptance testing

**Deliverables**:
- ✅ Dati migrati
- ✅ Sistema completamente su new architecture
- ✅ Documentazione aggiornata

---

## Impatto e Rischi

### Impatto Positivo

| Area | Beneficio | Valore |
|------|-----------|--------|
| **UX** | Workflow creazione anagrafica più fluido | ⭐⭐⭐⭐⭐ |
| **Efficienza** | Riduzione duplicati anagrafiche | ⭐⭐⭐⭐ |
| **Qualità Dati** | Aggiornamento automatico da documenti | ⭐⭐⭐⭐ |
| **Scalabilità** | Supporto documenti multi-page | ⭐⭐⭐⭐⭐ |
| **Manutenibilità** | Visualizzazione standardizzata | ⭐⭐⭐⭐ |

### Rischi e Mitigazioni

#### RISCHIO 1: Performance Conversione File ⚠️
**Descrizione**: Conversione PDF/immagini può essere lenta (2-5 sec per file).

**Impatto**: Timeout upload, user experience negativa.

**Probabilità**: MEDIA

**Mitigazione**:
- ✅ Conversione asincrona (background job)
- ✅ Progress indicator in frontend
- ✅ Queue system (Celery/Redis) per gestire picchi
- ✅ Limite max file size (10MB per file)

#### RISCHIO 2: Storage Explosion 💾
**Descrizione**: File normalizzati raddoppiano storage (originale + JPEG).

**Impatto**: Costi storage aumentati.

**Probabilità**: ALTA

**Mitigazione**:
- ✅ Compressione JPEG quality 85% (buon compromesso)
- ✅ Resize max 2048px (riduce dimensioni)
- ✅ Policy retention file normalizzati (eliminare dopo N giorni se non usati)
- ✅ Opzione: eliminare originale dopo conversione (se accettabile)

**Stima Storage**:
```
Documento tipico (CI fronte+retro):
- Originale JPG (fronte): 3MB
- Originale JPG (retro): 2.5MB
- Normalizzato fronte: 800KB (2048px, quality 85%)
- Normalizzato retro: 700KB
Total: 7MB (vs 5.5MB senza normalizzazione) → +27%
```

#### RISCHIO 3: Similarity Algorithm False Positives 🎯
**Descrizione**: Algoritmo può suggerire match sbagliati (es: omonimi).

**Impatto**: User confusione, possibile merge errato.

**Probabilità**: MEDIA

**Mitigazione**:
- ✅ Threshold conservativo (suggerire solo match > 80%)
- ✅ Mostrare dettagli match (perché suggerito)
- ✅ Always allow "Crea Nuovo" option
- ✅ Log tutte le scelte user per analisi

#### RISCHIO 4: Migration Failures 💥
**Descrizione**: Migration script può fallire su dati corrupted/inconsistenti.

**Impatto**: Downtime, dati persi.

**Probabilità**: BASSA

**Mitigazione**:
- ✅ Backup completo database prima migration
- ✅ Dry-run migration su copia database
- ✅ Rollback plan documentato
- ✅ Migration idempotente (può essere rieseguita)
- ✅ Dual-mode support (vecchio + nuovo model coesistono)

#### RISCHIO 5: Dependency on External Parsing Services 🌐
**Descrizione**: Servizi parsing esterni possono essere down/lenti.

**Impatto**: Workflow bloccato.

**Probabilità**: MEDIA

**Mitigazione**:
- ✅ Retry logic (max 3 tentativi)
- ✅ Timeout configurabile
- ✅ Fallback: permettere upload senza parsing
- ✅ Monitoring + alerting su parsing failures

---

## Metriche di Successo

### KPI Tecnici
- ✅ **Upload Success Rate** > 99%
- ✅ **Conversione File Success Rate** > 98%
- ✅ **Parsing Success Rate** > 90% (servizi esterni)
- ✅ **API Response Time** < 500ms (escluso parsing asincrono)
- ✅ **Storage Growth** < +30% rispetto a baseline

### KPI Funzionali
- ✅ **Riduzione Duplicati Anagrafiche** > 40%
- ✅ **User Adoption Upload Multi-File** > 70% (vs single-file)
- ✅ **Similarity Match Accuracy** > 85% (user conferma match suggerito)
- ✅ **Time to Complete Anagrafica from Document** < 2 min (vs 5 min baseline)

---

## Conclusioni

### Raccomandazioni

1. **Priorità Implementazione**:
   - **FASE 1** (Foundation) è CRITICA → iniziare subito
   - **FASE 2** (Similarity) è HIGH VALUE → pianificare per dopo Fase 1
   - **FASE 3-5** possono essere parallelizzate se risorse disponibili

2. **Quick Wins**:
   - File normalization ha alto impatto con moderata complessità
   - DocumentViewer component riutilizzabile in tutti i moduli

3. **Technical Debt**:
   - Mantenere dual-mode (old + new) solo temporaneamente
   - Migration completa entro 3 mesi dall'inizio Fase 1

4. **Team & Skills Required**:
   - **Backend**: 1 senior dev (Python, SQLAlchemy, image processing)
   - **Frontend**: 1 mid-level dev (React, component design)
   - **DevOps**: Support per Redis/queue setup (se necessario)
   - **QA**: Test end-to-end workflow complessi

### Next Steps

1. **Review Documento con Stakeholders**
   - Product Owner approval requisiti
   - Technical Lead approval architettura
   - DevOps review infrastructure needs

2. **Refinement Meeting**
   - Dettagliare task Fase 1
   - Stimare effort (story points)
   - Identificare blockers

3. **Kick-off Fase 1**
   - Setup development environment
   - Create feature branch
   - Start implementation

---

**Document Version**: 1.0
**Last Updated**: 2026-01-31
**Author**: Claude Code Analysis
**Status**: DRAFT - Pending Review
