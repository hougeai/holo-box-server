import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import json
import httpx


base_url = 'https://xiaozhi.me/'
client = httpx.Client(base_url=base_url, timeout=60)
headers = {'Authorization': 'Bearer xx'}


def test_agent():
    # get list
    response = client.get('xiaozhi/agent/list', headers=headers)
    # create：{'code': 0, 'msg': 'success', 'data': 'cd85114b60d349c58bde7f80f137a416'} ，默认给到语言模型和音色
    # response = client.post('xiaozhi/agent', json={'agentName': '明道'}, headers=headers) # 只能输入助手昵称
    # update：
    # data = {'agentName': '明道', 'llmModelId': '5869bfe4a5823bcda038a7f79dbd50a2'}
    # response = client.put('xiaozhi/agent/cd85114b60d349c58bde7f80f137a416', json=data, headers=headers)
    # delete
    # response = client.delete('xiaozhi/agent/913958e99aef4565bea0f29640f18f52', headers=headers)
    print(response.status_code)
    with open('0.json', 'w', encoding='utf-8') as f:
        f.write(json.dumps(response.json(), indent=2, ensure_ascii=False))


def test_oss():
    from core.minio import oss

    oss.set_bucket_public_read()


if __name__ == '__main__':
    test_oss()
