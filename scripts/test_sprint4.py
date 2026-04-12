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
print("SPRINT 4 - TESTS")
print("=" * 50)

with httpx.Client(base_url='http://127.0.0.1:5000') as client:
    login_resp = client.post('/api/v1/auth/login', 
        data={'username': 'admin', 'password': 'Admin@SIEM2024!'})
    token = login_resp.json()['access_token']
    headers = {'Authorization': f'Bearer {token}'}
    print('T01: Login OK')
    
    # KPIs
    resp = client.get('/api/v1/dashboard/kpis?days=30', headers=headers)
    kpis = resp.json()
    t2 = "PASS" if resp.status_code == 200 and "kpis" in kpis else "FAIL"
    print(f'T02: KPIs - {t2}')
    if resp.status_code == 200:
        print(f'   SignIns: {kpis["kpis"]["total_connexions"]["value"]}')
    
    # Trends
    resp = client.get('/api/v1/dashboard/trends?days=30', headers=headers)
    t3 = "PASS" if resp.status_code == 200 else "FAIL"
    print(f'T03: Trends - {t3}')
    
    # Security Summary
    resp = client.get('/api/v1/dashboard/security-summary', headers=headers)
    t4 = "PASS" if resp.status_code == 200 else "FAIL"
    print(f'T04: Security Summary - {t4}')
    if resp.status_code == 200:
        print(f'   Score: {resp.json()["score"]}')
    
    # Director Dashboard
    resp = client.get('/api/v1/dashboard/director?days=30', headers=headers)
    t5 = "PASS" if resp.status_code == 200 else "FAIL"
    print(f'T05: Director Dashboard - {t5}')
    
    # PDF Export
    resp = client.get('/api/v1/dashboard/director-pdf?days=30', headers=headers)
    t6 = "PASS" if resp.status_code == 200 else "FAIL"
    print(f'T06: PDF Export - {t6}')

print("\nSprint 4 tests completed!")