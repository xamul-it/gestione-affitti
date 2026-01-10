# Sistema Scadenzario - Analisi Tecnico-Funzionale

**Progetto**: Gestione Affitti - Piattaforma Modulare
**Documento**: Analisi Tecnico-Funzionale Sistema Scadenzario
**Versione**: 1.0
**Data**: 10 Dicembre 2025
**Autore**: Claude Code

---

## 1. Introduzione

### 1.1 Obiettivo
Implementare un **sistema di scadenzario universale** che permetta a qualsiasi modulo della piattaforma di:
- Creare scadenze associate a qualsiasi entità
- Tracciare scadenze attive, scadute, completate
- Notificare utenti in prossimità di scadenze
- Gestire TODO (task senza entità associata)
- Visualizzare storia completa delle modifiche

### 1.2 Ambito
Il sistema è **platform-level**: fornisce servizi e componenti riusabili che i moduli business possono utilizzare senza dover implementare logica propria.

### 1.3 Principi Architetturali
- **Genericità**: Funziona con qualsiasi modulo/entità
- **Riusabilità**: Componenti frontend e API backend condivise
- **Modularità**: I moduli si integrano tramite convenzioni, non accoppiamento stretto
- **Estensibilità**: Sistema preparato per future evoluzioni (email, ricorrenze)

---

## 2. Requisiti Funzionali

### 2.1 Gestione Scadenze

#### RF-01: Creazione Scadenza
**Descrizione**: Qualsiasi utente con permesso "view" su un'entità può creare una scadenza.

**Dati Scadenza**:
- **Modulo** (string): Nome tecnico del modulo (es: "immobili", "anagrafica_italiana")
- **Tipo Entità** (string): Tipo entità nel modulo (es: "UnitaImmobiliare", "Contratto")
- **ID Entità** (integer): ID dell'entità specifica
- **Titolo** (string, required): Breve descrizione (max 200 caratteri)
- **Descrizione** (text, optional): Dettagli estesi della scadenza
- **Data Scadenza** (date, required): Data limite
- **Priorità** (enum): BASSA | MEDIA | ALTA
- **Destinatari** (array[user_id], optional): Lista utenti da notificare
  - Se vuoto: notifica solo il creatore
  - Se popolato: notifica tutti gli utenti specificati
- **Stato** (enum): ATTIVA | SCADUTA | COMPLETATA | POSTICIPATA | CANCELLATA
- **Creato Da** (user_id): Utente che ha creato la scadenza
- **Creato Il** (timestamp)

**Regole Business**:
- Data scadenza non può essere nel passato (warning, non blocco)
- Destinatari devono avere permesso "view" sull'entità
- Se entità viene cancellata → scadenze associate passano a CANCELLATA

#### RF-02: Modifica Scadenza
**Descrizione**: Chi ha creato la scadenza o i destinatari possono modificarla.

**Campi Modificabili**:
- Titolo, descrizione
- Data scadenza
- Priorità
- Destinatari
- Stato (solo: COMPLETATA, POSTICIPATA, CANCELLATA)

**Tracciamento**: Ogni modifica viene registrata in `scadenza_log` con:
- Campo modificato
- Valore precedente
- Valore nuovo
- Utente che ha modificato
- Timestamp

#### RF-03: TODO (Task Generici)
**Descrizione**: Una scadenza senza entità associata diventa un TODO.

**Differenze TODO**:
- `modulo` = NULL
- `entity_type` = NULL
- `entity_id` = NULL
- UI più semplice (checkbox list)
- Non ha deep-linking

**Caso d'uso**: "Chiamare tecnico caldaia", "Inviare documenti commercialista"

### 2.2 Notifiche e Alert

#### RF-04: Badge Scadenze nel Menu Utente
**Descrizione**: Il menu utente mostra un badge con il numero di scadenze scadute.

**Logica Badge**:
- Count scadenze con: `stato = SCADUTA` E `utente in destinatari OR creatore`
- Colore: Rosso (#dc2626)
- Posizionamento: Icona campanella nel menu utente
- Click: Apre dropdown con lista scadenze scadute (max 5) + link "Vedi tutte"

#### RF-05: Indicatori su Entità
**Descrizione**: Nelle liste e dettagli delle entità, mostrare se ci sono scadenze attive.

**Badge Colorato** (in lista):
- 🔴 Rosso: Scadenza scaduta (data < oggi)
- 🟡 Giallo: Scadenza prossima (data < oggi + 7gg)
- 🟢 Verde: Scadenza ok (data >= oggi + 7gg)

**Icona con Tooltip** (in dettaglio):
- Hover sull'icona → Tooltip mostra:
  - Titolo scadenza
  - Data scadenza (con "tra X giorni" o "scaduta da X giorni")
  - Priorità
- Click sull'icona → Apre modal "Gestione Scadenze Entità"

#### RF-06: Notifiche In-App (Fase 1)
**Descrizione**: Sistema di notifiche browser-native.

**Trigger Notifiche**:
- Giorno della scadenza (ore 09:00)
- Scadenza superata (giorno dopo, ore 09:00)

**Contenuto Notifica**:
- Titolo: "Scadenza: [titolo]"
- Body: "[Entità] - Scade [oggi/ieri]"
- Click → Naviga alla pagina scadenze con filtro su quella scadenza

**Nota**: Email notifiche rimandate a Fase 2 (quando piattaforma avrà email service).

### 2.3 Interfaccia Utente

#### RF-07: Pagina Gestione Scadenze
**Route**: `/scadenze`

**Sezioni**:
1. **Tabs**:
   - Tutte (default)
   - Scadute
   - Prossime (7 giorni)
   - Completate
   - TODO

2. **Filtri**:
   - Modulo (dropdown)
   - Priorità (dropdown multi)
   - Destinatario (autocomplete utenti)
   - Data da/a

3. **Lista Scadenze**:
   - Raggruppate per stato
   - Ordinamento: priorità DESC, data_scadenza ASC
   - Card compatta con:
     - Badge priorità
     - Titolo + descrizione (troncata)
     - Data scadenza (relativa: "tra 3 giorni", "scaduta da 2 giorni")
     - Destinatari (avatar o iniziali)
     - Link all'entità (se presente)
     - Azioni rapide: Completa | Posticipa | Modifica | Elimina

4. **Azioni Bulk**:
   - Seleziona multipli
   - Completa selezionati
   - Cancella selezionati

#### RF-08: Modal "Nuova Scadenza"
**Trigger**: Bottone "+" in qualsiasi pagina entità o pagina scadenze.

**Form Campi**:
- Entità (auto-compilato se aperto da pagina entità, altrimenti: dropdown modulo → autocomplete entità)
- Titolo* (input text)
- Descrizione (textarea)
- Data Scadenza* (date picker con quick actions: +7gg, +30gg, +90gg)
- Priorità (radio buttons: Bassa | Media | Alta)
- Destinatari (multi-select utenti con autocomplete)
- [Checkbox] "Crea come TODO" (nasconde selezione entità)

**Azioni**:
- Salva
- Salva e Crea Altra
- Annulla

#### RF-09: Modal "Gestione Scadenze Entità"
**Trigger**: Click su badge/icona scadenza in pagina entità.

**Contenuto**:
- Lista scadenze attive per l'entità
- Bottone "Nuova Scadenza" (pre-compila entità)
- Tab "Storia" con log modifiche

**Card Scadenza** (in modal):
- Inline editing: Click su campo → diventa editabile
- Azioni: Completa | Posticipa | Elimina
- Expand/collapse descrizione

#### RF-10: Storia Scadenze (Log)
**Descrizione**: Vista cronologica di tutte le azioni su una scadenza.

**Tipi Evento**:
- CREATA
- MODIFICATA (specifica campo)
- COMPLETATA
- POSTICIPATA
- CANCELLATA

**Formato Log Entry**:
```
[Data/Ora] [Nome Utente] [Azione]
- Campo: valore_vecchio → valore_nuovo
```

**Esempio**:
```
10/12/2025 14:30 - Mario Rossi - MODIFICATA
- Data Scadenza: 15/12/2025 → 20/12/2025
- Priorità: MEDIA → ALTA

10/12/2025 09:00 - Laura Bianchi - CREATA
- Titolo: Rinnovo contratto
- Data Scadenza: 15/12/2025
```

---

## 3. Requisiti Non Funzionali

### RNF-01: Performance
- Caricamento pagina scadenze: < 500ms (fino a 1000 scadenze)
- Calcolo badge menu: < 100ms (query ottimizzata con indici)
- Indicatori entità: Caricamento lazy, non blocca rendering lista

### RNF-02: Scalabilità
- Sistema supporta:
  - 10.000+ scadenze attive
  - 100+ moduli
  - 1000+ utenti
- Paginazione obbligatoria (max 50 scadenze per pagina)

### RNF-03: Usabilità
- UI mobile-responsive
- Accessibilità WCAG 2.1 Level AA
- Keyboard shortcuts:
  - `N` = Nuova scadenza
  - `C` = Completa scadenza selezionata
  - `ESC` = Chiudi modal

### RNF-04: Estensibilità
- Sistema preparato per:
  - Email notifications (Fase 2)
  - Scadenze ricorrenti (Fase 3)
  - Allegati su scadenze (Fase 3)
  - Integrazione calendario esterno (Fase 4)

---

## 4. Modello Dati

### 4.1 Schema Database

#### Tabella: `scadenze`
```sql
CREATE TABLE scadenze (
    id SERIAL PRIMARY KEY,

    -- Associazione entità (NULL per TODO)
    modulo VARCHAR(100),                    -- es: "immobili", "anagrafica_italiana"
    entity_type VARCHAR(100),               -- es: "UnitaImmobiliare", "Contratto"
    entity_id INTEGER,                      -- ID dell'entità

    -- Dati scadenza
    titolo VARCHAR(200) NOT NULL,
    descrizione TEXT,
    data_scadenza DATE NOT NULL,
    priorita VARCHAR(20) NOT NULL DEFAULT 'MEDIA',  -- BASSA | MEDIA | ALTA
    stato VARCHAR(20) NOT NULL DEFAULT 'ATTIVA',    -- ATTIVA | SCADUTA | COMPLETATA | POSTICIPATA | CANCELLATA

    -- Tracking
    creato_da INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    creato_il TIMESTAMP NOT NULL DEFAULT NOW(),
    modificato_il TIMESTAMP,
    completato_da INTEGER REFERENCES users(id) ON DELETE SET NULL,
    completato_il TIMESTAMP,

    -- Indici
    INDEX idx_scadenze_entity (modulo, entity_type, entity_id),
    INDEX idx_scadenze_stato (stato),
    INDEX idx_scadenze_data (data_scadenza),
    INDEX idx_scadenze_priorita (priorita),
    INDEX idx_scadenze_creatore (creato_da),

    -- Constraints
    CHECK (priorita IN ('BASSA', 'MEDIA', 'ALTA')),
    CHECK (stato IN ('ATTIVA', 'SCADUTA', 'COMPLETATA', 'POSTICIPATA', 'CANCELLATA')),
    CHECK ((modulo IS NULL AND entity_type IS NULL AND entity_id IS NULL) OR
           (modulo IS NOT NULL AND entity_type IS NOT NULL AND entity_id IS NOT NULL))
);
```

#### Tabella: `scadenza_destinatari`
```sql
CREATE TABLE scadenza_destinatari (
    id SERIAL PRIMARY KEY,
    scadenza_id INTEGER NOT NULL REFERENCES scadenze(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    notificato BOOLEAN DEFAULT FALSE,
    notificato_il TIMESTAMP,

    UNIQUE(scadenza_id, user_id),
    INDEX idx_destinatari_user (user_id),
    INDEX idx_destinatari_scadenza (scadenza_id)
);
```

#### Tabella: `scadenza_log`
```sql
CREATE TABLE scadenza_log (
    id SERIAL PRIMARY KEY,
    scadenza_id INTEGER NOT NULL REFERENCES scadenze(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    timestamp TIMESTAMP NOT NULL DEFAULT NOW(),
    azione VARCHAR(50) NOT NULL,              -- CREATA | MODIFICATA | COMPLETATA | POSTICIPATA | CANCELLATA
    campo_modificato VARCHAR(100),            -- NULL per CREATA/COMPLETATA/CANCELLATA
    valore_precedente TEXT,
    valore_nuovo TEXT,
    note TEXT,

    INDEX idx_log_scadenza (scadenza_id),
    INDEX idx_log_timestamp (timestamp DESC)
);
```

### 4.2 Pydantic Schemas (Backend)

```python
from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import date, datetime
from enum import Enum

class PrioritaEnum(str, Enum):
    BASSA = "BASSA"
    MEDIA = "MEDIA"
    ALTA = "ALTA"

class StatoScadenzaEnum(str, Enum):
    ATTIVA = "ATTIVA"
    SCADUTA = "SCADUTA"
    COMPLETATA = "COMPLETATA"
    POSTICIPATA = "POSTICIPATA"
    CANCELLATA = "CANCELLATA"

class ScadenzaCreate(BaseModel):
    modulo: Optional[str] = None
    entity_type: Optional[str] = None
    entity_id: Optional[int] = None
    titolo: str = Field(..., max_length=200)
    descrizione: Optional[str] = None
    data_scadenza: date
    priorita: PrioritaEnum = PrioritaEnum.MEDIA
    destinatari: List[int] = []  # user_ids

    @validator('data_scadenza')
    def data_non_troppo_passato(cls, v):
        if v < date.today() - timedelta(days=365):
            raise ValueError('Data scadenza non può essere più di 1 anno nel passato')
        return v

class ScadenzaUpdate(BaseModel):
    titolo: Optional[str] = Field(None, max_length=200)
    descrizione: Optional[str] = None
    data_scadenza: Optional[date] = None
    priorita: Optional[PrioritaEnum] = None
    stato: Optional[StatoScadenzaEnum] = None
    destinatari: Optional[List[int]] = None

class ScadenzaRead(BaseModel):
    id: int
    modulo: Optional[str]
    entity_type: Optional[str]
    entity_id: Optional[int]
    titolo: str
    descrizione: Optional[str]
    data_scadenza: date
    priorita: PrioritaEnum
    stato: StatoScadenzaEnum
    creato_da: int
    creato_il: datetime
    modificato_il: Optional[datetime]
    completato_da: Optional[int]
    completato_il: Optional[datetime]
    destinatari: List[int]

    # Computed fields
    giorni_rimanenti: int
    is_scaduta: bool
    is_prossima: bool  # scade entro 7 giorni
    badge_color: str   # "red" | "yellow" | "green"

    class Config:
        from_attributes = True

class ScadenzaLogRead(BaseModel):
    id: int
    scadenza_id: int
    user_id: int
    user_nome: str  # JOIN con users
    timestamp: datetime
    azione: str
    campo_modificato: Optional[str]
    valore_precedente: Optional[str]
    valore_nuovo: Optional[str]
    note: Optional[str]

    class Config:
        from_attributes = True
```

---

## 5. Architettura Backend

### 5.1 API Endpoints

#### **GET** `/api/v1/scadenze/`
**Descrizione**: Lista scadenze con filtri e paginazione.

**Query Params**:
- `skip` (int, default=0)
- `limit` (int, default=50, max=100)
- `stato` (enum, optional): Filtra per stato
- `priorita` (enum, optional): Filtra per priorità
- `modulo` (string, optional): Filtra per modulo
- `entity_type` (string, optional): Filtra per tipo entità
- `entity_id` (int, optional): Filtra per ID entità
- `destinatario_id` (int, optional): Filtra per destinatario
- `solo_mie` (bool, default=false): Solo scadenze create da me o assegnate a me
- `solo_scadute` (bool, default=false): Solo scadenze scadute
- `solo_prossime` (bool, default=false): Solo scadenze prossime (7 giorni)
- `solo_todo` (bool, default=false): Solo TODO (senza entità)

**Response**: `List[ScadenzaRead]`

**Permessi**: Qualsiasi utente autenticato (vede solo scadenze su entità che può vedere + scadenze assegnate a lui)

---

#### **GET** `/api/v1/scadenze/{id}`
**Descrizione**: Dettaglio scadenza singola.

**Response**: `ScadenzaRead`

**Permessi**: Utente deve essere creatore, destinatario, o avere permesso view sull'entità

---

#### **POST** `/api/v1/scadenze/`
**Descrizione**: Crea nuova scadenza.

**Body**: `ScadenzaCreate`

**Response**: `ScadenzaRead`

**Permessi**: Se associata a entità, utente deve avere permesso "view" sull'entità

**Business Logic**:
1. Valida che entity esiste (se specificata)
2. Valida che destinatari hanno permesso view sull'entità
3. Crea scadenza con stato ATTIVA
4. Crea log entry: CREATA
5. Se data_scadenza < oggi → stato = SCADUTA

---

#### **PUT** `/api/v1/scadenze/{id}`
**Descrizione**: Modifica scadenza esistente.

**Body**: `ScadenzaUpdate`

**Response**: `ScadenzaRead`

**Permessi**: Utente deve essere creatore o destinatario

**Business Logic**:
1. Per ogni campo modificato → crea log entry
2. Aggiorna `modificato_il`
3. Se stato → COMPLETATA: popola `completato_da` e `completato_il`
4. Ricalcola stato automatico (ATTIVA → SCADUTA se data < oggi)

---

#### **DELETE** `/api/v1/scadenze/{id}`
**Descrizione**: Elimina scadenza (soft delete: stato = CANCELLATA).

**Response**: `{"success": true}`

**Permessi**: Solo creatore può eliminare

**Business Logic**:
1. Imposta stato = CANCELLATA
2. Crea log entry: CANCELLATA

---

#### **POST** `/api/v1/scadenze/{id}/completa`
**Descrizione**: Marca scadenza come completata (shortcut).

**Response**: `ScadenzaRead`

**Permessi**: Creatore o destinatario

**Business Logic**:
- Equivalente a `PUT /scadenze/{id}` con `{"stato": "COMPLETATA"}`
- Popola `completato_da` e `completato_il`
- Crea log: COMPLETATA

---

#### **POST** `/api/v1/scadenze/{id}/posticipa`
**Descrizione**: Posticipa scadenza.

**Body**:
```json
{
  "nuova_data": "2025-12-20",
  "nota": "Rimandato per ferie cliente"
}
```

**Response**: `ScadenzaRead`

**Permessi**: Creatore o destinatario

**Business Logic**:
1. Imposta stato = POSTICIPATA
2. Aggiorna data_scadenza
3. Crea log: POSTICIPATA con nota
4. Riporta stato a ATTIVA (o SCADUTA se nuova data < oggi)

---

#### **GET** `/api/v1/scadenze/{id}/log`
**Descrizione**: Storia modifiche scadenza.

**Response**: `List[ScadenzaLogRead]` (ordinato per timestamp DESC)

**Permessi**: Creatore, destinatario, o permesso view su entità

---

#### **GET** `/api/v1/scadenze/badge-count`
**Descrizione**: Conta scadenze scadute per badge menu.

**Response**:
```json
{
  "count": 5,
  "dettaglio": {
    "scadute": 3,
    "prossime": 2
  }
}
```

**Permessi**: Utente autenticato (conta solo sue scadenze)

**Ottimizzazione**: Cache 5 minuti, invalidata su create/update scadenze

---

#### **GET** `/api/v1/scadenze/entity/{modulo}/{entity_type}/{entity_id}`
**Descrizione**: Scadenze associate a una specifica entità.

**Response**: `List[ScadenzaRead]`

**Permessi**: Permesso view sull'entità

**Uso**: Per mostrare badge/icona scadenze in liste e dettagli entità

---

### 5.2 Service Layer

#### `ScadenzaService` (Platform Service)
```python
# app/core/platform_services/scadenza_service.py

class ScadenzaService:
    """
    Platform service for deadline/reminder management.
    """

    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        data: ScadenzaCreate,
        current_user_id: int
    ) -> Scadenza:
        """Crea nuova scadenza con validazione e log."""
        # Validazione entità (se presente)
        if data.modulo and data.entity_type and data.entity_id:
            self._validate_entity_exists(
                data.modulo,
                data.entity_type,
                data.entity_id
            )
            self._validate_user_can_view_entity(
                current_user_id,
                data.modulo,
                data.entity_type,
                data.entity_id
            )

        # Validazione destinatari
        for dest_id in data.destinatari:
            if data.modulo:  # Se ha entità, destinatari devono poterla vedere
                self._validate_user_can_view_entity(
                    dest_id, data.modulo, data.entity_type, data.entity_id
                )

        # Determina stato iniziale
        stato = self._calcola_stato(data.data_scadenza, None)

        # Crea scadenza
        scadenza = Scadenza(
            **data.dict(exclude={'destinatari'}),
            stato=stato,
            creato_da=current_user_id
        )
        self.db.add(scadenza)
        self.db.flush()

        # Crea destinatari
        for dest_id in data.destinatari:
            dest = ScadenzaDestinatario(
                scadenza_id=scadenza.id,
                user_id=dest_id
            )
            self.db.add(dest)

        # Log creazione
        self._create_log(
            scadenza.id,
            current_user_id,
            'CREATA'
        )

        self.db.commit()
        self.db.refresh(scadenza)

        return scadenza

    def update(
        self,
        scadenza_id: int,
        data: ScadenzaUpdate,
        current_user_id: int
    ) -> Scadenza:
        """Aggiorna scadenza con tracking modifiche."""
        scadenza = self.get_by_id(scadenza_id)

        # Verifica permessi
        self._validate_user_can_edit(scadenza, current_user_id)

        # Traccia modifiche
        for field, new_value in data.dict(exclude_unset=True).items():
            old_value = getattr(scadenza, field)
            if old_value != new_value:
                self._create_log(
                    scadenza.id,
                    current_user_id,
                    'MODIFICATA',
                    campo_modificato=field,
                    valore_precedente=str(old_value),
                    valore_nuovo=str(new_value)
                )
                setattr(scadenza, field, new_value)

        # Aggiorna destinatari (se presenti)
        if data.destinatari is not None:
            self._update_destinatari(scadenza, data.destinatari)

        # Ricalcola stato se data cambiata
        if data.data_scadenza:
            scadenza.stato = self._calcola_stato(
                data.data_scadenza,
                scadenza.stato
            )

        # Gestisci completamento
        if data.stato == StatoScadenzaEnum.COMPLETATA:
            scadenza.completato_da = current_user_id
            scadenza.completato_il = datetime.now()

        scadenza.modificato_il = datetime.now()
        self.db.commit()
        self.db.refresh(scadenza)

        return scadenza

    def get_badge_count(self, user_id: int) -> dict:
        """Conta scadenze per badge menu (ottimizzato)."""
        # Scadenze dove user è creatore o destinatario
        query = self.db.query(Scadenza).filter(
            or_(
                Scadenza.creato_da == user_id,
                Scadenza.id.in_(
                    select(ScadenzaDestinatario.scadenza_id)
                    .where(ScadenzaDestinatario.user_id == user_id)
                )
            ),
            Scadenza.stato.in_(['ATTIVA', 'SCADUTA'])
        )

        scadute = query.filter(Scadenza.stato == 'SCADUTA').count()

        prossime = query.filter(
            Scadenza.stato == 'ATTIVA',
            Scadenza.data_scadenza <= date.today() + timedelta(days=7)
        ).count()

        return {
            'count': scadute + prossime,
            'dettaglio': {
                'scadute': scadute,
                'prossime': prossime
            }
        }

    def get_for_entity(
        self,
        modulo: str,
        entity_type: str,
        entity_id: int,
        user_id: int
    ) -> List[Scadenza]:
        """Scadenze associate a un'entità specifica."""
        # Verifica permessi view su entità
        self._validate_user_can_view_entity(
            user_id, modulo, entity_type, entity_id
        )

        return self.db.query(Scadenza).filter(
            Scadenza.modulo == modulo,
            Scadenza.entity_type == entity_type,
            Scadenza.entity_id == entity_id,
            Scadenza.stato.in_(['ATTIVA', 'SCADUTA', 'POSTICIPATA'])
        ).order_by(
            Scadenza.priorita.desc(),
            Scadenza.data_scadenza.asc()
        ).all()

    def _calcola_stato(
        self,
        data_scadenza: date,
        stato_corrente: Optional[str]
    ) -> str:
        """Calcola stato automatico in base a data."""
        # Non sovrascrivere stati finali
        if stato_corrente in ['COMPLETATA', 'CANCELLATA']:
            return stato_corrente

        if data_scadenza < date.today():
            return 'SCADUTA'
        else:
            return stato_corrente or 'ATTIVA'

    def _create_log(
        self,
        scadenza_id: int,
        user_id: int,
        azione: str,
        campo_modificato: Optional[str] = None,
        valore_precedente: Optional[str] = None,
        valore_nuovo: Optional[str] = None,
        note: Optional[str] = None
    ):
        """Crea entry nel log modifiche."""
        log = ScadenzaLog(
            scadenza_id=scadenza_id,
            user_id=user_id,
            azione=azione,
            campo_modificato=campo_modificato,
            valore_precedente=valore_precedente,
            valore_nuovo=valore_nuovo,
            note=note
        )
        self.db.add(log)

    # ... altri metodi helper
```

---

## 6. Architettura Frontend

### 6.1 Componenti Riusabili (Platform)

#### `<ScadenzaBadge>`
**Scopo**: Mostra badge colorato con indicatore scadenza.

**Props**:
```tsx
interface ScadenzaBadgeProps {
  modulo: string;
  entityType: string;
  entityId: number;
  size?: 'sm' | 'md' | 'lg';
  showTooltip?: boolean;
  onClick?: () => void;
}
```

**Comportamento**:
- Fetch scadenze per entità (GET `/scadenze/entity/...`)
- Calcola badge color: rosso/giallo/verde in base a scadenza più urgente
- Tooltip: Lista titoli scadenze con date
- Click: Apre modal `<GestioneScadenzeModal>`

**Uso nei Moduli**:
```tsx
// In lista entità
<ScadenzaBadge
  modulo="immobili"
  entityType="UnitaImmobiliare"
  entityId={unita.id}
  size="sm"
/>

// In dettaglio entità
<ScadenzaBadge
  modulo="affitti_lungo"
  entityType="Contratto"
  entityId={contratto.id}
  size="lg"
  showTooltip
  onClick={() => setShowModal(true)}
/>
```

---

#### `<NuovaScadenzaButton>`
**Scopo**: Bottone per creare scadenza (con o senza entità pre-selezionata).

**Props**:
```tsx
interface NuovaScadenzaButtonProps {
  modulo?: string;
  entityType?: string;
  entityId?: number;
  variant?: 'button' | 'fab' | 'icon';
  onSuccess?: (scadenza: Scadenza) => void;
}
```

**Comportamento**:
- Click → Apre modal `<ScadenzaFormModal>`
- Se entità specificata → Pre-compila form
- Altrimenti → Form completo con selezione entità

**Uso**:
```tsx
// In toolbar pagina entità
<NuovaScadenzaButton
  modulo="anagrafica_italiana"
  entityType="SoggettoAnagrafico"
  entityId={soggetto.id}
  variant="button"
/>

// Floating Action Button (TODO generici)
<NuovaScadenzaButton variant="fab" />
```

---

#### `<ScadenzaFormModal>`
**Scopo**: Modal form per creare/modificare scadenza.

**Props**:
```tsx
interface ScadenzaFormModalProps {
  open: boolean;
  onClose: () => void;
  scadenza?: Scadenza;  // Se presente = edit mode
  defaultModulo?: string;
  defaultEntityType?: string;
  defaultEntityId?: number;
  onSuccess?: (scadenza: Scadenza) => void;
}
```

**Form Fields**:
- Entità (se non default): Dropdown modulo → Autocomplete entità
- Checkbox "TODO" (nasconde selezione entità)
- Titolo* (required)
- Descrizione (textarea con rich editor)
- Data Scadenza* (date picker con quick buttons: +7gg, +30gg, +90gg)
- Priorità (3 radio buttons con icone)
- Destinatari (multi-select con avatar e autocomplete)

**Actions**:
- Salva
- Salva e Crea Altra
- Annulla

---

#### `<GestioneScadenzeModal>`
**Scopo**: Modal per gestire tutte le scadenze di un'entità.

**Props**:
```tsx
interface GestioneScadenzeModalProps {
  open: boolean;
  onClose: () => void;
  modulo: string;
  entityType: string;
  entityId: number;
}
```

**Sections**:
1. **Tabs**: Attive | Completate | Storia
2. **Lista Scadenze Attive**:
   - Card compatta per ogni scadenza
   - Inline editing: Click su titolo/data → Editable
   - Actions: Completa | Posticipa | Elimina
3. **Tab Storia**: Timeline con `<ScadenzaLogTimeline>`

---

#### `<ScadenzaLogTimeline>`
**Scopo**: Timeline cronologica modifiche scadenza.

**Props**:
```tsx
interface ScadenzaLogTimelineProps {
  scadenzaId: number;
  maxItems?: number;
}
```

**Comportamento**:
- Fetch log (GET `/scadenze/{id}/log`)
- Render timeline verticale con icone:
  - CREATA: ➕
  - MODIFICATA: ✏️
  - COMPLETATA: ✅
  - POSTICIPATA: ⏭️
  - CANCELLATA: ❌
- Ogni entry mostra: timestamp, user, azione, dettagli campo

---

#### `<ScadenzaBadgeMenu>`
**Scopo**: Badge nel menu utente con dropdown scadenze.

**Comportamento**:
- Fetch count badge (GET `/scadenze/badge-count`)
- Poll ogni 60 secondi
- Click → Dropdown con:
  - Max 5 scadenze scadute (con link)
  - Link "Vedi tutte le scadenze" → `/scadenze?solo_scadute=true`

**Integrazione**:
```tsx
// In app/components/Layout/UserMenu.jsx
import { ScadenzaBadgeMenu } from '@/components/Platform/Scadenze';

<UserMenu>
  {/* ... altri item ... */}
  <ScadenzaBadgeMenu />
</UserMenu>
```

---

### 6.2 Hook Personalizzati

#### `useScadenze()`
```tsx
function useScadenze(filters?: ScadenzeFilters) {
  const [scadenze, setScadenze] = useState<Scadenza[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchScadenze = useCallback(async () => {
    setLoading(true);
    try {
      const response = await api.get('/scadenze/', { params: filters });
      setScadenze(response.data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [filters]);

  useEffect(() => {
    fetchScadenze();
  }, [fetchScadenze]);

  return { scadenze, loading, error, refetch: fetchScadenze };
}
```

#### `useScadenzaBadge()`
```tsx
function useScadenzaBadge() {
  const [count, setCount] = useState(0);

  useEffect(() => {
    const fetchCount = async () => {
      const response = await api.get('/scadenze/badge-count');
      setCount(response.data.count);
    };

    fetchCount();
    const interval = setInterval(fetchCount, 60000); // Poll ogni 60s

    return () => clearInterval(interval);
  }, []);

  return count;
}
```

#### `useScadenzeEntity()`
```tsx
function useScadenzeEntity(
  modulo: string,
  entityType: string,
  entityId: number
) {
  const [scadenze, setScadenze] = useState<Scadenza[]>([]);
  const [hasScadenze, setHasScadenze] = useState(false);
  const [badgeColor, setBadgeColor] = useState<'red' | 'yellow' | 'green'>('green');

  useEffect(() => {
    const fetchScadenze = async () => {
      const response = await api.get(
        `/scadenze/entity/${modulo}/${entityType}/${entityId}`
      );
      const data = response.data;
      setScadenze(data);
      setHasScadenze(data.length > 0);

      if (data.length > 0) {
        // Calcola badge color in base a scadenza più urgente
        const urgente = data.reduce((prev, curr) =>
          curr.giorni_rimanenti < prev.giorni_rimanenti ? curr : prev
        );
        setBadgeColor(urgente.badge_color);
      }
    };

    if (modulo && entityType && entityId) {
      fetchScadenze();
    }
  }, [modulo, entityType, entityId]);

  return { scadenze, hasScadenze, badgeColor };
}
```

---

### 6.3 Pagina Gestione Scadenze

**Route**: `/scadenze`

**Componente**: `frontend/src/pages/Scadenze.jsx`

**Struttura**:
```tsx
function ScadenzePage() {
  const [activeTab, setActiveTab] = useState<'tutte' | 'scadute' | 'prossime' | 'completate' | 'todo'>('tutte');
  const [filters, setFilters] = useState<ScadenzeFilters>({});
  const { scadenze, loading, refetch } = useScadenze(filters);

  const handleCompleta = async (id: number) => {
    await api.post(`/scadenze/${id}/completa`);
    refetch();
  };

  return (
    <PageContainer>
      <Header>
        <h1>Gestione Scadenze</h1>
        <NuovaScadenzaButton variant="button" onSuccess={refetch} />
      </Header>

      <Tabs value={activeTab} onChange={setActiveTab}>
        <Tab label="Tutte" value="tutte" />
        <Tab label="Scadute" value="scadute" badge={countScadute} />
        <Tab label="Prossime (7gg)" value="prossime" />
        <Tab label="Completate" value="completate" />
        <Tab label="TODO" value="todo" />
      </Tabs>

      <Filters>
        <ModuloSelect value={filters.modulo} onChange={...} />
        <PrioritaSelect value={filters.priorita} onChange={...} />
        <UserAutocomplete value={filters.destinatario_id} onChange={...} />
        <DateRangePicker from={filters.data_da} to={filters.data_a} onChange={...} />
      </Filters>

      <ScadenzeList>
        {loading ? (
          <Skeleton count={5} />
        ) : (
          scadenze.map(scadenza => (
            <ScadenzaCard
              key={scadenza.id}
              scadenza={scadenza}
              onCompleta={handleCompleta}
              onEdit={...}
              onDelete={...}
            />
          ))
        )}
      </ScadenzeList>
    </PageContainer>
  );
}
```

---

## 7. Flussi Utente Principali

### 7.1 Flusso: Creare Scadenza da Pagina Entità

```
1. Utente visualizza dettaglio Contratto (id=123)
2. Click su bottone "Nuova Scadenza" in toolbar
3. Modal si apre con form pre-compilato:
   - Modulo: "affitti_lungo"
   - Entità: "Contratto #123 - Via Roma 10"
4. Utente compila:
   - Titolo: "Rinnovo contratto"
   - Data: 31/12/2025
   - Priorità: ALTA
   - Destinatari: Seleziona "Laura Bianchi"
5. Click "Salva"
6. POST /scadenze/ → Crea scadenza
7. Badge scadenza appare su card Contratto
8. Laura riceve notifica in-app
```

### 7.2 Flusso: Visualizzare Scadenze Scadute

```
1. Utente apre app
2. Badge rosso (3) appare nel menu utente
3. Click sul badge → Dropdown mostra:
   - "Rinnovo contratto - Scaduto da 2 giorni"
   - "Visura camerale - Scaduto da 5 giorni"
   - "Chiamare tecnico - Scaduto da 1 giorno"
   - [Link] "Vedi tutte le scadenze"
4. Click su "Rinnovo contratto"
5. Redirect a pagina dettaglio Contratto
6. Badge rosso lampeggiante su card Contratto
7. Click su badge → Modal "Gestione Scadenze Entità"
8. Utente vede scadenza con azioni:
   - [Completa] [Posticipa] [Modifica]
9. Click "Posticipa"
10. Form: Nuova data + Nota
11. Salva → Scadenza passa a POSTICIPATA
12. Log registra: "Posticipata da 31/12 a 15/01 - Nota: Ferie cliente"
```

### 7.3 Flusso: Creare TODO Generico

```
1. Utente in pagina Scadenze
2. Click bottone "+ Nuova Scadenza"
3. Modal si apre
4. Checkbox "Crea come TODO" → Nasconde selezione entità
5. Compila:
   - Titolo: "Chiamare assicurazione"
   - Data: 15/12/2025
   - Priorità: MEDIA
6. Salva
7. TODO appare in tab "TODO" senza link entità
8. Può essere completato con singolo click
```

---

## 8. Integrazioni Moduli

### 8.1 Pattern di Integrazione

I moduli business integrano lo scadenzario in 3 punti:

#### 1. **Liste Entità** (Badge Scadenza)
```tsx
// In ImmobiliList.jsx
import { ScadenzaBadge } from '@/components/Platform/Scadenze';

function ImmobiliList() {
  return (
    <Table>
      {immobili.map(immobile => (
        <TableRow key={immobile.id}>
          <TableCell>{immobile.indirizzo}</TableCell>
          <TableCell>
            <ScadenzaBadge
              modulo="immobili"
              entityType="UnitaImmobiliare"
              entityId={immobile.id}
              size="sm"
            />
          </TableCell>
        </TableRow>
      ))}
    </Table>
  );
}
```

#### 2. **Dettaglio Entità** (Toolbar + Badge)
```tsx
// In ContrattoDetail.jsx
import {
  ScadenzaBadge,
  NuovaScadenzaButton,
  GestioneScadenzeModal
} from '@/components/Platform/Scadenze';

function ContrattoDetail({ contratto }) {
  const [showModal, setShowModal] = useState(false);

  return (
    <PageContainer>
      <Toolbar>
        <h1>Contratto #{contratto.id}</h1>
        <NuovaScadenzaButton
          modulo="affitti_lungo"
          entityType="Contratto"
          entityId={contratto.id}
        />
        <ScadenzaBadge
          modulo="affitti_lungo"
          entityType="Contratto"
          entityId={contratto.id}
          size="lg"
          showTooltip
          onClick={() => setShowModal(true)}
        />
      </Toolbar>

      {/* ... rest of detail ... */}

      <GestioneScadenzeModal
        open={showModal}
        onClose={() => setShowModal(false)}
        modulo="affitti_lungo"
        entityType="Contratto"
        entityId={contratto.id}
      />
    </PageContainer>
  );
}
```

#### 3. **Widget Dashboard** (Opzionale)
```tsx
// In dashboard widget config
{
  id: "immobili.scadenze_certificate",
  title: "Certificati Energetici in Scadenza",
  component: () => {
    const { scadenze } = useScadenze({
      modulo: "immobili",
      entity_type: "CertificatoEnergetico",
      solo_prossime: true
    });

    return (
      <WidgetCard>
        <h3>Certificati in scadenza</h3>
        {scadenze.map(s => (
          <ScadenzaListItem key={s.id} scadenza={s} />
        ))}
      </WidgetCard>
    );
  }
}
```

---

## 9. Considerazioni Tecniche

### 9.1 Performance

**Problemi Potenziali**:
1. Query N+1 per badge in liste con molte entità
2. Calcolo badge count lento per utenti con molte scadenze
3. Polling frequente badge menu sovraccarica server

**Soluzioni**:
- **Batch Loading**: Endpoint `/scadenze/entity/batch` che accetta array di entità
  ```
  POST /scadenze/entity/batch
  Body: [
    { modulo: "immobili", entity_type: "UnitaImmobiliare", entity_id: 1 },
    { modulo: "immobili", entity_type: "UnitaImmobiliare", entity_id: 2 },
    ...
  ]
  Response: { "1": { has_scadenze: true, badge_color: "red" }, "2": { ... } }
  ```

- **Redis Cache**: Cache badge count per 5 minuti
  ```python
  @cache(key="scadenze:badge:{user_id}", ttl=300)
  def get_badge_count(user_id: int) -> dict:
      ...
  ```

- **WebSocket** (Fase 2): Real-time updates invece di polling
  ```tsx
  useWebSocket('/ws/scadenze', (message) => {
    if (message.type === 'badge_update') {
      setBadgeCount(message.count);
    }
  });
  ```

### 9.2 Sicurezza

**Validazioni**:
1. **Permessi Entità**: Utente deve avere `view` sull'entità per creare scadenza
2. **Destinatari Validi**: Solo utenti con `view` su entità possono essere destinatari
3. **Soft Delete**: Scadenze non vengono eliminate fisicamente, solo stato CANCELLATA
4. **Audit Log**: Tutte le azioni tracciate con user_id e timestamp

**SQL Injection**:
- Tutti i filtri passano tramite SQLAlchemy ORM (parametrizzato)
- Nessuna string interpolation raw

**XSS**:
- Tutti i campi user-input sanitizzati
- Rich editor descrizione con whitelist tags HTML

### 9.3 Estensibilità Futura

#### Fase 2: Email Notifications
**Quando**: Quando piattaforma avrà `EmailService`

**Implementazione**:
1. Cron job giornaliero (09:00): Trova scadenze prossime/scadute
2. Per ogni scadenza + destinatario: Invia email
3. Marca `notificato=true` in `scadenza_destinatari`
4. Template email parametrizzato:
   ```html
   Ciao {nome},

   La scadenza "{titolo}" è prevista per {data_scadenza}.

   Dettagli: {descrizione}
   Entità: {modulo} - {entity_type} #{entity_id}

   [Vai alla scadenza]
   ```

#### Fase 3: Scadenze Ricorrenti
**Schema Update**:
```sql
ALTER TABLE scadenze ADD COLUMN ricorrente BOOLEAN DEFAULT FALSE;
ALTER TABLE scadenze ADD COLUMN ricorrenza_pattern VARCHAR(50);
-- Pattern: "DAILY", "WEEKLY", "MONTHLY", "YEARLY", "CUSTOM"
ALTER TABLE scadenze ADD COLUMN ricorrenza_fine DATE;
```

**Logic**:
- Quando scadenza COMPLETATA + ricorrente → Crea nuova scadenza con data+pattern
- Pattern gestito con libreria `rrule` (iCalendar standard)

#### Fase 4: Allegati su Scadenze
**Schema Update**:
```sql
CREATE TABLE scadenza_allegati (
    id SERIAL PRIMARY KEY,
    scadenza_id INTEGER REFERENCES scadenze(id) ON DELETE CASCADE,
    file_path VARCHAR(500) NOT NULL,
    filename VARCHAR(200) NOT NULL,
    mime_type VARCHAR(100),
    size_bytes INTEGER,
    uploaded_by INTEGER REFERENCES users(id),
    uploaded_at TIMESTAMP DEFAULT NOW()
);
```

**UI**: Drag & drop area in `<ScadenzaFormModal>`

---

## 10. Piano di Implementazione

### Fase 1: Backend Core (2-3 giorni)
- [ ] Crea modelli SQLAlchemy: `Scadenza`, `ScadenzaDestinatario`, `ScadenzaLog`
- [ ] Migration Alembic
- [ ] Implementa `ScadenzaService` con tutti i metodi
- [ ] Crea Pydantic schemas
- [ ] Implementa API endpoints (CRUD + badge-count + entity)
- [ ] Unit tests service layer
- [ ] Integration tests API endpoints

### Fase 2: Frontend Core (2-3 giorni)
- [ ] Crea componenti platform:
  - [ ] `<ScadenzaBadge>`
  - [ ] `<NuovaScadenzaButton>`
  - [ ] `<ScadenzaFormModal>`
  - [ ] `<GestioneScadenzeModal>`
  - [ ] `<ScadenzaLogTimeline>`
  - [ ] `<ScadenzaBadgeMenu>`
- [ ] Implementa hook: `useScadenze`, `useScadenzaBadge`, `useScadenzeEntity`
- [ ] Pagina `/scadenze` con tabs e filtri
- [ ] Integra `<ScadenzaBadgeMenu>` in `UserMenu`
- [ ] Styling con Tailwind/Material-UI

### Fase 3: Integrazioni Moduli (1-2 giorni)
- [ ] Integra in `immobili`:
  - [ ] Badge in lista UnitaImmobiliare
  - [ ] Badge + button in dettaglio UnitaImmobiliare
  - [ ] Widget dashboard "Certificati in scadenza"
- [ ] Integra in `affitti_lungo`:
  - [ ] Badge in lista Contratti
  - [ ] Badge + button in dettaglio Contratto
- [ ] Integra in `anagrafica_italiana`:
  - [ ] Badge in lista Soggetti (documenti in scadenza)

### Fase 4: Testing & Polish (1 giorno)
- [ ] E2E tests con Playwright:
  - [ ] Crea scadenza → Badge appare
  - [ ] Completa scadenza → Badge sparisce
  - [ ] Posticipa scadenza → Log registrato
  - [ ] Badge menu funziona
- [ ] Performance testing (1000+ scadenze)
- [ ] Mobile responsiveness
- [ ] Accessibility audit (WCAG)
- [ ] Documentazione utente

### Fase 5 (Futura): Email & Ricorrenze
- [ ] Integra con `EmailService` quando disponibile
- [ ] Implementa scadenze ricorrenti
- [ ] Allegati su scadenze
- [ ] WebSocket real-time updates

---

## 11. Metriche di Successo

### KPI Funzionali
- **Adozione**: % moduli che usano scadenzario (target: 80% entro 3 mesi)
- **Utilizzo**: Media scadenze attive per utente (target: 5-10)
- **Completamento**: % scadenze completate entro data (target: >70%)
- **Tempo Risposta**: Tempo medio tra scadenza e completamento (target: <3 giorni)

### KPI Tecnici
- **Performance**: Caricamento pagina scadenze <500ms (target: 100% requests)
- **Affidabilità**: 0 errori critici in 30 giorni
- **Mobile**: 100% funzionalità disponibili su mobile
- **Accessibilità**: WCAG 2.1 Level AA compliance

---

## 12. Rischi e Mitigazioni

| Rischio | Probabilità | Impatto | Mitigazione |
|---------|-------------|---------|-------------|
| Performance degradation con molte scadenze | Media | Alto | Implementare batch loading, caching, indici DB |
| Notifiche spam (troppi alert) | Alta | Medio | Raggruppare notifiche, preferenze utente |
| Confusione stati scadenza | Media | Medio | UI chiara, tooltip esplicativi, guida utente |
| Perdita dati per cancellazione entità | Bassa | Alto | Soft delete, CASCADE behavior, backup |
| Adozione bassa da parte moduli | Media | Alto | Demo, documentazione, supporto integrazione |

---

## 13. Conclusioni

Il sistema scadenzario proposto è:
- **Universale**: Funziona con qualsiasi modulo/entità
- **Scalabile**: Gestisce migliaia di scadenze senza degrado performance
- **Riusabile**: Componenti platform ready-to-use per i moduli
- **Estensibile**: Preparato per email, ricorrenze, allegati

L'implementazione seguirà un approccio incrementale:
1. Backend core + API
2. Frontend core + componenti
3. Integrazioni moduli pilota
4. Testing & rollout completo
5. Feature avanzate (email, ricorrenze)

**Prossimo step**: Approvazione requisiti e inizio Fase 1 implementazione.

---

**Documento redatto da**: Claude Code
**Approvazione richiesta da**: Product Owner / Tech Lead
**Data inizio implementazione prevista**: TBD dopo approvazione
