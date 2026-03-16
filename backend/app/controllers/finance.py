from datetime import datetime
from typing import Optional
from tortoise.transactions import in_transaction
from models.finance import (
    Product,
    ProductOrder,
    Recharge,
    Gift,
    PointsGrant,
    PointsFlow,
)
from models.enums import PointsFlowType
from schemas.finance import (
    ProductCreate,
    ProductUpdate,
    ProductOrderCreate,
    ProductOrderUpdate,
    RechargeCreate,
    RechargeUpdate,
    GiftCreate,
    GiftUpdate,
    PointsGrantCreate,
    PointsGrantUpdate,
    PointsFlowCreate,
    PointsFlowUpdate,
)
from .crud import CRUDBase
from core.log import logger
from core.config import settings


# ========== Product ==========
class ProductController(CRUDBase[Product, ProductCreate, ProductUpdate]):
    def __init__(self):
        super().__init__(model=Product)

    async def get_by_key(self, key: str) -> Optional[Product]:
        return await self.model.filter(key=key).first()


# ========== ProductOrder ==========
class ProductOrderController(CRUDBase[ProductOrder, ProductOrderCreate, ProductOrderUpdate]):
    def __init__(self):
        super().__init__(model=ProductOrder)

    async def create_order(self, user_id: str, product_id: int) -> ProductOrder:
        """创建订单并扣减积分"""
        # 获取商品
        product = await Product.get(id=product_id)
        if not product or not product.is_public:
            raise ValueError('商品不存在或已下架')
        async with in_transaction(settings.TORTOISE_ORM['apps']['models']['default_connection']) as conn:
            return await self.create_order_in_transaction(user_id, product, conn)

    async def create_order_in_transaction(self, user_id, product, conn) -> ProductOrder:
        """在事务中创建订单的核心逻辑"""
        # 扣减积分（包含余额检查）
        consumed_grant_ids = await self._consume_points(user_id, product.points_price, conn)

        # 获取扣减后的余额
        balance = await pointsflow_controller.get_balance(user_id, conn)
        new_balance = balance - product.points_price

        # 创建订单
        order = await ProductOrder.create(
            user_id=user_id,
            product_id=product.id,
            points=product.points_price,
            status='completed',
            using_db=conn,
        )

        # 记录积分流水
        await PointsFlow.create(
            user_id=user_id,
            flow_type=PointsFlowType.ORDER,
            amount=-product.points_price,
            balance=new_balance,
            grant_ids=consumed_grant_ids,
            order_id=order.id,
            using_db=conn,
        )
        return order

    async def _consume_points(self, user_id: str, points: int, conn) -> list[int]:
        """消费积分，优先消耗快过期的"""
        # 1. 使用 select_for_update 加行锁，防止并发问题
        grants = (
            await PointsGrant.filter(user_id=user_id, amount__gt=0)
            .select_for_update()
            .order_by('expired_at')
            .using_db(conn)
            .all()
        )
        # 2. 计算总可用余额
        total_available = sum(g.amount for g in grants)
        if total_available < points:
            raise ValueError('积分不足')

        consumed_ids = []
        remaining = points

        for grant in grants:
            if remaining <= 0:
                break
            available = grant.amount
            if available > remaining:
                consumed_ids.append(grant.id)
                grant.amount -= remaining
                await grant.save(using_db=conn)
                remaining = 0
            else:
                consumed_ids.append(grant.id)
                remaining -= available
                grant.amount = 0
                await grant.save(using_db=conn)
        return consumed_ids


# ========== Recharge ==========
class RechargeController(CRUDBase[Recharge, RechargeCreate, RechargeUpdate]):
    def __init__(self):
        super().__init__(model=Recharge)

    async def confirm_payment(self, id: int) -> Recharge:
        """确认支付并添加积分"""
        recharge = await Recharge.get(id=id)
        if not recharge:
            raise ValueError('充值记录不存在')
        if recharge.is_paid:  # 防止重复添加
            return recharge
        async with in_transaction(settings.TORTOISE_ORM['apps']['models']['default_connection']) as conn:
            recharge.is_paid = True
            await recharge.save(using_db=conn)
            await self._add_points(
                recharge.user_id, recharge.points, PointsFlowType.RECHARGE, 'recharge', recharge.id, conn
            )

        return recharge

    async def _add_points(
        self, user_id: str, points: int, flow_type: PointsFlowType, source_type: str, source_id: int, conn
    ):
        """添加积分"""
        grant = await PointsGrant.create(
            user_id=user_id,
            amount=points,
            source_type=source_type,
            source_id=source_id,
            expired_at=settings.PERMANENT_EXPIRED_AT,
            using_db=conn,
        )

        balance = await pointsflow_controller.get_balance(user_id, conn)
        new_balance = balance + points
        await PointsFlow.create(
            user_id=user_id,
            flow_type=flow_type,
            amount=points,
            balance=new_balance,
            grant_ids=[grant.id],
            using_db=conn,
        )


# ========== Gift ==========
class GiftController(CRUDBase[Gift, GiftCreate, GiftUpdate]):
    def __init__(self):
        super().__init__(model=Gift)

    async def create_gift(
        self, user_id: str, points: int, gift_type: str, note: str, expired_at: Optional[datetime] = None
    ) -> Gift:
        """创建赠送记录并添加积分"""
        if expired_at is None:
            expired_at = settings.PERMANENT_EXPIRED_AT

        async with in_transaction(settings.TORTOISE_ORM['apps']['models']['default_connection']) as conn:
            gift = await Gift.create(
                user_id=user_id,
                points=points,
                gift_type=gift_type,
                note=note,
                expired_at=expired_at,
                using_db=conn,
            )

            grant = await PointsGrant.create(
                user_id=user_id,
                amount=points,
                source_type='gift',
                source_id=gift.id,
                expired_at=expired_at,
                using_db=conn,
            )

            balance = await pointsflow_controller.get_balance(user_id, conn)
            new_balance = balance + points
            await PointsFlow.create(
                user_id=user_id,
                flow_type=PointsFlowType.GIFT,
                amount=points,
                balance=new_balance,
                grant_ids=[grant.id],
                using_db=conn,
            )

        return gift


# ========== Points ==========
class PointsGrantController(CRUDBase[PointsGrant, PointsGrantCreate, PointsGrantUpdate]):
    def __init__(self):
        super().__init__(model=PointsGrant)

    async def check_expired_points(self):
        """检查并处理过期积分"""
        now = datetime.now()
        # 直接在事务内查询并加锁处理
        async with in_transaction(settings.TORTOISE_ORM['apps']['models']['default_connection']) as conn:
            expired_grants = (
                await PointsGrant.filter(expired_at__lte=now, amount__gt=0).select_for_update().using_db(conn).all()
            )

            for grant in expired_grants:
                balance = await pointsflow_controller.get_balance(grant.user_id, conn)
                new_balance = max(0, balance - grant.amount)
                grant.amount = 0
                await grant.save(using_db=conn)

                await PointsFlow.create(
                    user_id=grant.user_id,
                    flow_type=PointsFlowType.EXPIRE,
                    amount=-grant.amount,
                    balance=new_balance,
                    using_db=conn,
                )
            logger.info(f'处理过期积分成功: {len(expired_grants)}')


class PointsFlowController(CRUDBase[PointsFlow, PointsFlowCreate, PointsFlowUpdate]):
    def __init__(self):
        super().__init__(model=PointsFlow)

    async def get_balance(self, user_id: str, conn=None) -> int:
        """获取用户积分余额"""
        query = PointsFlow.filter(user_id=user_id).order_by('-id').first()
        if conn:
            latest_flow = await query.using_db(conn)
        else:
            latest_flow = await query
        return latest_flow.balance if latest_flow else 0


product_controller = ProductController()
productorder_controller = ProductOrderController()
recharge_controller = RechargeController()
gift_controller = GiftController()
pointsgrant_controller = PointsGrantController()
pointsflow_controller = PointsFlowController()
