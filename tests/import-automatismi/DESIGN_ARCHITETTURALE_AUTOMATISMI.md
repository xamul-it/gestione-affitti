# Design Architetturale: Automatismi Import

**Data**: 2025-11-29
**Architetto**: Sistema di Design Architetturale
**Versione**: 1.0
**Riferimento**: Analisi Funzionale v1.0

---

## 1. PRINCIPI ARCHITETTURALI

### 1.1 Design Principles

**🎯 Single Responsibility**: Ogni service ha una responsabilità specifica
**🔌 Dependency Injection**: Services iniettati via costruttore
**⚡ Fail-Safe**: Warning non bloccano operazioni
**📊 Observable**: Logging estensivo per troubleshooting
**🔄 Reversible**: Migration database reversibili
**🧩 Extensible**: Pattern facilmente estendibili

### 1.2 Architectural Patterns

- **Service Layer Pattern**: Business logic isolata in services
- **Repository Pattern**: Data access tramite SQLAlchemy ORM
- **Strategy Pattern**: Normalizzatori indirizzi intercambiabili
- **Factory Pattern**: Generazione codici univoci
- **Observer Pattern**: Logging eventi import

---

## 2. ARCHITETTURA LAYERED

```
┌────────────────────────────────────────────────────────────────┐
│                     PRESENTATION LAYER                         │
│  - Frontend React (ImportWizard)                               │
│  - API REST Endpoints (import_export.py)                       │
└────────────────────────┬───────────────────────────────────────┘
                         │
                         v
┌────────────────────────────────────────────────────────────────┐
│                      SERVICE LAYER                             │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │ ImportExportService (existing)                           │ │
│  │  - orchestrate_import()                                  │ │
│  │  - validate_and_transform()                              │ │
│  └──────────────────────────────────────────────────────────┘ │
│                                                                │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │ AddressNormalizerService (NEW)                           │ │
│  │  - normalize_address()                                   │ │
│  │  - parse_italian_address()                               │ │
│  │  - lookup_cap()                                          │ │
│  └──────────────────────────────────────────────────────────┘ │
│                                                                │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │ CodiceGeneratorService (NEW)                             │ │
│  │  - generate_codice()                                     │ │
│  │  - get_next_progressive()                                │ │
│  └──────────────────────────────────────────────────────────┘ │
│                                                                │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │ CategoriaCatastaleService (NEW)                          │ │
│  │  - infer_categoria()                                     │ │
│  │  - get_or_create_mapping()                               │ │
│  └──────────────────────────────────────────────────────────┘ │
└────────────────────────┬───────────────────────────────────────┘
                         │
                         v
┌────────────────────────────────────────────────────────────────┐
│                     DATA ACCESS LAYER                          │
│  - Models (SQLAlchemy ORM)                                     │
│  - Database Session Management                                 │
│  - Query Builders                                              │
└────────────────────────┬───────────────────────────────────────┘
                         │
                         v
┌────────────────────────────────────────────────────────────────┐
│                      DATABASE LAYER                            │
│  - PostgreSQL                                                  │
│  - Tables: unita_immobiliari, categorie_catastali,            │
│            tipo_immobile_categoria_map, comuni_italia         │
└────────────────────────────────────────────────────────────────┘
```

---

## 3. DATABASE DESIGN

### 3.1 New Tables Schema

#### Table: `categorie_catastali`

```sql
CREATE TABLE categorie_catastali (
    id SERIAL PRIMARY KEY,
    codice VARCHAR(10) NOT NULL UNIQUE,  -- 'A/2', 'C/6', etc.
    nome VARCHAR(200) NOT NULL,
    gruppo VARCHAR(1) NOT NULL,          -- 'A', 'B', 'C', 'D', 'E'
    descrizione TEXT,
    ordinamento INTEGER DEFAULT 0,       -- Per sorting UI
    attiva BOOLEAN DEFAULT TRUE,         -- Soft delete
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE,

    CHECK (gruppo IN ('A', 'B', 'C', 'D', 'E', 'F'))
);

CREATE INDEX idx_categorie_codice ON categorie_catastali(codice);
CREATE INDEX idx_categorie_gruppo ON categorie_catastali(gruppo);
CREATE INDEX idx_categorie_attiva ON categorie_catastali(attiva);
```

#### Table: `tipo_immobile_categoria_map`

```sql
CREATE TABLE tipo_immobile_categoria_map (
    id SERIAL PRIMARY KEY,
    tipo_immobile VARCHAR(100) NOT NULL,
    categoria_catastale_id INTEGER NOT NULL,
    confidence_score DECIMAL(3,2) DEFAULT 1.0,  -- 0.0-1.0 per ML future
    is_user_defined BOOLEAN DEFAULT FALSE,      -- Manual vs auto-inferred
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by VARCHAR(100),                    -- Future user tracking

    FOREIGN KEY (categoria_catastale_id)
        REFERENCES categorie_catastali(id)
        ON DELETE CASCADE,

    UNIQUE (tipo_immobile, categoria_catastale_id)
);

CREATE INDEX idx_tipo_cat_tipo ON tipo_immobile_categoria_map(tipo_immobile);
CREATE INDEX idx_tipo_cat_catid ON tipo_immobile_categoria_map(categoria_catastale_id);
```

#### Table: `comuni_italia` (Reference Data)

```sql
CREATE TABLE comuni_italia (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    nome_normalized VARCHAR(100) NOT NULL,  -- lowercase, no accents
    codice_istat VARCHAR(10) NOT NULL UNIQUE,
    codice_catastale VARCHAR(10),
    cap VARCHAR(10),
    provincia_sigla VARCHAR(2) NOT NULL,
    provincia_nome VARCHAR(100),
    regione VARCHAR(100),
    latitudine DECIMAL(10, 7),
    longitudine DECIMAL(10, 7),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_comuni_nome ON comuni_italia(nome);
CREATE INDEX idx_comuni_nome_norm ON comuni_italia(nome_normalized);
CREATE INDEX idx_comuni_provincia ON comuni_italia(provincia_sigla);
CREATE INDEX idx_comuni_cap ON comuni_italia(cap);
```

#### Alter Table: `unita_immobiliari`

```sql
ALTER TABLE unita_immobiliari
    ADD COLUMN categoria_catastale_id INTEGER,
    ADD COLUMN codice_auto_generated BOOLEAN DEFAULT FALSE,
    ADD COLUMN indirizzo_parsed_warnings TEXT[],  -- Array di warning parsing

    ADD CONSTRAINT fk_unita_categoria
        FOREIGN KEY (categoria_catastale_id)
        REFERENCES categorie_catastali(id)
        ON DELETE SET NULL;

CREATE INDEX idx_unita_categoria ON unita_immobiliari(categoria_catastale_id);
CREATE INDEX idx_unita_codice ON unita_immobiliari(codice);
```

### 3.2 Data Seeding

**Seed Script**: `backend/app/core/seeds/seed_categorie_catastali.py`

```python
CATEGORIE_SEED_DATA = [
    # Gruppo A - Abitazioni
    ('A/1', 'Abitazioni di tipo signorile', 'A'),
    ('A/2', 'Abitazioni di tipo civile', 'A'),
    ('A/3', 'Abitazioni di tipo economico', 'A'),
    ('A/4', 'Abitazioni di tipo popolare', 'A'),
    ('A/5', 'Abitazioni di tipo ultra-popolare', 'A'),
    ('A/6', 'Abitazioni di tipo rurale', 'A'),
    ('A/7', 'Abitazioni in villini', 'A'),
    ('A/8', 'Abitazioni in ville', 'A'),
    ('A/9', 'Castelli, palazzi di eminenti pregi artistici o storici', 'A'),
    ('A/10', 'Uffici e studi privati', 'A'),
    ('A/11', 'Abitazioni ed alloggi tipici dei luoghi', 'A'),

    # Gruppo C - Pertinenze
    ('C/1', 'Negozi e botteghe', 'C'),
    ('C/2', 'Magazzini e locali di deposito', 'C'),
    ('C/3', 'Laboratori per arti e mestieri', 'C'),
    ('C/4', 'Fabbricati e locali per esercizi sportivi', 'C'),
    ('C/5', 'Stabilimenti balneari e di acque curative', 'C'),
    ('C/6', 'Stalle, scuderie, rimesse, autorimesse', 'C'),
    ('C/7', 'Tettoie chiuse o aperte', 'C'),

    # Altri gruppi (parziale)
    ('D/1', 'Opifici', 'D'),
    ('D/8', 'Fabbricati costruiti per speciali esigenze', 'D'),
]
```

---

## 4. SERVICE ARCHITECTURE

### 4.1 AddressNormalizerService

**File**: `backend/app/core/platform_services/address_normalizer_service.py`

```python
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import re
from sqlalchemy.orm import Session

@dataclass
class AddressParseResult:
    """Result of address parsing."""
    indirizzo: Optional[str] = None
    citta: Optional[str] = None
    provincia: Optional[str] = None
    cap: Optional[str] = None
    piano: Optional[str] = None
    warnings: List[str] = None
    success: bool = False

    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []


class AddressNormalizerService:
    """
    Platform service for Italian address normalization.

    Capabilities:
    - Parse composite addresses (e.g., "MILANO (MI) VIA ROMA, 1")
    - Extract city, province, street, CAP
    - Lookup CAP from city/province
    - Fail-safe: warnings don't block import
    """

    # Regex patterns for Italian addresses
    PATTERN_FULL = re.compile(
        r"^([A-Z\s'À-ÿ]+)\s*\(([A-Z]{2})\)\s+(.+?)(?:\s+Piano\s+([^\s,]+))?(?:$|,|\s-)",
        re.IGNORECASE
    )

    PATTERN_SIMPLE = re.compile(
        r"^([A-Za-z\s'À-ÿ]+)\s+(Via|Viale|Corso|Piazza|Largo|Str)\s+([^,]+?),?\s*(\d+)?$",
        re.IGNORECASE
    )

    def __init__(self, db: Session):
        self.db = db

    def normalize_address(
        self,
        raw_address: str,
        existing_citta: str = None,
        existing_provincia: str = None,
        existing_cap: str = None
    ) -> AddressParseResult:
        """
        Main normalization method.

        Args:
            raw_address: Raw address string from CSV
            existing_*: Already populated fields (have priority)

        Returns:
            AddressParseResult with extracted/inferred data
        """
        result = AddressParseResult()

        if not raw_address or raw_address.strip() == '':
            result.warnings.append("Indirizzo vuoto")
            return result

        # Try parsing with patterns
        parsed = self._parse_with_patterns(raw_address)

        # Merge with existing data (existing has priority)
        result.indirizzo = existing_indirizzo if existing_indirizzo else parsed.indirizzo
        result.citta = existing_citta if existing_citta else parsed.citta
        result.provincia = existing_provincia if existing_provincia else parsed.provincia
        result.cap = existing_cap if existing_cap else parsed.cap
        result.piano = parsed.piano

        # Attempt CAP lookup if missing
        if not result.cap and result.citta:
            cap_lookup = self._lookup_cap(result.citta, result.provincia)
            if cap_lookup:
                result.cap = cap_lookup
            else:
                result.warnings.append(
                    f"Impossibile determinare CAP per {result.citta}"
                )

        # Validate provincia
        if result.provincia and len(result.provincia) != 2:
            result.warnings.append(f"Provincia '{result.provincia}' non valida")
            result.provincia = None

        result.success = bool(result.indirizzo or result.citta)
        result.warnings.extend(parsed.warnings)

        return result

    def _parse_with_patterns(self, raw: str) -> AddressParseResult:
        """Try multiple regex patterns."""
        result = AddressParseResult()

        # Pattern 1: Full format "CITTÀ (PROV) VIA X, N Piano Y"
        match = self.PATTERN_FULL.match(raw)
        if match:
            result.citta = self._normalize_city_name(match.group(1))
            result.provincia = match.group(2).upper()
            result.indirizzo = match.group(3).strip()
            result.piano = match.group(4) if match.group(4) else None
            result.success = True
            return result

        # Pattern 2: Simple format "Città Via Nome, Numero"
        match = self.PATTERN_SIMPLE.match(raw)
        if match:
            result.citta = self._normalize_city_name(match.group(1))
            via_type = match.group(2).capitalize()
            via_name = match.group(3).strip()
            numero = match.group(4) if match.group(4) else ""
            result.indirizzo = f"{via_type} {via_name}" + (f", {numero}" if numero else "")
            result.success = True
            return result

        # Fallback: keep original
        result.indirizzo = raw
        result.warnings.append("Formato indirizzo non riconosciuto - mantenuto originale")

        return result

    def _normalize_city_name(self, city: str) -> str:
        """Normalize city name (title case, trim)."""
        return city.strip().title().replace("'", "'")

    def _lookup_cap(self, citta: str, provincia: str = None) -> Optional[str]:
        """
        Lookup CAP from comuni_italia table.

        Args:
            citta: City name
            provincia: Province code (optional, for disambiguation)

        Returns:
            CAP string or None
        """
        from app.modules.affitti_lungo.models import ComuneItalia

        citta_norm = self._normalize_for_lookup(citta)

        query = self.db.query(ComuneItalia).filter(
            ComuneItalia.nome_normalized == citta_norm
        )

        if provincia:
            query = query.filter(ComuneItalia.provincia_sigla == provincia.upper())

        comune = query.first()

        return comune.cap if comune else None

    def _normalize_for_lookup(self, text: str) -> str:
        """Normalize text for database lookup (lowercase, no accents)."""
        import unicodedata
        text = text.lower().strip()
        # Remove accents
        text = ''.join(
            c for c in unicodedata.normalize('NFD', text)
            if unicodedata.category(c) != 'Mn'
        )
        return text
```

---

### 4.2 CodiceGeneratorService

**File**: `backend/app/core/platform_services/codice_generator_service.py`

```python
class CodiceGeneratorService:
    """
    Generate unique codes for UnitaImmobiliare.

    Format: {PROVINCIA_SIGLA}{PROGRESSIVE_5_DIGITS}
    Example: MI00001, BO00042, FO00123
    """

    def __init__(self, db: Session):
        self.db = db

    def generate_codice(
        self,
        provincia: str,
        model_class,
        max_attempts: int = 100
    ) -> str:
        """
        Generate unique codice.

        Args:
            provincia: Province code (2 chars)
            model_class: SQLAlchemy model (e.g., UnitaImmobiliare)
            max_attempts: Max collision resolution attempts

        Returns:
            Unique codice string

        Raises:
            ValueError: If cannot generate unique code after max_attempts
        """
        if not provincia or len(provincia) != 2:
            provincia = "XX"  # Fallback for missing provincia

        sigla = provincia.upper()

        for attempt in range(max_attempts):
            progressive = self._get_next_progressive(sigla, model_class)
            codice = f"{sigla}{progressive:05d}"

            # Check uniqueness
            exists = self.db.query(model_class).filter(
                model_class.codice == codice
            ).first()

            if not exists:
                return codice

        raise ValueError(
            f"Cannot generate unique codice after {max_attempts} attempts"
        )

    def _get_next_progressive(self, sigla: str, model_class) -> int:
        """
        Get next progressive number for given province.

        Query last codice with same sigla, increment by 1.
        """
        last_record = self.db.query(model_class)\
            .filter(model_class.codice.like(f"{sigla}%"))\
            .order_by(model_class.codice.desc())\
            .first()

        if last_record:
            try:
                # Extract number from "MI00042" -> 42
                last_num = int(last_record.codice[2:])
                return last_num + 1
            except (ValueError, IndexError):
                return 1

        return 1  # First record for this provincia
```

---

### 4.3 CategoriaCatastaleService

**File**: `backend/app/core/platform_services/categoria_catastale_service.py`

```python
class CategoriaCatastaleService:
    """
    Infer and manage categoria catastale for immobili.
    """

    # Default mappings
    DEFAULT_TIPO_CATEGORIA = {
        'appartamento': 'A/2',
        'casa': 'A/2',
        'villa': 'A/8',
        'villino': 'A/7',
        'attico': 'A/1',
        'mansarda': 'A/3',
        'box': 'C/6',
        'garage': 'C/6',
        'autorimessa': 'C/6',
        'cantina': 'C/2',
        'magazzino': 'C/2',
        'negozio': 'C/1',
        'ufficio': 'A/10',
        'locale commerciale': 'C/1',
    }

    FALLBACK_CATEGORIA = 'A/2'  # Default generico

    def __init__(self, db: Session):
        self.db = db

    def infer_categoria_id(self, tipo_immobile: str) -> Optional[int]:
        """
        Infer categoria_catastale_id from tipo_immobile text.

        Logic:
        1. Check existing mapping in DB
        2. Try keyword matching with defaults
        3. Return fallback categoria

        Returns:
            categoria_catastale.id or None
        """
        if not tipo_immobile:
            return None

        tipo_normalized = tipo_immobile.lower().strip()

        # 1. Check DB mapping
        mapping = self.db.query(TipoImmobileCategoriaMap).filter(
            TipoImmobileCategoriaMap.tipo_immobile == tipo_normalized
        ).first()

        if mapping:
            return mapping.categoria_catastale_id

        # 2. Try keyword matching
        categoria_code = None

        # Exact match
        if tipo_normalized in self.DEFAULT_TIPO_CATEGORIA:
            categoria_code = self.DEFAULT_TIPO_CATEGORIA[tipo_normalized]
        else:
            # Partial match (contains keyword)
            for keyword, code in self.DEFAULT_TIPO_CATEGORIA.items():
                if keyword in tipo_normalized:
                    categoria_code = code
                    break

        # 3. Fallback
        if not categoria_code:
            categoria_code = self.FALLBACK_CATEGORIA

        # Get categoria_id from code
        categoria = self.db.query(CategoriaCatastale).filter(
            CategoriaCatastale.codice == categoria_code
        ).first()

        if not categoria:
            return None

        # Optionally save mapping for future
        self._save_inferred_mapping(tipo_normalized, categoria.id)

        return categoria.id

    def _save_inferred_mapping(
        self,
        tipo_immobile: str,
        categoria_id: int
    ):
        """Save auto-inferred mapping to DB for future reuse."""
        try:
            mapping = TipoImmobileCategoriaMap(
                tipo_immobile=tipo_immobile,
                categoria_catastale_id=categoria_id,
                confidence_score=0.8,  # Auto-inferred
                is_user_defined=False
            )
            self.db.add(mapping)
            self.db.flush()  # Don't commit here, let caller handle transaction
        except Exception:
            # Ignore duplicates or errors (mapping already exists)
            pass
```

---

## 5. IMPORT FLOW INTEGRATION

### 5.1 Enhanced ImportExportService

**File**: `backend/app/core/platform_services/import_export_service.py`

**New method**:

```python
def import_from_csv_with_enrichment(
    self,
    model: Type[Any],
    csv_data: str,
    field_mapping: Dict[str, str],
    create_schema: Type[Any],
    skip_errors: bool = True,
    enable_updates: bool = True
) -> Dict[str, Any]:
    """
    Enhanced import with automatic enrichment.

    New features:
    - ID-based INSERT vs UPDATE detection
    - Automatic timestamp management
    - Address normalization
    - Codice generation
    - Categoria catastale inference
    """
    # Initialize services
    address_service = AddressNormalizerService(self.db)
    codice_service = CodiceGeneratorService(self.db)
    categoria_service = CategoriaCatastaleService(self.db)

    stats = {
        "success": True,
        "total_rows": 0,
        "created": 0,
        "updated": 0,
        "errors": 0,
        "warnings": [],
        "error_details": []
    }

    # Parse CSV
    csv_data = csv_data.replace('\r\n', '\n').replace('\r', '\n')
    csv_file = io.StringIO(csv_data, newline='')
    reader = csv.DictReader(csv_file)

    for row_num, row in enumerate(reader, start=2):
        stats["total_rows"] += 1

        try:
            # === STEP 1: ID Detection ===
            record_id = row.get('id')
            is_update = record_id and str(record_id).strip() != ''

            if is_update:
                # UPDATE mode: fetch existing record
                existing = self.db.query(model).filter(
                    model.id == int(record_id)
                ).first()

                if not existing:
                    raise ValueError(f"Record ID={record_id} not found")

            # === STEP 2: Field Mapping ===
            mapped_data = {}
            for csv_field, model_field in field_mapping.items():
                if csv_field in row:
                    value = row[csv_field]
                    mapped_data[model_field] = value if value.strip() else None

            # === STEP 3: Address Normalization ===
            if 'indirizzo' in mapped_data:
                address_result = address_service.normalize_address(
                    raw_address=mapped_data.get('indirizzo', ''),
                    existing_citta=mapped_data.get('citta'),
                    existing_provincia=mapped_data.get('provincia'),
                    existing_cap=mapped_data.get('cap')
                )

                if address_result.success:
                    if address_result.indirizzo:
                        mapped_data['indirizzo'] = address_result.indirizzo
                    if address_result.citta:
                        mapped_data['citta'] = address_result.citta
                    if address_result.provincia:
                        mapped_data['provincia'] = address_result.provincia
                    if address_result.cap:
                        mapped_data['cap'] = address_result.cap

                if address_result.warnings:
                    stats["warnings"].append({
                        "row": row_num,
                        "warnings": address_result.warnings
                    })

            # === STEP 4: Codice Generation ===
            if not mapped_data.get('codice') and not is_update:
                provincia = mapped_data.get('provincia', 'XX')
                try:
                    codice = codice_service.generate_codice(provincia, model)
                    mapped_data['codice'] = codice
                    mapped_data['codice_auto_generated'] = True
                except ValueError as e:
                    stats["warnings"].append({
                        "row": row_num,
                        "warnings": [f"Codice generation failed: {str(e)}"]
                    })

            # === STEP 5: Categoria Catastale ===
            if 'tipo' in mapped_data:
                categoria_id = categoria_service.infer_categoria_id(
                    mapped_data['tipo']
                )
                if categoria_id:
                    mapped_data['categoria_catastale_id'] = categoria_id

            # === STEP 6: Timestamps ===
            # Note: handled by SQLAlchemy server_default and onupdate
            # Remove from mapped_data if present
            mapped_data.pop('created_at', None)
            mapped_data.pop('updated_at', None)

            # === STEP 7: Validate with Pydantic ===
            if create_schema:
                validated_data = create_schema(**mapped_data)
                mapped_data = validated_data.model_dump()

            # === STEP 8: Save to DB ===
            if is_update:
                # UPDATE
                for field, value in mapped_data.items():
                    if hasattr(existing, field):
                        setattr(existing, field, value)
                stats["updated"] += 1
            else:
                # INSERT
                db_obj = model(**mapped_data)
                self.db.add(db_obj)
                stats["created"] += 1

        except Exception as e:
            stats["errors"] += 1
            stats["error_details"].append({
                "row": row_num,
                "data": row,
                "error": str(e)
            })

            if not skip_errors:
                stats["success"] = False
                self.db.rollback()
                return stats

    # Commit transaction
    try:
        self.db.commit()
    except Exception as e:
        self.db.rollback()
        stats["success"] = False
        stats["error_details"].append({
            "error": f"Database commit failed: {str(e)}"
        })

    return stats
```

---

## 6. API ENDPOINT UPDATE

**File**: `backend/app/core/routes/import_export.py`

Update `/import-with-mapping` endpoint to use new enrichment:

```python
@router.post("/import-with-mapping", response_model=ImportResult)
async def import_with_mapping(
    file: UploadFile = File(...),
    module_name: str = Query(...),
    entity_name: str = Query(...),
    field_mapping: str = Query(...),
    skip_errors: bool = Query(True),
    enable_updates: bool = Query(True),  # NEW parameter
    # ... other params
):
    """
    Enhanced import with automatic enrichment.

    New features:
    - enable_updates: Allow UPDATE operations via ID field
    """
    # ... existing code for file read, decode, model/schema loading ...

    # Use NEW enriched import method
    service = ImportExportService(db)
    result = service.import_from_csv_with_enrichment(
        model=model_class,
        csv_data=csv_data,
        field_mapping=mapping_dict,
        create_schema=create_schema,
        skip_errors=skip_errors,
        enable_updates=enable_updates  # Pass through
    )

    # Enhanced result includes created/updated counts
    return ImportResult(
        success=result["success"],
        total_rows=result["total_rows"],
        imported=result["created"] + result["updated"],
        created=result.get("created", 0),      # NEW
        updated=result.get("updated", 0),      # NEW
        errors=result["errors"],
        warnings=result.get("warnings", []),   # NEW
        error_details=result["error_details"]
    )
```

---

## 7. DATA MIGRATION STRATEGY

### 7.1 Alembic Migration

**File**: `backend/alembic/versions/xxx_add_categoria_catastale.py`

```python
def upgrade():
    # Create categorie_catastali table
    op.create_table(
        'categorie_catastali',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('codice', sa.String(length=10), nullable=False),
        sa.Column('nome', sa.String(length=200), nullable=False),
        sa.Column('gruppo', sa.String(length=1), nullable=False),
        sa.Column('descrizione', sa.Text(), nullable=True),
        sa.Column('ordinamento', sa.Integer(), server_default='0'),
        sa.Column('attiva', sa.Boolean(), server_default='true'),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), onupdate=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('codice'),
        sa.CheckConstraint("gruppo IN ('A', 'B', 'C', 'D', 'E', 'F')")
    )

    # Create tipo_immobile_categoria_map
    # ... similar pattern ...

    # Create comuni_italia
    # ... similar pattern ...

    # Alter unita_immobiliari
    op.add_column('unita_immobiliari',
        sa.Column('categoria_catastale_id', sa.Integer(), nullable=True)
    )
    op.add_column('unita_immobiliari',
        sa.Column('codice_auto_generated', sa.Boolean(), server_default='false')
    )
    op.add_column('unita_immobiliari',
        sa.Column('indirizzo_parsed_warnings', postgresql.ARRAY(sa.Text()), nullable=True)
    )

    op.create_foreign_key(
        'fk_unita_categoria',
        'unita_immobiliari', 'categorie_catastali',
        ['categoria_catastale_id'], ['id'],
        ondelete='SET NULL'
    )

    # Seed categorie catastali
    from app.core.seeds.seed_categorie_catastali import seed_categorie
    seed_categorie(op.get_bind())


def downgrade():
    op.drop_constraint('fk_unita_categoria', 'unita_immobiliari')
    op.drop_column('unita_immobiliari', 'indirizzo_parsed_warnings')
    op.drop_column('unita_immobiliari', 'codice_auto_generated')
    op.drop_column('unita_immobiliari', 'categoria_catastale_id')

    op.drop_table('tipo_immobile_categoria_map')
    op.drop_table('comuni_italia')
    op.drop_table('categorie_catastali')
```

### 7.2 Comuni Italia Data Load

**Source**: CSV pubblico da ISTAT (8,000+ comuni)
**Script**: `backend/app/core/seeds/load_comuni_italia.py`

```python
import csv

def load_comuni_from_csv(db_session):
    """Load comuni Italia from CSV file."""
    with open('data/comuni_italiani.csv', 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            comune = ComuneItalia(
                nome=row['nome'],
                nome_normalized=normalize_text(row['nome']),
                codice_istat=row['codice_istat'],
                cap=row['cap'],
                provincia_sigla=row['provincia'],
                provincia_nome=row['provincia_nome'],
                regione=row['regione']
            )
            db_session.add(comune)

    db_session.commit()
```

---

## 8. LOGGING & MONITORING

### 8.1 Structured Logging

```python
import logging

logger = logging.getLogger(__name__)

# In AddressNormalizerService
logger.debug(f"Parsing address: {raw_address}")
logger.info(f"Address normalized: {result.citta}, {result.provincia}")
logger.warning(f"CAP not found for {citta}")

# In ImportExportService
logger.info(f"Import started: {total_rows} rows")
logger.info(f"Import complete: {created} created, {updated} updated, {errors} errors")
```

### 8.2 Metrics Collection (Future)

```python
# Prometheus-style metrics (optional)
import_duration_seconds = Histogram('import_duration_seconds')
address_parse_success_rate = Gauge('address_parse_success_rate')
categoria_inference_accuracy = Gauge('categoria_inference_accuracy')
```

---

## 9. TESTING STRATEGY

### 9.1 Unit Tests

```python
# tests/test_address_normalizer.py
def test_parse_full_format():
    service = AddressNormalizerService(db)
    result = service.normalize_address("MILANO (MI) VIALE UMBRIA, 49")

    assert result.citta == "Milano"
    assert result.provincia == "MI"
    assert result.indirizzo == "VIALE UMBRIA, 49"

def test_cap_lookup():
    service = AddressNormalizerService(db)
    cap = service._lookup_cap("Milano", "MI")

    assert cap == "20100"
```

### 9.2 Integration Tests

```python
# tests/test_import_enrichment.py
def test_import_with_auto_enrichment(db, test_csv):
    service = ImportExportService(db)

    result = service.import_from_csv_with_enrichment(
        model=UnitaImmobiliare,
        csv_data=test_csv,
        field_mapping={'indirizzo': 'indirizzo'},
        create_schema=UnitaImmobiliareCreate
    )

    assert result['created'] > 0
    assert result['errors'] == 0

    # Verify enrichment
    immobile = db.query(UnitaImmobiliare).first()
    assert immobile.codice is not None
    assert immobile.categoria_catastale_id is not None
```

---

## 10. PERFORMANCE CONSIDERATIONS

### 10.1 Database Queries

**Optimization**:
- Index on `codice`, `categoria_catastale_id`
- Batch INSERT with flush every 100 records
- Query optimization for progressive lookup

### 10.2 Address Parsing

**Performance**:
- Regex pre-compiled (class-level)
- CAP lookup with index on `nome_normalized`
- Caching comune lookups (LRU cache)

```python
from functools import lru_cache

@lru_cache(maxsize=1000)
def _lookup_cap_cached(self, citta_norm: str, provincia: str) -> Optional[str]:
    # Same logic but cached
    pass
```

### 10.3 Bulk Import Optimization

```python
# Bulk insert with executemany
def bulk_insert_optimized(records: List[dict]):
    # Use Core insert instead of ORM for speed
    from sqlalchemy import insert

    stmt = insert(UnitaImmobiliare).values(records)
    db.execute(stmt)
```

---

## 11. SECURITY CONSIDERATIONS

### 11.1 Input Validation

- ✅ CSV size limit: 10 MB
- ✅ Row limit: 10,000 rows
- ✅ Regex timeout: 1 second per address
- ✅ SQL injection: Parameterized queries only

### 11.2 Data Privacy

- ✅ Personal data in addresses: handled as per GDPR
- ✅ Logging: No PII in logs (anonymize addresses)

---

## 12. ROLLOUT PLAN

### Phase 1: Database (Week 1)
1. Create migration
2. Run migration in DEV
3. Seed categorie catastali
4. Load comuni Italia data

### Phase 2: Services (Week 1-2)
5. Implement AddressNormalizerService
6. Implement CodiceGeneratorService
7. Implement CategoriaCatastaleService
8. Unit tests

### Phase 3: Integration (Week 2)
9. Update ImportExportService
10. Update API endpoint
11. Integration tests

### Phase 4: Testing (Week 2)
12. Test with provided CSV
13. UAT with real data
14. Performance testing

### Phase 5: Deploy (Week 3)
15. Deploy to staging
16. Final UAT
17. Deploy to production

---

## 13. SUCCESS METRICS

- ✅ Import success rate: > 95%
- ✅ Address parse success: > 80%
- ✅ CAP inference accuracy: > 90%
- ✅ Categoria inference accuracy: > 85%
- ✅ Import speed: < 3 sec per 100 records

---

**End of Architectural Design**

**Next Step**: Implementation

