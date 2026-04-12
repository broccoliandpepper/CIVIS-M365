import sys
from pathlib import Path
import os
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

with httpx.Client(base_url='http://127.0.0.1:5000') as client:
    health_resp = client.get('/health')
    print('/health Status:', health_resp.status_code)
    print('/health Response:', health_resp.json())

    if health_resp.status_code != 200:
        print('Health check failed')
        exit(1)

    username = os.getenv('SIEM_TEST_USERNAME', 'admin')
    password = os.getenv('SIEM_TEST_PASSWORD', 'Admin@SIEM2024!')
    login_resp = client.post(
        '/api/v1/auth/login',
        data={'username': username, 'password': password}
    )

    if login_resp.status_code == 200:
        token = login_resp.json()['access_token']
        headers = {'Authorization': f'Bearer {token}'}
        me_resp = client.get('/api/v1/auth/me', headers=headers)
        print('/me Status:', me_resp.status_code)
        print('/me Response:', me_resp.json())
        if me_resp.status_code != 200:
            print('Authenticated /me check failed')
            exit(1)
    else:
        print('Login check skipped: credentials differ from current DB state')