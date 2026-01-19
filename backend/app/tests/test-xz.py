import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import json
import httpx
from dotenv import load_dotenv

load_dotenv()  # 加载环境变量

base_url = 'https://xiaozhi.me'
client = httpx.Client(base_url=base_url, timeout=60)
headers = {'Authorization': f'Bearer {os.getenv("XZ_TOKEN")}'}


def test_get():
    response = client.get('/api/agents', params={'page': 1, 'pageSize': 100}, headers=headers)
    # response = client.get('/api/agents/1359699', headers=headers)
    print(response.status_code)
    # print(response.json())
    with open('0agent.json', 'w', encoding='utf-8') as f:
        f.write(json.dumps(response.json(), indent=2, ensure_ascii=False))


def test_post():
    data = {
        # "agent_name": "test测试",
        # "assistant_name": "小智",
        # "llm_model": "qwen",
        # "tts_voice": "zh_female_wanwanxiaohe_moon_bigtts",
        # "tts_speech_speed": "normal",
        # "tts_pitch": 0,
        # "asr_speed": "normal",
        # "language": "zh",
        # "character": "角色介绍...",
        # "memory_type": "SHORT_TERM",
        'id': 1359699
    }
    response = client.post('/api/agents/delete', json=data, headers=headers)
    print(response.status_code)
    with open('0.json', 'w', encoding='utf-8') as f:
        f.write(json.dumps(response.json(), indent=2, ensure_ascii=False))


if __name__ == '__main__':
    # test_get()
    test_post()
