from datetime import datetime
from typing import Optional
from pydantic import BaseModel


# 设备相关
class DeviceCreate(BaseModel):
    device_id: str
    uuid: str
    location: Optional[str] = None
    chip_type: Optional[str] = None
    device_model: Optional[str] = None
    app_version: Optional[str] = None
    ota_enabled: Optional[bool] = False
    last_conversation: Optional[datetime] = None
    note: Optional[str] = None
    user_id: Optional[str] = None
    is_unbound: Optional[bool] = False
    display_setting: Optional[dict] = None


class DeviceUpdate(DeviceCreate):
    id: int
    device_id: Optional[str] = None
    uuid: Optional[str] = None


class DeviceBind(BaseModel):
    agent_id: str
    code: str
