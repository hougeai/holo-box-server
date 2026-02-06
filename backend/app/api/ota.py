import aiohttp
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from core.log import logger
from core.config import settings

from controllers import device_controller
from models import Ota, Agent, Profile
from schemas import Fail

router = APIRouter(tags=['OTA'])

emoji_dict = {
    'happy': [{'code': 'happy', 'emoji': '🙂'}, {'code': 'neutral', 'emoji': '😶'}],
    'laugh': [{'code': 'laughing', 'emoji': '😆'}, {'code': 'funny', 'emoji': '😂'}],
    'sad': [{'code': 'sad', 'emoji': '😔'}, {'code': 'crying', 'emoji': '😭'}],
    'angry': [{'code': 'angry', 'emoji': '😠'}, {'code': 'silly', 'emoji': '😜'}],
    'love': [{'code': 'loving', 'emoji': '😍'}, {'code': 'delicious', 'emoji': '🤤'}],
    'embarrassed': [
        {'code': 'embarrassed', 'emoji': '😳'},
        {'code': 'surprised', 'emoji': '😲'},
        {'code': 'shocked', 'emoji': '😱'},
    ],
    'thinking': [{'code': 'thinking', 'emoji': '🤔'}],
    'playful': [{'code': 'cool', 'emoji': '😎'}, {'code': 'winking', 'emoji': '😉'}],
    'calm': [
        {'code': 'confident', 'emoji': '😏'},
        {'code': 'kissy', 'emoji': '😘'},
        {'code': 'relaxed', 'emoji': '😌'},
    ],
    'sleepy': [{'code': 'sleepy', 'emoji': '😴'}, {'code': 'confused', 'emoji': '🙄'}],
}


# OTA转发接口
@router.post('/ota', summary='OTA转发')
async def ota(request: Request):
    headers = request.headers
    forward_headers = {
        'Activation-Version': headers.get('Activation-Version', '1'),
        'Device-Id': headers.get('Device-Id', ''),
        'Client-Id': headers.get('Client-Id', ''),
        'User-Agent': headers.get('User-Agent', ''),
        'Accept-Language': headers.get('Accept-Language', 'zh'),
        'Content-Type': 'application/json',
    }
    data = await request.json()
    ori_version = data['application']['version']
    mac_address = data['mac_address']
    uuid = data['uuid']
    chip_type = data['chip_model_name']
    device_model = data['board']['type']
    res_data = {}

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(settings.XIAOZHI_OTA_URL, headers=forward_headers, json=data) as response:
                if response.status == 200:
                    res_data = await response.json()
                    logger.info(f'OTA转发成功: {res_data}')
                    if 'activation' in res_data:
                        message = res_data['activation']['message']
                        _, code = message.split('\n')
                        res_data['activation']['message'] = code
                else:
                    logger.error(f'Failed to get ota info: {response.status}')
    except Exception as e:
        logger.error(f'OTA转发失败: {e}')
        return Fail(code=400, msg=f'OTA转发失败: {e}')

    # 查询设备是否OTA，是否有新版本
    device = await device_controller.get_by_mac(mac_address)
    if device:
        try:
            # 如果存在agent_id，则增加形象视频
            agent_id = device.agent_id
            if agent_id:
                agent = await Agent.filter(agent_id=agent_id).first()
                profile = await Profile.get(id=agent.profile_id)
                gen_vids = profile.gen_vids
                # 转成设备需要的数据
                results = []
                for k, v in gen_vids.items():
                    for item in emoji_dict[k]:
                        item['url'] = v.get('url', '')
                        item['hash'] = v.get('hash', '')
                        results.append(item)
                res_data['profile'] = results
        except Exception as e:
            logger.error(f'获取形象信息失败: {e}')
        # 设备已存在，更新设备信息
        await device_controller.update(id=device.id, obj_in={'app_version': ori_version})
        if not device.auto_update:
            res_data['firmware'] = {'version': ori_version, 'url': ''}
            return JSONResponse(content=res_data)
        # 获取最新版本信息
        obj = await Ota.filter(device_model=device.device_model, is_default=True).first()
        if obj:
            logger.info(
                f'{device.mac_address} {device.device_model} OtaEnabled {device.auto_update} 当前版本：{ori_version}，更新版本：{obj.app_version}'
            )
            res_data['firmware'] = {'version': obj.app_version, 'url': f'{settings.OSS_BUCKET_URL}/{obj.ota_url}'}
        return JSONResponse(content=res_data)
    else:
        # 新增设备
        data = {
            'mac_address': mac_address,
            'uuid': uuid,
            'chip_type': chip_type,
            'device_model': device_model,
            'app_version': ori_version,
        }
        await device_controller.create(obj_in=data)
        logger.info(f'新增设备 {mac_address} 成功')
        return JSONResponse(content=res_data)


# OTA激活转发接口
@router.post('/ota/activate', summary='OTA激活')
async def ota_activate(request: Request):
    headers = request.headers
    forward_headers = {
        'Activation-Version': headers.get('Activation-Version', '1'),
        'Device-Id': headers.get('Device-Id', ''),
        'Client-Id': headers.get('Client-Id', ''),
        'User-Agent': headers.get('User-Agent', ''),
        'Accept-Language': headers.get('Accept-Language', 'zh'),
        'Content-Type': 'application/json',
    }
    data = await request.json()
    # 转发给xiaozhi-ota
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f'{settings.XIAOZHI_OTA_URL}/activate', headers=forward_headers, json=data
            ) as response:
                res_data = await response.json()
                logger.info(f'ota-activate转发结果: status={response.status}, data={res_data}')
                return JSONResponse(content=res_data, status_code=response.status)
    except Exception as e:
        logger.error(f'OTA转发失败: {e}')
        return Fail(code=400, msg=f'OTA转发失败: {e}')
