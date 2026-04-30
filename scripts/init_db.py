#!/usr/bin/env python3
"""
Script d'initialisation des bases de données
"""

import os
import secrets
import string
import sys
from pathlib import Path

from dotenv import load_dotenv

# Resolve project paths once and keep the process rooted at the repository level.
PROJECT_ROOT = Path(__file__).parent.parent.resolve()
BACKEND_ROOT = PROJECT_ROOT / "backend"

os.chdir(PROJECT_ROOT)

load_dotenv(BACKEND_ROOT / ".env")

sys.path.insert(0, str(BACKEND_ROOT))
sys.stdout.flush()
sys.stderr.flush()

# Import all models to avoid relationship issues
from app.database import init_all_databases, SessionLocal_config
from app.models import auth, audit, settings, signins, risky_users, incidents, truth_list, ingestion_logs, audit_logs_m365, archive_manifest, lifecycle_logs, new_user_review
from app.models.auth import User


SPECIAL_CHARS = "!@#$%^*_+-="


def generate_initial_password(length: int = 20) -> str:
    alphabet = string.ascii_letters + string.digits + SPECIAL_CHARS
    while True:
        password = "".join(secrets.choice(alphabet) for _ in range(length))
        if (
            any(char.islower() for char in password)
            and any(char.isupper() for char in password)
            and any(char.isdigit() for char in password)
            and any(char in SPECIAL_CHARS for char in password)
        ):
            return password


def create_admin_user():
    db = SessionLocal_config()

    try:
        admin = db.query(User).filter(User.username == "admin").first()

        if admin:
            print("Admin user already exists")
            return

        initial_password = os.getenv("SIEM_INITIAL_ADMIN_PASSWORD") or os.getenv("INITIAL_ADMIN_PASSWORD")
        generated_password = False
        if not initial_password:
            initial_password = generate_initial_password()
            generated_password = True

        admin = User(
            username="admin",
            email="admin@local.siem",
            role="admin",
            is_active=True
        )
        admin.set_password(initial_password)

        db.add(admin)
        db.commit()

        print("Admin user created:")
        print("  Username: admin")
        if generated_password:
            print(f"  Temporary password: {initial_password}")
            print("  This password was generated because INITIAL_ADMIN_PASSWORD was not set.")
        else:
            print("  Password source: INITIAL_ADMIN_PASSWORD from backend/.env or process environment")

    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
        raise
    finally:
        db.close()


def main():
    print("=" * 50)
    print("SIEM M365 - Database Initialization")
    print("=" * 50)
    
    env_path = BACKEND_ROOT / ".env"
    if not env_path.exists():
        print(".env file not found!")
        sys.exit(1)
    
    print("\nInitializing databases...")
    init_all_databases()
    
    print("\nCreating admin user...")
    create_admin_user()
    
    print("\n" + "=" * 50)
    print("Initialization complete!")
    print("=" * 50)


if __name__ == "__main__":
    main()