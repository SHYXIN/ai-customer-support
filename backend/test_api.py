import urllib.request
import json

data = json.dumps({"message": "如何取消订单？"}).encode("utf-8")
req = urllib.request.Request(
    "http://localhost:8000/api/chat",
    data=data,
    headers={"Content-Type": "application/json"},
)
try:
    with urllib.request.urlopen(req) as resp:
        result = json.loads(resp.read().decode("utf-8"))
        print(f"Response: {result['response'][:50]}...")
        print(f"References count: {len(result.get('references', []))}")
        for ref in result.get("references", [])[:2]:
            print(f"  - {ref.get('content', '')[:30]} | {ref.get('category', '')}")
except Exception as e:
    print(f"Error: {e}")
