#!/usr/bin/env python3
"""
Comprehensive migration script for Railway database
Adds all missing columns to receipts table
"""
import sys
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from app.database.connection import engine
from sqlalchemy import text, inspect

def migrate():
    """Add all missing columns to receipts table"""

    print("🔍 Checking current schema...")

    with engine.connect() as conn:
        # Check current columns
        inspector = inspect(engine)
        columns = [col['name'] for col in inspector.get_columns('receipts')]

        print(f"  Current columns: {len(columns)}")

        # Define all missing columns
        new_columns = {
            'user_id': 'INTEGER',
            'transaction_type': 'VARCHAR(20)',
            'transaction_confidence': 'VARCHAR(10)',
            'classification_reason': 'TEXT',
            'is_salary': 'BOOLEAN DEFAULT FALSE NOT NULL',
            'is_manual_income': 'BOOLEAN DEFAULT FALSE NOT NULL',
            'income_category': 'VARCHAR(100)',
            'detected_template': 'VARCHAR(100)',
            'ocr_engine': 'VARCHAR(50) DEFAULT \'template\''
        }

        added_count = 0
        for col_name, col_def in new_columns.items():
            if col_name in columns:
                print(f"  ✓ Column '{col_name}' already exists")
            else:
                print(f"  → Adding column '{col_name}' ({col_def})")
                try:
                    conn.execute(text(f"ALTER TABLE receipts ADD COLUMN {col_name} {col_def}"))
                    added_count += 1
                except Exception as e:
                    print(f"  ❌ Error adding '{col_name}': {e}")

        conn.commit()

    print(f"\n✅ Migration completed! Added {added_count} new columns.")
    print("\n📊 Updated schema:")
    inspector = inspect(engine)
    columns = inspector.get_columns('receipts')
    for col in columns:
        print(f"  • {col['name']}: {col['type']}")

if __name__ == "__main__":
    try:
        migrate()
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)