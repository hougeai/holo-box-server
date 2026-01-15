from fastapi import APIRouter
from core.dependency import DependPermisson

from .base import router as base_router
from .users import router as users_router
from .roles import router as roles_router
from .apis import router as apis_router
from .menus import router as menus_router
from .auditlog import router as auditlog_router
from .devices import router as devices_router
from .agents import router as agents_router
from .resources import router as resources_router
from .order import router as order_router
from .finance import router as finance_router

v1_router = APIRouter()

v1_router.include_router(base_router, tags=['基础模块'], prefix='/base')
v1_router.include_router(users_router, tags=['用户模块'], prefix='/user', dependencies=[DependPermisson])
v1_router.include_router(roles_router, tags=['角色模块'], prefix='/role', dependencies=[DependPermisson])
v1_router.include_router(apis_router, tags=['API模块'], prefix='/api', dependencies=[DependPermisson])
v1_router.include_router(menus_router, tags=['菜单模块'], prefix='/menu', dependencies=[DependPermisson])
v1_router.include_router(auditlog_router, tags=['审计日志模块'], prefix='/auditlog', dependencies=[DependPermisson])

v1_router.include_router(agents_router, tags=['智能体模块'], prefix='/agent', dependencies=[DependPermisson])
v1_router.include_router(devices_router, tags=['设备模块'], prefix='/device', dependencies=[DependPermisson])
v1_router.include_router(resources_router, tags=['资源模块'], prefix='/resource', dependencies=[DependPermisson])
v1_router.include_router(order_router, tags=['订单模块'], prefix='/order', dependencies=[DependPermisson])
v1_router.include_router(finance_router, tags=['支付模块'], prefix='/finance', dependencies=[DependPermisson])
