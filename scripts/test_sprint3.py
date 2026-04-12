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
print("SPRINT 3 - TESTS")
print("=" * 50)

with httpx.Client(base_url='http://127.0.0.1:5000') as client:
    # Login
    login_resp = client.post('/api/v1/auth/login', 
        data={'username': 'admin', 'password': 'Admin@SIEM2024!'})
    token = login_resp.json()['access_token']
    headers = {'Authorization': f'Bearer {token}'}
    print('T01: Login OK')
    
    # Query SignIns with filters
    resp = client.get('/api/v1/query/signins?status=failure&page=1&page_size=10', headers=headers)
    print(f'T02: Query SignIns - {resp.status_code}')
    if resp.status_code == 200:
        data = resp.json()
        print(f'   Total: {data["total"]}, Page: {data["page"]}')
    
    # Query Risky Users
    resp = client.get('/api/v1/query/risky-users?page=1&page_size=10', headers=headers)
    print(f'T03: Query Risky Users - {resp.status_code}')
    
    # Query Incidents
    resp = client.get('/api/v1/query/incidents?page=1&page_size=10', headers=headers)
    print(f'T04: Query Incidents - {resp.status_code}')
    
    # Query Audit Logs
    resp = client.get('/api/v1/query/audit-logs?page=1&page_size=10', headers=headers)
    print(f'T05: Query Audit Logs - {resp.status_code}')
    
    # Get KPIs
    resp = client.get('/api/v1/query/kpis?days=30', headers=headers)
    print(f'T06: KPIs - {resp.status_code}')
    if resp.status_code == 200:
        data = resp.json()
        print(f'   SignIns: {data.get("total_signins")}, Risky: {data.get("total_risky_users")}')
    
    # Export CSV
    resp = client.get('/api/v1/export/signins/csv?status=failure', headers=headers)
    print(f'T07: Export CSV - {resp.status_code}')

print("\nSprint 3 tests completed!")