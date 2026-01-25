from tortoise import fields
from .base import BaseModel, TimestampMixin, UUIDModel


# 设备表 默认值 null=False index=False
class Device(BaseModel, TimestampMixin, UUIDModel):
    user_id = fields.CharField(max_length=12, null=True, index=True, description='用户ID')
    device_id = fields.CharField(max_length=20, null=True, index=True, description='设备ID')
    mac_address = fields.CharField(max_length=20, null=True, index=True, description='MAC地址')
    app_version = fields.CharField(max_length=20, null=True, index=True, description='APP版本')
    chip_type = fields.CharField(max_length=255, null=True, index=True, description='芯片类型')
    device_model = fields.CharField(max_length=255, null=True, index=True, description='设备型号')
    auto_update = fields.BooleanField(default=False, description='是否开启OTA')
    last_conversation = fields.DatetimeField(null=True, description='最后一次对话时间')
    alias = fields.CharField(max_length=20, null=True, description='备注')
    is_unbound = fields.BooleanField(default=False, null=True, description='设备是否解绑过')
    agent_id = fields.CharField(max_length=64, null=True, index=True, description='智能体ID')
    serial_number = fields.CharField(max_length=64, null=True, index=True, description='序列号')
