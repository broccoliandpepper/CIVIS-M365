#!/usr/bin/env python3
"""Script pour changer le mot de passe admin"""

import sys
import os
from pathlib import Path

os.chdir(Path(__file__).parent.parent / "backend")
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from app.database import SessionLocal_config
from app.models.auth import User

def change_password(new_password):
    if len(new_password) < 12:
        print("Le mot de passe doit faire au moins 12 caracteres!")
        print("Example: MonNouveauMotPasse2024!")
        return
    
    if not any(c.isupper() for c in new_password):
        print("Le mot de passe doit contenir au moins une majuscule!")
        return
    
    if not any(c.isdigit() for c in new_password):
        print("Le mot de passe doit contenir au moins un chiffre!")
        return
    
    db = SessionLocal_config()
    
    try:
        admin = db.query(User).filter(User.username == "admin").first()
        if not admin:
            print("Utilisateur admin non trouve!")
            return
        
        admin.set_password(new_password)
        db.commit()
        print(f"\nMot de passe change avec succes!")
        print(f"Nouveau mot de passe: {new_password}")
        print(f"IMPORTANT: Notez-le quelque part!")
        
    except Exception as e:
        db.rollback()
        print(f"Erreur: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    print("=" * 50)
    print("CHANGEMENT MOT DE PASSE ADMIN")
    print("=" * 50)
    
    if len(sys.argv) < 2:
        print("\nUsage: python change_password.py 'NouveauMotDePasse'")
        print("\nExample:")
        print("  python change_password.py 'MonNouveauMotPasse2024!'")
    else:
        change_password(sys.argv[1])