#!/usr/bin/env python3
"""
Script to change admin user password and/or name
"""
import sys
import os

# Add backend directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database.connection import SessionLocal
from app.models.user import User
from app.services.auth_service import get_password_hash

def change_admin_user():
    db = SessionLocal()

    # Get admin user
    admin = db.query(User).filter(User.email == "admin@ocrbank.local").first()

    if not admin:
        print("❌ Admin user not found!")
        db.close()
        return

    print(f"📧 Current Admin Details:")
    print(f"   Email: {admin.email}")
    print(f"   Name: {admin.name}")
    print(f"   Is Admin: {admin.is_admin}")
    print()

    # Ask what to change
    print("What would you like to change?")
    print("1. Password only")
    print("2. Name only")
    print("3. Both password and name")
    print("4. Email (requires DB update)")

    choice = input("\nEnter choice (1-4): ").strip()

    if choice == "1":
        # Change password only
        old_password = input("Current password: ")
        if old_password != "OCR-Bank-Admin-2026!":
            print("❌ Wrong current password!")
            db.close()
            return

        new_password = input("New password (min 6 characters): ")
        if len(new_password) < 6:
            print("❌ Password must be at least 6 characters!")
            db.close()
            return

        admin.password_hash = get_password_hash(new_password)
        db.commit()
        print("✅ Password changed successfully!")

    elif choice == "2":
        # Change name only
        new_name = input("New name: ")
        if not new_name.strip():
            print("❌ Name cannot be empty!")
            db.close()
            return

        admin.name = new_name.strip()
        db.commit()
        print(f"✅ Name changed to: {new_name}")

    elif choice == "3":
        # Change both
        old_password = input("Current password: ")
        if old_password != "OCR-Bank-Admin-2026!":
            print("❌ Wrong current password!")
            db.close()
            return

        new_password = input("New password (min 6 characters): ")
        if len(new_password) < 6:
            print("❌ Password must be at least 6 characters!")
            db.close()
            return

        new_name = input("New name: ")
        if not new_name.strip():
            print("❌ Name cannot be empty!")
            db.close()
            return

        admin.password_hash = get_password_hash(new_password)
        admin.name = new_name.strip()
        db.commit()
        print(f"✅ Password and name changed successfully!")
        print(f"   New name: {new_name}")

    elif choice == "4":
        # Change email
        new_email = input("New email: ")
        if not new_email.strip() or "@" not in new_email:
            print("❌ Invalid email!")
            db.close()
            return

        # Check if email already exists
        existing = db.query(User).filter(User.email == new_email).first()
        if existing:
            print("❌ Email already exists!")
            db.close()
            return

        admin.email = new_email.strip()
        db.commit()
        print(f"✅ Email changed to: {new_email}")

    else:
        print("❌ Invalid choice!")
        db.close()
        return

    db.close()
    print("\n🎉 Changes saved! You'll need to login again with new credentials.")

if __name__ == "__main__":
    change_admin_user()