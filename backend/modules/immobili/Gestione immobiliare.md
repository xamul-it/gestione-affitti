# Modulo Gestione Immobiliare  
## Analisi Funzionale

---

## 1. Scopo del modulo

Il modulo **Gestione Immobiliare** consente la gestione strutturata del patrimonio immobiliare all’interno di una piattaforma **multi-tenant**.

Il modulo gestisce:
- unità immobiliari edificate
- terreni
- relazioni di proprietà (singola e multiproprietà)
- dati catastali e fiscali
- documentazione tecnica e amministrativa
- adempimenti e scadenze
- soggetti collegati (proprietari, tecnici, manutentori)

Il modulo costituisce il **master data immobiliare** della piattaforma.

---

## 2. Ambito ed esclusioni

### 2.1 Funzionalità incluse
- censimento immobili e terreni
- gestione proprietari e diritti reali
- gestione documenti immobiliari
- gestione conformità impiantistiche
- gestione scadenziario
- consultazione da parte di soggetti tecnici

### 2.2 Funzionalità escluse
Il modulo **NON gestisce**:
- affitti e locazioni
- contratti di locazione
- canoni
- incassi
- contabilità
- ticket o interventi di manutenzione
- pianificazione lavori

---

## 3. Contesto multi-tenant

- Ogni dato è associato a un **tenant**
- Gli utenti vedono esclusivamente i dati del proprio tenant
- Un tenant può gestire:
  - immobili propri
  - immobili di terzi (in gestione)

---

## 4. Unità Immobiliare

### 4.1 Tipologia Unità Immobiliare (DOMINIO)

| Codice | Descrizione |
|------|------------|
| FAB | Fabbricato / edificio |
| APT | Appartamento |
| LOC | Locale commerciale |
| UFF | Ufficio |
| MAG | Magazzino |
| LAB | Laboratorio |
| GAR | Autorimessa / garage |
| TER | Terreno |

---

### 4.2 Attributi Unità Immobiliare

**Obbligatori**
- Identificativo unità
- Tenant
- Tipologia unità immobiliare
- Indirizzo completo
- Stato unità
- Destinazione d’uso

**Facoltativi**
- Descrizione
- Superficie catastale
- Superficie commerciale
- Numero vani
- Piano
- Interno
- Anno costruzione
- Classe energetica
- Note

---

### 4.3 Stato Unità Immobiliare (DOMINIO)

| Codice | Descrizione |
|------|------------|
| ATT | Attiva |
| DIS | Dismessa |
| INI | Inagibile |
| VEN | Venduta |

---

### 4.4 Destinazione d’Uso (DOMINIO)

| Codice | Descrizione |
|------|------------|
| RES | Residenziale |
| COM | Commerciale |
| IND | Industriale |
| RIC | Ricettiva |
| AGR | Agricola |
| MISTA | Mista |

---

## 5. Terreni

Il terreno è una **tipologia di unità immobiliare**.

### 5.1 Attributi specifici Terreno

- Superficie (mq / ettari)
- Tipologia terreno
- Qualità catastale
- Reddito dominicale
- Reddito agrario
- Indice edificabilità
- Vincoli

### 5.2 Tipologia Terreno (DOMINIO)

| Codice | Descrizione |
|------|------------|
| AGR | Agricolo |
| EDI | Edificabile |
| BOS | Bosco |
| INE | Inedificabile |
| ALT | Altro |

---

## 6. Dati Catastali

Ogni unità immobiliare **DEVE** avere almeno una scheda catastale.

### 6.1 Attributi Catastali

- Comune catastale
- Sezione
- Foglio
- Particella
- Subalterno
- Categoria catastale
- Classe
- Consistenza
- Rendita catastale
- Data riferimento

---

### 6.2 Categoria Catastale (DOMINIO)

**Fabbricati**
- A/1, A/2, A/3, A/4, A/7, A/10
- C/1, C/2, C/6
- D/1, D/2, D/10
- F/2, F/3

**Terreni**
- Seminativo
- Seminativo arborato
- Bosco
- Prato
- Uliveto
- Vigneto

---

## 7. Proprietà e diritti reali

### 7.1 Relazione Proprietà

Un’unità immobiliare può avere **uno o più soggetti proprietari**.

### 7.2 Attributi relazione

- Soggetto
- Percentuale di proprietà
- Tipo di diritto
- Data inizio
- Data fine

### 7.3 Tipo di diritto (DOMINIO)

| Codice | Descrizione |
|------|------------|
| PPR | Proprietà piena |
| NPR | Nuda proprietà |
| USU | Usufrutto |
| SUP | Superficie |
| USO | Uso / abitazione |

---

## 8. Modulo Anagrafico – funzioni richieste

Il modulo immobiliare **utilizza** un modulo anagrafico esterno.

### 8.1 Tipologie soggetti

- Persona fisica
- Persona giuridica

### 8.2 Attributi minimi soggetto

- Nome / Denominazione
- Codice fiscale / Partita IVA
- Indirizzi
- Contatti
- Ruoli

### 8.3 Ruoli soggetto (DOMINIO)

| Codice | Descrizione |
|------|------------|
| PRO | Proprietario |
| TEC | Tecnico |
| MAN | Manutentore |
| AMM | Amministratore |

---

## 9. Soggetti tecnici e manutentori

### 9.1 Associazione soggetto–immobile

- Soggetto
- Tipo servizio
- Priorità
- Note

### 9.2 Tipo servizio tecnico (DOMINIO)

| Codice | Descrizione |
|------|------------|
| ELE | Elettricità |
| GAS | Gas |
| IDR | Idrico |
| TER | Termico |
| ANT | Antincendio |
| ASC | Ascensori |
| EDIL | Edilizia |

---

## 10. Documenti Immobiliari

Il modulo gestisce **metadati** dei documenti.  
I file sono archiviati in un **modulo documentale esterno**.

---

### 10.1 Tipologia Documento (DOMINIO)

| Codice | Descrizione |
|------|------------|
| APE | Attestato di Prestazione Energetica |
| DCE | Dichiarazione conformità impianto elettrico |
| DCG | Dichiarazione conformità impianto gas |
| DCI | Dichiarazione conformità impianto idrico |
| DCT | Dichiarazione conformità impianto termico |
| CPI | Certificato prevenzione incendi |
| AGI | Certificato agibilità |
| VIS | Visura catastale |
| PLA | Planimetria catastale |
| CDU | Certificato destinazione urbanistica |
| ATR | Atto di proprietà |
| POL | Polizza assicurativa |

---

### 10.2 Metadati comuni documento

**Obbligatori**
- Tipologia documento
- Unità immobiliare
- Data emissione
- Stato
- Riferimento documento esterno

**Facoltativi**
- Numero / protocollo
- Ente emittente
- Data scadenza
- Note

---

### 10.3 Stato Documento (DOMINIO)

| Codice | Descrizione |
|------|------------|
| VAL | Valido |
| SCA | In scadenza |
| SCO | Scaduto |
| SOS | Sostituito |
| NAP | Non applicabile |

---

### 10.4 Documenti con scadenza automatica

Generano scadenza:
- APE
- CPI
- POL
- CDU

---

### 10.5 Dichiarazioni di Conformità Impiantistica

#### Impianto elettrico (DCE)

**Obbligatori**
- Data rilascio
- Impresa installatrice
- Tecnico responsabile
- Normativa riferimento (DM 37/2008)
- Stato

**Regole**
- Nessuna scadenza temporale
- Diventa non valida se l’impianto è modificato
- Stato gestibile manualmente

Le stesse regole si applicano a:
- DCG
- DCI
- DCT

---

## 11. Scadenziario

### 11.1 Funzionalità

- Elenco scadenze per unità
- Elenco scadenze per tenant
- Filtri temporali
- Notifiche automatiche
- Storico

---

## 12. Ruoli applicativi

### AdminTenant
- Accesso completo
- Gestione domini
- Tutti gli immobili del tenant

### PropertyManager
- Gestione immobili
- Documenti
- Scadenze
- Proprietari e tecnici

### Viewer
- Consultazione sola lettura

### MaintenanceConnector
- Consultazione immobili associati
- Accesso documenti tecnici pertinenti

---

## 13. Conclusione

Il modulo Gestione Immobiliare rappresenta la **fonte primaria e strutturata** dei dati immobiliari.  
Ogni altro modulo della piattaforma **dipende** da queste informazioni ma **non le replica**.