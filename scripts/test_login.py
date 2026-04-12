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

with httpx.Client(base_url='http://127.0.0.1:5000') as client:
    response = client.post('/api/v1/auth/login', 
        data={'username': 'admin', 'password': 'Admin@SIEM2024!'})
    print('Status:', response.status_code)
    if response.status_code == 200:
        data = response.json()
        print('Login successful!')
        token = data.get('access_token', '')
        print('Token:', token[:50] + '...')
        print('User:', data.get('user'))
    else:
        print('Error:', response.text)