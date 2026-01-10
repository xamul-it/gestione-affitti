#!/usr/bin/env python3
"""
UAT Test Script - TC-003: Import Automatismi End-to-End
Esecuzione completa del test di import con tutti gli automatismi.
Usa solo l'API REST (non connessione diretta al database).
"""

import os
import sys
import csv
import json
import requests
import time
from datetime import datetime
from pathlib import Path
from io import StringIO

# Configurazione
API_BASE = "http://192.168.1.2:8000/api/v1"
TEST_OUTPUT_DIR = Path("/tmp/test_output")
TEST_OUTPUT_DIR.mkdir(exist_ok=True)

# Report
report = {
    'test_id': 'TC-003',
    'execution_date': datetime.now().isoformat(),
    'phases': {},
    'overall_result': 'PENDING'
}

def print_header(text):
    print("\n" + "=" * 80)
    print(f"  {text}")
    print("=" * 80)

def print_section(text):
    print(f"\n[{text}]")
    print("-" * 80)

def print_step(step_num, description):
    print(f"\n  STEP {step_num}: {description}")

print_header("UAT TEST EXECUTION - TC-003: Import Automatismi End-to-End")
print(f"Timestamp: {datetime.now().isoformat()}")
print(f"API Base: {API_BASE}")

# ============================================================================
# FASE 1: Verifica API disponibile
# ============================================================================
print_section("PHASE 1: API Connectivity Check")

try:
    response = requests.get(f"{API_BASE}/immobili", timeout=5)
    print(f"  ✓ API reachable (HTTP {response.status_code})")
    api_available = True
except Exception as e:
    print(f"  ✗ API not reachable: {e}")
    api_available = False

if not api_available:
    print("\n✗ Cannot proceed - API not available")
    sys.exit(1)

# ============================================================================
# FASE 2: Creazione CSV di test
# ============================================================================
print_section("PHASE 2: CSV Creation - Test Data with All Automation Patterns")

# Questo CSV simula esattamente quello descritto nel test plan TC-003
test_csv = """codice,tipo,indirizzo,citta,provincia,cap,superficie_mq,rendita_catastale,piano,locali
,Appartamento,"MILANO (MI) VIALE UMBRIA, 49 Piano 5",,,,,72,615.87,5,3
,Villa,"ROMA (RM) VIA APPIA ANTICA, 123",,,,,,1234.56,,4
,Box,"Via Garibaldi 10 Torino",,,,,15,200.00,,
,Negozio,"BOLOGNA (BO) VIA INDIPENDENZA, 45",,,,,80,850.00,,
,Ufficio,"Corso Vittorio Emanuele 78 Milano",,,,,120,1200.00,,2"""

csv_file_path = TEST_OUTPUT_DIR / "test_import_complete.csv"
csv_file_path.write_text(test_csv)

print(f"  ✓ CSV test file created: {csv_file_path}")
print(f"  ✓ CSV contains 5 records with realistic automation patterns")

# Anteprima CSV
print("\n  CSV Preview:")
for i, line in enumerate(test_csv.split('\n')[:3]):
    print(f"    {line}")
print(f"    ... ({test_csv.count(chr(10))} total lines)")

# ============================================================================
# FASE 3: Import via API
# ============================================================================
print_section("PHASE 3: Import Execution via API")

print_step(1, "Submit CSV file to import endpoint")

with open(csv_file_path, 'rb') as f:
    files = {'file': f}
    params = {
        'module_name': 'affitti_lungo',
        'entity_name': 'UnitaImmobiliare',
        'skip_errors': 'true'
    }

    print(f"  POST {API_BASE}/import-export/import")
    print(f"  Params: {json.dumps(params, indent=2)}")

    try:
        response = requests.post(
            f"{API_BASE}/import-export/import",
            files=files,
            params=params,
            timeout=30
        )

        print(f"\n  HTTP Status: {response.status_code}")

        if response.status_code == 200:
            import_result = response.json()
            print(f"  ✓ Import API call successful")
            print(f"    - Total rows: {import_result.get('total_rows')}")
            print(f"    - Imported: {import_result.get('imported')}")
            print(f"    - Errors: {import_result.get('errors')}")

            report['phases']['import'] = {
                'status': 'success',
                'result': import_result
            }
        else:
            print(f"  ✗ Import failed with status {response.status_code}")
            print(f"    Response: {response.text}")
            report['phases']['import'] = {
                'status': 'failed',
                'error': response.text
            }

    except Exception as e:
        print(f"  ✗ API call failed: {e}")
        report['phases']['import'] = {
            'status': 'failed',
            'error': str(e)
        }

# ============================================================================
# FASE 4: Verifica Automatismi via Query
# ============================================================================
print_section("PHASE 4: Automation Verification")

time.sleep(1)  # Breve pausa per assicurarsi che i dati siano committati

print_step(1, "Query immobili appena importati")

try:
    response = requests.get(f"{API_BASE}/immobili", timeout=10)

    if response.status_code == 200:
        immobili = response.json()
        print(f"  ✓ Query successful")
        print(f"  Total properties in system: {len(immobili) if isinstance(immobili, list) else 'unknown'}")

        if isinstance(immobili, list):
            # Prendi gli ultimi 5 (ultimi importati)
            latest = immobili[-5:] if len(immobili) >= 5 else immobili

            report['phases']['verification'] = {
                'status': 'completed',
                'records_found': len(latest),
                'records': []
            }

            # Mapping atteso
            expected_mapping = [
                ('Appartamento', 'MI00001', 'A/2', '20100', 'Milano', 'MI'),
                ('Villa', 'RM00001', 'A/8', '00100', 'Roma', 'RM'),
                ('Box', 'TO00001', 'C/6', '10100', 'Torino', 'TO'),
                ('Negozio', 'BO00001', 'C/1', '40100', 'Bologna', 'BO'),
                ('Ufficio', 'MI00002', 'A/10', '20100', 'Milano', 'MI')
            ]

            print_step(2, "Verify automatisms for each record")

            test_counters = {
                'codice_generation': {'pass': 0, 'fail': 0},
                'address_parsing': {'pass': 0, 'fail': 0},
                'cap_lookup': {'pass': 0, 'fail': 0},
                'timestamps': {'pass': 0, 'fail': 0}
            }

            for i, record in enumerate(latest[:5]):
                if i < len(expected_mapping):
                    exp_tipo, exp_codice, exp_cat, exp_cap, exp_citta, exp_prov = expected_mapping[i]

                    print(f"\n    Record {i+1}:")
                    print(f"      Tipo: {record.get('tipo')}")
                    print(f"      Codice: {record.get('codice')}")
                    print(f"      Città: {record.get('citta')}")
                    print(f"      Provincia: {record.get('provincia')}")
                    print(f"      CAP: {record.get('cap')}")
                    print(f"      Created: {record.get('created_at')}")

                    rec_report = {
                        'tipo': record.get('tipo'),
                        'codice': record.get('codice'),
                        'tests': {}
                    }

                    # Test 1: Codice Generation
                    if record.get('codice') == exp_codice:
                        print(f"      ✓ Codice generation PASSED (expected {exp_codice})")
                        test_counters['codice_generation']['pass'] += 1
                        rec_report['tests']['codice_generation'] = 'PASS'
                    else:
                        print(f"      ✗ Codice generation FAILED (expected {exp_codice}, got {record.get('codice')})")
                        test_counters['codice_generation']['fail'] += 1
                        rec_report['tests']['codice_generation'] = f"FAIL (expected {exp_codice})"

                    # Test 2: Address Parsing
                    if record.get('citta') and record.get('provincia'):
                        print(f"      ✓ Address parsing PASSED ({record.get('citta')}, {record.get('provincia')})")
                        test_counters['address_parsing']['pass'] += 1
                        rec_report['tests']['address_parsing'] = 'PASS'
                    else:
                        print(f"      ✗ Address parsing FAILED (citta={record.get('citta')}, prov={record.get('provincia')})")
                        test_counters['address_parsing']['fail'] += 1
                        rec_report['tests']['address_parsing'] = 'FAIL'

                    # Test 3: CAP Lookup
                    if record.get('cap') == exp_cap:
                        print(f"      ✓ CAP lookup PASSED (expected {exp_cap})")
                        test_counters['cap_lookup']['pass'] += 1
                        rec_report['tests']['cap_lookup'] = 'PASS'
                    else:
                        print(f"      ✗ CAP lookup FAILED (expected {exp_cap}, got {record.get('cap')})")
                        test_counters['cap_lookup']['fail'] += 1
                        rec_report['tests']['cap_lookup'] = f"FAIL (expected {exp_cap})"

                    # Test 4: Timestamps
                    if record.get('created_at'):
                        print(f"      ✓ Timestamps PASSED (created_at={record.get('created_at')})")
                        test_counters['timestamps']['pass'] += 1
                        rec_report['tests']['timestamps'] = 'PASS'
                    else:
                        print(f"      ✗ Timestamps FAILED (no created_at)")
                        test_counters['timestamps']['fail'] += 1
                        rec_report['tests']['timestamps'] = 'FAIL'

                    report['phases']['verification']['records'].append(rec_report)

            # Stampa summary
            print("\n\n  [TEST SUMMARY]")
            print("  " + "-" * 76)

            for test_name, counts in test_counters.items():
                total = counts['pass'] + counts['fail']
                percentage = (counts['pass'] / total * 100) if total > 0 else 0
                status = "PASS" if counts['fail'] == 0 else "FAIL"
                print(f"    {test_name}: {counts['pass']}/{total} ({percentage:.0f}%) - {status}")

            # Overall result
            overall_pass = all(c['fail'] == 0 for c in test_counters.values())
            report['overall_result'] = 'PASS' if overall_pass else 'FAIL'

        else:
            print(f"  ! API returned non-list response: {type(immobili)}")

    else:
        print(f"  ✗ Query failed with status {response.status_code}")

except Exception as e:
    print(f"  ✗ Query failed: {e}")
    report['phases']['verification'] = {
        'status': 'failed',
        'error': str(e)
    }

# ============================================================================
# REPORT
# ============================================================================
print_header(f"OVERALL RESULT: {report['overall_result']}")

report_file = TEST_OUTPUT_DIR / "test_report.json"
with open(report_file, 'w') as f:
    json.dump(report, f, indent=2, default=str)

print(f"\nDetailed report saved to: {report_file}")

print("\n" + "=" * 80)
print("UAT TEST EXECUTION COMPLETE")
print("=" * 80)

sys.exit(0 if report['overall_result'] == 'PASS' else 1)
