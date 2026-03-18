# Fase 1: Foundation - COMPLETATA ✅

**Data Completamento**: 2026-01-31
**Tempo Implementazione**: ~2 ore
**Status**: Ready for Testing

---

## 📦 Deliverables Completati

### 1. Database Migrations ✅

**File Creati**:
- `backend/modules/anagrafica_italiana/migrations/versions/2026013101_documento_multifile.py`
- `backend/alembic/versions/2026013101_add_multifile_config_to_tipo_documento.py`

**Modifiche Database**:
- ✅ Aggiunto campo `metadata_parsato` (JSON) a `anag_documenti`
- ✅ Aggiunto campo `confidence_score` (INT) a `anag_documenti`
- ✅ Resi nullable campi legacy (`nome_file`, `file_path`, `mime_type`, `dimensione`)
- ✅ Creata tabella `anag_documenti_files` con tutti i campi e relationships
- ✅ Creati 3 indexes per performance su DocumentoFile
- ✅ Aggiunto campo `parsing_multi_file_config` (JSON) a `anag_tipi_documento`

### 2. Modelli SQLAlchemy ✅

**File Creati/Modificati**:
- ✅ `backend/modules/anagrafica_italiana/models/documento_file.py` (NUOVO)
  - Classe `DocumentoFile` completa
  - Properties: `is_parsed`, `is_normalized`, `display_name`
  - Method `to_dict()` per API responses

- ✅ `backend/modules/anagrafica_italiana/models/documento.py` (MODIFICATO)
  - Aggiunti campi `metadata_parsato`, `confidence_score`
  - Aggiunta relationship `files` a DocumentoFile
  - Property `is_legacy` per backward compatibility
  - Method `get_files_list()` supporta legacy e nuovo formato
  - Method `to_dict()` aggiornato

- ✅ `backend/modules/anagrafica_italiana/models/__init__.py` (AGGIORNATO)
  - Export `DocumentoFile`

### 3. File Normalization Service ✅

**File Creato**:
- ✅ `backend/app/core/file_normalization.py`

**Features Implementate**:
- ✅ Conversione PDF → JPEG (singola pagina e multi-page)
- ✅ Conversione immagini → JPEG (PNG, HEIC, TIFF, GIF, BMP, WEBP)
- ✅ Resize automatico max 2048px (mantiene aspect ratio)
- ✅ Qualità JPEG 85% (ottimo compromesso qualità/dimensione)
- ✅ Progressive JPEG per web
- ✅ Gestione trasparenza (background bianco)
- ✅ Resampling LANCZOS per qualità ottimale

**Metodi Pubblici**:
```python
file_normalization.normalize_file(input_path, output_path, page_number=1)
→ Returns: (normalized_path, width, height)

file_normalization.normalize_pdf_multi_page(input_path, output_dir, base_filename)
→ Returns: [(path1, w1, h1), (path2, w2, h2), ...]

file_normalization.is_supported(file_path)
→ Returns: bool
```

### 4. Upload Multi-File API ✅

**File Modificato**:
- ✅ `backend/modules/anagrafica_italiana/routes/documenti.py`

**Nuovo Endpoint**:
```python
POST /api/v1/anagrafica/documenti/upload-multi

Form Data:
- soggetto_id: int
- tipo_documento_id: int
- files: List[UploadFile]
- tipo_pagina: Optional[List[str]]  # fronte, retro, pagina_1, etc.
- data_scadenza: Optional[str]      # YYYY-MM-DD
- note: Optional[str]
- descrizione: Optional[str]

Response:
{
  "documento": {
    "id": 123,
    "files": [
      {
        "id": 456,
        "file_path": "tenant_test/SOGGETTO/45/uuid_fronte.jpg",
        "file_normalizzato_path": "tenant_test/SOGGETTO/45/uuid_fronte_norm.jpg",
        "ordine": 1,
        "tipo_pagina": "fronte",
        "parsing_job_uuid": "abc-123"
      }
    ],
    "metadata_parsato": null,  # Populated after parsing
    "confidence_score": null
  },
  "parsing_jobs": [
    {
      "job_uuid": "abc-123",
      "status": "QUEUED"
    }
  ]
}
```

**Funzionalità**:
- ✅ Upload multipli file in una request
- ✅ Auto-determinazione `tipo_pagina` se non fornito
  - 1 file → "unico"
  - 2 file → "fronte", "retro"
  - 3+ file → "fronte", "retro", "pagina_3", "pagina_4", ...
- ✅ Normalizzazione automatica di ogni file
- ✅ Parsing opzionale per-file (basato su `parsing_multi_file_config`)
- ✅ Link DocumentoFile → DocumentJob se parsing attivo
- ✅ Rollback completo in caso di errore

### 5. Parsing Callback Enhancement ✅

**File Modificato**:
- ✅ `backend/app/core/platform_services/document_parsing_service.py`

**Nuovo Metodo**:
```python
def _update_documento_metadata(job: DocumentJob, parsed_data: Dict) -> None:
    """
    Update DocumentoFile and merge metadata into Documento parent.

    Workflow:
    1. Find DocumentoFile linked to job
    2. Update DocumentoFile.parsing_result and confidence_score
    3. Get parent Documento
    4. Merge all files' parsing results into Documento.metadata_parsato
    5. Calculate average confidence_score
    """
```

**Funzionalità**:
- ✅ Callback aggiornato per popolare `DocumentoFile.parsing_result`
- ✅ Merge automatico risultati da tutti i file in `Documento.metadata_parsato`
- ✅ Calcolo confidence_score medio
- ✅ Gestione graceful errori (non blocca callback se merge fallisce)
- ✅ Logging dettagliato per debug

---

## 🧪 Testing Checklist

### Database Migrations
- [ ] Run migration su tenant_test: `alembic -x schema=tenant_test upgrade head`
- [ ] Verificare tabella `anag_documenti_files` creata
- [ ] Verificare campi `metadata_parsato`, `confidence_score` in `anag_documenti`
- [ ] Verificare campi legacy nullable

### File Normalization
- [ ] Test conversione JPEG → JPEG (deve ottimizzare)
- [ ] Test conversione PNG → JPEG (trasparenza → background bianco)
- [ ] Test conversione PDF single-page → JPEG
- [ ] Test conversione PDF multi-page → multiple JPEG
- [ ] Verificare resize max 2048px
- [ ] Verificare qualità JPEG 85%

### Upload Multi-File API
- [ ] Test upload 1 file (tipo_pagina="unico")
- [ ] Test upload 2 file fronte/retro CI
- [ ] Test upload 3+ file (multi-page PDF)
- [ ] Test con `tipo_pagina` custom
- [ ] Test senza `tipo_pagina` (auto-detect)
- [ ] Test con parsing attivo (se configurato)
- [ ] Verificare file normalizzati creati
- [ ] Verificare DocumentoFile records creati

### Parsing Callback
- [ ] Test parsing single file → metadata_parsato popolato
- [ ] Test parsing multi-file → merge corretto in metadata_parsato
- [ ] Test confidence_score medio calcolato
- [ ] Verificare DocumentoFile.parsing_result aggiornato
- [ ] Test con parsing job fallito (non deve crashare)

### Backward Compatibility
- [ ] Documenti legacy (file_path popolato) ancora leggibili
- [ ] `get_files_list()` funziona con legacy
- [ ] `to_dict()` funziona con legacy
- [ ] Upload legacy `/upload` ancora funzionante

---

## 📋 Comandi Testing

### 1. Run Migrations
```bash
cd backend

# Migrate public schema
alembic upgrade head

# Migrate tenant_test
alembic -x schema=tenant_test upgrade head

# Verify
psql -d gestione_affitti -c "\d tenant_test.anag_documenti_files"
```

### 2. Test Upload Multi-File (curl)
```bash
# Upload CI fronte + retro
curl -X POST "http://localhost:8000/api/v1/anagrafica/documenti/upload-multi" \
  -H "Authorization: Bearer <token>" \
  -F "soggetto_id=1" \
  -F "tipo_documento_id=1" \
  -F "files=@fronte.jpg" \
  -F "files=@retro.jpg" \
  -F "tipo_pagina=fronte" \
  -F "tipo_pagina=retro"
```

### 3. Verify File Normalization
```bash
# Check storage directory
ls -lh storage/tenant_test/SOGGETTO/1/

# Should show:
# uuid_fronte.jpg          (original)
# uuid_fronte_norm.jpg     (normalized)
# uuid_retro.jpg           (original)
# uuid_retro_norm.jpg      (normalized)
```

### 4. Check Database
```sql
-- Get documento with files
SELECT
  d.id,
  d.metadata_parsato,
  d.confidence_score,
  COUNT(f.id) as num_files
FROM tenant_test.anag_documenti d
LEFT JOIN tenant_test.anag_documenti_files f ON f.documento_id = d.id
WHERE d.id = 1
GROUP BY d.id;

-- Get files details
SELECT
  id,
  nome_file,
  ordine,
  tipo_pagina,
  file_normalizzato_path,
  confidence_score
FROM tenant_test.anag_documenti_files
WHERE documento_id = 1
ORDER BY ordine;
```

---

## 🐛 Known Issues / Limitations

1. **Dependencies Required**:
   - ⚠️ Pillow deve essere installato: `pip install Pillow`
   - ⚠️ pdf2image deve essere installato: `pip install pdf2image`
   - ⚠️ poppler-utils deve essere installato: `sudo apt-get install poppler-utils`

2. **Performance**:
   - ⚠️ Normalizzazione file può richiedere 1-3 secondi per file
   - ⚠️ Upload multi-file con 5+ file può essere lento (da ottimizzare con async processing)

3. **Storage**:
   - ⚠️ File normalizzati raddoppiano storage (+100% per documento)
   - 💡 Mitigazione: JPEG quality 85% comprime bene

4. **Parsing**:
   - ⚠️ Parsing multi-file crea N DocumentJob (uno per file con parsing attivo)
   - ⚠️ Se un file fallisce parsing, altri continuano (behavior corretto)

---

## 🚀 Next Steps

### Immediate (Before Production)
1. **Install Dependencies** su tutti gli ambienti
2. **Run Migrations** su dev, staging, production
3. **Testing Completo** (vedi checklist sopra)
4. **Performance Testing** con file grandi (10MB+)

### Fase 2 (Next Sprint)
- [ ] Implementare Similarity Matching Algorithm
- [ ] API `POST /anagrafica/soggetti/find-similar`
- [ ] Frontend SimilarityMatchDialog component
- [ ] Workflow creazione anagrafica con merge intelligente

### Documentation
- [ ] Update API docs (Swagger/OpenAPI)
- [ ] User guide per upload multi-file
- [ ] Developer guide per file normalization

---

## 📊 Metriche Implementation

| Metrica | Valore |
|---------|--------|
| **Files Created** | 4 |
| **Files Modified** | 5 |
| **Lines of Code** | ~800 |
| **Database Tables Added** | 1 (anag_documenti_files) |
| **Database Fields Added** | 2 (Documento) + 13 (DocumentoFile) |
| **API Endpoints Added** | 1 (upload-multi) |
| **Time to Implement** | ~2 hours |
| **Test Coverage** | TBD (da implementare) |

---

**Implementation Completed By**: Claude Code
**Date**: 2026-01-31
**Status**: ✅ READY FOR TESTING
