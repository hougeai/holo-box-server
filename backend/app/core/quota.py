from models.admin import User, Role
from models.device import Device


class QuotaService:
    """用户配额服务类"""

    async def get_user_role(self, user_id: str, ret_role=False):
        """获取用户角色"""
        user = await User.filter(user_id=user_id).first()
        if not user or not user.role_id:
            return False, '用户不存在'
        role = await Role.filter(id=user.role_id).first()
        if role.id == 1 and not ret_role:  # 管理员无限制
            return True, ''
        return role, ''

    async def check_device(self, user_id: str):
        """检查设备绑定配额"""
        role, msg = await self.get_user_role(user_id)
        if isinstance(role, bool):
            return role, msg
        device_count = await Device.filter(user_id=user_id).count()
        if device_count >= role.max_devices:
            return False, f'当前用户等级：{role.name}，设备绑定数量已达上限：{role.max_devices}，请升级账号。'
        return True, ''


quota_service = QuotaService()
