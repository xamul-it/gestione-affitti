#!/usr/bin/env python3
"""
Verification script for regression fixes 2025-12-26
"""
import sys
import os

# Add modules to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../modules'))

print("=" * 60)
print("REGRESSION FIXES VERIFICATION")
print("=" * 60)

# Test 1: Check if routers are properly imported
print("\n1. Testing anagrafica_italiana router registration...")
try:
    from anagrafica_italiana import ROUTERS
    print(f"   ✅ Anagrafica module has {len(ROUTERS)} routers registered:")
    for router in ROUTERS:
        print(f"      - {router.prefix}")
except Exception as e:
    print(f"   ❌ Error importing routers: {e}")

# Test 2: Check model field changes
print("\n2. Testing Condominio model 'nome' field...")
try:
    from immobili.models.condomini import Condominio
    nome_column = Condominio.__table__.columns.get('nome')
    if nome_column:
        is_nullable = nome_column.nullable
        print(f"   {'✅' if is_nullable else '❌'} Condominio.nome nullable: {is_nullable}")
    else:
        print("   ❌ Condominio.nome column not found")
except Exception as e:
    print(f"   ❌ Error checking model: {e}")

# Test 3: Check schema changes
print("\n3. Testing Pydantic schema changes...")
try:
    from immobili.schemas.condomini import CondominioBase
    from pydantic import ValidationError

    # Test creating Condominio without nome
    test_data = {
        "codice": "TEST001",
        "indirizzo": "Via Test 1",
        "citta": "Milano"
    }

    try:
        obj = CondominioBase(**test_data)
        print(f"   ✅ CondominioBase accepts data without 'nome': {obj.codice}")
    except ValidationError as ve:
        print(f"   ❌ CondominioBase validation failed: {ve}")

except Exception as e:
    print(f"   ❌ Error testing schema: {e}")

# Test 4: Check if Scadenze is removed from menu
print("\n4. Checking main.py for Scadenze menu removal...")
try:
    with open(os.path.join(os.path.dirname(__file__), 'app/main.py'), 'r') as f:
        content = f.read()
        if '"id": "platform.scadenze"' not in content:
            print("   ✅ Scadenze menu item removed from main.py")
        else:
            print("   ❌ Scadenze menu item still present in main.py")
except Exception as e:
    print(f"   ❌ Error reading main.py: {e}")

# Test 5: Check migration file exists
print("\n5. Checking Alembic migration...")
migration_file = os.path.join(
    os.path.dirname(__file__),
    'alembic/versions/2025122601_make_nome_optional.py'
)
if os.path.exists(migration_file):
    print(f"   ✅ Migration file exists: {migration_file}")
else:
    print(f"   ❌ Migration file not found: {migration_file}")

print("\n" + "=" * 60)
print("VERIFICATION COMPLETE")
print("=" * 60)
print("\nNext steps:")
print("1. Start backend: cd backend && source venv/bin/activate && python app/main.py")
print("2. Test endpoints using curl or frontend")
print("3. Apply migration: cd backend && alembic upgrade head")
print("=" * 60)
