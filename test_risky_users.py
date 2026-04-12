#!/usr/bin/env python
"""Test script for Risky Users ingestion"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

import httpx
from app.main import app
import uvicorn
import threading
import time

def run_server():
    uvicorn.run(app, host='127.0.0.1', port=5000, log_level='error')

# Start server in background
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
    
    print("✓ Login successful")
    
    # Upload Risky Users
    sample_file = Path(__file__).parent / 'backend' / 'sample_data' / 'RiskyUsers.json'
    
    if not sample_file.exists():
        print(f"✗ Sample file not found: {sample_file}")
        exit(1)
    
    print(f"Uploading {sample_file}...")
    
    with open(sample_file, 'rb') as f:
        files = {'file': ('RiskyUsers.json', f, 'application/json')}
        upload_resp = client.post('/api/v1/upload/risky-users', 
            headers=headers, files=files)
    
    print(f"Upload Status: {upload_resp.status_code}")
    print(f"Upload Response: {upload_resp.json()}")
    
    if upload_resp.status_code == 200:
        result = upload_resp.json()
        print(f"✓ Upload successful!")
        print(f"  - Added: {result.get('lines_added')}")
        print(f"  - Duplicates: {result.get('lines_duplicate')}")
        print(f"  - Errors: {result.get('lines_error')}")
        
        # Try to query the data
        time.sleep(1)
        query_resp = client.get('/api/v1/query/risky-users?page=1&page_size=10', headers=headers)
        print(f"\nQuery Status: {query_resp.status_code}")
        if query_resp.status_code == 200:
            data = query_resp.json()
            print(f"✓ Query successful!")
            print(f"  - Total records: {data.get('total')}")
            print(f"  - Page: {data.get('page')}/{data.get('total_pages')}")
            if data.get('items'):
                item = data['items'][0]
                print(f"  - First record fields: {list(item.keys())}")
        else:
            print(f"✗ Query failed: {query_resp.text}")
    else:
        print(f"✗ Upload failed")
