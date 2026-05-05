#!/usr/bin/env python3
"""
Migration script to add transaction classification fields to receipts table
"""
import sys
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from app.database.connection import engine, get_db
from sqlalchemy import text, inspect

def migrate():
    """Add transaction_type, transaction_confidence, and classification_reason columns"""

    print("🔍 Checking current schema...")

    with engine.connect() as conn:
        # Check if columns already exist
        inspector = inspect(engine)
        columns = [col['name'] for col in inspector.get_columns('receipts')]

        new_columns = {
            'transaction_type': 'VARCHAR(20)',
            'transaction_confidence': 'VARCHAR(10)',
            'classification_reason': 'TEXT'
        }

        for col_name, col_type in new_columns.items():
            if col_name in columns:
                print(f"  ✓ Column '{col_name}' already exists")
            else:
                print(f"  → Adding column '{col_name}' ({col_type})")
                conn.execute(text(f"ALTER TABLE receipts ADD COLUMN {col_name} {col_type}"))

        conn.commit()

    print("\n✅ Migration completed successfully!")
    print("\n📊 Updated schema:")
    inspector = inspect(engine)
    columns = inspector.get_columns('receipts')
    for col in columns:
        if 'transaction' in col['name'].lower():
            print(f"  • {col['name']}: {col['type']}")

if __name__ == "__main__":
    try:
        migrate()
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        sys.exit(1)
