# Guida Import/Export Dati - Piattaforma Gestione Affitti

## Quick Start - Integrazione in 2 Minuti

Per aggiungere import/export a una lista entità:

```jsx
// 1. Import dei componenti
import ImportButton from '../../../../components/Platform/ImportButton';
import ExportButton from '../../../../components/Platform/ExportButton';

// 2. Aggiungi nella toolbar
<ImportButton
  moduleName="nome_modulo"           // es: "anagrafica_italiana", "immobili"
  entityName="NomeModelloSQLAlchemy" // es: "SoggettoAnagrafico", "UnitaImmobiliare"
  entityLabel="Etichetta UI"         // es: "Persone Fisiche"
  onImportComplete={() => fetchData()}
/>
<ExportButton
  moduleName="nome_modulo"
  entityName="NomeModelloSQLAlchemy"
  entityLabel="Etichetta UI"
/>
```

**Requisiti backend** (già soddisfatti per tutti i moduli esistenti):
- Modello in `modules/{modulo}/models/__init__.py`
- Schema `{Entity}Create` in `modules/{modulo}/schemas/__init__.py` (opzionale)

---

## Panoramica

La piattaforma fornisce un sistema di import/export dati generico a livello di core che permette ai moduli di importare ed esportare dati in formati standard (CSV, Excel, JSON) senza dover implementare logica custom.

**Caratteristiche principali:**

- Import/export generico per qualsiasi entità di qualsiasi modulo
- Supporto formati: CSV, Excel (XLSX), JSON
- Mapping automatico dei campi con fuzzy matching
- Anteprima e validazione pre-import
- Salvataggio configurazioni di mapping riutilizzabili
- Arricchimento automatico dati (per UnitaImmobiliare)
- Download diretto file

---

## Architettura

### Componenti

```
backend/app/core/
├── routes/
│   └── import_export.py          # API REST endpoints
├── platform_services/
│   └── import_export_service.py  # Logica di business
├── models/
│   └── import_configuration.py   # Modello per configurazioni salvate
└── schemas/
    └── import_configuration.py   # Schemi Pydantic
```

### Dipendenze

Il sistema si integra con:
- **Moduli business**: Carica dinamicamente modelli e schemi da `backend/modules/{module_name}/`
- **Multi-tenancy**: Rispetta l'isolamento tenant tramite `get_db()` dependency
- **Servizi di arricchimento**: `AddressNormalizerService`, `CodiceGeneratorService`, `CategoriaCatastaleService`

---

## API Endpoints

Tutti gli endpoint sono sotto il prefisso `/api/v1/import-export/`.

### Import

#### POST `/import`
Import generico da file CSV.

**Parametri Query:**
| Parametro | Tipo | Richiesto | Default | Descrizione |
|-----------|------|-----------|---------|-------------|
| `module_name` | string | ✓ | - | Nome tecnico modulo (es. `immobili`) |
| `entity_name` | string | ✓ | - | Nome entità (es. `UnitaImmobiliare`) |
| `skip_errors` | bool | - | true | Salta righe con errori |
| `enable_enrichment` | bool | - | true | Abilita arricchimento automatico |
| `enable_updates` | bool | - | true | Permette UPDATE se presente ID |

**Body:** `multipart/form-data` con file CSV

**Response:**
```json
{
  "success": true,
  "total_rows": 100,
  "imported": 95,
  "errors": 5,
  "error_details": [
    {"row": 3, "data": {...}, "error": "Validation failed: campo richiesto"}
  ]
}
```

**Esempio cURL:**
```bash
curl -X POST "http://localhost:8000/api/v1/import-export/import?module_name=immobili&entity_name=UnitaImmobiliare" \
  -H "Authorization: Bearer <token>" \
  -F "file=@unita_immobiliari.csv"
```

#### POST `/import-with-mapping`
Import con mapping esplicito dei campi.

**Parametri Query aggiuntivi:**
| Parametro | Tipo | Richiesto | Descrizione |
|-----------|------|-----------|-------------|
| `field_mapping` | string (JSON) | ✓ | Mapping CSV→entità |
| `save_configuration` | bool | - | Salva configurazione |
| `configuration_name` | string | - | Nome configurazione da salvare |

**Esempio:**
```bash
curl -X POST "http://localhost:8000/api/v1/import-export/import-with-mapping?\
module_name=immobili&\
entity_name=UnitaImmobiliare&\
field_mapping={\"Indirizzo\":\"indirizzo\",\"Citta\":\"citta\"}&\
save_configuration=true&\
configuration_name=Import_Agenzia_ABC" \
  -F "file=@data.csv"
```

---

### Export

#### GET `/export`
Export dati come JSON (per elaborazione programmatica).

**Parametri Query:**
| Parametro | Tipo | Richiesto | Default | Descrizione |
|-----------|------|-----------|---------|-------------|
| `module_name` | string | ✓ | - | Nome modulo |
| `entity_name` | string | ✓ | - | Nome entità |
| `format` | string | - | csv | Formato: `csv`, `excel`, `json` |
| `fields` | string | - | tutti | Campi separati da virgola |

**Response (format=json):**
```json
{
  "data": [
    {"id": 1, "indirizzo": "Via Roma 1", "citta": "Milano"},
    {"id": 2, "indirizzo": "Via Garibaldi 10", "citta": "Roma"}
  ],
  "count": 2
}
```

#### GET `/download`
Download file export diretto (per browser).

**Parametri:** Come `/export` ma `format` limitato a `csv` o `excel`.

**Response:** File binario con header `Content-Disposition: attachment`.

**Esempio browser:**
```
/api/v1/import-export/download?module_name=immobili&entity_name=UnitaImmobiliare&format=csv
```

---

### Template

#### GET `/template`
Genera template CSV per import (ritorna JSON).

**Parametri:**
| Parametro | Tipo | Default | Descrizione |
|-----------|------|---------|-------------|
| `module_name` | string | - | Nome modulo |
| `entity_name` | string | - | Nome entità |
| `include_sample` | bool | false | Include riga esempio |

#### GET `/download-template`
Scarica template CSV come file.

**Esempio:**
```bash
curl -O "http://localhost:8000/api/v1/import-export/download-template?\
module_name=immobili&entity_name=UnitaImmobiliare&include_sample=true"
```

---

### Analisi e Preview

#### POST `/analyze`
Analizza struttura CSV e suggerisce mapping campi.

**Response:**
```json
{
  "csv_columns": ["Indirizzo", "Città", "CAP"],
  "entity_fields": [
    {"name": "indirizzo", "label": "Indirizzo", "type": "string", "required": true},
    {"name": "citta", "label": "Citta", "type": "string", "required": false}
  ],
  "suggested_mapping": {
    "Indirizzo": "indirizzo",
    "Città": "citta",
    "CAP": "cap"
  },
  "sample_rows": [
    {"Indirizzo": "Via Roma 1", "Città": "Milano", "CAP": "20100"}
  ]
}
```

#### POST `/preview`
Valida dati senza salvare nel database.

**Response:**
```json
{
  "total_rows": 100,
  "valid_rows": 95,
  "invalid_rows": 5,
  "preview_data": [
    {
      "row_number": 2,
      "original_data": {"Indirizzo": "Via Roma"},
      "mapped_data": {"indirizzo": "Via Roma"},
      "validation_status": "valid",
      "validation_errors": []
    }
  ]
}
```

---

### Configurazioni Salvate

#### GET `/configurations`
Lista configurazioni salvate.

**Filtri opzionali:** `module_name`, `entity_name`

#### POST `/configurations`
Crea nuova configurazione.

**Body:**
```json
{
  "name": "Import Agenzia ABC",
  "module_name": "immobili",
  "entity_name": "UnitaImmobiliare",
  "field_mapping": {
    "Indirizzo_Completo": "indirizzo",
    "Comune": "citta",
    "Prov": "provincia"
  }
}
```

#### GET/PUT/DELETE `/configurations/{id}`
CRUD su singola configurazione.

---

## Integrazione con i Moduli

### Requisiti per i Moduli

Per supportare import/export, un modulo deve:

1. **Avere modelli SQLAlchemy** in `modules/{module_name}/models/__init__.py`
2. **Esportare i modelli** nel `__all__` del modulo
3. **(Opzionale)** Avere schemi Pydantic `{EntityName}Create` per validazione

### Esempio Struttura Modulo

```
modules/immobili/
├── __init__.py
├── __manifest__.py
├── models/
│   ├── __init__.py              # Esporta tutti i modelli
│   └── unita_immobiliare.py     # class UnitaImmobiliare(Base)
└── schemas/
    ├── __init__.py              # Esporta tutti gli schemi
    └── unita_immobiliare.py     # class UnitaImmobiliareCreate(BaseModel)
```

### Modello SQLAlchemy

```python
# modules/immobili/models/unita_immobiliare.py
from sqlalchemy import Column, Integer, String, Numeric
from app.core.database import Base

class UnitaImmobiliare(Base):
    __tablename__ = "unita_immobiliari"

    id = Column(Integer, primary_key=True)
    codice = Column(String(20), unique=True)
    indirizzo = Column(String(200), nullable=False)
    citta = Column(String(100))
    provincia = Column(String(2))
    cap = Column(String(5))
    superficie_mq = Column(Numeric(10, 2))
```

### Schema Pydantic (opzionale ma raccomandato)

```python
# modules/immobili/schemas/unita_immobiliare.py
from pydantic import BaseModel, Field
from typing import Optional
from decimal import Decimal

class UnitaImmobiliareCreate(BaseModel):
    codice: Optional[str] = None  # Auto-generato se mancante
    indirizzo: str = Field(..., min_length=1)
    citta: Optional[str] = None
    provincia: Optional[str] = Field(None, max_length=2)
    cap: Optional[str] = Field(None, pattern=r"^\d{5}$")
    superficie_mq: Optional[Decimal] = Field(None, ge=0)
```

### Export Modelli nel __init__.py

```python
# modules/immobili/models/__init__.py
from .unita_immobiliare import UnitaImmobiliare
from .condomini import Condominio

__all__ = ["UnitaImmobiliare", "Condominio"]
```

---

## Mapping Automatico dei Campi

Il sistema usa fuzzy matching per suggerire automaticamente il mapping tra colonne CSV e campi entità.

### Algoritmo

1. **Match esatto** (case-insensitive): `indirizzo` → `indirizzo`
2. **Alias predefiniti**: `city` → `citta`, `address` → `indirizzo`
3. **Fuzzy match** (soglia 70%): `superficie` → `superficie_mq`

### Alias Configurati

| Campo Entità | Alias Riconosciuti |
|--------------|-------------------|
| `indirizzo` | address, addr, via, street, strada |
| `citta` | city, città, comune, town |
| `cap` | zip, postal_code, codice_postale |
| `superficie_mq` | superficie, area, mq, sqm |
| `provincia` | prov, province |
| `nome` | name, firstname, first_name |
| `cognome` | surname, lastname, last_name |
| `email` | mail, e-mail, posta |
| `telefono` | phone, tel, mobile, cellulare |
| `codice_fiscale` | cf, tax_code, fiscal_code |
| `partita_iva` | piva, vat, vat_number |

### Estendere gli Alias

Per aggiungere nuovi alias, modificare `infer_field_mapping()` in:
`backend/app/core/platform_services/import_export_service.py`

---

## Arricchimento Automatico (UnitaImmobiliare)

Per l'entità `UnitaImmobiliare`, quando `enable_enrichment=true`:

### Funzionalità

1. **Address Parsing**: Estrae città, provincia, CAP da indirizzo composito
   - Input: `"MILANO (MI) VIALE UMBRIA, 49 Piano 5"`
   - Output: `citta=Milano, provincia=MI, piano=5`

2. **CAP Lookup**: Cerca CAP da database comuni_italia
   - Se città riconosciuta → assegna CAP principale

3. **Codice Generation**: Genera codice univoco `{PROVINCIA}{00001}`
   - Formato: 2 lettere provincia + 5 cifre sequenziali
   - Esempio: `MI00001`, `RM00042`

4. **Categoria Catastale Inference**: Deduce categoria da tipo immobile
   - `Appartamento` → `A/2`
   - `Villa` → `A/8`
   - `Box` → `C/6`

5. **ID-based INSERT/UPDATE**: Se presente colonna `id` con valore, aggiorna record esistente

### Servizi Utilizzati

```python
from app.core.platform_services import AddressNormalizerService
from immobili.services.codice_generator_service import CodiceGeneratorService
from immobili.services.categoria_catastale_service import CategoriaCatastaleService
```

---

## Gestione Errori

### Comportamento con `skip_errors=true` (default)

- Righe invalide vengono saltate
- Import continua con righe valide
- Errori riportati in `error_details`

### Comportamento con `skip_errors=false`

- Primo errore interrompe l'import
- Rollback transazione
- Nessun dato salvato

### Tipi di Errore Comuni

| Errore | Causa | Soluzione |
|--------|-------|-----------|
| `Model not found` | Entità non esiste nel modulo | Verificare nome esatto |
| `Validation failed` | Dati non conformi allo schema | Verificare formato dati |
| `Database commit failed` | Violazione constraint | Verificare unicità/FK |

---

## Esempi Pratici

### Import Completo con Preview

```bash
# 1. Analizza CSV
curl -X POST "http://localhost:8000/api/v1/import-export/analyze?\
module_name=immobili&entity_name=UnitaImmobiliare" \
  -F "file=@data.csv"

# 2. Preview con mapping
curl -X POST "http://localhost:8000/api/v1/import-export/preview?\
module_name=immobili&entity_name=UnitaImmobiliare&\
field_mapping={\"Address\":\"indirizzo\"}" \
  -F "file=@data.csv"

# 3. Import effettivo
curl -X POST "http://localhost:8000/api/v1/import-export/import-with-mapping?\
module_name=immobili&entity_name=UnitaImmobiliare&\
field_mapping={\"Address\":\"indirizzo\"}" \
  -F "file=@data.csv"
```

### Export e Download

```bash
# Export JSON (per elaborazione)
curl "http://localhost:8000/api/v1/import-export/export?\
module_name=immobili&entity_name=UnitaImmobiliare&format=json"

# Download CSV diretto
curl -O "http://localhost:8000/api/v1/import-export/download?\
module_name=immobili&entity_name=UnitaImmobiliare&format=csv&\
fields=codice,indirizzo,citta"

# Download template
curl -O "http://localhost:8000/api/v1/import-export/download-template?\
module_name=immobili&entity_name=UnitaImmobiliare&include_sample=true"
```

---

## Limitazioni Note

1. **Excel Export**: Richiede libreria `openpyxl` (`pip install openpyxl`)
2. **Relazioni**: Non gestisce automaticamente FK - devono essere ID validi
3. **File grandi**: Nessun limite di memoria esplicito - usare batch per file molto grandi
4. **Arricchimento**: Attualmente solo per `UnitaImmobiliare`

---

## Roadmap Future

- [ ] Supporto import Excel nativo
- [ ] Import asincrono per file grandi
- [ ] Webhook notifica completamento
- [ ] Arricchimento estensibile per altri moduli
- [x] UI frontend dedicata per import wizard (ImportButton + ImportWizard)
- [x] ExportButton con menu dropdown

---

## Componenti Frontend

La piattaforma fornisce componenti React riutilizzabili per l'import/export che possono essere integrati in qualsiasi lista entità.

### ImportButton

Bottone che apre un wizard multi-step per l'import.

```jsx
import ImportButton from '../../../../components/Platform/ImportButton';

function UnitaImmobiliariList() {
  const [data, setData] = useState([]);

  const fetchData = async () => {
    const response = await unitaImmobiliariAPI.getAll();
    setData(response.data);
  };

  return (
    <div>
      <div className="toolbar">
        <ImportButton
          moduleName="immobili"
          entityName="UnitaImmobiliare"
          entityLabel="Unità Immobiliari"
          onImportComplete={() => fetchData()}
        />
      </div>
      {/* ... rest of the list */}
    </div>
  );
}
```

**Props:**
| Prop | Tipo | Richiesto | Descrizione |
|------|------|-----------|-------------|
| `moduleName` | string | ✓ | Nome tecnico modulo backend |
| `entityName` | string | ✓ | Nome classe modello SQLAlchemy |
| `entityLabel` | string | - | Etichetta user-friendly |
| `onImportComplete` | function | - | Callback dopo import riuscito |

### ExportButton

Bottone con menu dropdown per export e download template.

```jsx
import ExportButton from '../../../../components/Platform/ExportButton';

function UnitaImmobiliariList() {
  return (
    <div>
      <div className="toolbar">
        <ExportButton
          moduleName="immobili"
          entityName="UnitaImmobiliare"
          entityLabel="Unità Immobiliari"
          fields="codice,indirizzo,citta,provincia"  // opzionale
        />
      </div>
      {/* ... */}
    </div>
  );
}
```

**Props:**
| Prop | Tipo | Richiesto | Descrizione |
|------|------|-----------|-------------|
| `moduleName` | string | ✓ | Nome tecnico modulo backend |
| `entityName` | string | ✓ | Nome classe modello SQLAlchemy |
| `entityLabel` | string | - | Etichetta user-friendly |
| `fields` | string | - | Campi da esportare (comma-separated) |

### Esempio Integrazione Completa

```jsx
import ImportButton from '../../../../components/Platform/ImportButton';
import ExportButton from '../../../../components/Platform/ExportButton';

function EntityList() {
  const [data, setData] = useState([]);

  return (
    <div className="entity-list">
      <div className="toolbar">
        <h2>Unità Immobiliari</h2>
        <div className="toolbar-actions">
          <ImportButton
            moduleName="immobili"
            entityName="UnitaImmobiliare"
            entityLabel="Unità Immobiliari"
            onImportComplete={fetchData}
          />
          <ExportButton
            moduleName="immobili"
            entityName="UnitaImmobiliare"
            entityLabel="Unità Immobiliari"
          />
        </div>
      </div>

      <DataTable data={data} />
    </div>
  );
}
```

### Esempio Reale: Persone Fisiche (anagrafica_italiana)

Integrazione nel file `frontend/src/modules/anagrafica_italiana/components/PersoneFisiche/PersoneFisicheList.jsx`:

```jsx
import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { getSoggettiAnagrafici, deleteSoggetto } from '../../services/anagraficaAPI';
import ImportButton from '../../../../components/Platform/ImportButton';
import ExportButton from '../../../../components/Platform/ExportButton';

function PersoneFisicheList() {
  const [persone, setPersone] = useState([]);

  const loadPersone = async () => {
    const data = await getSoggettiAnagrafici({ limit: 1000 });
    const personeFisiche = data.filter(s => s.tipo_soggetto === 'PERSONA_FISICA');
    setPersone(personeFisiche);
  };

  return (
    <div className="soggetti-list-container">
      <div className="soggetti-list-header">
        <h1>Persone Fisiche</h1>
        <div className="header-actions">
          <input type="text" placeholder="Cerca..." className="search-input" />

          {/* Bottoni Import/Export */}
          <ImportButton
            moduleName="anagrafica_italiana"
            entityName="SoggettoAnagrafico"
            entityLabel="Persone Fisiche"
            onImportComplete={() => loadPersone()}
          />
          <ExportButton
            moduleName="anagrafica_italiana"
            entityName="SoggettoAnagrafico"
            entityLabel="Persone Fisiche"
          />

          <Link to="/anagrafiche/persone-fisiche/nuovo" className="btn btn-primary">
            + Nuova Persona Fisica
          </Link>
        </div>
      </div>
      {/* ... tabella dati ... */}
    </div>
  );
}
```

**Nota**: L'entità è `SoggettoAnagrafico` (non `PersonaFisica`) perché nel modello dati le persone fisiche e giuridiche sono nella stessa tabella, distinte dal campo `tipo_soggetto`.

### API Frontend (importExportAPI)

Il servizio `importExportAPI` in `frontend/src/services/api.js` espone tutti i metodi:

```javascript
import { importExportAPI } from '../services/api';

// Import
importExportAPI.import(moduleName, entityName, file);
importExportAPI.importWithMapping(moduleName, entityName, file, mapping);
importExportAPI.analyzeCSV(moduleName, entityName, file);
importExportAPI.previewImport(moduleName, entityName, file, mapping);

// Export
importExportAPI.export(moduleName, entityName, format, fields);
importExportAPI.downloadExport(moduleName, entityName, format, fields);

// Template
importExportAPI.getTemplate(moduleName, entityName, includeSample);
importExportAPI.downloadTemplate(moduleName, entityName, includeSample);

// Configurazioni salvate
importExportAPI.getImportConfigurations(moduleName, entityName);
importExportAPI.saveImportConfiguration(config);
importExportAPI.deleteImportConfiguration(configId);

// Helper download
importExportAPI.triggerDownload(blob, filename);
```

---

## Multi-Tenancy

L'import/export è completamente **tenant-aware**:

1. Il token JWT include `tenant_schema` dopo la selezione tenant
2. Le API frontend aggiungono automaticamente il token via interceptor axios
3. Il backend applica `SET search_path TO {tenant_schema}` per ogni richiesta
4. I dati importati vanno nel schema del tenant corrente
5. L'export restituisce solo dati del tenant corrente

**Nessuna configurazione aggiuntiva richiesta** - basta usare i componenti e tutto funziona nel contesto tenant corretto.

---

## Riferimenti

- **API Docs**: http://localhost:8000/docs#/Import%2FExport
- **Servizio Core**: `backend/app/core/platform_services/import_export_service.py`
- **Route API**: `backend/app/core/routes/import_export.py`
- **Componenti Frontend**: `frontend/src/components/Platform/Import*.jsx`, `ExportButton.jsx`
- **API Frontend**: `frontend/src/services/api.js` (sezione `importExportAPI`)
- **Test UAT**: `tests/import-automatismi/`
