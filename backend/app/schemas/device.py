from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


# 设备相关
class DeviceCreate(BaseModel):
    mac_address: str
    user_id: Optional[str] = None
    device_id: Optional[str] = None
    chip_type: Optional[str] = None
    device_model: Optional[str] = None
    app_version: Optional[str] = None
    auto_update: Optional[bool] = False
    last_conversation: Optional[datetime] = None
    alias: Optional[str] = None
    is_unbound: Optional[bool] = False
    agent_id: Optional[str] = None
    serial_number: Optional[str] = None


class DeviceUpdate(DeviceCreate):
    id: int
    mac_address: Optional[str] = None


class DeviceBind(BaseModel):
    user_id: str = Field(description='用户ID')
    agent_id: Optional[str] = Field(default=None, description='智能体ID')
    code: str = Field(description='验证码')


class DevicePush(BaseModel):
    serial_number: str = Field(description='设备序列号')
    message: dict = Field(description='推送消息')
