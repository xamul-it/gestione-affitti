# Diagrammi Architettura Sistema Documenti

## 1. Architettura Attuale vs Proposta

```
┌─────────────────────────────────────────────────────────────────────┐
│                          ARCHITETTURA ATTUALE                       │
└─────────────────────────────────────────────────────────────────────┘

┌──────────────────────┐
│   Frontend Upload    │
│  (Single File)       │
└──────────┬───────────┘
           │
           v
┌──────────────────────────────────────────────────────────────────┐
│                        Backend API                                │
│  POST /documenti/upload                                          │
│  - entity_type, entity_id, tipo_documento                        │
│  - file (single)                                                 │
└──────────┬───────────────────────────────────────────────────────┘
           │
           v
┌──────────────────────────────────────────────────────────────────┐
│                     File Storage                                  │
│  storage/{tenant}/{entity_type}/{entity_id}/                     │
│    └─ {uuid}_{filename}  (formato originale)                    │
└──────────┬───────────────────────────────────────────────────────┘
           │
           v
┌──────────────────────────────────────────────────────────────────┐
│                  Database (Documento)                             │
│  ┌────────────────────────────────────────────┐                  │
│  │ Documento                                  │                  │
│  ├────────────────────────────────────────────┤                  │
│  │ id: int                                    │                  │
│  │ entity_type: str                           │                  │
│  │ entity_id: int                             │                  │
│  │ tipo_documento: TipoDocumentoEnum          │                  │
│  │ nome_file: str          ⚠️ SINGLE FILE     │                  │
│  │ file_path: str          ⚠️ SINGLE PATH     │                  │
│  │ mime_type: str                             │                  │
│  │ dimensione: int                            │                  │
│  │ data_scadenza: Date                        │                  │
│  └────────────────────────────────────────────┘                  │
└──────────────────────────────────────────────────────────────────┘
           │
           v (optional parsing)
┌──────────────────────────────────────────────────────────────────┐
│                  DocumentJob (Core Platform)                      │
│  ┌────────────────────────────────────────────┐                  │
│  │ DocumentJob                                │                  │
│  ├────────────────────────────────────────────┤                  │
│  │ job_uuid: str                              │                  │
│  │ file_path: str                             │                  │
│  │ document_type_key: str                     │                  │
│  │ parsing_service: str                       │                  │
│  │ parsing_result: JSON   ⚠️ DATI SEPARATI    │                  │
│  │ status: JobStatus                          │                  │
│  └────────────────────────────────────────────┘                  │
└──────────────────────────────────────────────────────────────────┘

PROBLEMI:
❌ No multi-file support (fronte/retro separati)
❌ Dati parsati separati da Documento
❌ No normalizzazione formato
❌ No merge/deduplication logic


┌─────────────────────────────────────────────────────────────────────┐
│                        ARCHITETTURA PROPOSTA                        │
└─────────────────────────────────────────────────────────────────────┘

┌──────────────────────┐
│   Frontend Upload    │
│  (Multi-File)        │
│  - fronte.jpg        │
│  - retro.jpg         │
└──────────┬───────────┘
           │
           v
┌──────────────────────────────────────────────────────────────────┐
│                        Backend API                                │
│  POST /documenti/upload-multi                                    │
│  - entity_type, entity_id, tipo_documento_id                     │
│  - files[] (array)                                               │
└──────────┬───────────────────────────────────────────────────────┘
           │
           v
┌──────────────────────────────────────────────────────────────────┐
│              File Normalization Service                           │
│  ┌─────────────────────────────────────────────────────┐         │
│  │ Input: PDF, PNG, HEIC, JPG, etc.                    │         │
│  │ Output: JPEG (2048px max, quality 85%)              │         │
│  │ ├─ original.pdf → page_1.jpg, page_2.jpg           │         │
│  │ ├─ image.png → image_normalized.jpg                │         │
│  │ └─ photo.heic → photo_normalized.jpg               │         │
│  └─────────────────────────────────────────────────────┘         │
└──────────┬───────────────────────────────────────────────────────┘
           │
           v
┌──────────────────────────────────────────────────────────────────┐
│                     File Storage                                  │
│  storage/{tenant}/{entity_type}/{entity_id}/                     │
│    ├─ {uuid}_fronte.jpg           (originale)                   │
│    ├─ {uuid}_fronte_norm.jpg      (normalizzato) ✅             │
│    ├─ {uuid}_retro.jpg            (originale)                   │
│    └─ {uuid}_retro_norm.jpg       (normalizzato) ✅             │
└──────────┬───────────────────────────────────────────────────────┘
           │
           v
┌──────────────────────────────────────────────────────────────────┐
│                  Database (Documento + Files)                     │
│  ┌────────────────────────────────────────────┐                  │
│  │ Documento                                  │                  │
│  ├────────────────────────────────────────────┤                  │
│  │ id: int                                    │                  │
│  │ entity_type: str                           │                  │
│  │ entity_id: int                             │                  │
│  │ tipo_documento_id: int → TipoDocumento     │                  │
│  │ descrizione: str                           │                  │
│  │ data_scadenza: Date                        │                  │
│  │ metadata_parsato: JSON     ✅ NUOVO        │                  │
│  │ confidence_score: int      ✅ NUOVO        │                  │
│  │ created_at: DateTime                       │                  │
│  └────────────────┬───────────────────────────┘                  │
│                   │ 1:N                                           │
│                   v                                               │
│  ┌────────────────────────────────────────────┐                  │
│  │ DocumentoFile                ✅ NUOVO      │                  │
│  ├────────────────────────────────────────────┤                  │
│  │ id: int                                    │                  │
│  │ documento_id: int → Documento              │                  │
│  │ file_path: str                             │                  │
│  │ nome_file: str                             │                  │
│  │ mime_type: str                             │                  │
│  │ dimensione: int                            │                  │
│  │ ordine: int                                │                  │
│  │ tipo_pagina: str (fronte/retro/pagina_N)  │                  │
│  │ file_normalizzato_path: str  ✅           │                  │
│  │ normalizzato_width: int                    │                  │
│  │ normalizzato_height: int                   │                  │
│  │ parsing_job_id: int → DocumentJob          │                  │
│  │ parsing_result: JSON                       │                  │
│  │ confidence_score: int                      │                  │
│  └────────────────────────────────────────────┘                  │
└──────────────────────────────────────────────────────────────────┘
           │
           v (per ogni file)
┌──────────────────────────────────────────────────────────────────┐
│                  DocumentJob (Parsing Async)                      │
│  1 job per DocumentoFile se parsing_required                     │
│  Callback → aggiorna DocumentoFile.parsing_result                │
│  Merge all files → Documento.metadata_parsato                    │
└──────────────────────────────────────────────────────────────────┘

VANTAGGI:
✅ Multi-file support nativo
✅ Dati parsati salvati in Documento
✅ File normalizzati per viewing/parsing
✅ Flessibilità per file (parsing optional per file)
```

---

## 2. Workflow Upload Multi-File

```
┌──────────────┐
│   Frontend   │
│              │
│ User selects:│
│ - fronte.jpg │
│ - retro.jpg  │
└──────┬───────┘
       │
       │ POST /documenti/upload-multi
       │ FormData:
       │   entity_type: "SOGGETTO_ANAGRAFICO"
       │   entity_id: 45
       │   tipo_documento_id: 1 (CARTA_IDENTITA)
       │   files[0]: fronte.jpg
       │   files[1]: retro.jpg
       v
┌───────────────────────────────────────────────┐
│              Backend API                      │
│  1. Validate files                            │
│  2. Create Documento record                   │
│  3. For each file:                            │
│     a. Save original                          │
│     b. Normalize to JPEG                      │
│     c. Create DocumentoFile record            │
│     d. If parsing_required:                   │
│        - Create DocumentJob                   │
│        - Submit to parsing service            │
│  4. Return response                           │
└───────────────┬───────────────────────────────┘
                │
                v
┌───────────────────────────────────────────────┐
│            File Storage                       │
│                                               │
│  storage/tenant_test/SOGGETTO/45/             │
│    ├─ abc123_fronte.jpg                       │
│    ├─ abc123_fronte_norm.jpg  ← normalized    │
│    ├─ def456_retro.jpg                        │
│    └─ def456_retro_norm.jpg   ← normalized    │
└───────────────┬───────────────────────────────┘
                │
                v
┌───────────────────────────────────────────────┐
│              Database                         │
│                                               │
│  Documento #123                               │
│  ├─ entity_type: "SOGGETTO_ANAGRAFICO"        │
│  ├─ entity_id: 45                             │
│  ├─ tipo_documento_id: 1                      │
│  ├─ metadata_parsato: null (pending)          │
│  └─ files:                                    │
│      ├─ DocumentoFile #456                    │
│      │   ├─ file_path: "...abc123_fronte.jpg" │
│      │   ├─ file_normalizzato_path: "..._norm"│
│      │   ├─ ordine: 1                         │
│      │   ├─ tipo_pagina: "fronte"             │
│      │   └─ parsing_job_id: job-uuid-1        │
│      │                                         │
│      └─ DocumentoFile #457                    │
│          ├─ file_path: "...def456_retro.jpg"  │
│          ├─ file_normalizzato_path: "..._norm"│
│          ├─ ordine: 2                         │
│          ├─ tipo_pagina: "retro"              │
│          └─ parsing_job_id: null (no parsing) │
└───────────────┬───────────────────────────────┘
                │
                v
┌───────────────────────────────────────────────┐
│         Parsing Service (Async)               │
│                                               │
│  DocumentJob job-uuid-1                       │
│  ├─ file_path: abc123_fronte_norm.jpg         │
│  ├─ status: QUEUED                            │
│  └─ Submit to MRZ service                     │
│                                               │
│  ... MRZ processes ...                        │
│                                               │
│  Callback received:                           │
│  {                                            │
│    "job_id": "job-uuid-1",                    │
│    "status": "finished",                      │
│    "result": {                                │
│      "codice_fiscale": "RSSMRA80A01H501Z",    │
│      "nome": "MARIO",                         │
│      "cognome": "ROSSI",                      │
│      ...                                      │
│    }                                          │
│  }                                            │
│                                               │
│  1. Update DocumentJob.parsing_result         │
│  2. Update DocumentoFile #456.parsing_result  │
│  3. Merge all files results →                 │
│     Documento #123.metadata_parsato           │
│  4. Create Scadenza notification              │
└───────────────────────────────────────────────┘
```

---

## 3. Workflow "Crea Anagrafica da Documento" con Similarity Matching

```
┌──────────────┐
│   Frontend   │
│              │
│ User uploads │
│ identity doc │
│ (NO anagrafica│
│  selected)   │
└──────┬───────┘
       │
       │ POST /anagrafica/from-document/upload-identity-document
       │ FormData:
       │   document_type: "CARTA_IDENTITA"
       │   file: fronte.jpg
       v
┌───────────────────────────────────────────────┐
│         DocumentParsingService                │
│  1. Save to temp storage                      │
│  2. Create DocumentJob (entity_id = NULL)     │
│  3. Submit to MRZ service                     │
└───────────────┬───────────────────────────────┘
                │
                v
┌───────────────────────────────────────────────┐
│         MRZ Service (External)                │
│  Process document...                          │
│  Extract data...                              │
│  Send callback                                │
└───────────────┬───────────────────────────────┘
                │
                v
┌───────────────────────────────────────────────┐
│         Callback Handler                      │
│  1. Update DocumentJob.parsing_result:        │
│     {                                         │
│       "codice_fiscale": "RSSMRA80A01H501Z",   │
│       "nome": "MARIO",                        │
│       "cognome": "ROSSI",                     │
│       "data_nascita": "1980-01-01",           │
│       ...                                     │
│     }                                         │
│  2. status = COMPLETED                        │
│  3. Create Scadenza notification              │
└───────────────┬───────────────────────────────┘
                │
                v
┌───────────────────────────────────────────────┐
│         User Notification                     │
│  "Documento elaborato! Rivedi i dati"         │
└───────────────┬───────────────────────────────┘
                │
                v
┌───────────────────────────────────────────────┐
│         Frontend                              │
│  User clicks notification                     │
│  → Opens review page                          │
│                                               │
│  Shows parsed data:                           │
│  ┌─────────────────────────────────────────┐  │
│  │ Nome:     MARIO                         │  │
│  │ Cognome:  ROSSI                         │  │
│  │ CF:       RSSMRA80A01H501Z              │  │
│  │ ...                                     │  │
│  └─────────────────────────────────────────┘  │
│                                               │
│  User clicks "Crea Anagrafica"                │
└───────────────┬───────────────────────────────┘
                │
                │ POST /anagrafica/find-similar
                │ { codice_fiscale: "RSSMRA80A01H501Z", ... }
                v
┌───────────────────────────────────────────────┐
│       SimilarityMatchingService   ✅ NEW      │
│                                               │
│  Algorithm:                                   │
│  1. Search by CF (exact match) → 100% score   │
│  2. Search by nome+cognome (fuzzy) → 50-99%   │
│  3. Rank by similarity score                  │
│                                               │
│  Results:                                     │
│  [                                            │
│    {                                          │
│      soggetto_id: 45,                         │
│      similarity_score: 1.0,                   │
│      match_reason: "CF identico",             │
│      soggetto: { ... }                        │
│    }                                          │
│  ]                                            │
└───────────────┬───────────────────────────────┘
                │
                v
┌───────────────────────────────────────────────┐
│         Frontend - Similarity Dialog          │
│  ┌─────────────────────────────────────────┐  │
│  │ Anagrafica esistente trovata!          │  │
│  │                                         │  │
│  │ Mario Rossi (CF: RSSMRA80A01H501Z)     │  │
│  │ Similarity: 100%                       │  │
│  │ Email: mario.rossi@example.com         │  │
│  │                                         │  │
│  │ [Aggiungi Documento a Questa Anagrafica]│  │
│  │ [No, Crea Nuova Anagrafica]            │  │
│  └─────────────────────────────────────────┘  │
└───────────────┬───────────────────────────────┘
                │
       ┌────────┴────────┐
       │                 │
       v                 v
   [Aggiungi]        [Crea Nuovo]
       │                 │
       │                 │ POST /anagrafica/from-document/complete
       │                 │ { job_uuid, ..., create_new: true }
       │                 │
       │                 v
       │           ┌───────────────────────┐
       │           │ Create new            │
       │           │ SoggettoAnagrafico    │
       │           └───────────────────────┘
       │
       │ POST /anagrafica/soggetti/{id}/add-documento-from-job
       │ { job_uuid, soggetto_id: 45 }
       │
       v
┌───────────────────────────────────────────────┐
│         Link Documento to Anagrafica          │
│  1. Move file from temp to permanent          │
│  2. Create Documento record                   │
│  3. Update DocumentJob.entity_id = 45         │
│  4. Complete Scadenza                         │
│  5. DONE!                                     │
└───────────────────────────────────────────────┘
```

---

## 4. Database Schema ER Diagram

```
┌──────────────────────────────────────────────────────────────────┐
│                      PUBLIC SCHEMA                               │
└──────────────────────────────────────────────────────────────────┘

┌─────────────────────────┐
│ TipoDocumento           │
├─────────────────────────┤
│ id (PK)                 │
│ codice                  │  "CARTA_IDENTITA"
│ nome                    │  "Carta d'Identità"
│ categoria               │  "identita"
│ richiede_scadenza       │  true
│ parsing_service         │  "mrz"
│ parsing_config          │  JSON
│ parsing_callback_url    │
│ parsing_multi_file_cfg  │  JSON ✅ NEW
└─────────────────────────┘
           │
           │ 1:N
           v
┌─────────────────────────┐
│ DocumentJob             │  (core platform)
├─────────────────────────┤
│ id (PK)                 │
│ job_uuid                │
│ tenant_schema           │
│ file_path               │
│ document_type_key       │
│ parsing_service         │
│ parsing_config          │
│ entity_type             │  nullable
│ entity_id               │  nullable
│ status                  │  PENDING/QUEUED/COMPLETED/FAILED
│ parsing_result          │  JSON
│ confidence_score        │
│ scadenza_id             │  → Scadenza
└─────────────────────────┘


┌──────────────────────────────────────────────────────────────────┐
│                    TENANT SCHEMA (e.g. tenant_test)              │
└──────────────────────────────────────────────────────────────────┘

┌─────────────────────────┐
│ SoggettoAnagrafico      │
├─────────────────────────┤
│ id (PK)                 │
│ tipo_soggetto           │
│ nome                    │
│ cognome                 │
│ codice_fiscale          │  UNIQUE
│ data_nascita            │
│ email                   │
│ telefono                │
│ ...                     │
└─────────────────────────┘
           │
           │ 1:N (polymorphic via entity_type/entity_id)
           v
┌─────────────────────────┐
│ Documento               │  ✅ MODIFIED
├─────────────────────────┤
│ id (PK)                 │
│ entity_type             │  "SOGGETTO_ANAGRAFICO"
│ entity_id               │  → SoggettoAnagrafico.id
│ tipo_documento_id       │  → public.TipoDocumento
│ descrizione             │
│ note                    │
│ data_scadenza           │
│ metadata_parsato        │  JSON ✅ NEW (merged from all files)
│ confidence_score        │  int ✅ NEW (average of all files)
│ created_at              │
│ updated_at              │
│ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─│
│ nome_file               │  ⚠️ DEPRECATED (legacy)
│ file_path               │  ⚠️ DEPRECATED (legacy)
│ mime_type               │  ⚠️ DEPRECATED (legacy)
│ dimensione              │  ⚠️ DEPRECATED (legacy)
└─────────────────────────┘
           │
           │ 1:N
           v
┌─────────────────────────┐
│ DocumentoFile           │  ✅ NEW
├─────────────────────────┤
│ id (PK)                 │
│ documento_id (FK)       │  → Documento.id
│ file_path               │  "tenant_test/SOGGETTO/45/uuid_fronte.jpg"
│ nome_file               │  "fronte.jpg"
│ mime_type               │  "image/jpeg"
│ dimensione              │  1234567
│ ordine                  │  1 (display order)
│ tipo_pagina             │  "fronte" | "retro" | "pagina_1" | ...
│ file_normalizzato_path  │  "tenant_test/.../uuid_fronte_norm.jpg"
│ normalizzato_width      │  2048
│ normalizzato_height     │  1536
│ parsing_job_id (FK)     │  → public.DocumentJob.id (nullable)
│ parsing_result          │  JSON (parsed data from THIS file)
│ confidence_score        │  95 (for this file)
│ created_at              │
└─────────────────────────┘


Example Data:
─────────────
Documento #123 (Carta Identità Mario Rossi)
├─ entity_type: "SOGGETTO_ANAGRAFICO"
├─ entity_id: 45
├─ tipo_documento_id: 1
├─ metadata_parsato: {
│    "codice_fiscale": "RSSMRA80A01H501Z",
│    "nome": "MARIO",
│    "cognome": "ROSSI",
│    "data_nascita": "1980-01-01",
│    "data_emissione": "2020-01-15",
│    "data_scadenza": "2030-01-15",
│    "numero_documento": "CA12345AB"
│  }
├─ confidence_score: 95 (average of files)
│
└─ files:
    ├─ DocumentoFile #456 (fronte)
    │   ├─ file_path: "tenant_test/SOGGETTO/45/abc123_fronte.jpg"
    │   ├─ file_normalizzato_path: "tenant_test/.../abc123_fronte_norm.jpg"
    │   ├─ ordine: 1
    │   ├─ tipo_pagina: "fronte"
    │   ├─ parsing_job_id: job-uuid-1
    │   ├─ parsing_result: { "codice_fiscale": "...", nome: "...", ... }
    │   └─ confidence_score: 95
    │
    └─ DocumentoFile #457 (retro)
        ├─ file_path: "tenant_test/SOGGETTO/45/def456_retro.jpg"
        ├─ file_normalizzato_path: "tenant_test/.../def456_retro_norm.jpg"
        ├─ ordine: 2
        ├─ tipo_pagina: "retro"
        ├─ parsing_job_id: null (no parsing configured for retro)
        └─ parsing_result: null
```

---

## 5. File Storage Directory Structure

```
storage/
│
├── tenant_test/                          # Tenant schema isolation
│   │
│   ├── temp_uploads/                     # Temporary upload staging
│   │   └── {job_uuid}/                   # Job-specific temp folder
│   │       ├── original_file.jpg
│   │       └── normalized_file.jpg       # Converted for parsing
│   │
│   ├── SOGGETTO_ANAGRAFICO/              # Entity type
│   │   └── {entity_id}/                  # Entity ID (e.g., 45)
│   │       ├── {uuid}_fronte.jpg         # Original file
│   │       ├── {uuid}_fronte_norm.jpg    # Normalized (JPEG, 2048px)
│   │       ├── {uuid}_retro.jpg
│   │       └── {uuid}_retro_norm.jpg
│   │
│   ├── IMMOBILE/
│   │   └── {entity_id}/
│   │       ├── {uuid}_planimetria.pdf
│   │       ├── {uuid}_planimetria_p1.jpg  # PDF page 1 normalized
│   │       ├── {uuid}_planimetria_p2.jpg  # PDF page 2 normalized
│   │       └── {uuid}_foto_facciata.jpg
│   │
│   └── CONTRATTO/
│       └── {entity_id}/
│           └── {uuid}_contratto.pdf
│
└── tenant_produzione/                    # Another tenant
    ├── temp_uploads/
    ├── SOGGETTO_ANAGRAFICO/
    └── ...


NORMALIZATION RULES:
──────────────────────
Input Format       → Output Format       │ Notes
────────────────────────────────────────────────────────────────
JPG/JPEG           → JPEG (optimized)     │ Quality 85%, max 2048px
PNG                → JPEG                 │ Transparency → white bg
PDF (single page)  → JPEG                 │ 1 page → 1 file
PDF (multi-page)   → JPEG per page        │ N pages → N files
HEIC/HEIF          → JPEG                 │ Apple format
TIFF               → JPEG                 │
GIF                → JPEG (first frame)   │ Animation lost
WEBP               → JPEG                 │
BMP                → JPEG                 │

All normalized files:
- Format: JPEG
- Max dimension: 2048px (aspect ratio preserved)
- Quality: 85%
- Color space: RGB
```

---

## 6. Similarity Matching Algorithm Flow

```
┌──────────────────────────────────────────────────────────────┐
│          SIMILARITY MATCHING ALGORITHM                       │
└──────────────────────────────────────────────────────────────┘

Input: Parsed Document Data
{
  "codice_fiscale": "RSSMRA80A01H501Z",
  "nome": "MARIO",
  "cognome": "ROSSI",
  "data_nascita": "1980-01-01"
}

                     │
                     v
        ┌────────────────────────┐
        │ STEP 1: CF Exact Match │
        └────────────────────────┘
                     │
     Query: SELECT * FROM soggetti
            WHERE codice_fiscale = 'RSSMRA80A01H501Z'
                     │
         ┌───────────┴───────────┐
         │                       │
       FOUND                  NOT FOUND
         │                       │
         v                       │
    ┌─────────────┐              │
    │ Return:     │              │
    │ score: 1.0  │              │
    │ reason: "CF"│              │
    └─────────────┘              │
                                 v
                    ┌────────────────────────────┐
                    │ STEP 2: Fuzzy Name Match   │
                    └────────────────────────────┘
                                 │
         Query: SELECT * FROM soggetti
                WHERE nome ILIKE '%MARIO%'
                  AND cognome ILIKE '%ROSSI%'
                                 │
                                 v
                    ┌────────────────────────────┐
                    │ For each candidate:        │
                    │ Calculate similarity       │
                    └────────────────────────────┘
                                 │
                                 v
            ┌────────────────────────────────────────┐
            │ Levenshtein Distance Algorithm         │
            │                                        │
            │ nome_score = levenshtein_ratio(        │
            │   parsed.nome,                         │
            │   candidate.nome                       │
            │ )                                      │
            │                                        │
            │ cognome_score = levenshtein_ratio(     │
            │   parsed.cognome,                      │
            │   candidate.cognome                    │
            │ )                                      │
            │                                        │
            │ birth_score = 1.0 if dates match       │
            │             else 0.0                   │
            │                                        │
            │ final_score = (                        │
            │   nome_score * 0.3 +                   │
            │   cognome_score * 0.3 +                │
            │   birth_score * 0.4                    │
            │ )                                      │
            └────────────────────────────────────────┘
                                 │
                                 v
                    ┌────────────────────────────┐
                    │ STEP 3: Filter & Rank      │
                    └────────────────────────────┘
                                 │
            Keep only candidates with score >= 0.5
            Sort by score DESC
                                 │
                                 v
                    ┌────────────────────────────┐
                    │ Return ranked list         │
                    └────────────────────────────┘


EXAMPLES:
─────────

Example 1: Perfect Match
────────────────────────
Parsed:    { cf: "RSSMRA80A01H501Z", nome: "MARIO", cognome: "ROSSI", dob: "1980-01-01" }
Candidate: { cf: "RSSMRA80A01H501Z", nome: "Mario", cognome: "Rossi", dob: "1980-01-01" }
→ score: 1.0 (CF exact match)


Example 2: Name Variant
────────────────────────
Parsed:    { cf: null, nome: "MARIO", cognome: "ROSSI", dob: "1980-01-01" }
Candidate: { cf: "...", nome: "Mario", cognome: "De Rossi", dob: "1980-01-01" }
→ nome_score: 1.0 (exact)
→ cognome_score: 0.75 (Rossi vs De Rossi)
→ birth_score: 1.0 (exact)
→ final: (1.0*0.3) + (0.75*0.3) + (1.0*0.4) = 0.925 → 92.5%


Example 3: Typo
────────────────
Parsed:    { nome: "MARIO", cognome: "ROSSI", dob: "1980-01-01" }
Candidate: { nome: "Marlo", cognome: "Rossi", dob: "1980-01-01" }
→ nome_score: 0.8 (1 char diff)
→ cognome_score: 1.0
→ birth_score: 1.0
→ final: (0.8*0.3) + (1.0*0.3) + (1.0*0.4) = 0.94 → 94%


Example 4: Omonimo (Different Person)
──────────────────────────────────────
Parsed:    { nome: "MARIO", cognome: "ROSSI", dob: "1980-01-01" }
Candidate: { nome: "Mario", cognome: "Rossi", dob: "1975-03-15" }
→ nome_score: 1.0
→ cognome_score: 1.0
→ birth_score: 0.0 (different)
→ final: (1.0*0.3) + (1.0*0.3) + (0.0*0.4) = 0.6 → 60%
→ MEDIUM match - show warning


THRESHOLD RECOMMENDATIONS:
──────────────────────────
Score          │ Action
───────────────┼─────────────────────────────────────────
1.0 (100%)     │ Almost certainly same person
               │ Suggest: "Aggiungi a questa anagrafica"
               │
0.85 - 0.99    │ Very likely same person
               │ Suggest: "Probabile match" (show details)
               │
0.70 - 0.84    │ Possible match
               │ Show: "Potrebbe essere questa persona?"
               │
0.50 - 0.69    │ Low confidence
               │ Show: "Verifica manualmente"
               │
< 0.50         │ Different person
               │ Don't show (filter out)
```

---

## 7. Migration Strategy - Dual Mode Support

```
┌──────────────────────────────────────────────────────────────┐
│                    MIGRATION STRATEGY                        │
│              (Backward Compatible Dual Mode)                 │
└──────────────────────────────────────────────────────────────┘

PHASE 1: Add New Schema (Week 1)
────────────────────────────────
┌────────────────────────────────────────┐
│ Documento (MODIFIED)                   │
├────────────────────────────────────────┤
│ # NEW FIELDS                           │
│ metadata_parsato: JSON                 │
│ confidence_score: int                  │
│                                        │
│ # LEGACY FIELDS (keep for now)         │
│ nome_file: str          ⚠️ NULLABLE    │
│ file_path: str          ⚠️ NULLABLE    │
│ mime_type: str          ⚠️ NULLABLE    │
│ dimensione: int         ⚠️ NULLABLE    │
└────────────────────────────────────────┘

┌────────────────────────────────────────┐
│ DocumentoFile (NEW TABLE)              │
├────────────────────────────────────────┤
│ id, documento_id, file_path, ...       │
└────────────────────────────────────────┘

Migration SQL:
─────────────
ALTER TABLE anag_documenti
  ADD COLUMN metadata_parsato JSON,
  ADD COLUMN confidence_score INTEGER,
  ALTER COLUMN nome_file DROP NOT NULL,
  ALTER COLUMN file_path DROP NOT NULL;

CREATE TABLE anag_documenti_files (
  id SERIAL PRIMARY KEY,
  documento_id INTEGER NOT NULL REFERENCES anag_documenti(id) ON DELETE CASCADE,
  file_path VARCHAR(500) NOT NULL,
  ...
);


PHASE 2: Dual Mode Logic (Week 2-3)
────────────────────────────────────
API reads both old and new structure:

def get_documento_files(documento_id):
    doc = Documento.query.get(documento_id)

    # NEW MODE: has files relationship
    if doc.files:
        return [file.to_dict() for file in doc.files]

    # LEGACY MODE: use old fields
    elif doc.file_path:
        return [{
            "id": None,
            "file_path": doc.file_path,
            "nome_file": doc.nome_file,
            "mime_type": doc.mime_type,
            "dimensione": doc.dimensione,
            "ordine": 1,
            "tipo_pagina": "unico",
            "_legacy": True
        }]

    return []


PHASE 3: Migration Script (Week 4)
───────────────────────────────────
Migrate all old documents to new structure:

def migrate_documenti():
    for doc in Documento.query.all():
        # Skip if already migrated
        if doc.files:
            continue

        # Skip if no file_path (empty)
        if not doc.file_path:
            continue

        print(f"Migrating Documento #{doc.id}")

        # Create DocumentoFile from legacy fields
        file = DocumentoFile(
            documento_id=doc.id,
            file_path=doc.file_path,
            nome_file=doc.nome_file,
            mime_type=doc.mime_type,
            dimensione=doc.dimensione,
            ordine=1,
            tipo_pagina="unico"
        )

        # Normalize file (if image/pdf)
        try:
            normalized_path, width, height = file_normalization.normalize_file(
                input_path=file_storage.get_file_path(file.file_path, tenant_schema),
                output_path=...,
            )
            file.file_normalizzato_path = normalized_path
            file.normalizzato_width = width
            file.normalizzato_height = height
        except Exception as e:
            print(f"  ⚠️ Normalization failed: {e}")

        db.session.add(file)

        # Clear legacy fields (optional - can wait for Phase 4)
        # doc.file_path = None
        # doc.nome_file = None

        db.session.commit()
        print(f"  ✓ Migrated to DocumentoFile #{file.id}")


PHASE 4: Deprecation (Month 2+)
────────────────────────────────
After all data migrated:

1. Remove dual-mode logic (always use files relationship)
2. Drop legacy columns:
   ALTER TABLE anag_documenti
     DROP COLUMN nome_file,
     DROP COLUMN file_path,
     DROP COLUMN mime_type,
     DROP COLUMN dimensione;

3. Update API docs
4. Remove legacy code paths
```

---

**Document Version**: 1.0
**Last Updated**: 2026-01-31
