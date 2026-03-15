from typing import Optional
from pydantic import BaseModel, Field, EmailStr
from models.enums import MethodType, MenuType


# 用户相关
class UserCreate(BaseModel):
    user_id: Optional[str] = Field(default=None, example='user123')
    user_name: str = Field(example='admin')
    password: Optional[str] = Field(default=None, example='123456ai')
    email: Optional[EmailStr] = Field(default=None, example='admin@qq.com')
    wxid: Optional[str] = Field(default=None, example='admin')
    openid: Optional[str] = Field(default=None, example='admin')
    phone: Optional[str] = Field(default=None, example='12345678901')
    avatar: Optional[str] = Field(default=None, example='https://avatars.githubusercontent.com/u/23102037?s=96&v=4')
    is_active: Optional[bool] = Field(default=True)
    role_id: Optional[int] = Field(default=3, example=3)


class UserUpdate(BaseModel):
    user_id: Optional[str] = None
    user_name: Optional[str] = None
    email: Optional[EmailStr] = None
    wxid: Optional[str] = None
    openid: Optional[str] = None
    phone: Optional[str] = None
    avatar: Optional[str] = None
    is_active: Optional[bool] = None
    role_id: Optional[int] = None


class UpdatePassword(BaseModel):
    old_password: str = Field(description='旧密码')
    new_password: str = Field(description='新密码')


# 角色相关
class BaseRole(BaseModel):
    id: int
    name: str
    desc: str = ''
    users: Optional[list] = []
    menus: Optional[list] = []
    apis: Optional[list] = []


class RoleCreate(BaseModel):
    name: str = Field(example='管理员')
    desc: str = Field(default='', example='管理员角色')
    max_devices: Optional[int] = Field(default=1, example=1)
    max_alarms: Optional[int] = Field(default=1, example=1)
    max_dailyplay: Optional[int] = Field(default=3, example=3)
    max_playlist: Optional[int] = Field(default=0, example=0)
    max_upload_songs: Optional[int] = Field(default=0, example=0)
    max_apikeys: Optional[int] = Field(default=1, example=1)
    kb_file_quota: Optional[int] = Field(default=0, example=0)
    kb_storage_quota: Optional[int] = Field(default=0, example=0)
    kb_dify_limit: Optional[int] = Field(default=0, example=0)
    price_monthly: Optional[float] = Field(default=0, example=0)
    price_yearly: Optional[float] = Field(default=0, example=0)


class RoleUpdate(RoleCreate):
    id: int = Field(example=1)
    name: Optional[str] = None
    desc: Optional[str] = None


class RoleUpdateMenusApis(BaseModel):
    id: int
    menu_ids: list[int] = []
    api_infos: list[dict] = []


# Api相关
class BaseApi(BaseModel):
    path: str = Field(..., description='API路径', example='/api/v1/user/list')
    summary: str = Field(default='', description='API简介', example='查看用户列表')
    method: MethodType = Field(..., description='API方法', example='GET')
    tags: str = Field(..., description='API标签', example='User')


# ... 是 pass 的一种简写
class ApiCreate(BaseApi): ...


class ApiUpdate(BaseApi):
    id: int


# menu相关
class BaseMenu(BaseModel):
    id: int
    name: str
    path: str
    remark: Optional[dict]
    menu_type: Optional[MenuType]
    icon: Optional[str]
    order: int
    parent_id: int
    hidden: bool
    component: str
    keepalive: bool
    redirect: Optional[str]
    children: Optional[list['BaseMenu']]


class MenuCreate(BaseModel):
    name: str = Field(example='用户管理')
    path: str = Field(example='/system/user')
    menu_type: MenuType = Field(default=MenuType.CATALOG.value)
    icon: Optional[str] = 'ph:user-list-bold'
    order: Optional[int] = Field(example=1)
    parent_id: Optional[int] = Field(example=0, default=0)
    hidden: Optional[bool] = False
    component: str = Field(default='Layout', example='/system/user')
    keepalive: Optional[bool] = True
    redirect: Optional[str] = ''


class MenuUpdate(MenuCreate):
    id: int
    name: Optional[str] = None
    path: Optional[str] = None
    menu_type: Optional[MenuType] = None


# 系统配置相关
class SystemConfigCreate(BaseModel):
    key: str = Field(description='配置键', example='register_gift')
    value: str = Field(description='配置值', example='100')
    note: Optional[str] = Field(default=None, description='备注', example='注册赠送积分')


class SystemConfigUpdate(BaseModel):
    id: int = Field(description='配置ID')
    key: Optional[str] = None
    value: Optional[str] = None
    note: Optional[str] = None
