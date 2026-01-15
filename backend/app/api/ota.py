import aiohttp
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from core.api import ip2loc
from core.log import logger
from core.config import settings

from controllers import device_controller
from models import Ota
from schemas import Success, Fail

router = APIRouter(tags=['OTA'])


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
    device_id = data['mac_address']
    uuid = data['uuid']
    chip_type = data['chip_model_name']
    device_model = data['board']['type']
    res_data = {}

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(settings.XIAOZHI_OTA_URL, headers=forward_headers, json=data) as response:
                if response.status == 200:
                    res_data = await response.json()
                    if 'activation' in res_data:
                        message = res_data['activation']['message']
                        _, code = message.split('\n')
                        res_data['activation']['message'] = '\n'.join([settings.USER_FE_URL, code])
                    logger.info(f'OTA转发成功: {res_data}')
                else:
                    logger.error(f'Failed to get ota info: {response.status}')
    except Exception as e:
        logger.error(f'OTA转发失败: {e}')
        return Fail(code=400, msg=f'OTA转发失败: {e}')
    mac = headers.get('Device-Id')
    # 新增 pro mqtt 消息
    res_data['mqtt_pro'] = {
        'endpoint': settings.MQTT_HOST,
        'port': settings.MQTT_PORT,
        'client_id': mac,
        'publish_topic': 'device-server',
    }
    # 查询设备是否OTA，是否有新版本
    device = await device_controller.get_by_deviceid(mac)
    if device:
        # 设备已存在，更新设备信息
        await device_controller.update(id=device.id, obj_in={'app_version': ori_version})
        if not device.ota_enabled:
            res_data['firmware'] = {'version': ori_version, 'url': ''}
            return JSONResponse(content=res_data)
        # 获取最新版本信息
        obj = await Ota.filter(device_model=device.device_model, is_default=True).first()
        if obj:
            logger.info(
                f'{device.device_id} {device.device_model} OtaEnabled {device.ota_enabled} 当前版本：{ori_version}，更新版本：{obj.app_version}'
            )
            res_data['firmware'] = {'version': obj.app_version, 'url': f'{settings.OSS_BUCKET_URL}/{obj.ota_url}'}
        return JSONResponse(content=res_data)
    else:
        # 新增设备
        logger.info(f'Client IP: {request.client.host}, Headers: {request.headers}')
        client_ip = (
            request.headers.get('x-forwarded-for', '').split(',')[0]
            or request.headers.get('x-real-ip')
            or request.client.host
        )
        location = await ip2loc.get_location(client_ip)
        data = {
            'device_id': device_id,
            'uuid': uuid,
            'location': location,
            'chip_type': chip_type,
            'device_model': device_model,
            'app_version': ori_version,
        }
        await device_controller.create(obj_in=data)
        logger.info(f'新增设备 {device_id} 成功')
        return JSONResponse(content=res_data)


# OTA激活转发接口
@router.post('/ota/activate', summary='OTA激活')
async def ota_activate(request: Request):
    headers = request.headers
    device = await device_controller.get_by_deviceid(headers.get('Device-Id'))
    if device and device.user_id:
        return Success(msg='OTA激活成功')
    else:
        logger.info(f'设备未绑定: {device.device_id}')
        return Fail(code=400, msg='设备未绑定用户')
