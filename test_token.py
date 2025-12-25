import requests

r = requests.post('http://localhost:8000/token', json={'roomName':'test-room','participantName':'alice'})
print(f'Status: {r.status_code}')
if r.status_code == 200:
    token = r.json().get('token')
    print(f'Token (first 100 chars): {token[:100]}...')
else:
    print(f'Error: {r.json()}')
