#!/usr/bin/env python3
"""
Migration script to create user_settings table
"""
import sys
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from app.database.connection import engine
from sqlalchemy import text

def migrate():
    """Create user_settings table"""

    print("🔍 Creating user_settings table...")

    with engine.connect() as conn:
        # Check if table exists
        result = conn.execute(text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_name = 'user_settings'
            )
        """))
        exists = result.scalar()

        if exists:
            print("  ✓ Table 'user_settings' already exists")
        else:
            print("  → Creating table 'user_settings'")
            conn.execute(text("""
                CREATE TABLE user_settings (
                    id SERIAL PRIMARY KEY,
                    user_name VARCHAR(255),
                    name_variations TEXT DEFAULT '[]',
                    auto_classify BOOLEAN DEFAULT TRUE NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))

            # Create default settings
            conn.execute(text("""
                INSERT INTO user_settings (user_name, name_variations, auto_classify)
                VALUES ('', '[]', TRUE)
            """))

            conn.commit()

    print("\n✅ Migration completed successfully!")

if __name__ == "__main__":
    try:
        migrate()
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        sys.exit(1)
