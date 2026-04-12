import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

import httpx
from app.main import app
import uvicorn
import threading
import time

def run_server():
    uvicorn.run(app, host='127.0.0.1', port=5000, log_level='error')

server_thread = threading.Thread(target=run_server, daemon=True)
server_thread.start()
time.sleep(3)

print("=" * 50)
print("SPRINT 5 - TESTS")
print("=" * 50)

with httpx.Client(base_url='http://127.0.0.1:5000') as client:
    login_resp = client.post('/api/v1/auth/login', 
        data={'username': 'admin', 'password': 'Admin@SIEM2024!'})
    token = login_resp.json()['access_token']
    headers = {'Authorization': f'Bearer {token}'}
    print('T01: Login OK')
    
    # Archive Status
    resp = client.get('/api/v1/lifecycle/status', headers=headers)
    status = "PASS" if resp.status_code == 200 else "FAIL"
    print(f'T02: Archive Status - {status}')
    if resp.status_code == 200:
        data = resp.json()
        print(f'   HOT records: {data["hot"]["records"]}')
    
    # Create Backup
    resp = client.post('/api/v1/lifecycle/backup/create', headers=headers)
    backup_status = "PASS" if resp.status_code in [200, 201] else "FAIL"
    print(f'T03: Create Backup - {backup_status}')
    if resp.status_code == 200:
        print(f'   Backup ID: {resp.json().get("backup_id")}')
    
    # List Backups
    resp = client.get('/api/v1/lifecycle/backups', headers=headers)
    print(f'T04: List Backups - {resp.status_code}')
    
    # List Lifecycle Logs
    resp = client.get('/api/v1/lifecycle/logs', headers=headers)
    print(f'T05: Lifecycle Logs - {resp.status_code}')
    if resp.status_code == 200:
        print(f'   Logs count: {resp.json().get("total")}')

print("\nSprint 5 tests completed!")