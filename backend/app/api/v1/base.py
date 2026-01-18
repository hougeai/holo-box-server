import jwt
import json
import aiohttp
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Request
from core.config import settings
from core.background import CTX_USER_ID
from core.dependency import DependAuth
from core.security import create_token, get_password_hash, verify_password
from core.verifycode import RedisManager
from core.log import logger
from controllers import user_controller
from models.admin import Api, Menu, RoleApi, RoleMenu
from schemas.base import Fail, Success
from schemas.login import (
    CredentialsSchema,
    JWTPayload,
    JWTOut,
    WxLoinRequest,
)
from schemas.admin import UserCreate, UpdatePassword

router = APIRouter()
code_manager = RedisManager()


def generate_token_response(user, remember: bool = False, token_only: bool = False):
    # 生成过期时间
    access_token_expires = timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    access_expire = datetime.now(timezone.utc) + access_token_expires
    access_token = create_token(
        data=JWTPayload(
            user_id=user.user_id,
            exp=access_expire,
        )
    )
    if token_only:
        return access_token
    data = JWTOut(
        access_token=access_token,
        user_id=user.user_id,
    )
    # 将 Pydantic 模型的所有字段转换为 Python 字典
    response = Success(data=data.model_dump())
    refresh_token_expires = timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)
    refresh_expire = datetime.now(timezone.utc) + refresh_token_expires
    refresh_token = create_token(data=JWTPayload(user_id=user.user_id, exp=refresh_expire))
    if remember:
        max_age = settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
    else:
        max_age = None
    response.set_cookie(
        key='refresh_token',
        value=refresh_token,
        httponly=True,
        secure=False if settings.ENVIRONMENT == 'dev' else True,
        max_age=max_age,
        samesite='none',
    )
    return response


@router.post('/access_token', summary='获取token')
async def access_token(credentials: CredentialsSchema):
    # 验证用户名和密码
    user = await user_controller.authenticate(credentials)
    # 更新最后登录时间
    await user_controller.update_last_login(user.user_id)
    return generate_token_response(user, credentials.remember)


@router.post('/refresh_token', summary='刷新token')
async def refresh_token(request: Request):
    # 从cookie中获取refresh_token
    refresh_token = request.cookies.get('refresh_token')
    if not refresh_token:
        return Fail(msg='refresh token不存在')
    try:
        payload = jwt.decode(
            refresh_token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
            options={'verify_exp': True},
        )
        # 检查是否有用户信息
        if not payload.get('user_id', ''):
            return Fail(msg='无效的refresh token')
        user_id = payload['user_id']
        user = await user_controller.get_by_user_id(user_id)
        if not user:
            return Fail(msg='用户不存在')

        # 生成新的access token
        access_token_expires = timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
        access_expire = datetime.now(timezone.utc) + access_token_expires

        data = JWTOut(
            access_token=create_token(
                data=JWTPayload(
                    user_id=user.user_id,
                    exp=access_expire,
                )
            ),
            user_id=user.user_id,
        )
        return Success(data=data.model_dump())
    except jwt.ExpiredSignatureError:
        return Fail(msg='refresh token已过期')
    except jwt.InvalidTokenError:
        return Fail(msg='无效的refresh token')
    except Exception as e:
        return Fail(msg=f'token验证失败: {str(e)}')


@router.get('/userinfo', summary='查看用户信息', dependencies=[DependAuth])
async def get_userinfo():
    user_id = CTX_USER_ID.get()  # 保证用户身份的一致性；AuthControl中set
    user_obj = await user_controller.get_by_user_id(user_id)
    if not user_obj:
        return Fail(msg='用户不存在')
    data = await user_obj.to_dict(exclude_fields=['password', 'id'])
    return Success(data=data)


@router.get('/usermenu', summary='查看用户菜单', dependencies=[DependAuth])
async def get_user_menu():
    user_id = CTX_USER_ID.get()
    user_obj = await user_controller.get_by_user_id(user_id)
    if not user_obj:
        return Fail(msg='用户不存在')
    menus: list[Menu] = []
    if user_obj.is_superuser:
        menus = await Menu.all()
    else:
        role_menus = await RoleMenu.filter(role_id=user_obj.role_id).all()
        menu_ids = [role_menu.menu_id for role_menu in role_menus]
        menus = await Menu.filter(id__in=menu_ids).all()

    parent_menus: list[Menu] = []
    for menu in menus:
        if menu.parent_id == 0:
            parent_menus.append(menu)
    res = []
    for parent_menu in parent_menus:
        parent_menu_dict = await parent_menu.to_dict()
        parent_menu_dict['children'] = []
        for menu in menus:
            if menu.parent_id == parent_menu.id:
                parent_menu_dict['children'].append(await menu.to_dict())
        res.append(parent_menu_dict)
    return Success(data=res)


@router.get('/userapi', summary='查看用户API', dependencies=[DependAuth])
async def get_user_api():
    user_id = CTX_USER_ID.get()
    user_obj = await user_controller.get_by_user_id(user_id)
    if not user_obj:
        return Fail(msg='用户不存在')
    if user_obj.is_superuser:
        api_objs: list[Api] = await Api.all()
        apis = [api.method.lower() + api.path for api in api_objs]
        return Success(data=apis)
    role_apis = await RoleApi.filter(role_id=user_obj.role_id).all()
    api_ids = [ra.api_id for ra in role_apis]
    api_objs = await Api.filter(id__in=api_ids).all()
    apis = [api.method.lower() + api.path for api in api_objs]
    return Success(data=apis)


@router.post('/update_password', summary='修改密码', dependencies=[DependAuth])
async def update_user_password(request: UpdatePassword):
    user_id = CTX_USER_ID.get()
    user = await user_controller.get_by_user_id(user_id)
    if not user:
        return Fail(msg='用户不存在')
    verified = verify_password(request.old_password, user.password)
    if not verified:
        return Fail(msg='旧密码验证错误！')
    user.password = get_password_hash(request.new_password)
    await user.save()
    return Success(msg='修改成功')


# 小程序用户注册登录
@router.post('/wx_login', summary='小程序用户注册登录')
async def wx_login(request: WxLoinRequest):
    params = {
        'appid': settings.MP_APPID,
        'secret': settings.MP_SECRET,
        'js_code': request.code,
        'grant_type': 'authorization_code',
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get('https://api.weixin.qq.com/sns/jscode2session', params=params) as response:
                if response.status != 200:
                    logger.error(f'请求微信服务器失败: {response.status}')
                    return Fail(msg=f'请求微信服务器失败: {response.status}')
                response_text = await response.text()
                try:
                    data = json.loads(response_text)
                    logger.info(f'微信服务器返回: {data}')
                except json.JSONDecodeError:
                    logger.error(f'微信服务器返回非JSON格式: {response_text}')
                    return Fail(msg=f'微信服务器返回非JSON格式: {response_text}')
                openid = data.get('openid', None)
                if not openid:
                    return Fail(msg=f'微信服务器返回错误: {data.get("errmsg")}')
                # 查库：如果没有则注册
                user = await user_controller.get_by_openid(openid)
                if not user:
                    obj = UserCreate(openid=openid, user_name='微信用户')
                    user = await user_controller.create_user(obj)
                access_token = generate_token_response(user, token_only=True)
                data['user_id'] = user.user_id
                data['access_token'] = access_token
                return Success(data=data)
    except Exception as e:
        logger.error(f'请求微信服务器失败: {e}')
        return Fail(msg=f'请求微信服务器失败: {e}')
