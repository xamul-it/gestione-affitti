"""
Script per ricreare tutte le tabelle del database.
ATTENZIONE: Questo script elimina TUTTI i dati!
"""
from app.core.database import engine, Base
from app.modules.affitti_lungo.models import *

print("🗑️  Dropping all tables...")
Base.metadata.drop_all(bind=engine)
print("✅ All tables dropped!")

print("🏗️  Creating all tables with new schema...")
Base.metadata.create_all(bind=engine)
print("✅ All tables created successfully!")

print("\n📋 Tables created:")
from sqlalchemy import inspect
inspector = inspect(engine)
for table_name in inspector.get_table_names():
    print(f"  - {table_name}")

print("\n✨ Database recreated successfully!")
