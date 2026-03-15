from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field
from models.enums import GiftType, PointsFlowType


# ========== Product ==========


class ProductCreate(BaseModel):
    name: str = Field(description='商品名称')
    points_price: int = Field(description='积分价格')
    description: Optional[str] = Field(default=None, description='商品描述')
    is_public: bool = Field(default=True, description='是否上架')


class ProductUpdate(ProductCreate):
    id: int = Field(description='ID')
    name: Optional[str] = Field(default=None, description='商品名称')
    points_price: Optional[int] = Field(default=None, description='积分价格')
    is_public: Optional[bool] = Field(default=None, description='是否上架')


# ========== ProductOrder ==========


class ProductOrderCreate(BaseModel):
    user_id: str = Field(description='用户ID')
    product_id: int = Field(description='商品ID')


class ProductOrderUpdate(BaseModel):
    id: int = Field(description='ID')
    status: Optional[str] = Field(default=None, description='订单状态')


# ========== Recharge ==========


class RechargeCreate(BaseModel):
    user_id: str = Field(description='用户ID')
    amount: float = Field(description='充值金额')
    payment_method: str = Field(description='支付方式')


class RechargeUpdate(BaseModel):
    id: int = Field(description='ID')
    is_paid: Optional[bool] = Field(default=None, description='是否已支付')


# ========== Gift ==========


class GiftCreate(BaseModel):
    user_id: str = Field(description='用户ID')
    points: int = Field(description='赠送积分')
    gift_type: GiftType = Field(description='赠送类型')
    expired_at: Optional[datetime] = Field(default=None, description='过期时间')
    note: Optional[str] = Field(default=None, description='备注')


class GiftUpdate(BaseModel):
    id: int = Field(description='ID')
    points: Optional[int] = Field(default=None, description='赠送积分')
    gift_type: Optional[GiftType] = Field(default=None, description='赠送类型')
    expired_at: Optional[datetime] = Field(default=None, description='过期时间')
    note: Optional[str] = Field(default=None, description='备注')


# ========== PointsGrant ==========
class PointsGrantCreate(BaseModel):
    user_id: str = Field(description='用户ID')
    amount: int = Field(description='剩余可用积分')
    expired_at: Optional[datetime] = Field(default=None, description='过期时间')


class PointsGrantUpdate(BaseModel):
    id: int = Field(description='ID')
    expired_at: Optional[datetime] = Field(default=None, description='过期时间')


# ========== PointsFlow ==========
class PointsFlowCreate(BaseModel):
    user_id: str = Field(description='用户ID')
    flow_type: PointsFlowType = Field(description='流水类型')
    amount: int = Field(description='积分数额（正数增加，负数扣减）')
    balance: int = Field(description='变动后余额')
    grant_ids: Optional[list[int]] = Field(default=None, description='关联的积分授予ID列表')
    order_id: Optional[int] = Field(default=None, index=True, description='关联的订单ID，仅当流水类型是order时有值')


class PointsFlowUpdate(PointsFlowCreate):
    id: int = Field(description='ID')
