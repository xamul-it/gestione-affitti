# Sistema Ruoli Azienda - Modulo Anagrafica Italiana

**Data Implementazione:** 9 Dicembre 2025
**Versione:** 1.0
**Stato:** ✅ Completo (Backend + Frontend)

---

## 1. Panoramica

Il sistema **Ruoli Azienda** permette di associare persone fisiche a persone giuridiche attraverso ruoli aziendali (es: "Mario Rossi è Amministratore Delegato di ACME SRL").

### 1.1 Differenza con Sistema Ruoli di Business

⚠️ **IMPORTANTE**: I Ruoli Azienda sono **diversi** dai Ruoli di Business menzionati in ANAGRAFICA_GAP_ANALYSIS.md:

| Aspetto | Ruoli Azienda | Ruoli di Business |
|---------|---------------|-------------------|
| **Scopo** | Relazioni organizzative | Controllo accessi |
| **Esempio** | "Mario è AD di ACME SRL" | "Mario è affittuario" |
| **Entità** | Persona ↔ Azienda | Soggetto ↔ Sistema |
| **Temporalità** | Data inizio/fine | Permanente |
| **Visibilità** | Dati anagrafici | Cono di visibilità |

---

## 2. Modello Dati

### 2.1 Tabella: ruoli_azienda

Relazioni N:N tra persone fisiche e giuridiche con ruolo e periodo.

```sql
CREATE TABLE ruoli_azienda (
    id SERIAL PRIMARY KEY,
    persona_fisica_id INTEGER NOT NULL REFERENCES soggetti_anagrafici(id) ON DELETE CASCADE,
    persona_giuridica_id INTEGER NOT NULL REFERENCES soggetti_anagrafici(id) ON DELETE CASCADE,
    ruolo_tipo_id INTEGER REFERENCES ruoli_azienda_tipi(id) ON DELETE SET NULL,
    ruolo VARCHAR(100),  -- Backward compatible, nullable
    data_inizio DATE,
    data_fine DATE,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX ix_ruoli_azienda_persona_fisica ON ruoli_azienda(persona_fisica_id);
CREATE INDEX ix_ruoli_azienda_persona_giuridica ON ruoli_azienda(persona_giuridica_id);
CREATE INDEX ix_ruoli_azienda_ruolo_tipo ON ruoli_azienda(ruolo_tipo_id);
```

**Vincoli:**
- `persona_fisica_id` deve riferirsi a un soggetto con `tipo_soggetto = 'PERSONA_FISICA'`
- `persona_giuridica_id` deve riferirsi a un soggetto con `tipo_soggetto = 'PERSONA_GIURIDICA'`
- `ruolo_tipo_id` è preferito; `ruolo` text usato solo se ruolo_tipo_id è NULL (backward compatibility)

### 2.2 Tabella: ruoli_azienda_tipi (Dati di Dominio)

Tipologie normalizzate di ruoli aziendali.

```sql
CREATE TABLE ruoli_azienda_tipi (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(100) NOT NULL UNIQUE,
    descrizione VARCHAR(500),
    attivo BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX ix_ruoli_azienda_tipi_nome ON ruoli_azienda_tipi(nome);
CREATE INDEX ix_ruoli_azienda_tipi_attivo ON ruoli_azienda_tipi(attivo);
```

**Esempi di ruoli:**
- Amministratore Delegato
- Direttore Generale
- Segretaria
- Responsabile Tecnico
- Consulente Esterno
- Socio
- Rappresentante Legale

---

## 3. Backend API

### 3.1 Ruoli Azienda (Associazioni)

#### GET /api/v1/anagrafica/ruoli-azienda/soggetto/{soggetto_id}
Ottieni tutti i ruoli di un soggetto (sia come persona fisica che come azienda).

**Query Parameters:**
- `attivi_only` (bool): Solo ruoli attivi (data_fine null o futura)

**Response:**
```json
{
  "come_persona": [
    {
      "id": 1,
      "persona_fisica_id": 123,
      "persona_giuridica_id": 456,
      "persona_giuridica": {
        "id": 456,
        "ragione_sociale": "ACME SRL",
        "codice_fiscale": "12345678901"
      },
      "ruolo_tipo_id": 1,
      "ruolo": "Amministratore Delegato",
      "data_inizio": "2023-01-15",
      "data_fine": null,
      "attivo": true
    }
  ],
  "come_azienda": [
    {
      "id": 2,
      "persona_fisica_id": 789,
      "persona_giuridica_id": 456,
      "persona_fisica": {
        "id": 789,
        "nome": "Maria",
        "cognome": "Verdi",
        "codice_fiscale": "MRAVRD80A01H501Z"
      },
      "ruolo_tipo_id": 2,
      "ruolo": "Segretaria",
      "data_inizio": "2024-03-01",
      "data_fine": null,
      "attivo": true
    }
  ]
}
```

#### POST /api/v1/anagrafica/ruoli-azienda/
Crea una nuova associazione ruolo.

**Request:**
```json
{
  "persona_fisica_id": 123,
  "persona_giuridica_id": 456,
  "ruolo": "Amministratore Delegato",
  "data_inizio": "2025-01-01",
  "data_fine": null
}
```

**Note:**
- Il sistema cerca automaticamente un `ruolo_tipo_id` corrispondente al nome del ruolo
- Se non esiste, viene salvato come testo libero in `ruolo`

#### PUT /api/v1/anagrafica/ruoli-azienda/{id}
Aggiorna un'associazione esistente (es: cambio data fine per cessazione ruolo).

#### DELETE /api/v1/anagrafica/ruoli-azienda/{id}
Elimina un'associazione ruolo.

---

### 3.2 Ruoli Azienda Tipi (Dati di Dominio)

#### GET /api/v1/anagrafica/domini/ruoli-azienda-tipi/
Lista tutti i tipi di ruolo.

**Query Parameters:**
- `skip` (int): Offset paginazione
- `limit` (int): Numero risultati
- `attivi_solo` (bool): Solo ruoli attivi
- `search` (string): Ricerca per nome

**Response:**
```json
[
  {
    "id": 1,
    "nome": "Amministratore Delegato",
    "descrizione": "Responsabile della gestione operativa dell'azienda",
    "attivo": true,
    "created_at": "2025-12-01T10:00:00Z",
    "updated_at": "2025-12-01T10:00:00Z"
  }
]
```

#### POST /api/v1/anagrafica/domini/ruoli-azienda-tipi/
Crea un nuovo tipo di ruolo.

**Request:**
```json
{
  "nome": "Direttore Commerciale",
  "descrizione": "Gestione della rete vendite e sviluppo commerciale",
  "attivo": true
}
```

#### PUT /api/v1/anagrafica/domini/ruoli-azienda-tipi/{id}
Aggiorna un tipo di ruolo (nome, descrizione, attivo).

#### DELETE /api/v1/anagrafica/domini/ruoli-azienda-tipi/{id}
Elimina un tipo di ruolo.

**Comportamento:**
- Le associazioni esistenti con questo ruolo vengono mantenute (FK con ON DELETE SET NULL)
- Il nome del ruolo rimane salvato in campo `ruolo` text

#### POST /api/v1/anagrafica/domini/ruoli-azienda-tipi/merge
Unisce due ruoli duplicati in uno solo.

**Request:**
```json
{
  "source_id": 5,
  "target_id": 3
}
```

**Comportamento:**
1. Aggiorna tutte le associazioni da `source_id` a `target_id`
2. Elimina il ruolo sorgente
3. Ritorna il conteggio delle associazioni aggiornate

**Use Case:**
Quando si trovano duplicati (es: "Amministratore Delegato" e "AD"), si possono unificare mantenendo lo storico.

---

## 4. Frontend

### 4.1 Componenti Implementati

#### RuoliAziendaTipiList (Gestione Domini)
**Path:** `/anagrafiche/domini/ruoli-azienda`
**File:** `frontend/src/modules/anagrafica_italiana/components/RuoliAziendaTipi/RuoliAziendaTipiList.jsx`

**Funzionalità:**
- ✅ Lista tutti i tipi di ruolo con filtri (attivi/inattivi, ricerca)
- ✅ Crea/modifica/elimina tipi di ruolo
- ✅ **Merge** ruoli duplicati con UI guidata
- ✅ Badge visivi (attivo/inattivo)
- ✅ Statistiche utilizzo per ogni ruolo

**Screenshot Logico:**
```
┌─────────────────────────────────────────────┐
│ Gestione Ruoli Azienda                      │
│ [+ Nuovo Ruolo]  [🔄 Merge]                 │
├─────────────────────────────────────────────┤
│ 🔍 Ricerca: [___________]  ☑ Solo attivi   │
├─────────────────────────────────────────────┤
│ Nome                    | Attivo | Azioni   │
├─────────────────────────────────────────────┤
│ Amministratore Delegato | ✅     | [✏️] [🗑️]│
│ Segretaria              | ✅     | [✏️] [🗑️]│
│ Socio (obsoleto)        | ❌     | [✏️] [🗑️]│
└─────────────────────────────────────────────┘
```

#### RuoloAziendaTipoForm (Modal)
**File:** `frontend/src/modules/anagrafica_italiana/components/RuoliAziendaTipi/RuoloAziendaTipoForm.jsx`

**Funzionalità:**
- ✅ Form creazione/modifica ruolo tipo
- ✅ Validazione nome univoco
- ✅ Campo descrizione opzionale
- ✅ Toggle attivo/inattivo
- ✅ Messaggi errore da backend

#### RuoloAziendaForm (Modal)
**File:** `frontend/src/modules/anagrafica_italiana/components/RuoliAzienda/RuoloAziendaForm.jsx`

**Funzionalità:**
- ✅ Form assegnazione ruolo persona-azienda
- ✅ **Autocomplete** ruoli da ruoli_azienda_tipi attivi (HTML5 datalist)
- ✅ Selezione controparte (persona o azienda)
- ✅ Date inizio/fine opzionali
- ✅ Pre-compilazione soggetto corrente

**Integrazione Autocomplete:**
```javascript
// Carica ruoli attivi
const ruoliTipi = await getRuoliAziendaTipi({ attivi_solo: true });

// HTML5 datalist per autocomplete nativo
<input
  type="text"
  list="ruoli-datalist"
  placeholder="es: Amministratore Delegato, Segretaria..."
/>
<datalist id="ruoli-datalist">
  {ruoliTipi.map(ruolo => (
    <option key={ruolo.id} value={ruolo.nome} />
  ))}
</datalist>
```

**Vantaggi:**
- ✅ Suggerimenti mentre si digita
- ✅ Possibilità di inserire ruoli custom
- ✅ Performance (datalist nativo)
- ✅ Accessibilità (supporto screen reader)

---

### 4.2 Pagina da Implementare

#### RuoliAziendaList (TODO)
**Path proposto:** `/anagrafiche/ruoli-azienda`
**Scopo:** Vista centralizzata di tutte le associazioni ruolo

**Requisiti:**
- [ ] Lista tutte le associazioni persona-azienda
- [ ] Filtri: per persona, per azienda, per ruolo, attivi/cessati
- [ ] Colonne: Persona, Azienda, Ruolo, Data inizio, Data fine, Stato
- [ ] Azioni: Modifica (cambio date), Elimina
- [ ] Paginazione + ricerca
- [ ] Export CSV

**Use Case:**
"Voglio vedere tutti gli amministratori delegati delle aziende nel sistema" oppure "Chi lavora per ACME SRL?"

---

## 5. Integrazione con Altri Componenti

### 5.1 SoggettoDetail.jsx
I ruoli azienda sono visualizzati nella scheda dettaglio soggetto.

**Tab "Ruoli":**
```javascript
<RuoliAziendaSection
  soggetto={soggetto}
  onUpdate={handleRuoliUpdate}
/>
```

**Funzionalità:**
- ✅ Visualizza ruoli del soggetto (come persona o come azienda)
- ✅ Button "Aggiungi Ruolo" apre RuoloAziendaForm
- ✅ Badge attivo/cessato
- ✅ Modifica/elimina ruoli esistenti

### 5.2 PersonaFisicaDetail.jsx / PersonaGiuridicaDetail.jsx
Se esistono viste specifiche per PF/PG, anche qui si visualizzano i ruoli.

---

## 6. Logica di Business

### 6.1 Normalizzazione Ruoli

**Problema:** Gli utenti potrebbero inserire ruoli simili con piccole variazioni:
- "Amministratore Delegato" vs "AD" vs "Ammin. Delegato"

**Soluzione implementata:**

1. **Autocomplete**: Suggerisce ruoli esistenti mentre si digita
2. **Merge manuale**: Admin può unificare duplicati in ruoli_azienda_tipi
3. **Backward compatibility**: Se un ruolo non esiste in ruoli_azienda_tipi, viene salvato come text in campo `ruolo`

**Workflow raccomandato:**
1. Inserire nuovi ruoli liberamente (autocomplete suggerisce)
2. Periodicamente, admin accede a `/anagrafiche/domini/ruoli-azienda`
3. Usa funzione **Merge** per unificare duplicati
4. Disattiva ruoli obsoleti invece di cancellarli

### 6.2 Gestione Date

**Campo `data_inizio`:**
- Opzionale
- Se NULL, ruolo attivo da sempre

**Campo `data_fine`:**
- Opzionale
- Se NULL, ruolo ancora attivo
- Se valorizzato, ruolo cessato

**Calcolo stato "attivo":**
```python
attivo = (data_fine is None) or (data_fine > today())
```

**Use Case:**
- Mario è AD di ACME dal 01/01/2020 a oggi → data_fine = NULL
- Maria era Segretaria fino al 31/12/2024 → data_fine = 2024-12-31

### 6.3 Validazioni

**Backend (routes/ruoli_azienda.py):**
- ✅ `persona_fisica_id` deve essere tipo PERSONA_FISICA
- ✅ `persona_giuridica_id` deve essere tipo PERSONA_GIURIDICA
- ✅ Non permette associare due persone fisiche o due giuridiche
- ✅ Dates: data_fine >= data_inizio (se entrambe valorizzate)

**Frontend (RuoloAziendaForm.jsx):**
- ✅ Campo ruolo obbligatorio
- ✅ Selezione controparte obbligatoria
- ✅ Disabilita selezione controparte in edit mode

---

## 7. Permessi

Tutti gli endpoint richiedono permessi standard del modulo anagrafico:

| Operazione | Permesso Richiesto |
|------------|-------------------|
| View ruoli | `soggetto.view` |
| Create ruolo | `soggetto.create` |
| Update ruolo | `soggetto.update` |
| Delete ruolo | `soggetto.delete` |
| Manage tipi ruolo | `soggetto.update` |

**Note:**
- Utenti business (affittuari, proprietari) possono vedere i ruoli ma non modificarli
- Solo Admin e operatori interni possono gestire ruoli

---

## 8. Database Migration

### 8.1 Creazione Tabelle

Le tabelle sono create automaticamente da SQLAlchemy al primo avvio:

```python
# backend/modules/anagrafica_italiana/models/ruolo_azienda_tipo.py
# backend/modules/anagrafica_italiana/models/ruolo_azienda.py
Base.metadata.create_all(bind=engine)
```

### 8.2 Migrazione Dati Esistenti

Se il sistema aveva già dati in `ruoli_azienda` con solo campo `ruolo` text:

```sql
-- Step 1: Identificare ruoli unici esistenti
INSERT INTO ruoli_azienda_tipi (nome, attivo)
SELECT DISTINCT ruolo, true
FROM ruoli_azienda
WHERE ruolo IS NOT NULL AND ruolo != ''
ON CONFLICT (nome) DO NOTHING;

-- Step 2: Popolare ruolo_tipo_id
UPDATE ruoli_azienda ra
SET ruolo_tipo_id = rat.id
FROM ruoli_azienda_tipi rat
WHERE ra.ruolo = rat.nome
  AND ra.ruolo_tipo_id IS NULL;

-- Step 3 (opzionale): Pulire campo text
-- UPDATE ruoli_azienda SET ruolo = NULL WHERE ruolo_tipo_id IS NOT NULL;
```

---

## 9. Test e Validazione

### 9.1 Test Backend

**Test API:**
```bash
# Login
TOKEN=$(curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}' | jq -r '.access_token')

# Get ruoli soggetto
curl http://localhost:8000/api/v1/anagrafica/ruoli-azienda/soggetto/1 \
  -H "Authorization: Bearer $TOKEN"

# Create ruolo
curl -X POST http://localhost:8000/api/v1/anagrafica/ruoli-azienda/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "persona_fisica_id": 1,
    "persona_giuridica_id": 2,
    "ruolo": "Amministratore Delegato",
    "data_inizio": "2025-01-01"
  }'

# Merge ruoli duplicati
curl -X POST http://localhost:8000/api/v1/anagrafica/domini/ruoli-azienda-tipi/merge \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"source_id": 5, "target_id": 3}'
```

### 9.2 Test Frontend

**Checklist:**
- [ ] Accesso a `/anagrafiche/domini/ruoli-azienda` mostra lista tipi
- [ ] Creazione nuovo tipo ruolo funziona
- [ ] Autocomplete in RuoloAziendaForm mostra suggerimenti
- [ ] Merge di due ruoli aggiorna associazioni
- [ ] Filtro "Solo attivi" nasconde ruoli disattivati
- [ ] Disattivare ruolo lo nasconde dall'autocomplete
- [ ] Badge "Attivo/Inattivo" visibili correttamente

---

## 10. Roadmap Futura

### 10.1 Funzionalità Avanzate (Opzionali)

#### Storico Ruoli con Audit Trail
- [ ] Tracciare chi ha creato/modificato ogni assegnazione
- [ ] Log delle modifiche (chi, quando, cosa)

#### Ruoli con Deleghe
- [ ] Ruolo con delega temporanea a terzi
- [ ] Es: "Mario AD delega a Maria dal 01/06 al 30/06"

#### Organigrammi Visuali
- [ ] Grafico interattivo delle relazioni persona-azienda
- [ ] Export organigramma in PDF

#### Notifiche Scadenze
- [ ] Alert quando un ruolo sta per scadere
- [ ] Email automatica N giorni prima della data_fine

#### Import Bulk
- [ ] Import CSV di associazioni multiple
- [ ] Validazione e preview prima del commit

---

## 11. FAQ

### Q: Posso associare una persona a più aziende?
**A:** Sì, una persona può avere ruoli in più aziende contemporaneamente.

### Q: Posso avere più persone con lo stesso ruolo nella stessa azienda?
**A:** Sì, non ci sono vincoli di unicità. Es: ACME può avere 3 soci.

### Q: Cosa succede se cancello un tipo di ruolo usato?
**A:** Le associazioni esistenti sono mantenute (FK con ON DELETE SET NULL). Il nome rimane salvato nel campo `ruolo` text.

### Q: Come gestisco un ruolo temporaneo (es: interim)?
**A:** Usa data_inizio e data_fine. Es: "Mario AD interim dal 01/01 al 31/03".

### Q: Posso inserire ruoli custom non in lista?
**A:** Sì! Scrivi liberamente nel campo ruolo. Poi l'admin può normalizzare creando il tipo in `ruoli_azienda_tipi`.

---

## 12. File Modificati/Creati

### Backend
- ✅ `backend/modules/anagrafica_italiana/models/ruolo_azienda_tipo.py` (NEW)
- ✅ `backend/modules/anagrafica_italiana/models/ruolo_azienda.py` (MODIFIED)
- ✅ `backend/modules/anagrafica_italiana/schemas/ruolo_azienda_tipo.py` (NEW)
- ✅ `backend/modules/anagrafica_italiana/routes/ruoli_azienda_tipi.py` (NEW)
- ✅ `backend/modules/anagrafica_italiana/routes/ruoli_azienda.py` (routes già esistenti)

### Frontend
- ✅ `frontend/src/modules/anagrafica_italiana/components/RuoliAziendaTipi/RuoliAziendaTipiList.jsx` (NEW)
- ✅ `frontend/src/modules/anagrafica_italiana/components/RuoliAziendaTipi/RuoloAziendaTipoForm.jsx` (NEW)
- ✅ `frontend/src/modules/anagrafica_italiana/components/RuoliAziendaTipi/RuoliAziendaTipi.css` (NEW)
- ✅ `frontend/src/modules/anagrafica_italiana/components/RuoliAzienda/RuoloAziendaForm.jsx` (MODIFIED - autocomplete)
- ✅ `frontend/src/modules/anagrafica_italiana/services/anagraficaAPI.js` (MODIFIED - nuovi endpoint)
- ✅ `frontend/src/modules/anagrafica_italiana/index.js` (MODIFIED - export RuoliAziendaTipiList)
- ✅ `frontend/src/App.jsx` (MODIFIED - route /anagrafiche/domini/ruoli-azienda)

### Database
- ✅ Tabella `ruoli_azienda_tipi` (NEW)
- ✅ Tabella `ruoli_azienda` (MODIFIED - aggiunti ruolo_tipo_id, ruolo nullable)

---

## 13. Conclusioni

### Stato Implementazione: ✅ COMPLETO

Il sistema Ruoli Azienda è **completamente funzionale** con:
- ✅ Backend: modelli, API, validazioni
- ✅ Frontend: gestione domini, autocomplete, merge
- ✅ Database: schema migrato e funzionante
- ✅ Integrazione: componenti riutilizzabili

### Unica Pagina Mancante: RuoliAziendaList

La **lista centralizzata** delle associazioni è l'unico componente da creare per completezza (non bloccante).

### Valore Aggiunto

Questo sistema permette di:
1. **Tracciare organizzazione aziendale**: Chi lavora per chi, con quale ruolo
2. **Normalizzare dati**: Ruoli standard riutilizzabili, no duplicati
3. **Gestire storico**: Date inizio/fine per tracciare cambiamenti nel tempo
4. **Scalabilità**: Facile aggiungere nuovi ruoli, merge duplicati
5. **UX migliore**: Autocomplete velocizza inserimento, riduce errori

---

*Documento creato il 9 Dicembre 2025*
*Ultima modifica: 9 Dicembre 2025*
