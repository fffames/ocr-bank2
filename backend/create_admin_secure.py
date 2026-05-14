#!/usr/bin/env python3
"""
Create admin user in production database using environment variables.
Usage:
  export ADMIN_EMAIL="admin@example.com"
  export ADMIN_PASSWORD="secure_password_here"
  DATABASE_URL="postgresql://..." python create_admin_secure.py
"""
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy.orm import Session
from app.database.connection import engine
from app.models.user import User
from app.services.auth_service import get_password_hash

def create_admin_user():
    """Create admin user from environment variables."""
    admin_email = os.getenv("ADMIN_EMAIL", "admin@ocrbank.local")
    admin_password = os.getenv("ADMIN_PASSWORD")
    admin_name = os.getenv("ADMIN_NAME", "Admin")

    if not admin_password:
        raise ValueError("ADMIN_PASSWORD environment variable is required")

    db = Session(engine)

    try:
        # Check if admin user already exists
        existing_admin = db.query(User).filter(User.email == admin_email).first()
        if existing_admin:
            print(f"✅ Admin user already exists: {admin_email}")
            return

        # Create admin user
        admin_user = User(
            email=admin_email,
            name=admin_name,
            password_hash=get_password_hash(admin_password),
            is_active=True,
            is_admin=True
        )

        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)

        print("✅ Admin user created successfully")
        print(f"   Email: {admin_user.email}")
        print(f"   Name: {admin_user.name}")
        print("⚠️  IMPORTANT: Change password immediately after first login!")

    except Exception as e:
        print(f"❌ Error creating admin user: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    print("🚀 Creating admin user from environment variables...")
    create_admin_user()
    print("✅ Admin setup complete!")