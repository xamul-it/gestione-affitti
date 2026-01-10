# Addendum: Integrazioni Prezzi e Filtri Immobili

**Versione:** 1.1
**Data:** 28 Dicembre 2025
**Modifiche:** Integrazione prezzi portali e filtro immobili affitti brevi

---

## Analisi Integrazioni API Portali di Prenotazione

### Ricerca Fattibilità (Dicembre 2025)

Ho analizzato la disponibilità delle API dei principali portali:

#### **Booking.com**
- ❌ **NO API pubblica disponibile**
- ❌ Accesso limitato a Connectivity Partners approvati
- ❌ Nuove registrazioni partner **chiuse** al momento
- **Complessità:** ALTA
- **Conclusione:** Non fattibile senza partnership formale

[Fonte: Booking.com Developers](https://developers.booking.com/connectivity/docs/ari)

#### **Airbnb**
- ❌ **NO API pubblica disponibile**
- ❌ Accesso solo per partner pre-approvati (Airbnb contatta loro i partner)
- ⚠️ **Cambio fee structure 2025:** 15.5% flat su host (prima 3% host + 14-16% guest)
- **Complessità:** ALTA
- **Conclusione:** Non fattibile per sviluppatori indipendenti

[Fonte: Elfsight - Airbnb API Guide](https://elfsight.com/blog/how-to-get-and-use-airbnb-api-partnership-and-integration/)

#### **Vrbo (HomeAway/Expedia Group)**
- ✅ **API disponibile per Property Manager**
- ✅ Contatto: pmsalesinquiry@expediagroup.com
- ✅ Sync real-time di availability, pricing, reservations
- ✅ Messaging integrato
- ⚠️ **Requisito:** Solo "Hotel Collect" (pagamenti gestiti dalla struttura, non da Vrbo)
- **Complessità:** MEDIA
- **Conclusione:** Fattibile ma richiede partnership e cambio modello pagamenti

[Fonti: Vrbo Integration Central](https://integration-central.vrbo.com/t), [Hostaway - Vrbo API](https://support.hostaway.com/hc/en-us/articles/34221390021275)

---

## Soluzione Raccomandata: Approccio Ibrido

### Fase 1: MVP - Link Esterni + Parsing iCal (SEMPLICE)

**Implementazione immediata** senza necessità di partnership:

#### 1.1 Aggiunte al Modello `CalendarioICal`

```python
class CalendarioICal(Base):
    # ... campi esistenti ...

    # NUOVO: Link diretto alla dashboard del portale
    url_dashboard_portale: str | None  # URL alla piattaforma per gestire prenotazioni
    note_accesso: str | None           # Credenziali/note per accesso

    # NUOVO: Configurazione parsing prezzi
    campo_prezzo_ical: str | None      # Es: "DESCRIPTION", "X-PRICE"
    pattern_parsing_prezzo: str | None # Regex per estrarre prezzo da description
```

**Esempio configurazione:**
- **Portale:** Booking.com
- **URL iCal:** `https://admin.booking.com/hotel/hoteladmin/ical/...?t=xyz123`
- **URL Dashboard:** `https://admin.booking.com/hotel/hoteladmin/extranet_ng/manage/booking.html?hotel_id=12345`
- **Pattern parsing:** `r'Importo:?\s*€?\s*(\d+(?:[.,]\d{2})?)'`

#### 1.2 Aggiunte al Modello `Prenotazione`

```python
class Prenotazione(Base):
    # ... campi esistenti ...

    # NUOVO: Gestione prezzi
    prezzo_per_notte: Decimal | None      # Prezzo medio per notte (totale/notti)
    prezzo_inserito_manualmente: bool     # Flag se prezzo è manuale
    valuta: str                           # EUR, USD, GBP, ecc.

    # NUOVO: Link diretto alla prenotazione sul portale
    url_prenotazione_portale: str | None  # Link diretto (se costruibile)
```

**Calcolo automatico `prezzo_per_notte`:**
```python
if importo_totale and numero_notti:
    prezzo_per_notte = importo_totale / numero_notti
```

#### 1.3 Parsing Intelligente del Campo DESCRIPTION iCal

Molti portali includono informazioni strutturate nel campo `DESCRIPTION` dell'evento iCal:

**Esempio Booking.com:**
```
DESCRIPTION:Prenotazione BK123456\n
Ospite: Mario Rossi\n
Adulti: 2, Bambini: 1\n
Importo totale: EUR 450.00\n
Email: mario.rossi@example.com
```

**Servizio di parsing:**
```python
# affitti_brevi/services/ical_parser.py

import re
from decimal import Decimal

PATTERNS_PREZZO = {
    'booking': r'Importo totale:?\s*EUR\s*(\d+(?:[.,]\d{2})?)',
    'airbnb': r'Total:?\s*€(\d+(?:[.,]\d{2})?)',
    'vrbo': r'Total:?\s*\$(\d+(?:[.,]\d{2})?)',
    'generic': r'(?:Importo|Total|Price):?\s*[€$£]?\s*(\d+(?:[.,]\d{2})?)'
}

def extract_price_from_description(description: str, portale: str) -> Decimal | None:
    """
    Tenta di estrarre il prezzo dal campo DESCRIPTION dell'iCal
    """
    if not description:
        return None

    pattern = PATTERNS_PREZZO.get(portale.lower(), PATTERNS_PREZZO['generic'])
    match = re.search(pattern, description, re.IGNORECASE)

    if match:
        price_str = match.group(1).replace(',', '.')
        return Decimal(price_str)

    return None
```

#### 1.4 UI: Link Esterni Integrati

**Componente: `PrenotazioneActions.jsx`**

```jsx
function PrenotazioneActions({ prenotazione, calendario }) {
  return (
    <div className="actions">
      {/* Link alla piattaforma */}
      {calendario?.url_dashboard_portale && (
        <a
          href={calendario.url_dashboard_portale}
          target="_blank"
          rel="noopener noreferrer"
          className="btn btn-secondary"
        >
          <i className="icon-external-link"></i>
          Apri in {calendario.portale}
        </a>
      )}

      {/* Link diretto alla prenotazione (se disponibile) */}
      {prenotazione?.url_prenotazione_portale && (
        <a
          href={prenotazione.url_prenotazione_portale}
          target="_blank"
          rel="noopener noreferrer"
          className="btn btn-primary"
        >
          <i className="icon-booking"></i>
          Dettagli Prenotazione
        </a>
      )}

      {/* Modifica prezzo manuale */}
      <button onClick={handleEditPrice}>
        <i className="icon-edit"></i>
        {prenotazione.prezzo_inserito_manualmente ? 'Modifica Prezzo' : 'Inserisci Prezzo'}
      </button>
    </div>
  );
}
```

**Visualizzazione inline (optional):**

Per evitare di "uscire" completamente dal sito, si può aggiungere un modal con iframe:

```jsx
function PortaleModal({ url, portale, onClose }) {
  return (
    <Modal size="fullscreen" onClose={onClose}>
      <Modal.Header>
        Dashboard {portale}
        <button onClick={onClose}>Chiudi</button>
      </Modal.Header>
      <Modal.Body>
        <iframe
          src={url}
          style={{ width: '100%', height: '90vh', border: 'none' }}
          title={`Dashboard ${portale}`}
        />
      </Modal.Body>
    </Modal>
  );
}
```

**⚠️ Limitazione iframe:**
Molti portali (Booking, Airbnb) bloccano l'embedding via `X-Frame-Options: DENY`. In questo caso, il link esterno rimane l'unica opzione.

---

### Fase 2: Integrazione API Vrbo (OPZIONALE - Se necessario)

Se il cliente gestisce molte proprietà e vuole:
- Sync real-time bidirezionale
- Aggiornamento prezzi automatico da sistema
- Gestione messaggi ospiti integrata

Allora vale la pena investire nell'integrazione API Vrbo.

**Requisiti:**
1. Contattare Vrbo: pmsalesinquiry@expediagroup.com
2. Ottenere credenziali API
3. Passare a "Hotel Collect" (pagamenti gestiti dalla struttura)
4. Implementare OAuth2 authentication

**Endpoint esempio:**
```python
# Sync prezzi da Vrbo
GET /vrbo/api/v1/properties/{property_id}/rates

# Aggiorna disponibilità verso Vrbo
PUT /vrbo/api/v1/properties/{property_id}/availability
```

**Stima implementazione:** 2-3 settimane sviluppo + test

---

## Filtro Immobili per Affitti Brevi

### Problema
Non tutti gli immobili nel modulo `immobili` sono destinati ad affitti brevi. Servono filtri per identificare quali unità sono gestite per turismo breve.

### Soluzione 1: Campo Destinazione d'Uso

**Aggiunta al modello `UnitaImmobiliare`:**

```python
# modules/immobili/models/unita_immobiliare.py

class UnitaImmobiliare(Base):
    # ... campi esistenti ...

    # NUOVO
    destinazione_uso: str | None  # RESIDENZIALE, AFFITTO_BREVE, AFFITTO_LUNGO, COMMERCIALE
    attiva_affitti_brevi: bool    # Flag rapido per query
```

**Valori enum:**
```python
class DestinazioneUso(str, Enum):
    RESIDENZIALE = "RESIDENZIALE"           # Abitazione proprietario
    AFFITTO_BREVE = "AFFITTO_BREVE"         # Turismo < 30 giorni
    AFFITTO_LUNGO = "AFFITTO_LUNGO"         # Contratti > 30 giorni
    COMMERCIALE = "COMMERCIALE"             # Negozi, uffici
    MAGAZZINO = "MAGAZZINO"                 # Box, cantine
    MISTO = "MISTO"                         # Uso promiscuo
```

### Soluzione 2: Tabella di Associazione (più flessibile)

Se un immobile può avere **uso misto** (es. affitto breve in estate, lungo in inverno):

```python
class UnitaModuloAttivo(Base):
    """
    Associazione unità immobiliare → modulo attivo
    """
    __tablename__ = "unita_modulo_attivo"

    id: int
    unita_immobiliare_id: int
    modulo: str                    # AFFITTI_BREVI, AFFITTI_LUNGO
    data_inizio: date | None       # Periodo attivazione
    data_fine: date | None
    attivo: bool

    tenant_id: int
```

**Query esempio:**
```python
# Immobili attivi per affitti brevi
SELECT u.*
FROM unita_immobiliari u
JOIN unita_modulo_attivo m ON u.id = m.unita_immobiliare_id
WHERE m.modulo = 'AFFITTI_BREVI'
  AND m.attivo = true
  AND (m.data_fine IS NULL OR m.data_fine >= CURRENT_DATE)
```

### UI: Filtro Dropdown

**Componente: `CalendariForm.jsx`**

```jsx
function CalendariForm() {
  const [immobili, setImmobili] = useState([]);

  useEffect(() => {
    // Carica solo immobili con affitti brevi attivi
    api.get('/immobili/unita-immobiliari/?destinazione_uso=AFFITTO_BREVE')
       .then(res => setImmobili(res.data));
  }, []);

  return (
    <form>
      <FormGroup>
        <label>Appartamento *</label>
        <select name="unita_immobiliare_id" required>
          <option value="">-- Seleziona --</option>
          {immobili.map(u => (
            <option key={u.id} value={u.id}>
              {u.codice} - {u.indirizzo}
            </option>
          ))}
        </select>
      </FormGroup>

      {/* ... altri campi ... */}
    </form>
  );
}
```

### Configurazione Iniziale

**Endpoint per attivare affitti brevi su un immobile:**

```python
# POST /api/v1/immobili/unita-immobiliari/{id}/attiva-modulo
{
  "modulo": "AFFITTI_BREVI",
  "data_inizio": "2025-01-01"
}
```

**UI: Toggle nella scheda immobile:**

```jsx
function UnitaImmobiliareDetail({ unita }) {
  const [affittiBreviAttivi, setAffittiBreviAttivi] = useState(unita.attiva_affitti_brevi);

  const handleToggle = async () => {
    await api.post(`/immobili/unita-immobiliari/${unita.id}/attiva-modulo`, {
      modulo: 'AFFITTI_BREVI',
      attivo: !affittiBreviAttivi
    });
    setAffittiBreviAttivi(!affittiBreviAttivi);
  };

  return (
    <div className="module-activation">
      <label>
        <input
          type="checkbox"
          checked={affittiBreviAttivi}
          onChange={handleToggle}
        />
        Abilita gestione affitti brevi
      </label>

      {affittiBreviAttivi && (
        <Link to={`/affitti-brevi/calendari/nuovo?unita_id=${unita.id}`}>
          + Configura calendario iCal
        </Link>
      )}
    </div>
  );
}
```

---

## Calcolo Tassa di Soggiorno con Prezzi

### Problema Originale
Alcune tasse di soggiorno sono calcolate come **percentuale del prezzo** (es. 5% fino a max €5/notte).

### Requisiti Prezzi

Per il calcolo corretto, serve:
1. **Prezzo totale prenotazione** (già presente: `importo_totale`)
2. **Prezzo per notte** (nuovo campo calcolato)
3. **Prezzo per notte per persona** (calcolato: `prezzo_per_notte / numero_ospiti`)

### Formula Estesa

```python
def calcola_tassa_percentuale(prenotazione, config):
    """
    Calcola tassa come percentuale del prezzo per notte per persona
    """
    # Prezzo base
    prezzo_per_notte = prenotazione.importo_totale / prenotazione.numero_notti
    prezzo_per_persona = prezzo_per_notte / prenotazione.numero_ospiti_paganti

    # Tassa per persona per notte
    tassa_per_notte = prezzo_per_persona * (config.percentuale / 100)

    # Applica max
    if config.importo_massimo:
        tassa_per_notte = min(tassa_per_notte, config.importo_massimo)

    # Totale
    notti_tassabili = min(prenotazione.numero_notti, config.max_notti_tassabili or 999)

    tassa_totale = 0
    for ospite in prenotazione.ospiti:
        if not ospite.esente_tassa_soggiorno:
            tassa_totale += tassa_per_notte * notti_tassabili

    return round(tassa_totale, 2)
```

### Esempio Pratico

**Prenotazione:**
- Appartamento: Firenze
- 3 notti, 2 adulti + 1 bambino (10 anni)
- Importo totale: €450
- Prezzo per notte: €450 / 3 = €150
- Prezzo per persona/notte: €150 / 3 = €50

**Tariffa Firenze:**
- 5% del prezzo per persona, max €5/notte
- Bambini < 12 anni esenti

**Calcolo:**
- Adulto 1: €50 × 5% = €2.50 × 3 notti = €7.50
- Adulto 2: €50 × 5% = €2.50 × 3 notti = €7.50
- Bambino: €0 (esente)
- **Totale: €15**

### Configurazione UI

**Form `TassaSoggiornoConfig`:**

```jsx
function TassaConfigForm() {
  const [tipoCalcolo, setTipoCalcolo] = useState('FISSO');

  return (
    <form>
      <FormGroup>
        <label>Tipo calcolo *</label>
        <select value={tipoCalcolo} onChange={e => setTipoCalcolo(e.target.value)}>
          <option value="FISSO">Importo fisso per notte</option>
          <option value="PERCENTUALE">Percentuale sul prezzo</option>
          <option value="SCAGLIONI">Scaglioni per tipologia</option>
        </select>
      </FormGroup>

      {tipoCalcolo === 'FISSO' && (
        <FormGroup>
          <label>Importo per notte (€)</label>
          <input type="number" step="0.01" name="importo_per_notte" />
        </FormGroup>
      )}

      {tipoCalcolo === 'PERCENTUALE' && (
        <>
          <FormGroup>
            <label>Percentuale (%)</label>
            <input type="number" step="0.1" name="percentuale" />
          </FormGroup>
          <FormGroup>
            <label>Importo massimo per notte (€)</label>
            <input type="number" step="0.01" name="importo_massimo" />
          </FormGroup>
          <Alert type="info">
            La tassa sarà calcolata come percentuale del prezzo per persona per notte,
            con tetto massimo specificato.
          </Alert>
        </>
      )}

      {/* ... altri campi ... */}
    </form>
  );
}
```

---

## Gestione Ritenute Fiscali (Bonus)

### Nuovo Requisito Identificato

Per gli affitti brevi, serve calcolare anche le **ritenute d'acconto** del 21% sui redditi da locazione.

### Aggiunta al Modello

```python
class Prenotazione(Base):
    # ... campi esistenti ...

    # NUOVO: Ritenute fiscali
    ritenuta_acconto_percentuale: Decimal  # Default 21%
    ritenuta_acconto_importo: Decimal | None  # Calcolato
    netto_incassato: Decimal | None  # importo_totale - ritenuta
```

**Calcolo:**
```python
# Per cedolare secca 21%
ritenuta = importo_totale * 0.21
netto = importo_totale - ritenuta
```

### Report Fiscale

**Endpoint:**
```
GET /api/v1/affitti-brevi/report/fiscale?anno=2025&trimestre=1
```

**Risposta:**
```json
{
  "periodo": "Q1 2025",
  "totale_incassi_lordi": 15000.00,
  "totale_ritenute": 3150.00,
  "totale_netto": 11850.00,
  "totale_tasse_soggiorno": 450.00,
  "numero_prenotazioni": 45,
  "dettaglio_per_immobile": [...]
}
```

---

## Allineamento Tariffario tra Piattaforme

### Problema
Verificare che lo stesso appartamento abbia prezzi allineati su Booking, Airbnb, Vrbo.

### Soluzione: Report Comparativo

**Endpoint:**
```
GET /api/v1/affitti-brevi/report/comparazione-prezzi?unita_id=123&data_from=2025-01-01&data_to=2025-03-31
```

**Dashboard UI:**

| Data | Booking.com | Airbnb | Vrbo | Differenza |
|------|-------------|--------|------|------------|
| 15/01 | €120 | €125 | €120 | ⚠️ +€5 Airbnb |
| 16/01 | €120 | €120 | €120 | ✅ Allineato |
| 20/01 | - | €150 | €145 | ⚠️ +€5 Airbnb |

**Alert automatici:**
- Notifica se differenza > 10% tra portali
- Suggerimento aggiornamento prezzi

---

## Riepilogo Raccomandazioni

### ✅ Implementare Subito (MVP)

1. **Campo `destinazione_uso` in `UnitaImmobiliare`**
   - Filtro immobili per affitti brevi
   - Toggle attivazione modulo

2. **Campo `url_dashboard_portale` in `CalendarioICal`**
   - Link esterno alla piattaforma
   - Pulsante "Apri in Booking.com" nell'UI

3. **Campo `prezzo_per_notte` in `Prenotazione`**
   - Calcolo automatico da `importo_totale / numero_notti`
   - Parsing da campo DESCRIPTION iCal (best-effort)
   - Possibilità inserimento/modifica manuale

4. **Supporto tassa percentuale sul prezzo**
   - Formula estesa nel `TassaSoggiornoService`
   - UI configurazione con tipo "Percentuale"

### 🔄 Miglioramenti Futuri (Post-MVP)

1. **Parser intelligente iCal**
   - Pattern multipli per portale
   - Configurazione custom per portale non standard
   - Fallback manuale se parsing fallisce

2. **Modal iframe per portali**
   - Tentativo embedding (se portale lo permette)
   - Altrimenti apertura tab esterno

3. **Report comparazione prezzi**
   - Dashboard allineamento tariffario
   - Alert differenze > 10%

### 🚀 Opzionale Avanzato (Se Budget)

1. **Integrazione API Vrbo**
   - Sync bidirezionale real-time
   - Gestione messaggi ospiti
   - Costo: 2-3 settimane sviluppo + partnership

2. **Integrazione Channel Manager esistente**
   - Se il cliente usa già Hostaway, Lodgify, Guesty
   - API unificate per tutti i portali
   - Costo variabile

---

## Modifiche al Documento Principale

### Sezioni da Aggiornare

#### **Sezione 4.1 - Tabella `calendario_ical`**

Aggiungere campi:
```python
url_dashboard_portale: str | None
note_accesso: str | None
campo_prezzo_ical: str | None
pattern_parsing_prezzo: str | None
```

#### **Sezione 4.2 - Tabella `prenotazioni`**

Aggiungere campi:
```python
prezzo_per_notte: Decimal | None
prezzo_inserito_manualmente: bool
url_prenotazione_portale: str | None

# Ritenute fiscali
ritenuta_acconto_percentuale: Decimal
ritenuta_acconto_importo: Decimal | None
netto_incassato: Decimal | None
```

#### **Sezione 4.4 - Tabella `tassa_soggiorno_config`**

Campo già presente, ma chiarire utilizzo:
```python
tipo_calcolo: str  # FISSO, PERCENTUALE, SCAGLIONI

# Se tipo_calcolo = PERCENTUALE, usa:
percentuale: Decimal  # Es: 5.0 (= 5%)
importo_massimo: Decimal  # Es: 5.00 (tetto €5/notte)
```

#### **Nuova Sezione 5.7 - Report Fiscali**

```
GET /api/v1/affitti-brevi/report/fiscale
GET /api/v1/affitti-brevi/report/comparazione-prezzi
```

#### **Sezione 6 - UI**

Aggiungere:
- **Pulsante "Apri in [Portale]"** in dettaglio prenotazione
- **Form modifica prezzo manuale** con flag override
- **Dashboard comparazione prezzi** (opzionale)

#### **Sezione 8.1 - Integrazioni Esterne**

Aggiungere:
- **Parsing prezzi da iCal** (best-effort)
- **Integrazione API Vrbo** (opzionale)
- **Link diretti portali** (soluzione semplice MVP)

---

## Fonti

- [Booking.com Developers - Rates & Availability API](https://developers.booking.com/connectivity/docs/ari)
- [Elfsight - How to use Airbnb API](https://elfsight.com/blog/how-to-get-and-use-airbnb-api-partnership-and-integration/)
- [Vrbo Integration Central](https://integration-central.vrbo.com/t)
- [Hostaway - Advantages of Vrbo API](https://support.hostaway.com/hc/en-us/articles/34221390021275)
- [OwnerRez - Airbnb Service Fee Changes 2025](https://www.ownerrez.com/support/articles/email-blast-2025-08-28-airbnb-service-fee-changes-for-api-hosts)

---

**Fine Addendum**

Versione 1.1 - 28 Dicembre 2025
