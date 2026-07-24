# Ciclo di vita delle migration: core vs moduli

**Data:** 2026-07-23
**Stato:** Analisi — non contiene un piano di interventi (vedi piano separato)

## Perché questo documento

I documenti esistenti in questa cartella (`MULTI_TENANT_MIGRATION_ANALYSIS.md`,
`MULTI_TENANT_ADVANCED_FEATURES.md`, `MULTI_TENANT_IMPLEMENTATION_PROGRESS.md`,
`MULTI_TENANT_STATUS.md`) sono tutti datati 9 dicembre 2025 e descrivono la
fase di progettazione iniziale della multi-tenancy, prima del refactor che ha
introdotto il prefisso `core_` sulle tabelle di piattaforma e il sistema di
moduli a manifest attuale (`backend/app/core/module_system/`). Non contengono
nessuna delle regole di ciclo di vita descritte qui sotto — sono stati
verificati e non coprono: separazione del percorso di migrazione core/moduli,
gate di attivazione per-tenant, versionamento delle tabelle modulo per tenant,
ri-caricamento dati di esempio post-installazione.

Questo documento descrive lo stato attuale verificato nel codice e
l'architettura target concordata. Non contiene l'elenco degli interventi da
fare — quello vive nel piano di implementazione separato.

## 1. Migrazioni del core (schema `public`)

**Target:** tutte le modifiche allo schema core passano da Alembic, senza
eccezioni. Ciclo di vita:
- **Sviluppo:** nessun DB di sviluppo/produzione separato — quando si modifica
  il core, si crea un DB locale su file, lo si porta a `head` con Alembic
  (schema vuoto → tabelle + dati minimi di avvio via seed), si sviluppa.
- **Produzione:** all'avvio della nuova versione con il DB di produzione,
  Alembic porta lo schema a `head` **senza perdita di dati** (solo
  `ALTER`/`ADD`, mai un `DROP`/ricreazione distruttiva su tabelle con righe).

**Stato attuale verificato:** Alembic esiste (`backend/alembic/`, 6 migration,
tutte `target_schema = "public"`) ma non è affidabile come unica fonte di
verità:
- Il core si popola *anche* via `Base.metadata.create_all()` all'avvio
  dell'app (per creare tabelle mancanti) — un meccanismo parallelo/concorrente
  ad Alembic, non solo un fallback per schema vuoti.
- Almeno una migration (`2026011501_add_modules_registered.py`) referenzia un
  nome tabella pre-refactor (`modules` invece di `core_modules`) — sopravvive
  perché `create_all()` ha già creato le colonne, mascherando il fatto che la
  migration stessa non funziona se rieseguita da zero.
- Risultato pratico verificato: `alembic -x schema=all upgrade head` su uno
  schema vuoto fallisce (vedi bug env.py `public.tenants` → `public.core_tenants`,
  già corretto, e il riferimento a `modules` sopra, non ancora corretto).

**Conseguenza:** oggi non è vero che "Alembic porta il DB di produzione a
`head` senza perdita di dati" per un DB creato da zero — funziona solo perché
`create_all()` copre le lacune. Per la garanzia richiesta, Alembic deve poter
ricostruire lo schema pubblico da zero (dev) e aggiornarlo in place (prod)
senza dipendere da `create_all()` per l'evoluzione dello schema.

## 2. Classificazione dati: dove vive cosa

| Categoria | Schema | Esempio | Chi la scrive |
|---|---|---|---|
| Dati di dominio/riferimento condivisi | `public` | `comuni_italia`, `categorie_catastali`, `tipi_documento` | Seed di piattaforma, moduli che estendono domini condivisi |
| Dati/configurazione propri del modulo | `public` | config di modulo, tabelle di definizione non specifiche di un tenant | Il modulo stesso, mai il tenant |
| Dati utente (business) | schema tenant | `contratti`, `ab_prenotazioni`, ecc. | L'utente finale, tramite l'app |

**Regola:** i dati di modulo (dominio + configurazione) stanno sempre nel
core; i dati utente stanno sempre nel tenant. Una migration di modulo deve
poter toccare entrambi gli spazi nello stesso rilascio: aggiorna le tabelle di
dominio/config nel core, e aggiorna la struttura delle tabelle tenant per ogni
tenant su cui il modulo è attivo — senza perdere le righe già presenti.

**Stato attuale verificato:** la distinzione dominio-condiviso vs
dati-utente-tenant è già rispettata nel codice (tabelle di dominio in
`public`, tabelle di business nel tenant). Manca invece un meccanismo
esplicito e affidabile per propagare un cambio di struttura delle tabelle
tenant a *tutti* i tenant che hanno il modulo attivo (vedi punto 3).

## 3. Migrazione delle tabelle tenant di un modulo

**Target (ciclo di sviluppo modulo):** si lavora sull'istanza principale, si
crea un tenant di sviluppo, si modifica il modulo, si aggiorna la migration.
Quando un tenant con quel modulo attivo viene aperto (pagina di
gestione/abilitazione moduli del tenant), il sistema rileva se le tabelle di
quel tenant sono allineate alla versione corrente del modulo. Se non lo sono,
l'utente ha due sole scelte: **disabilitare il modulo** per quel tenant,
oppure **forzare l'aggiornamento delle tabelle**. Finché la situazione non è
risolta, il modulo non si avvia per quel tenant.

**Stato attuale verificato — meccanismo già esistente e riutilizzabile:**
`TenantModuleService.sync_module_tables_for_tenant()`
(`backend/app/core/services/tenant_module_service.py:757`) già esiste e fa
esattamente il lavoro di "aggiorna senza perdere dati": confronta le tabelle
tenant con i template in `public` e aggiunge colonne (`_sync_table_columns`,
riga 802) e indici mancanti (`_sync_table_indexes`, riga 855) via `ALTER
TABLE ... ADD COLUMN` — mai una `DROP`. Questo copre già il requisito "il
modulo deve aggiornare anche i dati senza perdere informazioni" per il caso
additivo (aggiunta colonne/indici).

**Gap verificato:** non esiste alcun tracciamento di versione per la coppia
tenant↔modulo. La tabella `core_tenant_modules`
(`backend/app/core/models/tenant.py:62`) ha solo `enabled`, `installed_at`,
`disabled_at`, `config` — nessun campo che dica "questo tenant ha le tabelle
del modulo X alla versione Y". Il modulo stesso (`core_modules`,
`backend/app/core/module_system/models.py:18`) ha un campo `version`, ma
niente confronta questo valore con lo stato di un singolo tenant. Di
conseguenza oggi non è possibile rilevare automaticamente il disallineamento
descritto sopra, né quindi mostrare il gate disabilita/forza-aggiorna.

## 4. Dati di esempio ("carica dati di esempio")

**Target:** nella pagina di gestione moduli del tenant, l'azione "carica dati
di esempio" deve essere sempre disponibile, anche quando il modulo è già
installato — non solo al momento dell'installazione iniziale.

**Stato attuale verificato:** il meccanismo `seed_test_data` esiste ed è
cablato end-to-end (`backend/app/core/services/tenant_module_service.py`,
`backend/app/core/schemas/tenant.py:102`, e implementato in almeno 3 moduli:
`affitti_brevi`, `immobili`, `anagrafica_italiana`), ma è raggiungibile solo
dal flusso di installazione
(`frontend/src/pages/Tenant/TenantModules.jsx:93-95`, il flag viene inviato
solo dentro `toggleTenantModule` al momento dell'attivazione). Non esiste
un'azione standalone per ri-eseguire il seed su un modulo già abilitato.

## Riepilogo stato attuale vs target

| Requisito | Stato |
|---|---|
| Alembic unica fonte di verità per il core, dev→prod senza perdita dati | ⚠️ Parziale — Alembic esiste ma non è affidabile da solo (dipende da `create_all()`), almeno 1 migration con riferimento a tabella pre-refactor |
| Tabelle di dominio/config modulo nel core, dati utente nel tenant | ✅ Già rispettato |
| Sync non distruttivo delle tabelle tenant di un modulo | ✅ Meccanismo già esistente (`sync_module_tables_for_tenant`) |
| Versionamento tabelle tenant per rilevare disallineamento | ❌ Assente |
| Gate attivazione tenant (disabilita / forza aggiorna, blocco finché non risolto) | ❌ Assente |
| Ricarica dati di esempio su modulo già installato | ❌ Assente (esiste solo al primo install) |
