import os
import sys
from pathlib import Path

from fastapi.testclient import TestClient


BACKEND_DIR = Path(__file__).parent.parent / "backend"
os.chdir(BACKEND_DIR)
sys.path.insert(0, str(BACKEND_DIR))

from app.main import app  # noqa: E402


def fail(message: str):
    print(f"FAIL: {message}")
    raise SystemExit(1)


def main():
    username = os.getenv("SIEM_TEST_USERNAME", "admin")
    password = os.getenv("SIEM_TEST_PASSWORD", "Admin@SIEM2024!")

    with TestClient(app) as client:
        login = client.post(
            "/api/v1/auth/login",
            data={"username": username, "password": password},
        )
        if login.status_code != 200:
            fail(f"login failed: {login.status_code} {login.text}")

        token = login.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        create = client.post("/api/v1/lifecycle/backup/create", headers=headers)
        if create.status_code != 200 or create.json().get("status") != "success":
            fail(f"backup create failed: {create.status_code} {create.text}")

        backup_id = create.json()["backup_id"]
        print(f"CREATE_BACKUP OK: {backup_id}")

        inspect = client.get(f"/api/v1/lifecycle/backup/{backup_id}/contents", headers=headers)
        if inspect.status_code != 200 or inspect.json().get("status") != "success":
            fail(f"inspect failed: {inspect.status_code} {inspect.text}")
        print("INSPECT OK")

        verify = client.post(f"/api/v1/lifecycle/backup/{backup_id}/verify", headers=headers)
        if verify.status_code != 200 or verify.json().get("status") != "verified":
            fail(f"verify failed: {verify.status_code} {verify.text}")
        print("VERIFY OK")

        dry_restore = client.post(f"/api/v1/lifecycle/backup/{backup_id}/restore", headers=headers)
        if dry_restore.status_code != 200 or dry_restore.json().get("status") != "success":
            fail(f"dry restore failed: {dry_restore.status_code} {dry_restore.text}")
        print("DRY_RESTORE OK")

        active_restore = client.post(
            f"/api/v1/lifecycle/backup/{backup_id}/restore/activate",
            headers=headers,
            json={"confirm_phrase": f"RESTORE {backup_id}"},
        )
        if active_restore.status_code != 200 or active_restore.json().get("status") != "success":
            fail(f"active restore failed: {active_restore.status_code} {active_restore.text}")

        rollback_id = active_restore.json()["rollback_id"]
        print(f"ACTIVE_RESTORE OK: {rollback_id}")

        rollback = client.post(
            f"/api/v1/lifecycle/rollback/{rollback_id}",
            headers=headers,
            json={"confirm_phrase": f"ROLLBACK {rollback_id}"},
        )
        if rollback.status_code != 200 or rollback.json().get("status") != "success":
            fail(f"rollback failed: {rollback.status_code} {rollback.text}")
        print("ROLLBACK OK")

        print("SMOKE TEST COMPLETED")


if __name__ == "__main__":
    main()
