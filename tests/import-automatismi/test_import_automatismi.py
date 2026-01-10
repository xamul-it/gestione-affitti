#!/usr/bin/env python3
"""
Test script for import automatismi with user-provided CSV
"""
import sys
import os

# Add backend to path
sys.path.insert(0, '/home/htpc/test/gestione-affitti/backend')

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.core.platform_services.import_export_service import ImportExportService
from app.modules.affitti_lungo.models import UnitaImmobiliare
from app.modules.affitti_lungo.schemas import UnitaImmobiliareCreate

def main():
    print("=" * 80)
    print("TEST: Import Automatismi con CSV Utente")
    print("=" * 80)

    # Setup database
    engine = create_engine(str(settings.DATABASE_URL))
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()

    # Read CSV file (use project-relative path)
    csv_file = os.path.join(os.path.dirname(__file__), 'test_clean_import.csv')

    if not os.path.exists(csv_file):
        print(f"❌ File not found: {csv_file}")
        return

    print(f"\n📄 Reading CSV: {csv_file}")

    with open(csv_file, 'r', encoding='utf-8-sig') as f:
        csv_data = f.read()

    print(f"✓ CSV read successfully ({len(csv_data)} bytes)")

    # Field mapping (CSV column → model field)
    field_mapping = {
        'codice': 'codice',
        'tipo': 'tipo',
        'condominio_id': 'condominio_id',
        'indirizzo': 'indirizzo',
        'citta': 'citta',
        'cap': 'cap',
        'provincia': 'provincia',
        'superficie_mq': 'superficie_mq',
        'locali': 'locali',
        'piano': 'piano',
        'classe_energetica': 'classe_energetica',
        'rendita_catastale': 'rendita_catastale',
        'foglio': 'foglio',
        'particella': 'particella',
        'subalterno': 'subalterno',
        'descrizione': 'descrizione',
        'note': 'note',
    }

    print(f"\n🔧 Field mapping configured ({len(field_mapping)} fields)")

    # Execute import
    print("\n🚀 Starting import with enrichment...")
    print("-" * 80)

    service = ImportExportService(db)

    try:
        result = service.import_from_csv_with_enrichment(
            model=UnitaImmobiliare,
            csv_data=csv_data,
            field_mapping=field_mapping,
            create_schema=UnitaImmobiliareCreate,
            skip_errors=True,
            enable_updates=False  # Only INSERT for test
        )

        print("\n✅ IMPORT COMPLETED")
        print("=" * 80)
        print(f"📊 Statistics:")
        print(f"   Total rows:     {result['total_rows']}")
        print(f"   Created:        {result.get('created', 0)}")
        print(f"   Updated:        {result.get('updated', 0)}")
        print(f"   Errors:         {result['errors']}")
        print(f"   Warnings:       {len(result.get('warnings', []))}")
        print()

        # Show warnings
        if result.get('warnings'):
            print("⚠️  WARNINGS:")
            for i, warning in enumerate(result['warnings'][:10], 1):  # Show first 10
                row = warning.get('row', '?')
                msgs = warning.get('warnings', [])
                print(f"   {i}. Row {row}: {', '.join(msgs)}")

            if len(result['warnings']) > 10:
                print(f"   ... and {len(result['warnings']) - 10} more warnings")
            print()

        # Show errors
        if result.get('error_details'):
            print("❌ ERRORS:")
            for i, error in enumerate(result['error_details'][:5], 1):  # Show first 5
                row = error.get('row', error.get('data', {}).get('row', '?'))
                err_msg = error.get('error', 'Unknown error')
                print(f"   {i}. Row {row}: {err_msg}")

            if len(result['error_details']) > 5:
                print(f"   ... and {len(result['error_details']) - 5} more errors")
            print()

        # Query database to verify
        print("\n🔍 Verifying database records...")

        count = db.query(UnitaImmobiliare).count()
        print(f"   Total UnitaImmobiliare in DB: {count}")

        # Show sample records
        samples = db.query(UnitaImmobiliare).limit(3).all()

        if samples:
            print(f"\n📋 Sample records (first 3):")
            for i, record in enumerate(samples, 1):
                print(f"\n   {i}. ID: {record.id}")
                print(f"      Codice: {record.codice} (auto: {getattr(record, 'codice_auto_generated', False)})")
                print(f"      Tipo: {record.tipo}")
                print(f"      Indirizzo: {record.indirizzo}")
                print(f"      Città: {record.citta}, Provincia: {record.provincia}, CAP: {record.cap}")
                print(f"      Categoria Catastale ID: {getattr(record, 'categoria_catastale_id', 'N/A')}")
                if hasattr(record, 'categoria_catastale') and record.categoria_catastale:
                    print(f"      Categoria: {record.categoria_catastale.codice} - {record.categoria_catastale.nome}")
                warnings = getattr(record, 'indirizzo_parsed_warnings', None)
                if warnings:
                    print(f"      Warnings: {warnings}")

        print("\n" + "=" * 80)
        print("✅ TEST COMPLETED SUCCESSFULLY")
        print("=" * 80)

    except Exception as e:
        print(f"\n❌ ERROR during import:")
        print(f"   {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()

    finally:
        db.close()

if __name__ == '__main__':
    main()
