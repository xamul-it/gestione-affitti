#!/usr/bin/env python3
"""
Direct test of enrichment service - TC-003 Import Automatismi
Tests the enrichment features directly (bypassing API endpoint bug)
"""

import sys
import os
sys.path.insert(0, '/home/htpc/test/gestione-affitti/backend')
os.environ['PGPASSWORD'] = 'affitti'

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.core.platform_services.import_export_service import ImportExportService
from app.modules.affitti_lungo.models import UnitaImmobiliare
from app.core.models import CategoriaCatastale
from datetime import datetime

# Setup
engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
db = SessionLocal()

print("=" * 80)
print("DIRECT TEST: Import Enrichment Service - TC-003")
print("=" * 80)
print(f"Start: {datetime.now().isoformat()}\n")

# CSV data - exactly as per test plan
csv_data = """codice,tipo,indirizzo,citta,provincia,cap,superficie_mq,rendita_catastale,piano,locali
,Appartamento,"MILANO (MI) VIALE UMBRIA, 49 Piano 5",,,,,72,615.87,5,3
,Villa,"ROMA (RM) VIA APPIA ANTICA, 123",,,,,,1234.56,,4
,Box,"Via Garibaldi 10 Torino",,,,,15,200.00,,
,Negozio,"BOLOGNA (BO) VIA INDIPENDENZA, 45",,,,,80,850.00,,
,Ufficio,"Corso Vittorio Emanuele 78 Milano",,,,,120,1200.00,,2"""

# Field mapping
field_mapping = {
    'codice': 'codice',
    'tipo': 'tipo',
    'indirizzo': 'indirizzo',
    'citta': 'citta',
    'provincia': 'provincia',
    'cap': 'cap',
    'superficie_mq': 'superficie_mq',
    'rendita_catastale': 'rendita_catastale',
    'piano': 'piano',
    'locali': 'locali'
}

print("STEP 1: Cleaning database")
print("-" * 80)
try:
    # Clean existing
    db.execute(text("DELETE FROM unita_immobiliari"))
    db.commit()
    count = db.query(UnitaImmobiliare).count()
    print(f"✓ Database cleaned. Records: {count}\n")
except Exception as e:
    print(f"✗ Cleanup failed: {e}")
    sys.exit(1)

print("STEP 2: Import with enrichment service")
print("-" * 80)

service = ImportExportService(db)

try:
    result = service.import_from_csv_with_enrichment(
        model=UnitaImmobiliare,
        csv_data=csv_data,
        field_mapping=field_mapping,
        skip_errors=True,
        enable_updates=False
    )

    print(f"Result:")
    print(f"  Total rows: {result['total_rows']}")
    print(f"  Created: {result['created']}")
    print(f"  Updated: {result['updated']}")
    print(f"  Errors: {result['errors']}")
    print(f"  Warnings: {len(result['warnings'])}")

    if result['errors'] > 0:
        print(f"\nErrors:")
        for err in result['error_details'][:3]:
            print(f"  Row {err['row']}: {err['error']}")

    if result['warnings']:
        print(f"\nWarnings:")
        for warn in result['warnings'][:3]:
            print(f"  Row {warn['row']}: {warn['warnings']}")

except Exception as e:
    print(f"✗ Import failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\nSTEP 3: Verify automatismi")
print("-" * 80)

# Query imported records
records = db.query(UnitaImmobiliare).order_by(UnitaImmobiliare.id).all()
print(f"Total imported: {len(records)}\n")

# Expected results per test plan
expected = [
    {
        'tipo': 'Appartamento',
        'codice': 'MI00001',
        'citta': 'Milano',
        'provincia': 'MI',
        'cap': '20100',
        'categoria': 'A/2'
    },
    {
        'tipo': 'Villa',
        'codice': 'RM00001',
        'citta': 'Roma',
        'provincia': 'RM',
        'cap': '00100',
        'categoria': 'A/8'
    },
    {
        'tipo': 'Box',
        'codice': 'TO00001',
        'citta': 'Torino',
        'provincia': 'TO',
        'cap': '10100',
        'categoria': 'C/6'
    },
    {
        'tipo': 'Negozio',
        'codice': 'BO00001',
        'citta': 'Bologna',
        'provincia': 'BO',
        'cap': '40100',
        'categoria': 'C/1'
    },
    {
        'tipo': 'Ufficio',
        'codice': 'MI00002',
        'citta': 'Milano',
        'provincia': 'MI',
        'cap': '20100',
        'categoria': 'A/10'
    }
]

test_results = {
    'CODICE_GENERATION': {'pass': 0, 'fail': 0},
    'ADDRESS_PARSING': {'pass': 0, 'fail': 0},
    'CAP_LOOKUP': {'pass': 0, 'fail': 0},
    'TIMESTAMPS': {'pass': 0, 'fail': 0},
    'CATEGORIA_CATASTALE': {'pass': 0, 'fail': 0}
}

for i, record in enumerate(records[:5]):
    exp = expected[i]
    print(f"Record {i+1} ({exp['tipo']}):")
    print(f"  ID: {record.id}")
    print(f"  Codice: {record.codice}")
    print(f"  Città: {record.citta} | Provincia: {record.provincia}")
    print(f"  CAP: {record.cap}")
    print(f"  Created: {record.created_at.isoformat()[:19] if record.created_at else 'NULL'}")

    # Test 1: Codice Generation
    if record.codice == exp['codice']:
        print(f"  ✓ CODICE_GENERATION: {record.codice}")
        test_results['CODICE_GENERATION']['pass'] += 1
    else:
        print(f"  ✗ CODICE_GENERATION: expected {exp['codice']}, got {record.codice}")
        test_results['CODICE_GENERATION']['fail'] += 1

    # Test 2: Address Parsing
    if record.citta == exp['citta'] and record.provincia == exp['provincia']:
        print(f"  ✓ ADDRESS_PARSING: {record.citta}, {record.provincia}")
        test_results['ADDRESS_PARSING']['pass'] += 1
    else:
        print(f"  ✗ ADDRESS_PARSING: expected {exp['citta']}/{exp['provincia']}, got {record.citta}/{record.provincia}")
        test_results['ADDRESS_PARSING']['fail'] += 1

    # Test 3: CAP Lookup
    if record.cap == exp['cap']:
        print(f"  ✓ CAP_LOOKUP: {record.cap}")
        test_results['CAP_LOOKUP']['pass'] += 1
    else:
        print(f"  ✗ CAP_LOOKUP: expected {exp['cap']}, got {record.cap}")
        test_results['CAP_LOOKUP']['fail'] += 1

    # Test 4: Timestamps
    if record.created_at is not None:
        print(f"  ✓ TIMESTAMPS: created_at set")
        test_results['TIMESTAMPS']['pass'] += 1
    else:
        print(f"  ✗ TIMESTAMPS: created_at is NULL")
        test_results['TIMESTAMPS']['fail'] += 1

    # Test 5: Categoria Catastale
    if record.categoria_catastale_id:
        cat = db.query(CategoriaCatastale).filter_by(id=record.categoria_catastale_id).first()
        if cat and cat.codice == exp['categoria']:
            print(f"  ✓ CATEGORIA_CATASTALE: {cat.codice}")
            test_results['CATEGORIA_CATASTALE']['pass'] += 1
        else:
            actual_cat = cat.codice if cat else 'NOT FOUND'
            print(f"  ✗ CATEGORIA_CATASTALE: expected {exp['categoria']}, got {actual_cat}")
            test_results['CATEGORIA_CATASTALE']['fail'] += 1
    else:
        print(f"  ✗ CATEGORIA_CATASTALE: categoria_catastale_id is NULL")
        test_results['CATEGORIA_CATASTALE']['fail'] += 1

    print()

# Summary
print("=" * 80)
print("TEST SUMMARY")
print("=" * 80)

overall_pass = True
for test_name, counts in test_results.items():
    total = counts['pass'] + counts['fail']
    if total > 0:
        pct = counts['pass'] / total * 100
        status = "PASS" if counts['fail'] == 0 else "FAIL"
        print(f"{test_name}: {counts['pass']}/{total} ({pct:.0f}%) - {status}")
        if counts['fail'] > 0:
            overall_pass = False

print("\n" + "=" * 80)
if overall_pass and result['created'] == 5:
    print("OVERALL RESULT: PASS")
    print("✓ All automatismi working correctly!")
else:
    print("OVERALL RESULT: FAIL")
print("=" * 80)

db.close()
