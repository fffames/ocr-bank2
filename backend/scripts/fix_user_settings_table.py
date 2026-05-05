#!/usr/bin/env python3
"""
Fix user_settings table column names
"""
import sys
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from app.database.connection import engine
from sqlalchemy import text

def migrate():
    """Fix column names in user_settings table"""

    print("🔍 Fixing user_settings table...")

    with engine.connect() as conn:
        # Rename column from name_variations to user_name_variations
        print("  → Renaming column 'name_variations' to 'user_name_variations'")
        conn.execute(text("""
            ALTER TABLE user_settings
            RENAME COLUMN name_variations TO user_name_variations
        """))

        conn.commit()

    print("\n✅ Migration completed successfully!")

if __name__ == "__main__":
    try:
        migrate()
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        sys.exit(1)
