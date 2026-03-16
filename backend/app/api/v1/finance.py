from typing import Optional
from fastapi import APIRouter, Query
from tortoise.expressions import Q
from core.config import settings
from core.pay import payment_service
from models.finance import Recharge
from models.admin import User
from controllers.finance import (
    product_controller,
    productorder_controller,
    recharge_controller,
    gift_controller,
    pointsgrant_controller,
    pointsflow_controller,
)
from schemas.base import Fail, Success, SuccessExtra
from schemas.finance import (
    ProductCreate,
    ProductUpdate,
    ProductOrderCreate,
    RechargeCreate,
    GiftCreate,
    GiftUpdate,
)

router = APIRouter()


# ========== Product ==========


@router.get('/product/list', summary='商品列表')
async def list_product(
    page: int = Query(1, description='页码'),
    page_size: int = Query(20, description='每页数量'),
    is_public: bool = Query(None, description='是否上架'),
):
    q = Q()
    if is_public is not None:
        q &= Q(is_public=is_public)
    total, objs = await product_controller.list(page=page, page_size=page_size, search=q, order=['-id'])
    data = [await obj.to_dict() for obj in objs]
    return SuccessExtra(data=data, total=total, page=page, page_size=page_size)


@router.post('/product/create', summary='创建商品')
async def create_product(obj_in: ProductCreate):
    obj = await product_controller.create(obj_in)
    return Success(data=await obj.to_dict())


@router.post('/product/update', summary='更新商品')
async def update_product(obj_in: ProductUpdate):
    obj = await product_controller.update(obj_in.id, obj_in)
    return Success(data=await obj.to_dict())


@router.delete('/product/delete', summary='删除商品')
async def delete_product(id: int = Query(..., description='ID')):
    await product_controller.remove(id=id)
    return Success(msg='删除成功')


# ========== Order ==========


@router.get('/order/list', summary='订单列表')
async def list_order(
    page: int = Query(1, description='页码'),
    page_size: int = Query(20, description='每页数量'),
    user_id: str = Query('', description='用户ID，用于搜索'),
    status: str = Query(None, description='订单状态'),
):
    q = Q()
    if user_id:
        q &= Q(user_id=user_id)
    if status:
        q &= Q(status=status)
    total, objs = await productorder_controller.list(page=page, page_size=page_size, search=q, order=['-id'])
    data = [await obj.to_dict() for obj in objs]
    return SuccessExtra(data=data, total=total, page=page, page_size=page_size)


@router.post('/order/create', summary='创建订单')
async def create_order(obj_in: ProductOrderCreate):
    # 先验证user_id是否存在
    exists = await User.filter(user_id=obj_in.user_id).exists()
    if not exists:
        return Fail(code=404, msg='用户不存在')
    try:
        order = await productorder_controller.create_order(obj_in.user_id, obj_in.product_id)
        return Success(data=await order.to_dict())
    except ValueError as e:
        return Fail(msg=str(e))


# ========== Recharge ==========


@router.get('/recharge/list', summary='充值列表')
async def list_recharge(
    page: int = Query(1, description='页码'),
    page_size: int = Query(20, description='每页数量'),
    user_id: str = Query('', description='用户ID，用于搜索'),
    is_paid: Optional[bool] = Query(None, description='是否已支付'),
):
    q = Q()
    if user_id:
        q &= Q(user_id=user_id)
    if is_paid is not None:
        q &= Q(is_paid=is_paid)
    total, objs = await recharge_controller.list(page=page, page_size=page_size, search=q, order=['-id'])
    data = [await obj.to_dict() for obj in objs]
    return SuccessExtra(data=data, total=total, page=page, page_size=page_size)


@router.post('/recharge/create', summary='创建充值')
async def create_recharge(obj_in: RechargeCreate):
    user_id = obj_in.user_id
    amount = obj_in.amount
    payment_method = obj_in.payment_method
    # 先验证user_id是否存在
    exists = await User.filter(user_id=user_id).exists()
    if not exists:
        return Fail(code=404, msg='用户不存在')

    if payment_method not in ['wechat', 'alipay']:
        return Fail(msg='支付方式只支持wechat/alipay')
    if payment_method == 'wechat':
        return Fail(msg='微信支付待接入')
    elif payment_method == 'alipay':
        result = await payment_service.create_payment(amount=amount, subject='全息盒子')
        if result.get('success', False):
            trade_id = result['data']['out_trade_no']
            obj = await Recharge.create(
                user_id=user_id,
                amount=amount,
                payment_method=payment_method,
                points=int(amount * settings.POINTS_PRICE_RATE),
                trade_id=trade_id,
                is_paid=False,
            )
            data = await obj.to_dict(exclude_fields=['id'])
            data['qr_code'] = result['data']['qr_code']
            data['trade_id'] = trade_id
            return Success(data=data)
        else:
            return Fail(msg=result.get('error', ''))


@router.get('/recharge/', summary='查询充值订单状态')
async def get_recharge_status(trade_id: str = Query(..., description='交易ID')):
    obj = await Recharge.filter(trade_id=trade_id).first()
    if not obj:
        return Fail(msg='Invalid Order ID')
    # 查询充值状态
    if obj.payment_method == 'alipay' and not obj.is_paid:
        result = await payment_service.query_payment(out_trade_no=obj.trade_id)
        if result.get('success', False):
            if result['data'].get('trade_status', '') == 'TRADE_SUCCESS':
                obj = await recharge_controller.confirm_payment(id=obj.id)
    data = await obj.to_dict(exclude_fields=['id'])
    return Success(data=data)


# ========== Gift ==========


@router.get('/gift/list', summary='赠送列表')
async def list_gift(
    page: int = Query(1, description='页码'),
    page_size: int = Query(20, description='每页数量'),
    user_id: str = Query('', description='用户ID，用于搜索'),
    gift_type: str = Query(None, description='赠送类型'),
):
    q = Q()
    if user_id:
        q &= Q(user_id=user_id)
    if gift_type:
        q &= Q(gift_type=gift_type)
    total, objs = await gift_controller.list(page=page, page_size=page_size, search=q, order=['-id'])
    data = [await obj.to_dict() for obj in objs]
    return SuccessExtra(data=data, total=total, page=page, page_size=page_size)


@router.post('/gift/create', summary='新建赠送积分')
async def create_gift(obj_in: GiftCreate):
    # 先验证user_id是否存在
    exists = await User.filter(user_id=obj_in.user_id).exists()
    if not exists:
        return Fail(code=404, msg='用户不存在')
    gift = await gift_controller.create_gift(
        obj_in.user_id, obj_in.points, obj_in.gift_type.value, obj_in.note, obj_in.expired_at
    )
    data = await gift.to_dict()
    return Success(data=data)


@router.post('/gift/update', summary='更新赠送积分')
async def update_gift(obj_in: GiftUpdate):
    obj = await gift_controller.update(obj_in.id, obj_in)
    return Success(data=await obj.to_dict())


# ========== PointsGrant ==========


@router.get('/points-grant/list', summary='积分授予列表')
async def list_grants(
    page: int = Query(1, description='页码'),
    page_size: int = Query(20, description='每页数量'),
    user_id: str = Query('', description='用户ID，用于搜索'),
    source_type: str = Query(None, description='来源类型'),
):
    q = Q()
    if user_id:
        q &= Q(user_id=user_id)
    if source_type:
        q &= Q(source_type=source_type)
    total, objs = await pointsgrant_controller.list(page=page, page_size=page_size, search=q, order=['-id'])
    data = [await obj.to_dict() for obj in objs]
    return SuccessExtra(data=data, total=total, page=page, page_size=page_size)


# ========== PointsFlow ==========


@router.get('/points-flow/list', summary='积分流水列表')
async def list_flows(
    page: int = Query(1, description='页码'),
    page_size: int = Query(20, description='每页数量'),
    user_id: str = Query('', description='用户ID，用于搜索'),
    flow_type: str = Query(None, description='流水类型'),
):
    q = Q()
    if user_id:
        q &= Q(user_id=user_id)
    if flow_type:
        q &= Q(flow_type=flow_type)
    total, objs = await pointsflow_controller.list(page=page, page_size=page_size, search=q, order=['-id'])
    data = [await obj.to_dict() for obj in objs]
    return SuccessExtra(data=data, total=total, page=page, page_size=page_size)


@router.get('/points-balance', summary='获取用户积分余额')
async def get_balance(user_id: str = Query(..., description='用户ID')):
    balance = await pointsflow_controller.get_balance(user_id)
    return Success(data={'balance': balance})
