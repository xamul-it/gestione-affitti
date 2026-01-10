#!/usr/bin/env python3
"""
Script to re-register widgets with updated module_id field
"""
import asyncio
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(__file__))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal, engine
from app.core.platform.models.dashboard import Widget

# Import module widgets
from modules.anagrafica_italiana import WIDGETS as ANAGRAFICA_WIDGETS
from modules.immobili import WIDGETS as IMMOBILI_WIDGETS

async def reregister_widgets():
    """Re-register all widgets with updated module_id"""
    db = SessionLocal()

    try:
        print("\n🔄 Re-registering widgets with module_id field...\n")

        # Combine all widgets
        all_widgets = []
        all_widgets.extend([{**w, "module_id": "anagrafica_italiana"} for w in ANAGRAFICA_WIDGETS])
        all_widgets.extend([{**w, "module_id": "immobili"} for w in IMMOBILI_WIDGETS])

        for widget_data in all_widgets:
            widget_id = widget_data["id"]
            module_id = widget_data.get("module_id")

            # Check if widget exists
            existing = db.query(Widget).filter(
                Widget.id == widget_id
            ).first()

            if existing:
                # Update existing widget
                existing.module_id = module_id
                existing.title = widget_data["title"]
                existing.component = widget_data["component"]
                existing.description = widget_data.get("description")
                existing.default_width = widget_data.get("default_width", 6)
                existing.default_height = widget_data.get("default_height", 4)
                existing.category = widget_data.get("category")
                existing.required_permission = widget_data.get("required_permission")
                print(f"  ✅ Updated: {widget_id} → module_id={module_id}")
            else:
                # Create new widget
                new_widget = Widget(
                    id=widget_id,
                    module_id=module_id,
                    title=widget_data["title"],
                    component=widget_data["component"],
                    description=widget_data.get("description"),
                    default_width=widget_data.get("default_width", 6),
                    default_height=widget_data.get("default_height", 4),
                    category=widget_data.get("category"),
                    required_permission=widget_data.get("required_permission"),
                    enabled=True
                )
                db.add(new_widget)
                print(f"  ✨ Created: {widget_id} → module_id={module_id}")

        db.commit()
        print(f"\n✅ Successfully re-registered {len(all_widgets)} widgets!\n")

    except Exception as e:
        print(f"\n❌ Error: {e}\n")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(reregister_widgets())
