#!/usr/bin/env python3
"""
Script d'initialisation des bases de données
"""

import sys
from pathlib import Path
import os

# Resolve project paths once and keep the process rooted at the repository level.
PROJECT_ROOT = Path(__file__).parent.parent.resolve()
BACKEND_ROOT = PROJECT_ROOT / "backend"

os.chdir(PROJECT_ROOT)

sys.path.insert(0, str(BACKEND_ROOT))
sys.stdout.flush()
sys.stderr.flush()

# Import all models to avoid relationship issues
from app.database import init_all_databases, SessionLocal_config
from app.models import auth, audit, settings, signins, risky_users, incidents, truth_list, ingestion_logs, audit_logs_m365, archive_manifest, lifecycle_logs, new_user_review
from app.models.auth import User


def create_admin_user():
    db = SessionLocal_config()
    
    try:
        admin = db.query(User).filter(User.username == "admin").first()
        
        if admin:
            print("Admin user already exists")
            return
        
        admin = User(
            username="admin",
            email="admin@local.siem",
            role="admin",
            is_active=True
        )
        admin.set_password("Admin@SIEM2024!")
        
        db.add(admin)
        db.commit()
        
        print("Admin user created:")
        print("  Username: admin")
        print("  Password: Admin@SIEM2024!  CHANGE THIS IMMEDIATELY!")
        
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