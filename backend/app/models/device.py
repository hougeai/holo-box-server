from tortoise import fields
from .base import BaseModel, TimestampMixin, UUIDModel


# 设备表 默认值 null=False index=False
class Device(BaseModel, TimestampMixin, UUIDModel):
    user_id = fields.CharField(max_length=12, null=True, index=True, description='用户ID')
    device_id = fields.CharField(max_length=20, unique=True, index=True, description='设备ID')
    location = fields.CharField(max_length=20, null=True, index=True, description='设备位置')
    app_version = fields.CharField(max_length=20, null=True, index=True, description='APP版本')
    chip_type = fields.CharField(max_length=255, null=True, index=True, description='芯片类型')
    device_model = fields.CharField(max_length=255, null=True, index=True, description='设备型号')
    ota_enabled = fields.BooleanField(default=False, description='是否开启OTA')
    last_conversation = fields.DatetimeField(null=True, description='最后一次对话时间')
    note = fields.CharField(max_length=20, null=True, description='备注')
    is_unbound = fields.BooleanField(default=False, null=True, description='设备是否解绑过')
    display_setting = fields.JSONField(null=True, description='显示设置')
    agent_id = fields.CharField(max_length=64, null=True, index=True, description='智能体ID')
