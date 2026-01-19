import hashlib
from fastapi import APIRouter, Query
from fastapi import File, UploadFile, Form
from tortoise.expressions import Q
from core.background import CTX_USER_ID
from core.log import logger
from core.xz_api import xz_service
from core.minio import oss
from core.config import settings
from controllers import agent_controller, agent_template_controller, voice_controller
from schemas.base import Fail, Success, SuccessExtra
from schemas.agent import AgentCreate, AgentUpdate, AgentTemplateCreate, AgentTemplateUpdate
from models.agent import Agent, AgentTemplate, Voice, LLM

router = APIRouter()


@router.get('/list', summary='查看智能体列表')
async def list_agent(
    page: int = Query(1, description='页码'),
    page_size: int = Query(999, description='每页数量'),
    user_id: str = Query('', description='用户ID，用于搜索'),
    agent_id: str = Query('', description='智能体ID，用于搜索'),
    agent_name: str = Query('', description='智能体名称，用于搜索'),
):
    q = Q()
    if user_id:
        q &= Q(user_id=user_id)
    if agent_id:
        q &= Q(agent_id=agent_id)
    if agent_name:
        q &= Q(agent_name_contains=agent_name)
    # 当前页码 每页显示数量；返回的是总数和当前页数据列表
    total, objs = await agent_controller.list(page=page, page_size=page_size, search=q, order=['-id'])
    data = [await obj.to_dict() for obj in objs]
    return SuccessExtra(data=data, total=total, page=page, page_size=page_size)


@router.post('/create', summary='创建智能体')
async def create_agent(
    obj_in: AgentCreate,
):
    user_id = CTX_USER_ID.get()
    obj = await Agent.filter(user_id=user_id, agent_name=obj_in.agent_name).first()
    if obj:
        return Fail(code=400, msg=f'{obj_in.agent_name}已存在，请重新命名')
    res = await xz_service.create_agent(obj_in)
    if not res or not res['data']:
        logger.error(f'创建智能体失败: {res}')
        return Fail(code=400, msg='XZ-API创建失败')
    obj_in.agent_id = str(res['data'].get('id'))
    obj_in.user_id = user_id
    # 查询智能体详情
    res = await xz_service.get_agent(obj_in.agent_id)
    if not res or not res['data']:
        logger.error(f'获取智能体详情失败: {res}')
        return Fail(code=400, msg='XZ-API获取智能体详情失败')
    agent = res['data'].get('agent')
    obj_in.mcp_endpoints = agent.get('mcp_endpoints')
    obj_in.source = agent.get('source')
    # 保存到数据库
    obj = await agent_controller.create(obj_in=obj_in)
    data = await obj.to_dict()
    return Success(data=data)


@router.post('/update', summary='更新智能体')
async def update_agent(
    obj_in: AgentUpdate,
):
    obj = await agent_controller.get(id=obj_in.id)
    if not obj:
        return Fail(code=400, msg='Agent not found')
    # 先更新远端的
    res = await xz_service.update_agent(obj.agent_id, obj_in)
    if not res or not res['success']:
        return Fail(code=400, msg='XZ-API更新失败')
    obj = await agent_controller.update(id=obj_in.id, obj_in=obj_in)
    data = await obj.to_dict()
    return Success(data=data)


@router.delete('/delete', summary='删除智能体')
async def delete_agent(
    id: int = Query(..., description='ID'),
):
    obj = await agent_controller.get(id=id)
    if not obj:
        return Fail(code=400, msg='Agent not found')
    # 先判断是否有设备绑定
    if obj.device_count > 0:
        return Fail(code=400, msg='请先解绑当前智能体下的所有设备')
    # 先删除远端的
    res = await xz_service.delete_agent(obj.agent_id)
    if not res or not res['success']:
        return Fail(code=400, msg='XZ-API删除失败')
    await agent_controller.remove(id=id)
    return Success(msg='Deleted Successfully')


@router.get('/voice/list', summary='TTS voice 列表')
async def list_voice(
    page: int = Query(1, description='页码'),
    page_size: int = Query(999, description='每页数量'),
    user_id: str = Query('', description='用户ID，用于搜索'),
    voice_id: str = Query('', description='音色ID，用于搜索'),
):
    q = Q()
    if user_id:
        q &= Q(user_id=user_id)
    if voice_id:
        q &= Q(voice_id=voice_id)
    # 当前页码 每页显示数量；返回的是总数和当前页数据列表
    total, objs = await voice_controller.list(page=page, page_size=page_size, search=q, order=['id'])
    data = [await obj.to_dict() for obj in objs]
    return SuccessExtra(data=data, total=total, page=page, page_size=page_size)


@router.get('/llm/list', summary='LLM 模型列表')
async def list_llm():
    objs = await LLM.all()
    data = [await obj.to_dict(exclude_fields=['update_at']) for obj in objs]
    return Success(data=data)


# 智能体模板
@router.get('/template/list', summary='查看智能体模板列表')
async def list_agent_template(
    page: int = Query(1, description='页码'),
    page_size: int = Query(999, description='每页数量'),
    agent_name: str = Query('', description='智能体模板名称，用于搜索'),
):
    q = Q()
    if agent_name:
        q &= Q(agent_name_contains=agent_name)
    total, objs = await agent_template_controller.list(page=page, page_size=page_size, search=q, order=['id'])
    data = [await obj.to_dict() for obj in objs]
    return SuccessExtra(data=data, total=total, page=page, page_size=page_size)


@router.post('/template/create', summary='创建智能体模板')
async def create_agent_template(
    obj_in: AgentTemplateCreate,
):
    obj = await AgentTemplate.filter(agent_name=obj_in.agent_name).first()
    if obj:
        return Fail(code=400, msg=f'{obj_in.agent_name}已存在，请重新命名')
    # 先给远端发请求
    res = await xz_service.create_agent_template(obj_in)
    if not res or not res['data']:
        logger.error(f'创建智能体模板失败: {res}')
        return Fail(code=400, msg='XZ-API创建失败')
    obj_in.agent_id = str(res['data'].get('id'))
    obj = await agent_template_controller.create(obj_in=obj_in)
    data = await obj.to_dict()
    return Success(data=data)


@router.post('/template/update', summary='更新智能体模板')
async def update_agent_template(
    obj_in: AgentTemplateUpdate,
):
    obj = await agent_template_controller.get(id=obj_in.id)
    if not obj:
        return Fail(code=400, msg='AgentTemplate not found')
    # 先更新远端的
    res = await xz_service.update_agent_template(obj.agent_id, obj_in)
    if not res or not res['success']:
        return Fail(code=400, msg='XZ-API更新失败')
    obj = await agent_template_controller.update(id=obj_in.id, obj_in=obj_in)
    data = await obj.to_dict()
    return Success(data=data)


@router.delete('/template/delete', summary='删除智能体模板')
async def delete_agent_template(
    id: int = Query(..., description='ID'),
):
    obj = await agent_template_controller.get(id=id)
    if not obj:
        return Fail(code=400, msg='AgentTemplate not found')
    # 先删除远端的
    res = await xz_service.delete_agent_template(obj.agent_id)
    if not res or not res['success']:
        return Fail(code=400, msg='XZ-API删除失败')
    await agent_template_controller.remove(id=id)
    return Success(msg='Deleted Successfully')


# 音色克隆相关
@router.post('/voice/upload', summary='上传音频文件')
async def upload_voice(
    audio_file: UploadFile = File(...),
):
    user_id = CTX_USER_ID.get()
    audio_content = await audio_file.read()
    unique_id = hashlib.md5(audio_content).hexdigest()[:8]
    audio_key = f'audio/ref-lx-{unique_id}.wav'
    obj = await Voice.filter(ref_audio=audio_key, user_id=user_id).first()
    if obj:
        return Fail(code=400, msg='音频已存在，请在音色管理页面编辑')
    logger.info(f'upload voice: {user_id} {unique_id}')
    result = await oss.upload_audio_async(key=audio_key, audio_data=audio_content)
    if not result:
        return Fail(code=400, msg='上传音频失败')
    # 请求xz_service创建音色栏位
    res = await xz_service.create_voice()
    if not res or not res['data']:
        logger.error(f'创建音色栏位失败: {res}')
        return Fail(code=400, msg='创建音色栏位失败')
    tts_voice_id = res['data']['id']
    tts_voice_name = res['data']['name']
    obj = await Voice.create(
        user_id=user_id,
        ref_audio=audio_key,
        tts_voice_id=tts_voice_id,
        tts_voice_name=tts_voice_name,
        status='Pending',
    )
    data = await obj.to_dict(exclude_fields=['update_at'])
    return Success(data=data)


@router.post('/voice/clone', summary='音色克隆')
async def clone_voice(
    id: str = Form(..., description='音色ID'),
    name: str = Form(..., description='音色名称'),
    gender: str = Form(None, description='性别'),
    language: str = Form(None, description='语言'),
):
    voice = await Voice.get(id=id)
    # 请求xz_service训练音色
    user_id = CTX_USER_ID.get()
    logger.info(f'clone voice: {user_id} {voice.tts_voice_id} {voice.ref_audio} {name}')
    key = f'{settings.OSS_BUCKET_URL}/{voice.ref_audio}'
    res = await xz_service.clone_voice(voice.tts_voice_id, key, name)
    if not res or not res['data']:
        logger.error(f'音色克隆失败: {res}')
        return Fail(code=400, msg='音色克隆失败')
    # 更新字段
    voice.status = res['data']['state']
    voice.tts_voice_name = name
    if language is not None or gender is not None:
        tags = voice.tags or {}
        if language is not None:
            tags['languages'] = [language]
        if gender is not None:
            tags['gender'] = gender
        voice.tags = tags
    await voice.save()
    data = await voice.to_dict(exclude_fields=['update_at'])
    return Success(data=data)


@router.post('/voice/update', summary='更新音色')
async def update_voice(
    id: str = Form(..., description='音色ID'),
    name: str = Form(None, description='音色名称'),
    language: str = Form(None, description='语言'),
    gender: str = Form(None, description='性别'),
):
    voice = await Voice.get(id=id)
    if name is not None:
        voice.tts_voice_name = name
        await xz_service.clone_voice(voice.tts_voice_id, ref_audio=None, name=name)

    if language is not None or gender is not None:
        tags = voice.tags or {}
        if language is not None:
            tags['languages'] = [language]
        if gender is not None:
            tags['gender'] = gender
        voice.tags = tags

    await voice.save()
    data = await voice.to_dict(exclude_fields=['update_at'])
    return Success(data=data)


@router.get('/voice/', summary='获取音色')
async def get_voice(
    id: int = Query(..., description='ID'),
):
    voice = await Voice.get(id=id)
    res = await xz_service.get_voice(voice.tts_voice_id)
    if not res or not res['data']:
        logger.error(f'音色获取失败: {res}')
        return Fail(code=400, msg='音色获取失败')
    state = res['data']['state']
    voice.status = state
    await voice.save()
    data = await voice.to_dict(exclude_fields=['update_at'])
    return Success(data=data)


@router.delete('/voice/delete', summary='删除音色')
async def delete_voice(id: int = Query(..., description='ID')):
    obj = await Voice.get(id=id)
    # 删除远端
    res = await xz_service.delete_voice(obj.tts_voice_id)
    # 删除对象存储
    await oss.delete_file_async(obj.ref_audio)
    # 删除数据库
    await Voice.filter(id=id).delete()
    if not res or res['code'] != 0:
        return Fail(code=400, msg='远端删除失败')
    return Success(msg='删除成功')
