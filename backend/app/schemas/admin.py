from typing import Optional, List
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


class FeedBackCreate(BaseModel):
    user_id: str = Field(..., description='用户ID')
    feed_type: str = Field(..., description='反馈类型', example='BUG')
    summary: str = Field(..., description='反馈内容', example='用户列表页面显示异常')


class MarkRequest(BaseModel):
    ids: List[int]


# 用户订阅
class UserOrderCreate(BaseModel):
    user_id: str = Field(..., description='用户ID')
    role_id: int = Field(..., description='角色ID')
    amount: Optional[float] = Field(None, description='金额')


class UserOrderUpdate(UserOrderCreate):
    id: int = Field(..., description='订单ID')
    user_id: Optional[str] = Field(None, description='用户ID')
    role_id: Optional[int] = Field(None, description='角色ID')


# 充值相关
class RechargeCreate(BaseModel):
    user_id: str = Field(..., description='用户ID')
    amount: float = Field(..., description='充值金额，Decimal(10,2)')
    order_id: Optional[str] = Field(None, description='充值订单ID（第三方订单号）')
    payment_method: Optional[str] = Field(None, description='支付方式')
    is_paid: Optional[bool] = Field(False, description='是否已支付成功')


class RechargeUpdate(RechargeCreate):
    id: Optional[int] = Field(None, description='充值ID')
    user_id: Optional[str] = Field(None, description='用户ID')
    amount: Optional[float] = Field(None, description='充值金额，Decimal(10,2)')
