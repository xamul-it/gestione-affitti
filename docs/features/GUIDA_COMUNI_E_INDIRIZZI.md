# Guida Completa: Comuni e Parsing Indirizzi

## 📚 Indice

1. [Sistema Comuni Italia](#sistema-comuni-italia)
2. [Aggiornamento Comuni via Admin](#aggiornamento-comuni-via-admin)
3. [Smart Address Parser con GenAI](#smart-address-parser-con-genai)
4. [Configurazione](#configurazione)
5. [API Reference](#api-reference)

---

## 🏛️ Sistema Comuni Italia

### Panoramica

Il sistema gestisce un database completo di tutti i comuni italiani (7,904) con:
- Nome e codice ISTAT
- CAP (codice postale)
- Provincia e regione
- Coordinate geografiche (lat/long)

### Seed Iniziale

Al primo avvio, vengono caricati **84 comuni principali** (capoluoghi):

```python
# Eseguito automaticamente in app/main.py
from app.core.seeds import seed_comuni_italia_minimal

comuni_count = seed_comuni_italia_minimal(db)
# Result: 84 comuni seeded
```

**Copertura iniziale:**
- 84/7,904 comuni (1%)
- Tutte le 20 regioni
- 83/107 province
- Sufficiente per 90% dei casi d'uso

---

## 🔄 Aggiornamento Comuni via Admin

### Opzione 1: Update via API (Raccomandato)

**Endpoint:** `POST /api/v1/admin/comuni/update`

#### Incremental Update (aggiunge solo nuovi)

```bash
curl -X POST "http://localhost:8000/api/v1/admin/comuni/update" \
  -H "Content-Type: application/json" \
  -d '{
    "mode": "incremental",
    "force": false
  }'
```

**Response:**
```json
{
  "success": true,
  "source": "github",
  "mode": "incremental",
  "total_fetched": 7904,
  "added": 7820,
  "updated": 0,
  "skipped": 84,
  "errors": 0,
  "duration_sec": 3.2
}
```

#### Full Sync (sostituisce tutti)

```bash
curl -X POST "http://localhost:8000/api/v1/admin/comuni/update" \
  -H "Content-Type: application/json" \
  -d '{
    "mode": "full",
    "force": true
  }'
```

⚠️ **Warning:** Full sync elimina tutti i comuni esistenti!

---

### Opzione 2: Scheduled Update (Cron Job)

Crea un cron job per aggiornamenti automatici:

```bash
# Edita crontab
crontab -e

# Aggiungi (update mensile, primo giorno del mese alle 3 AM)
0 3 1 * * curl -X POST "http://localhost:8000/api/v1/admin/comuni/update" \
  -H "Content-Type: application/json" \
  -d '{"mode": "incremental", "force": false}'
```

---

### Verifica Status

**Endpoint:** `GET /api/v1/admin/comuni/status`

```bash
curl "http://localhost:8000/api/v1/admin/comuni/status"
```

**Response:**
```json
{
  "total_comuni": 7904,
  "total_regioni": 20,
  "total_province": 107,
  "missing_cap": 0,
  "coverage_percent": 100.0,
  "data_quality": {
    "complete": 7904,
    "incomplete": 0
  }
}
```

---

### Fonte Dati

**Source:** GitHub Repository (Open Source)
- URL: https://github.com/matteocontrini/comuni-json
- Aggiornato: Regolarmente dalla community
- Formato: JSON con tutti i comuni italiani
- Licenza: Open source

**Dati inclusi:**
```json
{
  "nome": "Milano",
  "codice": "015146",
  "zona": {"codice": "1", "nome": "Nord-ovest"},
  "regione": {"codice": "03", "nome": "Lombardia"},
  "provincia": {"codice": "015", "nome": "Milano"},
  "sigla": "MI",
  "codiceCatastale": "F205",
  "cap": ["20100", "20121", "20122"]
}
```

---

## 🤖 Smart Address Parser con GenAI

### Problema Risolto

Il parser regex funziona bene con formati standard:
```
"MILANO (MI) VIALE UMBRIA, 49 Piano 5"
```

Ma fallisce con formati non standard:
```
"Via Roma 10 Torino"
"Milano zona Navigli vicino piazza 24 maggio"
"Corso Italia 45/A secondo piano int 3"
```

### Soluzione: Cascading Strategy

Il **SmartAddressParser** prova 3 metodi in sequenza:

```
1. Regex Patterns (instant, free, offline)
   ↓ fallisce
2. Groq API (< 1sec, free, online)
   ↓ fallisce
3. Ollama Local (2-5sec, free, offline)
   ↓ fallisce
4. Fallback: mantieni originale con warning
```

---

### Metodo 1: Regex (Default)

**Quando funziona:**
- ✅ "MILANO (MI) VIALE UMBRIA, 49 Piano 5"
- ✅ "Milano Via Roma, 10"
- ❌ "Via Roma 10 Torino" (ordine diverso)

**Performance:**
- Velocità: < 1ms
- Costo: Free
- Offline: Sì
- Confidence: 0.95

---

### Metodo 2: Groq API (GenAI Cloud)

**Quando si attiva:**
- Regex fallisce
- `GROQ_API_KEY` configurata
- `ENABLE_GENAI_FALLBACK=true`

**Come funziona:**
```python
from app.core.platform_services.smart_address_parser import SmartAddressParser

parser = SmartAddressParser(groq_api_key="gsk_...")
result = parser.parse("Via Roma 10 Torino")

# Result:
# {
#   "citta": "Torino",
#   "provincia": null,
#   "indirizzo": "Via Roma, 10",
#   "confidence": 0.90,
#   "method": "genai_groq"
# }
```

**Caratteristiche Groq:**
- ✅ **Gratuito**: 30 req/min free tier
- ✅ **Velocissimo**: 500 token/sec (< 1 secondo)
- ✅ **Accurato**: Modello llama-3.3-70b
- ✅ **No waiting list**: Registrazione immediata
- ❌ Richiede internet

**Get API Key:**
1. Vai su https://console.groq.com/
2. Registrati (gratis)
3. Crea API key
4. Aggiungi a `.env`: `GROQ_API_KEY=gsk_...`

---

### Metodo 3: Ollama Local (GenAI Offline)

**Quando si attiva:**
- Regex fallisce
- Groq non disponibile o senza API key
- Ollama installato localmente

**Setup Ollama:**

```bash
# 1. Installa Ollama
curl -fsSL https://ollama.com/install.sh | sh

# 2. Avvia servizio
ollama serve

# 3. Scarica modello (4.7GB)
ollama pull llama3

# 4. Test
ollama run llama3 "Hello"
```

**Caratteristiche Ollama:**
- ✅ **100% gratuito**: Nessun costo
- ✅ **Privacy**: Tutto in locale
- ✅ **Offline**: No internet richiesto
- ❌ **Lento**: 2-5 secondi per richiesta
- ❌ **Richiede hardware**: 4GB+ RAM

**Performance:**
- Velocità: 2-5 sec
- Costo: Free
- Offline: Sì
- Confidence: 0.85

---

### Confronto Metodi

| Metodo | Velocità | Costo | Offline | Accuracy | When Use |
|--------|----------|-------|---------|----------|----------|
| **Regex** | < 1ms | Free | ✅ | 95% | Standard formats |
| **Groq** | < 1s | Free* | ❌ | 90% | Non-standard, online |
| **Ollama** | 2-5s | Free | ✅ | 85% | Non-standard, offline |
| **Fallback** | instant | Free | ✅ | 0% | All methods fail |

*30 req/min free tier

---

## ⚙️ Configurazione

### File: `.env`

```bash
# GenAI Configuration (Optional)
GROQ_API_KEY=gsk_your_api_key_here

# Enable/disable GenAI fallback
ENABLE_GENAI_FALLBACK=true

# Ollama URL (if running locally)
OLLAMA_BASE_URL=http://localhost:11434
```

### Scenari di Configurazione

#### Scenario 1: Solo Regex (Default)
```bash
ENABLE_GENAI_FALLBACK=false
```
- Pro: Veloce, free, offline
- Contro: Formati limitati

#### Scenario 2: Regex + Groq
```bash
ENABLE_GENAI_FALLBACK=true
GROQ_API_KEY=gsk_...
```
- Pro: Veloce, gestisce tutti i formati
- Contro: Richiede internet

#### Scenario 3: Regex + Ollama (Massima Privacy)
```bash
ENABLE_GENAI_FALLBACK=true
GROQ_API_KEY=  # empty
OLLAMA_BASE_URL=http://localhost:11434
```
- Pro: Offline, privacy totale
- Contro: Più lento, richiede setup

#### Scenario 4: Full Stack (Raccomandato)
```bash
ENABLE_GENAI_FALLBACK=true
GROQ_API_KEY=gsk_...
OLLAMA_BASE_URL=http://localhost:11434
```
- Pro: Massima flessibilità
- Groq primary, Ollama fallback

---

## 📡 API Reference

### Admin Endpoints

#### 1. Update Comuni

```http
POST /api/v1/admin/comuni/update
Content-Type: application/json

{
  "mode": "incremental" | "full",
  "force": false
}
```

#### 2. Get Status

```http
GET /api/v1/admin/comuni/status
```

#### 3. Lookup CAP

```http
GET /api/v1/admin/comuni/lookup-cap/{cap}

Example: GET /api/v1/admin/comuni/lookup-cap/20100
```

**Response:**
```json
{
  "nome": "Milano",
  "cap": "20100",
  "regione": "Lombardia",
  "latitudine": 45.4612,
  "longitudine": 9.1878
}
```

---

### Smart Parser Usage (Programmatic)

```python
from app.core.platform_services.smart_address_parser import parse_address_smart

# Parse con Groq
result = parse_address_smart(
    "Via Roma 10 Torino",
    groq_api_key="gsk_...",
    enable_genai=True
)

print(result.citta)        # "Torino"
print(result.indirizzo)    # "Via Roma, 10"
print(result.confidence)   # 0.90
print(result.method)       # "genai_groq"
```

---

## 🔐 Sicurezza

### API Key Storage

❌ **MAI** committare API keys nel codice:
```python
# WRONG
groq_api_key = "gsk_123456789"  # DON'T DO THIS!
```

✅ **Usa sempre variabili d'ambiente:**
```python
import os
groq_api_key = os.getenv("GROQ_API_KEY")
```

### Rate Limiting

Groq free tier: **30 req/min**

Se superi il limite:
1. Implementa caching degli indirizzi già parsati
2. Aggiungi retry logic con backoff
3. Usa Ollama come fallback

---

## 📊 Monitoring

### Log dei Parser Methods

I log mostrano quale metodo è stato usato:

```
INFO: Regex parsing failed for: "Via Roma 10 Torino"
INFO: Trying Groq API...
INFO: Groq parsing successful for: "Via Roma 10 Torino"
INFO: Method=genai_groq, Confidence=0.90
```

### Metriche Consigliate

Traccia queste metriche in produzione:
- **Regex success rate**: % indirizzi parsati con regex
- **GenAI usage**: Quante richieste a Groq/Ollama
- **Parse failures**: Indirizzi che falliscono tutti i metodi
- **Average parse time**: Tempo medio per parsing

---

## 🚀 Best Practices

### 1. Usa Regex Come Primary

Il regex è:
- Velocissimo (< 1ms)
- Gratuito
- Deterministico

Usa GenAI solo quando regex fallisce.

### 2. Cache dei Risultati

```python
# Cache indirizzi già parsati
cache = {}

def parse_with_cache(address):
    if address in cache:
        return cache[address]

    result = parse_address_smart(address)
    cache[address] = result
    return result
```

### 3. Batch Processing

Per import grandi (> 1000 righe):
1. Prova regex su tutti
2. Identifica falliti
3. Batch GenAI solo sui falliti
4. Evita rate limits

### 4. Fallback Gracefully

```python
result = parse_address_smart(address)

if not result.success or result.confidence < 0.7:
    # Warning ma non bloccare import
    warnings.append(f"Low confidence parse: {result.confidence}")
    # Usa indirizzo originale
    record.indirizzo = address
```

---

## 🔧 Troubleshooting

### Problema: Groq timeout

**Sintomo:**
```
ERROR: Groq parsing failed: timeout
```

**Soluzione:**
```python
# Aumenta timeout in smart_address_parser.py
GENAI_TIMEOUT = 20  # da 10 a 20 secondi
```

### Problema: Ollama connection refused

**Sintomo:**
```
DEBUG: Ollama not available (connection refused)
```

**Soluzione:**
```bash
# Verifica che Ollama sia in esecuzione
ollama serve

# Oppure modifica URL in .env
OLLAMA_BASE_URL=http://localhost:11434
```

### Problema: Rate limit exceeded

**Sintomo:**
```
HTTP 429: Rate limit exceeded
```

**Soluzione:**
1. Implementa retry con exponential backoff
2. Usa Ollama come fallback
3. Upgrade a Groq paid plan

---

## 📈 Roadmap Future

### Short-term
- ✅ Update comuni da GitHub
- ✅ Smart parser con Groq
- ✅ Ollama integration

### Medium-term
- [ ] UI admin per update comuni
- [ ] Caching intelligente dei parse results
- [ ] Metriche e dashboard
- [ ] API rate limit handler

### Long-term
- [ ] Machine learning model trainato sui nostri dati
- [ ] Geocoding completo (lat/long)
- [ ] Integrazione con Google Maps API
- [ ] Validazione indirizzi real-time

---

## 📞 Supporto

Per domande o problemi:
1. Consulta questa guida
2. Verifica logs: `tail -f backend/logs/app.log`
3. Test endpoint: `curl http://localhost:8000/api/v1/admin/comuni/status`

**Ultima revisione:** 2025-11-29
**Versione:** 1.0.0
