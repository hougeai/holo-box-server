from fastapi import APIRouter, Query
from tortoise.expressions import Q
from typing import Optional
from models.admin import Recharge
from schemas.base import Fail, Success, SuccessExtra
from schemas.admin import RechargeCreate, RechargeUpdate
from controllers.admin import recharge_controller


router = APIRouter()


# 充值相关
@router.get('/recharge/list', summary='充值记录列表')
async def list_recharge(
    page: int = Query(1, description='页码'),
    page_size: int = Query(10, description='每页数量'),
    user_id: str = Query('', description='用户ID，用于查询'),
    order_id: str = Query('', description='充值订单ID，用于查询'),
    payment_method: str = Query('', description='支付方式，用于查询'),
    is_paid: Optional[bool] = Query(None, description='是否已支付，用于查询'),
):
    q = Q()
    if user_id:
        q &= Q(user_id=user_id)
    if order_id:
        q &= Q(order_id=order_id)
    if payment_method:
        q &= Q(payment_method=payment_method)
    if is_paid is not None:
        q &= Q(is_paid=is_paid)
    total, objs = await recharge_controller.list(page=page, page_size=page_size, search=q, order=['-id'])
    data = [await obj.to_dict(exclude_fields=['id']) for obj in objs]
    return SuccessExtra(data=data, total=total, page=page, page_size=page_size)


@router.get('/recharge/status', summary='查询订单状态')
async def get_recharge_status(order_id: str = Query(..., description='充值订单ID')):
    obj = await Recharge.get(order_id=order_id)
    if not obj:
        return Fail(msg='Invalid Order ID')
    # 查询充值状态
    if obj.payment_method == 'alipay' and not obj.is_paid:
        result = True
        if result:
            if result['data'].get('trade_status', '') == 'TRADE_SUCCESS':
                obj.is_paid = True
                await obj.save()

    return Success(data={'is_paid': obj.is_paid}, msg='Query Successfully')


@router.post('/recharge/create', summary='创建充值记录')
async def create_recharge(obj_in: RechargeCreate):
    # TODO：调用支付接口，获取支付链接；已接入支付宝，待接入微信
    if obj_in.payment_method == 'wechat':
        return Fail(msg='微信支付待接入，可选择支付宝支付')
    return Success(msg='Created Successfully')


@router.post('/recharge/update', summary='更新充值记录')
async def update_recharge(obj_in: RechargeUpdate):
    if obj_in.id:
        obj = await recharge_controller.get(id=obj_in.id)
    elif obj_in.order_id:
        obj = await Recharge.get(order_id=obj_in.order_id)
    else:
        return Fail(msg='Order ID or ID is required')
    obj = await recharge_controller.update(id=obj.id, obj_in=obj_in)
    return Success(msg='Updated Successfully')


@router.delete('/recharge/delete', summary='删除充值记录')
async def delete_recharge(id: int = Query(..., description='充值记录ID')):
    try:
        await recharge_controller.remove(id=id)
        return Success(msg='Deleted Successfully')
    except Exception as e:
        return Fail(msg=str(e))
