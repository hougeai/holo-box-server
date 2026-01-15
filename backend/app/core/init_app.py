import os
import json
import shutil
from aerich import Command
from fastapi import FastAPI
from fastapi.middleware import Middleware
from fastapi.middleware.cors import CORSMiddleware
from tortoise.expressions import Q
from api import api_router, ota_router
from models.admin import Api, Menu, Role, RoleMenu, RoleApi
from models.agent import AgentTemplate
from models.device import Device
from models.resource import Ota
from models.enums import MenuType
from schemas.admin import UserCreate
from controllers import api_controller, user_controller
from .exceptions import (
    DoesNotExist,
    DoesNotExistHandle,
    HTTPException,
    HttpExcHandle,
    IntegrityError,
    IntegrityHandle,
    RequestValidationError,
    RequestValidationHandle,
    ResponseValidationError,
    ResponseValidationHandle,
)
from .log import logger
from .config import settings
from .middlewares import BackGroundTaskMiddleware, HttpAuditLogMiddleware, OTACORSMiddleware


def make_middlewares():
    middleware = [
        Middleware(
            CORSMiddleware,
            allow_origins=[
                settings.ADMIN_FE_URL,
                settings.USER_FE_URL,
                'http://localhost:8077',
                'http://localhost:8078',
            ],
            allow_credentials=True,
            allow_methods=['*'],
            allow_headers=['*'],
        ),
        Middleware(OTACORSMiddleware),  # 添加自定义OTA CORS中间件
        Middleware(BackGroundTaskMiddleware),
        Middleware(
            HttpAuditLogMiddleware,
            methods=['GET', 'POST', 'PUT', 'DELETE'],
            exclude_paths=[
                '/api/v1/base/access_token',
                '/docs',
                '/redoc',
                '/openapi.json',
                r'^/static/.*',
                r'^/$',
                '/favicon.ico',
                '/ota',
            ],
        ),
    ]
    return middleware


def register_exceptions(app: FastAPI):
    app.add_exception_handler(DoesNotExist, DoesNotExistHandle)
    app.add_exception_handler(HTTPException, HttpExcHandle)
    app.add_exception_handler(IntegrityError, IntegrityHandle)
    app.add_exception_handler(RequestValidationError, RequestValidationHandle)
    app.add_exception_handler(ResponseValidationError, ResponseValidationHandle)


def register_routers(app: FastAPI):
    app.include_router(api_router, prefix='/api')
    app.include_router(ota_router)


async def init_db():
    command = Command(tortoise_config=settings.TORTOISE_ORM)
    try:
        await command.init_db(safe=True)  # 初始化数据库，safe=True 表示如果表已存在则跳过
    except FileExistsError:
        pass

    await command.init()  # 初始化 migrations 目录和配置
    try:
        await command.migrate()  # 根据模型变化生成迁移文件
    except AttributeError:
        # 如果获取不到历史记录，则重新初始化
        logger.warning('unable to retrieve model history from database, model history will be created from scratch')
        shutil.rmtree('migrations')  # 删除旧的迁移文件
        await command.init_db(safe=True)  # 重新初始化

    await command.upgrade(run_in_transaction=True)


async def init_menus():
    # 每次重启删除所有菜单并重新创建
    await Menu.all().delete()
    parent_menu = await Menu.create(
        menu_type=MenuType.CATALOG,
        name='系统管理',
        path='/system',
        order=1,
        parent_id=0,
        icon='carbon:gui-management',
        hidden=False,
        component='Layout',
        keepalive=False,
        redirect='/system/user',
    )
    children_menu = [
        Menu(
            menu_type=MenuType.MENU,
            name='用户管理',
            path='user',
            order=1,
            parent_id=parent_menu.id,
            icon='material-symbols:person-outline-rounded',
            hidden=False,
            component='/system/user',
            keepalive=False,
        ),
        Menu(
            menu_type=MenuType.MENU,
            name='角色管理',
            path='role',
            order=2,
            parent_id=parent_menu.id,
            icon='carbon:user-role',
            hidden=False,
            component='/system/role',
            keepalive=False,
        ),
        Menu(
            menu_type=MenuType.MENU,
            name='审计日志',
            path='auditlog',
            order=3,
            parent_id=parent_menu.id,
            icon='ph:clipboard-text-bold',
            hidden=False,
            component='/system/auditlog',
            keepalive=False,
        ),
    ]
    await Menu.bulk_create(children_menu)

    parent_menu = await Menu.create(
        menu_type=MenuType.CATALOG,
        name='资源管理',
        path='/resource',
        order=2,
        parent_id=0,
        icon='material-symbols:featured-play-list-outline',
        hidden=False,
        component='Layout',
        keepalive=False,
        redirect='/resource/device',
    )
    children_menu = [
        Menu(
            menu_type=MenuType.MENU,
            name='智能体模板管理',
            path='agentTemplate',
            order=1,
            parent_id=parent_menu.id,
            icon='material-symbols:support-agent',
            hidden=False,
            component='/resource/agentTemplate',
            keepalive=False,
        ),
        Menu(
            menu_type=MenuType.MENU,
            name='智能体管理',
            path='agent',
            order=2,
            parent_id=parent_menu.id,
            icon='material-symbols-light:support-agent',
            hidden=False,
            component='/resource/agent',
            keepalive=False,
        ),
        Menu(
            menu_type=MenuType.MENU,
            name='设备管理',
            path='device',
            order=3,
            parent_id=parent_menu.id,
            icon='material-symbols-light:devices',
            hidden=False,
            component='/resource/device',
            keepalive=False,
        ),
        Menu(
            menu_type=MenuType.MENU,
            name='OTA版本管理',
            path='ota',
            order=4,
            parent_id=parent_menu.id,
            icon='ant-design:api-outlined',
            hidden=False,
            component='/resource/ota',
            keepalive=False,
        ),
    ]
    await Menu.bulk_create(children_menu)

    parent_menu = await Menu.create(
        menu_type=MenuType.CATALOG,
        name='用户中心',
        path='/user',
        order=3,
        parent_id=0,
        icon='material-symbols:person',
        hidden=False,
        component='Layout',
        keepalive=False,
        redirect='/user/order',
    )
    children_menu = [
        Menu(
            menu_type=MenuType.MENU,
            name='订单管理',
            path='order',
            order=1,
            parent_id=parent_menu.id,
            icon='material-symbols:assignment-outline',
            hidden=False,
            component='/user/order',
            keepalive=False,
        ),
        Menu(
            menu_type=MenuType.MENU,
            name='充值管理',
            path='recharge',
            order=2,
            parent_id=parent_menu.id,
            icon='material-symbols:money-bag',
            hidden=False,
            component='/user/recharge',
            keepalive=False,
        ),
    ]
    await Menu.bulk_create(children_menu)


async def init_apis(app: FastAPI):
    # 每次重启都要刷新api
    await api_controller.refresh_api(app)


async def init_roles():
    roles = await Role.exists()
    if not roles:
        init_roles = [
            ('超级管理员', '拥有系统所有权限，可管理所有用户和设置'),
            ('管理员', '拥有管理权限，可管理普通用户和部分设置'),
            ('普通会员', '基础用户权限，可使用所有核心功能'),
        ]
        role_objs = [Role(name=n, desc=d) for n, d in init_roles]
        await Role.bulk_create(role_objs)

    # 分配所有API给超级管理员-先清空再重新赋值
    super_admin = await Role.get(name='超级管理员').first()
    await RoleApi.filter(role_id=super_admin.id).delete()
    all_apis = await Api.all()
    role_api_objects = [RoleApi(role_id=super_admin.id, api_id=api.id) for api in all_apis]
    await RoleApi.bulk_create(role_api_objects)

    # 分配所有菜单给超级管理员
    await RoleMenu.filter(role_id=super_admin.id).delete()
    all_menus = await Menu.all()
    role_menu_objects = [RoleMenu(role_id=super_admin.id, menu_id=menu.id) for menu in all_menus]
    await RoleMenu.bulk_create(role_menu_objects)

    # 为会员分配基本API和用户信息更新API
    member_roles = await Role.filter(name__in=['普通会员']).all()
    basic_apis = await Api.filter(
        Q(method__in=['GET'])
        | Q(tags='基础模块')
        | Q(tags='设备模块')
        | Q(tags='智能体模块')
        | Q(tags='资源模块')
        | Q(tags='通知模块')
        | Q(tags='订单模块')
        | Q(tags='API密钥模块')
        | Q(tags='资金模块')
    )
    user_update_api = await Api.filter(method='POST', tags='用户模块', summary='更新用户')
    all_apis = list(basic_apis) + list(user_update_api)
    for role in member_roles:
        await RoleApi.filter(role_id=role.id).delete()
        role_api_objects = [RoleApi(role_id=role.id, api_id=api.id) for api in all_apis]
        await RoleApi.bulk_create(role_api_objects)


async def init_superuser():
    user = await user_controller.model.exists()
    if not user:
        await user_controller.create_user(
            UserCreate(
                user_id='1',
                user_name=settings.SUPER_ADMIN_NAME,
                password=settings.SUPER_ADMIN_PASSWORD,
                email=settings.SUPER_ADMIN_EMAIL,
                avatar='https://avatars.githubusercontent.com/u/23102037?s=96&v=4',
                is_active=True,
                role_id=1,
            )
        )


async def init_device():
    obj = await Device.exists()
    if not obj:
        await Device.create(
            device_id='97:3d:ae:e6:83:d0',
            uuid='ab4ad1e9-0299-4880-9b0d-b96ea0a2bf3e',
            location='上海市静安区',
            chip_type='esp32s3',
            device_model='holo-box-wifi',
            app_version='2.1.0',
            user_id='1',
        )


async def init_ota():
    obj = await Ota.exists()
    if not obj:
        objs = [
            Ota(
                app_version='2.1.0',
                chip_type='esp32s3',
                device_model='holo-box-wifi',
                ota_url='firmware/holo-box-wifi-2.1.0.bin',
            ),
        ]
        await Ota.bulk_create(objs)


async def init_agent_template():
    obj = await AgentTemplate.exists()
    if not obj:
        dir_path = os.path.dirname(os.path.abspath(__file__))
        agent_file = os.path.join(dir_path, '../data/agent.json')
        agents = json.load(open(agent_file, 'r', encoding='utf-8'))
        objs = [
            AgentTemplate(
                user_id='1',
                agent_name=agent['agentName'],
                system_prompt=agent['systemPrompt'],
                avatar=agent['avatar'],
                tags=agent['tags'],
            )
            for agent in agents
        ]
        await AgentTemplate.bulk_create(objs)


async def init_data(app: FastAPI):
    await init_db()
    await init_menus()
    await init_apis(app)
    await init_roles()
    await init_superuser()
    await init_device()
    await init_ota()
    await init_agent_template()
