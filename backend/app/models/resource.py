from tortoise import fields
from .base import BaseModel, TimestampMixin


# OTA版本表
class Ota(BaseModel, TimestampMixin):
    app_version = fields.CharField(max_length=20, index=True, description='APP版本')
    chip_type = fields.CharField(max_length=255, null=True, index=True, description='芯片类型')
    device_model = fields.CharField(max_length=255, null=True, index=True, description='设备型号')
    ota_url = fields.CharField(max_length=255, null=True, description='OTA URL')
    whole_url = fields.CharField(max_length=255, null=True, description='完整固件 URL')
    is_default = fields.BooleanField(default=False, description='是否默认版本')
    force_update = fields.BooleanField(default=False, description='是否强制更新')
