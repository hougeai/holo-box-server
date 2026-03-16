from tortoise import fields
from core.config import settings
from .base import BaseModel, TimestampMixin
from .enums import GiftType, PointsFlowType


# 商品表
class Product(BaseModel, TimestampMixin):
    key = fields.CharField(max_length=50, unique=True, index=True, description='商品唯一标识')
    name = fields.CharField(max_length=100, description='商品名称')
    points_price = fields.BigIntField(description='积分价格')
    description = fields.TextField(null=True, description='商品描述')
    is_public = fields.BooleanField(default=True, index=True, description='是否上架')

    class Meta:
        table = 'product'


# 订单表
class ProductOrder(BaseModel, TimestampMixin):
    user_id = fields.CharField(max_length=12, index=True, description='用户ID')
    product_id = fields.BigIntField(index=True, description='商品ID')
    points = fields.BigIntField(description='消耗积分')
    status = fields.CharField(max_length=20, null=True, description='订单状态: completed/cancelled')

    class Meta:
        table = 'product_order'
        indexes = [
            ('user_id', 'status'),
        ]


# 充值表
class Recharge(BaseModel, TimestampMixin):
    user_id = fields.CharField(max_length=12, index=True, description='用户ID')
    amount = fields.DecimalField(max_digits=10, decimal_places=2, index=True, description='充值金额')
    payment_method = fields.CharField(max_length=20, null=True, description='支付方式')
    points = fields.BigIntField(description='获得积分')
    trade_id = fields.TextField(null=True, description='交易ID')
    is_paid = fields.BooleanField(default=False, index=True, description='是否已支付')

    class Meta:
        table = 'recharge'
        indexes = [
            ('user_id', 'is_paid'),
        ]


# 赠送表
class Gift(BaseModel, TimestampMixin):
    user_id = fields.CharField(max_length=12, index=True, description='用户ID')
    points = fields.BigIntField(description='赠送积分')
    gift_type = fields.CharEnumField(GiftType, description='赠送类型')
    expired_at = fields.DatetimeField(default=settings.PERMANENT_EXPIRED_AT, description='过期时间')
    note = fields.CharField(max_length=100, null=True, description='备注')

    class Meta:
        table = 'gift'


# 积分授予表
class PointsGrant(BaseModel, TimestampMixin):
    user_id = fields.CharField(max_length=12, index=True, description='用户ID')
    amount = fields.BigIntField(description='剩余可用积分')
    source_type = fields.CharField(max_length=20, description='来源类型: recharge/gift')
    source_id = fields.BigIntField(description='关联的来源记录ID（recharge.id 或 gift.id）')
    expired_at = fields.DatetimeField(default=settings.PERMANENT_EXPIRED_AT, description='过期时间')

    class Meta:
        table = 'points_grant'
        indexes = [
            ('user_id', 'amount'),  # 覆盖余额查询
            ('user_id', 'expired_at'),  # 覆盖消费排序查询
            ('source_type', 'source_id'),  # 覆盖关联查询
            ('expired_at', 'amount'),  # 覆盖过期任务查询
        ]


# 积分流水表
class PointsFlow(BaseModel, TimestampMixin):
    user_id = fields.CharField(max_length=12, index=True, description='用户ID')
    flow_type = fields.CharEnumField(PointsFlowType, description='流水类型')
    amount = fields.BigIntField(description='积分数额（正数增加，负数扣减）')
    balance = fields.BigIntField(description='变动后余额')
    grant_ids = fields.JSONField(null=True, description='关联的积分授予ID列表')
    order_id = fields.BigIntField(null=True, index=True, description='关联的订单ID，仅当流水类型是order时有值')

    class Meta:
        table = 'points_flow'
        indexes = [
            ('user_id', 'flow_type', 'id'),
        ]
