# Analisi Funzionale: Automatismi Import Unità Immobiliari

**Data**: 2025-11-29
**Analista**: Sistema di Analisi Tecnico-Funzionale
**Versione**: 1.0

---

## 1. CONTESTO

L'utente ha caricato un file CSV di esempio (`/tmp/UnitaImmobiliare_import_template.csv`) e ha riscontrato diversi errori durante l'importazione. È necessario implementare automatismi intelligenti per:

1. Gestione campi ID (nuovo record vs aggiornamento)
2. Gestione timestamp automatici
3. Generazione codice univoco immobile
4. Normalizzazione indirizzi con parsing intelligente
5. Gestione categorie catastali

---

## 2. ANALISI FILE CSV DI ESEMPIO

### 2.1 Struttura Rilevata

Il file contiene **14 record** con la seguente struttura:

```csv
codice,tipo,condominio_id,indirizzo,citta,cap,provincia,superficie_mq,locali,piano,
classe_energetica,rendita_catastale,foglio,particella,subalterno,descrizione,note,
created_at,updated_at
```

### 2.2 Problematiche Rilevate

#### A) Indirizzi Non Normalizzati
Gli indirizzi sono forniti in formato compatto misto:

**Esempi**:
- `"MILANO (MI) VIALE UMBRIA, 49 Piano 5-S1 - 7 int. 23"`
- `"BOLOGNA (BO) VIA EMILIA PONENTE, 354 Piano S1-1"`
- `"FORLI' (FO) VIA LUGHESE, 97 Piano T-1"`
- `"Milano Cadore 45"` (formato semplificato)

**Pattern identificati**:
1. **Formato completo**: `CITTÀ (PROVINCIA) VIA NOME, NUMERO Piano X`
2. **Formato semplificato**: `Città Via Numero`
3. **Informazioni mancanti**: CAP spesso vuoto

#### B) Campi Vuoti o Non Valorizzati
- `id`: Non presente nel CSV (colonna mancante)
- `codice`: Vuoto nella maggior parte dei record
- `cap`: Vuoto in 13 record su 14
- `provincia`: Vuoto o generico ("example text")
- `created_at/updated_at`: Vuoti o con formato inconsistente ("01-01-24")

#### C) Tipo Immobile Libero
Valori trovati:
- Standard: `Appartamento`, `Box`, `Casa`
- Non standard: `Cavalcavia`, `Toro`, `Casina`, `Rudere`
- Con descrizione: `Box pertinenza Cadore`, `Box prima casa`

**Osservazione**: Non esiste mappatura a categorie catastali ufficiali.

---

## 3. REQUISITI FUNZIONALI DETTAGLIATI

### RF-001: Gestione ID Record

**Priorità**: ALTA

**Requisito**:
- Se campo `id` è **vuoto o non presente**: → Nuovo record da creare
- Se campo `id` è **valorizzato**: → Aggiornamento record esistente

**Comportamento atteso**:
```python
if record.get('id') is None or record.get('id') == '':
    # INSERT: Crea nuovo record
    # ID generato automaticamente da database (SERIAL/AUTO_INCREMENT)
else:
    # UPDATE: Aggiorna record esistente con ID specificato
    # Verifica esistenza record con ID
    # Se non esiste → Errore: "Record ID={id} non trovato"
```

**Validazioni**:
- ID deve essere numero intero positivo se fornito
- ID deve esistere nel database per operazioni di UPDATE
- Impossibile aggiornare record inesistente

**Messaggi Errore**:
- `"ID non valido: deve essere un numero intero positivo"`
- `"Record con ID={id} non trovato per aggiornamento"`

---

### RF-002: Gestione Timestamp Automatici

**Priorità**: ALTA

**Requisito**:
- `created_at`: Valorizzato automaticamente alla creazione
- `updated_at`: Valorizzato automaticamente a ogni modifica

**Comportamento atteso**:

**Scenario 1: Nuovo Record (INSERT)**
```python
if is_new_record:
    created_at = datetime.now(timezone.utc)
    updated_at = datetime.now(timezone.utc)
```

**Scenario 2: Aggiornamento Record (UPDATE)**
```python
if is_update:
    # created_at NON viene modificato (mantiene valore originale)
    updated_at = datetime.now(timezone.utc)
```

**Regole**:
1. Valori forniti nel CSV per `created_at/updated_at` vengono **IGNORATI**
2. Timestamp sempre in **UTC**
3. Formato database: `timestamp with timezone`
4. `created_at` è immutabile dopo creazione

**Note implementative**:
- Usare `server_default=func.now()` in SQLAlchemy per `created_at`
- Usare `onupdate=func.now()` per `updated_at`
- CSV non deve includere questi campi (opzionale)

---

### RF-003: Generazione Codice Univoco Immobile

**Priorità**: ALTA

**Requisito**:
Se campo `codice` è vuoto, generare automaticamente usando convenzione:
**`{SIGLA_PROVINCIA}{PROGRESSIVO_5_CIFRE}`**

**Formato**: `MI00001`, `BO00042`, `FO00003`

**Algoritmo**:

```python
def generate_codice(provincia: str, db_session) -> str:
    """
    Genera codice univoco immobile.

    Args:
        provincia: Sigla provincia (es. "MI", "BO", "FO")
        db_session: Sessione database per verificare univocità

    Returns:
        Codice formato: {PROVINCIA}{PROGRESSIVO_5_CIFRE}
    """
    # 1. Normalizza sigla provincia (uppercase, 2 caratteri)
    sigla = normalize_provincia_code(provincia)

    # 2. Query ultimo progressivo per provincia
    last_code = db_session.query(UnitaImmobiliare)\
        .filter(UnitaImmobiliare.codice.like(f"{sigla}%"))\
        .order_by(UnitaImmobiliare.codice.desc())\
        .first()

    # 3. Calcola nuovo progressivo
    if last_code:
        last_number = int(last_code.codice[2:])  # Estrai numero da "MI00042"
        new_number = last_number + 1
    else:
        new_number = 1

    # 4. Formatta con zero-padding
    codice = f"{sigla}{new_number:05d}"

    return codice
```

**Esempi**:
- Milano, primo record: `MI00001`
- Bologna, 42° record: `BO00042`
- Forlì, primo record: `FO00001`

**Validazioni**:
- Sigla provincia deve essere valida (2 caratteri)
- Codice deve essere univoco nel database
- Se provincia mancante, usa `"XX"` come fallback

**Gestione Conflitti**:
- Se codice generato già esistente → Incrementa fino a trovare libero
- Max tentativi: 100 (poi errore)

---

### RF-004: Normalizzatore Indirizzi Intelligente

**Priorità**: CRITICA

**Requisito**:
Quando `indirizzo` contiene informazioni miste (città, provincia, via, CAP), il normalizzatore deve:
1. **Estrarre** automaticamente: `indirizzo`, `citta`, `provincia`, `cap`
2. **Popolare** i campi separati se vuoti
3. **Generare WARNING** se estrazione fallisce (ma importare comunque)

**Input Format Supportati**:

**Formato 1: Completo**
```
Input:  "MILANO (MI) VIALE UMBRIA, 49 Piano 5-S1 - 7 int. 23"
Output:
  - indirizzo: "VIALE UMBRIA, 49"
  - citta: "Milano"
  - provincia: "MI"
  - cap: "20100" (calcolato via lookup)
  - piano: "5" (estratto da "Piano 5-S1")
```

**Formato 2: Semplificato**
```
Input:  "Milano Cadore 45"
Output:
  - indirizzo: "Via Cadore, 45"
  - citta: "Milano"
  - provincia: "MI" (lookup da città)
  - cap: Tentativo calcolo, se fallisce → NULL + warning
```

**Formato 3: Bologna Style**
```
Input:  "BOLOGNA (BO) VIA EMILIA PONENTE, 354 Piano T-1"
Output:
  - indirizzo: "VIA EMILIA PONENTE, 354"
  - citta: "Bologna"
  - provincia: "BO"
  - cap: "40100" (lookup)
  - piano: "T-1"
```

#### 4.1 Algoritmo di Parsing

**Step 1: Regex Pattern Matching**

```python
import re

def parse_indirizzo_completo(raw_address: str) -> dict:
    """
    Parse indirizzo con pattern recognition.

    Returns dict con chiavi: indirizzo, citta, provincia, cap, piano
    """
    result = {
        'indirizzo': None,
        'citta': None,
        'provincia': None,
        'cap': None,
        'piano': None,
        'warnings': []
    }

    # Pattern 1: "CITTÀ (PROVINCIA) VIA NOME, NUMERO Piano X"
    pattern1 = r"^([A-Z\s']+)\s*\(([A-Z]{2})\)\s+(.+?)\s+Piano\s+(.+?)(?:\s|$)"
    match = re.match(pattern1, raw_address, re.IGNORECASE)

    if match:
        result['citta'] = match.group(1).strip().title()
        result['provincia'] = match.group(2).upper()
        result['indirizzo'] = match.group(3).strip()
        result['piano'] = match.group(4).strip()
        return result

    # Pattern 2: "Città Via Numero"
    pattern2 = r"^([A-Za-z\s']+)\s+([A-Za-z\s]+)\s+(\d+)"
    match = re.match(pattern2, raw_address)

    if match:
        result['citta'] = match.group(1).strip().title()
        via = match.group(2).strip()
        numero = match.group(3)
        result['indirizzo'] = f"Via {via}, {numero}"
        result['warnings'].append("Formato semplificato: provincia e CAP da verificare")
        return result

    # Fallback: mantieni originale
    result['indirizzo'] = raw_address
    result['warnings'].append("Impossibile parsare indirizzo, mantenuto formato originale")

    return result
```

#### 4.2 Lookup CAP da Città/Provincia

**Database Lookup Interno** (nessuna API esterna):

```python
# Dizionario città → CAP principali italiani
CITTA_CAP_MAP = {
    'milano': '20100',
    'roma': '00100',
    'bologna': '40100',
    'torino': '10100',
    'firenze': '50100',
    'napoli': '80100',
    'venezia': '30100',
    'genova': '16100',
    'palermo': '90100',
    'forli': '47100',
    'cesena': '47521',
    # ... estendibile
}

def get_cap_from_citta(citta: str) -> str | None:
    """Lookup CAP da nome città."""
    citta_normalized = citta.lower().strip()
    return CITTA_CAP_MAP.get(citta_normalized)
```

**Alternativa**: Usare API pubblica gratuita **comuni-italiani.it** (no key required)

```python
import requests

def get_cap_from_api(citta: str, provincia: str = None) -> str | None:
    """
    Query API comuni italiani (gratuita, no auth).

    API: https://comuni-ita.herokuapp.com/api/comuni/nome/{nome}
    """
    try:
        url = f"https://comuni-ita.herokuapp.com/api/comuni/nome/{citta}"
        response = requests.get(url, timeout=5)

        if response.status_code == 200:
            data = response.json()
            if data and len(data) > 0:
                # Se provincia specificata, filtra
                if provincia:
                    for comune in data:
                        if comune.get('sigla') == provincia.upper():
                            return comune.get('cap')

                # Altrimenti prendi primo risultato
                return data[0].get('cap')

        return None
    except Exception as e:
        # Fallback silenzioso
        return None
```

#### 4.3 Gestione Conflitti Campi

**Regola di Merge**:

Se campo già valorizzato nel CSV **E** estratto dal parser:

1. **Campo CSV ha priorità** (non sovrascrivere)
2. **Se campo CSV vuoto** → Usa valore estratto
3. **Genera INFO log** per tracking

```python
def merge_parsed_address(csv_data: dict, parsed: dict) -> dict:
    """
    Merge dati CSV con dati parsati.

    Priorità: CSV > Parsed
    """
    result = csv_data.copy()

    for field in ['indirizzo', 'citta', 'provincia', 'cap']:
        csv_value = csv_data.get(field)
        parsed_value = parsed.get(field)

        if not csv_value or csv_value.strip() == '':
            if parsed_value:
                result[field] = parsed_value
                result.setdefault('_info', []).append(
                    f"{field} estratto da indirizzo: {parsed_value}"
                )

    return result
```

#### 4.4 Warning vs Error

**WARNING** (importazione continua):
- Impossibile estrarre CAP
- Formato indirizzo non riconosciuto
- Città non trovata in lookup

**Messaggio warning**:
```
"⚠️ Riga {N}: Impossibile calcolare CAP per città '{citta}' - record importato senza CAP"
```

**ERROR** (blocca importazione della riga):
- Indirizzo completamente vuoto
- Campi obbligatori mancanti (es. rendita_catastale se required)

---

### RF-005: Tabella Categorie Catastali

**Priorità**: MEDIA

**Requisito**:
Creare associazione `tipo_immobile` (testo libero) → `categoria_catastale` (codice ufficiale).

#### 5.1 Categorie Catastali Ufficiali (Agenzia Entrate)

**Gruppo A - Abitazioni**:
- A/1: Abitazioni signorili
- A/2: Abitazioni civili
- A/3: Abitazioni economiche
- A/4: Abitazioni popolari
- A/5: Abitazioni ultra-popolari
- A/6: Abitazioni rurali
- A/7: Villini
- A/8: Ville
- A/9: Castelli e palazzi storici
- A/10: Uffici e studi privati
- A/11: Abitazioni tipiche dei luoghi

**Gruppo C - Pertinenze**:
- C/1: Negozi e botteghe
- C/2: Magazzini e locali di deposito
- C/3: Laboratori per arti e mestieri
- C/4: Fabbricati per esercizi sportivi
- C/5: Stabilimenti balneari
- C/6: Autorimesse (box)
- C/7: Tettoie

**Altri Gruppi**: B (uso pubblico), D (immobili speciali), E (categorie speciali)

#### 5.2 Database Schema

**Nuova Tabella: `categorie_catastali`**

```sql
CREATE TABLE categorie_catastali (
    id SERIAL PRIMARY KEY,
    codice VARCHAR(10) NOT NULL UNIQUE,  -- es. "A/2", "C/6"
    nome VARCHAR(200) NOT NULL,           -- es. "Abitazioni civili"
    gruppo VARCHAR(1) NOT NULL,           -- 'A', 'B', 'C', 'D', 'E'
    descrizione TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP
);

-- Indici
CREATE INDEX idx_cat_codice ON categorie_catastali(codice);
CREATE INDEX idx_cat_gruppo ON categorie_catastali(gruppo);
```

**Tabella Associazione: `tipo_immobile_categoria_map`**

```sql
CREATE TABLE tipo_immobile_categoria_map (
    id SERIAL PRIMARY KEY,
    tipo_immobile VARCHAR(100) NOT NULL,         -- Testo libero utente
    categoria_catastale_id INTEGER NOT NULL,     -- FK a categorie_catastali
    is_default BOOLEAN DEFAULT FALSE,            -- Mapping di default
    created_at TIMESTAMP DEFAULT NOW(),

    FOREIGN KEY (categoria_catastale_id)
        REFERENCES categorie_catastali(id) ON DELETE CASCADE,

    UNIQUE (tipo_immobile, categoria_catastale_id)
);

CREATE INDEX idx_tipo_cat ON tipo_immobile_categoria_map(tipo_immobile);
```

#### 5.3 Mapping Automatico Suggerito

**Logica Default**:

```python
DEFAULT_TIPO_CATEGORIA_MAP = {
    # Abitazioni → A/2 (Abitazioni civili)
    'appartamento': 'A/2',
    'casa': 'A/2',
    'villa': 'A/8',
    'villino': 'A/7',
    'mansarda': 'A/3',
    'attico': 'A/1',

    # Pertinenze → C/6 (Box)
    'box': 'C/6',
    'garage': 'C/6',
    'autorimessa': 'C/6',
    'box pertinenza': 'C/6',
    'box prima casa': 'C/6',

    # Altro
    'magazzino': 'C/2',
    'cantina': 'C/2',
    'negozio': 'C/1',
    'ufficio': 'A/10',

    # Fallback per non riconosciuti
    '*': 'A/2'  # Default generico
}

def infer_categoria_catastale(tipo_immobile: str) -> str:
    """
    Inferisci categoria catastale da tipo immobile.

    Args:
        tipo_immobile: Descrizione libera (es. "Box pertinenza Cadore")

    Returns:
        Codice categoria (es. "C/6")
    """
    tipo_normalized = tipo_immobile.lower().strip()

    # Exact match
    if tipo_normalized in DEFAULT_TIPO_CATEGORIA_MAP:
        return DEFAULT_TIPO_CATEGORIA_MAP[tipo_normalized]

    # Partial match (contains keyword)
    for keyword, categoria in DEFAULT_TIPO_CATEGORIA_MAP.items():
        if keyword in tipo_normalized:
            return categoria

    # Fallback
    return DEFAULT_TIPO_CATEGORIA_MAP['*']
```

#### 5.4 Modifica Schema `UnitaImmobiliare`

**Aggiungere campo**:

```python
class UnitaImmobiliare(Base):
    # ... campi esistenti ...

    tipo = Column(String(100))  # Testo libero

    # NUOVO CAMPO
    categoria_catastale_id = Column(
        Integer,
        ForeignKey('categorie_catastali.id'),
        nullable=True  # Opzionale per retrocompatibilità
    )

    # RELATIONSHIP
    categoria_catastale = relationship(
        "CategoriaCatastale",
        backref="unita_immobiliari"
    )
```

**Durante import**:

```python
# 1. Cerca mapping esistente
mapping = db.query(TipoImmobileCategoriaMap)\
    .filter_by(tipo_immobile=tipo_from_csv)\
    .first()

if mapping:
    categoria_id = mapping.categoria_catastale_id
else:
    # 2. Inferisci automaticamente
    categoria_code = infer_categoria_catastale(tipo_from_csv)
    categoria = db.query(CategoriaCatastale)\
        .filter_by(codice=categoria_code)\
        .first()

    categoria_id = categoria.id if categoria else None

# 3. Assegna al record
unita_immobiliare.categoria_catastale_id = categoria_id
```

---

## 4. RIEPILOGO AUTOMATISMI

| # | Automatismo | Input | Output | Priorità |
|---|-------------|-------|--------|----------|
| 1 | **ID Management** | `id` vuoto → INSERT<br>`id` valorizzato → UPDATE | Nuovo record o aggiornamento | ALTA |
| 2 | **Timestamp Auto** | `created_at`, `updated_at` ignorati da CSV | Timestamp UTC automatici | ALTA |
| 3 | **Codice Generato** | `codice` vuoto | `{PROVINCIA}{00001}` | ALTA |
| 4 | **Parse Indirizzo** | `"MILANO (MI) VIA X, 1"` | `citta="Milano"`, `provincia="MI"`, `cap="20100"` | CRITICA |
| 5 | **Categoria Catastale** | `tipo="Appartamento"` | `categoria_catastale_id → A/2` | MEDIA |

---

## 5. FLUSSO DI IMPORT MODIFICATO

```
┌─────────────────┐
│ CSV Upload      │
└────────┬────────┘
         │
         v
┌─────────────────────────────────────────┐
│ Per ogni riga:                          │
│                                         │
│ 1. CHECK ID                             │
│    - vuoto? → INSERT mode               │
│    - valorizzato? → UPDATE mode         │
│                                         │
│ 2. NORMALIZZA INDIRIZZO                 │
│    - Parse formato completo             │
│    - Estrai: città, provincia, CAP      │
│    - Se fallisce → Warning, continua    │
│                                         │
│ 3. GENERA CODICE (se vuoto)            │
│    - Calcola: {PROVINCIA}{PROGR}        │
│    - Verifica univocità                 │
│                                         │
│ 4. INFERISCI CATEGORIA CATASTALE        │
│    - Match tipo → categoria             │
│    - Crea FK a categoria_catastale_id   │
│                                         │
│ 5. SET TIMESTAMP AUTOMATICI             │
│    - INSERT: created_at + updated_at    │
│    - UPDATE: solo updated_at            │
│                                         │
│ 6. VALIDAZIONE PYDANTIC                 │
│    - Schema con required fields         │
│                                         │
│ 7. SAVE TO DB                           │
│    - INSERT o UPDATE                    │
│    - Commit transazione                 │
│                                         │
└─────────────────────────────────────────┘
         │
         v
┌─────────────────┐
│ Import Report   │
│ - N created     │
│ - N updated     │
│ - N warnings    │
│ - N errors      │
└─────────────────┘
```

---

## 6. NON-FUNCTIONAL REQUIREMENTS

### 6.1 Performance
- Import fino a 10,000 record: < 30 secondi
- Normalizzazione indirizzo: < 100ms per record
- API lookup CAP: timeout 5 secondi, fallback silenzioso

### 6.2 Affidabilità
- Warning NON bloccano import
- Errori validation bloccano singola riga (modalità skip errors)
- Transazioni DB atomiche

### 6.3 Logging
- Log ogni parsing indirizzo (debug)
- Log warning per campi non estratti
- Log info per codici generati

### 6.4 Estensibilità
- Mapping tipo→categoria configurabile via DB
- Pattern regex indirizzi estendibili
- Dizionario CAP città espandibile

---

## 7. SERVIZI ESTERNI RICHIESTI

### 7.1 API Comuni Italiani (Opzionale)

**URL**: `https://comuni-ita.herokuapp.com`
**Auth**: Nessuna (API pubblica)
**Cost**: Gratuita
**Limits**: Nessun rate limit dichiarato
**Uso**: Lookup CAP da città

**Endpoint**:
```
GET /api/comuni/nome/{nome_comune}

Response:
[
  {
    "nome": "Milano",
    "sigla": "MI",
    "codice": "015146",
    "cap": "20100",
    "regione": "Lombardia"
  }
]
```

**Alternativa**: Database statico di 8,000 comuni italiani (incluso nel progetto)

### 7.2 Nessun Servizio a Pagamento
✅ Tutti i requisiti sono implementabili senza servizi a pagamento

---

## 8. ACCEPTANCE CRITERIA

### Test Case 1: Import Nuovo Record
```
Input CSV:
  codice=,tipo=Appartamento,indirizzo="MILANO (MI) VIA ROMA, 1"

Expected:
  ✓ id generato da DB
  ✓ codice = "MI00001"
  ✓ citta = "Milano"
  ✓ provincia = "MI"
  ✓ cap = "20100"
  ✓ categoria_catastale_id → A/2
  ✓ created_at = now()
  ✓ updated_at = now()
```

### Test Case 2: Update Record Esistente
```
Input CSV:
  id=42,tipo=Casa,indirizzo="BOLOGNA (BO) VIA VERDI, 10"

Expected:
  ✓ Record ID=42 aggiornato
  ✓ created_at NON modificato
  ✓ updated_at = now()
  ✓ Altri campi aggiornati
```

### Test Case 3: Indirizzo Non Parsabile + Warning
```
Input CSV:
  codice=,indirizzo="Via senza info complete"

Expected:
  ✓ Record importato
  ⚠️ Warning: "Impossibile estrarre CAP"
  ✓ cap = NULL
  ✓ Import NON bloccato
```

### Test Case 4: Tipo Non Mappato
```
Input CSV:
  tipo="Toro" (tipo custom non riconosciuto)

Expected:
  ✓ Record importato
  ✓ categoria_catastale_id → A/2 (fallback default)
  ℹ️ Info: "Categoria inferita: A/2 (default)"
```

---

## 9. IMPATTO SU SISTEMA ESISTENTE

### 9.1 Database Migration
- ✅ Nuova tabella: `categorie_catastali`
- ✅ Nuova tabella: `tipo_immobile_categoria_map`
- ✅ Modifica tabella: `unita_immobiliari` (+1 FK)

### 9.2 Backend Service
- ✅ Nuovi metodi in `ImportExportService`
- ✅ Nuovo service: `AddressNormalizerService`
- ✅ Logica UPDATE oltre INSERT

### 9.3 API Endpoints
- ✅ Nessuna modifica API pubblica
- ✅ Import endpoint gestisce automatismi trasparentemente

### 9.4 Frontend
- ✅ Nessuna modifica necessaria
- ✅ Warning mostrati nel report import

---

## 10. STIMA EFFORT

| Task | Effort | Priorità |
|------|--------|----------|
| DB migration + seed categorie | 2h | Alta |
| AddressNormalizer service | 4h | Critica |
| ID/Timestamp automatismi | 2h | Alta |
| Codice generator | 2h | Alta |
| Categoria catastale logic | 3h | Media |
| Testing + validation | 3h | Alta |
| **TOTALE** | **16h** | - |

---

## 11. RACCOMANDAZIONI

1. **Iniziare con AddressNormalizer** (blocco critico)
2. **Database CAP statico** preferibile ad API esterna (affidabilità)
3. **Logging estensivo** per debug normalizzazioni
4. **UI feedback** chiaro per warning (non errori)
5. **Migration reversibile** per categorie catastali

---

**Fine Analisi Funzionale**

---

**Approvazione**:
- [ ] Analista Funzionale
- [ ] Architetto Software
- [ ] Product Owner

**Prossimo Step**: Design Architetturale
