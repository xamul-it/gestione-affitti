# Deployment Checklist - Regression Fixes 2025-12-26

## Pre-Deployment Checks

### ✅ Code Verification
- [x] All 14 files modified correctly
- [x] 6 routers registered in anagrafica_italiana module
- [x] Router prefixes corrected with `/anagrafica` prefix
- [x] Scadenze removed from menu
- [x] Condominio.nome is nullable
- [x] Alembic migration created

### ✅ Testing (Local)
Run automated verification:
```bash
cd /home/htpc/test/gestione-affitti/backend
bash test_startup.sh
```

Expected output:
- [x] All critical files exist
- [x] 6 routers in ROUTERS list
- [x] Scadenze not in menu
- [x] Condominio.nome nullable

---

## Deployment Steps

### Step 1: Backup Current State
```bash
cd /home/htpc/test/gestione-affitti

# Backup database
pg_dump -U your_user gestione_affitti > backup_$(date +%Y%m%d_%H%M%S).sql

# Commit current state
git add -A
git commit -m "Pre-deployment backup before regression fixes"
```

### Step 2: Stop Services
```bash
# Stop backend
pkill -f "python.*app.main" || echo "Backend not running"

# Stop frontend
pkill -f "vite" || echo "Frontend not running"
```

### Step 3: Apply Backend Changes
```bash
cd /home/htpc/test/gestione-affitti/backend
source venv/bin/activate

# Verify changes
bash test_startup.sh

# Apply database migration
alembic upgrade head

# Expected output:
# INFO  [alembic.runtime.migration] Running upgrade -> 2025122601, make nome field optional
```

### Step 4: Start Backend
```bash
cd /home/htpc/test/gestione-affitti/backend
source venv/bin/activate

# Start with logging
python app/main.py 2>&1 | tee logs/startup_$(date +%Y%m%d_%H%M%S).log
```

**Watch for in logs:**
- ✅ "Registered 6 routers" for anagrafica_italiana
- ✅ "Registered 5 platform menu items" (Scadenze removed = 6-1=5)
- ✅ No errors during startup

### Step 5: Verify Backend Endpoints
Open new terminal:
```bash
# Get auth token
TOKEN=$(curl -s -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"changeme123"}' \
  | jq -r '.access_token')

echo "Token: $TOKEN"

# Test comuni endpoint
curl -s -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/v1/anagrafica/domini/comuni/?limit=1" | jq

# Expected: JSON array with 1 comune

# Test ruoli-azienda endpoint
curl -s -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/v1/anagrafica/ruoli-azienda/" | jq

# Expected: JSON array (may be empty)

# Test creating Condominio without nome
curl -s -X POST "http://localhost:8000/api/v1/immobili/condomini/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "codice": "TEST_COND_001",
    "indirizzo": "Via Test 123",
    "citta": "Milano"
  }' | jq

# Expected: 201 Created with condominio object
```

### Step 6: Start Frontend
```bash
cd /home/htpc/test/gestione-affitti/frontend

# Clear old build cache
rm -rf node_modules/.vite

# Start frontend
npm run dev
```

### Step 7: Frontend Verification

#### 7a. Clear Browser Cache
1. Open browser DevTools (F12)
2. Go to Application tab
3. Click "Clear storage"
4. Clear: Local Storage, Session Storage, Cookies
5. Reload page (Ctrl+Shift+R)

#### 7b. Test Tenant Selection (CRITICAL)
1. Open browser
2. Navigate to `http://192.168.1.2:3000/login`
3. Login with credentials
4. **Open Network tab in DevTools BEFORE continuing**
5. Observe tenant selection page load
6. **Verify: Only ONE call to `/api/v1/tenants/my-tenants`**
7. Select tenant
8. Verify smooth redirect to dashboard

**Expected:**
- ✅ Only 1 API call to /tenants/my-tenants
- ✅ No infinite loop
- ✅ No browser freeze
- ✅ Smooth tenant selection

#### 7c. Test Menu
1. Check sidebar menu
2. **Verify: "Scadenze" is NOT visible**
3. **Verify: Scadenze badge IS visible in TopBar**
4. Click badge → should show notifiche panel

#### 7d. Test Comuni Endpoint
1. Navigate to `/anagrafiche/comuni`
2. Verify page loads
3. Verify comuni list displays
4. Test search and filters

#### 7e. Test Ruoli Azienda
1. Navigate to `/anagrafiche/ruoli-azienda`
2. Verify page loads without errors
3. Verify list displays
4. Test creating new association (if data exists)

#### 7f. Test Nome Field Optional
1. Navigate to Condomini list
2. Click "Nuovo Condominio"
3. Fill only: codice, indirizzo, citta
4. **Leave nome empty**
5. Submit form
6. **Verify: Success - entity created**

---

## Post-Deployment Verification

### Backend Health Check
```bash
# Check process
ps aux | grep "python.*app.main"

# Check logs for errors
tail -f backend/logs/startup_*.log

# Test health endpoint
curl http://localhost:8000/health
# Expected: {"status":"ok"}
```

### Frontend Health Check
```bash
# Check process
ps aux | grep "vite"

# Check browser console
# Expected: No errors in console
```

### Database Verification
```bash
# Connect to database
psql -U your_user gestione_affitti

# Verify migration applied
SELECT * FROM alembic_version;
# Expected: 2025122601

# Check condomini table structure
\d condomini
# Verify nome column: nullable = YES

# Exit
\q
```

---

## Rollback Procedure

If critical issues occur:

### Quick Rollback (Code Only)
```bash
cd /home/htpc/test/gestione-affitti

# Stop services
pkill -f "python.*app.main"
pkill -f "vite"

# Rollback code
git reset --hard HEAD~1

# Rollback database
cd backend
source venv/bin/activate
alembic downgrade -1

# Restart services
python app/main.py &
cd ../frontend
npm run dev &
```

### Full Rollback (Database Restore)
```bash
# Stop all services
pkill -f "python.*app.main"
pkill -f "vite"

# Restore database
psql -U your_user gestione_affitti < backup_YYYYMMDD_HHMMSS.sql

# Rollback code
cd /home/htpc/test/gestione-affitti
git reset --hard HEAD~1

# Restart services
cd backend && source venv/bin/activate && python app/main.py &
cd ../frontend && npm run dev &
```

---

## Monitoring Post-Deployment

### First 15 Minutes
- [ ] Monitor backend logs for errors
- [ ] Monitor frontend console for errors
- [ ] Check CPU/Memory usage (should be normal)
- [ ] Test login flow 3 times
- [ ] Test tenant selection 3 times
- [ ] Verify no infinite loops

### First Hour
- [ ] Monitor API response times
- [ ] Check database connections
- [ ] Verify all menu items work
- [ ] Test CRUD operations on key entities
- [ ] Check for any user reports of issues

### First Day
- [ ] Review error logs
- [ ] Check database growth (should be normal)
- [ ] Verify performance metrics
- [ ] Collect user feedback

---

## Success Criteria

Deployment is successful when:
- ✅ No infinite tenant fetching loops
- ✅ All 6 anagrafica routers accessible
- ✅ Scadenze not in menu (but badge works)
- ✅ Entities can be created without nome field
- ✅ No new errors in logs
- ✅ Performance equal or better than before
- ✅ All existing functionality works

---

## Troubleshooting

### Issue: Backend won't start
```bash
# Check logs
tail -100 backend/logs/startup_*.log

# Common issues:
# 1. Port 8000 in use: pkill -f "python.*app.main"
# 2. Database not accessible: check DATABASE_URL in .env
# 3. Migration failed: alembic downgrade -1, then check database
```

### Issue: Frontend shows infinite loops
```bash
# 1. Clear browser cache completely
# 2. Clear sessionStorage: sessionStorage.clear() in console
# 3. Reload page with Ctrl+Shift+R
# 4. If persists, check TenantSelector.jsx changes were applied
```

### Issue: 404 on comuni endpoint
```bash
# Check router registration
cd backend/modules/anagrafica_italiana
grep -A 7 "^ROUTERS = " __init__.py

# Should show 6 routers including domini_router

# Check backend logs
grep "anagrafica_italiana" logs/startup_*.log
# Should show "Registered 6 routers"
```

### Issue: Nome field still required
```bash
# Check migration applied
cd backend
source venv/bin/activate
alembic current
# Should show: 2025122601

# If not applied:
alembic upgrade head
```

---

## Contact Information

- **Technical Lead**: [Your Name]
- **Database Admin**: [DBA Name]
- **Support**: [Support Email]

---

## Sign-off

- [ ] Code changes reviewed
- [ ] Automated tests passed
- [ ] Manual testing completed
- [ ] Documentation updated
- [ ] Rollback plan tested
- [ ] Team notified of deployment
- [ ] Backup created

**Approved by**: _______________
**Date**: _______________

---

## Related Documents

- `FIXES_SUMMARY.md` - Executive summary
- `REGRESSION_FIXES_2025-12-26.md` - Detailed technical documentation
- `backend/test_startup.sh` - Automated verification script
- `backend/alembic/versions/2025122601_make_nome_optional.py` - Migration

