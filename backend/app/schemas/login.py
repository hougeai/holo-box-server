from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class CredentialsSchema(BaseModel):
    email: str = Field(..., description='邮箱', example='admin')
    password: str = Field(..., description='密码', example='123456')
    remember: Optional[bool] = False  # 是否记住登录状态


class JWTOut(BaseModel):
    access_token: str
    user_id: str


class JWTPayload(BaseModel):
    user_id: str
    exp: datetime


#  小程序注册登录
class WxLoginRequest(BaseModel):
    code: str


class WxPhoneRequest(BaseModel):
    code: str
    user_id: str
