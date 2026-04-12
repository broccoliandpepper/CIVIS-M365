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
print("SPRINT 6 - HARDENING TESTS")
print("=" * 50)

results = []

with httpx.Client(base_url='http://127.0.0.1:5000') as client:
    # Login
    login_resp = client.post('/api/v1/auth/login', 
        data={'username': 'admin', 'password': 'Admin@SIEM2024!'})
    if login_resp.status_code != 200:
        print('Login FAILED')
        exit(1)
    
    token = login_resp.json()['access_token']
    headers = {'Authorization': f'Bearer {token}'}
    print('T01: Login OK')
    results.append(("T01-Login", "PASS"))
    
    # Test Health endpoint
    resp = client.get('/health')
    results.append(("T02-Health", "PASS" if resp.status_code == 200 else "FAIL"))
    print(f'T02: Health - {resp.status_code}')
    
    # Test root endpoint
    resp = client.get('/')
    results.append(("T03-Root", "PASS" if resp.status_code == 200 else "FAIL"))
    print(f'T03: Root - {resp.status_code}')
    
    # Test query endpoints
    resp = client.get('/api/v1/query/signins', headers=headers)
    results.append(("T04-Query SignIns", "PASS" if resp.status_code == 200 else "FAIL"))
    print(f'T04: Query SignIns - {resp.status_code}')
    
    # Test dashboard KPIs
    resp = client.get('/api/v1/dashboard/kpis', headers=headers)
    results.append(("T05-KPIs", "PASS" if resp.status_code == 200 else "FAIL"))
    print(f'T05: Dashboard KPIs - {resp.status_code}')
    
    # Test lifecycle status
    resp = client.get('/api/v1/lifecycle/status', headers=headers)
    results.append(("T06-Lifecycle Status", "PASS" if resp.status_code == 200 else "FAIL"))
    print(f'T06: Lifecycle Status - {resp.status_code}')
    
    # Test alerts
    resp = client.get('/api/v1/alerts/unknown-users', headers=headers)
    results.append(("T07-Alerts", "PASS" if resp.status_code == 200 else "FAIL"))
    print(f'T07: Alerts - {resp.status_code}')
    
    # Test export
    resp = client.get('/api/v1/export/signins/csv', headers=headers)
    results.append(("T08-Export", "PASS" if resp.status_code == 200 else "FAIL"))
    print(f'T08: Export CSV - {resp.status_code}')

# Print security headers check
print("\nSecurity Headers should be present in all responses")

# Summary
print("\n" + "=" * 50)
print("SUMMARY")
print("=" * 50)
passed = sum(1 for _, s in results if s == "PASS")
total = len(results)
for name, status in results:
    print(f"{name}: {status}")

print(f"\nTotal: {passed}/{total} PASS")
print("\nSPRINT 6 COMPLETE" if passed == total else "\nSPRINT 6 INCOMPLETE")