#!/usr/bin/env python3
"""
Update admin user password to work with bcrypt 72-byte limit.
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy.orm import Session
from app.database.connection import engine
from app.models.user import User
from app.services.auth_service import get_password_hash

def update_admin_password():
    """Update admin user password."""
    db = Session(engine)

    try:
        # Get admin user
        admin_user = db.query(User).filter(User.email == "admin@ocrbank.local").first()
        if not admin_user:
            print("❌ Admin user not found")
            return

        # Update password to shorter version
        new_password = "Admin@2026"
        admin_user.password_hash = get_password_hash(new_password)
        db.commit()

        print("✅ Admin password updated successfully")
        print(f"   Email: {admin_user.email}")
        print(f"   New Password: {new_password}")
        print(f"   Name: {admin_user.name}")

    except Exception as e:
        print(f"❌ Error updating admin password: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    print("🔄 Updating admin password...")
    update_admin_password()
    print("✅ Password update complete!")