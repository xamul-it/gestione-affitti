#!/usr/bin/env python3
"""
UAT Test Script - TC-003: Import Automatismi End-to-End
Esecuzione completa del test di import con tutti gli automatismi.
"""

import os
import sys
import csv
import json
import requests
from datetime import datetime
from pathlib import Path

# Aggiungi backend al path
sys.path.insert(0, '/home/htpc/test/gestione-affitti/backend')

from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.core.database import Base
from app.modules.affitti_lungo.models import UnitaImmobiliare
from app.core.models import CategoriaCatastale, ComuneItalia

# Configurazione
API_BASE = "http://192.168.1.2:8000/api/v1"
TEST_OUTPUT_DIR = Path("/tmp/test_output")
TEST_OUTPUT_DIR.mkdir(exist_ok=True)

# Setup database
engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

print("=" * 80)
print("UAT TEST EXECUTION - TC-003: Import Automatismi End-to-End")
print("=" * 80)
print(f"Timestamp: {datetime.now().isoformat()}")
print()

# ============================================================================
# FASE 1: SETUP - Pulisci database e verifica seed
# ============================================================================
print("\n[PHASE 1] SETUP: Database Cleanup & Verification")
print("-" * 80)

db = SessionLocal()
try:
    # Pulisci tabella unita_immobiliari
    print("  Cleaning unita_immobiliari table...")
    db.execute(text("DELETE FROM unita_immobiliari"))
    db.commit()

    # Conta dopo pulizia
    count_after = db.query(UnitaImmobiliare).count()
    print(f"  ✓ Database cleaned. Records remaining: {count_after}")

    # Verifica seed comuni
    comuni_count = db.query(ComuneItalia).count()
    print(f"  ✓ Comuni Italia seeded: {comuni_count} records")
    if comuni_count < 50:
        print(f"    WARNING: Expected ~80+ comuni, found {comuni_count}")

    # Verifica seed categorie
    categorie_count = db.query(CategoriaCatastale).count()
    print(f"  ✓ Categorie Catastali seeded: {categorie_count} records")
    if categorie_count < 40:
        print(f"    WARNING: Expected ~45 categorie, found {categorie_count}")

    print("  ✓ Setup Phase PASSED")

except Exception as e:
    print(f"  ✗ Setup Phase FAILED: {e}")
    sys.exit(1)
finally:
    db.close()

# ============================================================================
# FASE 2: Creare CSV di test con automatismi
# ============================================================================
print("\n[PHASE 2] CSV Creation - Test Data with All Automation Patterns")
print("-" * 80)

test_csv = """codice,tipo,indirizzo,citta,provincia,cap,superficie_mq,rendita_catastale,piano,locali
,Appartamento,"MILANO (MI) VIALE UMBRIA, 49 Piano 5",,,,,72,615.87,5,3
,Villa,"ROMA (RM) VIA APPIA ANTICA, 123",,,,,,1234.56,,4
,Box,"Via Garibaldi 10 Torino",,,,,15,200.00,,
,Negozio,"BOLOGNA (BO) VIA INDIPENDENZA, 45",,,,,80,850.00,,
,Ufficio,"Corso Vittorio Emanuele 78 Milano",,,,,120,1200.00,,2"""

# ERRORI REALISTICI INTRODOTTI (come farebbe un vero utente)
# Record 1: Parte vuoto il CAP ma con provincia piena
# Record 2: Provincia vuota (il sistema dovrebbe derivarla da Roma)
# Record 3: Indirizzo minimalista "Via Garibaldi 10 Torino" - il parser dovrebbe normalizzare
# Record 4: Tutto normalmente formattato
# Record 5: Manca il numero civico

csv_file_path = TEST_OUTPUT_DIR / "test_import_complete.csv"
csv_file_path.write_text(test_csv)
print(f"  ✓ CSV test file created: {csv_file_path}")
print(f"  ✓ CSV contains 5 records with realistic automation patterns")

# ============================================================================
# FASE 3: Effettuare import via API
# ============================================================================
print("\n[PHASE 3] Import Execution via API")
print("-" * 80)

with open(csv_file_path, 'rb') as f:
    files = {'file': f}
    params = {
        'module_name': 'affitti_lungo',
        'entity_name': 'UnitaImmobiliare',
        'skip_errors': 'true'
    }

    print(f"  Calling: POST {API_BASE}/import-export/import")
    print(f"  Params: {params}")

    try:
        response = requests.post(
            f"{API_BASE}/import-export/import",
            files=files,
            params=params,
            timeout=30
        )

        print(f"  HTTP Status: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            print(f"  ✓ Import successful")
            print(f"    - Total rows: {result.get('total_rows')}")
            print(f"    - Imported: {result.get('imported')}")
            print(f"    - Errors: {result.get('errors')}")

            # Save result
            import_result = result
        else:
            print(f"  ✗ Import failed with status {response.status_code}")
            print(f"    Response: {response.text}")
            sys.exit(1)

    except Exception as e:
        print(f"  ✗ API call failed: {e}")
        sys.exit(1)

# ============================================================================
# FASE 4: Verifica Automatismi
# ============================================================================
print("\n[PHASE 4] Automation Verification")
print("-" * 80)

db = SessionLocal()
try:
    records = db.query(UnitaImmobiliare).order_by(UnitaImmobiliare.id).all()

    print(f"  Total records imported: {len(records)}")

    # Mapping di test atteso
    expected = [
        {
            'tipo': 'Appartamento',
            'expected_codice': 'MI00001',
            'expected_categoria': 'A/2',  # Abitazioni civili
            'expected_cap': '20100',
            'expected_citta': 'Milano',
            'expected_provincia': 'MI'
        },
        {
            'tipo': 'Villa',
            'expected_codice': 'RM00001',
            'expected_categoria': 'A/8',  # Ville
            'expected_cap': '00100',
            'expected_citta': 'Roma',
            'expected_provincia': 'RM'
        },
        {
            'tipo': 'Box',
            'expected_codice': 'TO00001',
            'expected_categoria': 'C/6',  # Autorimesse
            'expected_cap': '10100',
            'expected_citta': 'Torino',
            'expected_provincia': 'TO'
        },
        {
            'tipo': 'Negozio',
            'expected_codice': 'BO00001',
            'expected_categoria': 'C/1',  # Negozi e botteghe
            'expected_cap': '40100',
            'expected_citta': 'Bologna',
            'expected_provincia': 'BO'
        },
        {
            'tipo': 'Ufficio',
            'expected_codice': 'MI00002',
            'expected_categoria': 'A/10',  # Uffici e studi privati
            'expected_cap': '20100',
            'expected_citta': 'Milano',
            'expected_provincia': 'MI'
        }
    ]

    # Verifica per ogni record
    test_results = {
        'codice_generation': {'passed': 0, 'failed': 0, 'details': []},
        'timestamps': {'passed': 0, 'failed': 0, 'details': []},
        'address_parsing': {'passed': 0, 'failed': 0, 'details': []},
        'cap_lookup': {'passed': 0, 'failed': 0, 'details': []},
        'categoria_catastale': {'passed': 0, 'failed': 0, 'details': []}
    }

    for i, record in enumerate(records[:5]):
        exp = expected[i]

        print(f"\n  Record {i+1}: {record.tipo}")
        print(f"    ID: {record.id}")
        print(f"    Codice: {record.codice}")
        print(f"    Città: {record.citta}")
        print(f"    Provincia: {record.provincia}")
        print(f"    CAP: {record.cap}")
        print(f"    Categoria Catastale ID: {record.categoria_catastale_id}")
        print(f"    Created at: {record.created_at}")
        print(f"    Updated at: {record.updated_at}")

        # Test 1: Codice Generation
        if record.codice == exp['expected_codice']:
            print(f"    ✓ Codice generation PASSED")
            test_results['codice_generation']['passed'] += 1
        else:
            print(f"    ✗ Codice generation FAILED: expected {exp['expected_codice']}, got {record.codice}")
            test_results['codice_generation']['failed'] += 1
            test_results['codice_generation']['details'].append({
                'record': i+1,
                'expected': exp['expected_codice'],
                'actual': record.codice
            })

        # Test 2: Timestamps
        if record.created_at and record.updated_at:
            print(f"    ✓ Timestamps PASSED")
            test_results['timestamps']['passed'] += 1
        else:
            print(f"    ✗ Timestamps FAILED: created_at={record.created_at}, updated_at={record.updated_at}")
            test_results['timestamps']['failed'] += 1
            test_results['timestamps']['details'].append({
                'record': i+1,
                'created_at': record.created_at,
                'updated_at': record.updated_at
            })

        # Test 3: Address Parsing
        if record.citta and record.provincia and record.indirizzo:
            print(f"    ✓ Address parsing PASSED")
            test_results['address_parsing']['passed'] += 1
        else:
            print(f"    ✗ Address parsing FAILED: citta={record.citta}, provincia={record.provincia}, indirizzo={record.indirizzo}")
            test_results['address_parsing']['failed'] += 1
            test_results['address_parsing']['details'].append({
                'record': i+1,
                'citta': record.citta,
                'provincia': record.provincia,
                'indirizzo': record.indirizzo
            })

        # Test 4: CAP Lookup
        if record.cap == exp['expected_cap']:
            print(f"    ✓ CAP lookup PASSED")
            test_results['cap_lookup']['passed'] += 1
        else:
            print(f"    ✗ CAP lookup FAILED: expected {exp['expected_cap']}, got {record.cap}")
            test_results['cap_lookup']['failed'] += 1
            test_results['cap_lookup']['details'].append({
                'record': i+1,
                'expected': exp['expected_cap'],
                'actual': record.cap
            })

        # Test 5: Categoria Catastale
        if record.categoria_catastale_id:
            categoria = db.query(CategoriaCatastale).filter_by(id=record.categoria_catastale_id).first()
            if categoria:
                expected_cat_code = exp['expected_categoria']
                if categoria.codice == expected_cat_code:
                    print(f"    ✓ Categoria catastale PASSED ({categoria.codice})")
                    test_results['categoria_catastale']['passed'] += 1
                else:
                    print(f"    ✗ Categoria catastale FAILED: expected {expected_cat_code}, got {categoria.codice}")
                    test_results['categoria_catastale']['failed'] += 1
                    test_results['categoria_catastale']['details'].append({
                        'record': i+1,
                        'expected': expected_cat_code,
                        'actual': categoria.codice
                    })
            else:
                print(f"    ✗ Categoria catastale FAILED: ID {record.categoria_catastale_id} not found")
                test_results['categoria_catastale']['failed'] += 1
        else:
            print(f"    ✗ Categoria catastale FAILED: categoria_catastale_id is None")
            test_results['categoria_catastale']['failed'] += 1

    # Stampa riepilogo test
    print("\n\n[TEST SUMMARY]")
    print("-" * 80)
    for test_name, result in test_results.items():
        total = result['passed'] + result['failed']
        percentage = (result['passed'] / total * 100) if total > 0 else 0
        status = "PASSED" if result['failed'] == 0 else "FAILED"
        print(f"  {test_name}: {result['passed']}/{total} ({percentage:.0f}%) - {status}")
        if result['details']:
            for detail in result['details']:
                print(f"    - {detail}")

except Exception as e:
    print(f"  ✗ Verification failed: {e}")
    import traceback
    traceback.print_exc()
finally:
    db.close()

print("\n" + "=" * 80)
print("UAT TEST EXECUTION COMPLETE")
print("=" * 80)
