# Migrazione a Soggetti Anagrafici Centralizzati

## ✅ COMPLETATO

Data: 2025-12-02

## Obiettivo

Centralizzare i dati anagrafici di proprietari, affittuari e tecnici in una unica tabella `soggetti_anagrafici`, eliminando la duplicazione dei dati e permettendo a un soggetto di avere più ruoli contemporaneamente.

## Architettura Implementata

### Prima (❌ Duplicazione)
```
proprietari (nome, cognome, CF, email, telefono, indirizzo...)
affittuari (nome, cognome, CF, email, telefono, indirizzo...)
tecnici (nome, cognome, CF/P.IVA, email, telefono, indirizzo...)
```

### Dopo (✅ Centralizzato)
```
soggetti_anagrafici (dati anagrafici completi)
    ↓ soggetto_id
proprietari (solo campi specifici: note_proprietario)
affittuari (solo campi specifici: note_affittuario)
tecnici (solo campi specifici: specializzazione, albo, note_tecnico)
```

## Vantaggi

1. **✅ No Duplicazione**: Ogni soggetto memorizzato una sola volta
2. **✅ Multi-Ruolo**: Un soggetto può essere proprietario+affittuario+tecnico
3. **✅ Integrità Dati**: Aggiornamento centralizzato (es. cambio telefono)
4. **✅ Estensibilità**: Nuovi moduli possono aggiungere ruoli
5. **✅ Storicità**: Tracciare assunzione/rimozione ruoli

## File Creati/Modificati

### Core Platform
- ✅ `/backend/app/core/models/soggetto_anagrafico.py` - Modello SoggettoAnagrafico
- ✅ `/backend/app/core/models/__init__.py` - Export del modello
- ✅ `/backend/app/main.py` - Import del modello

### Migrazione
- ✅ `/backend/migrations/migrate_to_soggetti_anagrafici.py` - Script di migrazione completo

### Moduli (Refactored)
- ✅ `/backend/app/modules/affitti_lungo/models/proprietari.py` - Usa soggetto_id
- ✅ `/backend/app/modules/affitti_lungo/models/affittuari.py` - Usa soggetto_id
- ✅ `/backend/app/modules/affitti_lungo/models/tecnici.py` - Usa soggetto_id

## Risultati Migrazione

```
✅ Tabella soggetti_anagrafici creata
✅ 10 soggetti anagrafici totali
✅ 3/3 proprietari collegati
✅ 4/4 affittuari collegati
✅ 2/3 tecnici collegati (1 senza CF/P.IVA)
```

### Distribuzione Ruoli
```
ID  | Nome                | Proprietario | Affittuario | Tecnico
----|---------------------|--------------|-------------|--------
1   | Giuseppe Verdi      | ✓            |             |
2   | Laura Bianchi       | ✓            |             |
3   | Franco Neri         | ✓            |             |
4   | Marco Rossi         |              | ✓           |
5   | Marco Rossi         |              | ✓           |
6   | Elena Ferrari       |              | ✓           |
7   | Ristorante Da Mario |              | ✓           |
8   | Mario Rossi         |              |             |
9   | Mario Bianchi       |              |             | ✓
10  | Luigi Verdi         |              |             | ✓
```

## Compatibilità Retro

I modelli mantengono i campi deprecati per garantire compatibilità durante la transizione:

```python
# DEPRECATED FIELDS - saranno rimossi nella prossima versione
nome = Column(String(100), nullable=True)  # DEPRECATED: use soggetto.nome
cognome = Column(String(100), nullable=True)  # DEPRECATED: use soggetto.cognome
codice_fiscale = Column(String(16), nullable=True)  # DEPRECATED: use soggetto.codice_fiscale
# ... etc
```

**Attenzione**: Questi campi sono ora READONLY per retrocompatibilità. Tutti i nuovi sviluppi devono usare `soggetto.*`

## Prossimi Step

### 1. Aggiornare API Routes e Schemas ⏳

Le API attuali continuano a funzionare grazie ai campi deprecati, ma vanno aggiornate per usare la nuova struttura:

#### Esempio Proprietari

**Prima:**
```python
# Schema
class ProprietarioCreate(BaseModel):
    nome: str
    cognome: str
    codice_fiscale: str
    email: Optional[str]
    telefono: Optional[str]
    # ... altri campi anagrafici

# Route
@router.post("/")
def create_proprietario(proprietario: ProprietarioCreate, db: Session = Depends(get_db)):
    db_prop = Proprietario(**proprietario.dict())
    db.add(db_prop)
    db.commit()
    return db_prop
```

**Dopo:**
```python
# Schema
class SoggettoAnagra ficoCreate(BaseModel):
    tipo_soggetto: TipoSoggetto
    codice_fiscale: Optional[str]
    nome: Optional[str]
    cognome: Optional[str]
    email: Optional[str]
    telefono: Optional[str]
    # ... altri campi anagrafici

class ProprietarioCreate(BaseModel):
    soggetto_id: Optional[int]  # Se esiste già
    soggetto: Optional[SoggettoAnagra ficoCreate]  # Se nuovo
    note_proprietario: Optional[str]

# Route
@router.post("/")
def create_proprietario(proprietario: ProprietarioCreate, db: Session = Depends(get_db)):
    # Se soggetto_id fornito, usa quello esistente
    if proprietario.soggetto_id:
        soggetto_id = proprietario.soggetto_id
    # Altrimenti crea nuovo soggetto
    else:
        soggetto = SoggettoAnagrafico(**proprietario.soggetto.dict())
        db.add(soggetto)
        db.flush()
        soggetto_id = soggetto.id

    # Crea proprietario con solo campi specifici
    db_prop = Proprietario(
        soggetto_id=soggetto_id,
        note_proprietario=proprietario.note_proprietario
    )
    db.add(db_prop)
    db.commit()
    db.refresh(db_prop)
    return db_prop

# Response deve includere soggetto tramite relationship
@router.get("/{id}")
def get_proprietario(id: int, db: Session = Depends(get_db)):
    prop = db.query(Proprietario).options(
        joinedload(Proprietario.soggetto)
    ).filter(Proprietario.id == id).first()

    if not prop:
        raise HTTPException(404)

    return {
        "id": prop.id,
        "soggetto_id": prop.soggetto_id,
        "soggetto": {
            "nome": prop.soggetto.nome,
            "cognome": prop.soggetto.cognome,
            "codice_fiscale": prop.soggetto.codice_fiscale,
            # ... altri campi soggetto
        },
        "note_proprietario": prop.note_proprietario
    }
```

### 2. Aggiornare Frontend ⏳

Modificare i form per gestire la selezione/creazione soggetto:

```jsx
// Form Proprietario - Esempio
function ProprietarioForm() {
  const [mode, setMode] = useState('nuovo'); // 'nuovo' | 'esistente'
  const [soggettoId, setSoggettoId] = useState(null);

  return (
    <form>
      {/* Modalità: nuovo soggetto o esistente */}
      <select value={mode} onChange={e => setMode(e.target.value)}>
        <option value="nuovo">Nuovo Soggetto</option>
        <option value="esistente">Soggetto Esistente</option>
      </select>

      {mode === 'esistente' ? (
        <SoggettoSelector value={soggettoId} onChange={setSoggettoId} />
      ) : (
        <SoggettoAnagra ficoForm />
      )}

      {/* Campi specifici proprietario */}
      <textarea name="note_proprietario" placeholder="Note specifiche proprietario" />
    </form>
  );
}
```

### 3. Creare API per Soggetti Anagrafici ⏳

```python
# backend/app/core/routes/soggetti_anagrafici.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.models import SoggettoAnagrafico

router = APIRouter(prefix="/soggetti-anagrafici", tags=["Soggetti"])

@router.get("/")
def get_all_soggetti(db: Session = Depends(get_db)):
    """Lista tutti i soggetti anagrafici"""
    return db.query(SoggettoAnagrafico).all()

@router.get("/{id}")
def get_soggetto(id: int, db: Session = Depends(get_db)):
    """Dettagli soggetto con tutti i ruoli"""
    soggetto = db.query(SoggettoAnagrafico).filter(
        SoggettoAnagrafico.id == id
    ).first()

    if not soggetto:
        raise HTTPException(404)

    # Include ruoli
    return {
        **soggetto.__dict__,
        "ruoli": {
            "proprietario": len(soggetto.proprietari) > 0,
            "affittuario": len(soggetto.affittuari) > 0,
            "tecnico": len(soggetto.tecnici) > 0,
        }
    }

@router.get("/search")
def search_soggetti(q: str, db: Session = Depends(get_db)):
    """Ricerca soggetti per nome/CF"""
    return db.query(SoggettoAnagrafico).filter(
        or_(
            SoggettoAnagrafico.nome.ilike(f"%{q}%"),
            SoggettoAnagrafico.cognome.ilike(f"%{q}%"),
            SoggettoAnagrafico.codice_fiscale.ilike(f"%{q}%"),
            SoggettoAnagrafico.ragione_sociale.ilike(f"%{q}%")
        )
    ).limit(20).all()

@router.post("/")
def create_soggetto(soggetto: SoggettoAnagra ficoCreate, db: Session = Depends(get_db)):
    """Crea nuovo soggetto anagrafico"""
    db_soggetto = SoggettoAnagrafico(**soggetto.dict())
    db.add(db_soggetto)
    db.commit()
    db.refresh(db_soggetto)
    return db_soggetto
```

### 4. Testing ⏳

Creare test per verificare:
- Creazione soggetto con ruolo singolo
- Creazione soggetto con ruoli multipli
- Aggiornamento dati anagrafici si riflette su tutti i ruoli
- Ricerca soggetti
- Query performance con JOIN

### 5. Rimozione Campi Deprecati 🔜

Una volta completato l'aggiornamento di API e frontend:

```sql
-- Rimuovere campi deprecati dalle tabelle
ALTER TABLE proprietari DROP COLUMN nome;
ALTER TABLE proprietari DROP COLUMN cognome;
ALTER TABLE proprietari DROP COLUMN codice_fiscale;
-- ... etc

ALTER TABLE affittuari DROP COLUMN nome;
-- ... etc

ALTER TABLE tecnici DROP COLUMN nome;
-- ... etc
```

## Query Utili

### Trova soggetti con ruoli multipli
```sql
SELECT
    s.id,
    COALESCE(s.ragione_sociale, s.nome || ' ' || s.cognome) as nome,
    COUNT(DISTINCT CASE WHEN p.id IS NOT NULL THEN 'P' END) as proprietario,
    COUNT(DISTINCT CASE WHEN a.id IS NOT NULL THEN 'A' END) as affittuario,
    COUNT(DISTINCT CASE WHEN t.id IS NOT NULL THEN 'T' END) as tecnico
FROM soggetti_anagrafici s
LEFT JOIN proprietari p ON s.id = p.soggetto_id
LEFT JOIN affittuari a ON s.id = a.soggetto_id
LEFT JOIN tecnici t ON s.id = t.soggetto_id
GROUP BY s.id
HAVING COUNT(DISTINCT
    CASE WHEN p.id IS NOT NULL THEN 'P' END ||
    CASE WHEN a.id IS NOT NULL THEN 'A' END ||
    CASE WHEN t.id IS NOT NULL THEN 'T' END
) > 1;
```

### Verifica integrità dati
```sql
-- Proprietari senza soggetto collegato
SELECT * FROM proprietari WHERE soggetto_id IS NULL;

-- Affittuari senza soggetto collegato
SELECT * FROM affittuari WHERE soggetto_id IS NULL;

-- Tecnici senza soggetto collegato
SELECT * FROM tecnici WHERE soggetto_id IS NULL;
```

## Rollback (se necessario)

Se serve tornare indietro:

```sql
-- I dati originali sono ancora presenti nei campi deprecati
-- Basta rimuovere la colonna soggetto_id
ALTER TABLE proprietari DROP COLUMN soggetto_id;
ALTER TABLE affittuari DROP COLUMN soggetto_id;
ALTER TABLE tecnici DROP COLUMN soggetto_id;

-- E rimuovere il vincolo NOT NULL dai campi deprecati se necessario
ALTER TABLE proprietari ALTER COLUMN codice_fiscale SET NOT NULL;
-- etc
```

## Note Tecniche

- **Cascade Delete**: Se un soggetto viene eliminato, vengono eliminati automaticamente tutti i suoi ruoli (CASCADE)
- **Unique Constraints**: CF e P.IVA sono unique in soggetti_anagrafici
- **Indexes**: soggetto_id è indicizzato in tutte le tabelle ruolo per performance
- **Timestamps**: created_at e updated_at tracciati sia su soggetto che sui ruoli

## Supporto

Per domande o problemi:
1. Verificare che la migrazione sia completata correttamente (vedere sezione "Risultati Migrazione")
2. Controllare i log del backend per errori
3. Verificare che i relationship SQLAlchemy funzionino correttamente
4. Testare le query con JOIN per assicurare performance

---

**Status**: ✅ MIGRAZIONE COMPLETATA - Pronto per aggiornamento API e Frontend
