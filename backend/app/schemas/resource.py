from typing import Optional
from pydantic import BaseModel


# OTA版本
class OtaCreate(BaseModel):
    app_version: str  # APP版本，不能为空
    chip_type: str  # 芯片类型，不能为空
    device_model: str  # 设备型号，不能为空
    ota_url: Optional[str] = None  # OTA URL
    whole_url: Optional[str] = None  # 完整固件 URL
    is_default: Optional[bool] = False  # 是否为默认版本，默认为False
    force_update: Optional[bool] = False  # 是否强制更新，默认为False


class OtaUpdate(OtaCreate):
    id: int  # OTA版本ID，不能为空
    app_version: Optional[str] = None
    chip_type: Optional[str] = None
    device_model: Optional[str] = None
    ota_url: Optional[str] = None
