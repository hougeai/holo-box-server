import hashlib
from typing import Optional
from fastapi import APIRouter, Query
from fastapi import File, UploadFile, Form
from tortoise.expressions import Q
from core.background import CTX_USER_ID, BgTasks
from core.log import logger
from core.xz_api import xz_service
from core.profile_api import bl_service
from core.minio import oss
from core.config import settings
from core.mcp_manager import mcp_manager
from controllers import (
    agent_controller,
    agent_template_controller,
    voice_controller,
    profile_controller,
    system_prompt_controller,
    mcp_tool_controller,
)
from schemas.base import Fail, Success, SuccessExtra
from schemas.agent import (
    AgentCreate,
    AgentUpdate,
    AgentTemplateCreate,
    AgentTemplateUpdate,
    ProfileVidGen,
    ProfileUpdate,
    VoiceUpdate,
    SystemPromptCreate,
    SystemPromptUpdate,
    McpToolCreate,
    McpToolUpdate,
)
from models.agent import Agent, AgentTemplate, Voice, LLM, Profile, SystemPrompt, McpTool

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
    obj = await Agent.filter(user_id=obj_in.user_id, agent_name=obj_in.agent_name).first()
    if obj:
        return Fail(code=400, msg=f'{obj_in.agent_name}已存在，请重新命名')
    res = await xz_service.create_agent(obj_in)
    if not res or not res.get('success'):
        msg = res.get('message', '') if res else '未知'
        logger.error(f'创建智能体失败: {msg}')
        return Fail(code=400, msg=f'服务端创建失败: {msg}')
    obj_in.agent_id = str(res['data'].get('id'))  # 只返回id
    # 查询智能体详情
    res = await xz_service.get_agent(obj_in.agent_id)
    if not res or not res.get('success'):
        msg = res.get('message', '') if res else '未知'
        logger.error(f'获取智能体详情失败: {msg}')
        return Fail(code=400, msg=f'服务端获取智能体详情失败: {msg}')
    agent = res['data'].get('agent')
    obj_in.mcp_endpoints = agent.get('mcp_endpoints')
    obj_in.source = agent.get('source')
    # fix：如果存在product_mcp_endpoints，则更新智能体
    if obj_in.product_mcp_endpoints:
        res = await xz_service.update_agent(obj_in.agent_id, obj_in)
        if not res or not res.get('success'):
            msg = res.get('message', '') if res else '未知'
            logger.error(f'更新product_mcp_endpoints失败: {msg}')
            return Fail(code=400, msg=f'服务端更新product_mcp_endpoints失败: {msg}')
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
    update_data = obj_in.model_dump(exclude_unset=True, exclude={'id'})
    local_only_fields = {'avatar', 'profile_id'}
    has_remote_fields = any(field not in local_only_fields for field in update_data.keys())
    # 如果有需要远程更新的字段，则调用远端服务
    if has_remote_fields:
        res = await xz_service.update_agent(obj.agent_id, obj_in)
        if not res or not res.get('success'):
            msg = res.get('message', '') if res else '未知'
            return Fail(code=400, msg=f'服务端更新失败: {msg}')
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
    # if obj.device_count > 0:
    #     return Fail(code=400, msg='请先解绑当前智能体下的所有设备')
    # 先删除远端的
    res = await xz_service.delete_agent(obj.agent_id)
    if not res or not res.get('success'):
        msg = res.get('message', '') if res else '未知'
        return Fail(code=400, msg=f'服务端删除失败: {msg}')
    await agent_controller.remove(id=id)
    return Success(msg='Deleted Successfully')


@router.get('/voice/list', summary='TTS voice 列表')
async def list_voice(
    page: int = Query(1, description='页码'),
    page_size: int = Query(999, description='每页数量'),
    user_id: Optional[str] = Query(None, description='用户ID，用于搜索'),
    voice_id: Optional[str] = Query(None, description='音色ID，用于搜索'),
    language: Optional[str] = Query(None, description='语言，用于搜索'),
    public: Optional[bool] = Query(None, description='是否公开，用户前端传入true'),
):
    q = Q()
    if user_id:
        q &= Q(user_id=user_id)
    if voice_id:
        q &= Q(voice_id=voice_id)
    if language:
        q &= Q(language=language)
    if public is not None:
        q &= Q(public=public)
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
    agent_name: Optional[str] = Query('', description='智能体模板名称，用于搜索'),
    public: Optional[bool] = Query(None, description='是否公开，用户前端传入true'),
):
    q = Q()
    if agent_name:
        q &= Q(agent_name_contains=agent_name)
    if public is not None:
        q &= Q(public=public)
    total, objs = await agent_template_controller.list(page=page, page_size=page_size, search=q, order=['-id'])
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
    if not res or not res.get('success'):
        msg = res.get('message', '') if res else '未知'
        logger.error(f'创建智能体模板失败: {msg}')
        return Fail(code=400, msg=f'服务端创建失败: {msg}')
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
    update_data = obj_in.model_dump(exclude_unset=True, exclude={'id'})
    local_only_fields = {'avatar', 'profile_id', 'public', 'desc', 'system_prompt'}
    has_remote_fields = any(field not in local_only_fields for field in update_data.keys())
    # 如果有需要远程更新的字段，则调用远端服务
    if has_remote_fields:
        res = await xz_service.update_agent_template(obj.agent_id, obj_in)
        if not res or not res.get('success'):
            msg = res.get('message', '') if res else '未知'
            return Fail(code=400, msg=f'服务端更新失败： {msg}')
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
    if not res or not res.get('success'):
        msg = res.get('message', '') if res else '未知'
        return Fail(code=400, msg=f'服务端删除失败: {msg}')
    await agent_template_controller.remove(id=id)
    return Success(msg='Deleted Successfully')


@router.get('/template/', summary='查询智能体模板详情')
async def get_template(
    id: int = Query(..., description='ID'),
):
    obj = await agent_template_controller.get(id=id)
    if not obj:
        return Fail(code=400, msg='AgentTemplate not found')
    data = await obj.to_dict()
    return Success(data=data)


# 形象相关
@router.get('/profile/list', summary='查看形象列表')
async def list_profile(
    page: int = Query(1, description='页码'),
    page_size: int = Query(999, description='每页数量'),
    user_id: Optional[str] = Query(None, description='用户ID，用于搜索'),
    public: Optional[bool] = Query(None, description='是否公开的形象，用户前端传入true'),
):
    q = Q()
    if user_id:
        q &= Q(user_id=user_id)
    if public is not None:
        q &= Q(public=public)
    total, objs = await profile_controller.list(page=page, page_size=page_size, search=q, order=['-id'])
    data = [await obj.to_dict() for obj in objs]
    return SuccessExtra(data=data, total=total, page=page, page_size=page_size)


@router.post('/profile/upload-img', summary='AIGC创建形象第一步：上传原始图片，生成形象记录')
async def upload_img(
    name: str = Form(..., description='形象名称'),
    ori_img: UploadFile = File(...),
    ret_gen_img: bool = Form(True, description='是否生成形象图片'),
    subject_type: str = Form('human', description='形象主体类型：human/animal等'),
):
    user_id = CTX_USER_ID.get()
    obj = await Profile.filter(user_id=user_id, name=name).first()
    if obj:
        return Fail(code=400, msg=f'{name}已存在，请重新命名')
    ori_img = await ori_img.read()
    # 验证图片尺寸
    is_valid, error_msg = bl_service.validate_image_size(ori_img)
    if not is_valid:
        return Fail(code=400, msg=error_msg)
    # 创建profile栏位
    obj = await Profile.create(
        user_id=user_id,
        name=name,
        status='pending',
        subject_type=subject_type,
    )
    suffix = hashlib.sha256(f'{obj.id}-ori'.encode()).hexdigest()[:4]
    ori_img_key = f'profile/img/{obj.id}-ori-img-{suffix}.png'
    result = await oss.upload_file_async(ori_img_key, file_data=ori_img)
    if not result:
        await profile_controller.remove(id=obj.id)
        return Fail(code=400, msg='上传原始图片失败')
    # 上传成功，根据ori_img_url生成形象图片
    ori_img_url = f'{settings.OSS_BUCKET_URL}/{ori_img_key}'
    obj.ori_img = ori_img_url
    if ret_gen_img:
        gen_img_url, msg = await bl_service.generate_image(ori_img_url, subject_type)
        if not gen_img_url:
            logger.error(f'生成形象图片失败: {msg}')
            await profile_controller.remove(id=obj.id)
            return Fail(code=400, msg=f'生成形象图片失败: {msg}')
        # 下载百炼生成的图片并上传到 oss
        suffix = hashlib.sha256(f'{obj.id}-gen'.encode()).hexdigest()[:4]
        gen_img_key = f'profile/img/{obj.id}-gen-img-{suffix}.png'
        gen_img_data, content_type = await bl_service.download_file(gen_img_url, 'image/png')
        if not gen_img_data:
            logger.error('下载生成图片失败')
            await profile_controller.remove(id=obj.id)
            return Fail(code=400, msg='下载生成图片失败')
        result = await oss.upload_file_async(gen_img_key, file_data=gen_img_data, content_type=content_type)
        if not result:
            logger.error('上传生成图片失败')
            await profile_controller.remove(id=obj.id)
            return Fail(code=400, msg='上传生成图片失败')
        obj.gen_img = f'{settings.OSS_BUCKET_URL}/{gen_img_key}'
    await obj.save()
    data = await obj.to_dict()
    return Success(data=data)


@router.post('/profile/generate-vid', summary='AIGC创建形象第二步：生成形象视频，立即返回')
async def generate_vid(
    obj_in: ProfileVidGen,
):
    obj = await Profile.get(id=obj_in.id)
    if not obj:
        return Fail(code=400, msg='请先创建形象第一步获取形象id')
    # 根据不同方法创建形象
    obj.method = obj_in.method
    if obj_in.method == 'bailian':
        await BgTasks.add_task(
            bl_service.generate_and_save, obj.id, obj.gen_img, obj.subject_type, 2
        )  # 响应返回前端之后，fastapi会自动执行这个后台任务
        obj.status = 'processing'
        await obj.save()
        data = await obj.to_dict()
        return Success(data=data)
    else:
        return Fail(code=400, msg=f'{obj_in.method} 方法暂不支持')


@router.post('/profile/generate-vid-edit', summary='编辑模式下生成替换视频，轮询等待返回')
async def generate_vid_edit(
    obj_in: ProfileVidGen,
):
    obj = await Profile.get(id=obj_in.id)
    if not obj:
        return Fail(code=400, msg='请先创建形象第一步获取形象id')
    # 根据不同方法创建形象
    if obj_in.method == 'bailian':
        video_url, msg = await bl_service.generate_video(obj.gen_img, obj.subject_type, emotion=obj_in.emotion)
        if not video_url:
            logger.error(f'生成形象视频失败: {msg}')
            return Fail(code=400, msg=f'生成形象视频失败: {msg}')
        # 下载百炼生成的视频并上传到 oss
        suffix = hashlib.sha256(f'{obj_in.id}-{obj_in.emotion}'.encode()).hexdigest()[:4]
        video_key = f'profile/vid/{obj_in.id}-{obj_in.emotion}-{suffix}.mp4'
        video_data, content_type = await bl_service.download_file(video_url, 'video/mp4')
        result = await oss.upload_file_async(video_key, file_data=video_data, content_type=content_type)
        if not result:
            logger.error('上传生成视频失败')
            return Fail(code=400, msg='上传生成视频失败')
        video_url = f'{settings.OSS_BUCKET_URL}/{video_key}'
        video_hash = hashlib.sha256(video_data).hexdigest()
        return Success(data={'video_url': video_url, 'video_hash': video_hash})
    else:
        return Fail(code=400, msg=f'{obj_in.method} 方法暂不支持')


@router.get('/profile/', summary='查询形象详情，包括形象生成状态等')
async def get_profile(
    id: int = Query(..., description='ID'),
):
    obj = await Profile.get(id=id)
    if not obj:
        return Fail(code=400, msg='Profile not found')
    data = await obj.to_dict()
    return Success(data=data)


@router.post('/profile/upload-vid', summary='手动创建形象：上传视频文件，返回url')
async def upload_vid(
    id: int = Form(..., description='ID'),
    emotion: str = Form(..., description='情绪'),
    video: UploadFile = File(...),
):
    suffix = hashlib.sha256(f'{id}-{emotion}'.encode()).hexdigest()[:4]
    video_key = f'profile/vid/{id}-{emotion}-{suffix}.mp4'
    video_data = await video.read()
    upload_result = await oss.upload_file_async(
        video_key,
        file_data=video_data,
        content_type=video.content_type or 'application/octet-stream',
    )
    if not upload_result:
        return Fail(code=400, msg='上传视频文件失败')
    video_url = f'{settings.OSS_BUCKET_URL}/{video_key}'
    # 计算视频文件的hash值，用于检测文件是否被覆盖
    video_hash = hashlib.sha256(video_data).hexdigest()
    return Success(data={'video_url': video_url, 'video_hash': video_hash})


@router.post('/profile/update', summary='手动创建形象(上传视频url)/更新形象')
async def update_profile(
    obj_in: ProfileUpdate,
):
    obj = await Profile.get(id=obj_in.id)
    if not obj:
        return Fail(code=400, msg='形象未创建')

    # 判断gen_vids是否完整，如果10个情绪的url都有值，则设置status为success
    if obj_in.gen_vids:
        valid_urls = [info.get('url') for info in obj_in.gen_vids.values() if info.get('url')]
        if len(valid_urls) == 10:
            obj_in.status = 'success'
    obj = await profile_controller.update(id=obj.id, obj_in=obj_in)
    data = await obj.to_dict()
    return Success(data=data)


@router.delete('/profile/delete', summary='删除形象')
async def delete_profile(
    id: int = Query(..., description='ID'),
):
    obj = await profile_controller.get(id=id)
    if not obj:
        return Fail(code=400, msg='形象未创建')
    # 先删除oss中的文件：注意要改为key，而不是url
    if obj.ori_img:
        key = obj.ori_img.replace(settings.OSS_BUCKET_URL, '')
        await oss.delete_file_async(key=key)
    if obj.gen_img:
        key = obj.gen_img.replace(settings.OSS_BUCKET_URL, '')
        await oss.delete_file_async(key=key)
    if obj.gen_vids:
        for emotion, info in obj.gen_vids.items():
            if info.get('url'):
                key = info['url'].replace(settings.OSS_BUCKET_URL, '')
                await oss.delete_file_async(key=key)
    await profile_controller.remove(id=id)
    return Success(msg='删除成功')


# 系统提示词相关
@router.get('/sys-prompt/list', summary='查看系统提示词列表')
async def list_sys_prompt_list(
    page: int = Query(1, description='页码'),
    page_size: int = Query(999, description='每页数量'),
    name: Optional[str] = Query('', description='名称，用于搜索'),
):
    q = Q()
    if name:
        q &= Q(name__icontains=name)
    total, objs = await system_prompt_controller.list(page=page, page_size=page_size, search=q, order=['-id'])
    data = [await obj.to_dict() for obj in objs]
    return SuccessExtra(data=data, total=total, page=page, page_size=page_size)


@router.post('/sys-prompt/create', summary='创建系统提示词')
async def create_sys_prompt(
    obj_in: SystemPromptCreate,
):
    obj = await SystemPrompt.filter(name=obj_in.name).first()
    if obj:
        return Fail(code=400, msg='系统提示词已存在')
    obj = await system_prompt_controller.create(obj_in)
    data = await obj.to_dict()
    return Success(data=data)


@router.post('/sys-prompt/update', summary='更新系统提示词')
async def update_sys_prompt(
    obj_in: SystemPromptUpdate,
):
    obj = await system_prompt_controller.get(id=obj_in.id)
    if not obj:
        return Fail(code=400, msg='系统提示词不存在')
    obj = await system_prompt_controller.update(id=obj.id, obj_in=obj_in)
    data = await obj.to_dict()
    return Success(data=data)


@router.delete('/sys-prompt/delete', summary='删除系统提示词')
async def delete_sys_prompt(
    id: int = Query(..., description='ID'),
):
    obj = await system_prompt_controller.get(id=id)
    if not obj:
        return Fail(code=400, msg='系统提示词不存在')
    await system_prompt_controller.remove(id=id)
    return Success(msg='删除成功')


# MCP 相关
@router.get('/mcp-tool/list', summary='查看MCP工具列表')
async def list_mcp_tool(
    page: int = Query(1, description='页码'),
    page_size: int = Query(999, description='每页数量'),
    name: Optional[str] = Query('', description='名称，用于搜索'),
    source: Optional[str] = Query('', description='创建来源'),
    public: Optional[bool] = Query(None, description='是否公开，用户前端传入true'),
):
    q = Q()
    if name:
        q &= Q(name__icontains=name)
    if source:
        q &= Q(source=source)
    if public is not None:
        q &= Q(public=public)
    total, objs = await mcp_tool_controller.list(page=page, page_size=page_size, search=q, order=['-id'])
    data = [await obj.to_dict() for obj in objs]
    return SuccessExtra(data=data, total=total, page=page, page_size=page_size)


@router.post('/mcp-tool/create', summary='创建MCP工具')
async def create_mcp_tool(
    obj_in: McpToolCreate,
):
    obj = await McpTool.filter(name=obj_in.name).first()
    if obj:
        return Fail(code=400, msg=f'MCP已存在: {obj.name}')
    # 检查 protocol 和 config 是否有效
    if not obj_in.protocol or not obj_in.config:
        return Fail(code=400, msg='请填写正确的protocol和config')
    ok, msg = await mcp_manager.test(obj_in)
    if not ok:
        return Fail(code=400, msg=f'MCP测试失败: {msg}')
    # 请求xz-service创建MCP
    res = await xz_service.create_mcp(obj_in.name, obj_in.description)
    if not res or not res.get('success'):
        msg = res.get('message', '') if res else '未知'
        logger.error(f'创建MCP失败: {msg}')
        return Fail(code=400, msg=f'云端创建MCP失败: {msg}')
    endpoint_id = res['data']['id']
    obj_in.endpoint_id = endpoint_id
    # 请求生成token
    res = await xz_service.create_mcp_token(endpoint_id)
    if not res or not res.get('success'):
        msg = res.get('message', '') if res else '未知'
        logger.error(f'创建MCP Token失败: {msg}')
        return Fail(code=400, msg=f'云端创建MCP Token失败: {msg}')
    token = res.get('token', '')
    if not token:
        return Fail(code=400, msg='创建MCP Token失败')
    obj_in.token = token
    mcp = obj_in.model_dump()
    # 创建mcp连接
    ok, msg = await mcp_manager.connect(mcp)
    if not ok:
        return Fail(code=400, msg=f'重启MCP服务失败: {msg}')
    result = mcp_manager.get_connection_status(mcp.get('endpoint_id'))
    obj_in.status = result.get('status', '')
    obj = await mcp_tool_controller.create(obj_in)
    data = await obj.to_dict()
    return Success(data=data)


@router.post('/mcp-tool/update', summary='更新MCP工具')
async def update_mcp_tool(
    obj_in: McpToolUpdate,
):
    obj = await mcp_tool_controller.get(id=obj_in.id)
    if not obj:
        return Fail(code=400, msg='MCP不存在')
    update_data = obj_in.model_dump(exclude_unset=True, exclude={'id'})
    local_only_fields = {'source', 'public', 'protocol', 'config', 'status'}
    has_remote_fields = any(field not in local_only_fields for field in update_data.keys())
    # 如果有需要远程更新的字段，则调用远端服务
    if has_remote_fields:
        res = await xz_service.update_mcp(obj_in)
        if not res or not res.get('success'):
            msg = res.get('message', '') if res else '未知'
            return Fail(code=400, msg=f'云端更新失败: {msg}')
    # 重启服务：要判断 protocol 和 config 是否有变化
    need_restart = False
    if 'protocol' in update_data and obj.protocol != obj_in.protocol:
        need_restart = True
    if 'config' in update_data and obj.config != obj_in.config:
        need_restart = True
    if need_restart:
        mcp = {
            'name': obj.name,
            'endpoint_id': obj.endpoint_id,
            'token': obj.token,
            'protocol': obj_in.protocol,
            'config': obj_in.config,
        }
        ok, msg = await mcp_manager.connect(mcp)
        if not ok:
            return Fail(code=400, msg=f'重启MCP服务失败: {msg}')
        result = mcp_manager.get_connection_status(mcp.get('endpoint_id'))
        obj_in.status = result.get('status', '')
        logger.info(f'重启MCP服务: {obj.endpoint_id}-{obj.name}')
    obj = await mcp_tool_controller.update(id=obj.id, obj_in=obj_in)
    data = await obj.to_dict()
    return Success(data=data)


@router.delete('/mcp-tool/delete', summary='删除MCP工具')
async def delete_mcp_tool(
    id: int = Query(..., description='ID'),
):
    obj = await mcp_tool_controller.get(id=id)
    if not obj:
        return Fail(code=400, msg='MCP不存在')
    # 删除manager中的服务
    mcp = await obj.to_dict()
    await mcp_manager.disconnect(mcp)
    # 删除xz-service的MCP
    res = await xz_service.delete_mcp(obj.endpoint_id)
    if not res or not res.get('success'):
        msg = res.get('message', '') if res else '未知'
        logger.error(f'删除MCP失败: {msg}')
        return Fail(code=400, msg=f'云端删除MCP失败: {msg}')
    await mcp_tool_controller.remove(id=id)
    return Success(msg='删除成功')


@router.post('/mcp-tool/start', summary='启动MCP服务')
async def start_mcp_tool(obj_in: McpToolUpdate):
    obj = await mcp_tool_controller.get(id=obj_in.id)
    if not obj:
        return Fail(code=400, msg='MCP不存在')
    mcp = await obj.to_dict()
    ok, msg = await mcp_manager.connect(mcp)
    if not ok:
        return Fail(code=400, msg=f'MCP服务启动失败: {msg}')
    result = mcp_manager.get_connection_status(mcp.get('endpoint_id'))
    await mcp_tool_controller.update(id=obj_in.id, obj_in={'status': result.get('status')})
    logger.info(f'启动MCP服务: {obj.endpoint_id}-{obj.name}')
    return Success(msg='MCP服务已启动')


@router.post('/mcp-tool/stop', summary='停止MCP服务')
async def stop_mcp_tool(obj_in: McpToolUpdate):
    obj = await mcp_tool_controller.get(id=obj_in.id)
    if not obj:
        return Fail(code=400, msg='MCP不存在')
    mcp = await obj.to_dict()
    await mcp_manager.disconnect(mcp)
    await mcp_tool_controller.update(id=obj_in.id, obj_in={'status': 'uncreated'})
    logger.info(f'停止MCP服务: {obj.endpoint_id}-{obj.name}')
    return Success(msg='MCP服务已停止')


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
        status='pending',
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
async def update_voice(obj_in: VoiceUpdate):
    voice = await Voice.get(id=obj_in.id)
    if not voice:
        return Fail(400, msg='音色不存在')
    obj = await voice_controller.update(id=obj_in.id, obj_in=obj_in)
    data = await obj.to_dict(exclude_fields=['update_at'])
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
