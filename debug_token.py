import jwt
import requests

# Get token from backend
r = requests.post('http://localhost:8000/token', json={'roomName':'test-room','participantName':'alice'})
if r.status_code != 200:
    print(f"Error: {r.json()}")
    exit(1)

token = r.json()['token']
print(f"Token: {token[:50]}...")

# Decode without verification to see payload
try:
    decoded = jwt.decode(token, options={"verify_signature": False})
    print("\nDecoded payload:")
    import json
    print(json.dumps(decoded, indent=2))
except Exception as e:
    print(f"Decode error: {e}")
