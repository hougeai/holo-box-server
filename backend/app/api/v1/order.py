from fastapi import APIRouter, Query
from tortoise.expressions import Q
from tortoise.transactions import in_transaction
from datetime import datetime, timedelta, timezone
from controllers import user_order_controller
from schemas.base import Fail, Success, SuccessExtra
from schemas.admin import UserOrderCreate, UserOrderUpdate
from models.admin import UserOrder
from core.config import settings
from core.log import logger

router = APIRouter()


@router.get('/list', summary='查看订单列表')
async def list_order(
    page: int = Query(1, description='页码'),
    page_size: int = Query(10, description='每页数量'),
    user_id: str = Query('', description='用户ID，用于查询'),
    role_id: int = Query(None, description='角色ID，用于查询'),
    payment_period: str = Query(None, description='支付周期，用于查询'),
    is_expired: bool = Query(None, description='是否已过期，用于查询'),
):
    q = Q()
    if user_id:
        q &= Q(user_id=user_id)
    if role_id:
        q &= Q(role_id=role_id)
    if payment_period:
        q &= Q(payment_period=payment_period)
    if is_expired is not None:
        q &= Q(is_expired=is_expired)
    total, objs = await user_order_controller.list(page=page, page_size=page_size, search=q, order=['-id'])
    data = [await obj.to_dict(exclude_fields=['id']) for obj in objs]
    return SuccessExtra(data=data, total=total, page=page, page_size=page_size)


@router.post('/create', summary='创建订单')
async def create_order(obj_in: UserOrderCreate):
    # 前端已判断余额是否充足
    time_delta = 30 if obj_in.payment_period == 'monthly' else 365
    # 先找到obj对应的user_id的所有未过期订单，在最新的基础上加上time_delta天
    exist_orders = await UserOrder.filter(user_id=obj_in.user_id, role_id=obj_in.role_id, is_expired=False).order_by(
        '-expire_at'
    )
    if exist_orders:
        obj_in.expire_at = exist_orders[0].expire_at + timedelta(days=time_delta)
    else:
        # 统一用utc创建对象,Tortoise 会自动处理时区转换
        obj_in.expire_at = datetime.now(timezone.utc) + timedelta(days=time_delta)
    try:
        # 在事务tx中执行所有数据库操作，确保要么全部成功，要么全部失败
        async with in_transaction(settings.TORTOISE_ORM['apps']['models']['default_connection']) as tx:
            # 1.生成订单
            obj = await UserOrder.create(
                user_id=obj_in.user_id,
                role_id=obj_in.role_id,
                payment_period=obj_in.payment_period,
                amount=obj_in.amount,
                expire_at=obj_in.expire_at,
                using_db=tx,
            )
            # 需要重新从数据库查询，确保时区转换正确
            obj = await user_order_controller.get(id=obj.id)
            data = await obj.to_dict(exclude_fields=['id'])
            return Success(data=data, msg='Created Successfully')
    except Exception as e:
        logger.error(f'处理订单时出错：{str(e)}')
        return Fail(code=500, msg=f'处理订单时出错: {str(e)}')


@router.post('/update', summary='更新订单')
async def update_order(obj_in: UserOrderUpdate):
    await user_order_controller.update(id=obj_in.id, obj_in=obj_in)
    return Success(msg='Updated Successfully')


@router.delete('/delete', summary='删除订单')
async def delete_order(
    id: int = Query(..., description='ID'),
):
    try:
        await user_order_controller.remove(id=id)
        return Success(msg='Deleted Successfully')
    except Exception as e:
        return Fail(msg=str(e))
