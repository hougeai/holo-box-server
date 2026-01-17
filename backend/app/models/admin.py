from tortoise import fields
from tortoise.exceptions import IntegrityError
from nanoid import generate
from .base import BaseModel, TimestampMixin
from .enums import MethodType, MenuType


class User(BaseModel, TimestampMixin):
    user_id = fields.CharField(
        max_length=12, null=True, unique=True, pk=False, description='用户唯一标识', index=True
    )  # 不是主键
    user_name = fields.CharField(max_length=20, description='用户名称', index=True)
    password = fields.CharField(max_length=128, null=True, description='密码')
    email = fields.CharField(max_length=255, null=True, unique=True, description='邮箱', index=True)
    wxid = fields.CharField(max_length=255, null=True, unique=True, description='微信ID，用户前端注册使用', index=True)
    openid = fields.CharField(
        max_length=255, null=True, unique=True, description='微信OpenID，用户小程序登录使用', index=True
    )
    phone = fields.CharField(max_length=20, null=True, unique=True, description='电话', index=True)
    avatar = fields.CharField(max_length=255, null=True, description='头像')
    is_active = fields.BooleanField(default=True, description='是否活跃', index=True)  # 冻结用户
    last_login = fields.DatetimeField(null=True, description='最后登录时间', index=False)
    role_id = fields.IntField(null=True, description='角色ID', index=True)
    is_del = fields.BooleanField(default=False, description='是否注销')

    class Meta:
        table = 'user'

    @property
    def is_superuser(self) -> bool:
        return self.role_id == 1

    async def save(self, *args, **kwargs):
        if not self.user_id:
            max_attempts = 5
            while max_attempts > 0:
                self.user_id = generate(size=8)
                try:
                    return await super().save(*args, **kwargs)
                except IntegrityError:
                    max_attempts -= 1
            raise ValueError('Failed to generate unique userid after attempts')
        return await super().save(*args, **kwargs)


class Role(BaseModel, TimestampMixin):
    name = fields.CharField(max_length=20, unique=True, description='角色名称', index=True)
    desc = fields.CharField(max_length=500, null=True, description='角色描述')
    # 配额限制字段
    max_agents = fields.IntField(default=1, description='最大智能体创建数量')
    # 会员价格字段：max_digits 10位数字，小数点后保留2位；Decimal 字段是处理金融数据的标准做法，避免舍入误差
    price_figure = fields.DecimalField(max_digits=10, decimal_places=2, default=0, description='创建形象价格')

    class Meta:
        table = 'role'

    async def get_authorizations(self):
        """
        获取角色关联的menu和API
        """
        # 获取关联的菜单ID列表
        role_menus = await RoleMenu.filter(role_id=self.id).all()
        menu_ids = [rm.menu_id for rm in role_menus]

        # 获取关联的API ID列表
        role_apis = await RoleApi.filter(role_id=self.id).all()
        api_ids = [ra.api_id for ra in role_apis]

        # 获取菜单和API的详细信息（可选）
        menus = await Menu.filter(id__in=menu_ids).all()
        apis = await Api.filter(id__in=api_ids).all()

        return {
            'menus': [await menu.to_dict() for menu in menus],
            'apis': [await api.to_dict() for api in apis],
        }


class Api(BaseModel, TimestampMixin):
    path = fields.CharField(max_length=100, description='API路径', index=True)
    method = fields.CharEnumField(MethodType, description='请求方法', index=True)
    summary = fields.CharField(max_length=500, description='请求简介', index=True)
    tags = fields.CharField(max_length=100, description='API标签', index=True)

    class Meta:
        table = 'api'


class Menu(BaseModel, TimestampMixin):
    name = fields.CharField(max_length=20, description='菜单名称', index=True)
    path = fields.CharField(max_length=100, description='菜单路径', index=True)
    remark = fields.JSONField(null=True, description='保留字段')
    menu_type = fields.CharEnumField(MenuType, null=True, description='菜单类型')
    icon = fields.CharField(max_length=100, null=True, description='菜单图标')
    order = fields.IntField(default=0, description='排序', index=True)
    parent_id = fields.IntField(default=0, description='父菜单ID', index=True)
    hidden = fields.BooleanField(default=False, description='是否隐藏')
    component = fields.CharField(max_length=100, description='组件')
    keepalive = fields.BooleanField(default=True, description='存活')
    redirect = fields.CharField(max_length=100, null=True, description='重定向')

    class Meta:
        table = 'menu'


class RoleMenu(BaseModel):
    role_id = fields.IntField(description='角色ID')
    menu_id = fields.IntField(description='菜单ID')

    class Meta:
        table = 'role_menu'


class RoleApi(BaseModel):
    role_id = fields.IntField(description='角色ID')
    api_id = fields.IntField(description='API ID')

    class Meta:
        table = 'role_api'


class AuditLog(BaseModel, TimestampMixin):
    user_id = fields.CharField(max_length=12, null=True, description='用户ID', index=True)
    module = fields.CharField(max_length=64, default='', description='功能模块', index=True)
    summary = fields.CharField(max_length=128, default='', description='请求描述', index=True)
    method = fields.CharField(max_length=10, default='', description='请求方法', index=True)
    path = fields.CharField(max_length=255, default='', description='请求路径', index=True)
    status = fields.IntField(default=-1, description='状态码', index=True)
    latency = fields.IntField(default=0, description='响应时间(单位ms)', index=True)
    args = fields.JSONField(null=True, description='请求参数')
    body = fields.JSONField(null=True, description='返回数据')


# 充值表
class Recharge(BaseModel, TimestampMixin):
    user_id = fields.CharField(max_length=12, index=True, description='用户ID')
    amount = fields.DecimalField(max_digits=10, decimal_places=2, index=True, description='充值金额')
    order_id = fields.CharField(max_length=100, index=True, description='充值订单ID')
    payment_method = fields.CharField(max_length=20, index=True, description='支付方式')
    is_paid = fields.BooleanField(
        default=False, index=True, description='是否已支付'
    )  # 只有支付成功才会写入BalanceFlow

    class Meta:
        indexes = [
            ('user_id', 'is_paid'),
        ]


# 订单表
class UserOrder(BaseModel, TimestampMixin):
    user_id = fields.CharField(max_length=12, index=True, description='用户ID')
    role_id = fields.IntField(index=True, description='角色ID')
    amount = fields.DecimalField(max_digits=10, decimal_places=2, null=True, description='金额')

    class Meta:
        # 联合索引，优化查询性能
        indexes = [
            ('user_id', 'role_id'),
        ]
