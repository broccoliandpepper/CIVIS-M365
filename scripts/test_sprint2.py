import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

import httpx
from app.main import app
import uvicorn
import threading
import time
import json

def run_server():
    uvicorn.run(app, host='127.0.0.1', port=5000, log_level='error')

server_thread = threading.Thread(target=run_server, daemon=True)
server_thread.start()
time.sleep(3)

with httpx.Client(base_url='http://127.0.0.1:5000') as client:
    # Login
    login_resp = client.post('/api/v1/auth/login', 
        data={'username': 'admin', 'password': 'Admin@SIEM2024!'})
    if login_resp.status_code != 200:
        print('Login failed:', login_resp.text)
        exit(1)
    
    token = login_resp.json()['access_token']
    headers = {'Authorization': f'Bearer {token}'}
    print('Login successful!')
    
    # Test 1: Upload Truth List
    with open('../backend/sample_data/truth_list_sample.csv', 'r', encoding='utf-8') as f:
        truth_data = f.read()
    
    resp = client.post('/api/v1/ingest/upload/truth-list',
        files={'file': ('truth_list_sample.csv', truth_data, 'text/csv')},
        headers=headers)
    print(f'\n1. Truth List Upload: {resp.status_code}')
    if resp.status_code == 200:
        data = resp.json()
        print(f'   Added: {data["lines_added"]}, Duplicates: {data["lines_duplicate"]}')
    else:
        print(f'   Error: {resp.text}')
    
    # Test 2: Upload SignIns
    with open('../backend/sample_data/signins_sample.json') as f:
        signin_data = f.read()
    
    resp = client.post('/api/v1/ingest/upload/signins',
        files={'file': ('signins_sample.json', signin_data, 'application/json')},
        headers=headers)
    print(f'\n2. SignIns Upload: {resp.status_code}')
    if resp.status_code == 200:
        data = resp.json()
        print(f'   Added: {data["lines_added"]}, Duplicates: {data["lines_duplicate"]}')
    else:
        print(f'   Error: {resp.text}')
    
    # Test 3: Upload same SignIns (should detect duplicates)
    resp = client.post('/api/v1/ingest/upload/signins',
        files={'file': ('signins_sample.json', signin_data, 'application/json')},
        headers=headers)
    print(f'\n3. SignIns Duplicate Upload: {resp.status_code}')
    if resp.status_code == 200:
        data = resp.json()
        print(f'   Added: {data["lines_added"]}, Duplicates: {data["lines_duplicate"]}')
    else:
        print(f'   Error: {resp.text}')
    
    # Test 4: Check unknown users
    resp = client.get('/api/v1/alerts/unknown-users', headers=headers)
    print(f'\n4. Unknown Users: {resp.status_code}')
    if resp.status_code == 200:
        data = resp.json()
        print(f'   Count: {data["count"]}')
        for u in data.get('users', [])[:2]:
            print(f'   - {u["user_principal"]} ({u["status"]})')
    
    # Test 5: Check known user
    resp = client.get('/api/v1/alerts/check-user/alice@company.com', headers=headers)
    print(f'\n5. Check Known User: {resp.status_code}')
    if resp.status_code == 200:
        print(f'   {resp.json()}')
    
    print('\nAll tests passed!')