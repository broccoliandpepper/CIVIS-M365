import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

import json
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

print("=" * 60)
print("SPRINT 3 - TESTS QA")
print("=" * 60)

results = []

with httpx.Client(base_url='http://127.0.0.1:5000') as client:
    # Login
    login_resp = client.post('/api/v1/auth/login', 
        data={'username': 'admin', 'password': 'Admin@SIEM2024!'})
    token = login_resp.json()['access_token']
    headers = {'Authorization': f'Bearer {token}'}
    print('T01: Login OK')
    results.append(("T01-Login", "PASS"))
    
    # Test: Query SignIns avec pagination
    resp = client.get('/api/v1/query/signins?page=1&page_size=10', headers=headers)
    t2 = "PASS" if resp.status_code == 200 and "items" in resp.json() else "FAIL"
    print(f'T02: Query SignIns paginated - {t2} ({resp.status_code})')
    results.append(("T02-Query SignIns pagination", t2))
    
    # Test: Query SignIns avec filtres
    resp = client.get('/api/v1/query/signins?status=failure&location_country=France', headers=headers)
    t3 = "PASS" if resp.status_code == 200 else "FAIL"
    print(f'T03: Query SignIns filters - {t3}')
    results.append(("T03-Query SignIns filters", t3))
    
    # Test: Query Risky Users
    resp = client.get('/api/v1/query/risky-users?page=1&page_size=10', headers=headers)
    t4 = "PASS" if resp.status_code == 200 else "FAIL"
    print(f'T04: Query Risky Users - {t4}')
    results.append(("T04-Query Risky Users", t4))
    
    # Test: Query Risky Users avec risk_level
    resp = client.get('/api/v1/query/risky-users?risk_level=high', headers=headers)
    t5 = "PASS" if resp.status_code == 200 else "FAIL"
    print(f'T05: Query Risky Users level - {t5}')
    results.append(("T05-Query risk level filter", t5))
    
    # Test: Query Incidents
    resp = client.get('/api/v1/query/incidents?page=1&page_size=10', headers=headers)
    t6 = "PASS" if resp.status_code == 200 else "FAIL"
    print(f'T06: Query Incidents - {t6}')
    results.append(("T06-Query Incidents", t6))
    
    # Test: Query Incidents severity filter
    resp = client.get('/api/v1/query/incidents?severity=high', headers=headers)
    t7 = "PASS" if resp.status_code == 200 else "FAIL"
    print(f'T07: Query Incidents severity - {t7}')
    results.append(("T07-Query severity filter", t7))
    
    # Test: Query Audit Logs
    resp = client.get('/api/v1/query/audit-logs?page=1&page_size=10', headers=headers)
    t8 = "PASS" if resp.status_code == 200 else "FAIL"
    print(f'T08: Query Audit Logs - {t8}')
    results.append(("T08-Query Audit Logs", t8))
    
    # Test: Query Audit Logs critical
    resp = client.get('/api/v1/query/audit-logs?is_critical=true', headers=headers)
    t9 = "PASS" if resp.status_code == 200 else "FAIL"
    print(f'T09: Query critical operations - {t9}')
    results.append(("T09-Query critical filter", t9))
    
    # Test: KPIs
    resp = client.get('/api/v1/query/kpis?days=30', headers=headers)
    kpis = resp.json() if resp.status_code == 200 else {}
    t10 = "PASS" if "total_signins" in kpis else "FAIL"
    print(f'T10: KPIs dashboard - {t10}')
    print(f'   SignIns: {kpis.get("total_signins")}, Failed: {kpis.get("failed_signins")}')
    results.append(("T10-KPIs dashboard", t10))
    
    # Test: Export SignIns CSV
    resp = client.get('/api/v1/export/signins/csv', headers=headers)
    t11 = "PASS" if resp.status_code == 200 else "FAIL"
    print(f'T11: Export SignIns CSV - {t11}')
    results.append(("T11-Export SignIns CSV", t11))
    
    # Test: Export Risky Users CSV
    resp = client.get('/api/v1/export/risky-users/csv', headers=headers)
    t12 = "PASS" if resp.status_code == 200 else "FAIL"
    print(f'T12: Export Risky Users CSV - {t12}')
    results.append(("T12-Export Risky Users CSV", t12))
    
    # Test: Export Incidents CSV
    resp = client.get('/api/v1/export/incidents/csv', headers=headers)
    t13 = "PASS" if resp.status_code == 200 else "FAIL"
    print(f'T13: Export Incidents CSV - {t13}')
    results.append(("T13-Export Incidents CSV", t13))
    
    # Test: Pagination next/previous
    resp = client.get('/api/v1/query/signins?page=2&page_size=5', headers=headers)
    data = resp.json() if resp.status_code == 200 else {}
    t14 = "PASS" if data.get("has_next") == False or data.get("has_next") == True else "FAIL"
    print(f'T14: Pagination has_next - {t14}')
    results.append(("T14-Pagination next/prev", t14))

# Résumé
print("\n" + "=" * 60)
print("RÉSUMÉ")
print("=" * 60)
passed = sum(1 for _, s in results if s == "PASS")
total = len(results)
for name, status in results:
    print(f"{name}: {status}")
print(f"\nTotal: {passed}/{total} PASS")
print("\nSPRINT 3 - ACCEPTÉ" if passed >= total * 0.8 else "\nSPRINT 3 - REFUSE")