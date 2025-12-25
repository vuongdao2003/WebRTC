import requests
try:
    r = requests.get('http://localhost:8000/token/debug', timeout=10)
    print('status', r.status_code)
    print(r.text)
except Exception as e:
    import traceback
    traceback.print_exc()
