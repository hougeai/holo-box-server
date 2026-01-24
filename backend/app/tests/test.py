import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import httpx


base_url = 'http://localhost:3004/api/v1/'
client = httpx.Client(base_url=base_url, timeout=60)

headers = {'token': 'dev'}


def test_wxlogin():
    headers = {'token': 'dev'}
    data = {'code': '0b35RWll2YXO2h4Ti4ll2EGiZT35RWlk', 'user_id': '1'}
    response = client.post('base/wx_phone', json=data, headers=headers)
    print(response.status_code, response.json())


def test_oss():
    from core.minio import oss

    # res = oss.set_bucket_public_read()
    res = oss.list_objects()
    # res = oss.upload_file('uploads/1.png', file_path='1.png')
    # res = oss.download_file('uploads/1.png', save_path='2.png')
    # res = oss.delete_batch(['uploads/1.png'])
    print(res)


async def test_xz():
    from core.xz_api import xz_service

    res = await xz_service._get_token()
    print(res)


async def test_wx():
    from core.wx_api import wx_service

    res = await wx_service.get_phone('0b35RWll2YXO2h4Ti4ll2EGiZT35RWlk')
    print(res)


async def test_profile():
    from core.profile_api import bl_service

    res = await bl_service.generate_video(img_url='http://1.95.14.72:9000/holo-box/aigc/2.png', emotion='happy')
    # res = await bl_service.get_video_status('1eae7bbe-8107-4818-914d-1981e9bbe16f')
    print(res)


if __name__ == '__main__':
    # test_wxlogin()
    test_oss()
    # import asyncio

    # asyncio.run(test_xz())
    # asyncio.run(test_wx())
    # asyncio.run(test_profile())
