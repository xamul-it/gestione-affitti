# Verifica Implementazione Modulo Anagrafica Italiana

**Data Verifica:** 9 Dicembre 2025
**Documento di Riferimento:** ANAGRAFICA_ANALISI_TECNICO_FUNZIONALE.md v1.0 (7 Dicembre 2025)

---

## 1. Sintesi Esecutiva

Il modulo Anagrafica Italiana presenta **due sistemi di gestione ruoli distinti**:

1. **Sistema Ruoli di Business** (documentato): `ruoli_disponibili`, `soggetti_ruoli`
2. **Sistema Ruoli Azienda** (NON documentato): `ruoli_azienda`, `ruoli_azienda_tipi`

**CRITICITÀ RILEVATA**: Il sistema Ruoli Azienda è stato implementato completamente ma NON è menzionato nel documento di analisi tecnico-funzionale. Il documento richiede aggiornamento.

---

## 2. Confronto Requisiti vs Implementazione

### 2.1 Backend - Modelli Database

| Entità | Documentato | Implementato | Tabella DB | Note |
|--------|-------------|--------------|------------|------|
| SoggettoAnagrafico | ✅ | ✅ | `soggetti_anagrafici` | COMPLETO |
| ComuneItalia | ✅ | ✅ | `comuni_italia` | ~8000 comuni |
| TipoDocumento | ✅ | ✅ | `tipi_documento` | 11 tipi standard |
| RuoloDisponibile | ✅ | ✅ | `ruoli_disponibili` | Modello core esistente |
| SoggettoRuolo | ✅ | ✅ | `soggetti_ruoli` | Modello core esistente |
| **RuoloAzienda** | ❌ | ✅ | `ruoli_azienda` | **NON DOCUMENTATO** |
| **RuoloAziendaTipo** | ❌ | ✅ | `ruoli_azienda_tipi` | **NON DOCUMENTATO** |

### 2.2 Backend - API Endpoints

#### ✅ API Implementate e Documentate

| Endpoint | Scopo | Stato |
|----------|-------|-------|
| GET/POST/PUT/DELETE `/soggetti` | CRUD soggetti anagrafici | ✅ COMPLETO |
| GET `/soggetti/{id}` | Dettaglio soggetto | ✅ COMPLETO |
| GET `/domini/comuni` | Lista comuni italiani | ✅ COMPLETO |
| GET `/domini/tipi-documento` | Lista tipi documento | ✅ COMPLETO |
| POST `/soggetti/{id}/documenti/upload` | Upload documento | ✅ COMPLETO |
| GET `/documenti/soggetto/{id}` | Lista documenti soggetto | ✅ COMPLETO |
| POST `/soggetti/{id}/create-user` | Crea user da soggetto | ✅ COMPLETO |

#### ✅ API Implementate ma NON Documentate (RuoliAzienda)

| Endpoint | Scopo | Stato |
|----------|-------|-------|
| GET `/ruoli-azienda/` | Lista tutte le associazioni ruolo | ✅ COMPLETO |
| GET `/ruoli-azienda/soggetto/{id}` | Ruoli di un soggetto | ✅ COMPLETO |
| GET `/ruoli-azienda/{id}` | Dettaglio singolo ruolo | ✅ COMPLETO |
| POST `/ruoli-azienda/` | Crea associazione ruolo | ✅ COMPLETO |
| PUT `/ruoli-azienda/{id}` | Aggiorna associazione ruolo | ✅ COMPLETO |
| DELETE `/ruoli-azienda/{id}` | Elimina associazione ruolo | ✅ COMPLETO |
| GET `/domini/ruoli-azienda-tipi` | Lista tipi ruolo azienda | ✅ COMPLETO |
| POST `/domini/ruoli-azienda-tipi` | Crea tipo ruolo | ✅ COMPLETO |
| PUT `/domini/ruoli-azienda-tipi/{id}` | Aggiorna tipo ruolo | ✅ COMPLETO |
| DELETE `/domini/ruoli-azienda-tipi/{id}` | Elimina tipo ruolo | ✅ COMPLETO |

#### ❌ API Documentate ma NON Implementate (Sistema Ruoli Business)

| Endpoint | Scopo | Stato |
|----------|-------|-------|
| POST `/soggetti/{id}/ruoli` | Assegna ruolo business | ❌ DA IMPLEMENTARE |
| DELETE `/soggetti/{id}/ruoli/{id}` | Rimuovi ruolo business | ❌ DA IMPLEMENTARE |
| GET `/ruoli-disponibili` | Lista ruoli business disponibili | ❌ DA IMPLEMENTARE |
| GET `/soggetti/{id}/ruoli` | Ruoli business di un soggetto | ❌ DA IMPLEMENTARE |

### 2.3 Frontend - Componenti UI

#### ✅ Componenti Implementati

| Componente | Scopo | File | Stato |
|------------|-------|------|-------|
| **SoggettiAnagraficiList** | Lista soggetti | `/SoggettiAnagrafici/` | ✅ COMPLETO |
| **PersoneFisicheList** | Lista persone fisiche | `/PersoneFisiche/` | ✅ COMPLETO |
| **PersoneGiuridicheList** | Lista persone giuridiche | `/PersoneGiuridiche/` | ✅ COMPLETO |
| **ComuniList** | Lista comuni | `/Comuni/` | ✅ COMPLETO |
| **DocumentoUpload** | Upload documenti | `/Documenti/` | ✅ COMPLETO |
| **RuoliAziendaSection** | Ruoli nella scheda soggetto | `/RuoliAzienda/` | ✅ COMPLETO |
| **RuoliAziendaList** | Lista centralizzata ruoli | `/RuoliAzienda/` | ✅ COMPLETO |
| **RuoloAziendaForm** | Form creazione/modifica ruolo | `/RuoliAzienda/` | ✅ COMPLETO |
| **RuoliAziendaTipiList** | Gestione domini ruoli | `/RuoliAziendaTipi/` | ✅ COMPLETO |

#### ❌ Componenti Documentati ma NON Implementati

| Componente | Scopo | Stato |
|------------|-------|-------|
| **SoggettoDetail** | Vista dettaglio soggetto | ⚠️ PARZIALE (redirect a PersonaFisicaDetail/PersonaGiuridicaDetail) |
| **SoggettoForm** | Form creazione/modifica soggetto | ⚠️ PARZIALE (form separati per PF/PG) |
| **AddressAutocomplete** | Autocomplete città | ❌ DA IMPLEMENTARE |
| **StatsSoggettiWidget** | Widget statistiche dashboard | ❌ DA IMPLEMENTARE |
| **RuoliBusinessSection** | Gestione ruoli business (proprietario, affittuario) | ❌ DA IMPLEMENTARE |

### 2.4 Servizi Platform

| Servizio | Scopo | Stato |
|----------|-------|-------|
| **DocumentService** | Upload/download documenti | ✅ ESISTENTE |
| **ScadenzarioService** | Monitoraggio scadenze | ✅ ESISTENTE |
| **ImportExportService** | Import/export CSV/Excel | ❌ DA IMPLEMENTARE |
| **AddressNormalizer** | Normalizzazione indirizzi | ❌ DA IMPLEMENTARE |
| **VisibilityService** | Cono di visibilità | ❌ DA IMPLEMENTARE |

---

## 3. Sistema Ruoli Azienda (NON Documentato)

### 3.1 Descrizione

**Sistema completamente implementato ma assente dal documento di analisi.**

Il sistema RuoliAzienda gestisce le associazioni tra persone fisiche e persone giuridiche con ruoli lavorativi specifici:

**Scopo:**
- Tracciare relazioni lavorative: "Giuseppe Verdi è Segretaria presso Azienda Test SRL"
- Storicizzare periodi di impiego (data_inizio, data_fine)
- Gestire ruoli standard tramite dominio normalizzato

**Schema Database:**

```sql
-- Tabella domini ruoli azienda
CREATE TABLE ruoli_azienda_tipi (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(100) UNIQUE NOT NULL,
    descrizione VARCHAR(500),
    attivo BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL
);

-- Tabella associazioni ruolo
CREATE TABLE ruoli_azienda (
    id SERIAL PRIMARY KEY,
    persona_fisica_id INT NOT NULL REFERENCES soggetti_anagrafici(id) ON DELETE CASCADE,
    persona_giuridica_id INT NOT NULL REFERENCES soggetti_anagrafici(id) ON DELETE CASCADE,
    ruolo VARCHAR(100),  -- Denormalizzato per backward compatibility
    ruolo_tipo_id INT REFERENCES ruoli_azienda_tipi(id) ON DELETE SET NULL,
    data_inizio DATE,
    data_fine DATE,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL
);
```

**Dati Domain Seed (8 ruoli standard):**
1. Segretaria
2. Amministratore Delegato
3. Direttore Generale
4. Responsabile Amministrativo
5. Responsabile Commerciale
6. Responsabile Tecnico
7. Contabile
8. Consulente

### 3.2 API Endpoints (Implementate)

**Backend:** `/api/v1/anagrafica/ruoli-azienda`

- `GET /` - Lista tutte le associazioni
- `GET /soggetto/{id}` - Ruoli di un soggetto (restituisce `{come_persona: [], come_azienda: []}`)
- `GET /{id}` - Dettaglio singolo ruolo
- `POST /` - Crea associazione
- `PUT /{id}` - Aggiorna associazione
- `DELETE /{id}` - Elimina associazione

**Backend:** `/api/v1/anagrafica/domini/ruoli-azienda-tipi`

- `GET /` - Lista tipi ruolo
- `POST /` - Crea tipo
- `PUT /{id}` - Aggiorna tipo
- `DELETE /{id}` - Elimina tipo

### 3.3 Frontend Components (Implementati)

**RuoliAziendaSection.jsx:**
- Mostrata nella scheda dettaglio di PersonaFisica e PersonaGiuridica
- Vista adattiva: mostra "Aziende" per PF, "Persone" per PG
- Filtro "Solo attivi" per ruoli correnti
- Display dinamico: mostra `ruolo_tipo_nome` dal dominio, fallback a `ruolo` testuale
- Badge "⚠ Custom" per ruoli non collegati ai domini

**RuoliAziendaList.jsx:**
- Lista centralizzata di tutte le associazioni ruolo
- Filtri: per persona, per azienda, per nome ruolo, solo attivi
- Statistiche: totale, attivi, cessati
- Form edit inline tramite modal

**RuoloAziendaForm.jsx:**
- Form modale per creazione/modifica
- SELECT dropdown con ruoli standard da dominio
- Opzione "Altro (nuovo ruolo)..." per casi eccezionali con warning
- Pre-compila soggetto corrente (persona o azienda)
- Validazione date (data_fine >= data_inizio)

**RuoliAziendaTipiList.jsx:**
- CRUD completo per gestione domini ruoli
- Attivazione/disattivazione ruoli

### 3.4 Funzionalità Chiave

✅ **Domini normalizzati**: I ruoli sono gestiti tramite tabella di dominio, garantendo coerenza
✅ **Live updates**: Le modifiche ai nomi dei ruoli nei domini si propagano immediatamente nelle viste
✅ **Backward compatibility**: Campo `ruolo` testuale mantenuto per vecchi dati
✅ **Storicizzazione**: Tracciamento periodi di impiego con date inizio/fine
✅ **Vista bidirezionale**: Dalla persona vedi le aziende, dall'azienda vedi le persone
✅ **Filtri intelligenti**: Solo attivi, ricerca testuale, filtri combinati

---

## 4. Sistema Ruoli Business (Documentato ma Non Implementato)

### 4.1 Descrizione

**Sistema documentato nel file di analisi ma non completamente implementato.**

Ruoli trasversali ai moduli che determinano il **cono di visibilità** dei dati:

**Scopo:**
- Proprietario: vede i propri immobili e contratti
- Affittuario: vede i contratti in cui è inquilino
- Tecnico: vede gli interventi assegnati
- Fornitore: vede fatture e ordini

**Modelli Esistenti:** `ruoli_disponibili`, `soggetti_ruoli` (in `app/core/models/ruoli.py`)

**Tabelle Database:** ✅ Esistenti (create da migrations)

### 4.2 Componenti Mancanti

❌ **API Endpoints** per:
- Assegnazione ruoli business a soggetti
- Listing ruoli disponibili
- Query ruoli di un soggetto

❌ **Registrazione automatica ruoli** da manifest dei moduli

❌ **VisibilityService** per filtri query basati su ruoli

❌ **UI Components** per gestione ruoli business nelle schede soggetto

❌ **Integrazione nei moduli** (immobili, affitti_lungo)

---

## 5. Funzionalità Documentate - Stato Implementazione

### ✅ COMPLETE

1. **CRUD Soggetti Anagrafici** - API e UI complete
2. **Domini ComuneItalia e TipoDocumento** - Dati seed e API
3. **Upload/Gestione Documenti** - API upload, lista documenti, integrazione scadenzario
4. **User Management** - Creazione user da soggetto, login con soggetto_id in JWT
5. **Sistema Ruoli Azienda** - CRUD completo backend + frontend (NON DOCUMENTATO)
6. **Menu Dinamico** - Registrazione automatica menu da manifest

### ⚠️ PARZIALI

1. **Vista Dettaglio Soggetto** - Esistono PersonaFisicaDetail e PersonaGiuridicaDetail separate, non SoggettoDetail unificato
2. **Form Soggetto** - Form separati per persona fisica/giuridica, non form unificato

### ❌ DA IMPLEMENTARE

1. **Sistema Ruoli Business completo** - API, registrazione automatica, UI
2. **Cono di Visibilità (VisibilityService)** - Filtri query basati su ruoli business
3. **Import/Export** - CSV/Excel con template e validazione
4. **Normalizzatore Indirizzi** - AddressNormalizer e autocomplete comuni
5. **Dashboard Widget** - StatsSoggettiWidget, widget documenti in scadenza
6. **Vista unificata dettaglio** - SoggettoDetail che include sia PF che PG

---

## 6. Differenze Critiche tra Documento e Implementazione

### 6.1 Sistema Ruoli Azienda (Implementato ma Non Documentato)

**IMPATTO: ALTO**

Il sistema RuoliAzienda è **completamente funzionale** e rappresenta una funzionalità core del modulo anagrafica, ma è **totalmente assente** dal documento di analisi tecnico-funzionale.

**Conseguenze:**
- Documentazione tecnica incompleta
- Onboarding difficile per nuovi sviluppatori
- Mancanza di linee guida per estensioni future
- Nessuna menzione nelle priorità di implementazione

**Azione Richiesta:**
✅ Aggiungere sezione completa nel documento:
- Descrizione sistema e casi d'uso
- Schema database e relationships
- API endpoints
- UI components
- Differenze con Sistema Ruoli Business

### 6.2 Vista Dettaglio Separata (Implementata Diversamente)

**IMPATTO: MEDIO**

Il documento prevede un componente **SoggettoDetail.jsx unificato**, ma l'implementazione usa:
- **PersonaFisicaDetail.jsx** per persone fisiche
- **PersonaGiuridicaDetail.jsx** per persone giuridiche

**Motivazione:** Differenza significativa nei campi e layout tra PF e PG giustifica componenti separati.

**Azione Richiesta:**
⚠️ Aggiornare documento per riflettere architettura a componenti separati

### 6.3 Sistema Ruoli Business (Documentato ma Non Implementato)

**IMPATTO: ALTO**

Il documento dedica ampio spazio al sistema di ruoli business, ma:
- API endpoints non implementati
- Nessuna UI per assegnazione ruoli
- VisibilityService non implementato
- Registrazione automatica da manifest assente

**Azione Richiesta:**
⚠️ Marcare chiaramente come "Sprint Future" o implementare secondo priorità

---

## 7. Raccomandazioni

### 7.1 Aggiornamento Urgente Documentazione

**PRIORITÀ: CRITICA**

1. Aggiungere sezione completa "Sistema Ruoli Azienda" (Sezione 12)
2. Aggiornare tabella modelli database (includere RuoloAzienda, RuoloAziendaTipo)
3. Aggiornare lista API implementate
4. Aggiornare lista componenti frontend
5. Modificare sezione "Stato Attuale Implementazione" per riflettere realtà

### 7.2 Chiarimento Differenze tra Due Sistemi Ruoli

**PRIORITÀ: ALTA**

Aggiungere tabella comparativa esplicita:

| Caratteristica | Ruoli Azienda | Ruoli Business |
|----------------|---------------|----------------|
| **Scopo** | Relazioni lavorative PF-PG | Cono visibilità dati |
| **Esempio** | "Mario è Segretaria in Azienda X" | "Mario è Proprietario immobile 42" |
| **Tabelle** | ruoli_azienda, ruoli_azienda_tipi | ruoli_disponibili, soggetti_ruoli |
| **Stato** | ✅ Implementato | ⚠️ Parziale |
| **Moduli** | anagrafica_italiana | core + tutti moduli |

### 7.3 Roadmap Implementazione Aggiornata

**Sprint Completati (non documentati):**
- ✅ Sprint "Ruoli Azienda": Modelli, API, UI completi (2 settimane)

**Sprint da Rivalutare:**
- ⚠️ Sprint 1 (Ruoli Business): Già esistono modelli, mancano API e UI
- ⚠️ Sprint 3 (Cono Visibilità): Dipende da Sprint 1

### 7.4 Documentazione Best Practices

Per future implementazioni:

1. **Sincronizzazione continua**: Aggiornare documento ad ogni sprint completato
2. **Code review check**: Verificare coerenza codice-documenti prima di merge
3. **Version tracking**: Aggiungere sezione "Change Log" nel documento
4. **Implementation notes**: Aggiungere note su scelte implementative diverse da design originale

---

## 8. Conclusioni

**Stato Complessivo Modulo Anagrafica:**

✅ **Punti di Forza:**
- CRUD soggetti completamente funzionante
- Sistema RuoliAzienda robusto e ben implementato
- Gestione documenti con scadenzario integrata
- User management operativo
- Domini ben strutturati (comuni, tipi documento, ruoli azienda)

⚠️ **Aree di Miglioramento:**
- Documentazione tecnica non aggiornata con implementazione reale
- Sistema Ruoli Business incompiuto
- Mancano funzionalità avanzate (import/export, normalizzatore indirizzi, dashboard)

❌ **Gap Critici:**
- **Documentazione obsoleta**: Sistema Ruoli Azienda completamente assente
- **Cono visibilità**: VisibilityService non implementato
- **Widget dashboard**: Nessun widget disponibile per anagrafica

**Priorità Immediate:**

1. **CRITICO**: Aggiornare ANAGRAFICA_ANALISI_TECNICO_FUNZIONALE.md
2. **ALTO**: Completare Sistema Ruoli Business (API + UI)
3. **MEDIO**: Implementare VisibilityService per moduli immobili/affitti
4. **BASSO**: Dashboard widget e funzionalità avanzate

---

*Documento di verifica generato il 9 Dicembre 2025*
*Riferimento: ANAGRAFICA_ANALISI_TECNICO_FUNZIONALE.md v1.0*
