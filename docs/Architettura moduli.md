
### 3.1 Manifest del modulo

Il manifest è un file Python `__manifest__.py` che espone un dict `manifest`.

**Campi obbligatori (vanno validati dal core)**
- `name`
- `technical_name`
- `version`
- `module_short_code` (4–6 caratteri)
- `schema_target`:
  - `public`
  - `tenant`
  - `public + tenant`
- `migrations_path`
- `seeds_path`
- `endpoints`:
  - `register`
  - `install`

**Campi opzionali supportati**
- `author`, `category`, `icon`, `license`, `price`
- `installable`, `auto_install`, `application`
- `depends`, `optional_depends`
- `permissions`, `models`, `routers`, `routes`, `extensions`, `data`
- `frontend_config`, `menu_items`, `widgets` (metadata per UI)

**Regola sul `module_short_code`**
- è lungo **4–6 caratteri**
- è obbligatorio
- deve essere utilizzato come prefisso per tutte le tabelle del modulo

---

## 4. Ruolo del core della piattaforma

Il core è l’unico componente autorizzato a:

- eseguire Alembic
- creare o aggiornare tabelle
- applicare seed
- gestire la versione dello schema

Tutte le operazioni di register, install e upgrade passano dal core.

---

## 5. Gestione delle migrazioni

### 5.1 Migrazioni dichiarative

I moduli:
- forniscono script Alembic
- **non** accedono direttamente all’engine DB

Il core:
- carica le migrazioni
- valida le operazioni
- le esegue nel contesto corretto

**Esecuzione per modulo (schema base)**
- Il core esegue le migrazioni **solo** del modulo in registrazione.
- Viene passato ad Alembic il percorso di migrazione del modulo (`migrations_path`).
- Lo schema target è deciso da `schema_target`.

### 5.2 Validazioni applicate dal core

Prima dell’esecuzione, il core verifica che:

- tutte le tabelle create abbiano il prefisso `module_short_code`
- lo schema target sia coerente:
  - `public` → register
  - schema tenant → install
- non vengano toccate tabelle di altri moduli
- non vengano eseguite operazioni SQL arbitrarie

Questo rende le convenzioni **vincoli tecnici**, non semplici linee guida.

**Prefisso automatico tabelle**
- Il core applica automaticamente il prefisso `module_short_code_` alle tabelle del modulo.
- Il prefisso viene applicato durante le migrazioni Alembic del modulo.
- Le foreign key verso `public` restano inalterate.

---

## 6. Gestione dei seed

Anche i seed sono **mediati dal core**.

Il core distingue tra:

- **seed globali**
  - applicati allo schema `public`
  - dati cross-tenant
  - tipicamente hard-coded
- **seed tenant**
  - applicati allo schema del tenant
  - configurazioni iniziali o dati funzionali

Il core garantisce:
- idempotenza
- assenza di duplicazioni
- corretto supporto al meccanismo di override

**Esecuzione seed per modulo (schema base)**
- Dopo le migrazioni del modulo, il core esegue i seed `public`.
- Il seed viene richiamato tramite `endpoints.register`.

**Esecuzione seed per modulo (tenant)**
- Durante l’installazione tenant, il core chiama `endpoints.install`.
- Contesto DB: `search_path = <tenant_schema>, public`.
- Firma supportata: `()`, `(db)`, `(db, tenant_id)`, `(db, tenant_id, tenant_schema)`.
- Se l’endpoint fallisce, l’installazione del modulo viene bloccata.

---

## 7. Prevenzione di tabelle non standard

Questo modello **impedisce strutturalmente** che un modulo possa:

- creare tabelle senza prefisso
- operare su schemi non autorizzati
- interferire con altri moduli
- violare il modello multi-tenant

Condizioni necessarie:
1. i moduli non hanno accesso diretto al database
2. tutte le operazioni passano dal runner Alembic del core
3. le migrazioni sono validate prima dell’esecuzione

In questo scenario, la creazione di tabelle non standard è **tecnicamente impossibile**.

---

## 8. Versionamento e problem determination

Il core mantiene informazioni su:

- versione del modulo
- versione dello schema
- tenant su cui è installato
- stato delle migrazioni

Questo consente:
- problem determination rapida
- audit strutturato
- rollback controllati
- riproducibilità dello stato del sistema

---

## 9. Idempotenza e affidabilità

Le operazioni di:
- register
- install
- upgrade

sono progettate per essere:
- idempotenti
- ripetibili
- sicure in ambienti multi-tenant

Lo stato del database è sempre riconducibile a:
- versione del modulo
- set di migrazioni applicate

---

## 10. Trade-off

### Svantaggi
- maggiore complessità nel core
- curva di apprendimento per lo sviluppo dei moduli
- riduzione della libertà operativa dei moduli

### Mitigazioni
- template ufficiali per i moduli
- CLI di supporto
- validazione preventiva delle migrazioni
- documentazione chiara e prescrittiva

---

## 11. Conclusione

Centralizzare nel core della piattaforma la gestione di:

- migrazioni Alembic
- creazione delle tabelle
- popolamento dei dati

e rendere i moduli **puramente dichiarativi** è una scelta:

- architetturalmente corretta
- scalabile
- sicura
- coerente con un modello multi-tenant modulare

Questo approccio consente di mantenere controllo, qualità e governabilità del database
anche al crescere del numero di moduli e tenant.
