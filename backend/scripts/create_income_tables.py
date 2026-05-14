#!/usr/bin/env python3
"""
Create missing income-related tables in Railway database
"""
import sys
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from app.database.connection import engine
from sqlalchemy import text

def create_income_tables():
    """Create missing income-related tables"""

    print("🔍 Creating income-related tables...")

    with engine.connect() as conn:
        # Create income_categories table
        print("\n📁 Creating income_categories table...")
        try:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS income_categories (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(100) UNIQUE NOT NULL,
                    color VARCHAR(20),
                    icon VARCHAR(50),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            print("  ✅ income_categories table created")
        except Exception as e:
            print(f"  ⚠️  income_categories table error: {e}")

        # Insert default income categories if table is empty
        try:
            result = conn.execute(text("SELECT COUNT(*) FROM income_categories"))
            count = result.scalar()

            if count == 0:
                print("  📝 Inserting default income categories...")
                default_categories = [
                    ('Salary', '#10B981', 'briefcase'),
                    ('Business', '#3B82F6', 'briefcase'),
                    ('Investment', '#8B5CF6', 'trending-up'),
                    ('Gift', '#EC4899', 'gift'),
                    ('Refund', '#F59E0B', 'refresh-ccw'),
                    ('Other Income', '#6B7280', 'dollar-sign')
                ]

                for name, color, icon in default_categories:
                    conn.execute(text("""
                        INSERT INTO income_categories (name, color, icon)
                        VALUES (:name, :color, :icon)
                    """), {"name": name, "color": color, "icon": icon})

                print(f"  ✅ Inserted {len(default_categories)} default categories")
            else:
                print(f"  ✓ income_categories already has {count} categories")
        except Exception as e:
            print(f"  ⚠️  Could not insert default categories: {e}")

        conn.commit()

    print("\n✅ Income tables created successfully!")

if __name__ == "__main__":
    try:
        create_income_tables()
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)