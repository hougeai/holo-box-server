import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import httpx


base_url = 'http://localhost:3004/api/v1/'
client = httpx.Client(base_url=base_url, timeout=60)

headers = {'token': 'dev'}


def test_wxlogin():
    headers = {'token': 'dev'}
    data = {
        'code': '0b35RWll2YXO2h4Ti4ll2EGiZT35RWlk',
    }
    response = client.post('base/wx_login', json=data, headers=headers)
    print(response.status_code, response.json())


if __name__ == '__main__':
    test_wxlogin()
