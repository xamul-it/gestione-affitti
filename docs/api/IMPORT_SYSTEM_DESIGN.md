# Sistema di Importazione Generico con Mappatura Campi
## Design Document

---

## 1. Obiettivi

### Requisiti Funzionali
1. **Genericità**: Sistema riusabile da qualsiasi modulo/entità
2. **Flessibilità**: Supporto sia template standard che CSV generici con mappatura
3. **Mappatura Campi**: UI intuitiva per associare colonne CSV a campi dell'entità
4. **Configurazioni Salvate**: Possibilità di salvare e riutilizzare mappature
5. **Validazione**: Preview e validazione dati prima dell'importazione
6. **Gestione Errori**: Report dettagliato con possibilità di correzione

### User Flow
1. **Upload CSV** → Selezione file
2. **Analisi Automatica** → Sistema rileva colonne e suggerisce mappature
3. **Mappatura Campi** → Utente conferma/modifica associazioni
4. **Preview Dati** → Visualizzazione anteprima righe con validazione
5. **Configurazione Salvataggio** → Opzione per salvare la mappatura
6. **Importazione** → Esecuzione con progress e report finale

---

## 2. Architettura Backend

### 2.1 Database Models

#### ImportConfiguration (Nuova Tabella)
```python
class ImportConfiguration(Base):
    __tablename__ = "import_configurations"

    id: int (PK)
    name: str  # Nome configurazione (es. "Import Immobili da Excel Agenzia")
    module_name: str  # "affitti_lungo"
    entity_name: str  # "UnitaImmobiliare"
    field_mapping: JSON  # {"CSV_Column": "model_field"}
    created_at: datetime
    updated_at: datetime
    created_by: str (optional - per futura gestione utenti)
```

### 2.2 API Endpoints

#### 1. Analisi CSV e Inferenza Campi
```
POST /api/v1/import-export/analyze
Request:
  - file: UploadFile
  - module_name: str
  - entity_name: str

Response:
{
  "csv_columns": ["Indirizzo", "Città", "CAP", "Superficie"],
  "entity_fields": [
    {
      "name": "indirizzo",
      "label": "Indirizzo",
      "type": "string",
      "required": true,
      "description": "Indirizzo completo dell'immobile"
    },
    {
      "name": "citta",
      "label": "Città",
      "type": "string",
      "required": true
    },
    ...
  ],
  "suggested_mapping": {
    "Indirizzo": "indirizzo",
    "Città": "citta",
    "CAP": "cap",
    "Superficie": "superficie_mq"
  },
  "sample_rows": [
    {"Indirizzo": "Via Roma 1", "Città": "Milano", ...},
    {"Indirizzo": "Via Verdi 2", "Città": "Roma", ...}
  ]
}
```

#### 2. Preview Importazione con Validazione
```
POST /api/v1/import-export/preview
Request:
  - file: UploadFile
  - module_name: str
  - entity_name: str
  - field_mapping: JSON

Response:
{
  "total_rows": 100,
  "valid_rows": 95,
  "invalid_rows": 5,
  "preview_data": [
    {
      "row_number": 1,
      "original_data": {"Indirizzo": "Via Roma 1", ...},
      "mapped_data": {"indirizzo": "Via Roma 1", ...},
      "validation_status": "valid",
      "validation_errors": []
    },
    {
      "row_number": 3,
      "original_data": {"Indirizzo": "", ...},
      "mapped_data": {"indirizzo": "", ...},
      "validation_status": "invalid",
      "validation_errors": ["indirizzo: Campo obbligatorio mancante"]
    }
  ]
}
```

#### 3. Salvataggio Configurazione
```
POST /api/v1/import-export/configurations
Request:
{
  "name": "Import Agenzia XYZ",
  "module_name": "affitti_lungo",
  "entity_name": "UnitaImmobiliare",
  "field_mapping": {"Indirizzo": "indirizzo", ...}
}

Response:
{
  "id": 1,
  "name": "Import Agenzia XYZ",
  ...
}
```

#### 4. Lista Configurazioni
```
GET /api/v1/import-export/configurations?module_name=affitti_lungo&entity_name=UnitaImmobiliare

Response:
{
  "configurations": [
    {
      "id": 1,
      "name": "Import Agenzia XYZ",
      "field_mapping": {...},
      "created_at": "2025-11-29T10:00:00"
    }
  ]
}
```

#### 5. Caricamento Configurazione
```
GET /api/v1/import-export/configurations/{id}
```

#### 6. Importazione con Mappatura
```
POST /api/v1/import-export/import
Request:
  - file: UploadFile
  - module_name: str
  - entity_name: str
  - field_mapping: JSON
  - skip_errors: bool
  - save_configuration: bool (optional)
  - configuration_name: str (optional)

Response:
{
  "success": true,
  "total_rows": 100,
  "imported": 95,
  "errors": 5,
  "error_details": [...],
  "configuration_id": 1 (if saved)
}
```

### 2.3 Service Layer Enhancement

#### ImportExportService Updates
```python
class ImportExportService:

    def analyze_csv(self, file_content, model_class, create_schema):
        """
        Analizza CSV e suggerisce mappature automatiche.
        - Estrae headers CSV
        - Estrae campi entity da model/schema
        - Suggerisce mappature per fuzzy matching dei nomi
        - Ritorna sample rows per preview
        """

    def infer_field_mapping(self, csv_columns, entity_fields):
        """
        Algoritmo di inferenza automatica:
        1. Exact match (case-insensitive)
        2. Fuzzy match (similarity > 80%)
        3. Common aliases (es. "Addr" -> "indirizzo")
        """

    def validate_import_preview(self, csv_data, field_mapping, create_schema):
        """
        Valida ogni riga senza salvarla nel DB.
        Ritorna preview con status validazione per riga.
        """

    def import_from_csv_with_mapping(self, csv_data, model, field_mapping, create_schema, skip_errors):
        """
        Versione aggiornata che usa field_mapping esplicito.
        """
```

---

## 3. Architettura Frontend

### 3.1 Componenti Principali

#### ImportWizard (Nuovo)
Multi-step wizard per l'intero processo:
```jsx
<ImportWizard
  moduleName="affitti_lungo"
  entityName="UnitaImmobiliare"
  entityLabel="Unità Immobiliari"
  onComplete={handleImportComplete}
  onCancel={handleCancel}
/>
```

**Steps:**
1. **Upload** - Selezione file e configurazione
2. **Mapping** - Associazione campi CSV → Entity
3. **Preview** - Anteprima e validazione
4. **Import** - Esecuzione e risultati

#### Step 1: ImportUploadStep
- Upload file (drag-and-drop o click)
- Scelta tra:
  - ☑️ Usa template standard (nessuna mappatura necessaria)
  - ☑️ Carica CSV generico (richiede mappatura)
  - ☑️ Carica configurazione salvata
- Dropdown per selezionare configurazioni esistenti
- Bottone "Analizza File"

#### Step 2: ImportMappingStep
```jsx
<ImportMappingStep
  csvColumns={["Indirizzo", "Città", "CAP"]}
  entityFields={[
    {name: "indirizzo", label: "Indirizzo", type: "string", required: true},
    {name: "citta", label: "Città", type: "string", required: true}
  ]}
  suggestedMapping={{"Indirizzo": "indirizzo", "Città": "citta"}}
  onMappingChange={handleMappingChange}
  onNext={handleNext}
/>
```

**UI Layout:**
```
┌─────────────────────────────────────────────────┐
│  Mappatura Campi CSV                            │
│                                                 │
│  Colonne CSV (file)     →    Campi Entity      │
│  ───────────────────────────────────────────   │
│  ┌─────────────────┐         ┌──────────────┐  │
│  │ Indirizzo       │ →→→→→→→ │ indirizzo ✓  │  │
│  └─────────────────┘         └──────────────┘  │
│                                                 │
│  ┌─────────────────┐         ┌──────────────┐  │
│  │ Città           │ →→→→→→→ │ citta ✓      │  │
│  └─────────────────┘         └──────────────┘  │
│                                                 │
│  ┌─────────────────┐         ┌──────────────┐  │
│  │ Superficie mq   │ →→→→→→→ │ superficie_mq│  │
│  └─────────────────┘         └──────────────┘  │
│                                                 │
│  ┌─────────────────┐         ┌──────────────┐  │
│  │ Non Mappato     │         │ [Ignora]     │  │
│  └─────────────────┘         └──────────────┘  │
│                                                 │
│  Campi Richiesti Non Mappati:                  │
│  ⚠️ cap (obbligatorio)                         │
│                                                 │
│  [ Salva questa configurazione ]               │
│  Nome: [_____________________]                 │
│                                                 │
│  [Annulla]  [← Indietro]  [Anteprima →]       │
└─────────────────────────────────────────────────┘
```

**Features:**
- Dropdown per ogni colonna CSV → seleziona campo entity
- Colori:
  - Verde: mappato correttamente
  - Giallo: campo opzionale non mappato
  - Rosso: campo obbligatorio mancante
- Auto-suggest basato su nomi simili
- Drag-and-drop alternativo
- Checkbox "Salva configurazione" con input nome

#### Step 3: ImportPreviewStep
```jsx
<ImportPreviewStep
  previewData={[
    {row: 1, status: "valid", data: {...}},
    {row: 2, status: "invalid", errors: [...], data: {...}}
  ]}
  totalRows={100}
  validRows={95}
  invalidRows={5}
  onBack={handleBack}
  onImport={handleImport}
/>
```

**UI Layout:**
```
┌─────────────────────────────────────────────────┐
│  Anteprima Importazione                         │
│                                                 │
│  Statistiche:                                   │
│  ✓ 95 righe valide                             │
│  ✗ 5 righe con errori                          │
│  📊 100 righe totali                            │
│                                                 │
│  ☑️ Importa solo righe valide (salta errori)   │
│  ☐ Interrompi su primo errore                  │
│                                                 │
│  Prime 10 righe:                                │
│  ┌───────────────────────────────────────────┐ │
│  │ Riga │ Indirizzo    │ Città  │ Status    │ │
│  ├───────────────────────────────────────────┤ │
│  │  1   │ Via Roma 1   │ Milano │ ✓ Valido  │ │
│  │  2   │ Via Verdi 2  │ Roma   │ ✓ Valido  │ │
│  │  3   │              │ Napoli │ ✗ Errore  │ │
│  │      │ ⚠️ indirizzo: campo obbligatorio   │ │
│  └───────────────────────────────────────────┘ │
│                                                 │
│  [Annulla]  [← Modifica Mappatura]  [Importa →]│
└─────────────────────────────────────────────────┘
```

#### Step 4: ImportResultsStep
Riutilizza il componente esistente con miglioramenti.

### 3.2 Component Structure

```
/src/components/Platform/
├── ImportWizard/
│   ├── ImportWizard.jsx          # Main wizard container
│   ├── ImportWizard.css
│   ├── ImportUploadStep.jsx      # Step 1: Upload
│   ├── ImportMappingStep.jsx     # Step 2: Field mapping
│   ├── ImportPreviewStep.jsx     # Step 3: Preview
│   ├── ImportResultsStep.jsx     # Step 4: Results
│   ├── FieldMapper.jsx            # Field mapping component
│   └── ConfigurationSelector.jsx # Saved configs dropdown
├── ImportButton.jsx               # Entry point (updated)
└── ImportModal.jsx                # Legacy (deprecabile)
```

---

## 4. Algoritmo di Inferenza Mappatura

### 4.1 Fuzzy Matching
```python
from difflib import SequenceMatcher

def calculate_similarity(a: str, b: str) -> float:
    """Calcola similarità tra due stringhe (0-1)"""
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()

def infer_mapping(csv_columns: List[str], entity_fields: List[str]) -> Dict[str, str]:
    mapping = {}

    for csv_col in csv_columns:
        best_match = None
        best_score = 0.0

        for entity_field in entity_fields:
            # 1. Exact match (case-insensitive)
            if csv_col.lower() == entity_field.lower():
                best_match = entity_field
                break

            # 2. Check aliases
            if csv_col.lower() in FIELD_ALIASES.get(entity_field, []):
                best_match = entity_field
                break

            # 3. Fuzzy match
            score = calculate_similarity(csv_col, entity_field)
            if score > best_score and score > 0.7:  # Threshold 70%
                best_score = score
                best_match = entity_field

        if best_match:
            mapping[csv_col] = best_match

    return mapping
```

### 4.2 Common Field Aliases
```python
FIELD_ALIASES = {
    "indirizzo": ["address", "addr", "via", "street"],
    "citta": ["city", "città", "comune"],
    "cap": ["zip", "postal_code", "codice_postale"],
    "superficie_mq": ["superficie", "area", "mq", "sqm", "square_meters"],
    "locali": ["rooms", "vani", "stanze"],
    # ... configurabile per ogni entità
}
```

---

## 5. Validazione e Gestione Errori

### 5.1 Tipi di Errori
1. **Errori di Mappatura**:
   - Campi obbligatori non mappati
   - Campi CSV non riconosciuti

2. **Errori di Validazione**:
   - Valori mancanti per campi required
   - Tipo dato incompatibile (string per int)
   - Vincoli Pydantic non rispettati
   - Chiavi esterne non valide

3. **Errori di Importazione**:
   - Vincoli DB (unique, foreign key)
   - Duplicati

### 5.2 Strategia di Gestione
- **Skip Errors Mode**: Salta righe invalide, importa valide
- **Stop on Error Mode**: Prima riga invalida → stop + rollback
- **Report Dettagliato**: Numero riga, dati originali, errore specifico

---

## 6. Configurazioni Salvate

### 6.1 Use Cases
1. **Import Ricorrenti**: Stesso fornitore/formato ogni mese
2. **Template Personalizzati**: Ogni agenzia ha suo formato
3. **Multi-Entity**: Configurazioni per diverse entità dello stesso modulo

### 6.2 UI Gestione Configurazioni
```
Gestione Configurazioni Import
┌─────────────────────────────────────────────┐
│ Nome                  │ Entità          │   │
├─────────────────────────────────────────────┤
│ Import Agenzia XYZ    │ UnitaImmobil.   │ 🗑️│
│ Import Excel Mensile  │ UnitaImmobil.   │ 🗑️│
│ Import Contratti 2025 │ Contratto       │ 🗑️│
└─────────────────────────────────────────────┘
[+ Nuova Configurazione]
```

---

## 7. Performance e Scalabilità

### 7.1 Ottimizzazioni
- **Batch Insert**: Gruppi di 100 record per query
- **Lazy Loading**: Preview solo prime 50 righe
- **Async Processing**: Import grandi > 1000 righe in background (futura)
- **Progress Updates**: WebSocket/polling per status real-time (futura)

### 7.2 Limiti
- File size: max 10MB (configurabile)
- Rows per import: max 10,000 (warning se > 1000)
- Preview rows: max 50 visualizzate

---

## 8. Workflow Completo - Esempio Pratico

### Scenario: Import Unità Immobiliari da Excel Agenzia

1. **Utente**: Click su "📥 Importa" in lista Unità Immobiliari
2. **Sistema**: Apre ImportWizard
3. **Utente**: Upload file "immobili_gennaio_2025.csv"
4. **Sistema**:
   - Analizza file (trova 150 righe)
   - Rileva colonne: "Indirizzo Completo", "Comune", "CAP", "Superficie", "N. Vani"
   - Suggerisce mapping:
     * "Indirizzo Completo" → indirizzo
     * "Comune" → citta
     * "CAP" → cap
     * "Superficie" → superficie_mq
     * "N. Vani" → locali
5. **Utente**: Conferma mapping, spunta "Salva configurazione", nome "Import Agenzia ABC"
6. **Sistema**: Valida 150 righe → 148 valide, 2 errori (CAP mancante)
7. **Utente**: Visualizza preview, sceglie "Salta errori", click "Importa"
8. **Sistema**: Import 148 righe, salva configurazione, mostra risultati
9. **Prossimo Mese**: Utente seleziona configurazione "Import Agenzia ABC" → mapping automatico

---

## 9. Testing Strategy

### 9.1 Unit Tests
- Fuzzy matching algorithm
- Field validation
- Mapping inference

### 9.2 Integration Tests
- API endpoints
- Database transactions
- File upload handling

### 9.3 UAT Scenarios
1. Import con template standard (nessuna mappatura)
2. Import CSV generico con mapping automatico perfetto
3. Import CSV con mapping parziale (richiede input utente)
4. Import con errori di validazione
5. Salvataggio e riutilizzo configurazione
6. Import di entità con relazioni (foreign keys)

---

## 10. Implementazione Phases

### Phase 1: Backend Core ✓
- [x] Model ImportConfiguration
- [x] API analyze endpoint
- [x] API preview endpoint
- [x] API configurations CRUD
- [x] Service layer updates

### Phase 2: Frontend Core ✓
- [x] ImportWizard component
- [x] Multi-step navigation
- [x] Upload step
- [x] Mapping step UI
- [x] Preview step
- [x] Results step

### Phase 3: Integration ✓
- [x] Integrate in Immobili module
- [x] UAT testing
- [x] Bug fixes

### Phase 4: Polish ✓
- [x] UX review
- [x] Final UAT
- [x] Documentation

