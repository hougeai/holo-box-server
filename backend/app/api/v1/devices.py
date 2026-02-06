from fastapi import APIRouter, Query
from tortoise.expressions import Q
from core.quota import quota_service
from core.xz_api import xz_service
from controllers import device_controller
from schemas.base import Fail, Success, SuccessExtra
from schemas.device import (
    DeviceCreate,
    DeviceUpdate,
    DeviceBind,
)
from models.agent import Agent


router = APIRouter()


@router.get('/list', summary='查看设备列表')
async def list_device(
    page: int = Query(1, description='页码'),
    page_size: int = Query(999, description='每页数量'),
    user_id: str = Query('', description='用户ID，用于搜索'),
    device_id: str = Query('', description='设备ID，用于搜索'),
    device_model: str = Query('', description='产品类型，用于搜索'),
):
    q = Q()
    if user_id:
        q &= Q(user_id=user_id)
    if device_id:
        q &= Q(device_id__contains=device_id)  # SQL: WHERE user_name LIKE '%xxx%'；user_name=user_name 精确匹配
    if device_model:
        q &= Q(device_model__contains=device_model)
    # 当前页码 每页显示数量；返回的是总数和当前页数据列表
    total, objs = await device_controller.list(page=page, page_size=page_size, search=q, order=['id'])
    data = [await obj.to_dict() for obj in objs]
    return SuccessExtra(data=data, total=total, page=page, page_size=page_size)


@router.post('/create', summary='创建设备')
async def create_device(
    obj_in: DeviceCreate,
):
    obj = await device_controller.get_by_mac(device_id=obj_in.device_id)
    if obj:
        return Fail(code=400, msg='设备已存在')

    await device_controller.create(obj_in=obj_in)
    return Success(msg='Created Successfully')


@router.post('/update', summary='更新设备')
async def update_device(
    obj_in: DeviceUpdate,
):
    # 检查设备配额：前端通过update user_id新增设备
    if obj_in.user_id:
        quota_ok, msg = await quota_service.check_device(obj_in.user_id)
        if not quota_ok:
            return Fail(code=400, msg=msg)
    await device_controller.update(id=obj_in.id, obj_in=obj_in)
    return Success(msg='Updated Successfully')


@router.delete('/delete', summary='删除设备')
async def delete_device(
    id: int = Query(..., description='ID'),
):
    # 首先获得device_id
    obj = await device_controller.get(id=id)
    if obj:
        await device_controller.remove(id=id)
        return Success(msg='Deleted Successfully')
    else:
        return Success(msg='Device not found')


@router.delete('/unbind', summary='解绑设备')
async def unbind_device(
    id: int = Query(..., description='ID'),
):
    # 首先获得device
    device = await device_controller.get(id=id)
    if device:
        if not device.user_id:
            return Fail(code=400, msg='设备已解绑')
        # 0. 更新agent的devcice_count
        agent = await Agent.filter(agent_id=device.agent_id).first()
        await agent.update_from_dict({'device_count': agent.device_count - 1})
        await agent.save()
        # 1. device和用户解绑：主键 id 查询已经是唯一的，不需要.first()调用；新增is_unbound表示这个设备解绑过；必须用orm的.save()才能自动更新update_at字段
        device.user_id = None
        device.agent_id = None
        device.last_conversation = None
        device.alias = None
        device.is_unbound = True
        await device.save()
        # 5. 给远端发请求
        result = await xz_service.unbind_device(deviceId=device.device_id)
        if not result or not result['success']:
            msg = result.get('message', '') if result else '未知'
            return Fail(code=400, msg=f'远端设备解绑失败：{msg}')
        return Success(msg='Deleted Successfully')
    else:
        return Fail(msg='Device not found')


@router.post('/bind', summary='绑定设备')
async def bind_device(obj_in: DeviceBind):
    res = await xz_service.bind_device(agentId=obj_in.agent_id, verificationCode=obj_in.code)
    if not res or not res['success']:
        msg = res.get('message', '') if res else '未知'
        return Fail(code=400, msg=f'设备绑定失败: {msg}')
    data = res['data']
    device = await device_controller.get_by_mac(data.get('mac_address', ''))
    await device_controller.update(
        id=device.id,
        obj_in={
            'user_id': obj_in.user_id,
            'agent_id': obj_in.agent_id,
            'device_id': data.get('id', ''),
            'auto_update': True if data.get('auto_update', False) else False,
            'serial_number': data.get('serial_number', ''),
        },
    )
    # 判断是否有agent_id
    if obj_in.agent_id:
        # 更新agent中device_count
        obj = await Agent.filter(agent_id=obj_in.agent_id).first()
        await obj.update_from_dict({'device_count': obj.device_count + 1})
        await obj.save()
    else:
        # 创建一个agent
        agent_id = data.get('agent_id', '')
        res = await xz_service.get_agent(agent_id)
        if not res or not res['success']:
            msg = res.get('message', '') if res else '未知'
            return Fail(code=400, msg=f'服务端获取智能体详情失败: {msg}')
        agent = res['data'].get('agent')
        agent['agent_id'] = agent.pop('id', agent_id)
        agent['device_count'] = agent.pop('deviceCount', 0)
        await Agent.create(user_id=obj_in.user_id, **{k: v for k, v in agent.items() if v is not None})
    return Success(msg='绑定成功')
