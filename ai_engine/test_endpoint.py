import requests

url = "http://localhost:8001/analyze"
payload = {"user_prompt": "hi", "metrics": {}}
response = requests.post(url, json=payload)

print(f"Status Code: {response.status_code}")
print(f"Response: {response.json()}")
