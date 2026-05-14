#!/usr/bin/env python3
"""
Migration script to make image_path nullable in receipts table.

Run this after deploying to update the database schema:
    python scripts/migrate_image_path_nullable.py
"""
import sys
import os

# Add the parent directory to the path so we can import from app
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database.connection import engine
from sqlalchemy import text


def migrate():
    """Make image_path column nullable."""
    try:
        with engine.connect() as conn:
            # Check if column is already nullable
            result = conn.execute(text("""
                SELECT is_nullable
                FROM information_schema.columns
                WHERE table_name = 'receipts'
                AND column_name = 'image_path'
            """)).fetchone()

            if result and result[0] == 'YES':
                print("✅ image_path is already nullable. No migration needed.")
                return

            print("Migrating: Making image_path nullable...")
            conn.execute(text("ALTER TABLE receipts ALTER COLUMN image_path DROP NOT NULL"))
            conn.commit()
            print("✅ Migration complete: image_path is now nullable")
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    migrate()
