#!/usr/bin/env python3
"""Script to rename core tables with core_ prefix."""
import os
import sys

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv('DATABASE_URL')

if not DATABASE_URL:
    print("ERROR: DATABASE_URL not set")
    sys.exit(1)

engine = create_engine(DATABASE_URL)

tables = [
    'permissions', 'roles', 'users', 'tenants', 'modules', 'ruoli_disponibili',
    'platform_menu_items', 'platform_widgets', 'scadenze', 'import_configurations',
    'user_roles', 'role_permissions', 'user_tenants', 'tenant_modules',
    'soggetti_ruoli', 'platform_user_dashboards', 'module_dependencies',
    'module_permissions', 'module_hooks', 'module_extensions', 'module_endpoints',
    'scadenza_destinatari', 'scadenza_log'
]

print(f"Rinominando tabelle core su {DATABASE_URL}...")
with engine.connect() as conn:
    print("Connesso...")
    for table in tables:
        new_name = f'core_{table}'
        try:
            query = text(f'ALTER TABLE public.{table} RENAME TO {new_name}')
            print(f"Eseguendo: {query}")
            conn.execute(query)
            conn.commit()
            print(f"  {table} -> {new_name}")
        except Exception as e:
            print(f"  SKIP {table}: {str(e)[:80]}")

print("Done!")
