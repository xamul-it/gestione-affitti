# Limite noto: bootstrap di un database da zero

`alembic upgrade head` da solo, contro lo schema `public` di un database
completamente vuoto (mai avviata l'app), **non funziona**.

## Perché

Le tabelle core di base (`core_users`, `core_tenants`, `core_modules`,
`core_roles`, ecc.) non sono mai state create da nessuna migration Alembic.
Vengono create da `create_core_tables()` (`backend/app/main.py`), che chiama
`Base.metadata.create_all()` per ogni tabella con prefisso `core_` al primo
avvio dell'applicazione (`./start.sh`).

Le migration in `backend/alembic/versions/` presuppongono che questa base
esista già e gestiscono solo l'evoluzione incrementale dello schema da lì in
poi. `2025122702_legacy_anchor.py` è esplicitamente un'"ancora" pensata per
collegare la storia delle migration a database già esistenti (creati via
`create_all()`), non per costruirne uno da zero — il suo stesso commento lo
dice.

## Procedura corretta oggi

1. `./start.sh` almeno una volta (crea le tabelle core in `public` + utente
   admin di default).
2. Poi `alembic upgrade head` / `alembic -x schema=all upgrade head` per le
   migration incrementali successive.

Questo è già l'ordine descritto in "Primo avvio" nel `README.md` — il punto
di questo documento è rendere esplicito **perché** quell'ordine è
obbligatorio, non solo consigliato.

## Cosa servirebbe per un bootstrap "solo migration"

Utile per pipeline CI/CD che separano il passo "applica le migration" dal
passo "avvia l'app" (pattern comune in produzione, per non lasciare che
l'app muti lo schema al boot). Servirebbe:

- Una migration iniziale (`target_schema = "public"`) che ricostruisca da
  zero tutte le tabelle core attualmente prodotte da `create_all()` — utenti,
  tenant, moduli, ruoli/permessi, dati di dominio condivisi (comuni, tipi
  documento, ecc.).
- Verificare che ogni migration successiva alla nuova baseline sia
  effettivamente idempotente/coerente se applicata subito dopo, senza mai
  passare da `create_all()`.

Non è stato fatto: è un lavoro sostanziale che tocca il bootstrap dell'intera
piattaforma, non una correzione puntuale. Da pianificare a parte se/quando
serve davvero un deploy che separa migrate da avvio app.

## Bug correlato, già corretto

`2026012801_create_document_jobs.py` creava esplicitamente il tipo enum
`jobstatus` e poi lo ridefiniva (con un secondo oggetto Python, stesso nome)
dentro `op.create_table(...)` — Alembic tenta di ricreare il tipo una seconda
volta e fallisce con "type already exists" la prima volta che questa
migration viene davvero eseguita contro uno schema che non ce l'ha già
(verificato con una riproduzione isolata). Corretto usando
`postgresql.ENUM(..., create_type=False)` sulla colonna, invece del generico
`sa.Enum(...)` — pattern già corretto, si veda `2026091801_create_core_scadenze_tenant_tables.py`.

Questo bug specifico **non impatta gli schema tenant**: il meccanismo di
"schema gate" di `alembic/env.py` (`_install_schema_gate`) salta
`op.create_table` quando il `target_schema` dichiarato non corrisponde allo
schema in migrazione, quindi per un tenant nuovo la tabella/tipo non vengono
mai (ri)creati — verificato empiricamente con `alembic -x schema=<nuovo
tenant> upgrade head` su schemi realmente vergini, due volte, zero errori e
zero tipi orfani lasciati indietro.
