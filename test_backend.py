import requests
import json

url = "http://localhost:8000/api/agent/chat"
data = {
    "message": "hello test",
    "conversation_id": None,
    "auto_approve_safe": True,
    "approval_mode": "normal",
    "claude_model": "claude-sonnet-4-5-20250929"
}

try:
    response = requests.post(url, json=data)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
except Exception as e:
    print(f"Error: {e}")
