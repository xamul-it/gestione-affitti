# Integrazione Anagrafica-User

## Problema

Attualmente il sistema ha due entità separate:
1. **SoggettoAnagrafico**: Persone/aziende nel registro anagrafico (con CF, P.IVA, documenti)
2. **User**: Account di accesso al sistema (con email, username, password, ruoli)

Manca il collegamento tra queste entità. Serve poter:
- Creare un account utente per un soggetto anagrafico esistente
- Associare permessi e visibilità in base al soggetto anagrafico

## Soluzione Proposta

### 1. Relazione 1:1 Opzionale

```
User (auth) -----> SoggettoAnagrafico (anagrafica)
     optional       obbligatorio per business users
```

**User.soggetto_anagrafico_id** (FK nullable):
- NULL = utente di sistema (admin, operatori interni)
- NOT NULL = utente business (proprietario, affittuario, tecnico)

### 2. Database Changes

```sql
-- Aggiungere colonna a tabella users
ALTER TABLE users 
ADD COLUMN soggetto_anagrafico_id INTEGER 
REFERENCES soggetti_anagrafici(id) ON DELETE SET NULL;

CREATE INDEX ix_users_soggetto_anagrafico_id 
ON users(soggetto_anagrafico_id);

-- Vincolo: un soggetto può avere max 1 utente
CREATE UNIQUE INDEX uq_users_soggetto_anagrafico 
ON users(soggetto_anagrafico_id) 
WHERE soggetto_anagrafico_id IS NOT NULL;
```

### 3. Backend API

**Endpoint: POST /api/v1/anagrafica/soggetti/{id}/create-user**

Request:
```json
{
  "email": "mario.rossi@example.com",
  "username": "mario.rossi",
  "password": "temporary_password",
  "send_welcome_email": true,
  "roles": ["affittuario"]  // Optional
}
```

Response:
```json
{
  "user_id": 123,
  "soggetto_id": 456,
  "email": "mario.rossi@example.com",
  "username": "mario.rossi",
  "temporary_password": true,
  "message": "User created successfully. Email sent with login credentials."
}
```

**Endpoint: GET /api/v1/anagrafica/soggetti/{id}/user**

Response:
```json
{
  "has_user": true,
  "user": {
    "id": 123,
    "email": "mario.rossi@example.com",
    "username": "mario.rossi",
    "is_active": true,
    "roles": ["affittuario"],
    "last_login": "2025-12-08T10:30:00Z"
  }
}
```

**Endpoint: DELETE /api/v1/anagrafica/soggetti/{id}/user**

Disattiva l'utente ma mantiene l'anagrafica.

### 4. Frontend UI

**In SoggettoDetail, tab "Utente":**

```
┌─────────────────────────────────────────┐
│ 👤 Account Utente                       │
├─────────────────────────────────────────┤
│                                          │
│ ❌ Nessun account utente associato      │
│                                          │
│ [+ Crea Account Utente]                 │
│                                          │
└─────────────────────────────────────────┘
```

**Dopo creazione:**

```
┌─────────────────────────────────────────┐
│ 👤 Account Utente                       │
├─────────────────────────────────────────┤
│ ✅ Account attivo                        │
│                                          │
│ Email:     mario.rossi@example.com      │
│ Username:  mario.rossi                  │
│ Ruoli:     Affittuario                  │
│ Ultimo:    08/12/2025 10:30             │
│                                          │
│ [🔑 Reset Password] [❌ Disattiva]      │
│                                          │
└─────────────────────────────────────────┘
```

### 5. Business Logic

**Regole:**
1. Solo PERSONA_FISICA può avere account (no persone giuridiche)
2. Email obbligatoria per creare account
3. Username generato automaticamente: nome.cognome (normalizzato)
4. Password temporanea generata, obbligo cambio al primo login
5. Ruoli business assegnabili: affittuario, proprietario, tecnico
6. Invio email automatica con credenziali (se configurato)

**Cono di Visibilità:**
- User con `soggetto_anagrafico_id` vede solo i suoi dati
- Proprietario vede: suoi immobili, contratti, incassi, spese
- Affittuario vede: suo contratto attivo, incassi pagati, documenti
- Tecnico vede: interventi assegnati, immobili dove lavora

### 6. Migration Path

**Per dati esistenti:**
```python
# Script di migrazione
# Se esistono User con email matching SoggettoAnagrafico.email
# -> Collegarli automaticamente
```

### 7. Security

**Permessi richiesti:**
- `soggetto.create_user` - Creare account da anagrafica
- `soggetto.view_user` - Vedere dettagli account
- `soggetto.disable_user` - Disattivare account

**Validazioni:**
- Email valida e univoca
- Soggetto deve essere PERSONA_FISICA
- Soggetto deve avere email in anagrafica
- Non può già avere un account esistente

## Implementation Priority

1. ✅ Database migration (ADD soggetto_anagrafico_id)
2. ✅ Backend User model update
3. ✅ API endpoint: create-user
4. ✅ API endpoint: get user info
5. ⏭️ Frontend: tab "Utente" in SoggettoDetail
6. ⏭️ Frontend: form creazione account
7. ⏭️ Email service (opzionale)
8. ⏭️ Cono di visibilità queries (advanced)

## Testing Checklist

- [ ] Creare account da anagrafica persona fisica
- [ ] Tentare creare per persona giuridica (deve fallire)
- [ ] Tentare creare duplicato (deve fallire)
- [ ] Login con nuovo account
- [ ] Verificare ruoli assegnati
- [ ] Disattivare account
- [ ] Cancellare soggetto con account (SET NULL)
