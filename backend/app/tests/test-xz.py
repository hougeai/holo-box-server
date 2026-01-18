import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import json
import httpx


base_url = 'https://xiaozhi.me'
client = httpx.Client(base_url=base_url, timeout=60)
headers = {
    'Authorization': 'Bearer eyJhbGciOiJFUzI1NiIsInR5cCI6IkpXVCJ9.eyJhcHBOYW1lIjoiaG9sb2JveCIsInVzZXJJZCI6NDc3MTY2LCJpc1RlbXBvcmFyeSI6dHJ1ZSwicHVycG9zZSI6ImRldmVsb3Blci1hcHAiLCJpYXQiOjE3Njg3MjMyMzcsImV4cCI6MTc2ODgwOTYzN30.CxN_LE1Nufupwe2OT5nCzzLGu8x1wWA3YhRk1zkVxcvLd6rtTCqi4W1rOAzJTdhUYsezdOHv6pEBGiCjgUQ1eQ'
}


def test_get():
    response = client.get('/api/developers/agent-templates/list', params={'page': 1, 'pageSize': 100}, headers=headers)
    print(response.status_code)
    # print(response.json())
    with open('0agentT.json', 'w', encoding='utf-8') as f:
        f.write(json.dumps(response.json(), indent=2, ensure_ascii=False))


if __name__ == '__main__':
    test_get()
