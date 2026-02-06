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


def test_template():
    headers = {'token': 'dev'}
    response = client.get('agent/template/?id=453', headers=headers)
    print(response.status_code, response.json())


def test_ota():
    import requests

    headers = {
        'Device-Id': '98:3d:ae:e6:83:d0',
    }
    data = {
        'version': 2,
        'language': 'zh-CN',
        'flash_size': 16777216,
        'minimum_free_heap_size': 8275968,
        'mac_address': '98:3d:ae:e6:83:d0',
        'uuid': 'aa4ad1e9-0299-4880-9b0d-b96ea0a2bf3e',
        'chip_model_name': 'esp32s3',
        'chip_info': {'model': 9, 'cores': 2, 'revision': 2, 'features': 18},
        'application': {
            'name': 'xiaozhi',
            'version': '1.4.7.1',
            'compile_time': 'Mar 18 2025T20:10:57Z',
            'idf_version': 'v5.3.1',
            'elf_sha256': 'c4c294b037cb5df2e17036d517f615c77fef1d05e627f64f9b3d9edcfbcc5050',
        },
        'board': {
            'type': 'bread-compact-wifi',
            'name': 'bread-compact-wifi',
            'ssid': '12_404',
            'rssi': -26,
            'channel': 1,
            'ip': '192.168.10.22',
            'mac': '98:3d:ae:e6:83:d0',
        },
    }
    response = requests.post('http://localhost:3004/ota', headers=headers, json=data)
    print(response.json(), response.status_code)


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

    # res = await xz_service._get_token()
    res = await xz_service.get_agent(id='1440116')
    print(res)


async def test_wx():
    from core.wx_api import wx_service

    res = await wx_service.get_phone('0b35RWll2YXO2h4Ti4ll2EGiZT35RWlk')
    print(res)


async def test_profile():
    from core.profile_api import bl_service

    # res = await bl_service.generate_video(img_url='http://1.95.14.72:9000/holo-box/aigc/2.png', emotion='happy')
    # res = await bl_service.generate_image(img_url='http://1.95.14.72:9000/holo-box/aigc/2.png')
    res = await bl_service.generate_image(img_url='https://image-zyhz.wentouzhiying.com/profile/img/13-ori-img.png')
    # res = await bl_service.get_video_status('1eae7bbe-8107-4818-914d-1981e9bbe16f')
    print(res)


if __name__ == '__main__':
    # test_wxlogin()
    # test_oss()
    # test_ota()
    # test_template()
    import asyncio

    asyncio.run(test_xz())
    # asyncio.run(test_wx())
    # asyncio.run(test_profile())
