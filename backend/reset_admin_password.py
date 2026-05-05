#!/usr/bin/env python3
"""
Reset admin password (works with any email)
"""
import sys
import os

# Add backend directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database.connection import SessionLocal
from app.models.user import User
from app.services.auth_service import get_password_hash

def reset_admin_password():
    db = SessionLocal()

    # Find ANY admin user
    admin = db.query(User).filter(User.is_admin == True).first()

    if not admin:
        print("❌ No admin account found!")
        db.close()
        return

    print(f"🔧 Found Admin Account:")
    print(f"   Email: {admin.email}")
    print(f"   Name: {admin.name}")
    print(f"   Is Admin: {admin.is_admin}")
    print()

    # Reset password
    new_password = input("Enter new password (min 6 characters): ")
    if len(new_password) < 6:
        print("❌ Password must be at least 6 characters!")
        db.close()
        return

    admin.password_hash = get_password_hash(new_password)
    db.commit()
    db.close()

    print(f"\n✅ Password reset successfully!")
    print(f"📧 Login with:")
    print(f"   Email: {admin.email}")
    print(f"   Password: {new_password}")

if __name__ == "__main__":
    reset_admin_password()
