import requests
import json

BASE = "http://127.0.0.1:5000/api/v1"

# Login
r = requests.post(f"{BASE}/auth/login", json={"username": "admin", "password": "AdminPassword123!"})
if r.status_code != 200:
    print(f"Login failed: {r.text}")
    exit(1)
    
token = r.json()["access_token"]
print(f"Token obtained: {token[:20]}...")

# Upload audit logs
headers = {"Authorization": f"Bearer {token}"}
with open("sample_data/AuditLogs_2026-04-11.json", "rb") as f:
    files = {"file": ("AuditLogs_2026-04-11.json", f, "application/json")}
    r = requests.post(f"{BASE}/ingest/upload/audit-logs", files=files, headers=headers)
    
print(f"Response: {r.status_code}")
print(f"Body: {r.text}")