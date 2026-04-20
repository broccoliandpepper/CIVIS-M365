#!/usr/bin/env python3
"""Test import backup endpoint."""

import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from fastapi.testclient import TestClient
from app.main import app

def test_import_backup():
    """Test l'import d'un backup .sbk existant."""
    print("\n=== TEST IMPORT BACKUP ===\n")
    
    client = TestClient(app)
    
    # Login
    username = os.getenv("SIEM_TEST_USERNAME", "admin")
    password = os.getenv("SIEM_TEST_PASSWORD", "Admin@SIEM2024!")
    
    print("0. Logging in...")
    login_resp = client.post(
        "/api/v1/auth/login",
        data={"username": username, "password": password},
    )
    
    if login_resp.status_code != 200:
        print(f"   ✗ Login failed: {login_resp.status_code}")
        print(f"   Response: {login_resp.json()}")
        return
    
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print(f"   ✓ Login OK")
    
    # 1. Créer un backup
    print("\n1. Creating backup...")
    response = client.post(
        "/api/v1/lifecycle/backup/create",
        headers=headers
    )
    if response.status_code != 200:
        print(f"   ✗ Status: {response.status_code}")
        print(f"   Response: {response.json()}")
        return
    
    backup_result = response.json()
    backup_id = backup_result.get("backup_id")
    print(f"   ✓ Backup créé: {backup_id}")
    print(f"   Size: {backup_result.get('size_bytes')} bytes")
    print(f"   Records: {backup_result.get('records')}")
    
    # 2. Localiser le fichier .sbk
    backup_dir = Path(__file__).parent.parent / "data" / "backups" / "archives"
    sbk_file = backup_dir / f"{backup_id}.sbk"
    
    if not sbk_file.exists():
        print(f"   ✗ Fichier .sbk non trouvé: {sbk_file}")
        return
    
    print(f"   ✓ Fichier .sbk trouvé: {sbk_file}")
    print(f"   Taille: {sbk_file.stat().st_size} bytes")
    
    # 3. Tester l'import
    print("\n2. Testing import endpoint...")
    import tempfile
    import shutil
    
    with tempfile.TemporaryDirectory(prefix="import_test_") as temp_dir:
        temp_sbk = Path(temp_dir) / sbk_file.name
        shutil.copy2(sbk_file, temp_sbk)
        print(f"   ✓ Fichier copié: {temp_sbk}")
        
        with open(temp_sbk, "rb") as f:
            files = {"file": (sbk_file.name, f, "application/octet-stream")}
            response = client.post(
                "/api/v1/lifecycle/import",
                files=files,
                headers=headers
            )
        
        print(f"   Status: {response.status_code}")
        import_result = response.json()
        
        if response.status_code == 200 and import_result.get("status") == "success":
            print(f"   ✓ Import réussi!")
            print(f"   - Backup ID: {import_result.get('backup_id')}")
            print(f"   - Records: {import_result.get('records')}")
            print(f"   - Manifest ID: {import_result.get('manifest_id')}")
            print(f"   - Message: {import_result.get('message')}")
        else:
            print(f"   ✗ Import échoué")
            print(f"   Response: {import_result}")
    
    # 4. Lister les backups pour vérifier l'import
    print("\n3. Listing backups...")
    response = client.get(
        "/api/v1/lifecycle/backups?limit=10",
        headers=headers
    )
    
    if response.status_code == 200:
        backups = response.json().get("backups", [])
        print(f"   Total backups: {len(backups)}")
        for backup in backups[:3]:
            status = backup.get('status', 'unknown')
            print(f"   - {backup.get('backup_id')} (status={status})")
    
    print("\n=== TEST COMPLETED ===\n")

if __name__ == "__main__":
    test_import_backup()

