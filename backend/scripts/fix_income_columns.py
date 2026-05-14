#!/usr/bin/env python3
"""
Quick fix: Add missing income-related columns to receipts table
"""
import sys
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from app.database.connection import engine
from sqlalchemy import text, inspect

def fix_income_columns():
    """Add missing columns for income functionality"""

    print("🔍 Checking for income-related columns...")

    with engine.connect() as conn:
        # Check current columns
        inspector = inspect(engine)
        columns = [col['name'] for col in inspector.get_columns('receipts')]

        # Required columns for income functionality
        income_columns = {
            'transaction_confidence': 'VARCHAR(10)',
            'classification_reason': 'TEXT',
            'is_salary': 'BOOLEAN DEFAULT FALSE NOT NULL',
            'is_manual_income': 'BOOLEAN DEFAULT FALSE NOT NULL',
            'income_category': 'VARCHAR(100)',
            'detected_template': 'VARCHAR(100)'
        }

        fixed_count = 0
        for col_name, col_def in income_columns.items():
            if col_name in columns:
                print(f"  ✓ Column '{col_name}' exists")
            else:
                print(f"  → Adding column '{col_name}'...")
                try:
                    conn.execute(text(f"ALTER TABLE receipts ADD COLUMN {col_name} {col_def}"))
                    fixed_count += 1
                    print(f"    ✅ Added '{col_name}'")
                except Exception as e:
                    print(f"    ❌ Error: {e}")

        conn.commit()

    print(f"\n✅ Fixed {fixed_count} columns for income functionality!")

    if fixed_count > 0:
        print("\n📊 Updated schema:")
        inspector = inspect(engine)
        columns = inspector.get_columns('receipts')
        for col in columns:
            if col['name'] in income_columns.keys():
                print(f"  • {col['name']}: {col['type']}")

if __name__ == "__main__":
    try:
        fix_income_columns()
    except Exception as e:
        print(f"\n❌ Fix failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)