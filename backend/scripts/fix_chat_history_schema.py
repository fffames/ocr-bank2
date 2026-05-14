#!/usr/bin/env python3
"""
Fix chat_history table schema for Railway
Changes context_receipts from INTEGER to TEXT to support JSON arrays
"""
import sys
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from app.database.connection import engine
from sqlalchemy import text, inspect

def migrate():
    """Fix chat_history table schema"""

    print("🔍 Checking chat_history schema...")

    with engine.connect() as conn:
        # Check current columns
        inspector = inspect(engine)
        columns = {col['name']: col for col in inspector.get_columns('chat_history')}

        print(f"  Current columns: {list(columns.keys())}")

        # Check if context_receipts exists and its type
        if 'context_receipts' in columns:
            current_type = str(columns['context_receipts']['type'])
            print(f"  context_receipts current type: {current_type}")

            # Check if it's the wrong type (INTEGER instead of TEXT)
            if 'INTEGER' in current_type.upper() or 'INT' in current_type.upper():
                print("  ⚠️  context_receipts is INTEGER - needs to be TEXT")

                # Step 1: Add new temporary column
                print("  → Adding temporary column context_receipts_new")
                conn.execute(text("ALTER TABLE chat_history ADD COLUMN context_receipts_new TEXT"))

                # Step 2: Copy data (convert existing integers to JSON arrays)
                print("  → Copying data to new column")
                conn.execute(text("""
                    UPDATE chat_history
                    SET context_receipts_new = CASE
                        WHEN context_receipts IS NOT NULL
                        THEN '[' || context_receipts || ']'
                        ELSE NULL
                    END
                """))

                # Step 3: Drop old column
                print("  → Dropping old context_receipts column")
                conn.execute(text("ALTER TABLE chat_history DROP COLUMN context_receipts"))

                # Step 4: Rename new column
                print("  → Renaming context_receipts_new to context_receipts")
                conn.execute(text("ALTER TABLE chat_history RENAME COLUMN context_receipts_new TO context_receipts"))

                conn.commit()
                print("✅ Schema migration completed successfully!")
            else:
                print("✅ context_receipts is already TEXT - no migration needed")
        else:
            print("  → Adding context_receipts column (TEXT type)")
            conn.execute(text("ALTER TABLE chat_history ADD COLUMN context_receipts TEXT"))
            conn.commit()
            print("✅ Column added successfully!")

    print("\n📊 Updated schema:")
    inspector = inspect(engine)
    columns = inspector.get_columns('chat_history')
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